"""Low-memory deployment guards; bounded synthetic tables, no server/model calls."""
import asyncio
import csv
from io import BytesIO, StringIO
import threading
from zipfile import ZipFile, ZIP_DEFLATED

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pandas as pd
import pytest

from app.api import datainput
from app.services import data_service as data, data_cleaning_service as cleaning


def valid_csv():
    config = data.OUTCOME_CONFIGS["blood_pressure"]
    headers = data._get_required_columns(config)
    row = dict.fromkeys(headers, "1")
    row["SEQN"] = "0001"
    row["DEMO_J__RIDAGEYR"] = "35"
    for key in config["outcome_columns"]["sbp"]:
        row[key] = "120"
    for key in config["outcome_columns"]["dbp"]:
        row[key] = "75"
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue().encode("utf-8-sig")


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(data, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(data, "data_store", {})
    monkeypatch.setattr(data, "analysis_store", {})
    monkeypatch.setattr(data, "_cache_sizes", {})
    monkeypatch.setattr(data, "_import_capacity", threading.BoundedSemaphore(1))
    for name in ("BATCH_MAX_ROWS", "BATCH_MAX_COLUMNS", "BATCH_MAX_CELLS", "BATCH_MAX_DATAFRAME_BYTES",
                 "BATCH_CACHE_MAX_DATASETS", "BATCH_CACHE_MAX_BYTES"):
        monkeypatch.delenv(name, raising=False)
    return tmp_path


def test_default_limits_accept_nhanes_sized_numeric_table(isolated):
    # Represents dimensions, not real participant data or a medical validation.
    columns = ["SEQN"] + [f"measurement_{index}" for index in range(156)]
    source = (",".join(columns) + "\n" + (",".join(["1"] * 157) + "\n") * 9254).encode()
    frame = data._read_tabular_file(source, "synthetic_nhanes_dimensions.csv")
    assert frame.shape == (9254, 157)
    assert frame["SEQN"].dtype.name == "string"
    assert pd.api.types.is_numeric_dtype(frame["measurement_0"])


@pytest.mark.parametrize("setting,value", [("BATCH_MAX_ROWS", "1"), ("BATCH_MAX_COLUMNS", "1"),
                                          ("BATCH_MAX_CELLS", "1"), ("BATCH_MAX_DATAFRAME_BYTES", "1")])
def test_deployment_table_limits_are_413_not_success(isolated, monkeypatch, setting, value):
    monkeypatch.setenv(setting, value)
    source = b"SEQN,amount\n0001,2\n0002,3\n"
    with pytest.raises(data.DatasetValidationError) as result:
        data._read_tabular_file(source, "fixture.csv")
    assert result.value.status_code == 413
    assert not list(isolated.iterdir())
    assert not data.data_store


def test_bad_format_is_422_and_no_record_is_saved(isolated):
    with pytest.raises(data.DatasetValidationError) as result:
        asyncio.run(data.import_batch_file(b"SEQN,SEQN\n1,2\n", "duplicate.csv"))
    assert result.value.status_code == 422
    assert not data.analysis_store
    assert not list(isolated.iterdir())


def test_xlsx_expansion_guard_is_reused_before_numeric_parse(isolated, monkeypatch):
    monkeypatch.setattr(cleaning, "MAX_EXPANDED_BYTES", 128)
    archive = BytesIO()
    with ZipFile(archive, "w", ZIP_DEFLATED) as workbook:
        workbook.writestr("xl/sharedStrings.xml", "A" * 1000)
    with pytest.raises(data.DatasetValidationError) as result:
        data._read_tabular_file(archive.getvalue(), "synthetic_expansion.xlsx")
    assert result.value.status_code == 413


def test_cache_eviction_keeps_disk_originals_and_restores_analysis(isolated, monkeypatch):
    monkeypatch.setenv("BATCH_CACHE_MAX_DATASETS", "2")
    payload = valid_csv()
    ids = [asyncio.run(data.import_batch_file(payload, f"sample_{index}.csv")).file_id for index in range(3)]
    assert set(data.data_store) == set(ids[-2:])
    assert set(data.analysis_store) == set(ids[-2:])
    for index, file_id in enumerate(ids):
        assert isolated.joinpath(f"{file_id}_sample_{index}.csv").read_bytes() == payload
        assert isolated.joinpath(f"{file_id}_analysis.json").is_file()
    restored = asyncio.run(data.get_dataset_analysis(ids[0]))
    assert restored["metadata"]["file_id"] == ids[0]
    assert len(set(data.data_store) | set(data.analysis_store)) <= 2
    assert len(list(isolated.iterdir())) == 6


def test_cache_byte_budget_can_skip_retaining_large_frame_without_deleting(isolated, monkeypatch):
    monkeypatch.setenv("BATCH_CACHE_MAX_BYTES", "1")
    result = asyncio.run(data.import_batch_file(valid_csv(), "sample.csv"))
    assert not data.data_store and not data.analysis_store
    assert isolated.joinpath(f"{result.file_id}_sample.csv").is_file()
    assert asyncio.run(data.get_dataset_analysis(result.file_id))["kpis"]["total_records"] == 1
    assert not data.analysis_store


def test_analysis_is_off_event_loop_and_duplicate_import_gets_busy(isolated, monkeypatch):
    started, release = threading.Event(), threading.Event()
    original = data._build_analysis
    worker_ids = []

    def paused_analysis(*args, **kwargs):
        worker_ids.append(threading.get_ident())
        started.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(data, "_build_analysis", paused_analysis)

    async def scenario():
        event_loop_thread = threading.get_ident()
        first = asyncio.create_task(data.import_batch_file(valid_csv(), "first.csv"))
        try:
            assert await asyncio.to_thread(started.wait, 2)
            with pytest.raises(data.DatasetValidationError) as result:
                await data.import_batch_file(valid_csv(), "duplicate.csv")
            assert result.value.status_code == 429
            assert worker_ids == [worker_ids[0]]
            assert worker_ids[0] != event_loop_thread
        finally:
            release.set()
            await first

    asyncio.run(scenario())
    assert len(list(isolated.glob("*.csv"))) == 1


def test_batch_and_public_demo_api_preserve_busy_status(isolated):
    app = FastAPI()
    app.include_router(datainput.router)
    assert data._import_capacity.acquire(blocking=False)
    try:
        with TestClient(app) as client:
            response = client.post("/api/datainput/batch", files={"file": ("fixture.csv", valid_csv(), "text/csv")})
            assert response.status_code == 429
            assert response.headers["Retry-After"] == "5"
            assert "file_id" not in response.json()
            response = client.post("/api/datainput/demo/import")
            assert response.status_code == 429
            assert response.headers["Retry-After"] == "5"
    finally:
        data._import_capacity.release()
    assert not list(isolated.iterdir())


def test_batch_api_oversize_read_is_bounded_and_file_closed(isolated, monkeypatch):
    monkeypatch.setattr(datainput, "MAX_UPLOAD_SIZE", 4)
    read_sizes = []

    class Upload:
        filename = "oversize.csv"
        closed = False

        async def read(self, size):
            read_sizes.append(size)
            return b"x" * size

        async def close(self):
            self.closed = True

    upload = Upload()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as result:
        asyncio.run(datainput.import_batch_data(upload, "blood_pressure"))
    assert result.value.status_code == 413
    assert read_sizes == [5]
    assert upload.closed
    assert not list(isolated.iterdir())
