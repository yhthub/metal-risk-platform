"""True two-path orchestration on a tiny CLOSED fixture, no production scans."""
import copy
import math
import unittest
from unittest.mock import patch
import test_corpus_retrieval as corpus_fixtures
from app.services.corpus_retrieval_service import CorpusUnavailable
from app.services.hybrid_retrieval_service import HybridRetrievalService, reciprocal_rank_fusion, common_query


class FixtureDense:
    def __init__(self, ready=True):
        self.ready, self.calls, self.error = ready, [], None

    def status(self):
        return {"ready": self.ready, "scope": "tiny_fixture_full_axis", "error": "fixture index missing"}

    def search(self, query, top_k, sources):
        self.calls.append((query, top_k, sources))
        if self.error:
            raise self.error
        return {"hits": [{"row_index": 2, "dense_score": 17.5, "dense_rank": 1}],
                "mode": "fixture_exact", "diagnostics": {"scope": "tiny_fixture_full_axis"}}


class HybridTests(unittest.TestCase):
    def setUp(self):
        self.fixture = corpus_fixtures.CorpusFixture()
        self.fixture.setUp()
        self.dense = FixtureDense()
        self.service = HybridRetrievalService(self.fixture.service, self.dense, allow_degraded=False)
        self.service.mode = "hybrid"

    def tearDown(self):
        self.service._pool.shutdown(wait=True)
        self.fixture.tearDown()

    def test_dense_can_recall_document_absent_from_bm25(self):
        result = self.service.search("lead", candidate_k=2, top_k=3)
        self.assertEqual(result["mode"], "hybrid_medcpt_bm25")
        self.assertTrue(result["diagnostics"]["independent_dense_recall"])
        self.assertEqual([hit["row_index"] for hit in result["sparse_hits"]], [1])
        self.assertEqual([hit["row_index"] for hit in result["dense_hits"]], [2])
        self.assertEqual({hit["row_index"] for hit in result["hits"]}, {1, 2})
        self.assertEqual(result["dense_hits"][0]["dense_score"], 17.5)
        self.assertIsNone(result["dense_hits"][0]["pmid"])

    def test_same_query_and_source_filters_sent_to_both_paths(self):
        with patch.object(self.fixture.service, "search", wraps=self.fixture.service.search) as sparse:
            result = self.service.search("职业铅暴露", candidate_k=32, sources=["textbooks"])
        self.assertEqual(sparse.call_args.args[0], self.dense.calls[0][0])
        self.assertEqual(sparse.call_args.args[3], self.dense.calls[0][2])
        self.assertEqual(result["diagnostics"]["candidate_limit_per_channel"], 32)

    def test_missing_dense_fails_before_sparse_or_encoding(self):
        self.dense.ready = False
        with patch.object(self.fixture.service, "search", side_effect=AssertionError("No query")):
            with self.assertRaises(CorpusUnavailable):
                self.service.search("lead")
        self.assertEqual(self.dense.calls, [])

    def test_explicit_degraded_mode_is_honest(self):
        self.dense.ready = False
        self.service.allow_degraded = True
        result = self.service.search("lead")
        self.assertEqual(result["mode"], "bm25_degraded")
        self.assertTrue(result["degraded"])
        self.assertFalse(result["diagnostics"]["independent_dense_recall"])
        self.assertTrue(result["diagnostics"]["warnings"])

    def test_dense_transport_error_does_not_silently_become_sparse(self):
        self.dense.error = CorpusUnavailable("fixture failure")
        with self.assertRaises(CorpusUnavailable):
            self.service.search("lead")
        self.dense.error = None
        self.assertEqual(self.service.search("lead")["mode"], "hybrid_medcpt_bm25")

    def test_explicit_bm25_arm_does_not_call_dense(self):
        self.dense.ready = False
        result = self.service.search("lead", mode="bm25")
        self.assertEqual(result["mode"], "bm25")
        self.assertFalse(result["degraded"])
        self.assertEqual(self.dense.calls, [])

    def test_medcpt_arm_never_queries_bm25(self):
        with patch.object(self.fixture.service, "search", side_effect=AssertionError("No BM25")):
            result = self.service.search("lead", mode="medcpt")
        self.assertEqual(result["mode"], "medcpt")
        self.assertEqual(result["sparse_hits"], [])

    def test_dense_wrong_row_axis_fails(self):
        with patch.object(self.dense, "search", return_value={"hits": [
                {"row_index": 999, "dense_score": 1, "dense_rank": 1}]}):
            with self.assertRaises(CorpusUnavailable):
                self.service.search("lead")

    def test_busy_retrieval_is_bounded(self):
        self.service.capacity.acquire()
        try:
            with self.assertRaises(CorpusUnavailable):
                self.service.search("lead")
        finally:
            self.service.capacity.release()

    def test_document_lookup_validation(self):
        self.assertEqual([hit["row_index"] for hit in self.fixture.service.documents([2, 0])], [2, 0])
        for values in ([True], [-1], [0] * 257):
            with self.assertRaises(ValueError):
                self.fixture.service.documents(values)

    def test_rrf_is_rank_based_not_raw_score_addition(self):
        sparse = [{"row_index": 1, "chunk_id": "a", "score": -99999},
                  {"row_index": 2, "chunk_id": "b", "score": -0.1}]
        dense = [{"row_index": 2, "chunk_id": "b", "dense_score": 999999},
                 {"row_index": 1, "chunk_id": "a", "dense_score": 0.01}]
        hits = reciprocal_rank_fusion(sparse, dense)
        self.assertEqual([hit["chunk_id"] for hit in hits], ["a", "b"])
        self.assertAlmostEqual(hits[0]["rrf_score"], 1/61 + 1/62)
        self.assertEqual(hits[0]["retrieval_channels"], ["bm25", "medcpt"])
        self.assertEqual(hits[0]["score_type"], "rrf_rank_fusion_not_probability")

    def test_duplicate_same_channel_does_not_accumulate_votes(self):
        item = {"row_index": 1, "chunk_id": "a", "score": -1}
        hits = reciprocal_rank_fusion([item, copy.deepcopy(item)], [])
        self.assertEqual(len(hits), 1)
        self.assertAlmostEqual(hits[0]["rrf_score"], 1/61)

    def test_conflicting_identity_and_invalid_weights_rejected(self):
        with self.assertRaises(CorpusUnavailable):
            reciprocal_rank_fusion([{"row_index": 1, "chunk_id": "a"}], [{"row_index": 1, "chunk_id": "b"}])
        for weight in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                reciprocal_rank_fusion([], [], dense_weight=weight)

    def test_english_query_is_not_lossily_rewritten(self):
        text = "Does cadmium cause kidney damage?"
        self.assertEqual(common_query(text)[0], text)

    def test_status_requires_independent_dense_readiness(self):
        self.dense.ready = False
        status = self.service.status()
        self.assertTrue(status["corpus_ready"])
        self.assertFalse(status["ready"])
        self.assertFalse(status["channels"]["medcpt"]["ready"])
