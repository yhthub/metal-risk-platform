"""Tiny closed SQLite fixtures only; hardware mount checks are mocked, no SSH."""
from dataclasses import replace
import gzip
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from unittest.mock import Mock, patch

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import aliyun_restore_closed_corpus as restore


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    # Linux unlink permits removing our 0444 hard-link alias. Windows maps 0444
    # to the shared inode's read-only attribute instead; simulate POSIX chmod
    # only for that publication step without changing production behavior.
    if os.name == "nt":
        real_chmod = restore.os.chmod

        def posix_chmod(path, mode, **options):
            if mode == 0o444 and str(path).endswith(".part"):
                return
            return real_chmod(path, mode, **options)

        monkeypatch.setattr(restore.os, "chmod", posix_chmod)
    data = tmp_path / "data"
    site = data / "zhiwei"
    corpus = site / "corpus/immutable-export"
    catalog = corpus / "00_catalog"
    catalog.mkdir(parents=True)
    transfer = site / "corpus/transfer"
    transfer.mkdir()
    private = site / "private"
    uploads = private / "uploads"
    uploads.mkdir(parents=True)
    env = private / "deployment.env"
    env.write_text(f"ALIYUN_DATA_ROOT={data}\nRAG_CORPUS_HOST_PATH={corpus}\nRAG_UPLOADS_HOST_PATH={uploads}\n", encoding="utf-8")
    env.chmod(0o600)
    original = tmp_path / "closed-fixture.sqlite3"
    connection = sqlite3.connect(original)
    connection.execute("CREATE TABLE chunks(row_index INTEGER, document_id TEXT, corpus TEXT, source_key TEXT, source_row INTEGER, title TEXT, content TEXT)")
    connection.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(title, content)")
    connection.commit()
    connection.close()
    source = gzip.compress(original.read_bytes(), mtime=0)
    paths = restore.RestorePaths(data, site, env)
    paths.archive.write_bytes(source)
    expected = restore.ExpectedArchive(len(source), hashlib.sha256(source).hexdigest(), original.stat().st_size)
    manifest = {"schema": "MEDRR-UNIFIED-RETRIEVAL-v1", "corpus_database": "database/corpus.sqlite3", "total_rows": 1}
    (corpus / "UNIFIED_MANIFEST_PORTABLE.json").write_text(json.dumps(manifest), encoding="utf-8")
    (catalog / "EXPORT_PROGRESS.json").write_text(json.dumps({"state": "COMPLETE", "local_database_bytes": expected.decoded_bytes, "total_chunks": 1}), encoding="utf-8")
    (catalog / "SNAPSHOT_PROVENANCE.json").write_text(json.dumps({"state": "COMPLETE", "snapshot_complete_by_backup_api": True}), encoding="utf-8")

    def storage(values, corpus_bytes):
        return restore.preflight.inspect_storage(values, corpus_bytes,
            mounts=[(data.resolve(), "ext4")], check_upload_owner=False,
            disk_usage=type("Usage", (), {"total": 500 * restore.GIB, "free": 400 * restore.GIB})())

    mount = Mock(return_value={"uuid": restore.DATA_UUID, "filesystem": "ext4"})
    kwargs = {"mount_checker": mount, "storage_checker": storage}
    return paths, expected, original, kwargs


def target(paths):
    return paths.corpus / "database/corpus.sqlite3"


def test_valid_archive_restores_readonly_closed_schema_and_keeps_gzip(fixture):
    paths, expected, original, kwargs = fixture
    result = restore.restore(paths, expected, **kwargs)
    assert result["status"] == "PASS"
    assert result["archive_sha256"] == result["gzip_crc"] == result["decoded_size"] == "PASS"
    assert result["schema_only"] == result["storage"] == "PASS"
    assert result["full_row_counts"] == result["model_calls"] == result["network_requests"] == 0
    assert target(paths).read_bytes() == original.read_bytes()
    if os.name == "posix":
        assert target(paths).stat().st_mode & 0o777 == 0o444
    assert not Path(str(target(paths)) + ".part").exists()
    assert paths.archive.is_file()
    assert json.loads(paths.receipt.read_text())["status"] == "PASS"
    assert result["corpus_basis"]["fts5_schema_present"] is True


def test_only_new_public_parents_override_restrictive_directory_creation(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    existing = corpus / "existing"
    existing.mkdir()
    private = tmp_path / "private"
    private.mkdir()
    original_modes = {path: path.stat().st_mode for path in (corpus, existing, private)}
    new_parents = [existing / "first", existing / "first/second", existing / "first/second/third"]
    original_mkdir = Path.mkdir
    original_chmod = restore.os.chmod
    chmod_calls = []

    def restrictive_mkdir(path, mode=0o777, parents=False, exist_ok=False):
        return original_mkdir(path, mode=0o700, parents=parents, exist_ok=exist_ok)

    def tracked_chmod(path, mode):
        chmod_calls.append((Path(path), mode))
        return original_chmod(path, mode)

    monkeypatch.setattr(Path, "mkdir", restrictive_mkdir)
    monkeypatch.setattr(restore.os, "chmod", tracked_chmod)
    restore._create_public_corpus_parents(corpus, new_parents[-1])
    assert chmod_calls == [(path, 0o755) for path in new_parents]
    assert all(path.is_dir() for path in new_parents)
    if os.name == "posix":
        assert all(path.stat().st_mode & 0o777 == 0o755 for path in new_parents)
    assert {path: path.stat().st_mode for path in original_modes} == original_modes


def test_public_parent_creation_cannot_change_private_paths(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    private = tmp_path / "private"
    private.mkdir()
    original_mode = private.stat().st_mode
    with pytest.raises(restore.RestoreError, match="inside the corpus root"):
        restore._create_public_corpus_parents(corpus, private / "new")
    assert private.stat().st_mode == original_mode
    assert not (private / "new").exists()


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX umask and directory modes")
def test_private_umask_restores_public_parents_and_readonly_database(fixture):
    paths, expected, _, kwargs = fixture
    manifest_path = paths.corpus / "UNIFIED_MANIFEST_PORTABLE.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["corpus_database"] = "replica_yht/projects/MedRR/experiment/retrieval/corpus/corpus.sqlite3"
    manifest_path.write_text(json.dumps(manifest))
    destination = paths.corpus / manifest["corpus_database"]
    existing_modes = {path: path.stat().st_mode for path in
                      (paths.corpus, paths.corpus / "00_catalog", paths.site_root / "private")}
    previous_umask = os.umask(0o077)
    try:
        result = restore.restore(paths, expected, **kwargs)
    finally:
        os.umask(previous_umask)
    assert result["status"] == "PASS"
    current = paths.corpus
    for part in destination.parent.relative_to(paths.corpus).parts:
        current /= part
        assert current.stat().st_mode & 0o777 == 0o755
    assert destination.stat().st_mode & 0o777 == 0o444
    assert {path: path.stat().st_mode for path in existing_modes} == existing_modes


@pytest.mark.parametrize("existing", ["final", "partial", "wal"])
def test_existing_outputs_or_live_sidecar_are_preserved_not_overwritten(fixture, existing):
    paths, expected, _, kwargs = fixture
    destination = target(paths)
    destination.parent.mkdir()
    conflict = destination if existing == "final" else Path(str(destination) + (".part" if existing == "partial" else "-wal"))
    conflict.write_bytes(b"existing evidence")
    with pytest.raises(restore.RestoreError, match="already exists"):
        restore.restore(paths, expected, **kwargs)
    assert conflict.read_bytes() == b"existing evidence"
    assert json.loads(paths.receipt.read_text())["status"] == "FAIL"


def test_checksum_failure_does_not_create_database_or_partial(fixture):
    paths, expected, _, kwargs = fixture
    with pytest.raises(restore.RestoreError, match="SHA256"):
        restore.restore(paths, replace(expected, sha256="0" * 64), **kwargs)
    assert not target(paths).exists()
    assert not Path(str(target(paths)) + ".part").exists()
    assert paths.archive.is_file()


def test_crc_failure_keeps_partial_and_never_publishes(fixture):
    paths, expected, _, kwargs = fixture
    source = bytearray(paths.archive.read_bytes())
    source[-8] ^= 1
    paths.archive.write_bytes(source)
    expected = replace(expected, sha256=hashlib.sha256(source).hexdigest())
    with pytest.raises(restore.RestoreError, match="restore failed"):
        restore.restore(paths, expected, **kwargs)
    assert Path(str(target(paths)) + ".part").is_file()
    assert not target(paths).exists()
    receipt = json.loads(paths.receipt.read_text())
    assert receipt["status"] == "FAIL" and receipt["partial_retained"] is True
    assert receipt["gzip_crc"] == "pending"


def test_decoded_size_failure_preserves_partial(fixture):
    paths, expected, _, kwargs = fixture
    expected = replace(expected, decoded_bytes=expected.decoded_bytes + 1)
    progress = paths.corpus / "00_catalog/EXPORT_PROGRESS.json"
    value = json.loads(progress.read_text())
    value["local_database_bytes"] = expected.decoded_bytes
    progress.write_text(json.dumps(value))
    with pytest.raises(restore.RestoreError, match="decoded database size"):
        restore.restore(paths, expected, **kwargs)
    assert not target(paths).exists()
    assert Path(str(target(paths)) + ".part").exists()


def test_schema_failure_keeps_unverified_partial_and_fail_receipt(fixture):
    paths, expected, _, kwargs = fixture
    kwargs["partial_schema_checker"] = Mock(side_effect=restore.preflight.PreflightError("fixture schema invalid"))
    with pytest.raises(restore.RestoreError, match="fixture schema invalid"):
        restore.restore(paths, expected, **kwargs)
    receipt = json.loads(paths.receipt.read_text())
    assert receipt["status"] == "FAIL" and receipt["published_unverified"] is False
    assert receipt["schema_only"] == "pending"
    assert Path(str(target(paths)) + ".part").exists()
    assert not target(paths).exists()


@pytest.mark.parametrize("relative", ["../escape.sqlite3", "/escape.sqlite3", "C:/escape.sqlite3", ".", "database/../../escape.sqlite3"])
def test_unportable_database_paths_are_rejected(fixture, relative):
    paths, expected, _, kwargs = fixture
    manifest = paths.corpus / "UNIFIED_MANIFEST_PORTABLE.json"
    value = json.loads(manifest.read_text())
    value["corpus_database"] = relative
    manifest.write_text(json.dumps(value))
    with pytest.raises(restore.RestoreError):
        restore.restore(paths, expected, **kwargs)
    assert not target(paths).exists()


def test_bounded_wait_uses_finished_filename_not_transfer_part(fixture):
    paths, expected, _, kwargs = fixture
    paths.archive.rename(Path(str(paths.archive) + ".part"))
    now = [0.0]
    delays = []

    def sleep(seconds):
        delays.append(seconds)
        now[0] += seconds

    with pytest.raises(restore.RestoreError, match="bounded wait"):
        restore.restore(paths, expected, wait_seconds=31, clock=lambda: now[0], sleeper=sleep, **kwargs)
    assert delays == [30, 1]
    assert Path(str(paths.archive) + ".part").exists()
    assert not target(paths).exists()


def test_wait_can_continue_once_final_upload_appears(fixture):
    paths, expected, _, kwargs = fixture
    uploaded = Path(str(paths.archive) + ".part")
    paths.archive.rename(uploaded)
    now = [0.0]

    def sleep(seconds):
        now[0] += seconds
        uploaded.rename(paths.archive)

    assert restore.restore(paths, expected, wait_seconds=30, clock=lambda: now[0], sleeper=sleep, **kwargs)["status"] == "PASS"


def test_preexisting_receipt_rejects_duplicate_owner(fixture):
    paths, expected, _, kwargs = fixture
    paths.receipt.write_text("previous receipt")
    with pytest.raises(restore.RestoreError, match="duplicate restore owner"):
        restore.restore(paths, expected, **kwargs)
    assert paths.receipt.read_text() == "previous receipt"


def test_mount_check_requires_exact_uuid_filesystem_and_target(fixture):
    paths, _, _, _ = fixture
    with patch.object(restore.subprocess, "run") as command:
        command.return_value.stdout = f"{restore.DATA_UUID} ext4 {paths.data_root}\n"
        assert restore.check_mount(paths.data_root)["uuid"] == restore.DATA_UUID
        command.return_value.stdout = f"wrong-uuid ext4 {paths.data_root}\n"
        with pytest.raises(restore.RestoreError, match="mount UUID"):
            restore.check_mount(paths.data_root)


def test_failed_mount_does_not_create_receipt_or_output(fixture):
    paths, expected, _, kwargs = fixture
    kwargs["mount_checker"] = Mock(side_effect=restore.RestoreError("wrong confirmed disk"))
    with pytest.raises(restore.RestoreError, match="wrong confirmed disk"):
        restore.restore(paths, expected, **kwargs)
    assert not paths.receipt.exists()
    assert not target(paths).exists()


def test_error_diagnostics_do_not_echo_unknown_input_exception(fixture, capsys):
    paths, expected, _, kwargs = fixture
    kwargs["env_reader"] = Mock(side_effect=ValueError("SECRET_FAKE_VALUE"))
    with pytest.raises(restore.RestoreError):
        restore.restore(paths, expected, **kwargs)
    assert "SECRET_FAKE_VALUE" not in paths.receipt.read_text()
    assert "SECRET_FAKE_VALUE" not in capsys.readouterr().out


def test_insufficient_free_space_stops_before_creating_output(fixture):
    paths, expected, _, kwargs = fixture
    kwargs["storage_checker"] = Mock(return_value={"data_mount_free_bytes": expected.decoded_bytes})
    with pytest.raises(restore.RestoreError, match="insufficient free"):
        restore.restore(paths, expected, **kwargs)
    assert not target(paths).exists()
    assert not Path(str(target(paths)) + ".part").exists()


@pytest.mark.parametrize("seconds", [-1, 21601])
def test_wait_limit_is_enforced_before_restore(fixture, seconds):
    paths, expected, _, kwargs = fixture
    with pytest.raises(restore.RestoreError, match="21600"):
        restore.restore(paths, expected, wait_seconds=seconds, **kwargs)
    assert not paths.receipt.exists()


def test_database_parent_symlink_is_rejected_without_touching_destination(fixture, tmp_path):
    paths, expected, _, kwargs = fixture
    outside = tmp_path / "untouched"
    outside.mkdir()
    try:
        target(paths).parent.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("host does not allow temporary-directory symlinks")
    with pytest.raises(restore.RestoreError, match="symbolic link"):
        restore.restore(paths, expected, **kwargs)
    assert not list(outside.iterdir())


def test_publish_cannot_overwrite_final_created_during_restore(fixture, monkeypatch):
    paths, expected, _, kwargs = fixture
    original_link = restore.os.link

    def conflicting_publish(partial, final):
        final.write_bytes(b"other operator evidence")
        original_link(partial, final)

    monkeypatch.setattr(restore.os, "link", conflicting_publish)
    with pytest.raises(restore.RestoreError, match="restore failed"):
        restore.restore(paths, expected, **kwargs)
    assert target(paths).read_bytes() == b"other operator evidence"
    assert Path(str(target(paths)) + ".part").exists()


def test_site_can_be_the_actual_mount_root(fixture):
    paths, expected, _, kwargs = fixture
    paths = replace(paths, data_root=paths.site_root)
    values = {"ALIYUN_DATA_ROOT": str(paths.data_root), "RAG_CORPUS_HOST_PATH": str(paths.corpus),
              "RAG_UPLOADS_HOST_PATH": str(paths.site_root / "private/uploads")}
    kwargs["env_reader"] = Mock(return_value=values)
    kwargs["storage_checker"] = Mock(return_value={"data_mount_free_bytes": 400 * restore.GIB,
                                                   "scope": "fixture existing mount"})
    assert restore.restore(paths, expected, **kwargs)["status"] == "PASS"
    kwargs["mount_checker"].assert_called_with(paths.site_root)
