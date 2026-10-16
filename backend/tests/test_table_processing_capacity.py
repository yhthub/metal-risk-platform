"""Shared table-job capacity; tiny synthetic inputs, no model or live API."""
import asyncio
import json
import threading

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

from app.api import data_cleaning, datainput
from app.services import data_service as data
from app.services import table_processing_capacity as capacity


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(capacity, "_table_capacity", threading.BoundedSemaphore(1))
    monkeypatch.setattr(data, "_import_capacity", threading.BoundedSemaphore(1))
    monkeypatch.setattr(data, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(data, "data_store", {})
    monkeypatch.setattr(data, "analysis_store", {})
    monkeypatch.setattr(data, "_cache_sizes", {})
    return tmp_path


def test_all_heavy_routes_share_busy_response_but_schema_remains_available(isolated):
    app = FastAPI()
    app.include_router(data_cleaning.router)
    app.include_router(datainput.router)
    assert capacity._table_capacity.acquire(blocking=False)
    try:
        with TestClient(app) as client:
            for route in ("inspect", "preview", "export"):
                response = client.post(
                    f"/api/datainput/cleaning/{route}",
                    files={"file": ("fixture.csv", b"id,value\n1,2\n", "text/csv")},
                    data={"options": json.dumps({"mode": "custom"})},
                )
                assert response.status_code == 429
                assert response.headers["Retry-After"] == "5"
                assert "file_id" not in response.json()
            assert client.get("/api/datainput/cleaning/schema").status_code == 200
            response = client.post("/api/datainput/batch", files={
                "file": ("fixture.csv", b"id,value\n1,2\n", "text/csv"),
            })
            assert response.status_code == 429
            assert response.headers["Retry-After"] == "5"
            response = client.post("/api/datainput/demo/import")
            assert response.status_code == 429
            assert response.headers["Retry-After"] == "5"
        assert not list(isolated.iterdir())
        # Busy failure did not strand the legacy per-import gate.
        assert data._import_capacity.acquire(blocking=False)
        data._import_capacity.release()
    finally:
        capacity._table_capacity.release()


def test_cleaning_worker_blocks_batch_and_another_cleaning_worker(isolated):
    started, release = threading.Event(), threading.Event()
    calls = []

    def paused():
        calls.append(threading.get_ident())
        started.set()
        assert release.wait(5)
        return "completed"

    async def scenario():
        loop_thread = threading.get_ident()
        first = asyncio.create_task(data_cleaning._convert(paused))
        try:
            assert await asyncio.to_thread(started.wait, 2)
            with pytest.raises(data.DatasetValidationError) as batch:
                await data.import_batch_file(b"id,value\n1,2\n", "fixture.csv")
            assert batch.value.status_code == 429
            with pytest.raises(HTTPException) as cleaning:
                await data_cleaning._convert(paused)
            assert cleaning.value.status_code == 429
            assert cleaning.value.headers["Retry-After"] == "5"
            assert len(calls) == 1 and calls[0] != loop_thread
            assert (await data_cleaning.schema())["outcome_id"] == "blood_pressure"
        finally:
            release.set()
            assert await first == "completed"

    asyncio.run(scenario())
    assert not list(isolated.iterdir())


def test_cancelled_await_keeps_slot_until_worker_exits(isolated, monkeypatch):
    started, release, slot_released = threading.Event(), threading.Event(), threading.Event()

    class ObservedSemaphore(threading.BoundedSemaphore):
        def release(self, n=1):
            super().release(n)
            slot_released.set()

    monkeypatch.setattr(capacity, "_table_capacity", ObservedSemaphore(1))

    def paused():
        started.set()
        assert release.wait(5)
        return "completed"

    async def scenario():
        first = asyncio.create_task(data_cleaning._convert(paused))
        try:
            assert await asyncio.to_thread(started.wait, 2)
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            assert not slot_released.is_set()
            with pytest.raises(data.DatasetValidationError) as batch:
                await data.import_batch_file(b"id,value\n1,2\n", "fixture.csv")
            assert batch.value.status_code == 429
        finally:
            release.set()
            assert await asyncio.to_thread(slot_released.wait, 2)
        assert await data_cleaning._convert(lambda: "next") == "next"

    asyncio.run(scenario())
    assert not list(isolated.iterdir())


def test_worker_failure_releases_shared_slot(isolated):
    def broken():
        raise RuntimeError("synthetic failure")

    with pytest.raises(RuntimeError, match="synthetic failure"):
        capacity.run_table_processing(broken)
    assert capacity.run_table_processing(lambda: "next") == "next"
