"""Actual ApiGuard + loopback HTTP integration, not retrieval/model validation.

The app has one synthetic endpoint; it never imports app.main or any service.
Temporary access keys exist only in memory/headers; no RAW or key files are made.
"""
import importlib.util
import logging
import os
import secrets
import socket
import sys
import threading
import time
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI, Request
import uvicorn

PROJECT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/agent/evidence-search"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, PROJECT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_api_guard():
    # Load the actual backend source under an isolated package name. Its only
    # relative import is rag_config; no main/application/service is imported.
    package_name = "_rag_eval_guard_test_backend"
    package = types.ModuleType(package_name)
    package.__path__ = [str(PROJECT / "backend" / "app")]
    module_name = package_name + ".security"
    spec = importlib.util.spec_from_file_location(module_name, PROJECT / "backend" / "app" / "security.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {package_name: package, module_name: module}):
        spec.loader.exec_module(module)
    return module.ApiGuard


mechanical = load_script("rag_evaluate")
retrieval = load_script("rag_retrieval_evaluate")
ApiGuard = load_api_guard()


@contextmanager
def guarded_loopback_server(key):
    """Own exactly one ephemeral socket/thread, with bounded startup/shutdown."""
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.middleware("http")(ApiGuard())
    delivered = []

    @app.post(ENDPOINT)
    async def synthetic_retrieval(request: Request):
        # Only safe path/presence metadata is retained, never request headers/body.
        delivered.append({"path": request.url.path,
                          "has_authorization": "authorization" in request.headers,
                          "has_legacy_header": "x-api-key" in request.headers})
        return {"mode": "bm25", "test_scope": "synthetic_api_guard_only",
                "hits": [{"chunk_id": "synthetic/auth-contract", "source": "synthetic",
                          "content": "Synthetic fixture, not a medical retrieval result."}]}

    with patch.dict(os.environ, {"RAG_API_KEY": key, "RAG_API_KEYS": key,
                                 "RAG_REQUIRE_API_KEY": "true", "RAG_RATE_LIMIT_PER_MINUTE": "200"}):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as owned_socket:
            owned_socket.bind(("127.0.0.1", 0))
            port = owned_socket.getsockname()[1]
            # Disable normal/error/access logging; no token is logged or saved.
            logger_names = ("uvicorn.error", "uvicorn.access", "uvicorn.asgi")
            old_levels = {name: logging.getLogger(name).level for name in logger_names}
            server, thread, failures = None, None, []
            try:
                server = uvicorn.Server(uvicorn.Config(
                    app, host="127.0.0.1", port=port, log_config=None, log_level="critical",
                    access_log=False, lifespan="off", ws="none", loop="asyncio", http="h11",
                    timeout_graceful_shutdown=1,
                ))

                def serve():
                    try:
                        server.run(sockets=[owned_socket])
                    except BaseException:
                        failures.append(True)  # Do not retain/log exception or request data.

                thread = threading.Thread(target=serve, name="rag-eval-api-guard-test", daemon=True)
                thread.start()
                deadline = time.monotonic() + 5
                while not server.started and thread.is_alive() and time.monotonic() < deadline:
                    time.sleep(0.01)
                if failures or not server.started:
                    raise RuntimeError("Owned synthetic API server did not start")
                yield f"http://127.0.0.1:{port}", delivered
            finally:
                if server is not None:
                    server.should_exit = True
                if thread is not None and thread.ident is not None:
                    thread.join(timeout=3)
                    if thread.is_alive():
                        server.force_exit = True
                        thread.join(timeout=2)
                for name, level in old_levels.items():
                    logging.getLogger(name).setLevel(level)
                if (thread is not None and thread.is_alive()) or failures:
                    raise RuntimeError("Owned synthetic API server failed bounded teardown")


class EvaluationApiGuardTests(unittest.TestCase):
    def setUp(self):
        self.key = secrets.token_hex(32)
        self.wrong_key = secrets.token_hex(32)

    def call_client(self, which, origin, key):
        payload = {"query": "synthetic auth fixture", "mode": "bm25", "top_k": 1, "candidate_k": 1}
        if which == "mechanical":
            return mechanical.call_api(origin, ENDPOINT, payload, key, 2)
        return retrieval.call_retrieval(origin + ENDPOINT, payload, key, 2)

    def assert_key_not_exposed(self, origin, raw):
        # Avoid assertion failure messages that could themselves print a key.
        self.assertFalse(self.key in raw or self.wrong_key in raw, "Response exposed a credential")
        self.assertFalse(self.key in origin or self.wrong_key in origin, "URL exposed a credential")

    def test_both_real_clients_valid_bearer_pass_actual_api_guard(self):
        with guarded_loopback_server(self.key) as (origin, delivered):
            for which in ("mechanical", "retrieval"):
                with self.subTest(client=which):
                    status, response, raw = self.call_client(which, origin, self.key)
                    self.assertEqual(status, 200)
                    self.assertEqual(response["test_scope"], "synthetic_api_guard_only")
                    self.assertEqual(response["hits"][0]["chunk_id"], "synthetic/auth-contract")
                    self.assert_key_not_exposed(origin, raw)
            self.assertEqual(len(delivered), 2)  # Exactly one request per call, no retries.
            self.assertTrue(all(row["path"] == ENDPOINT and row["has_authorization"]
                                and not row["has_legacy_header"] for row in delivered))

    def test_both_real_clients_missing_or_wrong_bearer_rejected_by_actual_api_guard(self):
        with guarded_loopback_server(self.key) as (origin, delivered):
            for which in ("mechanical", "retrieval"):
                for label, key in (("missing", ""), ("wrong", self.wrong_key)):
                    with self.subTest(client=which, auth_case=label):
                        status, response, raw = self.call_client(which, origin, key)
                        self.assertEqual(status, 401)
                        self.assertIn("detail", response)
                        self.assert_key_not_exposed(origin, raw)
            self.assertEqual(delivered, [])  # Rejected before the synthetic handler.

    def test_both_real_clients_legacy_header_rejected_by_actual_api_guard(self):
        # Simulate only the historical header on the Request-construction boundary.
        # The actual client opener, loopback network and actual ApiGuard still run.
        original_request = mechanical.urllib.request.Request

        def legacy_only_request(*args, **kwargs):
            headers = dict(kwargs.get("headers", {}))
            authorization = headers.pop("Authorization", "")
            if not authorization.startswith("Bearer "):
                raise AssertionError("Client failed to supply the expected Bearer header")
            headers["X-API-Key"] = authorization[7:]
            kwargs["headers"] = headers
            return original_request(*args, **kwargs)

        with guarded_loopback_server(self.key) as (origin, delivered):
            for which in ("mechanical", "retrieval"):
                with self.subTest(client=which):
                    module = mechanical if which == "mechanical" else retrieval
                    with patch.object(module.urllib.request, "Request", side_effect=legacy_only_request):
                        status, response, raw = self.call_client(which, origin, self.key)
                    self.assertEqual(status, 401)
                    self.assertIn("detail", response)
                    self.assert_key_not_exposed(origin, raw)
            self.assertEqual(delivered, [])


if __name__ == "__main__":
    unittest.main()
