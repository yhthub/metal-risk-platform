"""Environment-only, portable configuration for the real RAG service."""
from dataclasses import dataclass
import os
from typing import Optional


def _integer(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(os.getenv(name, str(default)))))
    except ValueError:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes"}


def optional_env_bool(name: str) -> Optional[bool]:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    folded = value.strip().lower()
    if folded in {"true", "1", "yes"}:
        return True
    if folded in {"false", "0", "no"}:
        return False
    raise ValueError(name + " must be true or false")


@dataclass(frozen=True)
class RagSettings:
    model: str
    base_url: str
    model_api_key: str
    timeout: int
    max_tokens: int
    context_chars: int
    top_k: int
    candidate_k: int
    concurrency: int
    context_window: int = 4096
    provider: str = "openai_compatible"
    model_enabled: bool = True
    enable_thinking: Optional[bool] = None

    @classmethod
    def from_env(cls):
        provider = os.getenv("RAG_LLM_PROVIDER", "openai_compatible").strip().lower()
        if provider not in {"openai_compatible", "ollama"}:
            raise ValueError("RAG_LLM_PROVIDER must be openai_compatible or ollama")
        return cls(
            model=os.getenv("RAG_LLM_MODEL", "Llama-3.1-8B"),
            base_url=os.getenv("RAG_LLM_BASE_URL", "http://127.0.0.1:11434" if provider == "ollama" else
                               "http://127.0.0.1:8081/v1").rstrip("/"),
            model_api_key=os.getenv("RAG_LLM_API_KEY", ""),
            timeout=_integer("RAG_LLM_TIMEOUT_SECONDS", 180, 5, 600),
            max_tokens=_integer("RAG_LLM_MAX_TOKENS", 768, 64, 2048),
            context_chars=_integer("RAG_LLM_CONTEXT_CHARS", 12000, 2000, 24000),
            top_k=_integer("RAG_TOP_K", 6, 1, 12),
            candidate_k=_integer("RAG_CANDIDATE_K", 32, 8, 128),
            concurrency=_integer("RAG_MAX_CONCURRENT_GENERATIONS", 1, 1, 8),
            context_window=_integer("RAG_LLM_CONTEXT_WINDOW", 4096, 2048, 131072),
            provider=provider,
            model_enabled=env_bool("RAG_LLM_ENABLED", True),
            enable_thinking=optional_env_bool("RAG_LLM_ENABLE_THINKING"),
        )
