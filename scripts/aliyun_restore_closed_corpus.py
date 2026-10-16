"""One bounded restore of the authorized closed corpus; no live DB/WAL or network.

The CLI has fixed source, target root, size, checksum and data-disk identity.
Existing database/partial/receipt files are never overwritten or cleaned up.
The source archive is retained. Failed outputs remain explicitly unverified.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import time

import aliyun_preflight as preflight

MIB = 1024 ** 2
GIB = 1024 ** 3
MAX_WAIT_SECONDS = 21600
DATA_UUID = "25986262-9cf2-4d7b-a42f-40861c30ac5d"


class RestoreError(ValueError):
    """Controlled diagnostics never include environment values or source text."""


@dataclass(frozen=True)
class RestorePaths:
    data_root: Path = Path("/data/zhiwei")
    site_root: Path = Path("/data/zhiwei")
    env_file: Path = Path("/data/zhiwei/private/deployment.env")

    @property
    def archive(self):
        return self.site_root / "corpus/transfer/corpus.sqlite3.gz"

    @property
    def corpus(self):
        return self.site_root / "corpus/immutable-export"

    @property
    def receipt(self):
        return self.site_root / "corpus/restore_receipt.json"


@dataclass(frozen=True)
class ExpectedArchive:
    compressed_bytes: int = 26555436386
    sha256: str = "daf563e03864fd9c8261659ab77012583da215e8e69349efc983d2eb1eacba7c"
    decoded_bytes: int = 64232280064


def check_mount(root: Path):
    result = subprocess.run(["findmnt", "-n", "-o", "UUID,FSTYPE,TARGET", "--target", str(root)],
                            check=True, capture_output=True, text=True, timeout=10)
    fields = result.stdout.strip().split()
    if len(fields) != 3 or fields != [DATA_UUID, "ext4", str(root)]:
        raise RestoreError("data mount UUID/filesystem/target does not match the confirmed disk")
    return {"uuid": DATA_UUID, "filesystem": "ext4", "scope": "existing mount identity only; no mount/format"}


def no_symlinks(path: Path, *, missing=False):
    if not path.is_absolute() or ".." in path.parts:
        raise RestoreError("restore paths must be absolute and traversal-free")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise RestoreError("restore path contains a symbolic link")
        if not missing and not current.exists():
            raise RestoreError("required restore path is missing")


def _json_object(path: Path):
    no_symlinks(path)
    if not path.is_file() or path.stat().st_size > 4 * MIB:
        raise RestoreError("required portable catalog is missing or oversized")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise RestoreError("portable catalog must contain a JSON object")
    return value


def database_target(corpus: Path, expected: ExpectedArchive):
    manifest = _json_object(corpus / "UNIFIED_MANIFEST_PORTABLE.json")
    progress = _json_object(corpus / "00_catalog/EXPORT_PROGRESS.json")
    provenance = _json_object(corpus / "00_catalog/SNAPSHOT_PROVENANCE.json")
    if (manifest.get("schema") != "MEDRR-UNIFIED-RETRIEVAL-v1"
            or progress.get("state") != "COMPLETE" or provenance.get("state") != "COMPLETE"
            or provenance.get("snapshot_complete_by_backup_api") is not True):
        raise RestoreError("catalogs do not identify a completed independent closed backup")
    if progress.get("local_database_bytes") != expected.decoded_bytes:
        raise RestoreError("decoded size differs from the completed snapshot catalog")
    total = manifest.get("total_rows")
    if type(total) is not int or total <= 0 or progress.get("total_chunks") != total:
        raise RestoreError("completed row-axis catalogs disagree")
    relative = manifest.get("corpus_database")
    if not isinstance(relative, str) or not relative or "\x00" in relative or re.match(r"^[A-Za-z]:", relative):
        raise RestoreError("database path is not a portable relative path")
    portable = Path(relative.replace("\\", "/"))
    if portable.is_absolute() or ".." in portable.parts or portable == Path("."):
        raise RestoreError("database path escapes the immutable export root")
    target = corpus / portable
    no_symlinks(target, missing=True)
    if not target.resolve().is_relative_to(corpus.resolve()):
        raise RestoreError("database path escapes the immutable export root")
    for candidate in (target, Path(str(target) + ".part"), *(Path(str(target) + suffix)
                       for suffix in ("-wal", "-shm", "-journal"))):
        if candidate.exists() or candidate.is_symlink():
            raise RestoreError("database, partial, or live-database sidecar already exists; refusing overwrite")
    return target


def _create_public_corpus_parents(corpus: Path, parent: Path):
    """Make only new public corpus directories traversable despite a private umask."""
    no_symlinks(corpus)
    no_symlinks(parent, missing=True)
    if not parent.is_relative_to(corpus):
        raise RestoreError("public database directories must stay inside the corpus root")
    current = corpus
    for part in parent.relative_to(corpus).parts:
        current /= part
        try:
            current.mkdir(mode=0o755)
        except FileExistsError:
            no_symlinks(current)
            if not current.is_dir():
                raise RestoreError("database parent is not a directory")
        else:
            no_symlinks(current)
            # mkdir's mode is filtered by systemd UMask=0077. Only directories
            # this call actually created receive the public-corpus mode.
            os.chmod(current, 0o755)
    no_symlinks(parent)


def _identity(path: Path):
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise RestoreError("completed archive must be a regular file")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def inspect_partial_schema(path: Path):
    """Read only the completed unpublished inode; never recount or use WAL."""
    no_symlinks(path)
    identity = _identity(path)
    if any(Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise RestoreError("refusing staged database with live sidecars")
    deadline = time.monotonic() + 3
    connection = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=2)
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA cache_size=-1024")
        connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 100)
        schema = connection.execute("SELECT sql FROM sqlite_master WHERE name='chunks_fts'").fetchone()
        if not schema or not re.search(r"\bUSING\s+fts5\s*\(", schema[0], re.IGNORECASE):
            raise RestoreError("unpublished chunks_fts is not an existing FTS5 virtual table")
        columns = {row[1] for row in connection.execute("PRAGMA table_info(chunks_fts)")}
        if not {"title", "content"}.issubset(columns):
            raise RestoreError("unpublished chunks_fts lacks expected title/content fields")
        columns = {row[1] for row in connection.execute("PRAGMA table_info(chunks)")}
        expected = {"row_index", "document_id", "corpus", "source_key", "source_row", "title", "content"}
        if not expected.issubset(columns):
            raise RestoreError("unpublished chunks table does not match retrieval schema")
    finally:
        connection.close()
    if _identity(path) != identity:
        raise RestoreError("unpublished database changed during schema-only inspection")
    return {"fts5_schema_present": True, "scope": "unpublished closed inode schema only; no full row count"}


def restore(paths=RestorePaths(), expected=ExpectedArchive(), *, wait_seconds=0,
            mount_checker=check_mount, corpus_checker=preflight.inspect_corpus,
            partial_schema_checker=inspect_partial_schema,
            storage_checker=preflight.inspect_storage, env_reader=preflight.read_environment,
            clock=time.monotonic, sleeper=time.sleep):
    if not 0 <= wait_seconds <= MAX_WAIT_SECONDS:
        raise RestoreError("wait must be between 0 and 21600 seconds")
    for candidate in (paths.data_root, paths.site_root, paths.corpus, paths.receipt.parent):
        no_symlinks(candidate)
    if not paths.site_root.is_relative_to(paths.data_root):
        raise RestoreError("site must stay inside the confirmed data mount")
    if not paths.env_file.is_relative_to(paths.site_root / "private"):
        raise RestoreError("private environment must stay inside the site's private directory")
    mount = mount_checker(paths.data_root)
    no_symlinks(paths.receipt, missing=True)
    receipt_tmp = Path(str(paths.receipt) + ".write.tmp")
    if paths.receipt.exists() or receipt_tmp.exists() or receipt_tmp.is_symlink():
        raise RestoreError("restore receipt already exists; refusing duplicate restore owner")

    result = {"status": "STARTING", "stage": "preflight", "mount": mount,
              "expected_compressed_bytes": expected.compressed_bytes,
              "expected_archive_sha256": expected.sha256,
              "expected_decoded_bytes": expected.decoded_bytes,
              "archive_sha256": "pending", "gzip_crc": "pending", "decoded_size": "pending",
              "schema_only": "pending", "storage": "pending", "network_requests": 0,
              "model_calls": 0, "full_row_counts": 0,
              "scope": "closed corpus restore and schema/storage checks; not RAG/model acceptance"}

    # Exclusive creation identifies this one restore owner. Later journal writes
    # atomically replace ONLY this run's receipt, never a previous receipt.
    with paths.receipt.open("x", encoding="utf-8") as stream:
        # This receipt contains public-corpus metadata and controlled diagnostics
        # only, never private environment values or individual health records.
        # The unprivileged API reads it as a readiness gate but cannot modify it.
        os.chmod(paths.receipt, 0o644)
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())

    def journal(status, stage, **fields):
        result.update(status=status, stage=stage, **fields)
        with receipt_tmp.open("x", encoding="utf-8") as stream:
            os.chmod(receipt_tmp, 0o644)
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(receipt_tmp, paths.receipt)
        print(json.dumps({"status": status, "stage": stage, **fields}, ensure_ascii=False), flush=True)

    partial = None
    published = False
    try:
        no_symlinks(paths.env_file)
        env_stat = paths.env_file.stat()
        if os.name == "posix" and (env_stat.st_uid != 0 or env_stat.st_mode & 0o077):
            raise RestoreError("private environment must be root-owned and mode 0600 or stricter")
        values = env_reader(paths.env_file)  # Never print/store this mapping or its model/app tokens.
        for key, required in (("ALIYUN_DATA_ROOT", paths.data_root), ("RAG_CORPUS_HOST_PATH", paths.corpus)):
            if Path(values.get(key, "")) != required:
                raise RestoreError("private environment paths do not match this fixed restore")
        initial_storage = storage_checker(values, expected.decoded_bytes)
        if initial_storage["data_mount_free_bytes"] < expected.decoded_bytes + preflight.MIN_FREE_BYTES:
            raise RestoreError("insufficient free data-disk space for decoded corpus plus reserve")
        target = database_target(paths.corpus, expected)
        partial = Path(str(target) + ".part")
        deadline = clock() + wait_seconds
        while not paths.archive.exists():
            no_symlinks(paths.archive, missing=True)
            if clock() >= deadline:
                raise RestoreError("completed upload archive did not arrive within the bounded wait")
            journal("WAITING", "await_completed_upload")
            sleeper(min(30, max(0, deadline - clock())))
        no_symlinks(paths.archive)
        identity = _identity(paths.archive)
        if identity[2] != expected.compressed_bytes:
            raise RestoreError("completed gzip size differs from the authorized transfer receipt")
        journal("VERIFYING", "gzip_sha256")
        digest = hashlib.sha256()
        with paths.archive.open("rb") as stream:
            while block := stream.read(4 * MIB):
                digest.update(block)
        if _identity(paths.archive) != identity or digest.hexdigest() != expected.sha256:
            raise RestoreError("completed gzip source identity/SHA256 differs from the authorized archive")
        journal("RESTORING", "gzip_decode", archive_sha256="PASS")
        no_symlinks(target, missing=True)
        _create_public_corpus_parents(paths.corpus, target.parent)
        count = 0
        next_progress = GIB
        with partial.open("xb") as output:
            os.chmod(partial, 0o600)
            with gzip.open(paths.archive, "rb") as source:
                while block := source.read(4 * MIB):
                    count += len(block)
                    if count > expected.decoded_bytes:
                        raise RestoreError("gzip decoded content exceeds the authorized database size")
                    output.write(block)
                    if count >= next_progress:
                        journal("RESTORING", "gzip_decode", decoded_bytes=count)
                        next_progress = count + GIB
            output.flush()
            os.fsync(output.fileno())
        if count != expected.decoded_bytes or partial.stat().st_size != expected.decoded_bytes:
            raise RestoreError("decoded database size differs from the authorized closed snapshot")
        if _identity(paths.archive) != identity:
            raise RestoreError("gzip source changed during restore")
        journal("VERIFYING", "publish_and_schema", gzip_crc="PASS", decoded_size="PASS", decoded_bytes=count)
        os.chmod(partial, 0o444)
        staged_schema = partial_schema_checker(partial)
        storage_checker(values, expected.decoded_bytes)
        mount_checker(paths.data_root)
        journal("VERIFYING", "atomic_publication", unpublished_schema="PASS", unpublished_schema_basis=staged_schema)
        # Exclusive hard-link publication is atomic and cannot replace a final
        # created by another operator. Retain our .part alias through validation
        # so any later failure preserves the exact failed output for inspection.
        os.link(partial, target)
        published = True
        corpus = corpus_checker(paths.corpus)
        storage = storage_checker(values, expected.decoded_bytes)
        mount_checker(paths.data_root)
        partial.unlink()  # Only this run's own successfully verified temporary alias.
        journal("PASS", "completed", schema_only="PASS", storage="PASS",
                corpus_basis=corpus, storage_basis=storage, published_readonly=True)
        return result
    except Exception as error:
        # OS/JSON/SQLite errors can include private input; do not print their bodies.
        message = str(error) if isinstance(error, (RestoreError, preflight.PreflightError)) else (
            type(error).__name__ + ": restore failed; source and any partial output were retained")
        journal("FAIL", result["stage"], error=message, partial_retained=bool(partial and partial.exists()),
                published_unverified=published)
        raise RestoreError(message) from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait", type=int, default=0, help="wait 0..21600 seconds for the completed gzip filename")
    parser.add_argument("--env-file", type=Path, default=RestorePaths().env_file)
    args = parser.parse_args(argv)
    try:
        restore(RestorePaths(env_file=args.env_file), wait_seconds=args.wait)
        return 0
    except Exception as error:
        message = str(error) if isinstance(error, RestoreError) else type(error).__name__ + ": restore initialization failed"
        print(json.dumps({"status": "FAIL", "error": message, "ready": False}, ensure_ascii=False), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
