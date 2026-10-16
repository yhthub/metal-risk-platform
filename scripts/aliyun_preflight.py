"""Read-only checks for BM25 + external-model deployment on the small Aliyun ECS.

Does not install, mount, format, start containers, contact models, hash the corpus,
run COUNT(*), or change existing site configuration. No secret values are printed.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import time
from urllib.parse import urlsplit

MIB = 1024 ** 2
GIB = 1024 ** 3
MIN_FREE_BYTES = 8 * GIB
PERSISTENT_FILESYSTEMS = {"ext4", "xfs", "btrfs", "ext3"}


class PreflightError(ValueError):
    """Controlled diagnostics that contain no secret values or source text."""


def read_environment(path: Path) -> dict[str, str]:
    if path.stat().st_size > 64 * 1024:
        raise PreflightError("environment file exceeds size limit")
    if os.name == "posix" and path.stat().st_mode & 0o077:
        raise PreflightError("private environment file must have mode 0600 or stricter")
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").split("\n"), 1):
        line = line.rstrip("\r").strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise PreflightError(f"environment line {number}: missing assignment")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or key in values:
            raise PreflightError(f"environment line {number}: invalid or duplicate key")
        # Deliberately simple .env grammar: no shell expansion, inline comments,
        # quoted values, or interpolation characters. Do not print offending text.
        if any(char in value for char in "\"'`$#\x00\r\n"):
            raise PreflightError(f"environment line {number}: unsafe value characters")
        values[key] = value.strip()
    return values


def _safe_url(value: str, *, origin: bool = False) -> bool:
    if not re.fullmatch(r"https?://[A-Za-z0-9.-]+(?::[0-9]{1,5})?(?:/[A-Za-z0-9._/-]*)?", value):
        return False
    try:
        parsed = urlsplit(value)
        if not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
            return False
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            return False
        return not origin or not parsed.path
    except ValueError:
        return False


def validate_environment(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for key in ("ALIYUN_API_IMAGE", "ALIYUN_WEB_IMAGE"):
        value = values.get(key, "")
        if (not re.fullmatch(r"[A-Za-z0-9._/-]+(?::[A-Za-z0-9._-]+|@sha256:[a-f0-9]{64})", value)
                or value.endswith(":latest") or "REPLACE" in value):
            errors.append(f"{key}: require a verified versioned image, not latest or a placeholder")
    token = values.get("RAG_API_KEY", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", token) or "REPLACE" in token:
        errors.append("RAG_API_KEY: require a random 32-256 character token; value not printed")
    model_key = values.get("RAG_LLM_API_KEY", "")
    if model_key and (not re.fullmatch(r"[A-Za-z0-9_.-]{1,256}", model_key) or "REPLACE" in model_key):
        errors.append("RAG_LLM_API_KEY: unsafe or placeholder token; value not printed")
    if model_key and model_key == token:
        errors.append("application token and external model token must be different")
    if values.get("RAG_LLM_PROVIDER") not in {"ollama", "openai_compatible"}:
        errors.append("RAG_LLM_PROVIDER: require ollama or openai_compatible")
    origin = values.get("RAG_PUBLIC_ORIGIN", "")
    if not _safe_url(origin, origin=True) or "REPLACE" in origin:
        errors.append("RAG_PUBLIC_ORIGIN: require the approved exact HTTP(S) origin, no path")
    endpoint = values.get("RAG_LLM_BASE_URL", "")
    if not _safe_url(endpoint) or "REPLACE" in endpoint:
        errors.append("RAG_LLM_BASE_URL: require the actual external model base URL")
    else:
        parsed = urlsplit(endpoint)
        hostname = parsed.hostname or ""
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if hostname in {"localhost", "api", "llm", "host.docker.internal"} or (
                address and (address.is_loopback or address.is_unspecified or address.is_link_local)):
            errors.append("RAG_LLM_BASE_URL: container-local addresses are not the external model")
        if parsed.scheme == "http":
            approved_private = (values.get("ALIYUN_ALLOW_PRIVATE_HTTP_MODEL") == "true"
                                and address and address.is_private and not address.is_reserved
                                and not address.is_loopback and not address.is_link_local)
            if not approved_private:
                errors.append("RAG_LLM_BASE_URL: use HTTPS or an explicitly confirmed private-IP HTTP service")
        if parsed.path.rstrip("/").endswith(("/api/chat", "/api/tags", "/chat/completions")):
            errors.append("RAG_LLM_BASE_URL: configure a base URL, not a concrete API method")
    model = values.get("RAG_LLM_MODEL", "")
    if not re.fullmatch(r"[A-Za-z0-9._:/-]{1,200}", model) or "REPLACE" in model:
        errors.append("RAG_LLM_MODEL: require the actual remote model name")
    base = values.get("ALIYUN_BASE_PATH", "/")
    if not re.fullmatch(r"/(?:[A-Za-z0-9_-]+/)*", base):
        errors.append("ALIYUN_BASE_PATH: require / or an approved /prefix/ with trailing slash")
    for key, low, high, default in (
        ("RAG_WEB_PORT", 1024, 65535, 8080), ("RAG_LLM_TIMEOUT_SECONDS", 5, 180, 180),
        ("RAG_LLM_MAX_TOKENS", 64, 1024, 512), ("RAG_LLM_CONTEXT_CHARS", 2000, 8000, 3500),
        ("RAG_LLM_CONTEXT_WINDOW", 2048, 131072, 4096), ("RAG_TOP_K", 1, 4, 2),
        ("RAG_CANDIDATE_K", 8, 32, 8), ("RAG_RETRIEVAL_TIMEOUT_SECONDS", 1, 15, 8),
        ("RAG_RATE_LIMIT_PER_MINUTE", 1, 20, 20),
    ):
        try:
            value = int(values.get(key, str(default)))
            if not low <= value <= high:
                raise ValueError
        except ValueError:
            errors.append(f"{key}: outside the small-server profile's integer range")
    try:
        if int(values.get("RAG_LLM_MAX_TOKENS", "512")) >= int(values.get("RAG_LLM_CONTEXT_WINDOW", "4096")):
            errors.append("model output token budget must be less than the context window")
    except ValueError:
        pass  # Already reported without printing values.
    return errors


def _small_json(path: Path, max_bytes: int = 4 * MIB) -> dict:
    if not path.is_file() or path.stat().st_size > max_bytes:
        raise PreflightError(f"missing or oversized catalog: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise PreflightError(f"catalog is not an object: {path.name}")
    return value


def inspect_corpus(root: Path) -> dict:
    root = root.resolve(strict=True)
    manifest = _small_json(root / "UNIFIED_MANIFEST_PORTABLE.json")
    progress = _small_json(root / "00_catalog/EXPORT_PROGRESS.json")
    provenance = _small_json(root / "00_catalog/SNAPSHOT_PROVENANCE.json")
    if manifest.get("schema") != "MEDRR-UNIFIED-RETRIEVAL-v1":
        raise PreflightError("unsupported portable corpus manifest schema")
    if progress.get("state") != "COMPLETE" or provenance.get("state") != "COMPLETE" or (
            provenance.get("snapshot_complete_by_backup_api") is not True):
        raise PreflightError("corpus is not a completed independent closed backup snapshot")
    relative = manifest.get("corpus_database")
    if not isinstance(relative, str) or not relative or re.match(r"^[A-Za-z]:", relative):
        raise PreflightError("corpus database must have a portable relative path")
    portable = Path(relative.replace("\\", "/"))
    if portable.is_absolute() or relative.replace("\\", "/").startswith("/") or ".." in portable.parts:
        raise PreflightError("corpus database path is absolute or traverses outside the root")
    db = (root / portable).resolve(strict=True)
    if not db.is_relative_to(root) or not db.is_file():
        raise PreflightError("corpus database escapes its root or is not a regular file")
    if any(Path(str(db) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise PreflightError("refusing corpus with WAL/SHM/journal sidecars")
    size = db.stat().st_size
    if type(progress.get("local_database_bytes")) is not int or size != progress["local_database_bytes"] or size <= 0:
        raise PreflightError("closed database file size differs from export receipt")
    total = manifest.get("total_rows")
    if type(total) is not int or total <= 0 or progress.get("total_chunks") != total:
        raise PreflightError("declared corpus row-axis catalogs disagree")
    identity = (size, db.stat().st_mtime_ns)
    deadline = time.monotonic() + 3
    connection = sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=2)
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA cache_size=-1024")
        connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 100)
        schema = connection.execute("SELECT sql FROM sqlite_master WHERE name='chunks_fts'").fetchone()
        if not schema or not re.search(r"\bUSING\s+fts5\s*\(", schema[0], re.IGNORECASE):
            raise PreflightError("chunks_fts is not an existing FTS5 virtual table")
        fts_columns = {row[1] for row in connection.execute("PRAGMA table_info(chunks_fts)")}
        if not {"title", "content"}.issubset(fts_columns):
            raise PreflightError("chunks_fts does not contain the expected title/content fields")
        columns = {row[1] for row in connection.execute("PRAGMA table_info(chunks)")}
        expected = {"row_index", "document_id", "corpus", "source_key", "source_row", "title", "content"}
        if not expected.issubset(columns):
            raise PreflightError("chunks table does not match the current retrieval schema")
    finally:
        connection.close()
    if (db.stat().st_size, db.stat().st_mtime_ns) != identity:
        raise PreflightError("closed corpus changed during schema-only inspection")
    return {"database_bytes": size, "declared_chunks": total,
            "row_count_basis": "completed catalogs; no recount", "fts5_schema_present": True,
            "scope": "closed receipt/file identity/schema only; not full content or retrieval validation"}


def read_mounts(path: Path = Path("/proc/self/mountinfo")) -> list[tuple[Path, str]]:
    records = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        fields = line.split()
        if not fields or "-" not in fields:
            continue
        separator = fields.index("-")
        # Linux mountinfo escapes spaces/tab/backslash; do not shell-evaluate it.
        raw = fields[4]
        decoded = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match[1], 8)), raw)
        records.append((Path(decoded).resolve(), fields[separator + 1]))
    return records


def inspect_storage(values: dict[str, str], corpus_bytes: int, *, mounts=None, disk_usage=None,
                    check_upload_owner: bool = True) -> dict:
    paths = {}
    for key in ("ALIYUN_DATA_ROOT", "RAG_CORPUS_HOST_PATH", "RAG_UPLOADS_HOST_PATH"):
        raw = values.get(key, "")
        candidate = Path(raw)
        if not raw or "REPLACE" in raw or not candidate.is_absolute() or not candidate.is_dir():
            raise PreflightError(f"{key}: require an existing absolute directory")
        paths[key] = candidate.resolve(strict=True)
    root = paths["ALIYUN_DATA_ROOT"]
    if root == Path(root.anchor):
        raise PreflightError("data root must be a separate mounted data filesystem, not /")
    for key in ("RAG_CORPUS_HOST_PATH", "RAG_UPLOADS_HOST_PATH"):
        if paths[key] == root or not paths[key].is_relative_to(root):
            raise PreflightError(f"{key}: must be a subdirectory of the confirmed data mount")
    if paths["RAG_CORPUS_HOST_PATH"] == paths["RAG_UPLOADS_HOST_PATH"] or (
            paths["RAG_UPLOADS_HOST_PATH"].is_relative_to(paths["RAG_CORPUS_HOST_PATH"])):
        raise PreflightError("writable uploads must not live inside the immutable corpus")
    records = read_mounts() if mounts is None else mounts
    filesystem = next((fstype for mount, fstype in records if mount == root), None)
    if filesystem not in PERSISTENT_FILESYSTEMS:
        raise PreflightError("data root is not a confirmed separate supported persistent filesystem mount")
    usage = shutil.disk_usage(root) if disk_usage is None else disk_usage
    if usage.total < corpus_bytes + MIN_FREE_BYTES or usage.free < MIN_FREE_BYTES:
        raise PreflightError("data mount must fit the closed corpus and retain at least 8 GiB free space")
    if os.name == "posix" and check_upload_owner:
        stat = paths["RAG_UPLOADS_HOST_PATH"].stat()
        if stat.st_uid != 10001 or stat.st_mode & 0o007:
            raise PreflightError("private uploads must be owned by API uid 10001 and not accessible to other users")
    return {"filesystem": filesystem, "data_mount_total_bytes": usage.total,
            "data_mount_free_bytes": usage.free, "required_free_reserve_bytes": MIN_FREE_BYTES,
            "scope": "existing mount/storage only; no partitioning, formatting, or mounts performed"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args(argv)
    result = {"status": "FAIL", "errors": [], "network_requests": 0, "model_calls": 0,
              "full_hashes": 0, "full_row_counts": 0, "mutations": 0,
              "scope": "read-only preparation checks; not deployment or RAG performance acceptance"}
    try:
        values = read_environment(args.env_file)
        result["errors"] = validate_environment(values)
        if not result["errors"]:
            # Validate the confirmed mount BEFORE touching the corpus metadata.
            inspect_storage(values, 0)
            result["corpus"] = inspect_corpus(Path(values.get("RAG_CORPUS_HOST_PATH", "")))
            result["storage"] = inspect_storage(values, result["corpus"]["database_bytes"])
            result["status"] = "PASS"
    except PreflightError as error:
        result["errors"].append(str(error))
    except (OSError, ValueError, sqlite3.Error):
        # OS/SQLite/JSON exceptions may include private paths or source text.
        # Keep output secret-safe; actionable controlled errors are gathered above.
        result["errors"].append("snapshot/storage/private env checks failed; inspect local catalogs and mount ownership without printing secrets")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
