"""Independent MedCPT raw-inner-product retrieval over a frozen corpus axis.

Serving requires a verified full-corpus FAISS index. An explicitly enabled,
budgeted sharded-exact backend is a reference implementation, not the default
24-million-row serving path. No BM25 candidates enter this module.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

from .corpus_retrieval_service import (
    CorpusRetrievalService, CorpusUnavailable, RetrievalTimeout, _read_json, _under_root,
)

QUERY_REVISION = "d83a36cc6b8e3a5c5e9d9d6ba156808c1643dcbc"
QUERY_PARENT = "replica_yht/models/MedRR-EBM-Sufficiency/MedCPT/MedCPT-Query-Encoder"
VALID_SOURCES = {"pubmed", "textbooks", "statpearls"}


class DenseUnavailable(CorpusUnavailable):
    """Independent full-corpus dense search is not genuinely ready."""


def resolve_query_path(root: str | Path | None = None, override: str | Path | None = None) -> Path:
    default = "E:/医学检索库_完整_20261010" if os.name == "nt" else "/data/medical-corpus"
    corpus_root = Path(root or os.getenv("RAG_CORPUS_ROOT", default)).expanduser().resolve()
    candidate = Path(override or os.getenv("RAG_MEDCPT_QUERY_PATH", "") or corpus_root / QUERY_PARENT).expanduser().resolve()
    path = candidate if candidate.name == QUERY_REVISION else candidate / QUERY_REVISION
    if not (path / "config.json").is_file():
        raise DenseUnavailable("Fixed-revision MedCPT Query-Encoder config is missing")
    config = _read_json(path / "config.json")
    if config.get("hidden_size") != 768 or config.get("model_type") != "bert":
        raise DenseUnavailable("Query-Encoder is incompatible with the 768-D MedCPT vector contract")
    if not ((path / "model.safetensors").is_file() or (path / "pytorch_model.bin").is_file()):
        raise DenseUnavailable("Fixed-revision Query-Encoder weights are missing")
    if not ((path / "tokenizer.json").is_file() or (path / "vocab.txt").is_file()):
        raise DenseUnavailable("Fixed-revision Query-Encoder tokenizer is missing")
    return path


class MedcptDenseService:
    def __init__(self, root: str | Path | None = None, *, backend: str | None = None,
                 index_path: str | Path | None = None, allow_exact_scan: bool | None = None,
                 max_scan_rows: int | None = None, block_rows: int = 8192,
                 timeout_seconds: float | None = None, max_index_bytes: int | None = None,
                 query_encoder: Callable[[str], Any] | None = None):
        self.corpus = CorpusRetrievalService(root, medcpt_rerank=False)
        self.root = self.corpus.root
        self.backend = backend or os.getenv("RAG_DENSE_BACKEND", "faiss")
        configured_index = index_path or os.getenv("RAG_DENSE_INDEX_PATH", "")
        self.index_path = Path(configured_index).expanduser().resolve() if configured_index else None
        self.allow_exact_scan = allow_exact_scan if allow_exact_scan is not None else (
            os.getenv("RAG_DENSE_ALLOW_EXACT_SCAN", "false").casefold() == "true")
        self.max_scan_rows = int(max_scan_rows if max_scan_rows is not None else os.getenv("RAG_DENSE_MAX_SCAN_ROWS", "0"))
        self.block_rows = max(1, min(int(block_rows), 32768))
        self.timeout_seconds = float(timeout_seconds if timeout_seconds is not None else os.getenv("RAG_DENSE_TIMEOUT_SECONDS", "20"))
        self.max_index_bytes = int(max_index_bytes if max_index_bytes is not None else os.getenv("RAG_DENSE_MAX_INDEX_BYTES", str(512 * 1024 * 1024)))
        self._provided_encoder = query_encoder
        self._encoder_lock = threading.Lock()
        self._encoder = None
        self._tokenizer = None
        self._index_lock = threading.Lock()
        self._index = None
        self._index_identity = None
        self._index_io = "not_loaded"

    def resolve_query_path(self) -> Path:
        return resolve_query_path(self.root)

    def _preflight(self, *, sources=None) -> dict[str, Any]:
        try:
            manifest, db, identity = self.corpus._verify_snapshot()
        except CorpusUnavailable as exc:
            raise DenseUnavailable(str(exc)) from exc
        if (manifest.get("dimensions") != 768 or manifest.get("dtype") != "float32"
                or manifest.get("similarity") != "raw_inner_product"
                or manifest.get("normalization") != "none"
                or manifest.get("document_encoder") != "ncbi/MedCPT-Article-Encoder"):
            raise DenseUnavailable("Frozen corpus vectors are not compatible MedCPT raw-IP vectors")
        total_rows = int(manifest["total_rows"])
        if total_rows <= 0:
            raise DenseUnavailable("Dense corpus row axis must be nonempty")
        shards = sorted(manifest.get("vector_shards", []), key=lambda item: int(item["start"]))
        cursor = 0
        for shard in shards:
            if int(shard["start"]) != cursor or int(shard["end"]) <= cursor:
                raise DenseUnavailable("Vector manifest has a gap, overlap, or invalid row axis")
            cursor = int(shard["end"])
            if self.backend == "sharded_exact":
                path = _under_root(self.root, shard["path"])
                if not path.is_file():
                    raise DenseUnavailable("A declared frozen vector shard is missing")
                expected_bytes = shard.get("source_identity", {}).get("bytes")
                if expected_bytes and path.stat().st_size != int(expected_bytes):
                    raise DenseUnavailable("Vector shard size disagrees with source identity")
        if cursor != total_rows:
            raise DenseUnavailable("Vector axis does not cover every declared corpus row")
        if sources and not set(sources).issubset(VALID_SOURCES):
            raise ValueError("Unknown corpus source filter")
        filtered_sources = sources if sources and set(sources) != VALID_SOURCES else None
        # Fail resource readiness BEFORE importing/loading any query model.
        metadata = None
        if self.backend == "sharded_exact":
            if not self.allow_exact_scan:
                raise DenseUnavailable("Sharded exact full-corpus scan requires explicit opt-in")
            if self.max_scan_rows < total_rows:
                raise DenseUnavailable(f"Exact-scan budget {self.max_scan_rows} rows is smaller than full axis {total_rows}; partial scans are not full-corpus recall")
            if self.timeout_seconds <= 0:
                raise DenseUnavailable("Dense search timeout must be positive")
        elif self.backend == "faiss":
            metadata = self._index_metadata(manifest, total_rows)
            if filtered_sources:
                raise DenseUnavailable("Source-restricted ANN needs source-complete indexes; finite global top-k post-filtering is not supported")
            if importlib.util.find_spec("faiss") is None:
                raise DenseUnavailable("Optional FAISS runtime is not installed")
        else:
            raise DenseUnavailable("Independent dense backend is disabled or unknown")
        query_path = self.resolve_query_path()
        if self._provided_encoder is None:
            if importlib.util.find_spec("torch") is None or importlib.util.find_spec("transformers") is None:
                raise DenseUnavailable("Optional local MedCPT torch/transformers runtime is not installed")
        return {"manifest": manifest, "db": db, "identity": identity, "shards": shards,
                "total_rows": total_rows, "metadata": metadata, "query_path": query_path,
                "sources": filtered_sources}

    def _index_metadata(self, manifest: dict[str, Any], total_rows: int) -> dict[str, Any]:
        if self.index_path is None or not self.index_path.is_file():
            raise DenseUnavailable("No completed full-corpus FAISS index is configured; build planning does not create an index")
        if self.index_path.stat().st_size > self.max_index_bytes:
            raise DenseUnavailable("FAISS artifact exceeds configured serialized-index byte budget")
        metadata = _read_json(Path(str(self.index_path) + ".json"))
        digest = hashlib.sha256((self.root / "UNIFIED_MANIFEST_PORTABLE.json").read_bytes()).hexdigest()
        expected = {
            "schema": "MEDCPT-ANN-v1", "state": "COMPLETE", "total_rows": total_rows,
            "dimensions": 768, "metric": "raw_inner_product", "normalization": "none",
            "pooling": "CLS", "query_max_length": 64, "query_encoder_revision": QUERY_REVISION,
            "article_encoder_revision": manifest.get("legacy_article_revision"),
            "row_ids": "global_row_index", "corpus_manifest_sha256": digest,
        }
        if any(metadata.get(key) != value for key, value in expected.items()):
            raise DenseUnavailable("FAISS index provenance/row-axis/encoder/metric metadata mismatch")
        if "approximate" not in metadata or not isinstance(metadata["approximate"], bool):
            raise DenseUnavailable("FAISS index must declare exact versus approximate retrieval")
        return metadata

    def status(self) -> dict[str, Any]:
        base = {"channel": "medcpt", "backend": self.backend, "scope": "full_corpus",
                "query_encoder_revision": QUERY_REVISION, "pooling": "CLS", "query_max_length": 64,
                "metric": "raw_inner_product", "normalization": "none",
                "tie_break": "row_index_ASC", "original_experiment_tie_break": "document_id_ASC_not_row_index",
                "reproduction_warning": "Serving tie breaks and approximate ANN do not promise exact YHT experiment reproduction",
                "independent_of_bm25": True, "default_full_vector_scan": False,
                "max_scan_rows": self.max_scan_rows, "max_index_bytes": self.max_index_bytes,
                "memory_note": "Index file-size budget is not a hard resident-memory limit; provision target process memory separately"}
        try:
            preflight = self._preflight()
            return {**base, "ready": True, "total_rows": preflight["total_rows"],
                    "vector_shards": len(preflight["shards"]),
                    "vector_shards_basis": "declared manifest axis; FAISS serving does not require original npy files",
                    "approximate": bool((preflight["metadata"] or {}).get("approximate", False)),
                    "readiness_basis": "metadata/resources/dependency preflight; no encoder inference or full vector scan performed"}
        except (CorpusUnavailable, ValueError, OSError) as exc:
            return {**base, "ready": False, "error": str(exc)}

    def _encode_query(self, query: str, path: Path):
        if self._provided_encoder:
            return self._provided_encoder(query)
        import torch
        from transformers import AutoModel, AutoTokenizer
        with self._encoder_lock:
            if self._encoder is None:
                self._tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True)
                self._encoder = AutoModel.from_pretrained(str(path), local_files_only=True)
                self._encoder.to(os.getenv("RAG_EMBEDDING_DEVICE", "cpu")).eval()
            device = next(self._encoder.parameters()).device
            inputs = self._tokenizer([query], padding=True, truncation=True,
                                     max_length=64, return_tensors="pt").to(device)
            with torch.inference_mode():
                # Exact MedCPT contract: float32 CLS, no L2 normalization.
                return self._encoder(**inputs).last_hidden_state[0, 0].float().cpu().numpy()

    def _load_faiss_index(self, preflight):
        import faiss
        with self._index_lock:
            stat = self.index_path.stat()
            identity = (stat.st_size, stat.st_mtime_ns)
            if self._index is not None and self._index_identity != identity:
                raise DenseUnavailable("Cached immutable FAISS generation changed; restart with a closed index")
            if self._index is None:
                # IVF inverted lists can be mmap'ed; index bytes are still
                # budget-checked because not all FAISS types support mmap.
                try:
                    index = faiss.read_index(str(self.index_path), faiss.IO_FLAG_MMAP | faiss.IO_FLAG_READ_ONLY)
                    self._index_io = "mmap_requested"
                except RuntimeError as exc:
                    # Some Windows FAISS wheels do not register the mmap IVF
                    # hook. A tiny fixture/index can be loaded safely; large
                    # artifacts require explicit memory opt-in and remain under
                    # the existing serialized-index byte budget.
                    hook_missing = "InvertedListsIOHook" in str(exc) or "could not load ArrayInvertedLists" in str(exc)
                    allow_memory = os.getenv("RAG_DENSE_ALLOW_IN_MEMORY_INDEX", "false").casefold() == "true"
                    if not hook_missing or (stat.st_size > 64*1024*1024 and not allow_memory):
                        raise DenseUnavailable("FAISS mmap load failed; large in-memory index loading requires explicit opt-in") from exc
                    index = faiss.read_index(str(self.index_path), faiss.IO_FLAG_READ_ONLY)
                    self._index_io = "in_memory_small_index" if stat.st_size <= 64*1024*1024 else "in_memory_explicit_opt_in"
                if index.ntotal != preflight["total_rows"] or index.d != 768 or index.metric_type != faiss.METRIC_INNER_PRODUCT:
                    raise DenseUnavailable("Loaded FAISS index differs from declared full-corpus raw-IP contract")
                if not index.is_trained:
                    raise DenseUnavailable("FAISS index has not been trained")
                underlying = index
                while isinstance(underlying, (faiss.IndexIDMap, faiss.IndexIDMap2)):
                    underlying = faiss.downcast_index(underlying.index)
                if not preflight["metadata"]["approximate"] and not isinstance(underlying, faiss.IndexFlat):
                    raise DenseUnavailable("Non-Flat FAISS search must not be declared exact")
                nprobe = int(os.getenv("RAG_DENSE_NPROBE", "32"))
                if hasattr(index, "nprobe"):
                    index.nprobe = max(1, min(nprobe, int(index.nlist)))
                self._index = index
                self._index_identity = identity
            return self._index

    def search(self, query: str, top_k: int = 32, sources=None) -> dict[str, Any]:
        import numpy as np
        if not query.strip() or len(query) > 2000:
            raise ValueError("Dense query must contain 1 to 2000 characters")
        top_k = max(1, min(int(top_k), 128))
        preflight = self._preflight(sources=sources)
        started = time.monotonic()
        vector = np.asarray(self._encode_query(query.strip(), preflight["query_path"]), dtype=np.float32)
        if vector.shape != (768,) or not np.isfinite(vector).all() or not np.any(vector):
            raise DenseUnavailable("Query encoder returned an invalid 768-D vector")
        if self.backend == "faiss":
            index = self._load_faiss_index(preflight)
            scores, row_ids = index.search(vector.reshape(1, -1), min(top_k, preflight["total_rows"]))
            results = [(int(row), float(score)) for row, score in zip(row_ids[0], scores[0]) if int(row) >= 0]
            if any(row >= preflight["total_rows"] or not np.isfinite(score) for row, score in results):
                raise DenseUnavailable("FAISS returned invalid corpus row IDs or scores")
            if len({row for row, _ in results}) != len(results):
                raise DenseUnavailable("FAISS returned duplicated global row IDs")
            mode = "medcpt_faiss_ann" if preflight["metadata"]["approximate"] else "medcpt_faiss_exact"
            scanned_rows = None
        else:
            results = self._sharded_exact(vector, top_k, preflight, started + self.timeout_seconds)
            mode, scanned_rows = "medcpt_sharded_exact", preflight["total_rows"]
        db_stat = preflight["db"].stat()
        if (db_stat.st_size, db_stat.st_mtime_ns) != preflight["identity"]:
            raise DenseUnavailable("Frozen corpus changed during dense retrieval")
        results.sort(key=lambda item: (-item[1], item[0]))
        hits = [{"row_index": row, "dense_score": score, "dense_rank": rank}
                for rank, (row, score) in enumerate(results[:top_k], 1)]
        return {"hits": hits, "mode": mode, "diagnostics": {
            "scope": "full_corpus", "total_rows": preflight["total_rows"],
            "sources": preflight["sources"] or [], "independent_of_bm25": True,
            "query_encoder_revision": QUERY_REVISION, "pooling": "CLS", "query_max_length": 64,
            "metric": "raw_inner_product", "normalization": "none", "scan_rows": scanned_rows,
            "tie_break": "row_index_ASC", "original_experiment_tie_break": "document_id_ASC_not_row_index",
            "reproduction_warning": "Same vectors/encoder contract does not prove original experiment tie-boundary or ANN equivalence",
            "approximate": bool((preflight["metadata"] or {}).get("approximate", False)),
            "score_semantics": "approximate_inner_product" if (preflight["metadata"] or {}).get("approximate") else "exact_raw_inner_product",
            "index_io": self._index_io if self.backend == "faiss" else "bounded_shard_mmap",
            "elapsed_ms": round((time.monotonic() - started) * 1000, 2)}}

    def _sharded_exact(self, vector, top_k, preflight, deadline):
        import numpy as np
        best_scores, best_ids = np.empty(0, dtype=np.float32), np.empty(0, dtype=np.int64)
        connection = self.corpus._connect(preflight["db"]) if preflight["sources"] else None
        try:
            for shard in preflight["shards"]:
                arrays = np.load(_under_root(self.root, shard["path"]), mmap_mode="r", allow_pickle=False)
                try:
                    start, end = int(shard["start"]), int(shard["end"])
                    if arrays.shape != (end-start, 768) or arrays.dtype != np.float32:
                        raise DenseUnavailable("Frozen shard shape or dtype mismatch")
                    for offset in range(0, end-start, self.block_rows):
                        if time.monotonic() >= deadline:
                            raise RetrievalTimeout("Independent exact dense scan timed out; no partial results returned")
                        stop = min(end-start, offset+self.block_rows)
                        if connection:
                            placeholders = ",".join("?" for _ in preflight["sources"])
                            rows = connection.execute(f"SELECT row_index FROM chunks WHERE row_index>=? AND row_index<? AND corpus IN ({placeholders})",
                                [start+offset, start+stop, *preflight["sources"]]).fetchall()
                            block_ids = np.asarray([int(row[0]) for row in rows], dtype=np.int64)
                            if not block_ids.size:
                                continue
                            block_vectors = arrays[block_ids-start]
                        else:
                            block_ids = np.arange(start+offset, start+stop, dtype=np.int64)
                            block_vectors = arrays[offset:stop]
                        scores = block_vectors @ vector
                        if not np.isfinite(scores).all():
                            raise DenseUnavailable("Non-finite frozen vector inner products")
                        all_scores = np.concatenate((best_scores, scores))
                        all_ids = np.concatenate((best_ids, block_ids))
                        # Bounded deterministic exact selection. Memory holds
                        # one <=32768-row block plus top-k, never the full corpus.
                        order = np.lexsort((all_ids, -all_scores))[:top_k]
                        best_scores, best_ids = all_scores[order], all_ids[order]
                        del block_vectors
                finally:
                    mmap = getattr(arrays, "_mmap", None)
                    if mmap is not None:
                        mmap.close()
                    del arrays
        finally:
            if connection:
                connection.close()
        return list(zip(best_ids.tolist(), best_scores.tolist()))
