"""All-uploaded-record inference tests; never train or use remote resources."""
import importlib.util
from contextlib import ExitStack
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import numpy as np
import pandas as pd

from app.api.prediction import router
from app.models.prediction_schemas import CohortPredictionRequest
from app.services import nhanes_cohort_service as cohort
from app.services import data_service
from app.services import nhanes_prediction_service as native


MODEL_ROOT = Path(__file__).resolve().parents[2] / "models" / "nhanes_v5"
HAS_NATIVE = all(importlib.util.find_spec(name) is not None for name in ("xgboost", "catboost", "threadpoolctl"))
HAS_ASSETS = (MODEL_ROOT / "integrity.json").is_file()


def request():
    return {"file_id": "FILE-12345678", "measurements": native.get_prediction_demo()["payload"]["measurements"]}


def frame(rows=3):
    """Synthetic contract fixture only; never labelled as NHANES source data."""
    columns = native.CONTRACT["batch_required_columns"]
    return pd.DataFrame([dict(zip(columns, [str(100000 + index), 18 + index % 63, 1 + index % 2,
        22 + (index % 10) * 0.2, 1.0 + index * 0.001, 0.3 + (index % 9) * 0.02, 1.2 + (index % 7) * 0.1]))
        for index in range(rows)])


class CohortContractTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_public_api_has_no_paging_or_sampling_request_parameters(self):
        for key, value in (("offset", 20), ("limit", 20), ("sample_size", 20)):
            payload = request()
            payload[key] = value
            response = self.client.post("/api/risk/predict-cohort", json=payload)
            self.assertEqual(response.status_code, 422)

    def test_shared_native_capacity_still_limits_to_one_inference_job(self):
        self.assertTrue(native._capacity.acquire(blocking=False))
        try:
            response = self.client.post("/api/risk/predict-cohort", json=request())
            self.assertEqual(response.status_code, 429)
        finally:
            native._capacity.release()

    def test_missing_whole_bmi_column_is_an_explicit_422(self):
        with patch.object(native, "_batch_frame", return_value=frame().drop(columns="BMX_J__BMXBMI")):
            response = self.client.post("/api/risk/predict-cohort", json=request())
        self.assertEqual(response.status_code, 422)
        self.assertIn("BMX_J__BMXBMI", response.json()["detail"])

    def test_fixed_nhanes_units_and_duplicate_ids_cannot_be_ignored(self):
        payload = request()
        payload["measurements"]["pb"]["unit"] = "ug/L"
        with patch.object(native, "_batch_frame") as read:
            response = self.client.post("/api/risk/predict-cohort", json=payload)
        self.assertEqual(response.status_code, 422)
        read.assert_not_called()
        duplicate = frame()
        duplicate.loc[1, "SEQN"] = duplicate.loc[0, "SEQN"] + ".0"
        with patch.object(native, "_batch_frame", return_value=duplicate):
            response = self.client.post("/api/risk/predict-cohort", json=request())
        self.assertEqual(response.status_code, 422)
        self.assertIn("重复", response.json()["detail"])

    def test_existing_import_capacity_limit_is_enforced_without_truncation(self):
        with patch.dict(os.environ, {"BATCH_MAX_ROWS": "2"}), patch.object(native, "_batch_frame", return_value=frame(3)):
            response = self.client.post("/api/risk/predict-cohort", json=request())
        self.assertEqual(response.status_code, 413)
        self.assertNotIn("records", response.json())

    def test_missing_models_return_503_not_synthetic_group_statistics(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NHANES_MODEL_ROOT": directory}), \
                patch.object(native, "_batch_frame", return_value=frame(3)):
            response = self.client.post("/api/risk/predict-cohort", json=request())
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("summary", response.json())


@unittest.skipUnless(HAS_NATIVE and HAS_ASSETS, "Needs installed native runtime and released local v5 models")
class RealCohortTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"NHANES_MODEL_ROOT": str(MODEL_ROOT)})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    def test_whole_cohort_exceeds_old_page_cap_and_all_statistics_match_all_records(self):
        source = frame(1005)
        original = source.copy(deep=True)
        with patch.object(native, "_batch_frame", return_value=source), \
                patch.object(native, "_predictions", wraps=native._predictions) as inference:
            result = cohort.predict_cohort(CohortPredictionRequest.model_validate(request()))
        pd.testing.assert_frame_equal(source, original)
        self.assertTrue(result["complete"])
        self.assertEqual(result["analysis_scope"], "all_uploaded_records")
        self.assertEqual(result["total_records"], 1005)
        self.assertEqual(result["processed_records"], 1005)
        self.assertEqual(result["skipped_records"], 0)
        self.assertEqual(result["limit"], 1005)
        self.assertFalse(result["has_more"])
        self.assertEqual(len(result["records"]), 1005)
        self.assertEqual(result["demographic_profile"]["total_records"], 1005)
        self.assertEqual(result["demographic_profile"]["sex"]["valid_count"], 1005)
        self.assertEqual(result["records"][-1]["person_id"], "101004")
        self.assertEqual(sum(len(call.args[1]) for call in inference.call_args_list), 1005)
        self.assertEqual(inference.call_count, 2)
        self.assertFalse(result["provenance"]["sampling_used"])
        self.assertFalse(result["provenance"]["page_limiting_used"])
        self.assertTrue(all(len(record["results"]) == 12 and "input" in record for record in result["records"]))
        self.assertEqual(len(result["outcome_metadata"]), 12)
        self.assertTrue(all("test_metrics" in item for item in result["outcome_metadata"]))
        self.assertTrue(all("test_metrics" not in item and "missing_input_fields" not in item
                            for record in result["records"] for item in record["results"]))
        for summary in result["summary"]:
            values = np.asarray([item["prediction"] for record in result["records"] for item in record["results"]
                                 if item["target"] == summary["target"] and item["prediction"] is not None])
            self.assertEqual(summary["estimated_count"], len(values))
            self.assertEqual(summary["statistics"]["n"], len(values))
            self.assertEqual(sum(item["eligible_count"] for item in summary["by_gender"]), 1005)
            self.assertEqual(sum(item["eligible_count"] for item in summary["by_age_band"]), 1005)
            self.assertEqual(sum(summary["histogram"]["counts"]), len(values))
            if len(values):
                stats = summary["statistics"]
                self.assertAlmostEqual(stats["mean"], float(values.mean()), places=10)
                self.assertAlmostEqual(stats["median"], float(np.median(values)), places=10)
                self.assertAlmostEqual(stats["std"], float(np.std(values, ddof=0)), places=10)
                self.assertEqual(summary["withheld_count"], 0)
                self.assertEqual(len(summary["histogram"]["counts"]), 10)
                self.assertEqual(len(summary["histogram"]["bin_edges"]), 11)
            else:
                self.assertEqual(summary["withheld_count"], 1005)
                self.assertIsNone(summary["statistics"]["mean"])
                self.assertEqual(summary["status"], "INSUFFICIENT_VALIDATED_ACCURACY")
        sbp = next(item for item in result["summary"] if item["target"] == "sbp")
        male = next(group for group in sbp["by_gender"] if group["group"] == "male")
        expected = [next(item["prediction"] for item in record["results"] if item["target"] == "sbp")
                    for record in result["records"] if record["input"]["person"]["gender"] == "male"]
        self.assertEqual(male["eligible_count"], len(expected))
        self.assertAlmostEqual(male["statistics"]["mean"], float(np.mean(expected)), places=10)
        json.dumps(result, allow_nan=False)

    def test_bad_rows_are_kept_with_specific_missing_bmi_reasons(self):
        source = frame(5)
        source.loc[1, "BMX_J__BMXBMI"] = np.nan
        source.loc[3, "DEMO_J__RIDAGEYR"] = 17
        source.loc[4, "PBCD_J__LBXBCD"] = -1
        with patch.object(native, "_batch_frame", return_value=source):
            result = cohort.predict_cohort(CohortPredictionRequest.model_validate(request()))
        self.assertEqual(result["processed_records"], 2)
        self.assertEqual(result["skipped_records"], 3)
        self.assertEqual(len(result["records"]), 5)
        profile = result["demographic_profile"]
        self.assertEqual(profile["total_records"], 5)
        self.assertEqual(profile["sex"]["valid_count"], 5)
        self.assertEqual(profile["age"]["valid_count"], 5)
        self.assertEqual(profile["age"]["min"], 17)
        self.assertEqual(profile["age"]["bands"][0]["count"], 1)
        self.assertEqual(profile["bmi"]["missing_count"], 1)
        self.assertEqual(result["records"][1]["status"], "INPUT_NOT_ELIGIBLE")
        self.assertIn("BMI", result["records"][1]["reason"])
        self.assertIn("BMX_J__BMXBMI", result["records"][1]["reason"])
        self.assertEqual(next(item for item in result["summary"] if item["target"] == "sbp")["estimated_count"], 2)

    def test_all_bad_rows_return_no_eligible_state_and_null_not_zero_statistics(self):
        source = frame(3)
        source["BMX_J__BMXBMI"] = np.nan
        with patch.object(native, "_batch_frame", return_value=source):
            result = cohort.predict_cohort(CohortPredictionRequest.model_validate(request()))
        self.assertTrue(result["complete"])
        self.assertEqual(result["status"], "NO_ELIGIBLE_RECORDS")
        self.assertEqual(result["processed_records"], 0)
        self.assertEqual(result["skipped_records"], 3)
        self.assertEqual(result["demographic_profile"]["sex"]["valid_count"], 3)
        self.assertEqual(result["demographic_profile"]["bmi"]["valid_count"], 0)
        self.assertIsNone(result["demographic_profile"]["bmi"]["mean"])
        self.assertTrue(all(item["mean_prediction"] is None for item in result["summary"]))
        self.assertTrue(all(item["histogram"]["counted_records"] == 0 for item in result["summary"]))

    def test_actual_api_returns_every_record_and_not_a_paged_response(self):
        app = FastAPI()
        app.include_router(router)
        with TestClient(app) as client, patch.object(native, "_batch_frame", return_value=frame(503)):
            response = client.post("/api/risk/predict-cohort", json=request())
        self.assertEqual(response.status_code, 200, response.text[:1000])
        result = response.json()
        self.assertEqual(len(result["records"]), 503)
        self.assertEqual(result["processed_records"], 503)
        self.assertTrue(result["complete"])
        self.assertEqual(result["analysis_scope"], "all_uploaded_records")
        self.assertEqual(result["demographic_profile"]["total_records"], 503)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_person_601_can_be_the_maximum_and_is_not_lost_in_first_page(self):
        source = frame(700)
        source["DEMO_J__RIDAGEYR"] = 25
        source["DEMO_J__RIAGENDR"] = 1
        source["BMX_J__BMXBMI"] = 22.0
        source["PBCD_J__LBXBPB"] = 1.0
        source["PBCD_J__LBXBCD"] = 0.3
        source["PBCD_J__LBXTHG"] = 1.2
        source.loc[600, "DEMO_J__RIDAGEYR"] = 80
        source.loc[600, "DEMO_J__RIAGENDR"] = 2
        source.loc[600, "BMX_J__BMXBMI"] = 40
        with patch.object(native, "_batch_frame", return_value=source):
            result = cohort.predict_cohort(CohortPredictionRequest.model_validate(request()))
        values = [next(item["prediction"] for item in record["results"] if item["target"] == "sbp")
                  for record in result["records"]]
        largest = int(np.argmax(values))
        self.assertEqual(largest, 600)
        self.assertEqual(result["records"][largest]["person_id"], "100600")
        self.assertEqual(next(item for item in result["summary"] if item["target"] == "sbp")["statistics"]["max"],
                         values[600])
        self.assertEqual(len(result["records"]), 700)

    def test_real_public_demo_import_runs_whole_cohort_without_page_contract(self):
        app = FastAPI()
        app.include_router(router)
        with ExitStack() as stack:
            directory = stack.enter_context(tempfile.TemporaryDirectory())
            stack.enter_context(patch.object(data_service, "UPLOAD_DIR", directory))
            for name in ("data_store", "analysis_store", "_cache_sizes"):
                stack.enter_context(patch.dict(getattr(data_service, name), {}, clear=True))
            client = stack.enter_context(TestClient(app))
            imported = client.post("/api/risk/demo-batch/import")
            self.assertEqual(imported.status_code, 200, imported.text)
            body = imported.json()
            response = client.post("/api/risk/predict-cohort", json={
                "file_id": body["import_result"]["file_id"], "measurements": body["measurements"]})
        self.assertEqual(response.status_code, 200, response.text[:1000])
        result = response.json()
        self.assertEqual(result["processed_records"], 20)
        self.assertEqual(result["skipped_records"], 0)
        self.assertTrue(result["complete"])
        self.assertEqual(result["analysis_scope"], "all_uploaded_records")
        self.assertEqual(len(result["records"]), result["total_records"])
        self.assertEqual(len(result["summary"]), 12)
        profile = result["demographic_profile"]
        self.assertEqual(profile["total_records"], 20)
        self.assertEqual(profile["sex"]["valid_count"], 20)
        self.assertEqual(profile["education"]["valid_count"], 20)
        self.assertEqual(profile["marital"]["valid_count"], 20)
        self.assertFalse(profile["weighted"])
        self.assertEqual(sum(item["statistics"]["n"] == 20 for item in result["summary"]), 7)


if __name__ == "__main__":
    unittest.main()
