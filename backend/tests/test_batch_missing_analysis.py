"""Missing-aware analysis and cleaner/export/import roundtrip, no remote calls."""
import asyncio
import csv
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.services import data_service as data, data_cleaning_service as cleaning


CONFIG = data.OUTCOME_CONFIGS["blood_pressure"]
HEADERS = data._get_required_columns(CONFIG)
EXPOSURES = [item["column"] for item in CONFIG["exposures"]]


def fixture(rows):
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def valid_row(identifier="0001", **changes):
    row = dict.fromkeys(HEADERS, "1")
    row["SEQN"] = identifier
    row["DEMO_J__RIDAGEYR"] = "35"
    for column in CONFIG["outcome_columns"]["sbp"]:
        row[column] = "120"
    for column in CONFIG["outcome_columns"]["dbp"]:
        row[column] = "75"
    row.update(changes)
    return row


class BatchMissingAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.before_data = dict(data.data_store)
        self.before_analysis = dict(data.analysis_store)
        self.directory = tempfile.TemporaryDirectory(prefix="batch-missing-test-")
        self.upload_patch = patch.object(data, "UPLOAD_DIR", self.directory.name)
        self.upload_patch.start()

    def tearDown(self):
        data.data_store.clear()
        data.data_store.update(self.before_data)
        data.analysis_store.clear()
        data.analysis_store.update(self.before_analysis)
        self.upload_patch.stop()
        self.directory.cleanup()

    def import_and_restore(self, payload):
        imported = asyncio.run(data.import_batch_file(payload, "missing.csv"))
        analysis = asyncio.run(data.get_dataset_analysis(imported.file_id))
        # Strict JSON rejects NaN/Infinity; source is saved byte-for-byte unchanged.
        json.dumps(analysis, allow_nan=False)
        saved_source = Path(self.directory.name, f"{imported.file_id}_missing.csv")
        self.assertEqual(saved_source.read_bytes(), payload)
        analysis_path = Path(self.directory.name, f"{imported.file_id}_analysis.json")
        self.assertEqual(json.loads(analysis_path.read_text(encoding="utf-8")), analysis)
        del data.analysis_store[imported.file_id]
        self.assertEqual(asyncio.run(data.get_dataset_analysis(imported.file_id)), analysis)
        return imported, analysis

    def test_default_cleaner_keeps_missing_cells_and_imports_actual_data(self):
        measured = valid_row("0001")
        missing = valid_row("0002", **dict.fromkeys(EXPOSURES, ""))
        missing[CONFIG["outcome_columns"]["sbp"][2]] = ""
        missing[CONFIG["outcome_columns"]["dbp"][2]] = ""
        child = valid_row("0003", DEMO_J__RIDAGEYR="12")
        original = fixture([measured, missing, child])
        payload, _, result = cleaning.export_table(original, "source.csv", cleaning.CleaningOptions(
            confirm_system_semantics=True, drop_invalid_system_rows=True).model_dump_json())
        self.assertTrue(result["system_ready"])
        self.assertEqual(result["total_rows"], 2)
        exported = list(csv.DictReader(StringIO(payload.decode("utf-8-sig"))))
        self.assertEqual(exported, [measured, missing])
        imported, analysis = self.import_and_restore(payload)
        self.assertEqual(imported.analysis_records, 2)
        self.assertEqual(analysis["metadata"]["excluded_records"], 0)
        self.assertIsNone(analysis["bubble"]["points"][1]["exposure_percentile"])
        self.assertEqual(analysis["bubble"]["unknown_exposure_records"], 1)
        self.assertEqual(analysis["bubble"]["sampled_unknown_exposure_records"], 1)
        self.assertTrue(any("气泡图不绘制" in warning for warning in analysis["metadata"]["warnings"]))
        self.assertTrue(data.data_store[imported.file_id][EXPOSURES].iloc[1].isna().all())

    def test_all_missing_exposure_has_no_fabricated_density_or_boxplot(self):
        payload = fixture([valid_row("0001", **dict.fromkeys(EXPOSURES, "")),
                           valid_row("0002", **dict.fromkeys(EXPOSURES, ""))])
        _, analysis = self.import_and_restore(payload)
        self.assertEqual(analysis["boxplot"]["values"], [[None] * 5] * 5)
        for series in analysis["density"]["series"]:
            self.assertEqual(series["x"], [])
            self.assertEqual(series["values"], [])
        for series in analysis["histogram"]["series"]:
            self.assertEqual(sum(series["values"]), 0)
        self.assertEqual(analysis["bubble"]["unknown_exposure_records"], 2)

    def test_constant_metal_standardizes_only_observed_values(self):
        payload = fixture([valid_row("0001"), valid_row("0002", **{EXPOSURES[0]: ""}), valid_row("0003")])
        _, analysis = self.import_and_restore(payload)
        self.assertEqual(sum(analysis["histogram"]["series"][0]["values"]), 2)
        self.assertEqual(analysis["exposure_statistics"][0]["n"], 2)
        self.assertEqual(analysis["completeness"][0]["missing_count"], 1)
        self.assertEqual(analysis["boxplot"]["values"][0], [0.0] * 5)

    def test_no_eligible_adults_is_missing_not_nan(self):
        imported, analysis = self.import_and_restore(fixture([valid_row(DEMO_J__RIDAGEYR="12")]))
        self.assertEqual(imported.analysis_records, 0)
        self.assertIsNone(analysis["kpis"]["mean_sbp"])
        self.assertEqual(analysis["bubble"]["points"], [])
        self.assertEqual(analysis["boxplot"]["values"], [[None] * 5] * 5)

    def test_illegal_infinity_is_rejected_without_partial_storage(self):
        for invalid in ("inf", "-inf"):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(data.DatasetValidationError, "无穷"):
                asyncio.run(data.import_batch_file(fixture([valid_row(**{EXPOSURES[0]: invalid})]), "invalid.csv"))
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])
        self.assertEqual(set(data.data_store), set(self.before_data))
        self.assertEqual(set(data.analysis_store), set(self.before_analysis))

    def test_nonfinite_derived_output_fails_before_storage(self):
        with patch.object(data, "_build_analysis", return_value={"metadata": {"warnings": []}, "unexpected": float("inf")}), self.assertRaisesRegex(data.DatasetValidationError, "未保存"):
            asyncio.run(data.import_batch_file(fixture([valid_row()]), "invalid.csv"))
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])
        self.assertEqual(set(data.data_store), set(self.before_data))
        with self.assertRaisesRegex(data.DatasetValidationError, "无穷"):
            data._json_missing_values({"value": float("inf")})
        self.assertEqual(data._json_missing_values({"value": float("nan")}), {"value": None})


if __name__ == "__main__":
    unittest.main()
