import asyncio
import json
import os
import threading
import unittest
from unittest.mock import patch

from starlette.responses import Response

from app.site_admission import SiteAdmissionMiddleware, TABLE_POSTS, RISK_POSTS
from app.services import nhanes_prediction_service as prediction


class SiteAdmissionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.block = asyncio.Event()
        self.entered = asyncio.Event()
        self.reads = []
        self.started = []

        async def app(scope, receive, send):
            if scope["method"] == "POST":
                value = (await receive())["body"]
                self.started.append(value)
                self.entered.set()
                if value == b"hold":
                    await self.block.wait()
            else:
                value = b"ok"
            await Response(value)(scope, receive, send)

        with patch.dict(os.environ, {"SITE_MAX_CONCURRENT_USERS": "20"}):
            self.site = SiteAdmissionMiddleware(app)

    async def request(self, path, text="", *, method="POST", disconnect=False):
        events = []

        async def receive():
            self.reads.append(text)
            if disconnect:
                return {"type": "http.disconnect"}
            return {"type": "http.request", "body": text.encode(), "more_body": False}

        async def send(event):
            events.append(event)

        await self.site({"type": "http", "method": method, "path": path}, receive, send)
        if not events:
            return None
        return events[0]["status"], events[1]["body"]

    async def check_twenty(self, paths, queue):
        group = sorted(paths)
        first = asyncio.create_task(self.request(group[0], "hold"))
        await asyncio.wait_for(self.entered.wait(), 2)
        others = [asyncio.create_task(self.request(group[i % len(group)], str(i))) for i in range(1, 20)]
        await asyncio.sleep(0)
        self.assertEqual(queue.admitted, 20)
        self.assertEqual(self.reads, ["hold"])
        status, _ = await self.request(group[0], "too many")
        self.assertEqual(status, 429)
        self.assertEqual(await self.request("/health", method="GET"), (200, b"ok"))
        self.block.set()
        expected = [b"hold"] + [str(i).encode() for i in range(1, 20)]
        self.assertEqual(await asyncio.gather(first, *others), [(200, x) for x in expected])
        self.assertEqual(self.started, expected)
        self.assertEqual(queue.admitted, 0)

    async def test_twenty_table_clients_fifo_without_reading_waiting_multipart_bodies(self):
        await self.check_twenty(TABLE_POSTS, self.site.tables)

    async def test_twenty_mixed_native_requests_preserve_payloads_and_admission_limit(self):
        await self.check_twenty(RISK_POSTS, self.site.risk)

    async def test_cancelled_waiter_and_disconnected_client_do_not_run_next_request(self):
        path = "/api/risk/predict"
        first = asyncio.create_task(self.request(path, "hold"))
        await self.entered.wait()
        waiting = asyncio.create_task(self.request(path, "skip"))
        await asyncio.sleep(0)
        waiting.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await waiting
        self.assertEqual(self.site.risk.admitted, 1)
        closed = asyncio.create_task(self.request(path, "closed", disconnect=True))
        last = asyncio.create_task(self.request(path, "last"))
        self.block.set()
        await first
        self.assertIsNone(await closed)
        self.assertEqual(await last, (200, b"last"))
        self.assertEqual(self.started, [b"hold", b"last"])

    async def test_cancelled_active_request_retains_slot_until_its_work_finishes(self):
        path = "/api/datainput/demo/import"
        first = asyncio.create_task(self.request(path, "hold"))
        await self.entered.wait()
        first.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await first
        next_client = asyncio.create_task(self.request(path, "next"))
        await asyncio.sleep(0)
        self.assertEqual(self.site.tables.admitted, 2)
        self.assertEqual(self.started, [b"hold"])
        self.assertEqual(await self.request("/api/risk/predict", "independent"), (200, b"independent"))
        self.block.set()
        self.assertEqual(await next_client, (200, b"next"))
        self.assertEqual(self.site.tables.admitted, 0)

    async def test_queue_wait_timeout_releases_capacity_without_consuming_body(self):
        self.site.timeout = .02
        first = asyncio.create_task(self.request("/api/risk/predict", "hold"))
        await self.entered.wait()
        self.assertEqual((await self.request("/api/risk/dashboard", "timeout"))[0], 429)
        self.assertEqual(self.reads, ["hold"])
        self.assertEqual(self.site.risk.admitted, 1)
        self.block.set()
        await first

    async def test_twenty_cold_status_requests_verify_once_then_busy_status_uses_verified_snapshot(self):
        entered, finish = threading.Event(), threading.Event()
        def verify():
            entered.set()
            finish.wait(3)
            return {"ready": True}
        path = "/api/risk/status"
        with patch.object(prediction, "get_prediction_status", side_effect=verify) as check:
            checks = [asyncio.create_task(self.request(path, method="GET")) for _ in range(20)]
            self.assertTrue(await asyncio.to_thread(entered.wait, 2))
            finish.set()
            responses = await asyncio.gather(*checks)
            self.assertTrue(all(status == 200 and json.loads(body)["ready"] for status, body in responses))
            check.assert_called_once()
            first = asyncio.create_task(self.request("/api/risk/predict", "hold"))
            await self.entered.wait()
            with patch.object(prediction, "_last_status", {"ready": True, "verified_at_unix": 150.0}):
                status, body = await self.request(path, method="GET")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["readiness_source"], "last_verification_while_busy")
            self.assertEqual(self.site.risk.admitted, 1)
            check.assert_called_once()
            self.block.set()
            await first

    async def test_local_default_bypasses_admission(self):
        self.site.limit = 0
        self.assertEqual(await self.request("/api/risk/predict", "individual"), (200, b"individual"))
        self.assertEqual(self.site.risk.admitted, 0)
