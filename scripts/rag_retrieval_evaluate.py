"""Gated three-arm retrieval evaluation; never calls a generator or opens a corpus DB.

Default: print a plan only. Scoring uses external frozen qrels, never QA answers.
An execution writes a new first_raw.jsonl with exclusive creation; no retries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ARMS = ("bm25", "medcpt", "hybrid")
ENDPOINT = "/api/agent/evidence-search"


def reject_nonfinite_json(value):
    raise ValueError(f"Nonstandard JSON constant {value} is not allowed")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    """Hash small evaluation inputs only; not models, indexes or corpus files."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path):
    # Iterate physical lines: Unicode U+2028/U+2029 may appear inside JSON strings.
    with path.open("r", encoding="utf-8-sig") as stream:
        for number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    value = json.loads(line, parse_constant=reject_nonfinite_json)
                except (json.JSONDecodeError, ValueError) as error:
                    raise ValueError(f"Invalid JSON at {path.name}:{number}") from error
                if not isinstance(value, dict):
                    raise ValueError(f"Expected an object at {path.name}:{number}")
                yield value


def load_queries(path: Path, limit: int) -> list[dict[str, str]]:
    records, seen = [], set()
    for row in read_jsonl(path):
        if set(row) != {"query_id", "query"}:
            raise ValueError("Queries must contain only query_id and query (no answers/options/qrels)")
        identifier, query = row["query_id"], row["query"]
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
            raise ValueError("Query IDs must be nonempty and unique")
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ValueError("Each query must contain 1 to 2000 characters")
        seen.add(identifier)
        records.append(row)
        if len(records) > limit:
            raise ValueError(f"Query count exceeds the explicit bounded limit {limit}; do not silently truncate")
    if not records:
        raise ValueError("Queries are empty")
    return records


def load_qrels(path: Path | None, query_ids: set[str]) -> dict[str, dict[str, float]] | None:
    if path is None:
        return None
    result: dict[str, dict[str, float]] = {}
    with path.open("r", encoding="utf-8-sig") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            values = line.rstrip("\r\n").split("\t")
            if len(values) == 4:
                query_id, iteration, chunk_id, raw_grade = values
                if iteration != "0":
                    raise ValueError("TREC qrels iteration column must be 0")
            elif len(values) == 3:
                query_id, chunk_id, raw_grade = values
            else:
                raise ValueError(f"Qrels require 3 or 4 tab-separated columns at line {number}")
            if query_id not in query_ids or not chunk_id.strip():
                raise ValueError(f"Qrels contain an unknown query or empty chunk at line {number}")
            grade = float(raw_grade)
            if not math.isfinite(grade) or grade < 0 or grade > 5:
                raise ValueError("Frozen qrels grades must be finite in [0, 5]")
            judged = result.setdefault(query_id, {})
            if chunk_id in judged:
                raise ValueError("Duplicate qrels are rejected, not merged or repaired")
            judged[chunk_id] = grade
    return result


def budgets(policy: str, candidate_budget: int, top_k: int) -> dict[str, int]:
    if not 1 <= top_k <= 12 or not 1 <= candidate_budget <= 128:
        raise ValueError("top_k must be 1..12 and candidate budget 1..128")
    if policy == "total":
        if candidate_budget % 2 or candidate_budget // 2 < top_k:
            raise ValueError("Equal total budget must be even and at least 2*top_k")
        return {"bm25": candidate_budget, "medcpt": candidate_budget, "hybrid": candidate_budget // 2}
    if policy == "per_channel" and candidate_budget >= top_k:
        return dict.fromkeys(ARMS, candidate_budget)
    raise ValueError("Per-channel budget must be at least top_k")


def ranking_metrics(ids: list[str], judgments: dict[str, float] | None, top_k: int) -> dict[str, Any]:
    if judgments is None:
        return {"status": "NOT_EVALUATED", "reason": "no_qrels_for_query"}
    positives = {identifier for identifier, grade in judgments.items() if grade > 0}
    if not positives:
        return {"status": "NOT_EVALUATED", "reason": "no_positive_judgments", "judged_count": len(judgments)}
    retrieved = ids[:top_k]
    grades = [judgments.get(identifier, 0.0) for identifier in retrieved]
    relevant_ranks = [rank for rank, grade in enumerate(grades, 1) if grade > 0]
    dcg = sum((2 ** grade - 1) / math.log2(rank + 1) for rank, grade in enumerate(grades, 1))
    ideal = sorted(judgments.values(), reverse=True)[:top_k]
    idcg = sum((2 ** grade - 1) / math.log2(rank + 1) for rank, grade in enumerate(ideal, 1))
    return {
        "status": "SCORED", "recall_at_k": len(positives.intersection(retrieved)) / len(positives),
        "rr_at_k": 1 / relevant_ranks[0] if relevant_ranks else 0.0,
        "ndcg_at_k": dcg / idcg,
        "positive_judgments": len(positives), "judged_count": len(judgments),
        "judged_retrieved": sum(identifier in judgments for identifier in retrieved),
        "unjudged_retrieved": sum(identifier not in judgments for identifier in retrieved),
        "unjudged_policy": "zero_for_metrics_not_a_negative_label",
    }


def validate_response(response: Any, arm: str, per_channel: int, top_k: int,
                      sources: list[str] | None = None) -> tuple[list[str], dict[str, Any]]:
    if not isinstance(response, dict) or not isinstance(response.get("hits"), list):
        raise ValueError("Retrieval response must be an object with a hits list")
    if response.get("answer") or response.get("degraded"):
        raise ValueError("Generated answers and degraded retrieval are not valid three-arm results")
    mode = response.get("mode", "")
    if mode not in {"bm25": {"bm25"}, "medcpt": {"medcpt", "medcpt_sharded_exact", "medcpt_faiss_exact", "medcpt_faiss_ann"},
                    "hybrid": {"hybrid", "hybrid_medcpt_bm25"}}[arm]:
        raise ValueError("Returned retrieval mode does not match the requested arm")
    ids = []
    for hit in response["hits"]:
        if not isinstance(hit, dict) or not isinstance(hit.get("chunk_id"), str) or not hit["chunk_id"]:
            raise ValueError("Every ranked hit must have a canonical chunk_id")
        if sources and hit.get("source") not in sources:
            raise ValueError("Hit source is missing or differs from the frozen source filter")
        for name in ("score", "dense_score", "bm25_score", "rrf_score"):
            value = hit.get(name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                raise ValueError("Ranking scores must be finite when supplied")
        ids.append(hit["chunk_id"])
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate ranked IDs are rejected, not silently deduplicated")
    if len(ids) > top_k:
        raise ValueError("Response exceeded the frozen final top_k")
    diagnostics = response.get("diagnostics", {})
    if not isinstance(diagnostics, dict):
        raise ValueError("Diagnostics must be an object")
    declared = diagnostics.get("candidate_limit_per_channel")
    if declared is not None and declared != per_channel:
        raise ValueError("Response candidate budget differs from the frozen plan")
    channels = diagnostics.get("channels", {})
    if not isinstance(channels, dict):
        raise ValueError("Channel diagnostics must be an object")
    if arm in {"medcpt", "hybrid"}:
        dense_metadata = channels.get("medcpt", {})
        if diagnostics.get("independent_dense_recall") is not True or not isinstance(dense_metadata, dict) or dense_metadata.get("ready") is not True:
            raise ValueError("Dense evaluation requires explicit independent_dense_recall and a ready MedCPT channel")
    if arm == "hybrid":
        sparse_metadata = channels.get("bm25", {})
        if diagnostics.get("dual_route_executed") is not True or not isinstance(sparse_metadata, dict) or sparse_metadata.get("ready") is not True:
            raise ValueError("Hybrid evaluation requires explicit dual_route_executed and both ready channels")
    for name in ARMS[:2]:
        metadata = channels.get(name, {})
        if isinstance(metadata, dict) and metadata.get("count") is not None:
            count = metadata["count"]
            if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= per_channel:
                raise ValueError("Actual per-route candidate count exceeds its frozen budget")
        if isinstance(metadata, dict):
            reported_filters = metadata.get("source_filters", metadata.get("sources"))
            if reported_filters and (not isinstance(reported_filters, list) or not all(isinstance(value, str) for value in reported_filters)
                                     or set(reported_filters) != set(sources or [])):
                raise ValueError("Reported channel source filters differ from the frozen plan")
    dense = channels.get("medcpt", {})
    dense = dense if isinstance(dense, dict) else {}
    return ids, {"mode": mode, "channels": channels, "prepared_query": diagnostics.get("prepared_query"),
                 "terminology_expansion": diagnostics.get("terminology_expansion", []),
                 "dense_scope": dense.get("scope"), "dense_approximate": dense.get("approximate"),
                 "query_encoder_revision": dense.get("query_encoder_revision"),
                 "query_max_length": dense.get("query_max_length"), "dense_tie_break": dense.get("tie_break"),
                 "original_experiment_tie_break": dense.get("original_experiment_tie_break"),
                 "warnings": diagnostics.get("warnings", [])}


def load_rankings(path: Path, queries: list[dict[str, str]], planned_budgets: dict[str, int], top_k: int,
                  sources: list[str] | None = None) -> dict[tuple[str, str], dict]:
    expected = {row["query_id"]: row["query"] for row in queries}
    result = {}
    for record in read_jsonl(path):
        query_id, arm = record.get("query_id"), record.get("arm")
        if not isinstance(query_id, str) or query_id not in expected or arm not in ARMS or record.get("query") != expected[query_id]:
            raise ValueError("Cached ranking query/ID/arm differs from frozen input")
        key = (query_id, arm)
        if key in result:
            raise ValueError("Repeated cached attempts are rejected; select the authorized first RAW set explicitly")
        if record.get("candidate_k") != planned_budgets[arm] or record.get("top_k") != top_k:
            raise ValueError("Cached candidate/top_k budgets differ from the frozen plan")
        request = record.get("request", {})
        cached_sources = request.get("sources", []) if isinstance(request, dict) else None
        if not isinstance(cached_sources, list) or not all(isinstance(value, str) for value in cached_sources) or set(cached_sources) != set(sources or []):
            raise ValueError("Cached source filter differs from the frozen plan")
        if record.get("http_status", 200) == 200 and not record.get("error"):
            validate_response(record.get("response"), arm, planned_budgets[arm], top_k, sources)
        elapsed = record.get("elapsed_seconds")
        if elapsed is not None and (isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or
                                    not math.isfinite(elapsed) or elapsed < 0):
            raise ValueError("Elapsed seconds must be finite and nonnegative when supplied")
        result[key] = record
    if set(result) != {(query_id, arm) for query_id in expected for arm in ARMS}:
        raise ValueError("Cached rankings must contain exactly one first attempt for every query and all three arms")
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward a private API token through a redirect.
        return None


def integration_url(base_url: str, allow_remote: bool) -> str:
    parsed = urlsplit(base_url)
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise ValueError("Base URL must be an origin without credentials, paths, query or fragment")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("An HTTP(S) API origin is required")
    local = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if not local and (not allow_remote or parsed.scheme != "https"):
        raise ValueError("Remote integration needs explicit --allow-remote and HTTPS; no plaintext remote API tokens")
    return base_url.rstrip("/") + ENDPOINT


def call_retrieval(url: str, payload: dict, key: str, timeout: float) -> tuple[int, Any, str]:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = urllib.request.Request(url, method="POST", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                     headers=headers)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            status, raw = response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read().decode("utf-8", errors="replace")
    if key and key in raw:
        # Preserve failure, never a sensitive response body containing the private key.
        raise OSError("API response echoed an access credential; sensitive body withheld")
    try:
        response = json.loads(raw, parse_constant=reject_nonfinite_json)
    except (json.JSONDecodeError, ValueError):
        response = None
    return status, response, raw


def write_json_exclusive(path: Path, value: Any):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def summarize(records: list[dict], top_k: int, has_qrels: bool) -> dict:
    arms = {}
    for arm in ARMS:
        rows = [record for record in records if record["arm"] == arm]
        valid = [row for row in rows if row["status"] == "VALID_RANKING"]
        scored = [row for row in valid if row["metrics"]["status"] == "SCORED"]
        latencies = [row["elapsed_seconds"] for row in valid if row.get("elapsed_seconds") is not None]
        arms[arm] = {
            "planned_queries": len(rows), "valid_rankings": len(valid), "failed_attempts": len(rows) - len(valid),
            "completion_rate": len(valid) / len(rows) if rows else None,
            "empty_valid_rankings": sum(not row["ranked_ids"] for row in valid),
            "mean_returned_hits": statistics.mean(len(row["ranked_ids"]) for row in valid) if valid else None,
            "observed_mean_latency_seconds": statistics.mean(latencies) if latencies else None,
            "latency_observations": len(latencies), "latency_warning": "cache/order/hardware dependent; not independent timing trials",
            "quality_status": "SCORED_ON_EXTERNAL_QRELS" if scored else "NOT_EVALUATED",
            "quality_denominator_successfully_retrieved_and_positive_qrels": len(scored),
            "unscored_queries": len(rows) - len(scored),
            "mrr_at_k": statistics.mean(row["metrics"]["rr_at_k"] for row in scored) if scored else None,
            "mean_ndcg_at_k": statistics.mean(row["metrics"]["ndcg_at_k"] for row in scored) if scored else None,
            "mean_recall_at_k": statistics.mean(row["metrics"]["recall_at_k"] for row in scored) if scored else None,
            "unjudged_retrieved": sum(row["metrics"]["unjudged_retrieved"] for row in scored),
        }
    # Paired comparisons use only queries scored for every arm, not unequal subsets.
    scored_sets = [{row["query_id"] for row in records if row["arm"] == arm and row["status"] == "VALID_RANKING"
                    and row["metrics"]["status"] == "SCORED"} for arm in ARMS]
    paired = sorted(set.intersection(*scored_sets))
    paired_means = {}
    for arm in ARMS:
        rows = [row for row in records if row["arm"] == arm and row["query_id"] in paired]
        paired_means[arm] = {name: statistics.mean(row["metrics"][key] for row in rows) if rows else None
                            for name, key in (("mrr_at_k", "rr_at_k"), ("mean_ndcg_at_k", "ndcg_at_k"),
                                              ("mean_recall_at_k", "recall_at_k"))}
    return {"schema": "RAG_RETRIEVAL_EVAL_SUMMARY_v1", "top_k": top_k, "has_external_qrels": has_qrels,
            "not_clinical_accuracy": True, "no_answer_generation": True, "arms": arms,
            "paired_scored_query_ids": paired, "paired_denominator": len(paired), "paired_means": paired_means,
            "quality_caveat": "Unjudged hits score as zero only for metric computation; judgment completeness remains external."}


def run(args: argparse.Namespace) -> dict:
    if args.integration and args.rankings:
        raise ValueError("Choose cached offline rankings OR integration, not both")
    planned_budgets = budgets(args.budget_policy, args.candidate_budget, args.top_k)
    queries = load_queries(args.queries, args.max_queries)
    judgments = load_qrels(args.qrels, {row["query_id"] for row in queries})
    cached = load_rankings(args.rankings, queries, planned_budgets, args.top_k, args.sources) if args.rankings else None
    mode = "integration_retrieval_only" if args.integration else ("offline_cached_rankings" if cached is not None else "unconfigured")
    plan = {"schema": "RAG_RETRIEVAL_EVAL_PLAN_v1", "state": "PLAN_ONLY", "mode": mode,
            "query_count": len(queries), "arms": list(ARMS), "top_k": args.top_k,
            "budget_policy": args.budget_policy, "candidate_k_per_route": planned_budgets,
            "total_candidate_capacity": {arm: count * (2 if arm == "hybrid" else 1) for arm, count in planned_budgets.items()},
            "equal_total_candidates_not_equal_compute": args.budget_policy == "total",
            "sources": args.sources or [], "endpoint": ENDPOINT if args.integration else None,
            "external_qrels": args.qrels is not None, "quality_metrics_without_qrels": "NOT_EVALUATED",
            "expected_query_encoder": {"revision": args.query_encoder_revision, "max_length": args.query_max_length},
            "corpus_identity_declared_not_verified": args.corpus_identity,
            "no_llm_requests": True, "no_index_construction": True, "no_corpus_file_open": True,
            "integration_warning": "Explicit future execution may scan the configured full dense corpus. This plan does not authorize that run."}
    if not args.execute:
        return plan
    if mode == "unconfigured":
        raise ValueError("Execution requires --rankings for offline replay or explicit --integration")
    if args.output is None:
        raise ValueError("Execution requires a new --output directory")
    endpoint, key = None, None
    if args.integration:
        endpoint = integration_url(args.base_url, args.allow_remote)
        key = os.environ.get(args.api_key_env, "")
        if not key:
            raise ValueError("Integration requires an API key in the named environment variable; it is never written to output")
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {**plan, "state": "RUNNING", "started_at": utc_now(),
                "inputs": {str(path.resolve()): sha256(path) for path in (args.queries, args.qrels, args.rankings) if path is not None},
                "source_raw_is_copied_not_rewritten": cached is not None, "attempt_policy": "first_only_no_retry_no_overwrite",
                "arm_order": "rotate_bm25_medcpt_hybrid_by_query_index; not independent cache trials"}
    write_json_exclusive(args.output / "RUN_MANIFEST.json", manifest)
    scored_records = []
    with (args.output / "first_raw.jsonl").open("x", encoding="utf-8", newline="\n") as raw_stream:
        for index, query in enumerate(queries):
            order = ARMS[index % 3:] + ARMS[:index % 3]
            for arm in order:
                payload = {"query": query["query"], "mode": arm, "top_k": args.top_k, "candidate_k": planned_budgets[arm]}
                if args.sources:
                    payload["sources"] = args.sources
                record = {**query, "arm": arm, "candidate_k": planned_budgets[arm], "top_k": args.top_k,
                          "request": payload, "recorded_at": utc_now(), "evaluation_mode": mode}
                if cached is not None:
                    # Persist the original record intact under source_raw and preserve its observed timing.
                    source = cached[(query["query_id"], arm)]
                    record.update(response=source.get("response"), http_status=source.get("http_status", 200),
                                  elapsed_seconds=source.get("elapsed_seconds"), source_raw=source)
                    if source.get("error"):
                        record["error"] = source["error"]
                else:
                    started = time.monotonic()
                    try:
                        status, response, raw = call_retrieval(endpoint, payload, key, args.timeout)
                        record.update(http_status=status, response=response, raw_http_body=raw)
                    except (OSError, urllib.error.URLError, TimeoutError):
                        # Do not persist exception repr: it may contain proxy credentials or local secrets.
                        record.update(http_status=None, response=None, error="transport_error_no_retry")
                    record["elapsed_seconds"] = time.monotonic() - started
                # FIRST RAW is durable before structural/quality checks and is never overwritten.
                raw_stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                raw_stream.flush()
                os.fsync(raw_stream.fileno())
                score = {"query_id": query["query_id"], "arm": arm, "elapsed_seconds": record.get("elapsed_seconds")}
                try:
                    if record.get("error") or record.get("http_status") != 200:
                        raise ValueError("retrieval_attempt_failed")
                    ids, metadata = validate_response(record["response"], arm, planned_budgets[arm], args.top_k, args.sources)
                    score.update(status="VALID_RANKING", ranked_ids=ids, metadata=metadata,
                                 metrics=ranking_metrics(ids, judgments.get(query["query_id"]) if judgments is not None else None, args.top_k))
                    if arm != "bm25":
                        actual = (metadata.get("query_encoder_revision"), metadata.get("query_max_length"))
                        score["encoder_contract_matches_declared"] = actual == (args.query_encoder_revision, args.query_max_length)
                        score["encoder_contract_warning"] = None if score["encoder_contract_matches_declared"] else "missing_or_different_encoder_metadata"
                except ValueError as error:
                    score.update(status="FAILED", ranked_ids=[], failure=str(error),
                                 metrics={"status": "NOT_EVALUATED", "reason": "retrieval_or_structure_failed"})
                scored_records.append(score)
    summary = summarize(scored_records, args.top_k, judgments is not None)
    write_json_exclusive(args.output / "scored_rankings.json", scored_records)
    write_json_exclusive(args.output / "SUMMARY.json", summary)
    write_json_exclusive(args.output / "RUN_COMPLETION.json", {"state": "COMPLETE", "completed_at": utc_now(),
                         "raw_attempts": len(scored_records), "failed_attempts": sum(row["status"] == "FAILED" for row in scored_records),
                         "no_llm_requests": True, "clinical_validation": "NOT_PERFORMED"})
    return {"state": "COMPLETE", "output": str(args.output.resolve()), "summary": summary}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True, help="Frozen JSONL: query_id, query only")
    parser.add_argument("--qrels", type=Path, help="External manually verified judgments; 3/4-column TSV, no bundled clinical gold")
    parser.add_argument("--rankings", type=Path, help="External cached first-RAW JSONL, one query/arm record each")
    parser.add_argument("--integration", action="store_true", help="Explicit retrieval-only API mode; no LLM")
    parser.add_argument("--execute", action="store_true", help="Omit to remain PLAN_ONLY without API calls or file creation")
    parser.add_argument("--output", type=Path, help="A NEW result directory; existing paths are refused")
    parser.add_argument("--budget-policy", choices=("total", "per_channel"), default="total")
    parser.add_argument("--candidate-budget", type=int, default=32)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--max-queries", type=int, default=20)
    parser.add_argument("--sources", nargs="+", choices=("pubmed", "textbooks", "statpearls"))
    parser.add_argument("--corpus-identity", default="UNSPECIFIED", help="Frozen generation identity, not independently verified by runner")
    parser.add_argument("--query-encoder-revision", default="d83a36cc6b8e3a5c5e9d9d6ba156808c1643dcbc")
    parser.add_argument("--query-max-length", type=int, choices=(64, 512), default=64)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--allow-remote", action="store_true", help="Explicit HTTPS remote origin only; never inferred from a saved server IP")
    parser.add_argument("--api-key-env", default="RAG_API_KEY")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per request 1..60 seconds, no retries")
    return parser


def main():
    args = build_parser().parse_args()
    if not 1 <= args.max_queries <= 100 or not 1 <= args.timeout <= 60:
        raise SystemExit("Explicit query limit must be 1..100 and timeout 1..60 seconds")
    try:
        result = run(args)
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
