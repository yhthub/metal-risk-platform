"""Contract and real saved-model inference tests; no model fitting or remote IO."""
from copy import deepcopy
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pandas as pd
from pydantic import ValidationError

from app.api.prediction import router
from app.models.prediction_schemas import BatchPredictionRequest, PersonPredictionRequest
from app.services import data_service
from app.services import nhanes_prediction_service as prediction


MODEL_ROOT = Path(__file__).resolve().parents[2] / "models" / "nhanes_v5"
HAS_NATIVE = all(importlib.util.find_spec(name) is not None for name in ("xgboost", "catboost", "threadpoolctl"))
HAS_ASSETS = (MODEL_ROOT / "integrity.json").is_file()


def demo():
    return prediction.get_prediction_demo()["payload"]


def request(**person_changes):
    payload = demo()
    payload["person"].update(person_changes)
    return PersonPredictionRequest.model_validate(payload)


class ContractTests(unittest.TestCase):
    def test_demo_is_explicitly_synthetic(self):
        payload = prediction.get_prediction_demo()
        self.assertTrue(payload["is_demo"])
        self.assertIn("合成", payload["notice"])
        self.assertEqual(PersonPredictionRequest.model_validate(payload["payload"]).person.age, 45)

    def test_unknown_covariates_stay_missing_not_unknown_or_zero(self):
        payload = demo()
        payload["covariates"] = {}
        original = deepcopy(payload)
        encoded, _ = prediction._encode(PersonPredictionRequest.model_validate(payload))
        self.assertEqual(payload, original)
        self.assertEqual(len(encoded), 24)
        self.assertTrue(all(encoded[key] is None for key in encoded if "__" in key))
        self.assertIsNone(encoded["alcohol_any_past_year"])
        self.assertEqual(encoded["sex_female"], 0)

    def test_complete_one_hot_category(self):
        encoded, _ = prediction._encode(request())
        self.assertEqual(sum(encoded[key] for key in encoded if key.startswith("smoking__")), 1)
        self.assertEqual(encoded["smoking__less_than_100_lifetime"], 1)
        self.assertEqual(encoded["smoking__unknown"], 0)

    def test_conversion_is_explicit_and_original_is_preserved(self):
        payload = demo()
        payload["person"]["pb"] = 15.0
        payload["measurements"]["pb"]["unit"] = "μg/L"
        original = deepcopy(payload)
        encoded, audit = prediction._encode(PersonPredictionRequest.model_validate(payload))
        self.assertEqual(encoded["blood_lead_ug_dl"], 1.5)
        self.assertEqual(audit[0]["conversion_factor"], 0.1)
        self.assertEqual(audit[0]["original_unit"], "μg/L")
        self.assertEqual(payload, original)
        payload["measurements"]["pb"]["unit"] = "ng/mL"
        encoded, audit = prediction._encode(PersonPredictionRequest.model_validate(payload))
        self.assertEqual(encoded["blood_lead_ug_dl"], 1.5)
        self.assertEqual(audit[0]["conversion_factor"], 0.1)

    def test_missing_and_unconfirmed_measurements_are_rejected(self):
        for mutation in ("missing", "urine", "serum", "unconfirmed", "wrong_analyte", "unknown_unit"):
            with self.subTest(mutation=mutation):
                payload = demo()
                if mutation == "missing":
                    del payload["measurements"]["hg"]
                elif mutation in {"urine", "serum"}:
                    payload["measurements"]["hg"]["sample"] = mutation
                elif mutation == "unconfirmed":
                    payload["measurements"]["hg"]["confirmed"] = False
                elif mutation == "wrong_analyte":
                    payload["measurements"]["hg"]["analyte"] = "cadmium"
                else:
                    payload["measurements"]["hg"]["unit"] = "ug/g"
                with self.assertRaises((ValidationError, prediction.PredictionError)):
                    prediction._encode(PersonPredictionRequest.model_validate(payload))

    def test_required_missing_nonfinite_and_boolean_are_rejected(self):
        for value in (None, "", True, "1.2", float("nan"), float("inf"), float("-inf"), -0.1):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                request(pb=value)
        with self.assertRaises(prediction.PredictionError):
            prediction._encode(request(pb=1e100))
        with self.assertRaises(prediction.PredictionError):
            prediction._encode(request(pb=1e-100))

    def test_true_zero_metal_is_not_a_missing_value(self):
        encoded, _ = prediction._encode(request(pb=0, cd=0, hg=0))
        self.assertEqual(encoded["blood_lead_ug_dl"], 0)
        self.assertEqual(encoded["blood_cadmium_ug_l"], 0)

    def test_explicit_gender_adult_age_and_bmi_contract(self):
        for updates in ({"gender": ""}, {"gender_confirmed": False}, {"gender_confirmed": 1},
                        {"age": 17}, {"age": 81}, {"age": 40.5}, {"bmi": 0}):
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                request(**updates)

    def test_no_legacy_or_unknown_category_guessing(self):
        for group, value in (("education", "bachelor"), ("smoking", "never"),
                             ("marital", "unmarried"), ("education", "unknown"),
                             ("alcohol_any_past_year", "frequent")):
            payload = demo()
            payload["covariates"][group] = value
            with self.subTest(group=group, value=value), self.assertRaises(ValidationError):
                PersonPredictionRequest.model_validate(payload)
        payload = demo()
        payload["person"]["work_years"] = 10
        with self.assertRaises(ValidationError):
            PersonPredictionRequest.model_validate(payload)


class ApiContractTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_missing_models_are_503_without_fabricated_predictions(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NHANES_MODEL_ROOT": directory}):
            response = self.client.post("/api/risk/predict", json=demo())
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("results", response.json())
            status = self.client.get("/api/risk/status").json()
            self.assertFalse(status["ready"])
            self.assertEqual(status["profile"], "basic")
            self.assertIn("measurement_contract", status["contract"])

    def test_invalid_json_nonfinite_is_422_not_error_serialization_500(self):
        payload = demo()
        for value in (float("nan"), float("inf"), float("-inf")):
            payload["person"]["pb"] = value
            response = self.client.post("/api/risk/predict", content=json.dumps(payload),
                                        headers={"Content-Type": "application/json"})
            self.assertEqual(response.status_code, 422, response.text)
            self.assertIn("detail", response.json())

    def test_missing_measurement_is_422(self):
        payload = demo()
        del payload["measurements"]["cd"]
        response = self.client.post("/api/risk/predict", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_concurrent_prediction_is_bounded(self):
        self.assertTrue(prediction._capacity.acquire(blocking=False))
        try:
            response = self.client.post("/api/risk/predict", json=demo())
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers["retry-after"], "2")
        finally:
            prediction._capacity.release()

    def test_batch_rejects_file_path_as_file_id(self):
        response = self.client.post("/api/risk/predict-batch", json={
            "file_id": "../../private.csv", "measurements": demo()["measurements"]})
        self.assertEqual(response.status_code, 422)

    def test_batch_without_bmi_explains_missing_field(self):
        frame = pd.DataFrame([{name: 1 for name in prediction.CONTRACT["batch_required_columns"] if name != "BMX_J__BMXBMI"}])
        with patch.object(prediction, "_batch_frame", return_value=frame):
            response = self.client.post("/api/risk/predict-batch", json={
                "file_id": "FILE-12345678", "measurements": demo()["measurements"]})
        self.assertEqual(response.status_code, 422)
        self.assertIn("BMX_J__BMXBMI", response.json()["detail"])

    def test_fixed_nhanes_batch_column_units_cannot_be_relabelled(self):
        for key, unit in (("pb", "ug/L"), ("pb", "ng/mL"), ("cd", "ug/dL"), ("hg", "ug/dL")):
            with self.subTest(key=key, unit=unit):
                measurements = demo()["measurements"]
                measurements[key]["unit"] = unit
                with patch.object(prediction, "_batch_frame") as frame:
                    response = self.client.post("/api/risk/predict-batch", json={
                        "file_id": "FILE-12345678", "measurements": measurements})
                self.assertEqual(response.status_code, 422)
                self.assertIn("固定NHANES J", response.json()["detail"])
                frame.assert_not_called()

    def test_batch_canonical_greek_units_and_equal_ng_ml_are_accepted(self):
        measurements = demo()["measurements"]
        measurements["pb"]["unit"] = "μg/dL"
        measurements["cd"]["unit"] = "µg/L"
        measurements["hg"]["unit"] = "ng/mL"
        original = deepcopy(measurements)
        validated = prediction._check_batch_metadata(measurements)
        self.assertEqual(validated, original)
        self.assertEqual(measurements, original)


@unittest.skipUnless(HAS_NATIVE and HAS_ASSETS, "Needs installed native runtime and released v5 local model assets")
class RealSavedModelTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"NHANES_MODEL_ROOT": str(MODEL_ROOT)})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    def test_real_saved_models_predict_twelve_outcomes_with_accuracy_guard(self):
        payload = request()
        result = prediction.predict_person(payload)
        self.assertEqual(result["run_id"], prediction.RUN_ID)
        self.assertEqual(result["profile"], "basic")
        self.assertEqual(len(result["results"]), 12)
        numeric = [item for item in result["results"] if item["prediction"] is not None]
        withheld = [item for item in result["results"] if item["prediction"] is None]
        self.assertEqual(len(numeric), 7)
        self.assertEqual(len(withheld), 5)
        self.assertTrue(all(math.isfinite(item["prediction"]) for item in numeric))
        self.assertTrue(all(item["reference_interval"]["guaranteed_coverage"] is False for item in numeric))
        self.assertTrue(all(item["status"] == "INSUFFICIENT_VALIDATED_ACCURACY" for item in withheld))
        self.assertTrue(all(item["test_metrics"]["n"] > 0 for item in result["results"]))
        json.dumps(result, allow_nan=False)

    def test_actual_api_and_model_readiness(self):
        app = FastAPI()
        app.include_router(router)
        with TestClient(app) as client:
            status = client.get("/api/risk/status")
            self.assertEqual(status.status_code, 200)
            self.assertTrue(status.json()["ready"], status.text)
            response = client.post("/api/risk/predict", json=demo())
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(len(response.json()["results"]), 12)
            self.assertEqual(response.headers["cache-control"], "no-store")

    def test_explicit_unit_conversion_matches_real_prediction(self):
        first = prediction.predict_person(request())
        payload = demo()
        payload["person"]["pb"] *= 10
        payload["measurements"]["pb"]["unit"] = "ug/L"
        second = prediction.predict_person(PersonPredictionRequest.model_validate(payload))
        self.assertEqual([item["prediction"] for item in first["results"]],
                         [item["prediction"] for item in second["results"]])

    def test_missing_optional_inputs_still_run_without_zero_imputation(self):
        payload = demo()
        payload["covariates"] = {}
        result = prediction.predict_person(PersonPredictionRequest.model_validate(payload))
        self.assertEqual(len(result["results"]), 12)
        self.assertIsNone(result["encoded_input"]["education__unknown"])
        self.assertIsNone(result["encoded_input"]["smoking__current"])
        self.assertTrue(any("可选资料未知" in warning for warning in result["warnings"]))

    def test_sha_mismatch_disables_even_previously_cached_models(self):
        # Mutate only a temporary copied asset generation, never the real release.
        prediction.predict_person(request())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "models"
            root.mkdir()
            shutil.copy2(MODEL_ROOT / "integrity.json", root / "integrity.json")
            shutil.copy2(MODEL_ROOT / "registry.json", root / "registry.json")
            shutil.copytree(MODEL_ROOT / "basic", root / "basic")
            source = root / "basic" / "sbp" / "component_0.ubj"
            with source.open("ab") as stream:
                stream.write(b"tamper")
            with patch.dict(os.environ, {"NHANES_MODEL_ROOT": str(root)}):
                with self.assertRaises(prediction.PredictionError) as caught:
                    prediction.predict_person(request())
                self.assertEqual(caught.exception.status_code, 503)
                self.assertFalse(prediction.get_prediction_status()["ready"])

    def test_real_vectorized_batch_skips_invalid_row_and_no_id_duplicates(self):
        columns = prediction.CONTRACT["batch_required_columns"]
        frame = pd.DataFrame([
            dict(zip(columns, ["1", 45, 1, 25.0, 1.5, 0.4, 1.2])),
            dict(zip(columns, ["2", 17, 2, 22.0, 1.0, 0.2, 0.8])),
            dict(zip(columns, ["3", 48, 2, 24.0, 1.0, 0.2, 0.8])),
        ])
        payload = BatchPredictionRequest.model_validate({"file_id": "FILE-12345678", "measurements": demo()["measurements"]})
        with patch.object(prediction, "_batch_frame", return_value=frame):
            result = prediction.predict_batch(payload)
        self.assertEqual(result["processed_records"], 2)
        self.assertEqual(result["skipped_records"], 1)
        self.assertEqual(result["records"][1]["status"], "INPUT_NOT_ELIGIBLE")
        self.assertEqual(len(result["records"][0]["results"]), 12)
        self.assertEqual(result["summary"][0]["estimated_count"], 2)
        self.assertIsNone(result["summary"][5]["mean_prediction"])
        frame.loc[2, "SEQN"] = "1"
        with patch.object(prediction, "_batch_frame", return_value=frame), self.assertRaises(prediction.PredictionError):
            prediction.predict_batch(payload)
        frame.loc[2, "SEQN"] = "1.0"
        with patch.object(prediction, "_batch_frame", return_value=frame), self.assertRaises(prediction.PredictionError):
            prediction.predict_batch(payload)

    def test_equal_ng_ml_does_not_change_batch_numerical_results(self):
        columns = prediction.CONTRACT["batch_required_columns"]
        frame = pd.DataFrame([dict(zip(columns, ["1", 45, 1, 25.0, 1.5, 0.4, 1.2]))])
        canonical = {"file_id": "FILE-12345678", "measurements": demo()["measurements"]}
        with patch.object(prediction, "_batch_frame", return_value=frame):
            first = prediction.predict_batch(BatchPredictionRequest.model_validate(canonical))
        equivalent = deepcopy(canonical)
        equivalent["measurements"]["pb"]["unit"] = "μg/dL"
        equivalent["measurements"]["cd"]["unit"] = "ng/mL"
        equivalent["measurements"]["hg"]["unit"] = "ng/mL"
        with patch.object(prediction, "_batch_frame", return_value=frame):
            second = prediction.predict_batch(BatchPredictionRequest.model_validate(equivalent))
        self.assertEqual([item["prediction"] for item in first["records"][0]["results"]],
                         [item["prediction"] for item in second["records"][0]["results"]])
        self.assertTrue(all(item["conversion_factor"] == 1 for item in second["records"][0]["measurement_audit"]))


if __name__ == "__main__":
    unittest.main()
