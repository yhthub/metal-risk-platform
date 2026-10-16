"""Offline adapter tests use only a small newly-created immutable fixture.

No production SQLite file, encoder, LLM, network, or full corpus scan is used.
"""

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from app.services.corpus_retrieval_service import (
    CorpusRetrievalService, CorpusUnavailable, RetrievalTimeout, lexical_terms,
)


class CorpusFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.catalog = self.root / "00_catalog"
        self.catalog.mkdir()
        self.db = self.root / "corpus.sqlite3"
        with closing(sqlite3.connect(self.db)) as connection:
            connection.executescript("""
                CREATE TABLE chunks(row_index INTEGER PRIMARY KEY, document_id TEXT NOT NULL UNIQUE,
                    corpus TEXT NOT NULL,title TEXT NOT NULL,content TEXT NOT NULL,
                    source_key TEXT NOT NULL,source_row INTEGER NOT NULL);
                CREATE VIRTUAL TABLE chunks_fts USING fts5(title,content,content='chunks',
                    content_rowid='row_index',tokenize='unicode61');
            """)
            rows = [
                (0, "pubmed/example_0", "pubmed", "Cadmium and kidney injury",
                 "Occupational cadmium exposure causes renal tubular injury.", "example", 0),
                (1, "statpearls/example_1", "statpearls", "Lead poisoning",
                 "Blood lead and occupational exposure to lead require assessment.", "medtext", 1),
                (2, "textbooks/example_2", "textbooks", "Blood pressure",
                 "Hypertension and blood pressure measurement.", "medtext", 2),
            ]
            connection.executemany("INSERT INTO chunks VALUES(?,?,?,?,?,?,?)", rows)
            connection.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
            connection.commit()
        self.manifest = {
            "schema": "MEDRR-UNIFIED-RETRIEVAL-v1", "corpus_database": "corpus.sqlite3",
            "total_rows": 3, "vector_shards": [], "dimensions": 768, "dtype": "float32",
            "document_encoder": "ncbi/MedCPT-Article-Encoder", "similarity": "raw_inner_product",
            "normalization": "none",
        }
        self.progress = {"state": "COMPLETE", "local_database_bytes": self.db.stat().st_size,
                         "total_chunks": 3, "source_counts": {"pubmed": 1, "statpearls": 1, "textbooks": 1}}
        self.provenance = {"state": "COMPLETE", "snapshot_complete_by_backup_api": True}
        self.save_catalogs()
        self.service = CorpusRetrievalService(self.root, medcpt_rerank=False)

    def save_catalogs(self):
        (self.root / "UNIFIED_MANIFEST_PORTABLE.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        (self.catalog / "EXPORT_PROGRESS.json").write_text(json.dumps(self.progress), encoding="utf-8")
        (self.catalog / "SNAPSHOT_PROVENANCE.json").write_text(json.dumps(self.provenance), encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def test_status_does_not_count_or_open_db(self):
        with patch.object(self.service, "_connect", side_effect=AssertionError("Must not open")):
            status = self.service.status()
        self.assertTrue(status["ready"])
        self.assertEqual(status["total_chunks"], 3)
        self.assertIn("catalog", status["counts_basis"])

    def test_true_bm25_and_absent_identifiers_are_null(self):
        result = self.service.search("cadmium kidney", top_k=1)
        self.assertEqual(result["mode"], "bm25")
        hit = result["hits"][0]
        self.assertEqual(hit["chunk_id"], "pubmed/example_0")
        self.assertLess(hit["score"], 0)
        self.assertIsNone(hit["pmid"])
        self.assertIsNone(hit["doi"])
        self.assertIsNone(hit["dense_score"])
        self.assertEqual(result["diagnostics"]["independent_dense_recall"], False)
        self.assertEqual(hit["query_term_coverage"], 1.0)
        self.assertEqual(hit["match_tier"], "all_terms")

    def test_chinese_expansion_is_explicit(self):
        result = self.service.search("镉影响肾小管吗", top_k=1)
        self.assertEqual(result["hits"][0]["source"], "pubmed")
        self.assertEqual(set(result["diagnostics"]["terminology_expansion"]), {"cadmium", "renal tubular"})
        self.assertIn("dictionary", result["diagnostics"]["translation_method"])

    def test_empty_lexical_query_does_not_open_database(self):
        with patch.object(self.service, "_connect", side_effect=AssertionError("Must not open")):
            result = self.service.search("你好")
        self.assertEqual(result["hits"], [])
        self.assertTrue(result["diagnostics"]["warnings"])

    def test_disease_and_nonadjacent_occupation_terms_are_not_lost(self):
        terms, translations = lexical_terms("职业铅暴露与高血压")
        self.assertTrue({"occupational", "lead", "exposure", "hypertension"}.issubset(terms))
        terms, _ = lexical_terms("阿尔茨海默病会影响认知吗")
        self.assertEqual(set(terms), {"alzheimer", "cognition"})

    def test_or_supplement_is_marked_partial_not_sufficient(self):
        # Both words exist, but in different documents: a partial supplement is
        # still allowed and must not be presented as complete support.
        result = self.service.search("lead hypertension", top_k=2)
        self.assertEqual(result["diagnostics"]["all_term_candidates"], 0)
        self.assertEqual(result["hits"][0]["match_tier"], "partial_terms")
        self.assertEqual(result["hits"][0]["query_term_coverage"], 0.5)
        self.assertTrue(result["diagnostics"]["warnings"])

    def test_missing_literal_does_not_expand_to_high_frequency_partial_search(self):
        with patch.object(self.service, "_lexical_query", wraps=self.service._lexical_query) as query:
            result = self.service.search("nonexistentconcept kidney", top_k=2)
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["diagnostics"]["missing_lexical_terms"], ["nonexistentconcept"])
        self.assertEqual(query.call_count, 1)
        self.assertIn("OR skipped", result["diagnostics"]["lexical_operator"])
        self.assertTrue(result["diagnostics"]["warnings"])

    def test_fts_operators_are_literals_and_tokens_are_bounded(self):
        tokens, _ = lexical_terms('cadmium" OR * NEAR(kidney) ' + "word " * 500)
        self.assertNotIn("or", tokens)
        self.assertLessEqual(len(tokens), 18)
        self.assertNotIn('"', " ".join(tokens))
        result = self.service.search('cadmium" OR (kidney)', top_k=2)
        self.assertTrue(result["hits"])

    def test_source_filter_is_real_and_no_result_does_not_fabricate(self):
        result = self.service.search("lead", sources=["pubmed"])
        self.assertEqual(result["hits"], [])
        result = self.service.search("lead", sources=["statpearls"])
        self.assertEqual(result["hits"][0]["source"], "statpearls")
        with self.assertRaises(ValueError):
            self.service.search("lead", sources=["invented"])

    def test_refuses_wal_before_any_connection(self):
        Path(str(self.db) + "-wal").touch()
        with patch.object(self.service, "_connect", side_effect=AssertionError("Must not open")):
            with self.assertRaises(CorpusUnavailable):
                self.service.search("lead")
        self.assertFalse(self.service.status()["ready"])

    def test_refuses_incomplete_and_size_mismatch(self):
        self.progress["state"] = "DOWNLOADING"
        self.save_catalogs()
        self.assertFalse(self.service.status()["ready"])
        self.progress["state"] = "COMPLETE"
        self.progress["local_database_bytes"] += 1
        self.save_catalogs()
        self.assertFalse(self.service.status()["ready"])

    def test_refuses_manifest_escape(self):
        self.manifest["corpus_database"] = "../production.db"
        self.save_catalogs()
        self.assertFalse(CorpusRetrievalService(self.root).status()["ready"])

    def test_interrupted_query_reports_timeout_not_empty_success(self):
        with patch.object(self.service, "_lexical_query", side_effect=sqlite3.OperationalError("interrupted")):
            with self.assertRaises(RetrievalTimeout):
                self.service.search("lead")

    def test_unavailable_dense_reranker_retains_only_real_bm25(self):
        self.service.medcpt_rerank = True
        with patch.object(self.service, "_rerank_medcpt", side_effect=ImportError("No encoder")):
            result = self.service.search("lead")
        self.assertEqual(result["mode"], "bm25")
        self.assertIsNone(result["hits"][0]["dense_score"])
        self.assertTrue(result["diagnostics"]["warnings"])

    def test_optional_medcpt_uses_real_candidate_vector_products(self):
        import numpy as np

        # Tiny 3-row fixture, never a model call or production embedding write.
        vectors = np.zeros((3, 768), dtype=np.float32)
        vectors[1, 0] = 1.0
        vectors[2, 0] = 2.0
        np.save(self.root / "vectors.npy", vectors)
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("UPDATE chunks SET content=? WHERE row_index=2", ("lead occupational exposure",))
            connection.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
            connection.commit()
        self.progress["local_database_bytes"] = self.db.stat().st_size
        self.manifest["vector_shards"] = [{"path": "vectors.npy", "start": 0, "end": 3}]
        self.save_catalogs()
        service = CorpusRetrievalService(self.root, medcpt_rerank=True)
        query_vector = np.zeros(768, dtype=np.float32)
        query_vector[0] = 1.0
        with patch.object(service, "_encode_query", return_value=query_vector):
            result = service.search("lead", top_k=2)
        self.assertEqual(result["mode"], "bm25_medcpt_rerank")
        self.assertEqual({hit["row_index"]: hit["dense_score"] for hit in result["hits"]}, {1: 1.0, 2: 2.0})
        self.assertTrue(all(hit["score_type"].startswith("rrf_") for hit in result["hits"]))
        self.assertFalse(result["diagnostics"]["independent_dense_recall"])

    def test_incompatible_vector_contract_does_not_label_result_dense(self):
        self.manifest["normalization"] = "l2"
        self.save_catalogs()
        service = CorpusRetrievalService(self.root, medcpt_rerank=True)
        with patch.object(service, "_encode_query", side_effect=AssertionError("Must not encode incompatible vectors")):
            result = service.search("lead")
        self.assertEqual(result["mode"], "bm25")
        self.assertIsNone(result["hits"][0]["dense_score"])

    def test_content_is_bounded(self):
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("UPDATE chunks SET content=? WHERE row_index=0", ("cadmium " * 3000,))
            connection.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
            connection.commit()
        self.progress["local_database_bytes"] = self.db.stat().st_size
        self.save_catalogs()
        hit = self.service.search("cadmium", top_k=1)["hits"][0]
        self.assertEqual(len(hit["content"]), 12000)
        self.assertTrue(hit["content_truncated"])


if __name__ == "__main__":
    unittest.main()
