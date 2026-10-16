"""No Docker, network, real model, or real keys used."""
import importlib.util
import tempfile
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location("deployment_preflight", Path(__file__).resolve().parents[1] / "scripts" / "deployment_preflight.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DeploymentPreflightTests(unittest.TestCase):
    def values(self):
        return {"RAG_API_KEY": "synthetic_test_token_" + "x" * 32,
                "RAG_PUBLIC_ORIGIN": "https://rag.example.org", "RAG_API_ORIGIN": "https://api.example.org",
                "RAG_API_HOST": "api.example.org", "RAG_WEB_IMAGE": "example/web:reviewed-test-version"}

    def test_edge_mode_does_not_require_model_or_corpus(self):
        self.assertEqual(module.validate(self.values(), edge_only=True), [])

    def test_nginx_key_injection_is_rejected(self):
        values = self.values()
        values["RAG_API_KEY"] = '"; injection ' + "x" * 32
        self.assertTrue(any("RAG_API_KEY" in error for error in module.validate(values, edge_only=True)))

    def test_upstream_certificate_host_mismatch_is_rejected(self):
        values = self.values()
        values["RAG_API_HOST"] = "other.example.org"
        self.assertTrue(any("RAG_API_HOST" in error for error in module.validate(values, edge_only=True)))

    def test_public_http_and_placeholder_image_are_rejected(self):
        values = self.values()
        values["RAG_PUBLIC_ORIGIN"] = "http://8.148.158.242"
        values["RAG_WEB_IMAGE"] = "REPLACE_WITH_IMAGE"
        errors = module.validate(values, edge_only=True)
        self.assertTrue(any("RAG_PUBLIC_ORIGIN" in error for error in errors))
        self.assertTrue(any("RAG_WEB_IMAGE" in error for error in errors))

    def full_values(self, path):
        # Fake one-byte files exercise only path/config validation, never model/index contents.
        model, corpus, index = path / "model", path / "corpus", path / "index"
        for directory in (model, corpus, index):
            directory.mkdir()
        for name in ("config.json", "tokenizer_config.json", "synthetic.safetensors"):
            (model / name).write_text("synthetic", encoding="utf-8")
        (index / "synthetic.faiss").write_bytes(b"xx")
        (index / "synthetic.faiss.json").write_text("{}", encoding="utf-8")
        return {**self.values(), "RAG_LLM_API_KEY": "different_synthetic_test_" + "y" * 32,
                "RAG_CORPUS_HOST_PATH": str(corpus), "RAG_MODEL_HOST_PATH": str(model),
                "RAG_DENSE_INDEX_HOST_PATH": str(index), "RAG_DENSE_INDEX_FILENAME": "synthetic.faiss",
                "RAG_DENSE_MAX_INDEX_BYTES": "2", "INSTALL_MEDCPT": "true",
                "VLLM_IMAGE": "example/model:reviewed-test-version", "RAG_TOP_K": "8",
                "RAG_LLM_MAX_TOKENS": "768", "RAG_LLM_CONTEXT_CHARS": "18000",
                "RAG_MAX_CONCURRENT_GENERATIONS": "1", "RAG_RATE_LIMIT_PER_MINUTE": "20",
                "VLLM_MAX_MODEL_LEN": "8192"}

    def test_hybrid_prepare_needs_explicit_dependency_build_and_index_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            values = self.full_values(Path(temp))
            self.assertEqual(module.validate(values), [])
            values["INSTALL_MEDCPT"] = "false"
            self.assertTrue(any("INSTALL_MEDCPT" in error for error in module.validate(values)))
            values["INSTALL_MEDCPT"] = "true"
            values["RAG_DENSE_MAX_INDEX_BYTES"] = "1"
            self.assertTrue(any("RAG_DENSE_MAX_INDEX_BYTES" in error for error in module.validate(values)))

    def test_context_disagreement_and_index_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            values = self.full_values(Path(temp))
            values["RAG_LLM_CONTEXT_WINDOW"] = "4096"
            values["RAG_DENSE_INDEX_FILENAME"] = "../synthetic.faiss"
            errors = module.validate(values)
            self.assertTrue(any("context window" in error for error in errors))
            self.assertTrue(any("RAG_DENSE_INDEX_FILENAME" in error for error in errors))

    def test_missing_sidecar_and_silent_degradation_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            values = self.full_values(Path(temp))
            values["RAG_DENSE_INDEX_FILENAME"] = "missing.faiss"
            values["RAG_ALLOW_DEGRADED_RETRIEVAL"] = "true"
            errors = module.validate(values)
            self.assertTrue(any("provenance sidecar" in error for error in errors))
            self.assertTrue(any("silent BM25" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
