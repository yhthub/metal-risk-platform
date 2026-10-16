"""Smoke runner unit tests use synthetic transport only; no corpus/model/network calls."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "rag_ollama_smoke.py"
SPEC = importlib.util.spec_from_file_location("rag_ollama_smoke", SCRIPT)
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


class FakeResponse:
    def __init__(self, status, value):
        self.status_code, self.value = status, value
        self.text = json.dumps(value)

    def json(self):
        return copy.deepcopy(self.value)


class FakeClient:
    def __init__(self, *, ready=True, mode="bm25", positive_http=200, echo_token=False):
        self.ready, self.mode = ready, mode
        self.positive_http, self.echo_token = positive_http, echo_token
        self.posts = []

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False

    def get(self, path, headers=None):
        if (headers or {}).get("Authorization") != "Bearer " + os.environ["RAG_API_KEY"]:
            return FakeResponse(401, {"detail": "Synthetic unauthorized"})
        return FakeResponse(200, {"status": "ready" if self.ready else "not_ready",
            "retrieval": {"mode": self.mode, "degraded": False}})

    def post(self, path, headers=None, json=None):
        self.posts.append(copy.deepcopy(json))
        positive = json["message"] == smoke.CASES[0]["query"]
        if positive and self.positive_http != 200:
            return FakeResponse(self.positive_http, {"detail": "Synthetic local generation failure"})
        response = {"status": "answered" if positive else "insufficient_evidence",
            "answer": "Synthetic excerpt statement [E1]." if positive else "No anchored excerpts.",
            "citations": [{"id": "E1", "chunk_id": "fixture/one", "source": "pubmed", "title": "Synthetic title"}] if positive else [],
            "evidence_cards": [{"chunk_id": "fixture/one"}] if positive else [],
            "model": {"name": "llama3.1:8b", "reported_name": "llama3.1:8b", "backend": "ollama_native", "invoked": positive},
            "retrieval": {"mode": "bm25", "degraded": False}}
        if positive and self.echo_token:
            response["answer"] = os.environ["RAG_API_KEY"]
        return FakeResponse(200, response)


class OllamaSmokeRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.output = self.root / "new-run"
        self.corpus = self.root / "independent-corpus"

    def tearDown(self):
        self.temp.cleanup()

    def args(self, *extra):
        return smoke.build_parser().parse_args(["--run-dir", str(self.output), "--corpus-root", str(self.corpus), *extra])

    def execute(self, client, mode="bm25"):
        source = {"total_chunks": smoke.EXPECTED_TOTAL_CHUNKS, "closed_snapshot_verified": True, "identity": "synthetic_only"}
        with patch.dict(os.environ), patch.object(smoke, "make_client", return_value=client), \
             patch.object(smoke, "source_receipt", return_value=source), \
             patch.object(smoke, "resource_snapshot", return_value={"synthetic": True}):
            return smoke.run(self.args("--execute", "--retrieval-mode", mode))

    def test_default_plan_has_no_requests_environment_or_output(self):
        before = dict(os.environ)
        with patch.object(smoke, "make_client", side_effect=AssertionError("No requests")), \
             patch.object(smoke, "resource_snapshot", side_effect=AssertionError("No resources")):
            result = smoke.run(self.args())
        self.assertEqual(result["state"], "PLAN_ONLY")
        self.assertEqual(result["retrieval_mode"], "hybrid")
        self.assertFalse(result["automatic_degradation"])
        self.assertFalse(self.output.exists())
        self.assertEqual(before, dict(os.environ))

    def test_origins_reject_cloud_credentials_path_query_and_other_port(self):
        for origin in ("https://example.com", "http://127.0.0.1:11434/v1", "http://u:p@127.0.0.1:11434",
                       "http://127.0.0.1:11434?x=1", "http://127.0.0.1:11434#x", "http://127.0.0.1:8000"):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                smoke.run(self.args("--origin", origin))
        self.assertFalse(self.output.exists())

    def test_existing_generation_is_not_overwritten(self):
        self.output.mkdir()
        marker = self.output / "original.txt"
        marker.write_text("Preserve first run", encoding="utf-8")
        with self.assertRaises(ValueError):
            smoke.run(self.args("--execute"))
        self.assertEqual(marker.read_text(encoding="utf-8"), "Preserve first run")

    def test_output_cannot_write_into_corpus_or_its_ancestor(self):
        for target in (self.corpus, self.corpus / "run", self.root):
            with self.subTest(target=str(target)), self.assertRaises(ValueError):
                smoke.run(self.args("--run-dir", str(target)))

    def test_frozen_model_id_cannot_be_switched(self):
        with self.assertRaises(ValueError):
            smoke.run(self.args("--model", "qwen2.5:7b"))

    def test_two_first_attempts_keep_raw_and_mechanical_scope(self):
        client = FakeClient()
        result = self.execute(client)
        self.assertEqual(result["state"], "PASS")
        self.assertEqual(result["passed"], 2)
        self.assertEqual(len(client.posts), 2)
        self.assertEqual(result["retrieval_scope"], "BM25-only/full_closed_corpus")
        self.assertEqual(result["request_transport"], "in_process_TestClient_not_socket")
        records = [json.loads(line) for line in (self.output / "first_raw.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertTrue(all(row["attempt"] == 1 and row["raw_body"] for row in records))
        self.assertFalse(records[1]["response"]["model"]["invoked"])
        self.assertEqual(result["clinical_accuracy"], "NOT_EVALUATED")

    def test_failed_positive_http_is_preserved_and_not_retried(self):
        client = FakeClient(positive_http=503)
        result = self.execute(client)
        self.assertEqual(result["state"], "FAIL")
        self.assertEqual(len(client.posts), 2)
        self.assertEqual(result["results"][0]["http_status"], 503)
        self.assertTrue(result["results"][1]["pass"])

    def test_hybrid_not_ready_never_automatically_degrades_or_chats(self):
        client = FakeClient(ready=False, mode="hybrid")
        result = self.execute(client, "hybrid")
        self.assertEqual(result["state"], "FAIL")
        self.assertEqual(client.posts, [])
        self.assertFalse((self.output / "first_raw.jsonl").exists())
        self.assertFalse(result["automatic_degradation"])

    def test_credential_echo_is_not_saved_and_has_no_retry(self):
        client = FakeClient(echo_token=True)
        with patch.dict(os.environ):
            result = self.execute(client)
        first = json.loads((self.output / "first_raw.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(result["state"], "FAIL")
        self.assertIsNone(first["raw_body"])
        self.assertIsNone(first["response"])
        self.assertEqual(first["error_type"], "ValueError")
        self.assertEqual(len(client.posts), 2)


if __name__ == "__main__":
    unittest.main()
