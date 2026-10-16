"""API guard and route contracts; no LLM/server/corpus invocation."""
import unittest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.agent import router
from app.security import ApiGuard
from app.services.corpus_retrieval_service import CorpusUnavailable


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict("os.environ", {"RAG_API_KEY": "fixture-key", "RAG_REQUIRE_API_KEY": "true",
                                              "RAG_RATE_LIMIT_PER_MINUTE": "20"})
        self.env.start()
        app = FastAPI()
        app.middleware("http")(ApiGuard())
        app.include_router(router)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.env.stop()

    def test_auth_before_model_or_retrieval(self):
        with patch("app.api.agent.get_rag_service", side_effect=AssertionError("No service")):
            self.assertEqual(self.client.get("/api/agent/status").status_code, 401)
            self.assertEqual(self.client.get("/api/agent/status", headers={"Authorization": "Bearer wrong"}).status_code, 401)

    def test_default_dense_failure_is_503_not_fake_success(self):
        with patch("app.api.agent.get_rag_service") as factory:
            factory.return_value.retriever.search.side_effect = CorpusUnavailable("MedCPT not ready")
            factory.return_value.settings.candidate_k = 32
            response = self.client.post("/api/agent/evidence-search", headers={"Authorization": "Bearer fixture-key"},
                                        json={"query": "lead"})
            self.assertEqual(response.status_code, 503)

    def test_retrieval_arm_and_budget_are_forwarded(self):
        with patch("app.api.agent.get_rag_service") as factory:
            factory.return_value.settings.candidate_k = 32
            factory.return_value.retriever.search.return_value = {"hits": [], "mode": "medcpt"}
            response = self.client.post("/api/agent/evidence-search", headers={"Authorization": "Bearer fixture-key"},
                                        json={"query": "lead", "mode": "medcpt", "candidate_k": 16, "top_k": 5})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(factory.return_value.retriever.search.call_args.args[:3], ("lead", 5, 16))
            self.assertEqual(factory.return_value.retriever.search.call_args.kwargs, {"mode": "medcpt"})

    def test_invalid_inputs_never_reach_retrieval(self):
        with patch("app.api.agent.get_rag_service", side_effect=AssertionError("No service")):
            for body in ({"query": "x", "mode": "fake"}, {"query": "x", "candidate_k": 129},
                         {"query": "x", "sources": ["fake"]}, {"query": "x" * 2001}):
                response = self.client.post("/api/agent/evidence-search", headers={"Authorization": "Bearer fixture-key"}, json=body)
                self.assertEqual(response.status_code, 422)

    def test_private_upload_is_not_faked(self):
        response = self.client.post("/api/agent/upload-kb", headers={"Authorization": "Bearer fixture-key"})
        self.assertEqual(response.status_code, 501)

    def test_rate_limit_is_bounded(self):
        with patch.dict("os.environ", {"RAG_RATE_LIMIT_PER_MINUTE": "1"}):
            headers = {"Authorization": "Bearer fixture-key"}
            self.assertEqual(self.client.post("/api/agent/upload-kb", headers=headers).status_code, 501)
            self.assertEqual(self.client.post("/api/agent/upload-kb", headers=headers).status_code, 429)
