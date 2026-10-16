"""Local bounded API preflight; no chat/model generation, no full vector scan."""
import argparse
import json
import os
from pathlib import Path
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lexical-smoke", action="store_true", help="One bounded real BM25 request, no dense/model generation")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Do not load or replace user configuration. Keys are ephemeral in process
    # memory, and only the test client receives the literal secret.
    secret = secrets.token_hex(32)
    os.environ["RAG_API_KEY"] = secret
    os.environ["RAG_REQUIRE_API_KEY"] = "true"
    os.environ["RAG_RETRIEVAL_MODE"] = "hybrid"
    os.environ["RAG_ALLOW_DEGRADED_RETRIEVAL"] = "false"
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.agent import router
    from app.security import ApiGuard
    app = FastAPI()
    app.middleware("http")(ApiGuard())
    app.include_router(router)
    checks = {"scope": "local_API_preflight_plus_optional_bounded_BM25",
              "model_generations": 0, "dense_encoder_calls": 0, "full_vector_scans": 0,
              "source_mutations": 0}
    with TestClient(app) as client:
        checks["unauthenticated_status_code"] = client.get("/api/agent/status").status_code
        headers = {"Authorization": "Bearer " + secret}
        response = client.get("/api/agent/status", headers=headers)
        checks["authenticated_status_code"] = response.status_code
        checks["readiness"] = response.json()
        # Assert missing dense resources produce an explicit error, not a fake
        # hybrid result. Never send a dense request when it could actually scan.
        if not checks["readiness"]["retrieval"]["channels"]["medcpt"].get("ready"):
            failure = client.post("/api/agent/evidence-search", headers=headers, json={"query": "cadmium kidney", "top_k": 3})
            checks["missing_dense_status_code"] = failure.status_code
            checks["missing_dense_error"] = failure.json()
        if args.lexical_smoke:
            lexical = client.post("/api/agent/evidence-search", headers=headers,
                json={"query": "cadmium kidney", "mode": "bm25", "top_k": 3, "candidate_k": 8})
            result = lexical.json()
            checks["bounded_bm25"] = {"status_code": lexical.status_code, "mode": result.get("mode"),
                "diagnostics": result.get("diagnostics"), "hits": [
                    {key: hit.get(key) for key in ("chunk_id", "row_index", "title", "bm25_score", "pmid", "doi")}
                    for hit in result.get("hits", [])]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(checks, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"output": str(args.output), "model_generations": 0,
                      "full_vector_scans": 0, "http_status": checks["authenticated_status_code"]}))


if __name__ == "__main__":
    main()
