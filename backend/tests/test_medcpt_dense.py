"""Independent dense reference tests: tiny frozen fixtures, no real encoder."""
import hashlib
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import numpy as np

from app.services.medcpt_dense_service import (
    DenseUnavailable, MedcptDenseService, QUERY_PARENT, QUERY_REVISION, resolve_query_path,
)
from app.services.corpus_retrieval_service import RetrievalTimeout


class IndependentDenseFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "00_catalog").mkdir()
        self.db = self.root / "corpus.sqlite3"
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("CREATE TABLE chunks(row_index INTEGER PRIMARY KEY,corpus TEXT)")
            connection.executemany("INSERT INTO chunks VALUES(?,?)", [(0,"pubmed"),(1,"textbooks"),(2,"statpearls")])
            connection.commit()
        vectors = np.zeros((3, 768), dtype=np.float32)
        vectors[:, 0] = [3.0, 1.0, 2.0]
        np.save(self.root / "first.npy", vectors[:2])
        np.save(self.root / "second.npy", vectors[2:])
        self.manifest = {
            "schema": "MEDRR-UNIFIED-RETRIEVAL-v1", "total_rows": 3,
            "corpus_database": "corpus.sqlite3", "dimensions": 768, "dtype": "float32",
            "similarity": "raw_inner_product", "normalization": "none",
            "document_encoder": "ncbi/MedCPT-Article-Encoder",
            "legacy_article_revision": "d05a736da4bb84ee4057b7f7999485be6ed85465",
            "vector_shards": [{"start": 0, "end": 2, "path": "first.npy"},
                              {"start": 2, "end": 3, "path": "second.npy"}],
        }
        self.write_manifest()
        (self.root / "00_catalog/EXPORT_PROGRESS.json").write_text(json.dumps({
            "state": "COMPLETE", "total_chunks": 3, "local_database_bytes": self.db.stat().st_size}),encoding="utf-8")
        (self.root / "00_catalog/SNAPSHOT_PROVENANCE.json").write_text(json.dumps({
            "state": "COMPLETE", "snapshot_complete_by_backup_api": True}), encoding="utf-8")
        self.encoder_path = self.root / QUERY_PARENT / QUERY_REVISION
        self.encoder_path.mkdir(parents=True)
        (self.encoder_path / "config.json").write_text(json.dumps({"model_type":"bert","hidden_size":768}), encoding="utf-8")
        (self.encoder_path / "model.safetensors").write_bytes(b"fixture-not-a-model")
        (self.encoder_path / "tokenizer.json").write_text("{}", encoding="utf-8")
        self.encoder_calls = []
        self.query_vector = np.zeros(768, dtype=np.float32)
        self.query_vector[0] = 3.0

    def write_manifest(self):
        (self.root / "UNIFIED_MANIFEST_PORTABLE.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def encoder(self, query):
        self.encoder_calls.append(query)
        return self.query_vector

    def service(self, **kwargs):
        options = {"backend":"sharded_exact", "allow_exact_scan":True, "max_scan_rows":3,
                   "block_rows":1, "query_encoder":self.encoder}
        options.update(kwargs)
        return MedcptDenseService(self.root, **options)

    def tearDown(self):
        self.temporary.cleanup()

    def test_resolves_fixed_revision_child_not_empty_parent(self):
        self.assertEqual(resolve_query_path(self.root), self.encoder_path)
        self.assertEqual(resolve_query_path(self.root, self.encoder_path), self.encoder_path)

    def test_disabled_default_never_encodes_or_scans_vectors(self):
        service = MedcptDenseService(self.root, query_encoder=self.encoder)
        with patch("numpy.load", side_effect=AssertionError("No default scan")):
            self.assertFalse(service.status()["ready"])
            with self.assertRaises(DenseUnavailable):
                service.search("fixture")
        self.assertEqual(self.encoder_calls, [])

    def test_budget_insufficient_fails_before_encoding_not_partial_recall(self):
        service = self.service(max_scan_rows=2)
        with patch("numpy.load", side_effect=AssertionError("No partial scan")):
            self.assertFalse(service.status()["ready"])
            with self.assertRaises(DenseUnavailable):
                service.search("fixture")
        self.assertEqual(self.encoder_calls, [])

    def test_exact_requires_separate_explicit_opt_in(self):
        with self.assertRaises(DenseUnavailable):
            self.service(allow_exact_scan=False).search("fixture")
        self.assertEqual(self.encoder_calls, [])

    def test_status_never_runs_encoder_or_loads_arrays(self):
        service = self.service()
        with patch("numpy.load", side_effect=AssertionError("Status must not scan")):
            status = service.status()
        self.assertTrue(status["ready"])
        self.assertEqual(status["total_rows"], 3)
        self.assertEqual(status["scope"], "full_corpus")
        self.assertEqual(self.encoder_calls, [])

    def test_independent_full_fixture_raw_inner_product_not_cosine(self):
        result = self.service().search("unrelated to all BM25 fixture text", top_k=2)
        self.assertEqual([hit["row_index"] for hit in result["hits"]], [0,2])
        self.assertEqual([hit["dense_score"] for hit in result["hits"]], [9.0,6.0])
        self.assertEqual(result["diagnostics"]["scan_rows"], 3)
        self.assertTrue(result["diagnostics"]["independent_of_bm25"])
        self.assertEqual(result["mode"], "medcpt_sharded_exact")

    def test_exact_source_filter_precedes_ranking(self):
        result = self.service().search("fixture", top_k=1, sources=["textbooks"])
        self.assertEqual(result["hits"][0]["row_index"], 1)
        self.assertEqual(result["hits"][0]["dense_score"], 3.0)

    def test_vector_axis_gaps_are_rejected_before_encoding(self):
        self.manifest["vector_shards"][1]["start"] = 1
        self.write_manifest()
        with self.assertRaises(DenseUnavailable):
            self.service().search("fixture")
        self.assertEqual(self.encoder_calls, [])

    def test_incompatible_metric_is_not_a_dense_success(self):
        self.manifest["normalization"] = "l2"
        self.write_manifest()
        self.assertFalse(self.service().status()["ready"])
        self.assertEqual(self.encoder_calls, [])

    def test_sidecar_refusal_before_any_encoding(self):
        Path(str(self.db) + "-wal").touch()
        with self.assertRaises(DenseUnavailable.__bases__[0]):
            self.service().search("fixture")
        self.assertEqual(self.encoder_calls, [])

    def test_exact_timeout_does_not_return_partial_hits(self):
        with patch("app.services.medcpt_dense_service.time.monotonic", side_effect=[0.0,100.0]):
            with self.assertRaises(RetrievalTimeout):
                self.service(timeout_seconds=1).search("fixture")

    def test_nonfinite_query_vector_is_rejected(self):
        self.query_vector[0] = np.nan
        with self.assertRaises(DenseUnavailable):
            self.service().search("fixture")

    def test_zero_query_vector_is_not_informative_dense_recall(self):
        self.query_vector[:] = 0
        with self.assertRaises(DenseUnavailable):
            self.service().search("fixture")

    def test_ann_metadata_must_cover_same_full_axis(self):
        index_path = self.root / "index.faiss"
        index_path.write_bytes(b"fixture-no-real-faiss")
        metadata = {
            "schema":"MEDCPT-ANN-v1", "state":"COMPLETE", "total_rows":3,
            "dimensions":768, "metric":"raw_inner_product", "normalization":"none",
            "pooling":"CLS", "query_max_length":64, "query_encoder_revision":QUERY_REVISION,
            "article_encoder_revision":self.manifest["legacy_article_revision"],
            "row_ids":"global_row_index", "approximate":True,
            "corpus_manifest_sha256":hashlib.sha256((self.root / "UNIFIED_MANIFEST_PORTABLE.json").read_bytes()).hexdigest(),
        }
        Path(str(index_path)+".json").write_text(json.dumps(metadata), encoding="utf-8")
        service = self.service(backend="faiss", index_path=index_path)
        with patch("app.services.medcpt_dense_service.importlib.util.find_spec", return_value=object()):
            self.assertTrue(service.status()["ready"])
        metadata["total_rows"] = 2
        Path(str(index_path)+".json").write_text(json.dumps(metadata), encoding="utf-8")
        self.assertFalse(service.status()["ready"])
        self.assertEqual(self.encoder_calls, [])

    def test_optional_faiss_is_not_silently_substituted_by_bm25(self):
        with patch("app.services.medcpt_dense_service.importlib.util.find_spec", return_value=None):
            status = MedcptDenseService(self.root, query_encoder=self.encoder).status()
        self.assertFalse(status["ready"])
        self.assertTrue(status["independent_of_bm25"])

    @unittest.skipUnless(importlib.util.find_spec("faiss"), "Optional FAISS not installed; exact mmap reference covered separately")
    def test_actual_optional_faiss_flat_fixture(self):
        import faiss
        index_path = self.root / "tiny.faiss"
        vectors = np.zeros((3, 768), dtype=np.float32)
        vectors[:,0] = [3.0,1.0,2.0]
        index = faiss.IndexFlatIP(768)
        index.add(vectors)
        faiss.write_index(index,str(index_path))
        metadata = {
            "schema":"MEDCPT-ANN-v1", "state":"COMPLETE", "total_rows":3,
            "dimensions":768, "metric":"raw_inner_product", "normalization":"none",
            "pooling":"CLS", "query_max_length":64, "query_encoder_revision":QUERY_REVISION,
            "article_encoder_revision":self.manifest["legacy_article_revision"],
            "row_ids":"global_row_index", "approximate":False,
            "corpus_manifest_sha256":hashlib.sha256((self.root / "UNIFIED_MANIFEST_PORTABLE.json").read_bytes()).hexdigest(),
        }
        Path(str(index_path)+".json").write_text(json.dumps(metadata),encoding="utf-8")
        # A completed ANN/Flat serving package can omit the original shards;
        # only reference exact search/rebuild needs their original bytes.
        (self.root / "first.npy").unlink()
        (self.root / "second.npy").unlink()
        result = self.service(backend="faiss",index_path=index_path).search("fixture",top_k=2)
        self.assertEqual([item["row_index"] for item in result["hits"]],[0,2])
        self.assertEqual([item["dense_score"] for item in result["hits"]],[9.0,6.0])
        self.assertEqual(result["mode"],"medcpt_faiss_exact")
        with self.assertRaises(DenseUnavailable):
            self.service().search("fixture")


if __name__ == "__main__":
    unittest.main()
