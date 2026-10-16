"""Streaming raw-IP IVFPQ builder. Default is PLAN_ONLY; --execute is required.

Never writes into the frozen corpus and never runs an encoder. A new independent
generation retains progress/partial files on failure; COMPLETE is published last.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.corpus_retrieval_service import CorpusRetrievalService, _under_root
from app.services.medcpt_dense_service import DenseUnavailable, QUERY_REVISION, resolve_query_path

GIB = 1024**3


@dataclass(frozen=True)
class BuildParameters:
    nlist: int = 4096
    pq_m: int = 64
    pq_bits: int = 8
    nprobe: int = 32
    sample_rows: int = 200000
    block_rows: int = 8192
    seed: int = 20261011
    threads: int = 4
    min_free_ram_gib: int = 8
    min_free_disk_gib: int = 8

    def validate(self, total_rows: int):
        if not (1 <= self.nlist <= 65536 and 1 <= self.pq_m <= 768 and 768 % self.pq_m == 0):
            raise ValueError("Invalid IVFPQ nlist or m (768 must be divisible by m)")
        if not (1 <= self.pq_bits <= 8 and 1 <= self.nprobe <= self.nlist):
            raise ValueError("IVFPQ bits must be 1..8 and nprobe must be 1..nlist")
        if not (1 <= self.sample_rows <= 500000 and 1 <= self.block_rows <= 8192 and 1 <= self.threads <= 32):
            raise ValueError("Training/sample/block/thread parameter exceeds bounded resource contract")
        if min(self.sample_rows, total_rows) < max(self.nlist, 1 << self.pq_bits):
            raise ValueError("Insufficient bounded training sample for selected centroids/codebook size")
        if self.min_free_ram_gib < 8 or self.min_free_disk_gib < 8:
            raise ValueError("Build safety floor is 8 GiB free RAM and 8 GiB free disk")
        if not (0 <= self.seed < 2**31):
            raise ValueError("Training seed must be an explicit nonnegative int32")


def available_ram_bytes() -> int:
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_uint32), ("memory_load", ctypes.c_uint32),
                        ("total_phys", ctypes.c_uint64), ("available_phys", ctypes.c_uint64),
                        ("total_page", ctypes.c_uint64), ("available_page", ctypes.c_uint64),
                        ("total_virtual", ctypes.c_uint64), ("available_virtual", ctypes.c_uint64),
                        ("available_extended", ctypes.c_uint64)]
        info = MemoryStatus()
        info.length = ctypes.sizeof(info)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(info)):
            raise DenseUnavailable("Cannot verify free physical RAM")
        return int(info.available_phys)
    memory_info = Path("/proc/meminfo")
    if memory_info.is_file():
        for line in memory_info.read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    raise DenseUnavailable("Cannot verify available RAM on this platform; build refused")


def output_target(root: Path, output: str | Path) -> Path:
    target = Path(output).expanduser().resolve()
    if target.is_relative_to(root) or root.is_relative_to(target):
        raise ValueError("Output generation must be independent of the corpus root/ancestors")
    if target.exists():
        raise FileExistsError("Output generation already exists; refusing overwrite or resume")
    return target


def _nearest_existing_parent(path: Path) -> Path:
    ancestor = path.parent
    while not ancestor.exists():
        if ancestor == ancestor.parent:
            raise DenseUnavailable("Cannot find destination filesystem for disk preflight")
        ancestor = ancestor.parent
    return ancestor


def _identity(path: Path):
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


def preflight(root: str | Path, output: str | Path, parameters: BuildParameters):
    corpus = CorpusRetrievalService(root, medcpt_rerank=False)
    manifest, db, _ = corpus._verify_snapshot()
    target = output_target(corpus.root, output)
    total = int(manifest["total_rows"])
    parameters.validate(total)
    if (manifest.get("dimensions") != 768 or manifest.get("dtype") != "float32"
            or manifest.get("similarity") != "raw_inner_product" or manifest.get("normalization") != "none"
            or manifest.get("document_encoder") != "ncbi/MedCPT-Article-Encoder"):
        raise DenseUnavailable("Builder accepts only unchanged 768-D float32 MedCPT raw-IP vectors")
    query_path = resolve_query_path(corpus.root)
    paths = [db, corpus.root / "UNIFIED_MANIFEST_PORTABLE.json",
             corpus.root / "00_catalog/EXPORT_PROGRESS.json", corpus.root / "00_catalog/SNAPSHOT_PROVENANCE.json"]
    paths.extend(path for path in query_path.iterdir() if path.is_file()
                 and not path.name.endswith(".part.source.json"))
    shards = sorted(manifest["vector_shards"], key=lambda row: int(row["start"]))
    cursor = 0
    for shard in shards:
        if int(shard["start"]) != cursor or int(shard["end"]) <= cursor:
            raise DenseUnavailable("Frozen vector axis has a gap or overlap")
        cursor = int(shard["end"])
        path = _under_root(corpus.root, shard["path"])
        if not path.is_file():
            raise DenseUnavailable("Missing declared vector shard")
        expected = shard.get("source_identity", {}).get("bytes")
        if expected and path.stat().st_size != int(expected):
            raise DenseUnavailable("Source vector size differs from declared identity")
        paths.append(path)
    if cursor != total:
        raise DenseUnavailable("Frozen vector axis does not cover the complete corpus")
    identities = {path: _identity(path) for path in paths}
    manifest_hash = hashlib.sha256((corpus.root / "UNIFIED_MANIFEST_PORTABLE.json").read_bytes()).hexdigest()
    return {"corpus": corpus, "manifest": manifest, "target": target, "shards": shards,
            "total_rows": total, "source_identities": identities,
            "manifest_hash": manifest_hash, "query_path": query_path}


def _write_json(path: Path, payload):
    temporary = path.with_name(path.name + ".writing")
    temporary.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    temporary.replace(path)


def _sample_ids(total: int, count: int, seed: int):
    import random
    # random.sample(range) uses bounded O(count) storage, not a full permutation.
    return sorted(random.Random(seed).sample(range(total), count))


def _training_sample(preflight_info, parameters):
    import numpy as np
    selected = np.asarray(_sample_ids(preflight_info["total_rows"],
                          min(parameters.sample_rows, preflight_info["total_rows"]), parameters.seed), dtype=np.int64)
    sample = np.empty((len(selected), 768), dtype=np.float32)
    root = preflight_info["corpus"].root
    for shard in preflight_info["shards"]:
        start, end = int(shard["start"]), int(shard["end"])
        left, right = np.searchsorted(selected, [start,end])
        if left == right:
            continue
        vectors = np.load(_under_root(root, shard["path"]), mmap_mode="r", allow_pickle=False)
        try:
            if vectors.shape != (end-start,768) or vectors.dtype != np.float32:
                raise DenseUnavailable("Training shard shape/dtype mismatch")
            for offset in range(int(left),int(right),parameters.block_rows):
                stop = min(int(right),offset+parameters.block_rows)
                sample[offset:stop] = vectors[selected[offset:stop]-start]
        finally:
            vectors._mmap.close()
    if not np.isfinite(sample).all():
        raise DenseUnavailable("Non-finite training vectors")
    return selected, sample


def build_index(root: str | Path, output: str | Path, *, execute: bool = False,
                parameters: BuildParameters | None = None):
    parameters = parameters or BuildParameters()
    info = preflight(root, output, parameters)
    raw_bytes = info["total_rows"] * 768 * 4
    estimated_codes = info["total_rows"] * (parameters.pq_m + 8)
    plan = {
        "state":"PLAN_ONLY", "execution_performed":False, "vectors_scanned":0,
        "encoder_calls":0, "source_writes":0, "output_generation":str(info["target"]),
        "total_rows":info["total_rows"], "vector_shards":len(info["shards"]),
        "raw_vector_bytes":raw_bytes, "estimated_code_and_id_bytes":estimated_codes,
        "bounded_training_bytes":min(parameters.sample_rows,info["total_rows"])*768*4,
        "training_sample_method":"global_row_uniform_without_replacement",
        "parameters":asdict(parameters), "metric":"raw_inner_product", "normalize":False,
        "approximate":True, "warnings":["PLAN_ONLY does not create an index or completion receipt.",
            "IVFPQ recall and row-index tie policy do not reproduce original YHT exact document-ID tie rules."]}
    if not execute:
        return plan
    free_ram = available_ram_bytes()
    free_disk = shutil.disk_usage(_nearest_existing_parent(info["target"])).free
    required_disk = max(parameters.min_free_disk_gib*GIB, estimated_codes*2 + GIB)
    if free_ram < parameters.min_free_ram_gib*GIB or free_disk < required_disk:
        raise DenseUnavailable("Insufficient resources: execution requires >=8 GiB free physical RAM and >=8 GiB free disk (or larger index budget)")
    try:
        import faiss
        import numpy as np
    except ImportError as exc:
        raise DenseUnavailable("Execute requires optional local faiss-cpu and numpy; no packages are installed automatically") from exc
    # Atomic generation creation; never reuse or overwrite an old generation.
    info["target"].mkdir(parents=True,exist_ok=False)
    progress_path = info["target"] / "BUILD_PROGRESS.json"
    progress = {**plan,"state":"BUILDING","execution_performed":True,"started_unix":time.time(),
                "inserted_rows":0,"full_source_hashes":0,"source_writes":0,"encoder_calls":0,
                "free_ram_before":free_ram,"free_disk_before":free_disk}
    _write_json(progress_path,progress)
    try:
        faiss.omp_set_num_threads(parameters.threads)
        selected,sample = _training_sample(info,parameters)
        np.save(info["target"] / "training_row_ids.npy",selected,allow_pickle=False)
        sample_validation = sample[:min(5,len(sample))].copy()
        validation_ids = selected[:len(sample_validation)].copy()
        quantizer = faiss.IndexFlatIP(768)
        index = faiss.IndexIVFPQ(quantizer,768,parameters.nlist,parameters.pq_m,parameters.pq_bits,faiss.METRIC_INNER_PRODUCT)
        index.cp.seed = parameters.seed
        index.pq.cp.seed = parameters.seed
        index.train(sample)
        if not index.is_trained:
            raise DenseUnavailable("FAISS training did not produce a trained index")
        del sample
        index.nprobe = parameters.nprobe
        for shard in info["shards"]:
            start,end = int(shard["start"]),int(shard["end"])
            vectors = np.load(_under_root(info["corpus"].root,shard["path"]),mmap_mode="r",allow_pickle=False)
            try:
                if vectors.shape != (end-start,768) or vectors.dtype != np.float32:
                    raise DenseUnavailable("Insertion shard shape/dtype mismatch")
                for offset in range(0,end-start,parameters.block_rows):
                    stop = min(end-start,offset+parameters.block_rows)
                    block = np.ascontiguousarray(vectors[offset:stop],dtype=np.float32)
                    if not np.isfinite(block).all():
                        raise DenseUnavailable("Non-finite insertion vectors")
                    ids = np.arange(start+offset,start+stop,dtype=np.int64)
                    index.add_with_ids(block,ids)
                    progress["inserted_rows"] += len(ids)
                    del block
            finally:
                vectors._mmap.close()
            progress["updated_unix"] = time.time()
            _write_json(progress_path,progress)
        if progress["inserted_rows"] != info["total_rows"] or index.ntotal != info["total_rows"]:
            raise DenseUnavailable("FAISS ntotal/global row-axis insertion coverage mismatch")
        scores,ids = index.search(sample_validation,min(5,info["total_rows"]))
        validation = []
        for source_id,row_scores,row_ids in zip(validation_ids,scores,ids):
            valid = row_ids >= 0
            if not valid.any() or not np.isfinite(row_scores[valid]).all() or (row_ids[valid] >= info["total_rows"]).any():
                raise DenseUnavailable("Small-sample index row-ID/score validation failed")
            if len(set(row_ids[valid].tolist())) != int(valid.sum()):
                raise DenseUnavailable("Small-sample index validation returned duplicate row IDs")
            validation.append({"sample_row_index":int(source_id),"returned_row_ids":row_ids[valid].tolist(),
                               "approximate_inner_product_scores":row_scores[valid].tolist()})
        partial = info["target"] / "medcpt_ivfpq.partial.faiss"
        faiss.write_index(index,str(partial))
        if any(_identity(path) != expected for path,expected in info["source_identities"].items()):
            raise DenseUnavailable("Frozen source file size/mtime changed during index build")
        # Re-check closed snapshot/sidecars after all training/insert/serialize.
        info["corpus"]._verify_snapshot()
        final = info["target"] / "medcpt_ivfpq.faiss"
        partial.replace(final)
        metadata = {
            "schema":"MEDCPT-ANN-v1","state":"COMPLETE","total_rows":info["total_rows"],
            "dimensions":768,"metric":"raw_inner_product","normalization":"none",
            "pooling":"CLS","query_max_length":64,"query_encoder_revision":QUERY_REVISION,
            "article_encoder_revision":info["manifest"].get("legacy_article_revision"),
            "row_ids":"global_row_index","corpus_manifest_sha256":info["manifest_hash"],
            "approximate":True,"parameters":asdict(parameters),"faiss_version":getattr(faiss,"__version__","unknown"),
            "training_sample_method":"global_row_uniform_without_replacement",
            "inserted_rows":progress["inserted_rows"],"ntotal":int(index.ntotal),
            "source_identity_check":"size_mtime_PASS_not_full_content_hash",
            "small_sample_validation":validation,"semantic_gold_used":False,"encoder_calls":0,"source_writes":0,
            "validation_scope":"row-ID range/uniqueness, finite approximate scores and ntotal only; not ANN recall or semantic relevance validation",
            "tie_break":"row_index_ASC","original_experiment_tie_break":"document_id_ASC_not_row_index",
            "completed_unix":time.time(),"index_bytes":final.stat().st_size,
        }
        # The canonical usable sidecar is the final publication operation. No
        # later progress write can fail after a COMPLETE sidecar was committed.
        progress.update(state="COMPLETE",index_path=str(final),completed_unix=time.time())
        _write_json(progress_path,progress)
        _write_json(Path(str(final)+".json"),metadata)
        return metadata
    except Exception as exc:
        progress.update(state="FAILED",error_type=type(exc).__name__,error=str(exc),updated_unix=time.time())
        _write_json(progress_path,progress)
        raise


def main():
    parser = argparse.ArgumentParser(description="Build independent MedCPT IVFPQ; default PLAN_ONLY, explicit --execute required")
    parser.add_argument("--corpus-root",required=True)
    parser.add_argument("--output-dir",required=True,help="New independent generation directory; must not already exist")
    parser.add_argument("--execute",action="store_true")
    for field,default in asdict(BuildParameters()).items():
        parser.add_argument("--"+field.replace("_","-"),type=int,default=default)
    args = parser.parse_args()
    parameters = BuildParameters(**{field:getattr(args,field) for field in asdict(BuildParameters())})
    result = build_index(args.corpus_root,args.output_dir,execute=args.execute,parameters=parameters)
    print(json.dumps(result,ensure_ascii=True,indent=2))


if __name__ == "__main__":
    main()
