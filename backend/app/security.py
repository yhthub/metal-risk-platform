"""Small deployment guardrails; shared API keys are not a full account system."""
from collections import defaultdict, deque
import hashlib
import hmac
import ipaddress
import os
import threading
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from .rag_config import env_bool


def api_keys():
    return [value.strip() for value in os.getenv("RAG_API_KEYS", os.getenv("RAG_API_KEY", "")).split(",") if value.strip()]


def local_client(host):
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class ApiGuard:
    def __init__(self):
        self.events = defaultdict(deque)
        self.lock = threading.Lock()

    async def __call__(self, request: Request, call_next):
        guarded = request.url.path.startswith(("/api/", "/uploads", "/docs", "/redoc", "/openapi.json"))
        if not guarded or request.method == "OPTIONS":
            return await call_next(request)
        keys = api_keys()
        authorization = request.headers.get("authorization", "")
        token = authorization[7:] if authorization.startswith("Bearer ") else ""
        authenticated = any(hmac.compare_digest(token.encode(), key.encode()) for key in keys)
        host = request.client.host if request.client else ""
        if keys or env_bool("RAG_REQUIRE_API_KEY"):
            if not authenticated:
                return JSONResponse({"detail": "需要有效访问密钥。"}, status_code=401)
        elif not local_client(host):
            # Safe developer default: not accidentally public because uvicorn
            # was bound to 0.0.0.0. Do NOT trust spoofable Forwarded headers.
            return JSONResponse({"detail": "未配置访问密钥，API仅允许本机访问。"}, status_code=403)
        if request.headers.get("content-length", "").isdigit():
            if int(request.headers["content-length"]) > 26 * 1024**2:
                return JSONResponse({"detail": "请求体超过允许大小。"}, status_code=413)
        if request.method == "POST" and request.url.path.startswith("/api/agent"):
            try:
                limit = max(1, min(int(os.getenv("RAG_RATE_LIMIT_PER_MINUTE", "20")), 200))
            except ValueError:
                limit = 20
            bucket = hashlib.sha256((token if authenticated else host).encode()).hexdigest()
            now = time.monotonic()
            with self.lock:
                if len(self.events) > 10000:
                    self.events = defaultdict(deque, {key: value for key, value in self.events.items()
                                                       if value and value[-1] > now-60})
                events = self.events[bucket]
                while events and events[0] <= now-60:
                    events.popleft()
                if len(events) >= limit:
                    return JSONResponse({"detail": "请求过于频繁，请稍后再试。"}, status_code=429,
                                        headers={"Retry-After": "60"})
                events.append(now)
        return await call_next(request)
