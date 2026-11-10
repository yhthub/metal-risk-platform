"""Sequential, bounded BM25 federation over MedRR and three local evidence DBs.

The original databases and scores remain separate. No dense service is created,
no corpus is rewritten, and source categories do not establish evidence quality.
"""
from __future__ import annotations

import math
import os
import threading
import time

from .corpus_retrieval_service import CorpusRetrievalService, CorpusUnavailable, RetrievalTimeout, lexical_terms
from .local_evidence_service import LocalEvidenceRetrievalService, DATABASES, QUALITY_NOTICE, query_terms, fts_group
from .retrieval_text import term_present


MEDRR_SOURCES = ("pubmed", "textbooks", "statpearls")
LOCAL_SOURCES = tuple(DATABASES)
ALL_SOURCES = MEDRR_SOURCES + LOCAL_SOURCES
PARTITIONS = ("medrr", *LOCAL_SOURCES)


class CombinedBm25RetrievalService:
    mode = "bm25"
    medcpt_rerank = False
    knowledge_bases = [
        {"id": "pubmed", "name": "PubMed标题/摘要"},
        {"id": "textbooks", "name": "医学教材"},
        {"id": "statpearls", "name": "StatPearls"},
        *[{"id": key, "name": label} for key, (_, label) in DATABASES.items()],
    ]

    def __init__(self, medrr=None, local=None, *, timeout_seconds=None):
        # None disables only the inherited 18-term truncation. The outer query
        # gate below bounds the complete query at 24 concepts before any I/O.
        self.medrr = medrr if medrr is not None else CorpusRetrievalService(
            medcpt_rerank=False, lexical_term_limit=None)
        self.local = local if local is not None else LocalEvidenceRetrievalService()
        value = float(timeout_seconds if timeout_seconds is not None else os.getenv(
            "RAG_COMBINED_RETRIEVAL_TIMEOUT_SECONDS", os.getenv("RAG_RETRIEVAL_TIMEOUT_SECONDS", "8")))
        if not math.isfinite(value):
            raise ValueError("Combined retrieval timeout must be finite")
        self.timeout_seconds = max(.1, min(value, 30.0))
        self.capacity = threading.BoundedSemaphore(1)

    def status(self):
        medrr, local = self.medrr.status(), self.local.status()
        ready = bool(medrr.get("ready") and local.get("ready"))
        some_ready = bool(medrr.get("ready") or local.get("ready") or any(
            item.get("ready") for item in local.get("databases", {}).values()))
        # Never relabel the original MedRR count as the combined total. Local
        # schema checks do not count rows, and unknown counts are explicitly null.
        counts = {
            "medrr": {"total_chunks": medrr.get("total_chunks"),
                      "source_counts": medrr.get("source_counts"),
                      "basis": medrr.get("counts_basis", "unavailable")},
            "local_evidence": {"total_chunks": None,
                               "source_counts": {source: None for source in LOCAL_SOURCES},
                               "basis": "not counted; read-only schema checks only"},
        }
        return {"ready": ready, "corpus_ready": ready,
                "name": "MedRR 医学库＋职业金属暴露证据库", "backend": "combined_bm25",
                "mode": "bm25", "engine": "federated_sqlite_fts5_bm25", "read_only": True,
                "degraded": some_ready and not ready, "partial": some_ready and not ready,
                "total_chunks": None, "counts": counts,
                "libraries": {"medrr": medrr, "local_evidence": local},
                "channels": {"bm25": {"ready": ready, "partial": some_ready and not ready,
                                        "scope": "MedRR database and three local evidence databases"},
                             "medcpt": {"ready": False, "scope": "disabled in combined BM25 mode"}},
                "independent_dense_recall": False,
                "readiness_basis": "separate library preflights; no full-row count, model load or quality audit",
                "warnings": [QUALITY_NOTICE]}

    def search(self, query, top_k=8, candidate_k=32, sources=None, mode=None):
        if not self.capacity.acquire(blocking=False):
            raise CorpusUnavailable("Combined retrieval is busy; only one request is allowed")
        try:
            return self._search(query, top_k, candidate_k, sources, mode)
        finally:
            self.capacity.release()

    def _search(self, query, top_k, candidate_k, sources, mode):
        if mode not in {None, "bm25"}:
            raise ValueError("Combined retrieval supports BM25 only; dense retrieval is disabled")
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ValueError("Retrieval query must contain 1 to 2000 characters")
        if sources is not None and (not isinstance(sources, (list, tuple, set)) or
                                    any(source not in ALL_SOURCES for source in sources)):
            raise ValueError("Unknown combined evidence source filter")
        # Both underlying implementations treat [] as all: never pass an empty
        # subset to either one. Only None means the default six-source search.
        selected_sources = list(ALL_SOURCES) if sources is None else list(dict.fromkeys(sources))
        top_k = max(1, min(int(top_k), 12))
        candidate_k = max(top_k, min(int(candidate_k), 32))
        terms, translations = query_terms(query)
        started = time.monotonic()
        deadline = started + self.timeout_seconds
        diagnostics = {"backend": "combined_bm25", "query_terms": terms,
                       "terminology_expansion": translations, "prepared_query": query,
                       "translation_method": "explicit lexical expansion; all final anchors retained",
                       "untranslated_segments": [], "sources": selected_sources,
                       "candidate_limit_per_database": candidate_k, "candidate_limit": candidate_k,
                       "timeout_seconds": self.timeout_seconds, "execution": "sequential",
                       "independent_dense_recall": False, "dual_route_executed": False,
                       "libraries": {}, "warnings": [QUALITY_NOTICE]}
        if not selected_sources:
            diagnostics["search_state"] = "empty_source_selection"
            return self._result([], diagnostics, started, top_k, complete=True, executed=False)
        if len(terms) > 24 or not terms:
            diagnostics["query_limit_exceeded"] = len(terms) > 24
            diagnostics["search_state"] = "query_limit_exceeded" if terms else "no_supported_query"
            diagnostics["warnings"].append("检索概念须为1至24个；未截断问题条件，也未执行检索。")
            return self._result([], diagnostics, started, top_k, complete=False, executed=False)

        old_sources = [source for source in MEDRR_SOURCES if source in selected_sources]
        jobs = [("medrr", self.medrr, old_sources)] if old_sources else []
        jobs += [(source, self.local, [source]) for source in LOCAL_SOURCES if source in selected_sources]
        medrr_terms, _ = lexical_terms(query, limit=None)
        local_unsupported_terms = [term for term in terms if fts_group(term) is None]
        unsupported_sources = []
        hits, failures, succeeded = [], [], 0
        for partition, service, subset in jobs:
            unsupported = not medrr_terms if partition == "medrr" else bool(local_unsupported_terms)
            if unsupported:
                unsupported_sources.extend(subset)
                diagnostics["libraries"][partition] = {
                    "ready": False, "searched": False, "blocked": True,
                    "status": "unsupported_query", "sources": subset, "count": 0,
                    "unsupported_terms": terms if partition == "medrr" else local_unsupported_terms,
                }
                diagnostics["warnings"].append(f"{partition} 无法将当前条件转换为索引查询；未访问该分库，不代表库中没有相关证据。")
                continue
            try:
                # All three MedRR sources are the whole physical database.
                # Preserve its FTS-first LIMIT path; a redundant source JOIN
                # can otherwise rank many postings before finding enough rows.
                # Empty selections never reach this loop and are not widened.
                query_sources = None if partition == "medrr" and subset == list(MEDRR_SOURCES) else subset
                result = self._search_one(service, query, candidate_k, query_sources, deadline)
                child_diagnostics = result.get("diagnostics", {})
                if result.get("degraded") or result.get("mode") != "bm25":
                    raise CorpusUnavailable("A combined partition did not complete in BM25 mode")
                child_hits = result.get("sparse_hits", result.get("hits", []))[:candidate_k]
                normalized = [self._hit(hit, partition, rank + 1, terms, subset)
                              for rank, hit in enumerate(child_hits)]
                hits.extend(normalized)
                succeeded += 1
                diagnostics["libraries"][partition] = {
                    "ready": True, "searched": True, "sources": subset, "count": len(normalized),
                    "diagnostics": child_diagnostics,
                    # MedRR's English lexer cannot index unknown Chinese terms;
                    # these still constrain full-query coverage and RAG anchors.
                    "final_anchor_only_terms": [term for term in terms if term not in
                                                child_diagnostics.get("query_terms", terms)],
                }
                diagnostics["warnings"].extend(child_diagnostics.get("warnings", []))
            except (CorpusUnavailable, RetrievalTimeout) as error:
                failures.append(error)
                diagnostics["libraries"][partition] = {
                    "ready": False, "searched": False, "sources": subset, "count": 0,
                    "error_type": type(error).__name__, "error": str(error),
                }
                diagnostics["warnings"].append(f"{partition} 检索未完成：{type(error).__name__}；其他分库结果不代表全部库成功。")
        diagnostics["unsupported_sources"] = unsupported_sources
        diagnostics["failed_sources"] = [source for item in diagnostics["libraries"].values()
                                         if "error_type" in item for source in item["sources"]]
        if not succeeded:
            if not failures:
                diagnostics["search_state"] = "unsupported_query"
                return self._result([], diagnostics, started, top_k, complete=False, executed=False)
            if failures and all(isinstance(error, RetrievalTimeout) for error in failures):
                raise RetrievalTimeout("All requested combined partitions exceeded the shared query budget")
            raise CorpusUnavailable("All requested combined retrieval partitions are unavailable")

        # Each database gets the same bounded candidate allowance. Coverage is
        # measured on the entire original query, then equal within-database ranks
        # interleave deterministically; never compare cross-database BM25 scores.
        hits.sort(key=lambda hit: (-hit["query_term_coverage"], hit["partition_rank"],
                                   PARTITIONS.index(hit["retrieval_partition"]), hit["chunk_id"]))
        unique = {}
        for hit in hits:
            unique.setdefault(hit["chunk_id"], hit)
        hits = list(unique.values())[:candidate_k]
        for rank, hit in enumerate(hits, 1):
            hit["combined_rank"] = rank
        complete = not failures and not unsupported_sources
        diagnostics["search_state"] = "complete" if complete else "partial"
        return self._result(hits, diagnostics, started, top_k, complete=complete, executed=True)

    @staticmethod
    def _search_one(service, query, candidate_k, sources, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RetrievalTimeout("Shared combined retrieval budget exhausted before this partition")
        # Instances belong to this adapter and all searches share its semaphore.
        # Give each SQLite progress handler only the remaining request budget.
        original_timeout = service.timeout_seconds
        service.timeout_seconds = min(original_timeout, remaining)
        try:
            return service.search(query, top_k=candidate_k, candidate_k=candidate_k, sources=sources)
        finally:
            service.timeout_seconds = original_timeout

    @staticmethod
    def _hit(hit, partition, rank, terms, allowed_sources):
        source = hit.get("source")
        if source not in allowed_sources:
            raise CorpusUnavailable("A partition returned a source outside its requested filter")
        backend = "medrr" if partition == "medrr" else "local_evidence"
        original_chunk = hit.get("original_chunk_id", hit["chunk_id"])
        original_document = hit.get("original_document_id", hit.get("document_id", original_chunk))
        matched = [term for term in terms if term_present(
            str(hit.get("title", "")) + " " + str(hit.get("content", "")), term)]
        return {**hit, "chunk_id": f"{backend}/{source}/{original_chunk}",
                "document_id": f"{backend}/{source}/{original_document}",
                "original_chunk_id": original_chunk, "original_document_id": original_document,
                "retrieval_backend": backend, "retrieval_partition": partition, "partition_rank": rank,
                "source": source, "channel": hit.get("channel") or ("scientific" if backend == "medrr" else source),
                "url": hit.get("url") or hit.get("source_url"),
                "metadata_quality_verified": False, "retrieval_channels": ["bm25"], "dense_score": None,
                "matched_query_terms": matched, "query_term_coverage": len(matched) / len(terms),
                "match_tier": "all_terms" if len(matched) == len(terms) else "partial_terms"}

    @staticmethod
    def _result(hits, diagnostics, started, top_k, *, complete, executed):
        partial = executed and not complete
        diagnostics.update(
            all_requested_sources_searched=complete, partial=partial,
            candidates_retrieved=len(hits), elapsed_ms=round((time.monotonic() - started) * 1000, 2),
            ranking="full-query concept coverage, then within-database rank, then fixed database order; raw BM25 scores are not compared across databases",
            channels={"bm25": {"ready": executed, "complete": complete, "partial": partial, "count": len(hits)},
                      "medcpt": {"ready": False, "count": 0, "scope": "disabled in combined BM25 mode"}},
        )
        diagnostics["warnings"] = list(dict.fromkeys(diagnostics["warnings"]))
        return {"hits": hits[:top_k], "sparse_hits": hits, "dense_hits": [],
                "mode": "bm25", "degraded": partial, "partial": partial, "diagnostics": diagnostics}
