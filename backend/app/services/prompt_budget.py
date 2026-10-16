"""Bound model input before generation; no network tokenizer downloads."""
import os
from pathlib import Path
import threading


class PromptBudget:
    def __init__(self, model=None):
        self.model = model or os.getenv("RAG_LLM_MODEL", "Llama-3.1-8B")
        self.tokenizer = None
        self.checked = False
        self.lock = threading.Lock()

    def count(self, messages):
        with self.lock:
            if not self.checked:
                # Do not count an Ollama/Qwen prompt with the unrelated Llama
                # tokenizer merely because its file happens to be present.
                llama31 = self.model.casefold().replace("_", "-").startswith(
                    ("llama-3.1-8b", "llama3.1:8b"))
                configured = os.getenv("RAG_LLM_TOKENIZER_PATH")
                path = Path(configured) if configured else (
                    Path("E:/医学RAG模型/Llama-3.1-8B-Instruct/tokenizer.json") if llama31 else None)
                try:
                    from tokenizers import Tokenizer
                    if path and path.is_file():
                        self.tokenizer = Tokenizer.from_file(str(path))
                except (ImportError, OSError, ValueError, RuntimeError):
                    self.tokenizer = None
                self.checked = True
        # Reserve chat template special tokens separately. When a matching
        # tokenizer is unavailable, UTF-8 bytes are a conservative upper bound
        # for byte-based tokenizers, not a word estimate or a measured count for
        # arbitrary cloud models. The endpoint can still reject its own limit.
        count = sum(len(self.tokenizer.encode(item["content"]).ids) if self.tokenizer else
                    len(item["content"].encode("utf-8")) for item in messages)
        return count + 32 * len(messages) + 64

    @property
    def method(self):
        return "explicit_or_matching_local_tokenizer_plus_template_reserve" if self.tokenizer else "conservative_utf8_bytes_plus_template_reserve"
