"""Bounded retrieval from the exported MedRAG/MedCPT corpus, never a live DB.

The default engine is genuine SQLite FTS5/BM25. Optional MedCPT computes
actual inner products on BM25 candidates only: it is a candidate reranker,
not an independent all-corpus dense search. No metadata or scores are invented.
"""

from __future__ import annotations

import bisect
import json
import math
import os
import re
import sqlite3
import stat
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


class CorpusUnavailable(RuntimeError):
    """Corpus is missing, mutable, unverified, incompatible, or inaccessible."""


class RetrievalTimeout(RuntimeError):
    """The bounded lexical query exceeded its resource budget."""


MAX_RESTORE_RECEIPT_BYTES = 4 * 1024 * 1024


# Deliberately small terminology dictionary, not a hidden translator or model.
# The corpus is predominantly English. Caller may supply a reviewed English
# retrieval query; this expansion is useful for common Chinese health terms.
TERMS = {
    "血铅": "blood lead", "铅": "lead", "镉": "cadmium", "汞": "mercury",
    "砷": "arsenic", "铬": "chromium", "镍": "nickel", "锰": "manganese",
    "钴": "cobalt", "硒": "selenium", "重金属": "heavy metal",
    "职业暴露": "occupational exposure", "复合暴露": "mixture exposure",
    "职业": "occupational", "暴露": "exposure",
    "肾": "kidney", "肾小管": "renal tubular", "血压": "blood pressure",
    "高血压": "hypertension", "糖尿病": "diabetes", "肺癌": "lung cancer",
    "癌症": "cancer", "神经": "neurological", "贫血": "anemia",
    "骨质疏松": "osteoporosis", "认知": "cognition", "心血管": "cardiovascular",
    "炎症": "inflammation", "螯合": "chelation", "随机试验": "randomized trial",
    "系统综述": "systematic review", "荟萃分析": "meta analysis",
    "妊娠": "pregnancy", "儿童": "children", "成年人": "adults",
    "阿尔茨海默": "alzheimer", "阿兹海默": "alzheimer", "痴呆": "dementia",
    "肾损伤": "kidney injury", "肾功能": "renal function", "肾毒性": "nephrotoxicity",
    "神经毒性": "neurotoxicity", "肝": "liver", "损伤": "injury", "中毒": "poisoning",
    "人体": "human", "人群": "human", "工人": "workers", "成人": "adults", "金属": "metal",
}
STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "of", "to", "in", "on", "at", "for", "from", "with", "and", "or",
    "what", "which", "how", "does", "do", "can", "could", "would", "should",
    "it", "its", "that", "this", "these", "those", "please", "tell", "me",
    "about", "evidence", "study", "studies", "effect", "effects", "risk",
})
def lexical_terms(query: str) -> tuple[list[str], list[str]]:
    """Make safe, limited literal FTS terms; never interpolate FTS operators."""
    normalized = query.casefold()
    translations: list[str] = []
    # Prefer the longest matching concept: 血压 should not double-count 高血压.
    remaining = normalized
    for chinese, english in sorted(TERMS.items(), key=lambda item: -len(item[0])):
        if chinese in remaining:
            translations.append(english)
            remaining = remaining.replace(chinese, " ")
    tokens = re.findall(r"[a-z][a-z0-9]*(?:[-'][a-z0-9]+)*", normalized)
    tokens += [word for phrase in translations for word in phrase.split()]
    unique: list[str] = []
    for token in tokens:
        if token not in STOP_WORDS and len(token) > 1 and token not in unique:
            unique.append(token)
    return unique[:18], translations


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object")
        return payload
    except (OSError, ValueError) as exc:
        raise CorpusUnavailable(f"Missing or invalid corpus catalog: {path.name}") from exc


def _under_root(root: Path, value: str) -> Path:
    """Portable manifests contain relative paths, not old host absolute paths."""
    path = Path(value.replace("\\", "/"))
    if path.is_absolute() or re.match(r"^[A-Za-z]:", value):
        raise CorpusUnavailable("Corpus manifest must contain relative paths")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise CorpusUnavailable("Corpus manifest path escapes configured root")
    return resolved


class CorpusRetrievalService:
    def __init__(self, root: str | Path | None = None, *, timeout_seconds: float | None = None,
                 medcpt_rerank: bool | None = None, require_restore_receipt: bool | None = None):
        default = "E:/医学检索库_完整_20261010" if os.name == "nt" else "/data/medical-corpus"
        self.root = Path(root or os.getenv("RAG_CORPUS_ROOT", default)).expanduser().resolve()
        self.timeout_seconds = max(0.1, min(float(timeout_seconds if timeout_seconds is not None
            else os.getenv("RAG_RETRIEVAL_TIMEOUT_SECONDS", "8")), 30.0))
        self.medcpt_rerank = medcpt_rerank if medcpt_rerank is not None else (
            os.getenv("RAG_MEDCPT_RERANK", "false").casefold() == "true")
        self.require_restore_receipt = require_restore_receipt if require_restore_receipt is not None else (
            os.getenv("RAG_REQUIRE_RESTORE_RECEIPT", "false").strip().casefold() == "true")
        self._manifest: dict[str, Any] | None = None
        self._db_path: Path | None = None
        self._lock = threading.Lock()
        self._encoder_lock = threading.Lock()
        self._query_encoder: Any = None
        self._tokenizer: Any = None
        self._shards: list[dict[str, Any]] = []
        self._shard_ends: list[int] = []

    def _verify_restore_receipt(self, database_bytes: int | None = None) -> dict[str, Any] | None:
        """Optional deployment gate; a published inode alone is not restore PASS.

        Reread the small atomically replaced public receipt on every request,
        including immediately before SQLite opens. Never hash/count the corpus
        or expose receipt contents in API diagnostics.
        """
        if not self.require_restore_receipt:
            return None
        path = self.root.parent / "restore_receipt.json"
        try:
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_RESTORE_RECEIPT_BYTES:
                raise ValueError("Invalid restore receipt file")
            with path.open("rb") as stream:
                opened = os.fstat(stream.fileno())
                if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                    raise ValueError("Restore receipt changed before opening")
                raw = stream.read(MAX_RESTORE_RECEIPT_BYTES + 1)
            if len(raw) > MAX_RESTORE_RECEIPT_BYTES:
                raise ValueError("Restore receipt is too large")
            receipt = json.loads(raw.decode("utf-8-sig"))
        except (OSError, ValueError, RecursionError) as exc:
            raise CorpusUnavailable("Corpus restore receipt is missing, unreadable, or invalid; retrieval is not ready") from exc
        if not isinstance(receipt, dict) or receipt.get("status") != "PASS" or receipt.get("stage") != "completed":
            raise CorpusUnavailable("Corpus restore has not completed with a PASS receipt; retrieval is not ready")
        checks = ("archive_sha256", "gzip_crc", "decoded_size", "schema_only", "storage", "unpublished_schema")
        basis = receipt.get("corpus_basis")
        expected = receipt.get("expected_decoded_bytes")
        compressed = receipt.get("expected_compressed_bytes")
        if (any(receipt.get(check) != "PASS" for check in checks)
                or receipt.get("published_readonly") is not True
                or not isinstance(basis, dict) or basis.get("fts5_schema_present") is not True
                or type(basis.get("declared_chunks")) is not int or basis["declared_chunks"] <= 0
                or type(expected) is not int or expected <= 0
                or type(compressed) is not int or compressed <= 0
                or type(receipt.get("decoded_bytes")) is not int or receipt["decoded_bytes"] != expected
                or type(basis.get("database_bytes")) is not int or basis["database_bytes"] != expected
                or not isinstance(receipt.get("expected_archive_sha256"), str)
                or re.fullmatch(r"[0-9a-fA-F]{64}", receipt["expected_archive_sha256"]) is None
                or (database_bytes is not None and database_bytes != expected)):
            raise CorpusUnavailable("Corpus restore receipt checks or database identity are incomplete; retrieval is not ready")
        return receipt

    def _verify_snapshot(self) -> tuple[dict[str, Any], Path, tuple[int, int]]:
        # Small catalogs can be reread each request; never run COUNT(*)/integrity
        # scans over the 64 GB database merely to answer a health check.
        with self._lock:
            receipt = self._verify_restore_receipt()
            manifest = self._manifest
            if manifest is None:
                manifest = _read_json(self.root / "UNIFIED_MANIFEST_PORTABLE.json")
                if manifest.get("schema") != "MEDRR-UNIFIED-RETRIEVAL-v1":
                    raise CorpusUnavailable("Unsupported corpus manifest schema")
                db = _under_root(self.root, str(manifest.get("corpus_database", "")))
                self._manifest, self._db_path = manifest, db
            else:
                db = self._db_path
            if db is None:
                raise CorpusUnavailable("Missing corpus database path")
            progress = _read_json(self.root / "00_catalog" / "EXPORT_PROGRESS.json")
            provenance = _read_json(self.root / "00_catalog" / "SNAPSHOT_PROVENANCE.json")
            if progress.get("state") != "COMPLETE":
                raise CorpusUnavailable("Corpus export has not completed")
            if provenance.get("state") != "COMPLETE" or not provenance.get("snapshot_complete_by_backup_api"):
                raise CorpusUnavailable("Corpus is not a verified independent closed snapshot")
            # SQLite immutable=1 ignores WAL entirely. Refuse such a file, rather
            # than accidentally treating mutable production data as immutable.
            try:
                if any(Path(str(db) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
                    raise CorpusUnavailable("Refusing corpus database with WAL/SHM/journal sidecars")
                stat = db.stat()
            except OSError as exc:
                raise CorpusUnavailable("Corpus database or snapshot sidecars are inaccessible") from exc
            expected = int(progress.get("local_database_bytes", 0))
            if expected <= 0 or stat.st_size != expected:
                raise CorpusUnavailable("Corpus database size disagrees with completed export")
            if int(progress.get("total_chunks", -1)) != int(manifest.get("total_rows", -2)):
                raise CorpusUnavailable("Corpus row-axis catalogs disagree")
            if receipt and (receipt["expected_decoded_bytes"] != stat.st_size
                    or receipt["corpus_basis"].get("declared_chunks") != int(manifest["total_rows"])):
                raise CorpusUnavailable("Corpus restore receipt does not match the configured closed snapshot")
            if receipt and os.name == "posix" and stat.st_mode & 0o222:
                raise CorpusUnavailable("Restored corpus database is not published read-only")
            return manifest, db, (stat.st_size, stat.st_mtime_ns)

    def status(self) -> dict[str, Any]:
        """Cheap readiness, declared counts distinguished from runtime validation."""
        try:
            manifest, db, _ = self._verify_snapshot()
            query_path = self._encoder_path()
            return {
                "ready": True, "engine": "sqlite_fts5_bm25", "read_only": True,
                "immutable_snapshot_verified": True,
                "readiness_basis": ("completed restore receipt; " if self.require_restore_receipt else "")
                    + "catalog/file-size/sidecar preflight; FTS checked during search",
                "restore_receipt_required": self.require_restore_receipt,
                "restore_receipt_verified": self.require_restore_receipt,
                "total_chunks": int(manifest["total_rows"]),
                "source_counts": _read_json(self.root / "00_catalog" / "EXPORT_PROGRESS.json").get("source_counts", {}),
                "counts_basis": "completed export catalog, not a new full-row scan",
                "database_bytes": db.stat().st_size,
                "vector_shards": len(manifest.get("vector_shards", [])),
                "medcpt_rerank_enabled": self.medcpt_rerank,
                "query_encoder_available": query_path.is_dir(),
                "dense_scope": "BM25 candidates only, not independent dense recall",
                "metadata_limitations": "Original corpus has no PMID/DOI columns; absent identifiers remain null",
            }
        except CorpusUnavailable as exc:
            return {"ready": False, "engine": "sqlite_fts5_bm25", "error": str(exc),
                    "restore_receipt_required": self.require_restore_receipt,
                    "restore_receipt_verified": False}

    def _connect(self, db: Path) -> sqlite3.Connection:
        if self.require_restore_receipt:
            # Do not cache PASS across an atomic receipt replacement or bypass
            # the gate when this low-level opener is called directly.
            self._verify_restore_receipt()
            try:
                metadata = db.stat()
            except OSError as exc:
                raise CorpusUnavailable("Restored corpus database is inaccessible") from exc
            self._verify_restore_receipt(metadata.st_size)
            if os.name == "posix" and metadata.st_mode & 0o222:
                raise CorpusUnavailable("Restored corpus database is not published read-only")
        connection = sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True,
                                     timeout=self.timeout_seconds)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA temp_store=MEMORY")
        connection.execute("PRAGMA cache_size=-8192")
        return connection

    def search(self, query: str, top_k: int = 8, candidate_k: int = 48,
               sources: list[str] | None = None) -> dict[str, Any]:
        query = query.strip()
        if not query or len(query) > 2000:
            raise ValueError("Retrieval query must contain 1 to 2000 characters")
        top_k = max(1, min(int(top_k), 128))
        candidate_k = max(top_k, min(int(candidate_k), 128))
        allowed = {"pubmed", "textbooks", "statpearls"}
        if sources and not set(sources).issubset(allowed):
            raise ValueError("Unknown corpus source filter")
        manifest, db, identity = self._verify_snapshot()
        tokens, translations = lexical_terms(query)
        diagnostics: dict[str, Any] = {
            "query_terms": tokens, "terminology_expansion": translations,
            "translation_method": "small explicit terminology dictionary, not full translation",
            "candidate_limit": candidate_k, "source_filters": sources or [],
            "independent_dense_recall": False, "warnings": [],
        }
        if not tokens:
            diagnostics["warnings"].append("No supported lexical terms: provide an English retrieval query")
            return {"hits": [], "mode": "bm25", "diagnostics": diagnostics}
        # All terms are quoted literals; user-provided AND/OR/quotes never become
        # operators. AND first improves precision, then OR only if insufficient.
        literals = ['"' + token.replace('"', '""') + '"' for token in tokens]
        started = time.monotonic()
        deadline = started + self.timeout_seconds
        connection = self._connect(db)
        connection.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        try:
            fts_schema = connection.execute("SELECT sql FROM sqlite_master WHERE name='chunks_fts'").fetchone()
            if not fts_schema or "fts5" not in str(fts_schema[0]).casefold():
                raise CorpusUnavailable("Expected chunks_fts FTS5 index is missing")
            rows = self._lexical_query(connection, " AND ".join(literals), candidate_k, sources)
            diagnostics["lexical_operator"] = "AND"
            missing_terms = []
            if not rows and len(literals) > 1:
                # A zero conjunction can otherwise expand an unknown compound
                # into hundreds of thousands of unrelated "kidney" postings.
                # These bounded posting-existence probes have no ranking/sort,
                # COUNT(*) or text scan. They do not assess medical relevance.
                for token, literal in zip(tokens, literals):
                    exists = connection.execute(
                        "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? LIMIT 1", (literal,)
                    ).fetchone()
                    if exists is None:
                        missing_terms.append(token)
                diagnostics["missing_lexical_terms"] = missing_terms
                if missing_terms:
                    diagnostics["lexical_operator"] = "AND; OR skipped because literal terms are absent"
                    diagnostics["warnings"].append(
                        "Some literal query terms are absent from the closed FTS index; "
                        "broad OR expansion was skipped. This does not establish absence of scientific evidence."
                    )
            if not missing_terms and len(rows) < top_k and len(literals) > 1:
                seen = {row["document_id"] for row in rows}
                for row in self._lexical_query(connection, " OR ".join(literals), candidate_k, sources):
                    if row["document_id"] not in seen:
                        rows.append(row)
                        seen.add(row["document_id"])
                    if len(rows) >= candidate_k:
                        break
                diagnostics["lexical_operator"] = "AND then OR supplement"
        except sqlite3.OperationalError as exc:
            if "interrupted" in str(exc).casefold():
                raise RetrievalTimeout("Corpus lexical search exceeded configured timeout") from exc
            raise CorpusUnavailable("Corpus FTS query failed; check database schema/runtime compatibility") from exc
        finally:
            connection.close()
        if (db.stat().st_size, db.stat().st_mtime_ns) != identity:
            raise CorpusUnavailable("Immutable corpus changed during retrieval")
        hits = [self._hit(row, index + 1) for index, row in enumerate(rows)]
        for hit in hits:
            # A lexical coverage flag is not a medical relevance judgment. It
            # prevents an OR-only partial match being presented as full support.
            text = (hit["title"] + " " + hit["content"]).casefold()
            matched = [token for token in tokens if re.search(r"(?<!\w)" + re.escape(token) + r"(?!\w)", text)]
            hit["matched_query_terms"] = matched
            hit["query_term_coverage"] = round(len(matched) / len(tokens), 4)
            hit["match_tier"] = "all_terms" if len(matched) == len(tokens) else "partial_terms"
        diagnostics["all_term_candidates"] = sum(hit["match_tier"] == "all_terms" for hit in hits)
        diagnostics["partial_term_candidates"] = len(hits) - diagnostics["all_term_candidates"]
        if diagnostics["partial_term_candidates"]:
            diagnostics["warnings"].append("OR supplement contains partial lexical matches; hits alone do not establish evidence sufficiency")
        mode = "bm25"
        if self.medcpt_rerank and hits:
            try:
                self._rerank_medcpt(query, hits, manifest)
                mode = "bm25_medcpt_rerank"
            except (ImportError, OSError, ValueError, RuntimeError) as exc:
                # Explicit degraded lexical mode. No rank-derived dense values.
                diagnostics["warnings"].append(f"MedCPT unavailable; genuine BM25 retained ({type(exc).__name__})")
        diagnostics["candidates_retrieved"] = len(hits)
        diagnostics["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)
        return {"hits": hits[:top_k], "mode": mode, "diagnostics": diagnostics}

    def documents(self, row_indices: list[int]) -> list[dict[str, Any]]:
        """Resolve independently recalled vector IDs on the same closed row axis."""
        if len(row_indices) > 256 or any(isinstance(i, bool) or not isinstance(i, int) or i < 0
                                         for i in row_indices):
            raise ValueError("Document lookup requires at most 256 nonnegative integer row IDs")
        if not row_indices:
            return []
        _, db, identity = self._verify_snapshot()
        connection = self._connect(db)
        try:
            marks = ",".join("?" for _ in row_indices)
            rows = connection.execute(f"SELECT *, NULL AS bm25_score FROM chunks WHERE row_index IN ({marks})",
                                      row_indices).fetchall()
            by_row = {int(row["row_index"]): self._hit(row, 0) for row in rows}
        finally:
            connection.close()
        if (db.stat().st_size, db.stat().st_mtime_ns) != identity:
            raise CorpusUnavailable("Immutable corpus changed during document lookup")
        if len(by_row) != len(set(row_indices)):
            raise CorpusUnavailable("Dense row IDs do not match the closed corpus row axis")
        return [by_row[i] for i in row_indices]

    @staticmethod
    def _lexical_query(connection: sqlite3.Connection, expression: str, limit: int,
                       sources: list[str] | None) -> list[sqlite3.Row]:
        # rank is FTS5's real BM25 and ORDER BY rank allows its top-k optimized
        # path. Do not scan 24M rows with LIKE or load all texts into Python.
        parameters: list[Any] = [expression]
        if sources:
            # Join from the FTS candidate iterator, never materialize all row IDs
            # of a source (PubMed alone has 23.9M records and no corpus index).
            placeholders = ",".join("?" for _ in sources)
            parameters.extend(sources)
            parameters.append(limit)
            sql = ("SELECT c.*, chunks_fts.rank AS bm25_score FROM chunks_fts "
                   "JOIN chunks c ON c.row_index=chunks_fts.rowid WHERE chunks_fts MATCH ? "
                   f"AND c.corpus IN ({placeholders}) ORDER BY chunks_fts.rank LIMIT ?")
        else:
            parameters.append(limit)
            sql = (
                "SELECT c.*, f.bm25_score FROM ("
                "SELECT rowid, rank AS bm25_score FROM chunks_fts WHERE chunks_fts MATCH ?"
                " ORDER BY rank LIMIT ?) f "
                "JOIN chunks c ON c.row_index=f.rowid ORDER BY f.bm25_score,c.document_id"
            )
        return list(connection.execute(sql, parameters).fetchall())

    @staticmethod
    def _hit(row: sqlite3.Row, rank: int) -> dict[str, Any]:
        content = str(row["content"])
        # These fields are source provenance, not fabricated paper identifiers.
        # PubMed row IDs are package row IDs, and do NOT encode an actual PMID.
        return {
            "chunk_id": str(row["document_id"]), "row_index": int(row["row_index"]),
            "title": str(row["title"]), "content": content[:12000],
            "content_truncated": len(content) > 12000, "content_length": len(content),
            "source": str(row["corpus"]), "corpus": str(row["corpus"]),
            "source_key": str(row["source_key"]), "source_row": int(row["source_row"]),
            "pmid": None, "doi": None, "source_url": None,
            "score": float(row["bm25_score"]) if row["bm25_score"] is not None else None,
            "score_type": "fts5_bm25_lower_is_better" if row["bm25_score"] is not None else None,
            "lexical_rank": rank, "dense_score": None,
        }

    def _encoder_path(self) -> Path:
        override = os.getenv("RAG_MEDCPT_QUERY_PATH")
        if override:
            return Path(override).expanduser().resolve()
        parent = self.root / "replica_yht/models/MedRR-EBM-Sufficiency/MedCPT/MedCPT-Query-Encoder"
        if (parent / "config.json").is_file():
            return parent
        revisions = sorted(path for path in parent.glob("*") if (path / "config.json").is_file())
        return revisions[0] if len(revisions) == 1 else parent

    def _encode_query(self, query: str) -> Any:
        import torch
        from transformers import AutoModel, AutoTokenizer

        with self._encoder_lock:
            device = os.getenv("RAG_EMBEDDING_DEVICE", "cpu")
            if self._query_encoder is None:
                encoder_path = str(self._encoder_path())
                self._tokenizer = AutoTokenizer.from_pretrained(encoder_path, local_files_only=True)
                self._query_encoder = AutoModel.from_pretrained(encoder_path, local_files_only=True)
                self._query_encoder.to(device).eval()
            inputs = self._tokenizer([query], padding=True, truncation=True, max_length=64,
                                     return_tensors="pt").to(device)
            with torch.inference_mode():
                vector = self._query_encoder(**inputs).last_hidden_state[:, 0, :]
            return vector[0].float().cpu().numpy()

    def _rerank_medcpt(self, query: str, hits: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
        import numpy as np

        if (manifest.get("document_encoder") != "ncbi/MedCPT-Article-Encoder"
                or manifest.get("dimensions") != 768 or manifest.get("dtype") != "float32"
                or manifest.get("similarity") != "raw_inner_product"
                or manifest.get("normalization") != "none"):
            raise ValueError("MedCPT vector contract is incompatible")
        query_vector = self._encode_query(query)
        if query_vector.shape != (768,) or not np.isfinite(query_vector).all():
            raise ValueError("Invalid MedCPT query vector")
        if not self._shards:
            self._shards = sorted(manifest.get("vector_shards", []), key=lambda shard: int(shard["start"]))
            self._shard_ends = [int(shard["end"]) for shard in self._shards]
        grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for hit in hits:
            index = bisect.bisect_right(self._shard_ends, hit["row_index"])
            if index >= len(self._shards) or hit["row_index"] < int(self._shards[index]["start"]):
                raise ValueError("Candidate row is outside declared vector axis")
            grouped[index].append(hit)
        scores: dict[str, float] = {}
        for index, shard_hits in grouped.items():
            shard = self._shards[index]
            vectors = np.load(_under_root(self.root, shard["path"]), mmap_mode="r", allow_pickle=False)
            try:
                if vectors.shape != (int(shard["end"]) - int(shard["start"]), 768) or vectors.dtype != np.float32:
                    raise ValueError("Vector shard shape/dtype differs from manifest")
                # Advanced indexing copies these few rows only, not a full shard.
                rows = [hit["row_index"] - int(shard["start"]) for hit in shard_hits]
                products = vectors[rows] @ query_vector
                for hit, score in zip(shard_hits, products):
                    if not math.isfinite(float(score)):
                        raise ValueError("Non-finite candidate vector score")
                    scores[hit["chunk_id"]] = float(score)
            finally:
                del vectors
        dense_order = sorted(hits, key=lambda hit: (-scores[hit["chunk_id"]], hit["chunk_id"]))
        for index, hit in enumerate(dense_order, 1):
            hit["dense_score"] = scores[hit["chunk_id"]]
            hit["dense_rank"] = index
            hit["bm25_score"] = hit["score"]
            hit["score"] = 1 / (60 + hit["lexical_rank"]) + 1 / (60 + index)
            hit["score_type"] = "rrf_bm25_medcpt_candidates_higher_is_better"
        hits.sort(key=lambda hit: (-hit["score"], hit["chunk_id"]))
