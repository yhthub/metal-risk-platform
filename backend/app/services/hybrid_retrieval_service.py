"""Independent MedCPT + FTS5/BM25 retrieval; rank fusion is not evidence certainty."""
from concurrent.futures import ThreadPoolExecutor
import math
import os
import re
import threading
import time
from .corpus_retrieval_service import CorpusRetrievalService, CorpusUnavailable, lexical_terms, TERMS


def common_query(query):
    terms, expansions = lexical_terms(query)
    # English queries are preserved. Chinese support is an explicit terminology
    # expansion, never advertised as general translation or clinical parsing.
    expanded = " ".join(terms) if re.search(r"[\u3400-\u9fff]", query) else query.strip()
    return expanded, terms, expansions


def untranslated_segments(query):
    remaining = query
    for chinese in sorted(TERMS, key=len, reverse=True):
        remaining = remaining.replace(chinese, " ")
    # Only question scaffolding is discarded. Unknown medical names stay
    # visible and block excerpt-grounded generation rather than silently vanishing.
    # The chat orchestrator may instead give a clearly labeled general answer.
    scaffold = ("是否", "有什么", "有哪些", "什么", "怎么", "如何", "影响", "关系", "相关", "研究",
                "证据", "导致", "引起", "造成", "风险", "以及", "关于", "请问", "请", "这个", "这种",
                "这些", "那它", "那么", "与", "和", "及", "的", "对", "会", "吗", "是", "了", "有", "能", "否")
    for phrase in scaffold:
        remaining = remaining.replace(phrase, " ")
    return re.findall(r"[\u3400-\u9fff]+", remaining)


def annotate(hit, terms):
    text = (str(hit.get("title", "")) + " " + str(hit.get("content", ""))).casefold()
    matched = [term for term in terms if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text)]
    hit["matched_query_terms"] = matched
    hit["query_term_coverage"] = len(matched) / len(terms) if terms else 0.0
    hit["match_tier"] = "all_terms" if terms and len(matched) == len(terms) else "partial_terms"


def reciprocal_rank_fusion(sparse, dense, *, k=60, sparse_weight=1.0, dense_weight=1.0):
    if k <= 0 or not all(math.isfinite(w) and w > 0 for w in (sparse_weight, dense_weight)):
        raise ValueError("RRF requires a positive constant and finite positive channel weights")
    merged = {}
    for name, items, weight in (("bm25", sparse, sparse_weight), ("medcpt", dense, dense_weight)):
        seen = set()
        for rank, item in enumerate(items, 1):
            row = item["row_index"]
            if row in seen:
                continue
            seen.add(row)
            if row in merged and merged[row]["chunk_id"] != item["chunk_id"]:
                raise CorpusUnavailable("Retrieval channels disagree on corpus row identity")
            hit = merged.setdefault(row, {**item, "retrieval_channels": [], "rrf_score": 0.0,
                                          "bm25_rank": None, "bm25_score": None,
                                          "dense_rank": None, "dense_score": None})
            hit["retrieval_channels"].append(name)
            hit["rrf_score"] += weight / (k + rank)
            if name == "bm25":
                hit["bm25_rank"], hit["bm25_score"] = rank, item.get("score")
            else:
                hit["dense_rank"], hit["dense_score"] = rank, item.get("dense_score")
            hit["score"] = hit["rrf_score"]
            hit["score_type"] = "rrf_rank_fusion_not_probability"
    return sorted(merged.values(), key=lambda item: (-item["rrf_score"], item["chunk_id"]))


class HybridRetrievalService:
    medcpt_rerank = False

    def __init__(self, sparse=None, dense=None, *, allow_degraded=None):
        self.sparse = sparse or CorpusRetrievalService(medcpt_rerank=False)
        if dense is None:
            from .medcpt_dense_service import MedcptDenseService
            dense = MedcptDenseService(root=self.sparse.root)
        self.dense = dense
        self.mode = os.getenv("RAG_RETRIEVAL_MODE", "hybrid").strip().lower()
        if self.mode not in {"hybrid", "bm25"}:
            raise ValueError("RAG_RETRIEVAL_MODE must be hybrid or bm25")
        self.allow_degraded = allow_degraded if allow_degraded is not None else (
            os.getenv("RAG_ALLOW_DEGRADED_RETRIEVAL", "false").lower() == "true")
        self.capacity = threading.BoundedSemaphore(1)
        self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="rag-retrieval")

    def status(self):
        sparse, dense = self.sparse.status(), self.dense.status()
        ready = bool(sparse.get("ready") and (self.mode == "bm25" or dense.get("ready") or self.allow_degraded))
        return {**sparse, "ready": ready, "engine": "medcpt_bm25_rrf" if self.mode == "hybrid" else "sqlite_fts5_bm25",
                "corpus_ready": bool(sparse.get("ready")), "mode": self.mode,
                "channels": {"bm25": sparse, "medcpt": dense},
                "dense_scope": dense.get("scope", "unavailable"),
                "degraded": self.mode == "hybrid" and not dense.get("ready") and self.allow_degraded,
                "rrf_k": 60, "rrf_weights": {"bm25": 1, "medcpt": 1},
                "independent_dense_recall": self.mode == "hybrid" and bool(dense.get("ready"))}

    def search(self, query, top_k=8, candidate_k=32, sources=None, mode=None):
        if not self.capacity.acquire(blocking=False):
            raise CorpusUnavailable("Retrieval is busy; concurrent full-corpus requests are bounded")
        try:
            return self._search(query, top_k, candidate_k, sources, mode or self.mode)
        finally:
            self.capacity.release()

    def _search(self, query, top_k, candidate_k, sources, mode):
        if mode not in {"hybrid", "bm25", "medcpt"}:
            raise ValueError("Unknown retrieval mode")
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ValueError("Retrieval query must contain 1 to 2000 characters")
        if sources and not set(sources).issubset({"pubmed", "textbooks", "statpearls"}):
            raise ValueError("Unknown corpus source filter")
        top_k, candidate_k = max(1, min(int(top_k), 128)), max(1, min(int(candidate_k), 128))
        candidate_k = max(top_k, candidate_k)
        prepared, terms, expansions = common_query(query)
        started = time.monotonic()
        dense_status = self.dense.status()
        wants_dense = mode != "bm25"
        can_degrade = mode == "hybrid" and self.allow_degraded
        if wants_dense and not dense_status.get("ready") and not can_degrade:
            raise CorpusUnavailable("Independent MedCPT retrieval is not ready: " + str(dense_status.get("error", "index/runtime required")))
        diagnostics = {"query_terms": terms, "terminology_expansion": expansions,
                       "untranslated_segments": untranslated_segments(query),
                       "prepared_query": prepared, "translation_method": "explicit terminology dictionary; not general translation",
                       "candidate_limit_per_channel": candidate_k, "rrf_k": 60,
                       "rrf_weights": {"bm25": 1, "medcpt": 1}, "warnings": [],
                       "independent_dense_recall": False}
        if diagnostics["untranslated_segments"]:
            diagnostics["warnings"].append("中文术语字典未覆盖部分词语；不丢弃未知概念来生成回答，请提供完整英文问题。")
        if not prepared:
            return {"hits": [], "sparse_hits": [], "dense_hits": [], "mode": "no_supported_query",
                    "degraded": False, "diagnostics": {**diagnostics, "candidates_retrieved": 0}}
        sparse_future = self._pool.submit(self.sparse.search, prepared, candidate_k, candidate_k, sources) if mode != "medcpt" else None
        dense_future = self._pool.submit(self.dense.search, prepared, candidate_k, sources) if wants_dense and dense_status.get("ready") else None
        # Always drain both bounded workers before releasing capacity, including
        # on failure; cancelled clients must not accumulate abandoned searches.
        errors, sparse_result, dense_result = [], {}, {}
        if sparse_future:
            try:
                sparse_result = sparse_future.result()
            except Exception as error:
                errors.append(error)
        if dense_future:
            try:
                dense_result = dense_future.result()
            except CorpusUnavailable as error:
                if not can_degrade:
                    errors.append(error)
                else:
                    diagnostics["warnings"].append("MedCPT失败，已显式降级为BM25；不是双路检索。")
            except Exception as error:
                errors.append(error)
        if errors:
            raise errors[0]
        sparse_hits = sparse_result.get("hits", [])
        dense_raw = dense_result.get("hits", [])
        dense_hits = self.sparse.documents([item["row_index"] for item in dense_raw]) if dense_raw else []
        for document, vector_hit in zip(dense_hits, dense_raw):
            if sources and document.get("source") not in sources:
                raise CorpusUnavailable("Dense source-filter contract disagrees with resolved corpus provenance")
            document.update(dense_score=vector_hit["dense_score"], dense_rank=vector_hit["dense_rank"],
                            score=vector_hit["dense_score"], score_type=("medcpt_approximate_inner_product" if
                                dense_result.get("diagnostics", {}).get("approximate") else "medcpt_raw_inner_product"),
                            dense_approximate=bool(dense_result.get("diagnostics", {}).get("approximate")),
                            retrieval_channels=["medcpt"])
        for document in sparse_hits:
            document["retrieval_channels"] = ["bm25"]
        for document in sparse_hits + dense_hits:
            annotate(document, terms)
        fused = reciprocal_rank_fusion(sparse_hits, dense_hits)
        dense_ran = bool(dense_result) and wants_dense
        is_dual = dense_ran and mode == "hybrid"
        actual_mode = "hybrid_medcpt_bm25" if is_dual else ("medcpt" if dense_ran else ("bm25_degraded" if wants_dense else "bm25"))
        if wants_dense and not dense_ran:
            diagnostics["warnings"].append("MedCPT未就绪或失败，当前结果仅为BM25；不是双路已跑通。")
        diagnostics.update(candidates_retrieved=len(fused), independent_dense_recall=dense_ran,
                           dual_route_executed=is_dual,
                           channels={"bm25": {"ready": bool(sparse_future), "count": len(sparse_hits), **sparse_result.get("diagnostics", {})},
                                     "medcpt": {**dense_status, "ready": dense_ran,
                                                "count": len(dense_hits), **dense_result.get("diagnostics", {})}},
                           elapsed_ms=round((time.monotonic() - started) * 1000, 2))
        diagnostics["warnings"].extend(sparse_result.get("diagnostics", {}).get("warnings", []))
        return {"hits": fused[:top_k], "sparse_hits": sparse_hits, "dense_hits": dense_hits,
                "mode": actual_mode, "degraded": wants_dense and not dense_ran, "diagnostics": diagnostics}
