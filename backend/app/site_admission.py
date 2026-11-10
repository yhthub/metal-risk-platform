"""Bound waiting before FastAPI parses uploads or starts native CPU work."""
import asyncio
import os

from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse


TABLE_POSTS = {
    "/api/datainput/batch", "/api/datainput/demo/import", "/api/risk/demo-batch/import",
    "/api/datainput/cleaning/inspect", "/api/datainput/cleaning/preview", "/api/datainput/cleaning/export",
}
TABLE_READS = ("/api/datainput/analysis/", "/api/datainput/statistics/", "/api/datainput/visualization/")
RISK_POSTS = {"/api/risk/predict", "/api/risk/predict-batch", "/api/risk/predict-cohort", "/api/risk/dashboard"}


class _Queue:
    def __init__(self):
        self.slot = asyncio.Semaphore(1)
        self.admitted = 0
        self.running = None


class SiteAdmissionMiddleware:
    def __init__(self, app):
        self.app = app
        self.limit = max(0, min(20, int(os.getenv("SITE_MAX_CONCURRENT_USERS", "0"))))
        self.timeout = max(1, min(600, int(os.getenv("SITE_QUEUE_TIMEOUT_SECONDS", "120"))))
        self.tables = _Queue()
        self.risk = _Queue()
        self.status_task = None

    async def __call__(self, scope, receive, send):
        if not self.limit or scope["type"] != "http":
            return await self.app(scope, receive, send)
        method = scope["method"]
        path = scope["path"].rstrip("/")
        if (method == "POST" and path in TABLE_POSTS) or (method == "GET" and path.startswith(TABLE_READS)):
            queue = self.tables
        elif method == "POST" and path in RISK_POSTS:
            queue = self.risk
        elif method == "GET" and path == "/api/risk/status":
            return await self._status(scope, receive, send)
        else:
            return await self.app(scope, receive, send)

        if queue.admitted >= self.limit:
            return await self._busy(scope, receive, send, "同时处理的人数已达上限，请稍后重试。")
        queue.admitted += 1
        try:
            # asyncio.Semaphore hands free slots to queued waiters in FIFO order.
            # The query/body is not read and no worker thread is allocated here.
            await asyncio.wait_for(queue.slot.acquire(), timeout=self.timeout)
        except asyncio.TimeoutError:
            queue.admitted -= 1
            return await self._busy(scope, receive, send, "等待处理超时，请稍后重试。")
        except BaseException:
            queue.admitted -= 1
            raise

        async def run():
            try:
                if method == "POST":
                    # Uvicorn signals an already disconnected queued client on
                    # receive. Check only once admitted and replay that chunk.
                    first = await receive()
                    if first["type"] == "http.disconnect":
                        return

                    async def replay():
                        nonlocal first
                        if first is not None:
                            message, first = first, None
                            return message
                        return await receive()

                    await self.app(scope, replay, send)
                else:
                    await self.app(scope, receive, send)
            finally:
                queue.running = None
                queue.admitted -= 1
                queue.slot.release()

        work = asyncio.create_task(run())
        queue.running = work
        try:
            await asyncio.shield(work)
        except asyncio.CancelledError:
            # Pandas/native inference in a worker can outlive the HTTP waiter.
            # Let the operation release the slot when it actually finishes.
            work.add_done_callback(lambda finished: None if finished.cancelled() else finished.exception())
            raise

    async def _status(self, scope, receive, send):
        from .services.nhanes_prediction_service import get_prediction_status, last_verified_status

        result = last_verified_status() if self.risk.admitted else None
        if result is None:
            # Coalesce readiness on page entry. A burst of GETs must not compete
            # with each other for the native model or use twenty thread workers.
            async def verify():
                async with self.risk.slot:
                    return await run_in_threadpool(get_prediction_status)

            if self.status_task is None or self.status_task.done():
                self.status_task = asyncio.create_task(verify())
            try:
                result = await asyncio.wait_for(asyncio.shield(self.status_task), timeout=self.timeout)
            except asyncio.TimeoutError:
                return await self._busy(scope, receive, send, "模型状态尚在核验，请稍后重试。")
        await JSONResponse(result, headers={"Cache-Control": "no-store",
                                            "X-Content-Type-Options": "nosniff"})(scope, receive, send)

    @staticmethod
    async def _busy(scope, receive, send, detail):
        await JSONResponse({"detail": detail}, status_code=429, headers={
            "Retry-After": "5", "Cache-Control": "no-store",
        })(scope, receive, send)
