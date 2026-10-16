"""Two first-attempt public RAG checks. PLAN_ONLY unless --execute is explicit.

The FastAPI request path is in-process TestClient, not a socket deployment test.
Ollama and corpus retrieval are real in execution mode; no medical gold is used.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from rag_evaluate import check_response

EXPECTED_TOTAL_CHUNKS = 24139516
CASES = (
    {"case_id": "positive_cadmium_kidney", "query": "cadmium kidney", "expected_status": "answered", "expected_invoked": True},
    {"case_id": "negative_novel_compound", "query": "quazylophenezn42 kidney", "expected_status": "insufficient_evidence", "expected_invoked": False},
)
PROFILE = {"provider": "ollama", "top_k": 2, "candidate_k": 8, "context_chars": 3500,
           "max_tokens": 512, "context_window": 4096, "timeout_seconds": 180,
           "concurrency": 1, "attempts_per_case": 1}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--run-dir", type=Path, required=True, help="new generation only; existing paths rejected")
    parser.add_argument("--retrieval-mode", choices=("hybrid", "bm25"), default="hybrid")
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--origin", default="http://127.0.0.1:11434")
    parser.add_argument("--corpus-root", type=Path, default=Path("E:/医学检索库_完整_20261010"))
    return parser


def validate_options(args):
    parsed = urlsplit(args.origin)
    if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or parsed.port != 11434 or parsed.username or parsed.password or parsed.query
            or parsed.fragment or parsed.path not in {"", "/"}):
        raise ValueError("Ollama origin must be a loopback HTTP origin on 11434, without path/userinfo/query/fragment")
    if args.model != "llama3.1:8b":
        raise ValueError("This frozen smoke profile uses the existing exact model ID llama3.1:8b")
    root = args.corpus_root.expanduser().resolve()
    target = args.run_dir.expanduser().resolve()
    if target.exists():
        raise ValueError("Run generation already exists; never overwrite or rerun its first attempts")
    if target == Path(target.anchor) or target == root or target.is_relative_to(root) or root.is_relative_to(target):
        raise ValueError("Run output must be a dedicated directory independent of corpus assets")
    return root, target


def configure_environment(args, root):
    # This CLI runs in its own process. No credentials/configuration files are read.
    token = secrets.token_hex(32)
    values = {
        "RAG_API_KEY": token, "RAG_API_KEYS": token, "RAG_REQUIRE_API_KEY": "true",
        "RAG_RATE_LIMIT_PER_MINUTE": "20", "RAG_CORPUS_ROOT": str(root),
        "RAG_LLM_PROVIDER": "ollama", "RAG_LLM_MODEL": args.model,
        "RAG_LLM_BASE_URL": args.origin.rstrip("/"), "RAG_LLM_API_KEY": "",
        "RAG_RETRIEVAL_MODE": args.retrieval_mode, "RAG_ALLOW_DEGRADED_RETRIEVAL": "false",
        # Historical smoke is the strict evidence-only profile, not the demo fallback.
        "RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK": "false",
        "RAG_MEDCPT_RERANK": "false", "RAG_DENSE_BACKEND": "faiss",
        "RAG_DENSE_ALLOW_EXACT_SCAN": "false", "RAG_DENSE_MAX_SCAN_ROWS": "0",
        "RAG_LLM_TIMEOUT_SECONDS": "180", "RAG_LLM_MAX_TOKENS": "512",
        "RAG_LLM_CONTEXT_CHARS": "3500", "RAG_TOP_K": "2", "RAG_CANDIDATE_K": "8",
        "RAG_LLM_CONTEXT_WINDOW": "4096", "RAG_MAX_CONCURRENT_GENERATIONS": "1",
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
    }
    os.environ.update(values)
    return token


def make_client():
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.agent import router
    from app.security import ApiGuard
    app = FastAPI()
    app.middleware("http")(ApiGuard())
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def source_receipt(root):
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))
    from app.services.corpus_retrieval_service import CorpusRetrievalService
    manifest, database, identity = CorpusRetrievalService(root, medcpt_rerank=False)._verify_snapshot()
    if int(manifest["total_rows"]) != EXPECTED_TOTAL_CHUNKS:
        raise ValueError("This profile requires the declared complete 24,139,516-chunk export, not a small subset")
    return {"root": str(root), "database": str(database), "total_chunks": int(manifest["total_rows"]),
            "closed_snapshot_verified": True, "database_bytes": identity[0], "database_mtime_ns": identity[1],
            "manifest_sha256": hashlib.sha256((root / "UNIFIED_MANIFEST_PORTABLE.json").read_bytes()).hexdigest(),
            "row_count_basis": "completed export catalog; no COUNT(*) or full-row/vector scan"}


def resource_snapshot(origin):
    result = {"measurement_scope": "RAM/GPU counters and current Ollama loaded-model metadata; no private history"}
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    if os.name == "nt":
        command = "$o=Get-CimInstance Win32_OperatingSystem; [math]::Round($o.FreePhysicalMemory/1MB,2)"
        try:
            output = subprocess.check_output(["powershell", "-NoProfile", "-Command", command],
                                             timeout=15, creationflags=flags, text=True)
            result["free_ram_gib"] = float(output.strip())
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            result["ram_counter_error_type"] = type(error).__name__
    try:
        output = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total,memory.free",
                                          "--format=csv,noheader,nounits"], timeout=10, creationflags=flags, text=True)
        result["gpu_counters_csv"] = output.strip().splitlines()
    except (OSError, subprocess.SubprocessError) as error:
        result["gpu_counter_error_type"] = type(error).__name__
    import requests
    with requests.Session() as session:
        session.trust_env = False
        try:
            response = session.get(origin.rstrip("/") + "/api/ps", timeout=5, allow_redirects=False)
            response.raise_for_status()
            result["ollama_loaded_models"] = [{key: model.get(key) for key in
                ("name", "size", "size_vram", "context_length", "expires_at")}
                for model in response.json().get("models", [])]
        except (requests.RequestException, ValueError, TypeError, AttributeError) as error:
            result["ollama_ps_error_type"] = type(error).__name__
    return result


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def safe_response(response, secret):
    raw = response.text
    if secret in raw:
        raise ValueError("Credential echo: response body withheld from RAW")
    try:
        parsed = response.json()
    except ValueError:
        parsed = None
    return response.status_code, parsed, raw


def check_attempt(case, response, http_status, retrieval_mode):
    check = check_response(response, expected_status=case["expected_status"], http_status=http_status)
    checks = check["checks"]
    if isinstance(response, dict):
        model = response.get("model") if isinstance(response.get("model"), dict) else {}
        retrieval = response.get("retrieval") if isinstance(response.get("retrieval"), dict) else {}
        checks["expected_model_invocation"] = model.get("invoked") is case["expected_invoked"]
        checks["actual_configured_model_identity"] = model.get("name") == "llama3.1:8b" and model.get("backend") == "ollama_native"
        checks["retrieval_scope_not_disguised"] = retrieval.get("mode") == (
            "bm25" if retrieval_mode == "bm25" else "hybrid_medcpt_bm25") and retrieval.get("degraded") is False
        if case["expected_invoked"]:
            checks["reported_model_identity"] = model.get("reported_name") == "llama3.1:8b"
    failed = [key for key, value in checks.items() if not value]
    return {"pass": not failed, "checks": checks, "failed": failed}


def run(args):
    root, target = validate_options(args)
    plan = {"state": "PLAN_ONLY", "execution_performed": False, "run_dir": str(target),
            "corpus_root": str(root), "expected_total_chunks": EXPECTED_TOTAL_CHUNKS,
            "origin": args.origin, "model": args.model, "profile": PROFILE,
            "retrieval_mode": args.retrieval_mode, "automatic_degradation": False,
            "retrieval_scope": "BM25-only/full_closed_corpus" if args.retrieval_mode == "bm25" else "independent_hybrid/full_closed_corpus",
            "cases": list(CASES), "request_transport": "in_process_TestClient_not_socket",
            "clinical_accuracy": "NOT_EVALUATED", "semantic_support": "NOT_EVALUATED"}
    if not args.execute:
        return plan
    target.mkdir(parents=True, exist_ok=False)
    manifest = {**plan, "state": "STARTED", "execution_performed": True,
                "started_at": datetime.now(timezone.utc).isoformat(), "new_models_pulled": 0,
                "source_mutations": 0, "large_index_builds": 0, "automatic_retries": 0}
    write_json(target / "manifest.json", manifest)
    records, preflight, source_before = [], {}, None
    error_type = None
    try:
        secret = configure_environment(args, root)
        source_before = source_receipt(root)
        write_json(target / "source_before.json", source_before)
        write_json(target / "resources_before.json", resource_snapshot(args.origin))
        with make_client() as client:
            preflight["unauthenticated_status_code"] = client.get("/api/agent/status").status_code
            preflight["wrong_key_status_code"] = client.get("/api/agent/status", headers={"Authorization": "Bearer " + secrets.token_hex(32)}).status_code
            headers = {"Authorization": "Bearer " + secret}
            status_code, status, raw = safe_response(client.get("/api/agent/status", headers=headers), secret)
            preflight.update(authenticated_status_code=status_code, status_response=status, raw_status_body=raw)
            retrieval_status = status.get("retrieval") if isinstance(status, dict) and isinstance(status.get("retrieval"), dict) else {}
            preflight["checks"] = {
                "unauthenticated_401": preflight["unauthenticated_status_code"] == 401,
                "wrong_key_401": preflight["wrong_key_status_code"] == 401,
                "authenticated_200": status_code == 200,
                "ready_for_explicit_profile": isinstance(status, dict) and status.get("status") == "ready",
                "actual_mode": retrieval_status.get("mode") == args.retrieval_mode,
                "not_degraded": retrieval_status.get("degraded") is False,
            }
            write_json(target / "preflight.json", preflight)
            if all(preflight["checks"].values()):
                with (target / "first_raw.jsonl").open("x", encoding="utf-8") as raw_file:
                    for case in CASES:
                        payload = {"message": case["query"], "history": [], "model": args.model,
                                   "knowledge_bases": [], "enable_deep_think": False}
                        started = time.monotonic()
                        request_error = None
                        try:
                            http_status, response, raw_body = safe_response(client.post("/api/agent/chat", headers=headers, json=payload), secret)
                        except Exception as error:
                            # Never persist exception messages, headers, or echoed credentials.
                            http_status, response, raw_body = 0, None, None
                            request_error = type(error).__name__
                        record = {"case_id": case["case_id"], "attempt": 1, "request": payload,
                                  "http_status": http_status, "raw_body": raw_body, "response": response,
                                  "latency_seconds": round(time.monotonic()-started, 4), "error_type": request_error}
                        raw_file.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                        raw_file.flush()
                        os.fsync(raw_file.fileno())
                        records.append({"case_id": case["case_id"], "attempt": 1, "http_status": http_status,
                                        "latency_seconds": record["latency_seconds"],
                                        **check_attempt(case, response, http_status, args.retrieval_mode)})
    except Exception as error:
        error_type = type(error).__name__
    try:
        source_after = source_receipt(root)
        write_json(target / "source_after.json", source_after)
        source_unchanged = source_before is not None and source_before == source_after
    except Exception as error:
        source_unchanged = False
        error_type = error_type or type(error).__name__
    try:
        write_json(target / "resources_after.json", resource_snapshot(args.origin))
    except Exception as error:
        error_type = error_type or type(error).__name__
    passed = len(records) == len(CASES) and all(record["pass"] for record in records) and source_unchanged and not error_type
    summary = {**manifest, "state": "PASS" if passed else "FAIL", "completed_at": datetime.now(timezone.utc).isoformat(),
               "preflight_checks": preflight.get("checks", {}), "source_unchanged": source_unchanged,
               "case_attempts_recorded": len(records), "passed": sum(record["pass"] for record in records),
               "failed": sum(not record["pass"] for record in records), "results": records, "error_type": error_type,
               "review_boundary": "Mechanical references/identity/gating only; no clinical accuracy, semantic entailment, expert review or socket deployment claim",
               "service_retained": True, "inference_on_failed_http_request": "UNKNOWN; never interpret a missing response as zero model calls"}
    write_json(target / "mechanical_summary.json", summary)
    return summary


def main():
    args = build_parser().parse_args()
    try:
        result = run(args)
    except (OSError, ValueError) as error:
        print(json.dumps({"state": "ERROR", "error_type": type(error).__name__}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["state"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
