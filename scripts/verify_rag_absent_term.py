"""Bounded absent-term regression, or an independent offline record review.

Neither mode replays or overwrites an existing first-attempt record. Review mode
does not import the backend, instantiate a service, or issue corpus/model requests.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
ABSENT_TERM = "quazylophenezn42"
ABSENT_QUERY = ABSENT_TERM + " kidney"
DIAGNOSTIC_PATH = "response.retrieval.diagnostics.channels.bm25.missing_lexical_terms"


def mapping(value):
    return value if isinstance(value, dict) else {}


def has_missing_term(response):
    diagnostics = mapping(mapping(response).get("retrieval")).get("diagnostics")
    bm25 = mapping(mapping(mapping(diagnostics).get("channels")).get("bm25"))
    missing = bm25.get("missing_lexical_terms")
    return isinstance(missing, list) and ABSENT_TERM in missing


def review_record(source: Path, output: Path):
    """Recompute saved-response checks only; preserve runtime assertions as recorded."""
    if output.exists() or source.resolve() == output.resolve():
        raise ValueError("Output exists or is the source record; preserve the original")
    original_bytes = source.read_bytes()
    original = json.loads(original_bytes.decode("utf-8-sig"))
    if not isinstance(original, dict):
        raise ValueError("Review requires a JSON object first-attempt record")
    value = mapping(original.get("response"))
    retrieval = mapping(value.get("retrieval"))
    if type(original.get("attempt")) is not int or original["attempt"] != 1 or \
            retrieval.get("mode") != "bm25" or retrieval.get("query") != ABSENT_QUERY:
        raise ValueError("Review requires the first BM25 attempt for the fixed absent-term query")
    recorded_checks = mapping(original.get("checks"))
    checks = {
        "http_200": original.get("http_status") == 200,
        "explicit_abstention": value.get("status") == "insufficient_evidence",
        "no_model_calls": recorded_checks.get("no_model_calls") is True and
                          mapping(value.get("model")).get("invoked") is False,
        "no_evidence_or_citations": value.get("evidence_cards") == [] and value.get("citations") == [],
        "missing_term_diagnostic": has_missing_term(value),
        "source_identity_unchanged": recorded_checks.get("source_identity_unchanged") is True,
    }
    passed = all(checks.values())
    record = {
        "state": "OFFLINE_REVIEW_PASS" if passed else "OFFLINE_REVIEW_FAIL",
        "review_status": "PASS" if passed else "FAIL",
        "scope": "offline_mechanical_review_of_preserved_absent_term_first_attempt_only",
        "source_record": {"path": str(source.resolve()),
                          "sha256": hashlib.sha256(original_bytes).hexdigest(),
                          "original_state": original.get("state"), "attempt": original.get("attempt"),
                          "http_status": original.get("http_status"),
                          "elapsed_seconds": original.get("elapsed_seconds"),
                          "scope": original.get("scope")},
        "original_checks": recorded_checks,
        "checks": checks,
        "changed_check_values": [name for name, value in checks.items()
                                 if recorded_checks.get(name) != value],
        "diagnostic_path": DIAGNOSTIC_PATH,
        "check_provenance": {
            "saved_response_checks": ["http_200", "explicit_abstention", "no_evidence_or_citations",
                                      "missing_term_diagnostic"],
            "no_model_calls": "Recorded runtime assertion plus saved model.invoked=false; not rerun",
            "source_identity_unchanged": "Recorded runtime assertion only; corpus identity not rechecked",
        },
        "review_activity": {"corpus_requests": 0, "model_calls": 0, "runtime_replayed": False},
        "clinical_accuracy": "NOT_EVALUATED",
        "limitations": ["This reviews the saved BM25 absent-literal response, not current corpus/model health.",
                        "No hybrid retrieval, semantic evidence absence, or clinical accuracy is established."],
    }
    # Re-read only this small JSON record, not any corpus. Refuse a changed source.
    if hashlib.sha256(source.read_bytes()).hexdigest() != record["source_record"]["sha256"]:
        raise ValueError("Source record changed during offline review")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--execute", action="store_true")
    modes.add_argument("--review-record", type=Path,
                       help="Review an existing saved record offline; never rerun its request")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.review_record:
        record = review_record(args.review_record, args.output)
        print(json.dumps({name: record[name] for name in
                          ("state", "source_record", "checks", "changed_check_values", "review_activity")}))
        return 0 if record["review_status"] == "PASS" else 1
    if not args.execute:
        print(json.dumps({"state": "PLAN_ONLY", "corpus_requests": 0, "model_calls": 0}))
        return 0
    if args.output.exists():
        raise ValueError("Output exists; preserve original first attempt")
    secret = secrets.token_hex(32)
    os.environ.update(RAG_API_KEY=secret, RAG_API_KEYS=secret, RAG_REQUIRE_API_KEY="true",
                      RAG_RETRIEVAL_MODE="bm25", RAG_ALLOW_DEGRADED_RETRIEVAL="false",
                      RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK="false",
                      RAG_MEDCPT_RERANK="false", RAG_DENSE_ALLOW_EXACT_SCAN="false")
    sys.path.insert(0, str(PROJECT / "backend"))
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api import agent
    from app.security import ApiGuard
    from app.rag_config import RagSettings
    from app.services.rag_agent_service import RagAgentService

    model_calls = []
    def forbidden_model():
        model_calls.append(True)
        raise AssertionError("Absent-term regression must not instantiate or call a model")
    settings = RagSettings(model="llama3.1:8b", base_url="http://127.0.0.1:11434", model_api_key="",
        timeout=180, max_tokens=512, context_chars=3500, top_k=2, candidate_k=8, concurrency=1, provider="ollama")
    service = RagAgentService(settings=settings, llm_factory=forbidden_model)
    before = service.retriever.sparse._verify_snapshot()[2]
    # Dedicated script process only: do not replace a running web app's singleton.
    agent.get_rag_service = lambda: service
    app = FastAPI()
    app.middleware("http")(ApiGuard())
    app.include_router(agent.router)
    started = time.monotonic()
    with TestClient(app) as client:
        response = client.post("/api/agent/chat", headers={"Authorization": "Bearer " + secret},
            json={"message": ABSENT_QUERY, "model": "llama3.1:8b", "history": [],
                  "knowledge_bases": [], "enable_deep_think": False})
    if secret in response.text:
        raise ValueError("Sensitive response body withheld")
    value = response.json()
    after = service.retriever.sparse._verify_snapshot()[2]
    checks = {"http_200": response.status_code == 200,
              "explicit_abstention": value.get("status") == "insufficient_evidence",
              "no_model_calls": not model_calls and value.get("model", {}).get("invoked") is False,
              "no_evidence_or_citations": value.get("evidence_cards") == [] and value.get("citations") == [],
              "missing_term_diagnostic": has_missing_term(value),
              "source_identity_unchanged": before == after}
    record = {"state": "PASS" if all(checks.values()) else "FAIL", "attempt": 1,
        "scope": "real_closed_corpus_absent_literal_regression_only; model_factory_forbidden; not a full smoke replay",
        "http_status": response.status_code, "elapsed_seconds": round(time.monotonic()-started, 4),
        "checks": checks, "response": value, "clinical_accuracy": "NOT_EVALUATED"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
    print(json.dumps({key: record[key] for key in ("state", "http_status", "elapsed_seconds", "checks")}))
    return 0 if record["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
