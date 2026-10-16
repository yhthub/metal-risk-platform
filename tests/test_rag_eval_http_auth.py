"""Real loopback HTTP auth checks. Ephemeral keys never leave process memory/headers.

The tiny server only returns synthetic retrieval JSON: no app, corpus or LLM import.
"""
import argparse
import hmac
import importlib.util
import json
import secrets
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, PROJECT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mechanical = load_script("rag_evaluate")
retrieval = load_script("rag_retrieval_evaluate")


@contextmanager
def loopback_server(key, *, sink_origin=None, echo_credentials=False):
    paths, observations = [], []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # No access logs, token dumps or request-body output.

        def respond(self, status, response, location=None):
            encoded = json.dumps(response).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            if location:
                self.send_header("Location", location)
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self):
            self.handle_request()

        def do_POST(self):
            self.handle_request()

        def handle_request(self):
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b"{}"
            paths.append(self.path)
            # Only presence flags are retained; do not store the actual Authorization token.
            authorized = hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {key}")
            observations.append({"authorized": authorized, "has_authorization": "Authorization" in self.headers,
                                 "has_legacy_header": "X-API-Key" in self.headers})
            if not authorized:
                self.respond(401, {"detail": "Access denied"})
                return
            if echo_credentials:
                self.respond(200, {"detail": self.headers.get("Authorization")})
                return
            if self.path.startswith("/redirect/"):
                _, _, scope, code = self.path.split("/")
                origin = sink_origin if scope == "cross" else f"http://127.0.0.1:{self.server.server_port}"
                self.respond(int(code), {"detail": "Redirect must not be followed"}, origin + "/redirect-target")
                return
            payload = json.loads(body)
            arm = payload.get("mode", "bm25")
            budget = payload.get("candidate_k", payload.get("top_k", 8))
            dense = arm in {"medcpt", "hybrid"}
            sparse = arm in {"bm25", "hybrid"}
            response = {"mode": "hybrid_medcpt_bm25" if arm == "hybrid" else arm,
                        "hits": [{"chunk_id": "synthetic/loopback", "content": "Synthetic retrieval text only",
                                  "source": "pubmed", "score": 1.0}],
                        "diagnostics": {"candidate_limit_per_channel": budget,
                                        "independent_dense_recall": dense, "dual_route_executed": arm == "hybrid",
                                        "channels": {"bm25": {"ready": sparse, "count": int(sparse)},
                                                     "medcpt": {"ready": dense, "count": int(dense),
                                                                "scope": "synthetic_loopback_only", "approximate": False,
                                                                "query_encoder_revision": "d83a36cc6b8e3a5c5e9d9d6ba156808c1643dcbc",
                                                                "query_max_length": 64}}}}
            self.respond(200, response)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", paths, observations
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class EvaluationHttpAuthTests(unittest.TestCase):
    def setUp(self):
        self.key = secrets.token_hex(32)  # In-memory only; no credentials are read.
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def client(self, which, origin, path, key):
        payload = {"query": "synthetic term", "mode": "bm25", "top_k": 1, "candidate_k": 1}
        if which == "mechanical":
            return mechanical.call_api(origin, path, payload, key, 2)
        return retrieval.call_retrieval(origin + path, payload, key, 2)

    def assert_no_key_in_output_files(self, key):
        for path in self.root.rglob("*"):
            if path.is_file():
                self.assertFalse(key.encode() in path.read_bytes(), f"Credential leaked into {path.name}")

    def test_both_clients_valid_missing_wrong_bearer_keys_over_real_http(self):
        wrong_key = secrets.token_hex(32)
        with loopback_server(self.key) as (origin, paths, observations):
            for which in ("mechanical", "retrieval"):
                for key, expected in ((self.key, 200), ("", 401), (wrong_key, 401)):
                    with self.subTest(client=which, auth_case=expected):
                        status, response, raw = self.client(which, origin, "/api/agent/evidence-search", key)
                        self.assertEqual(status, expected)
                        self.assertFalse(self.key in raw, "Service response contained a credential")
                        self.assertFalse(wrong_key in raw, "Service response contained a credential")
                        if expected == 200:
                            self.assertTrue(response["hits"])
                        else:
                            self.assertIn("detail", response)
            self.assertEqual(len(paths), 6)
            self.assertTrue(all(self.key not in path and wrong_key not in path for path in paths))
            self.assertFalse(any(row["has_legacy_header"] for row in observations))
            self.assertEqual(sum(row["authorized"] for row in observations), 2)
            self.assertEqual(sum(row["has_authorization"] for row in observations), 4)

    def test_no_client_follows_same_or_cross_origin_redirects(self):
        with loopback_server(self.key) as (sink, sink_paths, _):
            with loopback_server(self.key, sink_origin=sink) as (origin, paths, _):
                for which in ("mechanical", "retrieval"):
                    for scope in ("same", "cross"):
                        for code in (301, 302, 303, 307, 308):
                            with self.subTest(client=which, scope=scope, status=code):
                                status, _, raw = self.client(which, origin, f"/redirect/{scope}/{code}", self.key)
                                self.assertEqual(status, code)
                                self.assertFalse(self.key in raw, "Redirect response contained a credential")
                self.assertEqual(len(paths), 20)
                self.assertNotIn("/redirect-target", paths)
            self.assertEqual(sink_paths, [])

    def test_legacy_x_api_key_is_not_accepted_by_test_service(self):
        with loopback_server(self.key) as (origin, _, observations):
            request = urllib.request.Request(origin + "/api/agent/evidence-search", method="POST", data=b"{}",
                                             headers={"X-API-Key": self.key, "Content-Type": "application/json"})
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with self.assertRaises(urllib.error.HTTPError) as error:
                opener.open(request, timeout=2)
            self.assertEqual(error.exception.code, 401)
            self.assertEqual(observations, [{"authorized": False, "has_authorization": False, "has_legacy_header": True}])

    def test_implicit_environment_proxy_never_receives_request_or_key(self):
        with loopback_server(self.key) as (proxy, proxy_paths, _):
            with loopback_server(self.key) as (origin, paths, _):
                # Deliberately hostile proxy settings, process-local and restored after this block.
                with patch.dict("os.environ", {"http_proxy": proxy, "https_proxy": proxy, "HTTP_PROXY": proxy,
                                               "HTTPS_PROXY": proxy, "no_proxy": "", "NO_PROXY": ""}):
                    for which in ("mechanical", "retrieval"):
                        self.assertEqual(self.client(which, origin, "/api/agent/evidence-search", self.key)[0], 200)
                self.assertEqual(len(paths), 2)
            self.assertEqual(proxy_paths, [])

    def test_mechanical_runner_writes_raw_without_key_using_real_loopback(self):
        cases = self.root / "synthetic_cases.json"
        cases.write_text(json.dumps({"cases": [{"case_id": "loopback_only", "query": "synthetic term"}]}), encoding="utf-8")
        with loopback_server(self.key) as (origin, paths, _):
            args = argparse.Namespace(cases=cases, max_cases=1, integration=True, mode="retrieval", allow_model=False,
                                      base_url=origin, dry_run=False, run_dir=self.root / "mechanical_run", top_k=1, timeout=2)
            with patch.dict("os.environ", {"RAG_EVAL_API_KEY": self.key}):
                result = mechanical.run(args)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(paths, ["/api/agent/evidence-search"])
        raw = list(retrieval.read_jsonl(args.run_dir / "first_raw.jsonl"))
        self.assertEqual(raw[0]["http_status"], 200)
        self.assertNotIn("Authorization", raw[0]["request"])
        self.assert_no_key_in_output_files(self.key)

    def test_three_arm_runner_writes_raw_without_key_using_real_loopback(self):
        queries = self.root / "synthetic_queries.jsonl"
        queries.write_text('{"query_id":"loopback_only","query":"synthetic term"}\n', encoding="utf-8")
        with loopback_server(self.key) as (origin, paths, _):
            args = retrieval.build_parser().parse_args(["--queries", str(queries), "--integration", "--execute",
                                                       "--output", str(self.root / "retrieval_run"), "--base-url", origin,
                                                       "--api-key-env", "RAG_LOOPBACK_TEST_KEY", "--timeout", "2"])
            with patch.dict("os.environ", {"RAG_LOOPBACK_TEST_KEY": self.key}):
                result = retrieval.run(args)
            self.assertEqual(result["state"], "COMPLETE")
            self.assertEqual(len(paths), 3)
            for arm in retrieval.ARMS:
                self.assertEqual(result["summary"]["arms"][arm]["failed_attempts"], 0)
        raw = list(retrieval.read_jsonl(args.output / "first_raw.jsonl"))
        self.assertEqual(len(raw), 3)
        self.assertTrue(all(row["http_status"] == 200 for row in raw))
        self.assert_no_key_in_output_files(self.key)

    def test_redirect_is_failed_not_successful_mechanical_evaluation(self):
        result = mechanical.check_response({"detail": "Redirect refused"}, mode="retrieval", http_status=302)
        self.assertFalse(result["pass"])
        self.assertIn("expected_http_success", result["failed"])

    def test_echoed_credential_body_is_withheld_by_both_clients(self):
        with loopback_server(self.key, echo_credentials=True) as (origin, paths, _):
            for which in ("mechanical", "retrieval"):
                with self.subTest(client=which):
                    with self.assertRaises(OSError) as error:
                        self.client(which, origin, "/api/agent/evidence-search", self.key)
                    self.assertFalse(self.key in str(error.exception), "Failure message contained a credential")
            self.assertEqual(len(paths), 2)

    def test_runners_preserve_failed_attempt_without_sensitive_echo_body(self):
        cases = self.root / "echo_cases.json"
        cases.write_text(json.dumps({"cases": [{"case_id": "loopback_only", "query": "synthetic term"}]}), encoding="utf-8")
        queries = self.root / "echo_queries.jsonl"
        queries.write_text('{"query_id":"loopback_only","query":"synthetic term"}\n', encoding="utf-8")
        with loopback_server(self.key, echo_credentials=True) as (origin, paths, _):
            old_args = argparse.Namespace(cases=cases, max_cases=1, integration=True, mode="retrieval", allow_model=False,
                                          base_url=origin, dry_run=False, run_dir=self.root / "echo_mechanical", top_k=1, timeout=2)
            args = retrieval.build_parser().parse_args(["--queries", str(queries), "--integration", "--execute",
                                                       "--output", str(self.root / "echo_retrieval"), "--base-url", origin,
                                                       "--api-key-env", "RAG_LOOPBACK_TEST_KEY", "--timeout", "2"])
            with patch.dict("os.environ", {"RAG_EVAL_API_KEY": self.key, "RAG_LOOPBACK_TEST_KEY": self.key}):
                old_result = mechanical.run(old_args)
                result = retrieval.run(args)
            self.assertEqual(old_result["failed"], 1)
            self.assertEqual(old_result["status"], "FAIL")
            self.assertEqual(len(paths), 4)  # No retries after withholding a sensitive body.
            for arm in retrieval.ARMS:
                self.assertEqual(result["summary"]["arms"][arm]["failed_attempts"], 1)
        old_raw = list(retrieval.read_jsonl(old_args.run_dir / "first_raw.jsonl"))
        self.assertEqual(old_raw[0]["error_type"], "OSError")
        self.assertIsNone(old_raw[0]["raw_body"])
        new_raw = list(retrieval.read_jsonl(args.output / "first_raw.jsonl"))
        self.assertTrue(all(row["error"] == "transport_error_no_retry" for row in new_raw))
        self.assertTrue(all("raw_http_body" not in row for row in new_raw))
        self.assert_no_key_in_output_files(self.key)


if __name__ == "__main__":
    unittest.main()
