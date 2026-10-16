"""Bounded RAG mechanical evaluation. Synthetic mode is offline and is NOT system/clinical validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "rag_eval_cases.json"
REFERENCE = re.compile(r"\[(E\d+)\]")
SENSITIVE_ERROR = re.compile(r"Traceback \(most recent call last\)|Bearer\s+[A-Za-z0-9_-]{16,}|api[_-]?key\s*=", re.I)


def check_response(response: Any, *, mode: str = "chat", expected_status: str | None = None,
                   forbidden_literals: list[str] | None = None, http_status: int = 200) -> dict[str, Any]:
    """Structural checks only. Citation presence does not prove that a cited paper supports a claim."""
    checks: dict[str, bool] = {"json_object": isinstance(response, dict)}
    if not isinstance(response, dict):
        return {"pass": False, "checks": checks, "failed": ["json_object"]}
    serialized = json.dumps(response, ensure_ascii=False)
    checks["error_does_not_expose_credentials_or_traceback"] = SENSITIVE_ERROR.search(serialized) is None
    # The retrieval query may legitimately echo the canary; test generated answer, not request metadata.
    checks["forbidden_literal_not_emitted"] = not any(word in str(response.get("answer", "")) for word in (forbidden_literals or []))
    if not 200 <= http_status < 300:
        checks["error_not_disguised_as_answer"] = response.get("status") != "answered" and not response.get("answer")
        checks["expected_http_success"] = False
        return {"pass": False, "checks": checks, "failed": [key for key, value in checks.items() if not value]}
    if mode == "retrieval":
        cards = response.get("hits", response.get("top_ranked", response.get("evidence_cards", [])))
        checks["retrieval_list"] = isinstance(cards, list)
        if isinstance(cards, list):
            checks["retrieval_traceability"] = all(isinstance(card, dict) and card.get("chunk_id") and
                                                   (card.get("content") or card.get("text")) for card in cards)
            identifiers = [str(card.get("chunk_id")) for card in cards if isinstance(card, dict)]
            checks["retrieval_unique_chunks"] = len(identifiers) == len(set(identifiers))
        checks["no_generated_answer_in_retrieval_mode"] = not response.get("answer")
    else:
        answer = response.get("answer")
        citations = response.get("citations")
        cards = response.get("evidence_cards", [])
        status = response.get("status")
        checks["answer_is_plain_text"] = isinstance(answer, str)
        checks["status_explicit"] = status in ("answered", "insufficient_evidence")
        checks["citations_list"] = isinstance(citations, list)
        citations = citations if isinstance(citations, list) else []
        valid = [item for item in citations if isinstance(item, dict)]
        ids = [str(item.get("id", "")) for item in valid]
        checks["citation_metadata_complete"] = len(valid) == len(citations) and all(
            re.fullmatch(r"E\d+", str(item.get("id", ""))) and item.get("chunk_id") and item.get("source") and item.get("title")
            for item in valid
        )
        checks["citation_ids_unique"] = len(ids) == len(set(ids))
        used = set(REFERENCE.findall(answer or ""))
        checks["no_unresolved_citation_markers"] = used.issubset(set(ids))
        if isinstance(cards, list):
            chunk_ids = {str(card.get("chunk_id")) for card in cards if isinstance(card, dict)}
            checks["citations_are_from_returned_evidence"] = all(str(item.get("chunk_id")) in chunk_ids for item in valid)
        else:
            checks["citations_are_from_returned_evidence"] = False
        checks["answered_has_evidence_and_reference"] = status != "answered" or bool(citations and used)
        checks["no_evidence_abstains"] = bool(cards) or status == "insufficient_evidence"
        checks["abstention_does_not_claim_citations"] = status != "insufficient_evidence" or not citations
        checks["model_and_retrieval_reported"] = isinstance(response.get("model"), dict) and isinstance(response.get("retrieval"), dict)
        if expected_status is not None:
            checks["fixture_expected_status"] = status == expected_status
    failed = [key for key, value in checks.items() if not value]
    return {"pass": not failed, "checks": checks, "failed": failed}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Even same-origin redirects are refused: an API key must not reach a new target.
        return None


def call_api(base_url: str, endpoint: str, payload: dict[str, Any], api_key: str, timeout: float) -> tuple[int, Any, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(base_url.rstrip("/") + endpoint,
                                     data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                     headers=headers, method="POST")
    # No implicit environment proxy or redirect can forward the private access token.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as result:
            status = result.status
            raw = result.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    if api_key and api_key in raw:
        # A misconfigured server can echo headers. Withhold this body instead of
        # allowing credentials into first RAW; the runner records a failed attempt.
        raise OSError("API response echoed an access credential; sensitive body withheld")
    # Preserve actual HTTP body before/independent of JSON parsing.
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = {"parse_error": "response was not JSON"}
    return status, value, raw


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_bytes = args.cases.read_bytes()
    dataset = json.loads(input_bytes.decode("utf-8-sig"))
    cases = dataset["cases"][:args.max_cases]
    if not cases or not all(isinstance(item, dict) and item.get("case_id") and isinstance(item.get("query"), str)
                            and 0 < len(item["query"]) <= 2000 for item in cases):
        raise ValueError("require nonempty cases with case_id and bounded query text")
    identifiers = [item["case_id"] for item in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate case_id in evaluation input")
    if args.integration and args.mode == "chat" and not args.allow_model:
        raise ValueError("chat integration may generate tokens; explicitly pass --allow-model")
    if not args.integration and args.mode != "chat":
        raise ValueError("offline fixtures use chat mode; retrieval requires --integration")
    parsed = urlsplit(args.base_url)
    if args.integration and (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.query or parsed.fragment):
        raise ValueError("invalid API base URL (userinfo/query/fragment forbidden)")
    api_key = os.getenv("RAG_EVAL_API_KEY", "")
    if args.integration and not api_key:
        raise ValueError("set RAG_EVAL_API_KEY in the process environment; never put it in case files")
    endpoint = "/api/agent/chat" if args.mode == "chat" else "/api/agent/evidence-search"
    if args.dry_run:
        return {"scope": "plan_only_no_requests_no_files", "cases": len(cases), "mode": args.mode,
                "integration": args.integration, "endpoint": endpoint, "model_calls_allowed": args.allow_model}
    args.run_dir.mkdir(parents=True, exist_ok=False)
    records = []
    manifest = {"started_at": datetime.now(timezone.utc).isoformat(), "mode": args.mode,
                "integration": args.integration, "model_calls_allowed": args.allow_model,
                "cases_sha256": hashlib.sha256(input_bytes).hexdigest(), "case_count": len(cases),
                "attempts_per_case": 1, "clinical_accuracy": "NOT_EVALUATED",
                "scope": "mechanical_contract_only" if args.integration else "synthetic_contract_self_check_only"}
    (args.run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with (args.run_dir / "first_raw.jsonl").open("x", encoding="utf-8") as raw_file:
        for case in cases:
            payload = {"message": case["query"], "history": case.get("history", []), "knowledge_bases": []} if args.mode == "chat" else {
                "query": case["query"], "top_k": args.top_k}
            started = time.monotonic()
            error = None
            try:
                if args.integration:
                    http_status, response, raw_body = call_api(args.base_url, endpoint, payload, api_key, args.timeout)
                else:
                    http_status, response = 200, case["synthetic_response"]
                    raw_body = json.dumps(response, ensure_ascii=False)
            except (OSError, ValueError) as exc:
                # Exception messages can contain URLs or credentials: keep type only, no substitution/fallback.
                http_status, response, raw_body = 0, None, None
                error = type(exc).__name__
            elapsed = round(time.monotonic() - started, 4)
            check = check_response(response, mode=args.mode,
                                   expected_status=None if args.integration else case.get("fixture_expected_status"),
                                   forbidden_literals=case.get("forbidden_literals"), http_status=http_status)
            if error:
                check = {"pass": False, "checks": {"request_completed": False}, "failed": ["request_completed"]}
            raw_record = {"case_id": case["case_id"], "attempt": 1, "request": payload,
                          "http_status": http_status, "raw_body": raw_body, "response": response,
                          "latency_seconds": elapsed, "error_type": error, "synthetic": not args.integration}
            raw_file.write(json.dumps(raw_record, ensure_ascii=False) + "\n")
            raw_file.flush()
            os.fsync(raw_file.fileno())
            records.append({"case_id": case["case_id"], "latency_seconds": elapsed, **check})
    summary = {**manifest, "completed_at": datetime.now(timezone.utc).isoformat(),
               "passed": sum(int(record["pass"]) for record in records), "failed": sum(int(not record["pass"]) for record in records),
               "results": records, "semantic_support": "MANUAL_REVIEW_REQUIRED",
               "status": "PASS" if all(record["pass"] for record in records) else "FAIL"}
    (args.run_dir / "mechanical_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    # No clinical gold is invented. Complete manually in a separate review file; do not edit RAW.
    review = {"gold_status": "UNLABELED", "items": [{"case_id": case["case_id"], "gold_answer": None,
              "gold_chunk_ids": [], "support_review": None, "expert_review": None} for case in cases]}
    (args.run_dir / "manual_review_template.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=FIXTURE_PATH)
    parser.add_argument("--run-dir", type=Path, required=True, help="new immutable run directory; existing paths rejected")
    parser.add_argument("--integration", action="store_true", help="explicitly permit requests to a running API")
    parser.add_argument("--allow-model", action="store_true", help="explicitly permit chat/model inference in integration mode")
    parser.add_argument("--mode", choices=("chat", "retrieval"), default="chat")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--max-cases", type=int, default=4)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.max_cases <= 20 or not 1 <= args.top_k <= 12 or not 0 < args.timeout <= 600:
        parser.error("max-cases=1..20, top-k=1..12, timeout=(0,600]")
    try:
        summary = run(args)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "ERROR", "error_type": type(exc).__name__, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return int(summary.get("status") == "FAIL")


if __name__ == "__main__":
    raise SystemExit(main())
