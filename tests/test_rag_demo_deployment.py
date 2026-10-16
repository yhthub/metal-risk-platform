"""Static demo configuration contracts; no nginx, model, network or corpus use."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RagDemoDeploymentTests(unittest.TestCase):
    def test_gateway_checks_the_same_bearer_header_as_the_client(self):
        config = (ROOT / "deploy/nginx/default.conf.template").read_text(encoding="utf-8")
        self.assertIn("map $http_authorization $rag_authorized {", config)
        self.assertIn('"Bearer ${RAG_API_KEY}" 1;', config)
        self.assertIn("default 0;", config)
        self.assertIn("if ($rag_authorized = 0) { return 401; }", config)
        self.assertNotIn("$http_x_api_key", config)
        client = (ROOT / "my-nuxt-app/app/composables/useApi.ts").read_text(encoding="utf-8")
        # The request's default comes from the shared session, but a read-only
        # access probe can supply a candidate without overwriting that session.
        # Match this contract rather than requiring the header to bypass it.
        token_parameter = re.search(
            r"const request\s*=\s*async\s*\([^)]*\b(\w+)\s*:\s*string\s*=\s*sessionApiKey\b",
            client,
        )
        self.assertIsNotNone(token_parameter, "request must default to the shared in-memory credential")
        token_name = token_parameter.group(1)
        self.assertIn("Authorization: `Bearer ${" + token_name + "}`", client)

    def test_cors_permits_the_actual_auth_header(self):
        config = (ROOT / "deploy/nginx/default.conf.template").read_text(encoding="utf-8")
        self.assertIn('Access-Control-Allow-Headers "Content-Type, Authorization"', config)
        self.assertNotIn('Access-Control-Allow-Headers "Content-Type, X-API-Key"', config)

    def test_both_proxy_layers_forward_client_token_not_an_injected_secret(self):
        for name in ("default.conf.template", "https-edge.conf.example"):
            with self.subTest(layer=name):
                config = (ROOT / "deploy/nginx" / name).read_text(encoding="utf-8")
                self.assertIn("proxy_set_header Authorization $http_authorization;", config)
                self.assertNotIn("proxy_set_header X-API-Key", config)
                self.assertNotIn('proxy_set_header Authorization "Bearer ${RAG_API_KEY}"', config)

    def test_launcher_uses_existing_ollama_without_downloading_or_starting_it(self):
        launcher = (ROOT / "start-dev.bat").read_text(encoding="utf-8")
        self.assertIn('if not defined RAG_LLM_PROVIDER set "RAG_LLM_PROVIDER=ollama"', launcher)
        self.assertIn('if /i "%RAG_LLM_PROVIDER%"=="ollama" (', launcher)
        self.assertIn('if not defined RAG_LLM_MODEL set "RAG_LLM_MODEL=llama3.1:8b"', launcher)
        self.assertIn('if not defined RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK set "RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK=true"', launcher)
        self.assertIn('if not defined RAG_ALLOW_DEGRADED_RETRIEVAL set "RAG_ALLOW_DEGRADED_RETRIEVAL=true"', launcher)
        self.assertNotRegex(launcher.lower(), r"\bollama\s+(pull|serve|run)\b")

    def test_preserved_historical_probes_remain_explicitly_strict(self):
        smoke = (ROOT / "scripts/rag_ollama_smoke.py").read_text(encoding="utf-8")
        absent = (ROOT / "scripts/verify_rag_absent_term.py").read_text(encoding="utf-8")
        self.assertIn('"RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK": "false"', smoke)
        self.assertIn('RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK="false"', absent)


if __name__ == "__main__":
    unittest.main()
