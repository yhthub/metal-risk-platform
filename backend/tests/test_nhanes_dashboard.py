"""Real native chart tests. No training, remote service or background job."""
from copy import deepcopy
import importlib.util
import json
import math
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pandas as pd

from app.api.prediction import router
from app.models.prediction_schemas import (
    BatchPredictionRequest, DashboardPredictionRequest, PersonPredictionRequest,
)
from app.services import nhanes_dashboard_service as dashboard
from app.services import nhanes_prediction_service as native


MODEL_ROOT = Path(__file__).resolve().parents[2] / "models" / "nhanes_v5"
HAS_NATIVE = all(importlib.util.find_spec(name) is not None for name in ("xgboost", "catboost", "threadpoolctl"))
HAS_ASSETS = (MODEL_ROOT / "integrity.json").is_file()


def payload(target="sbp"):
    return {"input": native.get_prediction_demo()["payload"], "target": target}


class DashboardContractTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_unknown_target_and_extra_fields_rejected(self):
        wrong = payload("future_cancer_probability")
        self.assertEqual(self.client.post("/api/risk/dashboard", json=wrong).status_code, 422)
        wrong = payload()
        wrong["random_data"] = True
        self.assertEqual(self.client.post("/api/risk/dashboard", json=wrong).status_code, 422)

    def test_dashboard_and_person_prediction_share_same_capacity(self):
        self.assertTrue(native._capacity.acquire(blocking=False))
        try:
            response = self.client.post("/api/risk/dashboard", json=payload())
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers["retry-after"], "2")
        finally:
            native._capacity.release()

    def test_invalid_input_is_not_replaced_by_a_demo(self):
        wrong = payload()
        wrong["input"]["measurements"]["hg"]["confirmed"] = False
        self.assertEqual(self.client.post("/api/risk/dashboard", json=wrong).status_code, 422)
        wrong = payload()
        wrong["input"]["person"]["pb"] = float("nan")
        response = self.client.post("/api/risk/dashboard", content=json.dumps(wrong),
                                    headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 422)


@unittest.skipUnless(HAS_NATIVE and HAS_ASSETS, "Needs installed native runtime and released local v5 models")
class RealDashboardTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"NHANES_MODEL_ROOT": str(MODEL_ROOT)})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    def test_original_dashboard_api_computes_real_charts(self):
        app = FastAPI()
        app.include_router(router)
        with TestClient(app) as client:
            response = client.post("/api/risk/dashboard", json=payload())
        self.assertEqual(response.status_code, 200, response.text)
        output = response.json()
        self.assertEqual(output["input"], payload()["input"])
        self.assertEqual(len(output["prediction"]["results"]), 12)
        charts = output["charts"]
        self.assertEqual(charts["status"], "AVAILABLE")
        self.assertEqual(charts["explanation"]["status"], "AVAILABLE")
        self.assertEqual(charts["explanation"]["scale_label"], "mmHg")
        self.assertEqual(len(charts["dose_response"]["values"]), 16)
        self.assertEqual(len(charts["joint_response"]["values"]), 25)
        self.assertEqual(len(charts["joint_response"]["x_values"]), 5)
        self.assertEqual(len(charts["joint_response"]["y_values"]), 5)
        self.assertEqual(response.headers["cache-control"], "no-store")
        json.dumps(output, allow_nan=False)

    def test_grouped_shap_includes_missing_extra_features_and_closes(self):
        output = dashboard.build_dashboard(DashboardPredictionRequest.model_validate(payload()))
        explanation = output["charts"]["explanation"]
        other = next(item for item in explanation["items"] if item["feature"] == "other_unprovided_model_features")
        self.assertGreater(other["native_feature_count"], 0)
        self.assertNotEqual(other["value"], 0)
        self.assertEqual(other["input_state"], "not_provided")
        self.assertAlmostEqual(explanation["base_value"] + sum(item["value"] for item in explanation["items"]),
                               explanation["raw_prediction"], places=3)
        self.assertLess(explanation["additivity_error"], 1e-3)
        sbp = next(item for item in output["prediction"]["results"] if item["target"] == "sbp")
        self.assertEqual(explanation["raw_prediction"], sbp["prediction"])

    def test_log_margin_and_log1p_scales_are_not_mislabelled_original_units(self):
        for target, scale, inverse in (("ast_u_l", "log(U/L)", math.exp), ("ggt_u_l", "log1p(U/L)", math.expm1)):
            with self.subTest(target=target):
                output = dashboard.build_dashboard(DashboardPredictionRequest.model_validate(payload(target)))
                explanation = output["charts"]["explanation"]
                self.assertEqual(explanation["status"], "AVAILABLE")
                self.assertEqual(explanation["scale_label"], scale)
                actual = next(item for item in output["prediction"]["results"] if item["target"] == target)["prediction"]
                self.assertTrue(math.isclose(inverse(explanation["raw_prediction"]), actual, rel_tol=2e-6))
                self.assertNotEqual(explanation["raw_prediction"], actual)
                self.assertEqual(output["charts"]["unit"], "U/L")

    def test_catboost_native_shap_and_response_are_supported(self):
        output = dashboard.build_dashboard(DashboardPredictionRequest.model_validate(payload("alt_u_l")))
        explanation = output["charts"]["explanation"]
        self.assertEqual(output["charts"]["model_family"], ["catboost"])
        self.assertEqual(explanation["status"], "AVAILABLE")
        self.assertEqual(explanation["scale_label"], "U/L")
        self.assertLess(explanation["additivity_error"], 1e-8)
        self.assertEqual(output["charts"]["dose_response"]["status"], "AVAILABLE")
        self.assertEqual(output["charts"]["joint_response"]["status"], "AVAILABLE")

    def test_curve_and_joint_values_equal_direct_actual_model_predictions(self):
        request = DashboardPredictionRequest.model_validate(payload("ast_u_l"))
        output = dashboard.build_dashboard(request)
        charts = output["charts"]
        point = charts["dose_response"]["values"][7]
        raw = request.input.model_dump()
        raw["person"]["pb"] = point["x"]
        standalone = native.predict_person(PersonPredictionRequest.model_validate(raw))
        prediction = next(item for item in standalone["results"] if item["target"] == "ast_u_l")["prediction"]
        self.assertEqual(point["prediction"], prediction)
        ix, iy, joint_prediction = charts["joint_response"]["values"][13]
        raw["person"]["pb"] = charts["joint_response"]["x_values"][ix]
        raw["person"]["cd"] = charts["joint_response"]["y_values"][iy]
        standalone = native.predict_person(PersonPredictionRequest.model_validate(raw))
        prediction = next(item for item in standalone["results"] if item["target"] == "ast_u_l")["prediction"]
        self.assertEqual(joint_prediction, prediction)

    def test_changed_person_changes_predictions_and_contributions(self):
        first = dashboard.build_dashboard(DashboardPredictionRequest.model_validate(payload()))
        changed = payload()
        changed["input"]["person"].update(age=70, bmi=32, gender="female")
        second = dashboard.build_dashboard(DashboardPredictionRequest.model_validate(changed))
        self.assertNotEqual(first["charts"]["explanation"]["raw_prediction"], second["charts"]["explanation"]["raw_prediction"])
        self.assertNotEqual(first["charts"]["explanation"]["items"], second["charts"]["explanation"]["items"])
        self.assertNotEqual(first["charts"]["dose_response"]["values"], second["charts"]["dose_response"]["values"])
        self.assertNotEqual(first["charts"]["joint_response"]["values"], second["charts"]["joint_response"]["values"])

    def test_withheld_target_does_not_bypass_accuracy_guard_for_charts(self):
        with patch.object(dashboard, "_explanation") as explanation, patch.object(dashboard, "_grid") as grid:
            output = dashboard.build_dashboard(DashboardPredictionRequest.model_validate(payload("uacr_mg_g")))
        explanation.assert_not_called()
        grid.assert_not_called()
        self.assertEqual(output["charts"]["status"], "INSUFFICIENT_VALIDATED_ACCURACY")
        self.assertTrue(output["charts"]["reason"])
        self.assertEqual(output["charts"]["explanation"]["items"], [])
        self.assertIsNone(output["charts"]["explanation"]["raw_prediction"])
        self.assertEqual(output["charts"]["dose_response"]["values"], [])
        self.assertEqual(output["charts"]["joint_response"]["values"], [])

    def test_native_explanation_failure_never_returns_fabricated_contributions(self):
        with patch.object(dashboard, "_explanation", side_effect=RuntimeError("test failure")):
            output = dashboard.build_dashboard(DashboardPredictionRequest.model_validate(payload()))
        self.assertEqual(output["charts"]["explanation"]["status"], "UNAVAILABLE")
        self.assertEqual(output["charts"]["explanation"]["items"], [])
        self.assertEqual(output["charts"]["dose_response"]["status"], "AVAILABLE")

    def test_nonlinear_ensemble_explanation_is_not_falsely_combined(self):
        with native._inference_slot():
            original = native._ensure_bundle()
            bundle = {**original, "cards": dict(original["cards"]), "models": dict(original["models"])}
            card = deepcopy(original["cards"]["sbp"])
            card["components"] = [deepcopy(card["components"][0]), deepcopy(card["components"][0])]
            card["components"][0]["weight"] = 0.5
            card["components"][1]["weight"] = 0.5
            card["components"][1]["config"]["target_transform"] = "log1p"
            bundle["cards"]["sbp"] = card
            bundle["models"][("sbp", 1)] = bundle["models"][("sbp", 0)]
            encoded, _ = native._encode(DashboardPredictionRequest.model_validate(payload()).input)
            explanation = dashboard._explanation(bundle, "sbp", encoded)
        self.assertEqual(explanation["status"], "UNAVAILABLE")
        self.assertEqual(explanation["items"], [])

    def test_batch_success_row_input_can_feed_same_real_dashboard(self):
        columns = native.CONTRACT["batch_required_columns"]
        frame = pd.DataFrame([dict(zip(columns, ["93703.0", 45, 1, 25.0, 1.5, 0.4, 1.2]))])
        request = BatchPredictionRequest.model_validate({"file_id": "FILE-12345678",
            "measurements": native.get_prediction_demo()["payload"]["measurements"]})
        with patch.object(native, "_batch_frame", return_value=frame):
            batch = native.predict_batch(request)
        input = batch["records"][0]["input"]
        self.assertEqual(input["person"]["id"], "93703")
        result = dashboard.build_dashboard(DashboardPredictionRequest.model_validate({"input": input, "target": "sbp"}))
        self.assertEqual(result["input"], input)
        expected = next(item for item in batch["records"][0]["results"] if item["target"] == "sbp")["prediction"]
        actual = next(item for item in result["prediction"]["results"] if item["target"] == "sbp")["prediction"]
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
