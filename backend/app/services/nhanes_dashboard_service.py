"""Lightweight native-model charts for the original risk dashboard.

Only inference on the user's selected person is performed. SHAP explains the
native raw margin; nonlinear links/target inverses are never applied to each
individual contribution. Conditional-response grids are model explorations,
not causal dose-response estimates or clinical safe/reference ranges.

Official APIs verified on 2026-10-16:
https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.Booster.predict
https://catboost.ai/docs/en/concepts/python-reference_catboostregressor_get_feature_importance
"""
from __future__ import annotations

from copy import deepcopy
import importlib
import json
import math
import time

from ..models.prediction_schemas import DashboardPredictionRequest
from . import nhanes_prediction_service as native


GROUPS = {
    "age_years": "年龄", "bmi_kg_m2": "BMI", "blood_lead_ug_dl": "全血铅",
    "blood_cadmium_ug_l": "全血镉", "blood_total_mercury_ug_l": "全血总汞",
    "sex_female": "性别", "education": "教育程度", "marital": "婚姻状况",
    "smoking": "吸烟情况", "alcohol_any_past_year": "过去一年饮酒",
    "other_unprovided_model_features": "其他未提供资料的模型缺失分支",
}
RESPONSE_NOTE = (
    "固定该对象其余输入，仅改变图示全血浓度后重新运行保存模型；"
    "此为模型条件预测响应，不是暴露的因果效应或疾病概率。"
    "横轴仅为探索范围，不是临床阈值或安全范围；训练资料对该范围的覆盖未经核定。"
)
UNAVAILABLE = "当前基本资料条件下该结局验证表现未优于常数参考，暂不显示预测解释或条件响应。"


def _feature_group(feature):
    if feature in GROUPS:
        return feature
    if feature in native.BASIC_FEATURES:
        prefix = feature.split("__", 1)[0]
        if prefix in {"education", "marital", "smoking"}:
            return prefix
    return "other_unprovided_model_features"


def _native_scale(model, config, unit):
    """Return the actual raw-margin link and target-transform semantics."""
    family = config["family"]
    transform = config["target_transform"]
    if family == "xgboost":
        objective = json.loads(model.save_config())["learner"]["objective"]["name"]
        if objective in {"reg:tweedie", "reg:gamma", "count:poisson"}:
            link = "exp"
        elif objective in {"reg:squarederror", "reg:absoluteerror", "reg:pseudohubererror",
                           "reg:squaredlogerror", "reg:quantileerror"}:
            link = "identity"
        else:
            raise ValueError("Unsupported native explanation objective")
    elif family == "catboost":
        objective = str(model.get_all_params().get("loss_function", ""))
        if objective not in {"MAE", "RMSE"}:
            raise ValueError("Unsupported CatBoost explanation objective")
        link = "identity"
    else:
        raise ValueError("Unsupported model family")
    if link == "identity" and transform == "identity":
        label = unit
        note = "原生加和解释与该连续指标同单位；贡献仅说明模型计算，不是因果效应。"
    elif link == "identity" and transform == "log1p":
        label = "log1p(" + unit + ")"
        note = "贡献和基线位于log1p目标尺度；整体原始分值经expm1后才是指标估计，不能逐项expm1贡献。"
    elif link == "exp" and transform == "identity":
        label = "log(" + unit + ")"
        note = "原生目标使用对数链接；贡献解释原始log-margin，整体分值经exp后才是指标估计，不能逐项指数化贡献。"
    else:
        label = "原始模型分值（非指标原单位）"
        note = "原始分值需依次经过模型链接函数和目标反变换；各项贡献不能独立作非线性单位换算。"
    return {"scale_label": label, "native_link": link, "target_transform": transform,
            "objective": objective, "note": note}


def _unavailable_explanation(reason):
    return {"status": "UNAVAILABLE", "reason": reason, "scale_label": "", "base_value": None,
            "raw_prediction": None, "additivity_error": None, "items": [], "note": "不使用随机数、比例摊分或输入浓度代替SHAP。"}


def _explanation(bundle, target, encoded):
    np, pd = bundle["np"], bundle["pd"]
    card = bundle["cards"][target]
    frame = pd.DataFrame([encoded], columns=native.BASIC_FEATURES, dtype="float32")
    pieces, scales = [], []
    with bundle["threadpools"].threadpool_limits(limits=native.THREADS):
        for index, component in enumerate(card["components"]):
            model = bundle["models"][(target, index)]
            scale = _native_scale(model, component["config"], card["unit"])
            scales.append(scale)
            native_frame = frame.reindex(columns=component["features"])
            if component["config"]["family"] == "xgboost":
                matrix = bundle["xgb"].DMatrix(native_frame, missing=np.nan, nthread=native.THREADS,
                                              enable_categorical=False)
                shap = np.asarray(model.predict(matrix, pred_contribs=True, approx_contribs=False), dtype="float64")
                raw = float(model.predict(matrix, output_margin=True)[0])
            else:
                cb = importlib.import_module("catboost")
                shap = np.asarray(model.get_feature_importance(cb.Pool(native_frame), type="ShapValues",
                    thread_count=native.THREADS, verbose=False), dtype="float64")
                raw = float(model.predict(native_frame, prediction_type="RawFormulaVal",
                    thread_count=native.THREADS, task_type="CPU")[0])
            if shap.shape != (1, len(component["features"]) + 1) or not np.isfinite(shap).all() or not math.isfinite(raw):
                raise ValueError("Native SHAP shape or finiteness verification failed")
            if not np.isclose(shap.sum(), raw, rtol=1e-5, atol=1e-4):
                raise ValueError("Native SHAP additivity check failed")
            pieces.append((component, shap[0], raw))
    # Linear identity components can be combined exactly after aligning feature
    # names. Inverse-transforming a weighted raw margin would be wrong for a
    # nonlinear ensemble, even when all component labels happen to match.
    if len(pieces) > 1 and any(scale["native_link"] != "identity" or scale["target_transform"] != "identity"
                               for scale in scales):
        return _unavailable_explanation("当前组合模型包含非线性或不同尺度的分值，不能合成统一的加和SHAP解释。")
    grouped = {key: 0.0 for key in GROUPS}
    counts = dict.fromkeys(GROUPS, 0)
    base, raw_prediction = 0.0, 0.0
    for component, shap, raw in pieces:
        weight = component["weight"]
        base += weight * float(shap[-1])
        raw_prediction += weight * raw
        for feature, value in zip(component["features"], shap[:-1]):
            group = _feature_group(feature)
            grouped[group] += weight * float(value)
            counts[group] += 1
    items = [{"feature": group, "label_zh": GROUPS[group], "value": grouped[group],
              "native_feature_count": counts[group],
              "input_state": "not_provided" if group == "other_unprovided_model_features" else
                  ("unknown" if (encoded.get(group) is None and group not in {"education", "marital", "smoking"})
                   or (group in {"education", "marital", "smoking"} and
                       all(encoded.get(feature) is None for feature in native.BASIC_FEATURES if feature.startswith(group + "__")))
                   else "observed")}
             for group in GROUPS if counts[group] > 0]
    items.sort(key=lambda item: (-abs(item["value"]), item["feature"]))
    error = abs(base + sum(item["value"] for item in items) - raw_prediction)
    if not math.isclose(base + sum(item["value"] for item in items), raw_prediction, rel_tol=1e-5, abs_tol=1e-4):
        raise ValueError("Grouped SHAP does not preserve additivity")
    scale = scales[0]
    return {"status": "AVAILABLE", "reason": None, "scale_label": scale["scale_label"],
            "native_link": scale["native_link"], "target_transform": scale["target_transform"],
            "base_value": base, "raw_prediction": raw_prediction, "additivity_error": error, "items": items,
            "note": scale["note"] + "教育、婚姻和吸烟按各自独热编码贡献求和；所有额外缺失字段归为“其他未提供资料”，不丢弃贡献。"}


def _native_importance(bundle, target):
    """Supplementary static model structure, not personal dynamic attribution."""
    card = bundle["cards"][target]
    if len(card["components"]) != 1:
        return {"status": "UNAVAILABLE", "reason": "组合模型的不同重要性口径不合并为单一分数。", "items": []}
    component = card["components"][0]
    model = bundle["models"][(target, 0)]
    with bundle["threadpools"].threadpool_limits(limits=native.THREADS):
        if component["config"]["family"] == "xgboost":
            method = "native_gain"
            score = model.get_score(importance_type="gain")
            values = [float(score.get(feature, 0.0)) for feature in component["features"]]
        else:
            method = "native_PredictionValuesChange"
            values = [float(value) for value in model.get_feature_importance(type="PredictionValuesChange",
                thread_count=native.THREADS, verbose=False)]
    if len(values) != len(component["features"]) or any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Invalid native feature importance")
    total = sum(values)
    grouped = dict.fromkeys(GROUPS, 0.0)
    for feature, value in zip(component["features"], values):
        grouped[_feature_group(feature)] += value
    return {"status": "AVAILABLE", "method": method, "scope": "saved_model_structure_not_person_effect",
            "scale_label": "模型内部归一化相对重要性（%）", "dynamic_by_person": False,
            "items": sorted([{"feature": key, "label_zh": GROUPS[key], "value": value / total * 100 if total else 0.0}
                             for key, value in grouped.items()], key=lambda item: -item["value"]),
            "note": "这是已保存模型的训练结构重要性，随所选结局变化，不应随同一个人的输入数值变化；不是因果作用比例，也不跨算法比较。"}


def _grid(bundle, target, encoded):
    np, pd = bundle["np"], bundle["pd"]
    current_pb = float(encoded["blood_lead_ug_dl"])
    current_cd = float(encoded["blood_cadmium_ug_l"])
    pb_max, cd_max = max(current_pb * 2, 5.0), max(current_cd * 2, 2.0)
    # Keep hypothetical inputs representable just as real inputs are. No
    # overflows or nonzero-to-zero conversions are handed to the native model.
    if not math.isfinite(pb_max) or not math.isfinite(cd_max) or max(pb_max, cd_max) > 3.4028234663852886e38:
        reason = "当前输入使探索网格超出模型数值范围；请核对实际测量值及单位。"
        return ({"status": "UNAVAILABLE", "reason": reason, "feature": "blood_lead_ug_dl", "unit": "ug/dL",
                 "values": [], "current_value": current_pb, "note": RESPONSE_NOTE},
                {"status": "UNAVAILABLE", "reason": reason, "x_feature": "blood_lead_ug_dl",
                 "y_feature": "blood_cadmium_ug_l", "x_unit": "ug/dL", "y_unit": "ug/L",
                 "x_values": [], "y_values": [], "values": [], "note": RESPONSE_NOTE})
    dose_x = np.linspace(0.0, pb_max, 16)
    joint_x, joint_y = np.linspace(0.0, pb_max, 5), np.linspace(0.0, cd_max, 5)
    rows = [{**encoded, "blood_lead_ug_dl": float(value)} for value in dose_x]
    # Row major order is explicit in the returned [x_index,y_index,prediction]
    # triples, so a heatmap never transposes lead and cadmium inadvertently.
    rows.extend({**encoded, "blood_lead_ug_dl": float(x), "blood_cadmium_ug_l": float(y)}
                for x in joint_x for y in joint_y)
    frame = pd.DataFrame(rows, columns=native.BASIC_FEATURES, dtype="float32")
    predictions = native._target_predictions(bundle, target, frame)
    dose = {"status": "AVAILABLE", "reason": None, "feature": "blood_lead_ug_dl", "unit": "ug/dL",
            "values": [{"x": float(value), "prediction": float(predictions[index])} for index, value in enumerate(dose_x)],
            "current_value": current_pb, "note": RESPONSE_NOTE}
    joint = {"status": "AVAILABLE", "reason": None, "x_feature": "blood_lead_ug_dl", "y_feature": "blood_cadmium_ug_l",
             "x_unit": "ug/dL", "y_unit": "ug/L", "x_values": [float(value) for value in joint_x],
             "y_values": [float(value) for value in joint_y],
             "values": [[ix, iy, float(predictions[16 + ix * 5 + iy])] for ix in range(5) for iy in range(5)],
             "note": RESPONSE_NOTE}
    return dose, joint


def _withheld(card):
    reason = UNAVAILABLE
    explanation = _unavailable_explanation(reason)
    explanation["status"] = "INSUFFICIENT_VALIDATED_ACCURACY"
    return {"target": card["target"], "label_zh": card["label_zh"], "unit": card["unit"],
            "status": "INSUFFICIENT_VALIDATED_ACCURACY", "reason": reason,
            "model_family": sorted({component["config"]["family"] for component in card["components"]}),
            "explanation": explanation,
            "native_importance": {"status": "INSUFFICIENT_VALIDATED_ACCURACY", "reason": reason, "items": []},
            "dose_response": {"status": "INSUFFICIENT_VALIDATED_ACCURACY", "reason": reason,
                              "feature": "blood_lead_ug_dl", "unit": "ug/dL", "values": [],
                              "current_value": None, "note": RESPONSE_NOTE},
            "joint_response": {"status": "INSUFFICIENT_VALIDATED_ACCURACY", "reason": reason,
                "x_feature": "blood_lead_ug_dl", "y_feature": "blood_cadmium_ug_l", "x_unit": "ug/dL", "y_unit": "ug/L",
                "x_values": [], "y_values": [], "values": [], "note": RESPONSE_NOTE}}


def build_dashboard(payload: DashboardPredictionRequest):
    """One person selected from a single form OR a successfully predicted batch row."""
    started = time.perf_counter()
    with native._inference_slot():
        # Validate original specimen/units before model availability checks.
        native._encode(payload.input)
        bundle = native._ensure_bundle()
        prediction = native._person_prediction_in_slot(payload.input, bundle)
        card = bundle["cards"][payload.target]
        if card["metrics_original_units"]["selection"]["R2"] <= 0:
            charts = _withheld(card)
        else:
            encoded = prediction["encoded_input"]
            try:
                explanation = _explanation(bundle, payload.target, encoded)
            except Exception:
                explanation = _unavailable_explanation("原生SHAP计算或加和校验未通过，暂不显示解释图；指标估计仍来自保存模型。")
            try:
                importance = _native_importance(bundle, payload.target)
            except Exception:
                importance = {"status": "UNAVAILABLE", "reason": "原生模型结构重要性暂不可用。", "items": []}
            try:
                dose, joint = _grid(bundle, payload.target, encoded)
            except Exception:
                reason = "真实模型条件网格计算未通过，暂不显示响应图。"
                dose = {"status": "UNAVAILABLE", "reason": reason, "feature": "blood_lead_ug_dl",
                        "unit": "ug/dL", "values": [], "current_value": encoded["blood_lead_ug_dl"], "note": RESPONSE_NOTE}
                joint = {"status": "UNAVAILABLE", "reason": reason, "x_feature": "blood_lead_ug_dl",
                         "y_feature": "blood_cadmium_ug_l", "x_unit": "ug/dL", "y_unit": "ug/L",
                         "x_values": [], "y_values": [], "values": [], "note": RESPONSE_NOTE}
            charts = {"target": payload.target, "label_zh": card["label_zh"], "unit": card["unit"],
                      "status": "AVAILABLE", "reason": None,
                      "model_family": sorted({component["config"]["family"] for component in card["components"]}),
                      "explanation": explanation, "native_importance": importance,
                      "dose_response": dose, "joint_response": joint}
        return {"input": payload.input.model_dump(), "prediction": prediction, "charts": charts,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 1)}
