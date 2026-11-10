"""Offline federation checks using stubs and tiny real read-only SQLite fixtures."""
import hashlib
import os
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

from app.services import combined_bm25_service as combined
from app.services.corpus_retrieval_service import CorpusRetrievalService, CorpusUnavailable, RetrievalTimeout
from app.services.rag_agent_service import create_retriever, select_evidence, evidence_context


def hit(source, index=1, *, score=-1, content="Cadmium kidney injury in children without unknownterm."):
    return {"chunk_id": str(index), "source": source, "title": "Fixture",
            "content": content * 5, "score": score, "lexical_rank": index,
            "score_type": "fts5_bm25_lower_is_better", "doi": None, "pmid": None}


class FakeRetriever:
    def __init__(self, name, log, *, results=None, errors=None, status=None):
        self.name, self.log = name, log
        self.results, self.errors = results or {}, errors or {}
        self.timeout_seconds = 8.0
        self.state = status if status is not None else {"ready": True}

    def status(self):
        return self.state

    def search(self, query, top_k, candidate_k, sources, *, deadline):
        self.log.append((self.name, query, top_k, candidate_k, sources, deadline))
        key = "medrr" if self.name == "medrr" else sources[0]
        if key in self.errors:
            raise self.errors[key]
        rows = self.results.get(key, [hit(sources[0] if sources else "pubmed")])
        return {"hits": rows[:top_k], "sparse_hits": rows, "mode": "bm25",
                "diagnostics": {"warnings": []}}


class CombinedRoutingTests(unittest.TestCase):
    def setUp(self):
        self.log = []
        self.old = FakeRetriever("medrr", self.log)
        self.local = FakeRetriever("local", self.log)
        self.service = combined.CombinedBm25RetrievalService(self.old, self.local)

    def test_default_search_is_sequential_and_visits_four_databases_six_sources(self):
        result = self.service.search("cadmium kidney", top_k=4, candidate_k=8)
        self.assertEqual([entry[0] for entry in self.log], ["medrr", "local", "local", "local"])
        self.assertEqual([entry[4] for entry in self.log], [None,
                         ["normative"], ["scientific"], ["guidelines"]])
        self.assertEqual(result["mode"], "bm25")
        self.assertEqual(result["dense_hits"], [])
        self.assertFalse(result["degraded"])
        self.assertTrue(result["diagnostics"]["all_requested_sources_searched"])

    def test_explicit_all_medrr_sources_use_the_unfiltered_fast_path(self):
        result = self.service.search("cadmium kidney", sources=["statpearls", "pubmed", "textbooks"])
        self.assertEqual(len(self.log), 1)
        self.assertIsNone(self.log[0][4])
        self.assertEqual(result["diagnostics"]["libraries"]["medrr"]["sources"], list(combined.MEDRR_SOURCES))
        self.assertEqual({row["source"] for row in result["hits"]}, {"pubmed"})

    def test_source_subsets_never_turn_empty_intersections_into_all(self):
        self.service.search("cadmium", sources=["guidelines", "guidelines"])
        self.assertEqual(len(self.log), 1)
        self.assertEqual(self.log[0][4], ["guidelines"])
        self.log.clear()
        self.service.search("cadmium", sources=["textbooks", "pubmed"])
        self.assertEqual(len(self.log), 1)
        self.assertEqual(self.log[0][4], ["pubmed", "textbooks"])
        self.log.clear()
        result = self.service.search("cadmium", sources=[])
        self.assertEqual(self.log, [])
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["diagnostics"]["search_state"], "empty_source_selection")

    def test_modes_invalid_sources_and_candidate_bounds(self):
        for kwargs in ({"mode": "hybrid"}, {"mode": "medcpt"}, {"sources": ["invented"]}, {"sources": "pubmed"}):
            with self.assertRaises(ValueError):
                self.service.search("cadmium", **kwargs)
        self.assertEqual(self.log, [])
        result = self.service.search("cadmium", top_k=99, candidate_k=999)
        self.assertTrue(all(entry[2:4] == (32, 32) for entry in self.log))
        self.assertLessEqual(len(result["hits"]), 12)
        self.assertLessEqual(len(result["sparse_hits"]), 32)

    def test_namespaces_metadata_and_raw_scores_are_retained(self):
        local = hit("normative")
        local.update(chunk_id="normative/1", original_chunk_id="1", original_document_id="D1",
                     source_url="https://example.org/source", standard_no_or_doi="GBZ 1-2020",
                     page=4, source_metadata={"evidence_priority": "P1"}, channel="normative")
        self.local.results["normative"] = [local]
        result = self.service.search("cadmium kidney", sources=["pubmed", "normative"])
        self.assertEqual({row["chunk_id"] for row in result["hits"]}, {"medrr/pubmed/1", "local_evidence/normative/1"})
        card = next(row for row in result["hits"] if row["source"] == "normative")
        self.assertEqual(card["original_chunk_id"], "1")
        self.assertEqual(card["url"], local["source_url"])
        self.assertEqual(card["standard_no_or_doi"], "GBZ 1-2020")
        self.assertEqual(card["page"], 4)
        self.assertEqual(card["source_metadata"], {"evidence_priority": "P1"})
        self.assertFalse(card["metadata_quality_verified"])
        self.assertIsNone(card["doi"])

    def test_equal_coverage_interleaves_database_ranks_without_raw_score_comparison(self):
        self.old.results["medrr"] = [hit("pubmed", 1, score=-99999), hit("pubmed", 2, score=-99998)]
        self.local.results["normative"] = [hit("normative", 1, score=-.00001), hit("normative", 2, score=-.000001)]
        result = self.service.search("cadmium kidney", sources=["pubmed", "normative"], top_k=4)
        self.assertEqual([row["source"] for row in result["hits"]], ["pubmed", "normative", "pubmed", "normative"])
        self.assertEqual(result["hits"][1]["score"], -.00001)
        self.assertEqual([row["combined_rank"] for row in result["hits"]], [1, 2, 3, 4])

    def test_full_query_coverage_precedes_partition_rank(self):
        self.old.results["medrr"] = [hit("pubmed", content="Cadmium only.")]
        result = self.service.search("cadmium kidney", sources=["pubmed", "normative"])
        self.assertEqual(result["hits"][0]["source"], "normative")
        self.assertEqual(result["hits"][1]["query_term_coverage"], .5)
        self.assertEqual(result["hits"][1]["match_tier"], "partial_terms")

    def test_long_query_negation_population_and_unknown_terms_retain_full_anchors(self):
        query = ("cadmium kidney injury exposure blood pressure hypertension diabetes cancer anemia "
                 "osteoporosis cognition cardiovascular inflammation chelation pregnancy workers adults "
                 "without quazylophenezn42 儿童 未知药物")
        result = self.service.search(query)
        terms = result["diagnostics"]["query_terms"]
        for term in ("without", "quazylophenezn42", "children", "未知药物"):
            self.assertIn(term, terms)
        self.assertFalse(select_evidence(result["hits"], 4, terms))
        self.assertTrue(all(entry[1] == query for entry in self.log))
        self.log.clear()
        result = self.service.search(query + " alpha beta gamma delta epsilon")
        self.assertTrue(result["diagnostics"]["query_limit_exceeded"])
        self.assertIn("epsilon", result["diagnostics"]["query_terms"])
        self.assertFalse(result["diagnostics"]["all_requested_sources_searched"])
        self.assertFalse(result["diagnostics"]["channels"]["bm25"]["ready"])
        self.assertEqual(result["hits"], [])
        self.assertEqual(self.log, [])

    def test_partial_failure_is_visible_and_successful_partitions_remain_usable(self):
        self.local.errors["scientific"] = CorpusUnavailable("fixture missing")
        result = self.service.search("cadmium")
        self.assertTrue(result["degraded"])
        self.assertTrue(result["partial"])
        self.assertEqual(result["diagnostics"]["failed_sources"], ["scientific"])
        self.assertFalse(result["diagnostics"]["all_requested_sources_searched"])
        self.assertEqual(len(result["hits"]), 3)
        self.assertTrue(any("未完成" in warning for warning in result["diagnostics"]["warnings"]))

    def test_unsupported_query_does_not_visit_missing_local_database_or_claim_success(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from app.services.local_evidence_service import LocalEvidenceRetrievalService
        with TemporaryDirectory() as root:
            missing = Path(root) / "not-created"
            local = LocalEvidenceRetrievalService(missing)
            service = combined.CombinedBm25RetrievalService(self.old, local)
            with patch.object(local, "_connect", side_effect=AssertionError("must not open")):
                result = service.search("孕妇", sources=["scientific"])
            self.assertFalse(missing.exists())
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["diagnostics"]["search_state"], "unsupported_query")
        self.assertFalse(result["diagnostics"]["all_requested_sources_searched"])
        self.assertFalse(result["diagnostics"]["libraries"]["scientific"]["searched"])
        self.assertEqual(result["diagnostics"]["unsupported_sources"], ["scientific"])
        self.assertEqual(result["diagnostics"]["failed_sources"], [])
        self.assertEqual(self.log, [])

    def test_all_unsupported_sources_return_empty_without_database_error(self):
        result = self.service.search("孕妇")
        self.assertEqual(self.log, [])
        self.assertEqual(result["diagnostics"]["search_state"], "unsupported_query")
        self.assertEqual(result["diagnostics"]["unsupported_sources"], list(combined.ALL_SOURCES))
        self.assertFalse(result["diagnostics"]["channels"]["bm25"]["ready"])
        self.assertTrue(all(not value["searched"] for value in result["diagnostics"]["libraries"].values()))

    def test_supported_medrr_and_unsupported_local_is_explicit_partial(self):
        result = self.service.search("cadmium 孕妇", sources=["pubmed", "scientific"])
        self.assertEqual(len(self.log), 1)
        self.assertEqual(self.log[0][0], "medrr")
        self.assertTrue(result["partial"])
        self.assertTrue(result["degraded"])
        self.assertEqual(result["diagnostics"]["search_state"], "partial")
        self.assertEqual(result["diagnostics"]["unsupported_sources"], ["scientific"])
        self.assertFalse(result["diagnostics"]["all_requested_sources_searched"])
        self.assertFalse(select_evidence(result["hits"], 4, result["diagnostics"]["query_terms"]))

    def test_all_failed_partitions_raise_and_release_capacity(self):
        self.old.errors["medrr"] = CorpusUnavailable("missing")
        with self.assertRaises(CorpusUnavailable):
            self.service.search("cadmium", sources=["pubmed"])
        self.old.errors.clear()
        self.assertTrue(self.service.search("cadmium", sources=["pubmed"])["hits"])
        self.local.errors["scientific"] = RetrievalTimeout("timeout")
        with self.assertRaises(RetrievalTimeout):
            self.service.search("cadmium", sources=["scientific"])

    def test_source_contract_violation_is_not_laundered_into_results(self):
        self.old.results["medrr"] = [hit("normative")]
        with self.assertRaises(CorpusUnavailable):
            self.service.search("cadmium", sources=["pubmed"])

    def test_queue_timeout_is_bounded_and_starts_no_query(self):
        self.service.queue_timeout_seconds = .01
        self.service.capacity.acquire()
        try:
            with self.assertRaisesRegex(RetrievalTimeout, "waiting for a BM25 search slot"):
                self.service.search("cadmium")
        finally:
            self.service.capacity.release()
        self.assertEqual(self.log, [])
        self.assertTrue(self.service.search("cadmium")["hits"])

    def test_shared_deadline_stops_later_partitions_without_mutating_child_timeout(self):
        now = [100.0]
        original_search = self.old.search
        def consumes_budget(*args, **kwargs):
            value = original_search(*args, **kwargs)
            now[0] += 9
            return value
        self.old.search = consumes_budget
        with patch.object(combined.time, "monotonic", side_effect=lambda: now[0]):
            result = self.service.search("cadmium")
        self.assertEqual(len(self.log), 1)
        self.assertEqual(self.log[0][5], 100 + self.service.timeout_seconds)
        self.assertTrue(result["partial"])
        self.assertEqual(result["diagnostics"]["failed_sources"], list(combined.LOCAL_SOURCES))
        self.assertEqual(self.old.timeout_seconds, 8)
        self.assertEqual(self.local.timeout_seconds, 8)

    def test_queue_wait_does_not_consume_sqlite_execution_budget(self):
        now = [100.0]
        def wait_for_slot(*, timeout):
            now[0] += 15.0
            return True
        with patch.object(self.service, "capacity") as capacity, \
             patch.object(combined.time, "monotonic", side_effect=lambda: now[0]):
            capacity.acquire.side_effect = wait_for_slot
            result = self.service.search("cadmium", sources=["pubmed"])
        self.assertEqual(result["diagnostics"]["queue_wait_ms"], 15000)
        self.assertEqual(result["diagnostics"]["elapsed_ms"], 0)
        self.assertEqual(self.log[0][5], 115 + self.service.timeout_seconds)

    def test_status_keeps_declared_old_count_separate_from_unknown_local_count(self):
        self.old.state.update(total_chunks=24139516, source_counts={"pubmed": 23902851}, counts_basis="fixture catalog")
        result = self.service.status()
        self.assertTrue(result["ready"])
        self.assertIsNone(result["total_chunks"])
        self.assertEqual(result["counts"]["medrr"]["total_chunks"], 24139516)
        self.assertIsNone(result["counts"]["local_evidence"]["total_chunks"])
        self.assertEqual(result["counts"]["local_evidence"]["source_counts"], dict.fromkeys(combined.LOCAL_SOURCES))
        self.assertFalse(result["channels"]["medcpt"]["ready"])
        self.local.state = {"ready": False, "databases": {"normative": {"ready": True}}}
        result = self.service.status()
        self.assertFalse(result["ready"])
        self.assertTrue(result["partial"])

    def test_constructor_and_explicit_factory_do_not_construct_hybrid_or_dense(self):
        with patch.object(combined, "CorpusRetrievalService", return_value=self.old) as corpus, \
             patch.object(combined, "LocalEvidenceRetrievalService", return_value=self.local) as local, \
             patch("app.services.rag_agent_service.HybridRetrievalService", side_effect=AssertionError("no hybrid")), \
             patch("app.services.medcpt_dense_service.MedcptDenseService", side_effect=AssertionError("no dense")), \
             patch.dict(os.environ, {"RAG_RETRIEVAL_BACKEND": "combined_bm25"}):
            service = create_retriever()
        self.assertIsInstance(service, combined.CombinedBm25RetrievalService)
        corpus.assert_called_once_with(medcpt_rerank=False, lexical_term_limit=None)
        local.assert_called_once_with(concurrency=service.search_concurrency)
        self.assertEqual({item["id"] for item in service.knowledge_bases}, set(combined.ALL_SOURCES))


class CombinedRealSqliteTests(unittest.TestCase):
    def setUp(self):
        # Reuse only tiny fixture setup/cleanup; no real corpus path is opened.
        from test_corpus_retrieval import CorpusFixture
        from test_local_evidence_retrieval import LocalEvidenceTests
        self.old = CorpusFixture()
        self.local = LocalEvidenceTests()
        self.old.setUp()
        self.local.setUp()
        self.old.service = CorpusRetrievalService(self.old.root, medcpt_rerank=False,
                                                  require_restore_receipt=False, lexical_term_limit=None)
        self.service = combined.CombinedBm25RetrievalService(self.old.service, self.local.service)

    def tearDown(self):
        self.local.tearDown()
        self.old.tearDown()

    def hashes(self):
        return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for root in (self.old.root, self.local.root)
                for path in root.rglob("*") if path.is_file()}

    def test_combined_real_bm25_works_without_writes_or_identifier_invention(self):
        before = self.hashes()
        self.assertTrue(self.service.status()["ready"])
        result = self.service.search("镉肾损伤", top_k=6, candidate_k=8)
        self.assertEqual({row["retrieval_partition"] for row in result["hits"]}, set(combined.PARTITIONS))
        selected = select_evidence(result["hits"], 6, result["diagnostics"]["query_terms"])
        context, cards = evidence_context(selected, 4000, result["diagnostics"]["query_terms"])
        self.assertTrue(context)
        self.assertTrue(cards)
        self.assertTrue(all(row["score"] < 0 and row["dense_score"] is None for row in result["hits"]))
        self.assertEqual(self.hashes(), before)

    def test_twenty_overlapping_requests_share_two_slots_and_keep_their_own_hits(self):
        with patch.dict(os.environ, {"RAG_BM25_SEARCH_CONCURRENCY": "2"}):
            service = combined.CombinedBm25RetrievalService(self.old.service, self.local.service)
        cases = [("cadmium kidney", ["pubmed", "scientific"]),
                 ("lead hypertension", ["pubmed", "normative"])] * 10
        def search(case):
            return service.search(case[0], sources=case[1])
        def signature(result):
            return [(hit["chunk_id"], hit["score"]) for hit in result["hits"]]
        expected = [signature(search(case)) for case in cases[:2]]
        self.assertNotEqual(expected[0], expected[1])

        ready = threading.Barrier(20, timeout=10)
        paired = threading.Barrier(2, timeout=5)
        original = self.old.service.search
        lock = threading.Lock()
        active = peak = 0
        def concurrent_query(*args, **kwargs):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            try:
                paired.wait()
                return original(*args, **kwargs)
            finally:
                with lock:
                    active -= 1
        def run(case):
            ready.wait()
            return search(case)
        with patch.object(self.old.service, "search", side_effect=concurrent_query):
            with ThreadPoolExecutor(max_workers=20) as pool:
                results = list(pool.map(run, cases))
        self.assertEqual(service.search_concurrency, 2)
        self.assertEqual(peak, 2)
        self.assertTrue(any(item["diagnostics"]["queue_wait_ms"] > 0 for item in results))
        for index, item in enumerate(results):
            self.assertEqual(item["diagnostics"]["search_state"], "complete")
            self.assertEqual(signature(item), expected[index % 2])

    def test_child_queries_enforce_request_deadlines_without_changing_config(self):
        for service, source in [(self.old.service, "pubmed"), (self.local.service, "scientific")]:
            with self.subTest(source=source):
                configured = service.timeout_seconds
                with self.assertRaises(RetrievalTimeout):
                    service.search("cadmium kidney", sources=[source], deadline=time.monotonic() - 1)
                self.assertEqual(service.timeout_seconds, configured)
                self.assertTrue(service.search("cadmium kidney", sources=[source])["hits"])

    def test_medrr_query_after_18th_term_is_not_truncated(self):
        query = ("cadmium kidney injury exposure blood pressure hypertension diabetes cancer anemia "
                 "osteoporosis cognition cardiovascular inflammation chelation pregnancy workers adults "
                 "without quazylophenezn42 children absent alpha beta")
        with patch.object(self.old.service, "_lexical_query", wraps=self.old.service._lexical_query) as lexical:
            result = self.service.search(query, sources=["pubmed"])
        terms = result["diagnostics"]["libraries"]["medrr"]["diagnostics"]["query_terms"]
        self.assertEqual(len(terms), 24)
        self.assertIn("without", terms)
        self.assertIn("quazylophenezn42", terms)
        self.assertIn("children", terms)
        self.assertIn("beta", terms)
        self.assertEqual(lexical.call_args_list[0].args[1], " AND ".join('"' + term + '"' for term in terms))
        self.assertEqual(lexical.call_count, 1)
        self.assertEqual(result["hits"], [])
        self.assertEqual(CorpusRetrievalService(self.old.root).lexical_term_limit, 18)

    def test_one_missing_local_database_is_partial_without_recreating_it(self):
        path = self.local.root / combined.DATABASES["scientific"][0]
        path.unlink()
        result = self.service.search("cadmium kidney", sources=["pubmed", "scientific"])
        self.assertTrue(result["partial"])
        self.assertFalse(path.exists())
        self.assertEqual({row["source"] for row in result["hits"]}, {"pubmed"})


if __name__ == "__main__":
    unittest.main()
