"""Read-only deployment checks. Does not start containers, models, or network requests."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


def read_environment(path: Path) -> dict[str, str]:
    values = {}
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise ValueError(f"environment line {number} has no '='")
        key, value = stripped.split("=", 1)
        if key in values:
            raise ValueError(f"duplicate environment key at line {number}")
        values[key] = value.strip().strip("\"'")
    return values


def validate(values: dict[str, str], *, edge_only: bool = False) -> list[str]:
    errors = []
    for key in (("RAG_API_KEY",) if edge_only else ("RAG_API_KEY", "RAG_LLM_API_KEY")):
        # Restrict interpolation characters: quotes/$/newline must never enter the nginx template.
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", values.get(key, "")) or "REPLACE" in values.get(key, ""):
            errors.append(f"{key}: require a random 32-256 character token (value not printed)")
    if not edge_only and values.get("RAG_API_KEY") == values.get("RAG_LLM_API_KEY"):
        errors.append("application and internal model keys must be different")
    origin = values.get("RAG_PUBLIC_ORIGIN", "")
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
        errors.append("RAG_PUBLIC_ORIGIN: require one exact HTTPS origin without path or userinfo")
    if not re.fullmatch(r"https://[A-Za-z0-9.-]+(?::[0-9]+)?", origin):
        errors.append("RAG_PUBLIC_ORIGIN: unsupported characters for nginx interpolation")
    if edge_only:
        upstream = values.get("RAG_API_ORIGIN", "")
        upstream_url = urlsplit(upstream)
        host = values.get("RAG_API_HOST", "")
        if not re.fullmatch(r"https://[A-Za-z0-9.-]+(?::[0-9]+)?", upstream) or "REPLACE" in upstream:
            errors.append("RAG_API_ORIGIN: require protected exact HTTPS upstream, no path")
        if not re.fullmatch(r"[A-Za-z0-9.-]+", host) or host != upstream_url.hostname:
            errors.append("RAG_API_HOST: must match the upstream certificate hostname")
        web_image = values.get("RAG_WEB_IMAGE", "")
        if not web_image or "REPLACE" in web_image or web_image.endswith(":latest") or (":" not in web_image and "@sha256:" not in web_image):
            errors.append("RAG_WEB_IMAGE: require a pre-built pinned non-latest frontend image")
        return errors
    for key in ("RAG_CORPUS_HOST_PATH", "RAG_MODEL_HOST_PATH", "RAG_DENSE_INDEX_HOST_PATH"):
        candidate = Path(values.get(key, ""))
        if not values.get(key) or not candidate.is_absolute() or not candidate.is_dir():
            errors.append(f"{key}: directory must exist and be absolute")
    model = Path(values.get("RAG_MODEL_HOST_PATH", "__missing_model__"))
    for name in ("config.json", "tokenizer_config.json"):
        if not (model / name).is_file():
            errors.append(f"model: missing {name}")
    if not any(model.glob("*.safetensors")) and not any(model.glob("pytorch_model*.bin")):
        errors.append("model: no Hugging Face weight shards found (GGUF requires llama.cpp, not this compose)")
    if values.get("INSTALL_MEDCPT", "false") != "true":
        errors.append("INSTALL_MEDCPT: explicit CPU embedding dependencies are required for this hybrid compose; no automatic installation")
    if values.get("RAG_RETRIEVAL_MODE", "hybrid") != "hybrid" or values.get("RAG_ALLOW_DEGRADED_RETRIEVAL", "false") != "false":
        errors.append("hybrid compose requires both retrieval routes and forbids silent BM25 degradation")
    filename = values.get("RAG_DENSE_INDEX_FILENAME", "unified-medcpt.faiss")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.faiss", filename):
        errors.append("RAG_DENSE_INDEX_FILENAME: require a plain .faiss basename, no directory traversal")
    else:
        index = Path(values.get("RAG_DENSE_INDEX_HOST_PATH", "__missing_index__")) / filename
        if not index.is_file() or not Path(str(index) + ".json").is_file():
            errors.append("dense index: require completed external .faiss artifact and its .faiss.json provenance sidecar")
        try:
            budget = int(values.get("RAG_DENSE_MAX_INDEX_BYTES", "2147483648"))
            if budget <= 0 or (index.is_file() and index.stat().st_size > budget):
                raise ValueError
        except ValueError:
            errors.append("RAG_DENSE_MAX_INDEX_BYTES: positive serialized file budget must cover the index; not a resident RAM guarantee")
    try:
        context = int(values.get("VLLM_MAX_MODEL_LEN", "8192"))
        if not 2048 <= context <= 131072 or int(values.get("RAG_LLM_MAX_TOKENS", "0")) >= context:
            raise ValueError
        if "RAG_LLM_CONTEXT_WINDOW" in values and int(values["RAG_LLM_CONTEXT_WINDOW"]) != context:
            raise ValueError
    except ValueError:
        errors.append("context window: VLLM_MAX_MODEL_LEN must fit output budget and any explicit API window must match it")
    image = values.get("VLLM_IMAGE", "")
    if not image or "REPLACE" in image or image.endswith(":latest") or (":" not in image and "@sha256:" not in image):
        errors.append("VLLM_IMAGE: pin a tested non-latest tag or digest")
    for key in ("RAG_TOP_K", "RAG_LLM_MAX_TOKENS", "RAG_LLM_CONTEXT_CHARS", "RAG_MAX_CONCURRENT_GENERATIONS", "RAG_RATE_LIMIT_PER_MINUTE"):
        try:
            if int(values.get(key, "0")) <= 0:
                raise ValueError
        except ValueError:
            errors.append(f"{key}: require a positive integer")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--edge-only", action="store_true", help="validate only static gateway/HTTPS upstream, without corpus/model paths")
    args = parser.parse_args()
    try:
        errors = validate(read_environment(args.env_file), edge_only=args.edge_only)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "FAIL" if errors else "PASS", "errors": errors,
                      "scope": "configuration and path checks only; no GPU/model/corpus correctness validation"}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
