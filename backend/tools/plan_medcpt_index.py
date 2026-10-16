"""PLAN ONLY: print a full-corpus independent MedCPT ANN build contract.

Does not encode, train, scan vectors, load FAISS, create an index, or write files.
The completion sidecar described below must come from a separately authorized
offline builder with its real build/coverage validation, not from this plan.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.corpus_retrieval_service import CorpusRetrievalService
from app.services.medcpt_dense_service import QUERY_REVISION, resolve_query_path


def main():
    parser = argparse.ArgumentParser(description="Plan independent MedCPT ANN build; no execution option exists")
    parser.add_argument("--corpus-root", required=True)
    args = parser.parse_args()
    corpus = CorpusRetrievalService(args.corpus_root, medcpt_rerank=False)
    manifest, _, _ = corpus._verify_snapshot()
    rows = int(manifest["total_rows"])
    query_path = resolve_query_path(corpus.root)
    digest = hashlib.sha256((corpus.root / "UNIFIED_MANIFEST_PORTABLE.json").read_bytes()).hexdigest()
    plan = {
        "state": "PLAN_ONLY_NOT_BUILT", "execution_performed": False,
        "source_writes": 0, "vectors_scanned": 0, "encoder_calls": 0,
        "corpus_root": str(corpus.root), "query_encoder_path": str(query_path),
        "total_rows": rows, "vector_shards": len(manifest["vector_shards"]),
        "raw_vector_bytes": rows * 768 * 4,
        "proposal": {
            "type": "IndexIVFPQ", "metric": "METRIC_INNER_PRODUCT",
            "dimensions": 768, "nlist": 4096, "m": 64, "nbits": 8,
            "normalize": False, "approximate": True,
            "estimated_code_and_row_id_bytes": rows * (64 + 8),
            "extra_memory": "centroids/codebooks/training sample/search buffers; measure on target server",
            "purpose": "interactive independent full-corpus dense recall, not scientific exact-search equivalence",
        },
        "required_offline_steps": [
            "Obtain explicit build authority and provision a separate output directory and resource budget.",
            "Use only this closed corpus snapshot and its frozen MedCPT vector axis; do not recut/reencode text.",
            "Choose and record a deterministic bounded training sample, seed, source stratification and row IDs.",
            "Train raw-IP IVF/PQ codebooks with no normalization; record FAISS version and parameters.",
            "Stream every declared shard in bounded mmap batches; add vectors with their original global row_index IDs.",
            "Validate every shard/row axis, index ntotal, ID coverage, and raw-IP contract; benchmark ANN recall on held-out queries against separately authorized exact reference searches.",
            "Write index to a temporary output generation; freeze it and publish a COMPLETE sidecar only after actual build validation.",
            "For source-filtered ANN, build source-complete indexes with the same global row IDs; do not post-filter a finite global top-k as if it were source-complete recall.",
            "Deploy index read-only with explicit index-memory budget and nprobe; mechanically verify readiness before real model tests.",
        ],
        "completion_sidecar_contract_NOT_A_COMPLETION_RECEIPT": {
            "schema": "MEDCPT-ANN-v1", "state": "COMPLETE_ONLY_AFTER_REAL_BUILD",
            "total_rows": rows, "dimensions": 768, "metric": "raw_inner_product",
            "normalization": "none", "pooling": "CLS", "query_max_length": 64,
            "query_encoder_revision": QUERY_REVISION,
            "article_encoder_revision": manifest.get("legacy_article_revision"),
            "row_ids": "global_row_index", "approximate": True,
            "corpus_manifest_sha256": digest,
        },
        "warnings": [
            "This script does not build anything and its PLAN_ONLY output cannot make dense.status ready.",
            "IVFPQ is approximate and does not reproduce YHT exact raw-IP experiment results automatically.",
            "The exported PubMed package's exact Article-Encoder revision was not documented; preserve original provenance/validation notes.",
        ],
    }
    print(json.dumps(plan, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
