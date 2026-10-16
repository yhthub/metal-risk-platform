"""Offline local-model client checks: no inference, network, or credentials."""

import unittest
from dataclasses import replace
from unittest.mock import Mock, patch

import requests

from app.rag_config import RagSettings
from app.services.local_llm_service import LocalLlmService, ModelUnavailableError


class LocalModelClientTests(unittest.TestCase):
    def setUp(self):
        self.settings = RagSettings(
            model="Llama-3.1-8B", base_url="http://127.0.0.1:8081/v1",
            model_api_key="", timeout=60, max_tokens=128,
            context_chars=4000, top_k=3, candidate_k=12, concurrency=1,
        )
        self.session = Mock()
        with patch("app.services.local_llm_service.requests.Session", return_value=self.session):
            self.client = LocalLlmService(self.settings)

    def response(self, payload):
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response

    def test_traffic_does_not_inherit_desktop_proxy(self):
        self.assertFalse(self.session.trust_env)

    def test_model_is_enabled_by_default_and_can_be_paused_from_environment(self):
        self.assertTrue(self.settings.model_enabled)
        with patch.dict("os.environ", {}, clear=True):
            self.assertTrue(RagSettings.from_env().model_enabled)
        for value in ("false", "0", "no"):
            with self.subTest(value=value), patch.dict("os.environ", {"RAG_LLM_ENABLED": value}, clear=True):
                self.assertFalse(RagSettings.from_env().model_enabled)
        with patch.dict("os.environ", {"RAG_LLM_ENABLED": "true", "RAG_LLM_PROVIDER": "ollama"}, clear=True):
            self.assertTrue(RagSettings.from_env().model_enabled)

    def test_disabled_status_preserves_configured_model_and_never_probes_network(self):
        for provider, backend in (("openai_compatible", "openai_compatible"), ("ollama", "ollama_native")):
            with self.subTest(provider=provider):
                self.client.settings = replace(self.settings, model="deepseek-v4.1-flash",
                                               provider=provider, model_enabled=False)
                status = self.client.status()
                self.assertFalse(status["ready"])
                self.assertEqual(status["name"], "deepseek-v4.1-flash")
                self.assertEqual(status["backend"], backend)
                self.assertEqual(status["available_models"], [])
                self.assertIn("等待", status["error"])
                self.assertIn("共享网站后端", status["error"])
                self.session.get.assert_not_called()
                self.session.post.assert_not_called()

    def test_disabled_generation_is_explicit_failure_without_model_request(self):
        for provider in ("openai_compatible", "ollama"):
            with self.subTest(provider=provider):
                self.client.settings = replace(self.settings, provider=provider, model_enabled=False)
                with self.assertRaisesRegex(ModelUnavailableError, "生成端尚未启用"):
                    self.client.generate([{"role": "user", "content": "Fixture only"}])
                self.session.get.assert_not_called()
                self.session.post.assert_not_called()

    def test_status_checks_configured_model_identity(self):
        self.session.get.return_value = self.response({"data": [{"id": "different-model"}]})
        status = self.client.status()
        self.assertFalse(status["ready"])
        self.assertIn("not served", status["error"])
        self.session.get.return_value = self.response({"data": [{"id": "Llama-3.1-8B"}]})
        self.assertTrue(self.client.status()["ready"])

    def test_status_malformed_response_is_not_a_ready_model(self):
        for payload in (["unexpected"], {"data": ["unexpected"]}, {"data": None}):
            with self.subTest(payload=payload):
                self.session.get.return_value = self.response(payload)
                self.assertFalse(self.client.status()["ready"])

    def test_generate_uses_actual_response_not_template_fallback(self):
        self.session.post.return_value = self.response({
            "model": "Llama-3.1-8B", "choices": [{"message": {"content": "Actual stub response [E1]"}, "finish_reason": "stop"}],
            "usage": {"completion_tokens": 7},
        })
        result = self.client.generate([{"role": "user", "content": "Fixture only"}])
        self.assertEqual(result["answer"], "Actual stub response [E1]")
        body = self.session.post.call_args.kwargs["json"]
        self.assertEqual(body["model"], "Llama-3.1-8B")
        self.assertFalse(body["stream"])
        self.assertEqual(body["temperature"], 0)

    def test_generate_error_does_not_echo_response_or_prompt(self):
        self.session.post.side_effect = requests.Timeout("SECRET RESPONSE AND PROMPT")
        with self.assertRaises(ModelUnavailableError) as caught:
            self.client.generate([{"role": "user", "content": "Sensitive fixture"}])
        self.assertNotIn("SECRET", str(caught.exception))
        self.assertNotIn("Sensitive", str(caught.exception))

    def test_provider_thinking_extension_is_explicit_and_not_sent_by_default(self):
        self.session.post.return_value = self.response({
            "model": "Llama-3.1-8B", "choices": [{"message": {"content": "Fixture [E1]"}}],
        })
        self.client.generate([])
        self.assertNotIn("enable_thinking", self.session.post.call_args.kwargs["json"])
        for enabled in (False, True):
            self.client.settings = replace(self.settings, enable_thinking=enabled)
            self.client.generate([])
            self.assertIs(self.session.post.call_args.kwargs["json"]["enable_thinking"], enabled)

    def test_thinking_environment_is_optional_and_rejects_invalid_values(self):
        for value, expected in (("", None), ("false", False), ("true", True)):
            with patch.dict("os.environ", {"RAG_LLM_ENABLE_THINKING": value}, clear=True):
                self.assertIs(RagSettings.from_env().enable_thinking, expected)
        with patch.dict("os.environ", {"RAG_LLM_ENABLE_THINKING": "unexpected"}, clear=True):
            with self.assertRaisesRegex(ValueError, "RAG_LLM_ENABLE_THINKING"):
                RagSettings.from_env()

    def test_generation_cannot_silently_switch_model(self):
        self.session.post.return_value = self.response({
            "model": "other-model", "choices": [{"message": {"content": "Wrong model [E1]"}}],
        })
        with self.assertRaises(ModelUnavailableError):
            self.client.generate([{"role": "user", "content": "Fixture"}])

    def test_empty_response_is_explicit_failure(self):
        self.session.post.return_value = self.response({"choices": [{"message": {"content": "  "}}]})
        with self.assertRaises(ModelUnavailableError):
            self.client.generate([{"role": "user", "content": "Fixture"}])

    def test_finish_reason_is_preserved_for_rag_truncation_gate(self):
        self.session.post.return_value = self.response({
            "choices": [{"message": {"content": "Partial fixture"}, "finish_reason": "length"}]
        })
        self.assertEqual(self.client.generate([])["finish_reason"], "length")


if __name__ == "__main__":
    unittest.main()
