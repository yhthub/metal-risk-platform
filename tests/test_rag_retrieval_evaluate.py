"""Synthetic unit checks only: no real corpus, model, network or medical gold."""
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "rag_retrieval_evaluate.py"
SPEC = importlib.util.spec_from_file_location("retrieval_evaluate", SCRIPT)
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


class RetrievalEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.queries = self.root / "queries.jsonl"
        self.queries.write_text('{"query_id":"synthetic_q1","query":"synthetic term"}\n', encoding="utf-8")
        self.output = self.root / "new_run"

    def tearDown(self):
        self.temp.cleanup()

    def args(self, *extra):
        return evaluation.build_parser().parse_args(["--queries", str(self.queries), "--output", str(self.output), *extra])

    def response(self, arm, identifiers=None, count=None):
        per_route = 16 if arm == "hybrid" else 32
        return {"mode": "hybrid_medcpt_bm25" if arm == "hybrid" else arm,
                "hits": [{"chunk_id": identifier, "score": 1.0, "source": "pubmed"} for identifier in (identifiers or ["synthetic/a", "synthetic/b"])],
                "diagnostics": {"candidate_limit_per_channel": per_route,
                                "independent_dense_recall": arm != "bm25", "dual_route_executed": arm == "hybrid",
                                "channels": {"bm25": {"count": count if count is not None else 2, "ready": arm != "medcpt"},
                                             "medcpt": {"count": 2, "ready": arm != "bm25", "scope": "synthetic_fixture",
                                                        "approximate": False, "query_max_length": 64,
                                                        "query_encoder_revision": "d83a36cc6b8e3a5c5e9d9d6ba156808c1643dcbc"}}}}

    def rankings(self, failed_arm=None):
        path = self.root / "rankings.jsonl"
        records = [{"query_id": "synthetic_q1", "query": "synthetic term", "arm": arm,
                    "candidate_k": 16 if arm == "hybrid" else 32, "top_k": 8,
                    "response": self.response(arm), "http_status": 503 if arm == failed_arm else 200,
                    "elapsed_seconds": 0.2, "source_marker": "first_original"} for arm in evaluation.ARMS]
        path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
        return path, records

    def test_plan_only_does_not_request_or_write(self):
        with patch.object(evaluation, "call_retrieval", side_effect=AssertionError("Network forbidden")):
            result = evaluation.run(self.args("--integration"))
        self.assertEqual(result["state"], "PLAN_ONLY")
        self.assertEqual(result["total_candidate_capacity"], dict.fromkeys(evaluation.ARMS, 32))
        self.assertFalse(self.output.exists())

    def test_total_vs_per_channel_budgets(self):
        self.assertEqual(evaluation.budgets("total", 32, 8), {"bm25": 32, "medcpt": 32, "hybrid": 16})
        self.assertEqual(evaluation.budgets("per_channel", 32, 8)["hybrid"], 32)
        for value in (15, 14, 129):
            with self.assertRaises(ValueError):
                evaluation.budgets("total", value, 8)

    def test_metric_known_formula(self):
        result = evaluation.ranking_metrics(["synthetic/b", "synthetic/c", "synthetic/a"],
                                            {"synthetic/a": 3, "synthetic/b": 1, "synthetic/x": 0}, 3)
        self.assertEqual(result["recall_at_k"], 1)
        self.assertEqual(result["rr_at_k"], 1)
        expected = (1 + 7 / math.log2(4)) / (7 + 1 / math.log2(3))
        self.assertAlmostEqual(result["ndcg_at_k"], expected)
        self.assertEqual(result["unjudged_retrieved"], 1)
        self.assertEqual(result["unjudged_policy"], "zero_for_metrics_not_a_negative_label")

    def test_missing_or_no_positive_qrels_never_fake_zero(self):
        for judgments in (None, {}, {"synthetic/a": 0}):
            result = evaluation.ranking_metrics(["synthetic/a"], judgments, 8)
            self.assertEqual(result["status"], "NOT_EVALUATED")
            self.assertNotIn("recall_at_k", result)

    def test_no_relevant_retrieved_is_zero_only_with_positive_qrels(self):
        result = evaluation.ranking_metrics([], {"synthetic/a": 1}, 8)
        self.assertEqual(result["recall_at_k"], 0)
        self.assertEqual(result["rr_at_k"], 0)
        self.assertEqual(result["ndcg_at_k"], 0)

    def test_duplicate_and_nonfinite_rankings_rejected(self):
        with self.assertRaises(ValueError):
            evaluation.validate_response(self.response("bm25", ["synthetic/a", "synthetic/a"]), "bm25", 32, 8)
        response = self.response("medcpt")
        response["hits"][0]["score"] = float("nan")
        with self.assertRaises(ValueError):
            evaluation.validate_response(response, "medcpt", 32, 8)

    def test_degraded_and_wrong_arm_rejected(self):
        response = self.response("hybrid")
        response["degraded"] = True
        with self.assertRaises(ValueError):
            evaluation.validate_response(response, "hybrid", 16, 8)
        with self.assertRaises(ValueError):
            evaluation.validate_response(self.response("bm25"), "hybrid", 16, 8)

    def test_actual_candidate_counts_cannot_exceed_budget(self):
        with self.assertRaises(ValueError):
            evaluation.validate_response(self.response("hybrid", count=17), "hybrid", 16, 8)

    def test_mode_name_alone_never_proves_dual_execution(self):
        for flag in ("independent_dense_recall", "dual_route_executed"):
            response = self.response("hybrid")
            response["diagnostics"].pop(flag)
            with self.assertRaises(ValueError):
                evaluation.validate_response(response, "hybrid", 16, 8)
        for channel in ("bm25", "medcpt"):
            response = self.response("hybrid")
            response["diagnostics"]["channels"][channel]["ready"] = False
            with self.assertRaises(ValueError):
                evaluation.validate_response(response, "hybrid", 16, 8)
        response = self.response("medcpt")
        response["diagnostics"]["independent_dense_recall"] = False
        with self.assertRaises(ValueError):
            evaluation.validate_response(response, "medcpt", 32, 8)

    def test_filtered_sources_are_validated_for_hits_and_channels(self):
        response = self.response("hybrid")
        evaluation.validate_response(response, "hybrid", 16, 8, ["pubmed"])
        with self.assertRaises(ValueError):
            evaluation.validate_response(response, "hybrid", 16, 8, ["textbooks"])
        response["diagnostics"]["channels"]["medcpt"]["sources"] = ["textbooks"]
        with self.assertRaises(ValueError):
            evaluation.validate_response(response, "hybrid", 16, 8, ["pubmed"])

    def test_queries_exclude_answers_and_preserve_unicode_separator(self):
        self.queries.write_text('{"query_id":"q1","query":"first\u2029second"}\n', encoding="utf-8-sig")
        self.assertEqual(len(evaluation.load_queries(self.queries, 1)), 1)
        self.queries.write_text('{"query_id":"q1","query":"text","answer":"forbidden"}\n', encoding="utf-8")
        with self.assertRaises(ValueError):
            evaluation.load_queries(self.queries, 1)

    def test_qrels_duplicates_and_unknown_queries_rejected(self):
        path = self.root / "qrels.tsv"
        for text in ("q1\t0\tsynthetic/a\t1\nq1\t0\tsynthetic/a\t1\n", "other\tsynthetic/a\t1\n"):
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(ValueError):
                evaluation.load_qrels(path, {"q1"})

    def test_qrels_three_or_four_columns(self):
        path = self.root / "qrels.tsv"
        path.write_text("q1\t0\tsynthetic/a\t3\nq1\tsynthetic/b\t1\n", encoding="utf-8")
        self.assertEqual(evaluation.load_qrels(path, {"q1"}), {"q1": {"synthetic/a": 3.0, "synthetic/b": 1.0}})

    def test_offline_no_qrels_preserves_original_and_refuses_overwrite(self):
        path, original = self.rankings()
        with patch.object(evaluation, "call_retrieval", side_effect=AssertionError("Network forbidden")):
            result = evaluation.run(self.args("--rankings", str(path), "--execute"))
        self.assertEqual(result["state"], "COMPLETE")
        raw = list(evaluation.read_jsonl(self.output / "first_raw.jsonl"))
        self.assertEqual(raw[0]["source_raw"], original[0])
        self.assertEqual(result["summary"]["paired_denominator"], 0)
        for arm in evaluation.ARMS:
            self.assertIsNone(result["summary"]["arms"][arm]["mrr_at_k"])
        prior = (self.output / "first_raw.jsonl").read_bytes()
        with self.assertRaises(FileExistsError):
            evaluation.run(self.args("--rankings", str(path), "--execute"))
        self.assertEqual((self.output / "first_raw.jsonl").read_bytes(), prior)

    def test_failed_attempt_is_preserved_excluded_from_paired_quality(self):
        path, original = self.rankings("medcpt")
        qrels = self.root / "qrels.tsv"
        qrels.write_text("synthetic_q1\tsynthetic/a\t1\n", encoding="utf-8")
        result = evaluation.run(self.args("--rankings", str(path), "--qrels", str(qrels), "--execute"))
        summary = result["summary"]
        self.assertEqual(summary["arms"]["medcpt"]["failed_attempts"], 1)
        self.assertEqual(summary["paired_denominator"], 0)
        failed_raw = [row for row in evaluation.read_jsonl(self.output / "first_raw.jsonl") if row["arm"] == "medcpt"][0]
        self.assertEqual(failed_raw["source_raw"], original[1])

    def test_cache_mismatch_and_repeated_attempts_rejected(self):
        path, original = self.rankings()
        original[0]["query"] = "different text"
        path.write_text("".join(json.dumps(row) + "\n" for row in original), encoding="utf-8")
        with self.assertRaises(ValueError):
            evaluation.run(self.args("--rankings", str(path)))
        path, original = self.rankings()
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(original[0]) + "\n")
        with self.assertRaises(ValueError):
            evaluation.run(self.args("--rankings", str(path)))

    def test_cached_source_filter_must_match(self):
        path, records = self.rankings()
        records[0]["request"] = {"sources": ["pubmed"]}
        path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
        with self.assertRaises(ValueError):
            evaluation.run(self.args("--rankings", str(path)))

    def test_nonstandard_json_number_rejected(self):
        self.queries.write_text('{"query_id":"q1","query":NaN}\n', encoding="utf-8")
        with self.assertRaises(ValueError):
            evaluation.load_queries(self.queries, 1)

    def test_remote_plaintext_and_credential_urls_forbidden(self):
        self.assertEqual(evaluation.integration_url("http://127.0.0.1:8000", False),
                         "http://127.0.0.1:8000/api/agent/evidence-search")
        for url in ("http://8.148.158.242", "https://user:secret@example.com", "https://example.com/path",
                    "https://example.com?key=secret"):
            with self.assertRaises(ValueError):
                evaluation.integration_url(url, True)
        with self.assertRaises(ValueError):
            evaluation.integration_url("https://example.com", False)

    def test_unconfigured_execute_requires_explicit_mode(self):
        with self.assertRaises(ValueError):
            evaluation.run(self.args("--execute"))
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
