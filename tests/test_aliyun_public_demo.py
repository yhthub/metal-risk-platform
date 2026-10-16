"""Public demo gateway contracts; no keys, remote connections or model requests."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'deploy/aliyun-host-nginx-public-demo.conf').read_text(encoding='utf-8')


def block(marker):
    start = SOURCE.index(marker) + len(marker)
    depth = 1
    end = start
    while depth:
        if SOURCE[end] == '{':
            depth += 1
        elif SOURCE[end] == '}':
            depth -= 1
        end += 1
    return SOURCE[start:end-1]


def test_anonymous_demo_injects_only_internal_app_auth_in_new_api_location():
    api = block('location ^~ /zhiwei/api/ {')
    assert 'return 401' not in SOURCE
    assert '$zhiwei_authorized' not in SOURCE
    assert SOURCE.count('__ZHIWEI_ACCESS_TOKEN__') == 1
    assert 'proxy_set_header Authorization "Bearer __ZHIWEI_ACCESS_TOKEN__";' in api
    assert 'proxy_pass http://127.0.0.1:18000/api/;' in api
    assert 'proxy_set_header Authorization $http_authorization;' not in api
    assert 'RAG_LLM_API_KEY' not in SOURCE and 'sk-sp-' not in SOURCE


def test_location_repeats_all_proxy_headers_to_preserve_nginx_semantics():
    api = block('location ^~ /zhiwei/api/ {')
    for name, value in [('Host', '$http_host'), ('Upgrade', '$http_upgrade'),
                        ('Connection', '$zhiwei_connection_upgrade'), ('X-Real-IP', '$remote_addr'),
                        ('X-Forwarded-For', '$remote_addr'), ('X-Forwarded-Proto', '$scheme')]:
        assert f'proxy_set_header {name} {value};' in api


def test_root_website_and_fixed_local_api_address_do_not_change():
    old = block('location / {')
    assert 'proxy_pass http://127.0.0.1:3000;' in old
    assert 'proxy_read_timeout 3600s;' in old
    assert 'Authorization' not in old and '__ZHIWEI_ACCESS_TOKEN__' not in old
    assert 'proxy_set_header Authorization $http_authorization;' in SOURCE
    assert '127.0.0.1:8080' not in SOURCE and '0.0.0.0:18000' not in SOURCE


def test_remaining_upload_origin_and_private_route_guards():
    api = block('location ^~ /zhiwei/api/ {')
    assert 'if ($zhiwei_origin_allowed = 0) { return 403; }' in api
    assert 'client_max_body_size 26m;' in SOURCE
    assert 'proxy_request_buffering off;' in SOURCE
    for route in ('uploads', 'docs', 'redoc'):
        assert f'location = /zhiwei/{route} {{ return 404; }}' in SOURCE
        assert f'location ^~ /zhiwei/{route}/ {{ return 404; }}' in SOURCE
    assert 'location = /zhiwei/openapi.json { return 404; }' in SOURCE
    assert 'access_log off;' in SOURCE and 'error_log /dev/null;' in SOURCE
    assert not re.search(r'add_header\s+Authorization', SOURCE)


def test_internal_backend_and_restore_gate_still_required():
    unit = (ROOT / 'deploy/aliyun-api.service').read_text(encoding='utf-8')
    assert '--host 127.0.0.1 --port 18000' in unit
    assert 'RAG_REQUIRE_API_KEY=true' in unit
    assert 'RAG_REQUIRE_RESTORE_RECEIPT=true' in unit
    assert 'RAG_MAX_CONCURRENT_GENERATIONS=1' in unit
    assert 'BATCH_MAX_CONCURRENT_IMPORTS=1' in unit
