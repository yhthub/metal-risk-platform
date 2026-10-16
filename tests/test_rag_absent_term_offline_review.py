"""Offline saved-record checks only: never run the real corpus/model branch."""
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("absent_term_review", PROJECT / "scripts" / "verify_rag_absent_term.py")
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


def synthetic_record():
    return {"state": "FAIL", "attempt": 1, "http_status": 200, "elapsed_seconds": 0.047,
            "checks": {"http_200": True, "explicit_abstention": True, "no_model_calls": True,
                       "no_evidence_or_citations": True, "missing_term_diagnostic": False,
                       "source_identity_unchanged": True},
            "response": {"status": "insufficient_evidence", "model": {"invoked": False},
                         "evidence_cards": [], "citations": [], "retrieval": {
                             "mode": "bm25", "query": review.ABSENT_QUERY, "diagnostics": {
                             "channels": {"bm25": {"missing_lexical_terms": [review.ABSENT_TERM]}}}}}}


class AbsentTermOfflineReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "original.json"
        self.output = self.root / "review.json"
        self.original = synthetic_record()
        self.source.write_text(json.dumps(self.original), encoding="utf-8")
        self.original_bytes = self.source.read_bytes()

    def tearDown(self):
        self.temp.cleanup()

    def test_correct_nested_diagnostic_passes_without_replacing_original_fail(self):
        result = review.review_record(self.source, self.output)
        self.assertEqual(result["state"], "OFFLINE_REVIEW_PASS")
        self.assertEqual(result["source_record"]["original_state"], "FAIL")
        self.assertEqual(result["source_record"]["attempt"], 1)
        self.assertEqual(result["source_record"]["sha256"], hashlib.sha256(self.original_bytes).hexdigest())
        self.assertEqual(result["changed_check_values"], ["missing_term_diagnostic"])
        self.assertEqual(result["review_activity"], {"corpus_requests": 0, "model_calls": 0, "runtime_replayed": False})
        self.assertFalse(result["original_checks"]["missing_term_diagnostic"])
        self.assertEqual(self.source.read_bytes(), self.original_bytes)

    def test_old_top_level_path_is_not_accepted_and_missing_list_is_strict(self):
        response = self.original["response"]
        response["retrieval"]["diagnostics"] = {"missing_lexical_terms": [review.ABSENT_TERM]}
        self.assertFalse(review.has_missing_term(response))
        for bad in (review.ABSENT_TERM, None, {}, ["another-token"]):
            response["retrieval"]["diagnostics"] = {"channels": {"bm25": {"missing_lexical_terms": bad}}}
            self.assertFalse(review.has_missing_term(response))

    def test_runtime_assertions_are_not_invented_from_the_saved_response(self):
        self.original["checks"].pop("source_identity_unchanged")
        self.original["checks"]["no_model_calls"] = False
        self.source.write_text(json.dumps(self.original), encoding="utf-8")
        result = review.review_record(self.source, self.output)
        self.assertEqual(result["state"], "OFFLINE_REVIEW_FAIL")
        self.assertFalse(result["checks"]["source_identity_unchanged"])
        self.assertFalse(result["checks"]["no_model_calls"])

    def test_review_refuses_other_attempt_mode_or_query_without_writing(self):
        for mismatch in ("attempt", "mode", "query"):
            with self.subTest(mismatch=mismatch):
                record = synthetic_record()
                if mismatch == "attempt":
                    record["attempt"] = 2
                else:
                    record["response"]["retrieval"][mismatch] = "other"
                self.source.write_text(json.dumps(record), encoding="utf-8")
                before = self.source.read_bytes()
                with self.assertRaises(ValueError):
                    review.review_record(self.source, self.output)
                self.assertFalse(self.output.exists())
                self.assertEqual(self.source.read_bytes(), before)

    def test_output_is_exclusive_and_cannot_be_the_source(self):
        self.output.write_text("first review", encoding="utf-8")
        with self.assertRaises(ValueError):
            review.review_record(self.source, self.output)
        with self.assertRaises(ValueError):
            review.review_record(self.source, self.source)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "first review")
        self.assertEqual(self.source.read_bytes(), self.original_bytes)

    def test_cli_offline_branch_never_creates_key_or_imports_backend(self):
        real_import = __import__

        def reject_runtime_import(name, *args, **kwargs):
            if name.split(".")[0] in {"app", "fastapi", "requests", "ollama"}:
                raise AssertionError("Offline review imported a runtime dependency")
            return real_import(name, *args, **kwargs)

        with patch.object(review.secrets, "token_hex", side_effect=AssertionError("Offline review created a key")), \
                patch("builtins.__import__", side_effect=reject_runtime_import), redirect_stdout(io.StringIO()):
            exit_code = review.main(["--review-record", str(self.source), "--output", str(self.output)])
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.source.read_bytes(), self.original_bytes)

    def test_execute_and_review_flags_are_mutually_exclusive(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            review.main(["--execute", "--review-record", str(self.source), "--output", str(self.output)])
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
