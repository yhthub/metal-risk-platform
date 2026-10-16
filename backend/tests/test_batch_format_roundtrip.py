"""Synthetic-only regressions for cleaning -> existing batch import.

These checks validate format compatibility, not medical correctness or efficacy.
No model, running server, real participant data or persistent upload directory is used.
"""
import asyncio
from io import BytesIO
import json

import pandas as pd
from pandas.api.types import is_numeric_dtype

from app.services import data_service
from app.services.data_cleaning_service import export_table


def _fixture_frame():
    config = data_service.OUTCOME_CONFIGS["blood_pressure"]
    columns = data_service._get_required_columns(config)
    records = []
    for index in range(4):
        row = {column: 1 for column in columns}
        row["SEQN"] = f"{index + 1:05d}"
        for reading, column in enumerate(config["outcome_columns"]["sbp"]):
            row[column] = 116 + index * 9 + reading
        for reading, column in enumerate(config["outcome_columns"]["dbp"]):
            row[column] = 72 + index * 5 + reading
        for exposure, item in enumerate(config["exposures"]):
            row[item["column"]] = 0.4 + exposure * 1.2 + index * 0.5
        row.update({
            "DEMO_J__RIDAGEYR": 25 + index * 10,
            "DEMO_J__RIAGENDR": 1 + index % 2,
            "DEMO_J__RIDRETH3": 1 + index,
            "DEMO_J__DMDEDUC2": 2 + index,
            "DEMO_J__DMDMARTL": 1 + index,
            "DEMO_J__INDFMPIR": 0.8 + index,
            "SMQ_J__SMQ020": 1 + index % 2,
            "ALQ_J__ALQ111": 1 + index % 2,
            # This optional legacy consumer still calls numeric Series.mean().
            "pb": 1.5 + index,
        })
        records.append(row)
    return pd.DataFrame.from_records(records)


def _csv_bytes(frame):
    return frame.to_csv(index=False).encode("utf-8-sig")


def test_batch_csv_keeps_leading_zero_ids_without_stringifying_quantities():
    parsed = data_service._read_tabular_file(_csv_bytes(_fixture_frame()), "fixture.CSV")
    assert parsed["SEQN"].tolist() == ["00001", "00002", "00003", "00004"]
    assert is_numeric_dtype(parsed["pb"])
    assert parsed["pb"].mean() == 3.0
    for item in data_service.OUTCOME_CONFIGS["blood_pressure"]["exposures"]:
        assert is_numeric_dtype(parsed[item["column"]])


def test_batch_xlsx_keeps_text_ids_and_numeric_legacy_columns():
    buffer = BytesIO()
    _fixture_frame().to_excel(buffer, index=False, engine="openpyxl")
    parsed = data_service._read_tabular_file(buffer.getvalue(), "fixture.xlsx")
    assert parsed["SEQN"].tolist() == ["00001", "00002", "00003", "00004"]
    assert is_numeric_dtype(parsed["pb"])
    assert parsed["pb"].mean() == 3.0


def test_identifier_dtype_does_not_change_main_analysis():
    content = _csv_bytes(_fixture_frame())
    baseline = pd.read_csv(BytesIO(content), encoding="utf-8-sig", low_memory=False)
    parsed = data_service._read_tabular_file(content, "fixture.csv")
    config = data_service.OUTCOME_CONFIGS["blood_pressure"]
    before = data_service._build_analysis(baseline, config, "fixture-id", "fixture.csv")
    after = data_service._build_analysis(parsed, config, "fixture-id", "fixture.csv")
    assert after == before
    assert after["metadata"]["analysis_records"] == 4
    # Also verifies no NaN/Infinity escaped into the persisted analysis document.
    json.dumps(after, allow_nan=False)


def test_legacy_visualization_optional_quantities_remain_numeric(monkeypatch):
    parsed = data_service._read_tabular_file(_csv_bytes(_fixture_frame()), "fixture.csv")
    monkeypatch.setattr(data_service, "data_store", {"fixture-id": parsed})
    result = asyncio.run(data_service.get_visualization_data("fixture-id"))
    assert result.metal_statistics["pb"]["mean"] == 3.0
    assert result.metal_statistics["pb"]["median"] == 3.0


def test_system_cleaning_export_roundtrips_into_current_batch_analysis(tmp_path, monkeypatch):
    required = data_service._get_required_columns(data_service.OUTCOME_CONFIGS["blood_pressure"])
    content = _csv_bytes(_fixture_frame())
    options = {
        "mode": "system", "outcome_id": "blood_pressure",
        "columns": [{"source": column, "target": column} for column in required],
        "confirm_system_semantics": True,
    }
    payload, filename, cleaning = export_table(content, "synthetic_fixture.csv", json.dumps(options))
    assert cleaning["system_ready"] is True
    assert cleaning["missing_required_columns"] == []
    assert cleaning["columns"] == required
    assert cleaning["total_rows"] == 4
    assert cleaning["preview"][0]["SEQN"] == "00001"

    # Isolate all writes and in-memory records; never touch real user upload data.
    monkeypatch.setattr(data_service, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(data_service, "data_store", {})
    monkeypatch.setattr(data_service, "analysis_store", {})
    imported = asyncio.run(data_service.import_batch_file(payload, filename, "blood_pressure"))
    assert imported.total_records == 4
    assert imported.analysis_records == 4
    assert imported.required_columns == required
    assert data_service.data_store[imported.file_id]["SEQN"].tolist() == ["00001", "00002", "00003", "00004"]
    assert data_service.analysis_store[imported.file_id]["metadata"]["analysis_records"] == 4
    originals = list(tmp_path.glob("*.csv"))
    assert len(originals) == 1
    assert originals[0].read_bytes() == payload
