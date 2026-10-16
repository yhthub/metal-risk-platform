"""Offline Aliyun profile contracts and small closed-SQLite fixtures only."""
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location("aliyun_preflight", ROOT / "scripts/aliyun_preflight.py")
preflight = module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


def valid_environment():
    return {
        "ALIYUN_API_IMAGE": "occupational-health-api:20261011-bm25",
        "ALIYUN_WEB_IMAGE": "occupational-health-web:20261011-root",
        "RAG_API_KEY": "a" * 64,
        "RAG_LLM_API_KEY": "sk-" + "b" * 36,
        "RAG_PUBLIC_ORIGIN": "https://health.example.org",
        "RAG_LLM_PROVIDER": "ollama",
        "RAG_LLM_BASE_URL": "https://model.example.org",
        "RAG_LLM_MODEL": "llama3.1:8b",
        "ALIYUN_BASE_PATH": "/",
    }


@pytest.fixture
def corpus(tmp_path):
    root = tmp_path / "data" / "corpus"
    db = root / "replica_yht/projects/example/corpus.sqlite3"
    db.parent.mkdir(parents=True)
    (root / "00_catalog").mkdir()
    connection = sqlite3.connect(db)
    connection.executescript("""
        CREATE TABLE chunks(row_index INTEGER PRIMARY KEY, document_id TEXT,
            corpus TEXT, source_key TEXT, source_row INTEGER, title TEXT, content TEXT);
        CREATE VIRTUAL TABLE chunks_fts USING fts5(title,content);
        INSERT INTO chunks VALUES(0,'fixture/0','pubmed','fixture',0,'Cadmium','Kidney evidence');
        INSERT INTO chunks_fts(rowid,title,content) VALUES(0,'Cadmium','Kidney evidence');
    """)
    connection.close()
    manifest = {"schema": "MEDRR-UNIFIED-RETRIEVAL-v1", "total_rows": 1,
                "corpus_database": "replica_yht/projects/example/corpus.sqlite3"}
    progress = {"state": "COMPLETE", "local_database_bytes": db.stat().st_size, "total_chunks": 1}
    provenance = {"state": "COMPLETE", "snapshot_complete_by_backup_api": True}
    for path, value in ((root / "UNIFIED_MANIFEST_PORTABLE.json", manifest),
                        (root / "00_catalog/EXPORT_PROGRESS.json", progress),
                        (root / "00_catalog/SNAPSHOT_PROVENANCE.json", provenance)):
        path.write_text(json.dumps(value), encoding="utf-8")
    return root, db


def replace_catalog(root, name, changes):
    path = root / name
    value = json.loads(path.read_text(encoding="utf-8"))
    value.update(changes)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_safe_existing_remote_ollama_configuration():
    assert preflight.validate_environment(valid_environment()) == []


def test_openai_compatible_external_model_and_optional_private_ollama_auth():
    values = valid_environment()
    values.update(RAG_LLM_PROVIDER="openai_compatible", RAG_LLM_BASE_URL="https://model.example.org/v1")
    assert preflight.validate_environment(values) == []
    values.update(RAG_LLM_PROVIDER="ollama", RAG_LLM_API_KEY="")
    assert preflight.validate_environment(values) == []


def test_current_ip_and_subpath_are_configuration_options_not_forced_routes():
    values = valid_environment()
    values.update(RAG_PUBLIC_ORIGIN="http://8.148.158.242", ALIYUN_BASE_PATH="/zhiwei/")
    assert preflight.validate_environment(values) == []


@pytest.mark.parametrize("key,value", [
    ("RAG_API_KEY", "short"), ("RAG_API_KEY", "a" * 32 + "$"),
    ("RAG_LLM_API_KEY", "token\";unsafe"), ("RAG_PUBLIC_ORIGIN", "https://host/path"),
    ("RAG_PUBLIC_ORIGIN", "https://host\";unsafe"), ("RAG_PUBLIC_ORIGIN", "https://user:password@host"),
    ("RAG_LLM_PROVIDER", "vllm"), ("RAG_LLM_BASE_URL", "http://127.0.0.1:11434"),
    ("RAG_LLM_BASE_URL", "http://localhost:11434"), ("RAG_LLM_BASE_URL", "http://api:8000"),
    ("RAG_LLM_BASE_URL", "http://public-model.example.org:11434"),
    ("RAG_LLM_BASE_URL", "https://model.example.org/api/chat"),
    ("RAG_LLM_BASE_URL", "https://model.example.org/v1/chat/completions"),
    ("RAG_LLM_MODEL", "REPLACE_WITH_MODEL"), ("ALIYUN_API_IMAGE", "example:latest"),
    ("ALIYUN_WEB_IMAGE", "example"), ("ALIYUN_BASE_PATH", "/../oldsite/"),
    ("RAG_WEB_PORT", "80"), ("RAG_LLM_MAX_TOKENS", "8000"), ("RAG_TOP_K", "12"),
])
def test_unsafe_or_heavy_environment_values_are_rejected(key, value):
    values = valid_environment()
    values[key] = value
    assert preflight.validate_environment(values)


def test_private_http_requires_explicit_network_confirmation():
    values = valid_environment()
    values["RAG_LLM_BASE_URL"] = "http://10.0.0.5:11434"
    assert preflight.validate_environment(values)
    values["ALIYUN_ALLOW_PRIVATE_HTTP_MODEL"] = "true"
    assert preflight.validate_environment(values) == []


def test_application_and_model_keys_cannot_be_identical():
    values = valid_environment()
    values["RAG_LLM_API_KEY"] = values["RAG_API_KEY"]
    assert preflight.validate_environment(values)


@pytest.mark.parametrize("line", ["RAG_API_KEY=abc$unsafe", "RAG_API_KEY=\"secret\"",
                                  "RAG_API_KEY=secret#suffix", "RAG_API_KEY=`command`",
                                  "RAG_API_KEY=a\nRAG_API_KEY=b", "export RAG_API_KEY=a"])
def test_env_parser_is_not_a_shell_and_does_not_print_secret(tmp_path, line):
    env = tmp_path / "private.env"
    env.write_text(line, encoding="utf-8")
    env.chmod(0o600)
    with pytest.raises(preflight.PreflightError) as error:
        preflight.read_environment(env)
    assert "secret" not in str(error.value)
    assert "abc$unsafe" not in str(error.value)


def test_closed_portable_fts_fixture_without_vectors_or_encoder(corpus):
    root, db = corpus
    identity = (db.stat().st_size, db.stat().st_mtime_ns)
    result = preflight.inspect_corpus(root)
    assert result["fts5_schema_present"] is True
    assert result["declared_chunks"] == 1
    assert (db.stat().st_size, db.stat().st_mtime_ns) == identity
    assert not Path(str(db) + "-wal").exists()


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_corpus_sidecars_are_refused_before_sqlite_connect(corpus, monkeypatch, suffix):
    root, db = corpus
    Path(str(db) + suffix).touch()
    monkeypatch.setattr(preflight.sqlite3, "connect", lambda *args, **kwargs: pytest.fail("must not open a sidecar-bearing DB"))
    with pytest.raises(preflight.PreflightError, match="WAL/SHM/journal"):
        preflight.inspect_corpus(root)


@pytest.mark.parametrize("relative", ["../../outside.sqlite3", "/etc/outside.sqlite3", "C:/outside.sqlite3"])
def test_portable_manifest_rejects_path_traversal(corpus, relative):
    root, _ = corpus
    replace_catalog(root, "UNIFIED_MANIFEST_PORTABLE.json", {"corpus_database": relative})
    with pytest.raises(preflight.PreflightError):
        preflight.inspect_corpus(root)


@pytest.mark.parametrize("name,changes", [
    ("00_catalog/EXPORT_PROGRESS.json", {"state": "RUNNING"}),
    ("00_catalog/SNAPSHOT_PROVENANCE.json", {"snapshot_complete_by_backup_api": False}),
    ("00_catalog/EXPORT_PROGRESS.json", {"local_database_bytes": 1}),
    ("00_catalog/EXPORT_PROGRESS.json", {"total_chunks": 2}),
])
def test_incomplete_snapshot_or_inconsistent_receipts_are_rejected(corpus, name, changes):
    root, _ = corpus
    replace_catalog(root, name, changes)
    with pytest.raises(preflight.PreflightError):
        preflight.inspect_corpus(root)


def test_missing_fts_schema_is_rejected(corpus):
    root, db = corpus
    connection = sqlite3.connect(db)
    connection.execute("DROP TABLE chunks_fts")
    connection.commit()
    connection.close()
    replace_catalog(root, "00_catalog/EXPORT_PROGRESS.json", {"local_database_bytes": db.stat().st_size})
    with pytest.raises(preflight.PreflightError, match="FTS5"):
        preflight.inspect_corpus(root)


def storage_environment(corpus):
    root, _ = corpus
    mount = root.parent
    uploads = mount / "private/uploads"
    uploads.mkdir(parents=True)
    return {"ALIYUN_DATA_ROOT": str(mount), "RAG_CORPUS_HOST_PATH": str(root),
            "RAG_UPLOADS_HOST_PATH": str(uploads)}, mount


def test_confirmed_mounted_data_storage_keeps_reserve(corpus):
    values, mount = storage_environment(corpus)
    result = preflight.inspect_storage(values, 64 * preflight.GIB,
        mounts=[(mount, "ext4")], disk_usage=SimpleNamespace(total=460 * preflight.GIB, free=200 * preflight.GIB),
        check_upload_owner=False)
    assert result["filesystem"] == "ext4"
    assert result["required_free_reserve_bytes"] == 8 * preflight.GIB


@pytest.mark.parametrize("mounts", [[], "overlay", "tmpfs"])
def test_unmounted_or_ephemeral_storage_is_refused(corpus, mounts):
    values, mount = storage_environment(corpus)
    records = [] if mounts == [] else [(mount, mounts)]
    with pytest.raises(preflight.PreflightError, match="filesystem mount"):
        preflight.inspect_storage(values, 1, mounts=records, check_upload_owner=False)


def test_space_reserve_and_upload_corpus_separation(corpus):
    values, mount = storage_environment(corpus)
    with pytest.raises(preflight.PreflightError, match="8 GiB"):
        preflight.inspect_storage(values, 64 * preflight.GIB, mounts=[(mount, "ext4")],
            disk_usage=SimpleNamespace(total=460 * preflight.GIB, free=2 * preflight.GIB), check_upload_owner=False)
    values["RAG_UPLOADS_HOST_PATH"] = values["RAG_CORPUS_HOST_PATH"]
    with pytest.raises(preflight.PreflightError, match="immutable corpus"):
        preflight.inspect_storage(values, 1, mounts=[(mount, "ext4")], check_upload_owner=False)


def test_compose_is_separate_no_models_no_api_ports_and_outbound_enabled():
    config = (ROOT / "deploy/aliyun-compose.yaml").read_text(encoding="utf-8")
    assert "name: occupational-health-aliyun" in config
    assert "127.0.0.1:${RAG_WEB_PORT:-8080}:8080" in config
    assert 'expose: ["8000"]' in config
    assert config.count("ports:") == 1
    assert "RAG_RETRIEVAL_MODE: bm25" in config
    assert 'RAG_MEDCPT_RERANK: "false"' in config
    assert 'RAG_DENSE_ALLOW_EXACT_SCAN: "false"' in config
    assert "  application: {}" in config
    uncommented = "\n".join(line for line in config.splitlines() if not line.lstrip().startswith("#"))
    assert "internal: true" not in uncommented
    assert "  llm:" not in config
    assert "RAG_MODEL_HOST_PATH" not in config
    assert "RAG_DENSE_INDEX_HOST_PATH" not in config
    assert "privileged:" not in config and "network_mode: host" not in config
    assert "mem_limit: 1g" in config and "mem_limit: 128m" in config
    assert "BATCH_MAX_CONCURRENT_IMPORTS" in config
    assert "BATCH_CACHE_MAX_BYTES" in config
    assert "image: ${ALIYUN_API_IMAGE" in config
    assert "image: ${ALIYUN_WEB_IMAGE" in config
    assert "    build:" not in config  # Build off-server and transfer pinned images.


def test_prebuilt_frontend_never_builds_on_ecs_and_keeps_existing_gateway_auth():
    dockerfile = (ROOT / "deploy/frontend-prebuilt.Dockerfile").read_text(encoding="utf-8")
    assert "COPY my-nuxt-app/.output/public" in dockerfile
    assert "COPY deploy/nginx/default.conf.template" in dockerfile
    assert "FROM node" not in dockerfile and "pnpm install" not in dockerfile
    ignored = (ROOT / "deploy/frontend-prebuilt.Dockerfile.dockerignore").read_text(encoding="utf-8")
    assert "!my-nuxt-app/.output/public/**" in ignored
    assert "**/*.key" in ignored and "**/*.pem" in ignored
    gateway = (ROOT / "deploy/nginx/default.conf.template").read_text(encoding="utf-8")
    assert '"Bearer ${RAG_API_KEY}" 1;' in gateway
    assert "proxy_set_header Authorization $http_authorization;" in gateway


def test_preflight_source_has_no_network_model_installs_or_full_scans():
    source = (ROOT / "scripts/aliyun_preflight.py").read_text(encoding="utf-8")
    assert "?mode=ro&immutable=1" in source
    assert "SELECT sql FROM sqlite_master" in source
    executable = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
    assert 'execute("SELECT COUNT' not in executable
    assert 'execute("PRAGMA integrity_check' not in executable
    assert "import requests" not in source and "import subprocess" not in source
    assert "hashlib" not in source and "pip install" not in source


def test_example_is_deliberately_not_runnable(tmp_path):
    env = tmp_path / "private.env"
    env.write_text((ROOT / "deploy/aliyun.env.example").read_text(encoding="utf-8"), encoding="utf-8")
    env.chmod(0o600)
    example = preflight.read_environment(env)
    assert preflight.validate_environment(example)
    assert example["RAG_LLM_API_KEY"] == ""


def test_mountinfo_parser_reads_existing_escaped_paths(tmp_path):
    data = tmp_path / "mount data"
    data.mkdir()
    info = tmp_path / "mountinfo"
    escaped = data.as_posix().replace(" ", "\\040")
    info.write_text(f"42 30 259:1 / {escaped} rw,relatime - ext4 /dev/nvme1n1 rw\n", encoding="utf-8")
    assert preflight.read_mounts(info) == [(data.resolve(), "ext4")]


def test_independent_80_gateway_preserves_old_root_and_strips_new_prefix():
    config = (ROOT / "deploy/aliyun-gateway.conf").read_text(encoding="utf-8")
    assert "listen 80;" in config and "listen [::]:80;" in config
    assert "location = /zhiwei {" in config
    assert "return 308 /zhiwei/$is_args$args;" in config
    assert "absolute_redirect off;" in config
    assert "location ^~ /zhiwei/ {" in config
    assert "proxy_pass http://127.0.0.1:8080/;" in config  # strip new path prefix
    assert "proxy_pass http://127.0.0.1:3000;" in config   # retain old URI
    assert "proxy_pass http://127.0.0.1:3000/;" not in config
    assert "client_max_body_size 26m;" in config
    assert "proxy_request_buffering off;" in config
    assert "proxy_buffering off;" in config
    assert "proxy_read_timeout 210s;" in config
    assert "proxy_read_timeout 3600s;" in config
    assert "proxy_set_header Upgrade $http_upgrade;" in config
    assert "proxy_set_header Connection $gateway_connection_upgrade;" in config
    assert "proxy_set_header Authorization $http_authorization;" in config
    assert "access_log off;" in config and "error_log /dev/null;" in config
    assert "ssl_certificate" not in config  # does not pretend HTTP is TLS


@pytest.mark.parametrize("public_path,upstream_path", [
    ("/zhiwei/", "/"), ("/zhiwei/agent", "/agent"),
    ("/zhiwei/datainput", "/datainput"), ("/zhiwei/api/agent/status", "/api/agent/status"),
    ("/zhiwei/_nuxt/app.js", "/_nuxt/app.js"),
])
def test_new_gateway_prefix_mapping_contract(public_path, upstream_path):
    # The config uses a prefix location + trailing-slash proxy_pass. This tests
    # expected URI mapping, not a claim of running Nginx/network validation.
    prefix = "/zhiwei/"
    assert public_path.startswith(prefix)
    assert "/" + public_path[len(prefix):] == upstream_path


def test_80_gateway_is_host_network_read_only_and_refuses_existing_listener():
    compose = (ROOT / "deploy/aliyun-gateway-compose.yaml").read_text(encoding="utf-8")
    assert "name: occupational-health-aliyun-gateway" in compose
    assert "network_mode: host" in compose
    assert "    ports:" not in compose  # host network only, Nginx binds the one new 80 ingress
    assert "read_only: true" in compose and "create_host_path: false" in compose
    assert "mem_limit: 128m" in compose and "memswap_limit: 128m" in compose
    assert "no-new-privileges:true" in compose and 'cap_drop: ["ALL"]' in compose
    assert "NET_BIND_SERVICE" in compose
    assert "privileged:" not in compose and "/var/run/docker.sock" not in compose
    assert "/proc/net/tcp /proc/net/tcp6" in compose
    assert '/:0050$$/' in compose and '$$4 == "0A"' in compose
    assert "refusing to replace the existing service" in compose
    assert "nginx -t" in compose
    assert "http://127.0.0.1/zhiwei/" in compose
    assert "RAG_API_KEY" not in compose and "RAG_LLM_API_KEY" not in compose
