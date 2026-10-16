"""Offline text contracts for the privately extracted host-only deployment.

Does not start systemd/Nginx, call a model, inspect secrets, or contact a server.
"""
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return (ROOT / "deploy" / name).read_text(encoding="utf-8")


def unit_values(source, key):
    return re.findall(r"^" + re.escape(key) + r"=(.*)$", source, re.MULTILINE)


def test_private_host_gateway_paths_and_auth_contract():
    source = load("aliyun-host-nginx.conf")
    assert "user zhiwei;" in source and "worker_processes 1;" in source
    assert "listen 80;" in source and "listen [::]:80;" in source
    assert '"Bearer __ZHIWEI_ACCESS_TOKEN__" 1;' in source
    assert "map $http_authorization $zhiwei_authorized" in source
    assert '"http://8.148.158.242" 1;' in source
    assert "if ($zhiwei_origin_allowed = 0) { return 403; }" in source
    assert "if ($zhiwei_authorized = 0) { return 401; }" in source
    assert "proxy_set_header Authorization $http_authorization;" in source
    assert "proxy_pass http://127.0.0.1:18000/api/;" in source
    assert "proxy_pass http://127.0.0.1:3000;" in source
    assert "proxy_pass http://127.0.0.1:3000/;" not in source
    assert "proxy_pass http://127.0.0.1:8080" not in source
    assert "return 308 /zhiwei/$is_args$args;" in source


@pytest.mark.parametrize("request_path,expected", [
    ("/zhiwei/api/info", "/api/info"),
    ("/zhiwei/api/agent/status", "/api/agent/status"),
    ("/zhiwei/api/agent/chat", "/api/agent/chat"),
    ("/zhiwei/api/datainput/cleaning/export", "/api/datainput/cleaning/export"),
])
def test_host_api_uri_prefix_contract(request_path, expected):
    assert "/api/" + request_path.removeprefix("/zhiwei/api/") == expected


def test_host_static_alias_and_named_spa_fallback_do_not_fall_into_old_site():
    source = load("aliyun-host-nginx.conf")
    public = "/data/zhiwei/releases/site_20261011_001/my-nuxt-app/.output/public"
    assert "location ^~ /zhiwei/_nuxt/ {" in source
    assert f"alias {public}/_nuxt/;" in source
    assert f"alias {public}/;" in source
    assert "try_files $uri $uri/ @zhiwei_spa;" in source
    assert "location @zhiwei_spa {" in source
    assert f"root {public};" in source
    assert "try_files /index.html =404;" in source
    assert "try_files $uri $uri/ /index.html;" not in source
    assert "autoindex off;" in source


def test_host_mime_temp_paths_are_self_contained_and_secret_safe():
    source = load("aliyun-host-nginx.conf")
    assert "include /etc/nginx/" not in source
    for mapping in ("text/html html htm;", "text/css css;", "application/javascript js mjs;",
                    "application/json json;", "font/woff2 woff2;"):
        assert mapping in source
    for path in ("client_body", "proxy", "fastcgi", "uwsgi", "scgi"):
        assert f"/data/zhiwei/runtime/nginx/tmp/{path};" in source
    assert "pid /data/zhiwei/runtime/nginx/run/nginx.pid;" in source
    assert "access_log off;" in source and "error_log /dev/null;" in source
    assert "client_max_body_size 26m;" in source
    assert "proxy_request_buffering off;" in source and "proxy_buffering off;" in source
    assert "proxy_set_header Upgrade $http_upgrade;" in source
    assert "proxy_set_header Connection $zhiwei_connection_upgrade;" in source
    assert "ssl_certificate" not in source


@pytest.mark.parametrize("route", ["uploads", "docs", "redoc"])
def test_host_public_sensitive_routes_remain_blocked(route):
    source = load("aliyun-host-nginx.conf")
    assert f"location = /zhiwei/{route} {{ return 404; }}" in source
    assert f"location ^~ /zhiwei/{route}/ {{ return 404; }}" in source
    assert "location = /zhiwei/openapi.json { return 404; }" in source


def test_api_dedicated_uid_env_file_and_local_single_worker():
    source = load("aliyun-api.service")
    assert unit_values(source, "User") == ["zhiwei"]
    assert unit_values(source, "Group") == ["zhiwei"]
    assert unit_values(source, "EnvironmentFile") == ["/data/zhiwei/private/deployment.env"]
    assert unit_values(source, "WorkingDirectory") == ["/data/zhiwei/releases/site_20261011_001/backend"]
    assert unit_values(source, "ReadWritePaths") == ["/data/zhiwei/private/uploads"]
    start = unit_values(source, "ExecStart")[0]
    assert start.startswith("/data/zhiwei/runtime/venv/bin/python -m uvicorn app.main:app")
    assert "--host 127.0.0.1 --port 18000 --workers 1" in start
    assert "--no-access-log --no-proxy-headers" in start
    assert "--host 0.0.0.0" not in start
    assert "RAG_RETRIEVAL_MODE=bm25" in source
    assert "RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK=true" in source
    assert "RAG_REQUIRE_API_KEY=true" in source
    assert "RAG_LLM_API_KEY=" not in source and "RAG_API_KEY=" not in source
    assert unit_values(source, "MemoryMax") == ["1G"]
    assert unit_values(source, "CPUQuota") == ["100%"]


def test_privately_extracted_nginx_no_global_or_old_configuration_paths():
    source = load("aliyun-nginx.service")
    executable = "/data/zhiwei/runtime/nginx/usr/sbin/nginx"
    private_config = "-p /data/zhiwei/runtime/nginx/ -c /data/zhiwei/runtime/etc/nginx.conf"
    for key in ("ExecStartPre", "ExecStart"):
        command = unit_values(source, key)[0]
        assert command.startswith(executable + " " + private_config)
    assert unit_values(source, "ExecStartPre")[0].endswith(" -t")
    assert unit_values(source, "ExecStart")[0].endswith('-g "daemon off;"')
    assert unit_values(source, "ExecReload")[0].endswith(" -t")
    assert unit_values(source, "ExecReload")[1] == "/bin/kill -HUP $MAINPID"
    assert "Environment=LD_LIBRARY_PATH=/data/zhiwei/runtime/nginx/usr/lib/x86_64-linux-gnu:" in source
    assert unit_values(source, "User") == ["root"]
    assert unit_values(source, "MemoryMax") == ["128M"]
    assert unit_values(source, "CPUQuota") == ["25%"]
    assert unit_values(source, "ReadWritePaths") == ["/data/zhiwei/runtime/nginx/run /data/zhiwei/runtime/nginx/tmp"]
    assert unit_values(source, "StandardOutput") == ["null"]
    assert unit_values(source, "StandardError") == ["null"]
    assert "CAP_KILL" in source  # root master can signal its uid10001 workers on reload
    assert "CAP_SYS_ADMIN" not in source and "CAP_NET_ADMIN" not in source
    assert "/etc/nginx/nginx.conf" not in source
    assert "/www/server/" not in source and "docker" not in "\n".join(unit_values(source, "ExecStart"))


@pytest.mark.parametrize("name", ["aliyun-api.service", "aliyun-nginx.service"])
def test_new_units_common_protection_and_no_unbounded_resource_use(name):
    source = load(name)
    for key in ("NoNewPrivileges", "PrivateTmp", "PrivateDevices", "ProtectHome", "ProtectKernelTunables",
                "ProtectKernelModules", "ProtectControlGroups", "RestrictSUIDSGID", "LockPersonality"):
        assert unit_values(source, key) == ["true"]
    assert unit_values(source, "ProtectSystem") == ["strict"]
    assert unit_values(source, "MemorySwapMax") == ["0"]
    assert unit_values(source, "TasksMax") == ["64"]
    assert unit_values(source, "UMask") == ["0077"]
    assert unit_values(source, "RequiresMountsFor") == ["/data/zhiwei"]
    assert unit_values(source, "WantedBy") == ["multi-user.target"]
