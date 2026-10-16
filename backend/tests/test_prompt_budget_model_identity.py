"""An alternate Ollama model must not inherit the transferred Llama tokenizer."""
import os
import sys
import types
import unittest
from unittest.mock import Mock, patch
from app.services.prompt_budget import PromptBudget


class PromptTokenizerIdentityTests(unittest.TestCase):
    def test_other_model_does_not_load_implicit_llama_file(self):
        loader = Mock()
        module = types.SimpleNamespace(Tokenizer=types.SimpleNamespace(from_file=loader))
        with patch.dict(os.environ, {"RAG_LLM_TOKENIZER_PATH": ""}), patch.dict(sys.modules, {"tokenizers": module}):
            with patch("app.services.prompt_budget.Path.is_file", return_value=True):
                budget = PromptBudget("qwen3:4b")
                budget.count([{"role": "user", "content": "测试"}])
        loader.assert_not_called()
        self.assertIn("conservative_utf8", budget.method)

    def test_original_model_can_reuse_matching_tokenizer(self):
        tokenizer = Mock()
        tokenizer.encode.return_value.ids = [1, 2]
        loader = Mock(return_value=tokenizer)
        module = types.SimpleNamespace(Tokenizer=types.SimpleNamespace(from_file=loader))
        with patch.dict(os.environ, {"RAG_LLM_TOKENIZER_PATH": ""}), patch.dict(sys.modules, {"tokenizers": module}):
            with patch("app.services.prompt_budget.Path.is_file", return_value=True):
                budget = PromptBudget("llama3.1:8b")
                self.assertEqual(budget.count([{"role": "user", "content": "hello"}]), 98)
        loader.assert_called_once()
        self.assertIn("matching_local_tokenizer", budget.method)


if __name__ == "__main__":
    unittest.main()
