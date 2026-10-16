"""Real public demo integrity, independent imports and real model round-trip."""
from contextlib import ExitStack
from copy import deepcopy
import csv
import hashlib
import importlib.util
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.prediction import router
from app.services import data_service
from app.services import nhanes_risk_demo_service as demo


MODEL_ROOT = Path(__file__).resolve().parents[2] / "models" / "nhanes_v5"
HAS_NATIVE = all(importlib.util.find_spec(name) is not None for name in ("xgboost", "catboost", "threadpoolctl"))
HAS_ASSETS = (MODEL_ROOT / "integrity.json").is_file()


class PublicRiskDemoTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def _temporary_assets(self, stack):
        directory = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        for name in (demo.MANIFEST_NAME, demo.SAMPLE_NAME):
            shutil.copy2(demo.ASSET_DIR / name, directory / name)
        stack.enter_context(patch.object(demo, "ASSET_DIR", directory))
        return directory

    def _isolated_uploads(self, stack):
        directory = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        stack.enter_context(patch.object(data_service, "UPLOAD_DIR", str(directory)))
        for name in ("data_store", "analysis_store", "_cache_sizes"):
            stack.enter_context(patch.dict(getattr(data_service, name), {}, clear=True))
        return directory

    def test_fixed_asset_has_twenty_actual_bmi_records_and_verified_provenance(self):
        manifest, content = demo._load_risk_demo()
        self.assertEqual(manifest["rows"], 20)
        self.assertEqual(len(manifest["columns"]), 24)
        self.assertEqual(hashlib.sha256(content).hexdigest(), demo.SAMPLE_SHA256)
        self.assertEqual(len(content), manifest["sample_bytes"])
        self.assertTrue(manifest["join"]["same_cycle"])
        self.assertTrue(manifest["join"]["selected_bmi_equal_raw_xpt"])
        self.assertFalse(manifest["join"]["imputation"])
        self.assertFalse(manifest["preparation"]["prediction_results_precomputed"])
        self.assertEqual(manifest["source_files"][1]["file"], "BMX_J.csv")
        rows = list(csv.DictReader(StringIO(content.decode("utf-8-sig"))))
        self.assertEqual(len(rows), 20)
        self.assertTrue(all(float(row["BMX_J__BMXBMI"]) > 0 for row in rows))
        self.assertTrue(any("独立" in item for item in manifest["limitations"]))

    def test_original_public_sample_strings_are_preserved_without_modification(self):
        _, content = demo._load_risk_demo()
        original_path = Path(__file__).resolve().parents[1] / "app" / "data" / "NHANES_2017-2018_public_adults_300.csv"
        original_bytes = original_path.read_bytes()
        self.assertEqual(hashlib.sha256(original_bytes).hexdigest(), demo.SOURCE_PINS[original_path.name][1])
        original = {demo._public_id(row["SEQN"]): row for row in csv.DictReader(StringIO(original_bytes.decode("utf-8-sig")))}
        for row in csv.DictReader(StringIO(content.decode("utf-8-sig"))):
            source = original[demo._public_id(row["SEQN"])]
            self.assertEqual({key: row[key] for key in source}, source)
        self.assertEqual(original_path.read_bytes(), original_bytes)

    def test_metadata_api_does_not_precompute_predictions_or_import_user_files(self):
        with patch.object(demo, "import_batch_file", new_callable=AsyncMock) as imported:
            response = self.client.get("/api/risk/demo-batch")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["rows"], 20)
        self.assertNotIn("predictions", response.json())
        self.assertEqual(response.headers["cache-control"], "no-store")
        imported.assert_not_awaited()

    def test_missing_assets_are_503_without_any_import(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(demo, "ASSET_DIR", Path(directory)), \
                patch.object(demo, "import_batch_file", new_callable=AsyncMock) as imported:
            response = self.client.post("/api/risk/demo-batch/import")
        self.assertEqual(response.status_code, 503)
        imported.assert_not_awaited()

    def test_changed_csv_is_rejected_even_if_manifest_checksum_is_recomputed(self):
        with ExitStack() as stack:
            directory = self._temporary_assets(stack)
            path = directory / demo.SAMPLE_NAME
            path.write_bytes(path.read_bytes().replace(b",66.0,2.0,4.0,", b",65.0,2.0,4.0,", 1))
            changed_bytes = path.read_bytes()
            manifest_path = directory / demo.MANIFEST_NAME
            manifest = json.loads(manifest_path.read_text("utf-8"))
            manifest["sample_sha256"] = hashlib.sha256(changed_bytes).hexdigest()
            manifest["sample_bytes"] = len(changed_bytes)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(demo, "import_batch_file", new_callable=AsyncMock) as imported:
                response = self.client.post("/api/risk/demo-batch/import")
            self.assertEqual(response.status_code, 503)
            imported.assert_not_awaited()

    def test_cross_cycle_or_measurement_unit_manifest_changes_are_rejected(self):
        for mutation in ("cycle", "source_hash", "unit", "one_to_many"):
            with self.subTest(mutation=mutation), ExitStack() as stack:
                directory = self._temporary_assets(stack)
                path = directory / demo.MANIFEST_NAME
                manifest = json.loads(path.read_text("utf-8"))
                if mutation == "cycle":
                    manifest["source_files"][1]["cycle"] = "2015-2016"
                elif mutation == "source_hash":
                    manifest["source_files"][1]["sha256"] = "0" * 64
                elif mutation == "unit":
                    manifest["measurement_contract"]["pb"]["unit"] = "ug/L"
                else:
                    manifest["join"]["validation"] = "one_to_many"
                path.write_text(json.dumps(manifest), encoding="utf-8")
                with patch.object(demo, "import_batch_file", new_callable=AsyncMock) as imported:
                    response = self.client.post("/api/risk/demo-batch/import")
                self.assertEqual(response.status_code, 503, response.text)
                imported.assert_not_awaited()

    def test_semantics_reject_bad_bmi_and_duplicate_person_without_imputation(self):
        manifest, content = demo._load_risk_demo()
        rows = list(csv.DictReader(StringIO(content.decode("utf-8-sig"))))
        for value in ("", "nan", "-1", "0", "5.397605346934028e-79"):
            changed = deepcopy(rows)
            changed[0]["BMX_J__BMXBMI"] = value
            with self.subTest(value=value), self.assertRaises(demo.RiskDemoError):
                demo._verify_semantics(changed, manifest["columns"], data_service.OUTCOME_CONFIGS["blood_pressure"])
        changed = deepcopy(rows)
        changed[1]["SEQN"] = changed[0]["SEQN"]
        with self.assertRaises(demo.RiskDemoError):
            demo._verify_semantics(changed, manifest["columns"], data_service.OUTCOME_CONFIGS["blood_pressure"])

    def test_each_import_gets_new_file_and_persists_correct_provenance(self):
        with ExitStack() as stack:
            directory = self._isolated_uploads(stack)
            first = self.client.post("/api/risk/demo-batch/import")
            second = self.client.post("/api/risk/demo-batch/import")
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(second.status_code, 200, second.text)
            one, two = first.json(), second.json()
            first_id, second_id = one["import_result"]["file_id"], two["import_result"]["file_id"]
            self.assertNotEqual(first_id, second_id)
            self.assertEqual(one["measurements"], demo.MEASUREMENTS)
            self.assertEqual(one["provenance"]["id"], demo.DEMO_ID)
            self.assertEqual(one["import_result"]["total_records"], 20)
            self.assertEqual(one["import_result"]["analysis_records"], 20)
            self.assertIn("BMX_J__BMXBMI", one["import_result"]["columns"])
            first_source = directory / (first_id + "_" + demo.SAMPLE_NAME)
            second_source = directory / (second_id + "_" + demo.SAMPLE_NAME)
            self.assertTrue(first_source.is_file())
            self.assertTrue(second_source.is_file())
            self.assertEqual(hashlib.sha256(first_source.read_bytes()).hexdigest(), demo.SAMPLE_SHA256)
            analysis = json.loads((directory / (first_id + "_analysis.json")).read_text("utf-8"))
            self.assertEqual(analysis["metadata"]["demo_provenance"]["id"], demo.DEMO_ID)
            self.assertNotIn("prediction", one)

    def test_import_failure_keeps_existing_api_error_status(self):
        failure = data_service.DatasetValidationError("测试容量限制", status_code=429)
        with patch.object(demo, "import_batch_file", new_callable=AsyncMock, side_effect=failure):
            response = self.client.post("/api/risk/demo-batch/import")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["retry-after"], "5")

    @unittest.skipUnless(HAS_NATIVE and HAS_ASSETS, "Needs installed native runtime and released local v5 models")
    def test_twenty_public_people_are_really_predicted_and_selected_person_explained(self):
        with ExitStack() as stack:
            self._isolated_uploads(stack)
            stack.enter_context(patch.dict(os.environ, {"NHANES_MODEL_ROOT": str(MODEL_ROOT)}))
            imported = self.client.post("/api/risk/demo-batch/import")
            self.assertEqual(imported.status_code, 200, imported.text)
            body = imported.json()
            response = self.client.post("/api/risk/predict-batch", json={
                "file_id": body["import_result"]["file_id"], "measurements": body["measurements"], "offset": 0, "limit": 20})
            self.assertEqual(response.status_code, 200, response.text)
            result = response.json()
            self.assertEqual(result["processed_records"], 20)
            self.assertEqual(result["skipped_records"], 0)
            self.assertFalse(result["has_more"])
            self.assertTrue(all(len(record["results"]) == 12 for record in result["records"]))
            self.assertEqual(sum(item["prediction"] is not None for record in result["records"] for item in record["results"]), 140)
            first = result["records"][0]
            detail = self.client.post("/api/risk/dashboard", json={"input": first["input"], "target": "sbp"})
            self.assertEqual(detail.status_code, 200, detail.text)
            self.assertEqual(detail.json()["charts"]["explanation"]["status"], "AVAILABLE")
            self.assertEqual(detail.json()["charts"]["dose_response"]["status"], "AVAILABLE")
            self.assertEqual(next(item["prediction"] for item in detail.json()["prediction"]["results"] if item["target"] == "sbp"),
                             next(item["prediction"] for item in first["results"] if item["target"] == "sbp"))


if __name__ == "__main__":
    unittest.main()
