"""Offline deployment receipt gate tests; only a tiny new closed fixture is opened."""

import copy
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.corpus_retrieval_service import (
    CorpusRetrievalService, CorpusUnavailable, MAX_RESTORE_RECEIPT_BYTES,
)


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    monkeypatch.delenv("RAG_REQUIRE_RESTORE_RECEIPT", raising=False)
    root = tmp_path / "corpus" / "immutable-export"
    catalog = root / "00_catalog"
    catalog.mkdir(parents=True)
    database = root / "corpus.sqlite3"
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript("""
            CREATE TABLE chunks(row_index INTEGER PRIMARY KEY,document_id TEXT,
                corpus TEXT,title TEXT,content TEXT,source_key TEXT,source_row INTEGER);
            CREATE VIRTUAL TABLE chunks_fts USING fts5(title,content,content='chunks',
                content_rowid='row_index');
            INSERT INTO chunks VALUES(0,'pubmed/example','pubmed','Lead exposure',
                'Blood lead exposure requires assessment.','example',0);
            INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild');
        """)
        connection.commit()
    size = database.stat().st_size
    manifest = {"schema": "MEDRR-UNIFIED-RETRIEVAL-v1", "corpus_database": "corpus.sqlite3",
                "total_rows": 1, "vector_shards": []}
    progress = {"state": "COMPLETE", "local_database_bytes": size, "total_chunks": 1}
    provenance = {"state": "COMPLETE", "snapshot_complete_by_backup_api": True}
    for path, value in ((root / "UNIFIED_MANIFEST_PORTABLE.json", manifest),
                        (catalog / "EXPORT_PROGRESS.json", progress),
                        (catalog / "SNAPSHOT_PROVENANCE.json", provenance)):
        path.write_text(json.dumps(value), encoding="utf-8")
    if os.name == "posix":
        database.chmod(0o444)
    receipt_path = root.parent / "restore_receipt.json"
    receipt = {"status": "PASS", "stage": "completed", "expected_compressed_bytes": 123,
               "expected_archive_sha256": "a" * 64, "expected_decoded_bytes": size,
               "archive_sha256": "PASS", "gzip_crc": "PASS", "decoded_size": "PASS",
               "schema_only": "PASS", "storage": "PASS", "unpublished_schema": "PASS",
               "published_readonly": True, "decoded_bytes": size,
               "corpus_basis": {"database_bytes": size, "declared_chunks": 1,
                                "fts5_schema_present": True}}
    return root, database, receipt_path, receipt


def save_receipt(corpus, receipt=None):
    corpus[2].write_text(json.dumps(corpus[3] if receipt is None else receipt), encoding="utf-8")


def assert_blocked(service):
    # The published database exists, but every public access path must refuse
    # before the real SQLite opener if receipt verification is not complete.
    with patch("app.services.corpus_retrieval_service.sqlite3.connect",
               side_effect=AssertionError("Must not open SQLite before receipt PASS")) as connect:
        status = service.status()
        assert status["ready"] is False
        assert status["restore_receipt_verified"] is False
        with pytest.raises(CorpusUnavailable):
            service.search("lead")
        with pytest.raises(CorpusUnavailable):
            service.documents([0])
        connect.assert_not_called()
    return status


def test_default_disabled_preserves_existing_closed_library(corpus):
    service = CorpusRetrievalService(corpus[0], medcpt_rerank=False)
    assert service.require_restore_receipt is False
    assert not corpus[2].exists()
    assert service.status()["ready"] is True
    assert service.search("lead")["hits"][0]["source"] == "pubmed"


def test_env_true_enables_gate_and_false_leaves_existing_library_unchanged(corpus, monkeypatch):
    monkeypatch.setenv("RAG_REQUIRE_RESTORE_RECEIPT", " true ")
    service = CorpusRetrievalService(corpus[0])
    assert service.require_restore_receipt is True
    assert_blocked(service)
    monkeypatch.setenv("RAG_REQUIRE_RESTORE_RECEIPT", "false")
    assert CorpusRetrievalService(corpus[0]).status()["ready"] is True


@pytest.mark.parametrize("status,stage", [
    ("WAITING", "await_completed_upload"), ("RESTORING", "gzip_decode"),
    ("VERIFYING", "atomic_publication"), ("FAIL", "publish_and_schema"),
    ("PASS", "atomic_publication"), ("FAIL", "completed"),
])
def test_waiting_failed_or_not_completed_never_opens_published_db(corpus, status, stage):
    receipt = {**corpus[3], "status": status, "stage": stage, "error": "PRIVATE_ERROR_NOT_FOR_API"}
    save_receipt(corpus, receipt)
    returned = assert_blocked(CorpusRetrievalService(corpus[0], require_restore_receipt=True))
    assert "PRIVATE_ERROR_NOT_FOR_API" not in json.dumps(returned)


@pytest.mark.parametrize("field,value", [
    ("archive_sha256", "pending"), ("gzip_crc", "FAIL"), ("schema_only", None),
    ("unpublished_schema", "pending"), ("storage", "FAIL"), ("decoded_size", "pending"),
    ("published_readonly", "true"), ("published_readonly", 1),
    ("expected_archive_sha256", "not-a-sha256"), ("expected_archive_sha256", None),
    ("expected_compressed_bytes", 0), ("expected_decoded_bytes", True), ("decoded_bytes", 1),
])
def test_receipt_requires_complete_typed_verification_fields(corpus, field, value):
    save_receipt(corpus, {**corpus[3], field: value})
    assert_blocked(CorpusRetrievalService(corpus[0], require_restore_receipt=True))


@pytest.mark.parametrize("field,value", [
    ("database_bytes", 1), ("declared_chunks", 2), ("declared_chunks", True),
    ("fts5_schema_present", "true"),
])
def test_receipt_corpus_basis_must_match_actual_catalog_and_size(corpus, field, value):
    receipt = copy.deepcopy(corpus[3])
    receipt["corpus_basis"][field] = value
    save_receipt(corpus, receipt)
    assert_blocked(CorpusRetrievalService(corpus[0], require_restore_receipt=True))


@pytest.mark.parametrize("content", ["{truncated", "[]", "null", "\xff"])
def test_invalid_receipt_never_opens_sqlite(corpus, content):
    corpus[2].write_bytes(content.encode("latin-1"))
    assert_blocked(CorpusRetrievalService(corpus[0], require_restore_receipt=True))


def test_missing_unreadable_and_oversized_receipts_fail_closed(corpus):
    service = CorpusRetrievalService(corpus[0], require_restore_receipt=True)
    assert_blocked(service)
    save_receipt(corpus)
    with patch("pathlib.Path.open", side_effect=PermissionError("PRIVATE_PATH")):
        status = assert_blocked(service)
    assert "PRIVATE_PATH" not in json.dumps(status)
    corpus[2].write_bytes(b" " * (MAX_RESTORE_RECEIPT_BYTES + 1))
    assert_blocked(service)


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_inaccessible_snapshot_sidecar_check_fails_closed(corpus, suffix):
    save_receipt(corpus)
    service = CorpusRetrievalService(corpus[0], require_restore_receipt=True)
    inaccessible = Path(str(corpus[1]) + suffix)
    original_exists = Path.exists

    def checked_exists(path):
        if path == inaccessible:
            raise PermissionError("PRIVATE_SIDECAR_PATH")
        return original_exists(path)

    # Mock directory traversal failures so this also runs on Windows and as root.
    with patch("pathlib.Path.exists", new=checked_exists):
        status = assert_blocked(service)
    assert "inaccessible" in status["error"]
    assert "PRIVATE_SIDECAR_PATH" not in json.dumps(status)


def test_completed_receipt_is_reread_even_after_manifest_is_cached(corpus):
    save_receipt(corpus)
    service = CorpusRetrievalService(corpus[0], require_restore_receipt=True, medcpt_rerank=False)
    with patch("app.services.corpus_retrieval_service.sqlite3.connect",
               side_effect=AssertionError("Health check must not open SQLite")):
        status = service.status()
    assert status["ready"] and status["restore_receipt_verified"]
    assert service.search("lead")["hits"]
    assert service.documents([0])[0]["source"] == "pubmed"
    save_receipt(corpus, {**corpus[3], "status": "FAIL"})
    assert_blocked(service)


def test_receipt_is_rechecked_immediately_before_sqlite_connect(corpus):
    save_receipt(corpus)
    service = CorpusRetrievalService(corpus[0], require_restore_receipt=True)
    original_verify = service._verify_snapshot

    def published_then_failed():
        snapshot = original_verify()
        save_receipt(corpus, {**corpus[3], "status": "FAIL"})
        return snapshot

    with patch.object(service, "_verify_snapshot", side_effect=published_then_failed):
        with patch("app.services.corpus_retrieval_service.sqlite3.connect") as connect:
            with pytest.raises(CorpusUnavailable):
                service.search("lead")
            connect.assert_not_called()


def test_receipt_is_not_trusted_when_published_database_size_differs(corpus):
    receipt = copy.deepcopy(corpus[3])
    for field in ("expected_decoded_bytes", "decoded_bytes"):
        receipt[field] += 1
    receipt["corpus_basis"]["database_bytes"] += 1
    save_receipt(corpus, receipt)
    assert_blocked(CorpusRetrievalService(corpus[0], require_restore_receipt=True))


@pytest.mark.skipif(os.name != "posix", reason="Windows file modes do not express POSIX publish permissions")
def test_claimed_readonly_requires_actual_posix_readonly_file(corpus):
    save_receipt(corpus)
    corpus[1].chmod(0o644)
    assert_blocked(CorpusRetrievalService(corpus[0], require_restore_receipt=True))
