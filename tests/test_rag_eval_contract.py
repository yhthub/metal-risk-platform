"""Offline evaluator contract tests. No model, network, or clinical corpus is accessed."""
import argparse
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rag_evaluate", ROOT / "scripts" / "rag_evaluate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
FIXTURES = json.loads(module.FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]


class RagEvaluationContractTests(unittest.TestCase):
    def test_all_synthetic_contract_fixtures_pass(self):
        for item in FIXTURES:
            with self.subTest(case=item["case_id"]):
                result = module.check_response(item["synthetic_response"], expected_status=item["fixture_expected_status"],
                                               forbidden_literals=item.get("forbidden_literals"))
                self.assertTrue(result["pass"], result)

    def test_fabricated_reference_fails(self):
        response = copy.deepcopy(FIXTURES[0]["synthetic_response"])
        response["answer"] += " [E999]"
        self.assertIn("no_unresolved_citation_markers", module.check_response(response)["failed"])

    def test_citation_not_from_evidence_fails(self):
        response = copy.deepcopy(FIXTURES[0]["synthetic_response"])
        response["citations"][0]["chunk_id"] = "FABRICATED"
        self.assertIn("citations_are_from_returned_evidence", module.check_response(response)["failed"])

    def test_empty_evidence_cannot_answer(self):
        response = copy.deepcopy(FIXTURES[0]["synthetic_response"])
        response["evidence_cards"] = []
        self.assertIn("no_evidence_abstains", module.check_response(response)["failed"])

    def test_injection_canary_fails(self):
        response = copy.deepcopy(FIXTURES[0]["synthetic_response"])
        response["answer"] += " INJECTED_SECRET_CANARY"
        result = module.check_response(response, forbidden_literals=["INJECTED_SECRET_CANARY"])
        self.assertIn("forbidden_literal_not_emitted", result["failed"])

    def test_http_error_is_not_success(self):
        result = module.check_response({"detail": "model unavailable"}, http_status=503)
        self.assertFalse(result["pass"])

    def test_error_traceback_fails(self):
        result = module.check_response({"detail": "Traceback (most recent call last)"}, http_status=500)
        self.assertFalse(result["checks"]["error_does_not_expose_credentials_or_traceback"])

    def test_retrieval_duplicate_chunks_fail(self):
        result = module.check_response({"top_ranked": [{"chunk_id": "1", "text": "x"}] * 2}, mode="retrieval")
        self.assertIn("retrieval_unique_chunks", result["failed"])

    def test_current_hits_schema_requires_actual_content(self):
        result = module.check_response({"hits": [{"chunk_id": "1", "content": "actual excerpt"}]}, mode="retrieval")
        self.assertTrue(result["pass"])
        result = module.check_response({"hits": [{"chunk_id": "1"}]}, mode="retrieval")
        self.assertIn("retrieval_traceability", result["failed"])

    def test_echoed_query_canary_is_not_generated_answer(self):
        response = copy.deepcopy(FIXTURES[1]["synthetic_response"])
        response["retrieval"]["query"] = "INJECTED_SECRET_CANARY"
        result = module.check_response(response, forbidden_literals=["INJECTED_SECRET_CANARY"])
        self.assertTrue(result["pass"])

    def test_integration_chat_requires_explicit_model_gate(self):
        args = self.arguments(Path("unused"))
        args.integration = True
        with self.assertRaisesRegex(ValueError, "allow-model"):
            module.run(args)

    def test_first_raw_is_preserved_and_rerun_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "first_run"
            args = self.arguments(target)
            summary = module.run(args)
            self.assertEqual(summary["status"], "PASS")
            original = (target / "first_raw.jsonl").read_bytes()
            self.assertEqual(len(original.decode().splitlines()), 4)
            with self.assertRaises(FileExistsError):
                module.run(args)
            self.assertEqual(original, (target / "first_raw.jsonl").read_bytes())

    def test_dry_run_creates_no_files(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "not_created"
            args = self.arguments(target)
            args.dry_run = True
            self.assertEqual(module.run(args)["scope"], "plan_only_no_requests_no_files")
            self.assertFalse(target.exists())

    @staticmethod
    def arguments(target):
        return argparse.Namespace(cases=module.FIXTURE_PATH, max_cases=4, integration=False, mode="chat",
                                  allow_model=False, base_url="http://127.0.0.1:8000", run_dir=target,
                                  timeout=1, top_k=8, dry_run=False)


if __name__ == "__main__":
    unittest.main()
