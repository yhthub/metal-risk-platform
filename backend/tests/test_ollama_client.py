"""Native Ollama transport regression; no network, corpus or model inference."""
from dataclasses import replace
import unittest
from unittest.mock import Mock, patch
from app.rag_config import RagSettings
from app.services.local_llm_service import LocalLlmService, ModelUnavailableError


class OllamaClientTests(unittest.TestCase):
    def setUp(self):
        self.settings = RagSettings(model="llama3.1:8b", base_url="http://127.0.0.1:11434",
            model_api_key="", timeout=120, max_tokens=256, context_chars=4000,
            top_k=3, candidate_k=8, concurrency=1, context_window=4096, provider="ollama")
        self.session = Mock()
        with patch("app.services.local_llm_service.requests.Session", return_value=self.session):
            self.client = LocalLlmService(self.settings)

    def response(self, payload):
        response = Mock()
        response.status_code = 200
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response

    def test_status_uses_tags_and_exact_model_name(self):
        self.session.get.return_value = self.response({"models": [{"name": "llama3.1:8b"}]})
        self.assertTrue(self.client.status()["ready"])
        self.assertEqual(self.session.get.call_args.args[0], "http://127.0.0.1:11434/api/tags")
        self.session.get.return_value = self.response({"models": [{"name": "Llama-3.1-8B"}]})
        self.assertFalse(self.client.status()["ready"])

    def test_generation_binds_allocated_context_and_preserves_usage(self):
        self.session.post.return_value = self.response({"model": "llama3.1:8b", "done": True,
            "done_reason": "stop", "message": {"content": "Real stub [E1]"},
            "prompt_eval_count": 100, "eval_count": 10})
        result = self.client.generate([{"role": "user", "content": "Fixture"}])
        self.assertEqual(result["answer"], "Real stub [E1]")
        self.assertEqual(result["usage"], {"prompt_tokens": 100, "completion_tokens": 10})
        self.assertEqual(result["finish_reason"], "stop")
        args = self.session.post.call_args
        self.assertEqual(args.args[0], "http://127.0.0.1:11434/api/chat")
        self.assertFalse(args.kwargs["json"]["stream"])
        self.assertEqual(args.kwargs["json"]["options"]["num_ctx"], 4096)
        self.assertEqual(args.kwargs["json"]["options"]["num_predict"], 256)
        self.assertFalse(args.kwargs["allow_redirects"])
        self.assertFalse(self.session.trust_env)

    def test_incomplete_or_switched_model_is_not_success(self):
        for payload in ({"model": "other", "done": True}, {"model": "llama3.1:8b", "done": False},
                        {"done": True}):
            self.session.post.return_value = self.response(payload)
            with self.assertRaises(ModelUnavailableError):
                self.client.generate([])

    def test_native_output_limit_is_visible(self):
        self.session.post.return_value = self.response({"model": "llama3.1:8b", "done": True,
            "done_reason": "length", "message": {"content": "Partial"}})
        self.assertEqual(self.client.generate([])["finish_reason"], "length")

    def test_environment_provider_is_explicit_no_silent_switch(self):
        with patch.dict("os.environ", {"RAG_LLM_PROVIDER": "ollama", "RAG_LLM_BASE_URL": "http://127.0.0.1:11434"}):
            self.assertEqual(RagSettings.from_env().provider, "ollama")
        with patch.dict("os.environ", {"RAG_LLM_PROVIDER": "unknown"}):
            with self.assertRaises(ValueError):
                RagSettings.from_env()

    def test_malformed_result_does_not_escape_as_internal_error(self):
        self.session.post.return_value = self.response(["unexpected"])
        with self.assertRaises(ModelUnavailableError):
            self.client.generate([])

    def test_redirect_cannot_forward_question_or_credential(self):
        response = self.response({"model": "llama3.1:8b", "done": True, "message": {"content": "Fake"}})
        response.status_code = 307
        self.session.post.return_value = response
        with self.assertRaises(ModelUnavailableError):
            self.client.generate([])
        self.assertFalse(self.session.post.call_args.kwargs["allow_redirects"])
        self.session.get.return_value = response
        self.assertFalse(self.client.status()["ready"])
        self.assertFalse(self.session.get.call_args.kwargs["allow_redirects"])


if __name__ == "__main__":
    unittest.main()
