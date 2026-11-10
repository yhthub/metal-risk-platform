"""Environment-only, portable configuration for the real RAG service."""
from dataclasses import dataclass, field
import json
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
    model_api_key: str = field(repr=False)
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
    answer_strategy: str = "excerpt_only"
    extra_model_keys: tuple = field(default=(), repr=False)

    @classmethod
    def from_env(cls):
        provider = os.getenv("RAG_LLM_PROVIDER", "openai_compatible").strip().lower()
        if provider not in {"openai_compatible", "ollama"}:
            raise ValueError("RAG_LLM_PROVIDER must be openai_compatible or ollama")
        strategy = os.getenv("RAG_ANSWER_STRATEGY", "excerpt_only").strip().lower()
        if strategy not in {"excerpt_only", "knowledge_evidence_synthesis"}:
            raise ValueError("RAG_ANSWER_STRATEGY must be excerpt_only or knowledge_evidence_synthesis")
        extra_keys = json.loads(os.getenv("RAG_LLM_EXTRA_API_KEYS") or "[]")
        if not isinstance(extra_keys, list) or not all(isinstance(key, str) and key.strip() for key in extra_keys):
            raise ValueError("RAG_LLM_EXTRA_API_KEYS must be a JSON array of non-empty strings")
        if extra_keys and provider != "openai_compatible":
            raise ValueError("Multiple keys require an OpenAI-compatible endpoint")
        return cls(
            model=os.getenv("RAG_LLM_MODEL", "Llama-3.1-8B"),
            base_url=os.getenv("RAG_LLM_BASE_URL", "http://127.0.0.1:11434" if provider == "ollama" else
                               "http://127.0.0.1:8081/v1").rstrip("/"),
            model_api_key=os.getenv("RAG_LLM_API_KEY", ""),
            timeout=_integer("RAG_LLM_TIMEOUT_SECONDS", 180, 5, 600),
            max_tokens=_integer("RAG_LLM_MAX_TOKENS", 768, 64, 4096),
            context_chars=_integer("RAG_LLM_CONTEXT_CHARS", 12000, 2000, 24000),
            top_k=_integer("RAG_TOP_K", 6, 1, 12),
            candidate_k=_integer("RAG_CANDIDATE_K", 32, 8, 128),
            concurrency=_integer("RAG_MAX_CONCURRENT_GENERATIONS", 1, 1, 20),
            context_window=_integer("RAG_LLM_CONTEXT_WINDOW", 4096, 2048, 131072),
            provider=provider,
            model_enabled=env_bool("RAG_LLM_ENABLED", True),
            enable_thinking=optional_env_bool("RAG_LLM_ENABLE_THINKING"),
            answer_strategy=strategy,
            extra_model_keys=tuple(key.strip() for key in extra_keys),
        )
