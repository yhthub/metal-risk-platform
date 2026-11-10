"""Bounded read-only FTS5 access to the original local evidence-pipeline DBs.

No embeddings, model loading, corpus export, index build or database writes.
Historical metadata is provenance, not a verified evidence-quality judgement.
"""
from __future__ import annotations

import os
import re
import sqlite3
import threading
import time
from contextlib import closing
from pathlib import Path

from .corpus_retrieval_service import CorpusUnavailable, RetrievalTimeout, lexical_terms
from .hybrid_retrieval_service import untranslated_segments
from .retrieval_text import term_aliases, term_present


DEFAULT_DB_DIR = Path("D:/研究生资料材料/研1/智能风险预测干预系统/evidence-pipeline/data/db")
DATABASES = {
    "normative": ("evidence.db", "本地规范资料"),
    "scientific": ("scientific_evidence.db", "本地科学文献"),
    "guidelines": ("guidelines_evidence.db", "本地指南资料"),
}
# FTS trigram requires at least three characters. These are explicit lexical
# expansions, not inferred effects or automatic verification of standards.
SHORT_TERM_EXPANSIONS = {
    "lead": ["铅中毒", "铅及其", "血铅水平"],
    "cadmium": ["镉中毒", "镉及其", "尿镉水平"],
    "mercury": ["汞中毒", "汞及其", "甲基汞"],
    "arsenic": ["砷中毒", "砷及其", "无机砷"],
    "chromium": ["铬中毒", "六价铬"],
    "nickel": ["镍及其", "羰基镍"],
    "manganese": ["锰中毒", "锰及其"],
    "cobalt": ["钴及其", "硬质合金"],
    "exposure": ["职业接触", "职业暴露", "复合暴露"],
    "blood": ["血液中", "血铅水平", "血压测量"],
    "pressure": ["高血压", "血压测量"],
    "kidney": ["肾损伤", "肾功能", "肾小管"],
    "renal": ["肾损伤", "肾功能", "肾小管"],
}
QUALITY_NOTICE = "本地历史库的来源类型和证据等级标签未在本次重新核验；检索命中不代表规范现行有效或指南质量已确认。"


def query_terms(query):
    terms, translations = lexical_terms(query, limit=None)
    # Keep unknown Chinese concepts too. They must never vanish merely because
    # the small bilingual dictionary cannot translate them.
    for fragment in untranslated_segments(query):
        if fragment not in terms:
            terms.append(fragment)
    return terms, translations


def fts_group(term):
    aliases = list(dict.fromkeys([*term_aliases(term), *SHORT_TERM_EXPANSIONS.get(term, [])]))
    literals = ['"' + word.replace('"', '""') + '"' for word in aliases if len(word) >= 3]
    return '(' + ' OR '.join(literals) + ')' if literals else None


class LocalEvidenceRetrievalService:
    mode = "bm25"
    medcpt_rerank = False
    knowledge_bases = [{"id": key, "name": label} for key, (_, label) in DATABASES.items()]

    def __init__(self, root=None, *, timeout_seconds=None):
        self.root = Path(root or os.getenv("RAG_EVIDENCE_DB_DIR", str(DEFAULT_DB_DIR))).expanduser().resolve()
        self.timeout_seconds = max(.1, min(float(timeout_seconds if timeout_seconds is not None else
                                               os.getenv("RAG_LOCAL_DB_TIMEOUT_SECONDS", "3")), 10.0))
        self.capacity = threading.BoundedSemaphore(1)

    def _connect(self, path, deadline):
        # mode=ro refuses to create a missing file and respects existing WAL.
        if not path.is_file():
            raise CorpusUnavailable("Local evidence database is missing: " + path.name)
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=.2)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA cache_size=-2048")
        connection.execute("PRAGMA mmap_size=0")
        connection.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        return connection

    def status(self):
        details = {}
        deadline = time.monotonic() + self.timeout_seconds
        for source, (filename, _) in DATABASES.items():
            path = self.root / filename
            try:
                with closing(self._connect(path, deadline)) as conn:
                    tables = {row[0] for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE name IN "
                        "('evidence_documents','evidence_chunks','evidence_chunks_fts')")}
                    if len(tables) != 3:
                        raise CorpusUnavailable("Local evidence database schema is incomplete")
                    conn.execute("SELECT c.chunk_id, c.text, d.title, d.source_url, d.doi_or_standard_no "
                                 "FROM evidence_chunks c JOIN evidence_documents d "
                                 "ON c.document_id=d.document_id LIMIT 0")
                details[source] = {"ready": True, "database": filename, "bytes": path.stat().st_size}
            except (OSError, sqlite3.Error, CorpusUnavailable) as error:
                details[source] = {"ready": False, "database": filename,
                                   "error": type(error).__name__ + ": local evidence source unavailable"}
        ready = all(item["ready"] for item in details.values())
        return {"ready": ready, "corpus_ready": ready, "name": "本地职业金属暴露证据库",
                "backend": "local_evidence", "mode": "bm25", "engine": "sqlite_fts5_bm25",
                "read_only": True, "degraded": False, "root": str(self.root), "databases": details,
                "readiness_basis": "read-only schema check; no full-row count or content quality audit",
                "channels": {"bm25": {"ready": ready, "scope": "three local evidence-pipeline databases"},
                             "medcpt": {"ready": False, "scope": "disabled in local lightweight mode"}},
                "independent_dense_recall": False, "warnings": [QUALITY_NOTICE]}

    def search(self, query, top_k=8, candidate_k=32, sources=None, mode=None):
        if not self.capacity.acquire(blocking=False):
            raise CorpusUnavailable("Local retrieval is busy; only one request is allowed")
        try:
            return self._search(query, top_k, candidate_k, sources, mode)
        finally:
            self.capacity.release()

    def _search(self, query, top_k, candidate_k, sources, mode):
        if mode not in {None, "bm25"}:
            raise ValueError("Local evidence mode supports BM25 only; dense retrieval is disabled")
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ValueError("Retrieval query must contain 1 to 2000 characters")
        if sources and not set(sources).issubset(DATABASES):
            raise ValueError("Unknown local evidence source filter")
        top_k = max(1, min(int(top_k), 12))
        candidate_k = max(top_k, min(int(candidate_k), 32))
        selected_sources = list(dict.fromkeys(sources or DATABASES))
        started = time.monotonic()
        deadline = started + self.timeout_seconds
        terms, translations = query_terms(query)
        diagnostics = {"query_terms": terms, "terminology_expansion": translations,
                       "prepared_query": query, "translation_method": "explicit bilingual lexical expansion; original concepts retained",
                       "independent_dense_recall": False, "dual_route_executed": False,
                       "candidate_limit_per_database": candidate_k, "sources": selected_sources,
                       "warnings": [QUALITY_NOTICE], "untranslated_segments": []}
        if len(terms) > 24:
            diagnostics["query_limit_exceeded"] = True
            diagnostics["warnings"].append("问题包含超过24个检索概念，请拆分问题；未截断条件，也未执行检索。")
            return self._result([], diagnostics, started)
        groups = [fts_group(term) for term in terms]
        if not terms or any(group is None for group in groups):
            diagnostics["warnings"].append("现有trigram索引无法单独匹配不足3字符且无明确展开的词语，请补充具体主题。")
            return self._result([], diagnostics, started)

        hits = []
        for source in selected_sources:
            path = self.root / DATABASES[source][0]
            try:
                with closing(self._connect(path, deadline)) as conn:
                    rows = self._query(conn, " AND ".join(groups), candidate_k)
                    # Supplement candidates without pretending partial matches
                    # support every concept. The RAG anchor check remains strict.
                    if len(rows) < top_k and len(groups) > 1:
                        seen = {row["id"] for row in rows}
                        for row in self._query(conn, " OR ".join(groups), candidate_k):
                            if row["id"] not in seen:
                                rows.append(row)
                                seen.add(row["id"])
                            if len(rows) >= candidate_k:
                                break
                    rows.sort(key=lambda row: (row["bm25_score"], row["id"]))
                    hits.extend(self._hit(source, row, rank + 1, terms) for rank, row in enumerate(rows))
            except sqlite3.OperationalError as error:
                if "interrupted" in str(error).lower():
                    raise RetrievalTimeout("Local evidence retrieval exceeded the bounded query budget") from error
                raise CorpusUnavailable("Local evidence FTS query failed: " + path.name) from error
            except (sqlite3.Error, OSError) as error:
                raise CorpusUnavailable("Local evidence database could not be read: " + path.name) from error
        # BM25 scores from separate databases have different corpus statistics.
        # Interleave by within-source rank; do not compare raw scores across DBs.
        hits.sort(key=lambda hit: (-hit["query_term_coverage"], hit["lexical_rank"], hit["chunk_id"]))
        hits = hits[:candidate_k]
        return self._result(hits, diagnostics, started, top_k)

    @staticmethod
    def _query(conn, expression, limit):
        return list(conn.execute(
            "SELECT c.id,c.chunk_id,c.document_id,c.text,c.section_title,c.page,c.clause_no,c.source_text_hash,"
            "d.title,d.source_url,d.doi_or_standard_no,d.source_channel,d.document_type,d.study_design,"
            "d.evidence_priority,d.source_verified,d.workflow_state,f.bm25_score "
            "FROM (SELECT rowid,rank AS bm25_score FROM evidence_chunks_fts "
            "WHERE evidence_chunks_fts MATCH ? ORDER BY rank LIMIT ?) f "
            "JOIN evidence_chunks c ON c.id=f.rowid "
            "JOIN evidence_documents d ON d.document_id=c.document_id "
            "ORDER BY f.bm25_score,c.id", (expression, limit)).fetchall())

    @staticmethod
    def _hit(source, row, rank, terms):
        content = str(row["text"] or "")
        title = str(row["title"] or "")
        excerpt = content[:12000]
        matched = [term for term in terms if term_present(title + " " + excerpt, term)]
        identifier = str(row["doi_or_standard_no"] or "").strip()
        doi = identifier if re.fullmatch(r"10\.\d{4,9}/\S+", identifier, re.I) else None
        return {"chunk_id": source + "/" + str(row["chunk_id"]),
                "document_id": source + "/" + str(row["document_id"]),
                "original_chunk_id": row["chunk_id"], "original_document_id": row["document_id"],
                "row_index": int(row["id"]), "source": source, "corpus": source, "channel": source,
                "title": title, "content": excerpt, "content_truncated": len(content) > len(excerpt),
                "content_length": len(content), "source_url": row["source_url"], "url": row["source_url"],
                "doi": doi, "pmid": None, "standard_no_or_doi": identifier or None,
                "section_title": row["section_title"], "page": row["page"], "clause_no": row["clause_no"],
                "source_text_hash": row["source_text_hash"],
                "source_metadata": {key: row[key] for key in ("source_channel", "document_type", "study_design",
                                        "evidence_priority", "source_verified", "workflow_state")},
                "metadata_quality_verified": False,
                "score": float(row["bm25_score"]), "bm25_score": float(row["bm25_score"]),
                "score_type": "fts5_bm25_within_source_lower_is_better", "lexical_rank": rank,
                "dense_score": None, "retrieval_channels": ["bm25"], "matched_query_terms": matched,
                "query_term_coverage": len(matched) / len(terms) if terms else 0.0,
                "match_tier": "all_terms" if terms and len(matched) == len(terms) else "partial_terms"}

    @staticmethod
    def _result(hits, diagnostics, started, top_k=8):
        diagnostics.update(candidates_retrieved=len(hits), elapsed_ms=round((time.monotonic() - started) * 1000, 2),
                           ranking="query concept coverage then within-source BM25 rank; raw cross-database scores not compared",
                           channels={"bm25": {"ready": True, "count": len(hits)},
                                     "medcpt": {"ready": False, "count": 0, "scope": "disabled in local lightweight mode"}})
        return {"hits": hits[:top_k], "sparse_hits": hits, "dense_hits": [],
                "mode": "bm25", "degraded": False, "diagnostics": diagnostics}
