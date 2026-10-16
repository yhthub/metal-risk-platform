"""CPU-only inference bridge for the frozen NHANES v5 basic-input package.

No training, threshold-based diagnosis, web downloads or model substitution is
available here. A missing dependency, invalid saved model or SHA256 mismatch
disables inference rather than returning prototype numbers. Models are loaded
once per verified artifact generation; every request rechecks the hashes.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import struct
import threading
import time

from pydantic import ValidationError

from ..models.prediction_schemas import (
    BatchPredictionRequest, BloodMeasurements, PersonPredictionRequest,
)


RUN_ID = "nhanes_12outcomes_targeted_20261016_005"
MODEL_VERSION = "NHANES-v5-basic"
THREADS = 4
TARGETS = (
    "sbp", "dbp", "serum_creatinine_mg_dl", "bun_mg_dl", "uric_acid_mg_dl",
    "uacr_mg_g", "hba1c_percent", "total_cholesterol_mg_dl",
    "hdl_cholesterol_mg_dl", "alt_u_l", "ast_u_l", "ggt_u_l",
)
BASIC_FEATURES = (
    "age_years", "bmi_kg_m2", "blood_lead_ug_dl", "blood_cadmium_ug_l",
    "blood_total_mercury_ug_l", "sex_female", "alcohol_any_past_year",
    "education__less_than_grade9", "education__grade9_11", "education__high_school_ged",
    "education__some_college_aa", "education__college_or_above", "education__unknown",
    "marital__married", "marital__widowed", "marital__divorced", "marital__separated",
    "marital__never_married", "marital__living_with_partner", "marital__unknown",
    "smoking__less_than_100_lifetime", "smoking__former", "smoking__current", "smoking__unknown",
)
METALS = {
    "pb": ("blood_lead_ug_dl", "lead", "ug/dL"),
    "cd": ("blood_cadmium_ug_l", "cadmium", "ug/L"),
    "hg": ("blood_total_mercury_ug_l", "total_mercury", "ug/L"),
}
SCOPE = "估计当前连续检查指标，不是未来发病概率、临床诊断或重金属因果效应。"
WARNINGS = [
    "模型来自美国 NHANES 2009–2018 成人资料；不能视为已在中国职业暴露人群中验证。",
    "低于或等于常数参考表现的结局暂不显示估计值；其余估计也不能替代实际检查。",
    "误差范围是历史残差的探索性参考范围，不是正常值范围，不保证个体覆盖率。",
    "可选资料未知保留缺失；历史测试误差不自动代表当前个人的误差。",
]
CONTRACT = {
    "profile": "basic", "required_person_fields": ["age", "gender", "gender_confirmed", "bmi", "pb", "cd", "hg"],
    "bounds": {"age": {"minimum": 18, "maximum": 80, "integer": True, "note": "NHANES年龄80岁顶码；超过80岁不直接套用"},
               "bmi": {"exclusive_minimum": 0}, "pb": {"minimum": 0},
               "cd": {"minimum": 0}, "hg": {"minimum": 0}},
    "gender": ["male", "female"], "gender_confirmed_required": True,
    "measurement_contract": {key: {"sample": "whole_blood", "analyte": value[1], "unit": value[2],
        "accepted_units": ["ug/dL", "ug/L", "ng/mL"], "confirmed": True} for key, value in METALS.items()},
    "covariates": {
        "education": ["less_than_grade9", "grade9_11", "high_school_ged", "some_college_aa", "college_or_above"],
        "marital": ["married", "widowed", "divorced", "separated", "never_married", "living_with_partner"],
        "smoking": ["less_than_100_lifetime", "former", "current"],
        "alcohol_any_past_year": [True, False], "unknown_value": None,
    },
    "batch_required_columns": ["SEQN", "DEMO_J__RIDAGEYR", "DEMO_J__RIAGENDR", "BMX_J__BMXBMI",
                               "PBCD_J__LBXBPB", "PBCD_J__LBXBCD", "PBCD_J__LBXTHG"],
    "batch_measurement_contract": {
        "pb": {"column": "PBCD_J__LBXBPB", "stored_unit": "ug/dL", "accepted_units": ["ug/dL"]},
        "cd": {"column": "PBCD_J__LBXBCD", "stored_unit": "ug/L", "accepted_units": ["ug/L", "ng/mL"]},
        "hg": {"column": "PBCD_J__LBXTHG", "stored_unit": "ug/L", "accepted_units": ["ug/L", "ng/mL"]},
    },
    "batch_max_records_per_request": 500,
}

_capacity = threading.BoundedSemaphore(1)
_bundle_cache = None


class PredictionError(ValueError):
    def __init__(self, message, status_code=422):
        super().__init__(message)
        self.status_code = status_code


@contextmanager
def _inference_slot():
    # Acquire inside the worker. Cancelling an HTTP request cannot release the
    # native inference slot before its worker has really finished.
    if not _capacity.acquire(blocking=False):
        raise PredictionError("另一项模型核验或预测正在进行，请稍后重试。", 429)
    try:
        yield
    finally:
        _capacity.release()


def _root():
    configured = os.getenv("NHANES_MODEL_ROOT")
    root = Path(configured) if configured else Path(__file__).resolve().parents[3] / "models" / "nhanes_v5"
    if not root.is_absolute() or root.is_symlink() or root.resolve() != root.absolute() or not root.is_dir():
        raise PredictionError("本地 NHANES 模型目录不可用，请配置完整的 v5 模型包。", 503)
    return root


def _safe_file(root, relative):
    if not isinstance(relative, str) or "\\" in relative:
        raise PredictionError("模型文件路径无效，已停止预测。", 503)
    rel = Path(relative)
    if rel.is_absolute() or not rel.parts or any(part in {"..", "."} for part in rel.parts):
        raise PredictionError("模型文件路径无效，已停止预测。", 503)
    source = root / rel
    if any((root / Path(*rel.parts[:index])).is_symlink() for index in range(1, len(rel.parts) + 1)):
        raise PredictionError("模型文件不允许重定向，已停止预测。", 503)
    if source.resolve().parent != (root / rel.parent).absolute() or not source.is_file():
        raise PredictionError("模型文件不完整，已停止预测。", 503)
    return source


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def _read_json(path, maximum=4 * 1024 * 1024):
    if path.stat().st_size > maximum:
        raise ValueError("Artifact metadata too large")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_json,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def _digest(path):
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Saved model exceeds local inference limit")
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Invalid numeric artifact: " + name)
    return float(value)


def _ensure_bundle():
    global _bundle_cache
    try:
        root = _root()
        integrity = _read_json(_safe_file(root, "integrity.json"))
        if integrity.get("run_id") != RUN_ID or not isinstance(integrity.get("files"), dict):
            raise ValueError("Wrong integrity generation")
        pins = integrity["files"]

        def verified(relative):
            expected = pins.get(relative)
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                raise ValueError("Missing integrity entry")
            source = _safe_file(root, relative)
            if _digest(source) != expected:
                raise ValueError("SHA256 mismatch")
            return source, expected

        registry_path, registry_hash = verified("registry.json")
        registry = _read_json(registry_path)
        if registry.get("run_id") != RUN_ID or registry.get("status") != "COMPLETE":
            raise ValueError("Wrong registry generation")
        registered = [item for item in registry["results"] if item["profile"] == "basic"]
        if len(registered) != 12 or {item["target"] for item in registered} != set(TARGETS):
            raise ValueError("Twelve unique basic targets required")
        cards, sources, hashes = {}, {}, [registry_hash]
        for target in TARGETS:
            directory = "basic/" + target
            path, card_hash = verified(directory + "/MODEL_CARD.json")
            card = _read_json(path)
            if (card.get("run_id") != RUN_ID or card.get("target") != target or card.get("profile") != "basic"
                    or len(card.get("input_features", [])) != 24 or set(card["input_features"]) != set(BASIC_FEATURES)):
                raise ValueError("Frozen basic feature contract mismatch")
            if not card.get("components") or len(card["components"]) > 4:
                raise ValueError("Unsupported saved component count")
            _finite(card["metrics_original_units"]["selection"]["R2"], "selection R2")
            for metric in ("MAE", "RMSE", "R2", "n"):
                _finite(card["metrics_original_units"]["test"][metric], "test " + metric)
            radius = _finite(card["reference_interval"]["radius_original_units"], "residual radius")
            if radius < 0:
                raise ValueError("Negative residual radius")
            weights = []
            for index, component in enumerate(card["components"]):
                name = component["model_file"]
                if not isinstance(name, str) or Path(name).name != name:
                    raise ValueError("Invalid component filename")
                source, component_hash = verified(directory + "/" + name)
                if component_hash != component.get("sha256"):
                    raise ValueError("Component and model card checksums differ")
                features = component["features"]
                if (not features or len(features) != len(set(features)) or
                        any(not isinstance(feature, str) or not feature for feature in features)):
                    raise ValueError("Invalid component feature contract")
                if not card.get("input_mask_to_basic") and features != card["input_features"]:
                    raise ValueError("Unexpected basic model feature contract")
                if card.get("input_mask_to_basic") and not set(BASIC_FEATURES) <= set(features):
                    raise ValueError("Masked baseline lacks required basic features")
                weight = _finite(component["weight"], "component weight")
                if weight < 0:
                    raise ValueError("Negative component weight")
                weights.append(weight)
                if component["config"].get("family") not in {"xgboost", "catboost"}:
                    raise ValueError("Unsupported model family")
                if component["config"].get("target_transform") not in {"identity", "log1p"}:
                    raise ValueError("Unsupported target transform")
                hashes.append(component_hash)
                sources[(target, index)] = source
            if not math.isclose(sum(weights), 1.0, abs_tol=1e-8):
                raise ValueError("Component weights must sum to one")
            hashes.append(card_hash)
            cards[target] = card
        fingerprint = (str(root), tuple(hashes))
        if _bundle_cache is not None and _bundle_cache["fingerprint"] == fingerprint:
            return _bundle_cache

        # The runtime is optional; importing the website never imports native ML
        # libraries. Only successful verification loads actual saved models.
        np = importlib.import_module("numpy")
        pd = importlib.import_module("pandas")
        threadpools = importlib.import_module("threadpoolctl")
        xgb = importlib.import_module("xgboost")
        families = {component["config"]["family"] for card in cards.values() for component in card["components"]}
        cb = importlib.import_module("catboost") if "catboost" in families else None
        loaded = {}
        with threadpools.threadpool_limits(limits=THREADS):
            for target, card in cards.items():
                for index, component in enumerate(card["components"]):
                    if component["config"]["family"] == "xgboost":
                        model = xgb.Booster(params={"device": "cpu", "nthread": THREADS})
                        model.load_model(str(sources[(target, index)]))
                        model.set_param({"device": "cpu", "nthread": THREADS})
                        feature_names = model.feature_names
                    else:
                        model = cb.CatBoostRegressor(task_type="CPU", thread_count=THREADS, allow_writing_files=False)
                        model.load_model(str(sources[(target, index)]), format="cbm")
                        feature_names = list(model.feature_names_)
                    if feature_names != component["features"]:
                        raise ValueError("Saved native feature order mismatch")
                    loaded[(target, index)] = model
        _bundle_cache = {"fingerprint": fingerprint, "cards": cards, "models": loaded, "np": np,
                         "pd": pd, "xgb": xgb, "threadpools": threadpools,
                         "versions": {"xgboost": xgb.__version__, "catboost": cb.__version__ if cb else None}}
        return _bundle_cache
    except PredictionError:
        raise
    except (ImportError, ModuleNotFoundError) as exc:
        raise PredictionError("本地模型推理依赖尚未安装，请使用网站专属 Python 环境。", 503) from exc
    except Exception as exc:
        raise PredictionError("模型包完整性、版本或加载校验未通过，已停止预测，请核验本地 v5 资产。", 503) from exc


def _normal_unit(value):
    return value.replace("μ", "u").replace("µ", "u").strip()


def _check_metadata(measurements):
    metadata = measurements.model_dump() if isinstance(measurements, BloodMeasurements) else measurements
    for key, (_, analyte, _) in METALS.items():
        item = metadata.get(key, {})
        if (item.get("sample") != "whole_blood" or item.get("confirmed") is not True
                or item.get("analyte") != analyte or _normal_unit(item.get("unit", "")) not in {"ug/dL", "ug/L", "ng/mL"}):
            raise PredictionError(f"{key} 必须是已确认的全血 {analyte}，单位须为 μg/dL、μg/L 或等价的 ng/mL；不可混用尿样、血清或未明确汞分析物。")
    return metadata


def _check_batch_metadata(measurements):
    """NHANES J column names also freeze the stored numerical unit.

    Unlike a person's explicitly supplied measurement, a fixed J source column
    cannot be relabelled into another numerical unit by changing a selector.
    Cd/Hg ng/mL is allowed only because its numbers equal ug/L exactly.
    """
    metadata = _check_metadata(measurements)
    allowed = {key: set(item["accepted_units"]) for key, item in CONTRACT["batch_measurement_contract"].items()}
    for key, units in allowed.items():
        if _normal_unit(metadata[key]["unit"]) not in units:
            expected = "μg/dL" if key == "pb" else "μg/L（或数值相同的ng/mL）"
            raise PredictionError(f"固定NHANES J字段的 {key} 数值单位必须为 {expected}；不能只改样本说明就对原CSV数值换算。")
    return metadata


def _encode(payload):
    metadata = _check_metadata(payload.measurements)
    person, covariates = payload.person, payload.covariates
    values = dict.fromkeys(BASIC_FEATURES, None)
    values.update(age_years=float(person.age), bmi_kg_m2=person.bmi, sex_female=float(person.gender == "female"))
    audit = []
    for metal, (field, analyte, target_unit) in METALS.items():
        item = metadata[metal]
        original = getattr(person, metal)
        source_unit = _normal_unit(item["unit"])
        # 1 ng/mL = 1 ug/L; only explicit mass/volume units for the SAME
        # confirmed whole-blood analyte can be converted.
        source_in_ug_l = {"ug/L": 1.0, "ng/mL": 1.0, "ug/dL": 10.0}[source_unit]
        factor = source_in_ug_l / (10.0 if target_unit == "ug/dL" else 1.0)
        converted = original * factor
        if not math.isfinite(converted) or (original != 0 and converted == 0):
            raise PredictionError(f"{metal} 单位换算后不是有限数值。")
        values[field] = converted
        audit.append({"field": metal, "original_value": original, "original_unit": item["unit"],
                      "sample": "whole_blood", "analyte": analyte, "normalized_value": converted,
                      "normalized_unit": target_unit, "conversion_factor": factor,
                      "conversion": "identity" if source_unit == target_unit else "same-specimen mass-per-volume conversion"})
    for group in ("education", "marital", "smoking"):
        category = getattr(covariates, group)
        if category is not None:
            for feature in BASIC_FEATURES:
                if feature.startswith(group + "__"):
                    values[feature] = float(feature == group + "__" + category)
    if covariates.alcohol_any_past_year is not None:
        values["alcohol_any_past_year"] = float(covariates.alcohol_any_past_year)
    # Native saved models consume float32. A finite JSON scalar may still
    # overflow that representation and must not silently become +/- infinity.
    for value in values.values():
        if value is None:
            continue
        try:
            represented = struct.unpack("!f", struct.pack("!f", value))[0]
        except (OverflowError, struct.error) as exc:
            raise PredictionError("输入数值超过模型可表示范围，请核对小数点和单位。") from exc
        if not math.isfinite(represented) or (value != 0 and represented == 0):
            raise PredictionError("输入数值超出模型浮点精度范围，请核对小数点和单位；非零值不会自动置零。")
    return values, audit


def _target_predictions(bundle, target, frame):
    """Predict only one target; caller owns the one-job inference slot."""
    np = bundle["np"]
    card = bundle["cards"][target]
    # Accuracy guard is determined exclusively from selection data,
    # never loosened because a demonstration needs twelve numbers.
    if card["metrics_original_units"]["selection"]["R2"] <= 0:
        return None
    with bundle["threadpools"].threadpool_limits(limits=THREADS):
        combined = np.zeros(len(frame), dtype="float64")
        for index, component in enumerate(card["components"]):
            native_frame = frame.reindex(columns=component["features"])
            model = bundle["models"][(target, index)]
            if component["config"]["family"] == "xgboost":
                matrix = bundle["xgb"].DMatrix(native_frame, nthread=THREADS, missing=np.nan, enable_categorical=False)
                pred = model.predict(matrix)
            else:
                pred = model.predict(native_frame, thread_count=THREADS, task_type="CPU")
            pred = np.asarray(pred, dtype="float64")
            if component["config"]["target_transform"] == "log1p":
                with np.errstate(over="raise", invalid="raise"):
                    pred = np.expm1(pred)
            if pred.shape != (len(frame),) or not np.isfinite(pred).all():
                raise PredictionError("保存模型输出非法数值，已停止预测。", 503)
            combined += component["weight"] * pred
        if not np.isfinite(combined).all():
            raise PredictionError("模型组合输出非法数值，已停止预测。", 503)
        return combined


def _predictions(bundle, rows):
    frame = bundle["pd"].DataFrame(rows, columns=BASIC_FEATURES, dtype="float32")
    return {target: _target_predictions(bundle, target, frame) for target in TARGETS}


def _result_items(bundle, predictions, index, encoded):
    result = []
    for target in TARGETS:
        card = bundle["cards"][target]
        prediction = None if predictions[target] is None else float(predictions[target][index])
        interval = None
        if prediction is not None:
            reference = card["reference_interval"]
            radius = reference["radius_original_units"]
            interval = {"lower": prediction - radius, "upper": prediction + radius,
                        "kind": "exploratory_residual_range_not_clinical_reference",
                        "nominal_calibration_level": 0.9, "guaranteed_coverage": False,
                        "heldout_empirical_coverage": reference["test_empirical_coverage"]}
        result.append({"target": target, "label_zh": card["label_zh"], "unit": card["unit"],
                       "prediction": prediction,
                       "status": "EXPLORATORY_ESTIMATE" if prediction is not None else "INSUFFICIENT_VALIDATED_ACCURACY",
                       "reason": None if prediction is not None else "当前基本资料条件下验证表现未优于常数参考，暂不显示估计值，请以实际检查为准。",
                       "reference_interval": interval,
                       "test_metrics": {key: card["metrics_original_units"]["test"][key] for key in ("MAE", "RMSE", "R2", "n")},
                       "selection_R2": card["metrics_original_units"]["selection"]["R2"],
                       "missing_input_fields": [feature for feature in card["input_features"] if encoded.get(feature) is None],
                       "model_family": sorted({item["config"]["family"] for item in card["components"]}),
                       "candidate_id": card["candidate_id"]})
    return result


def _provenance():
    return {"source": "CDC/NCHS NHANES public adult survey", "data_years": "2009–2018",
            "heldout_years": "2017–2018", "heldout_is_new_blind_validation": False,
            "input_profile": "24 frozen basic encoded fields", "maximum_cpu_threads": THREADS,
            "concurrent_inference_jobs": 1, "training_performed": False,
            "clinical_validation": False, "model_asset_integrity": "SHA256 verified",
            "calibration_note": "历史2015标签曾被既往模型使用；探索性残差范围不作个体覆盖率保证。"}


def get_prediction_status():
    status = {"ready": False, "model_version": MODEL_VERSION, "run_id": RUN_ID, "profile": "basic",
              "target_count": 12, "estimate_target_count": 0, "withheld_target_count": 12,
              "contract": deepcopy(CONTRACT), "scope": SCOPE}
    try:
        with _inference_slot():
            bundle = _ensure_bundle()
            count = sum(card["metrics_original_units"]["selection"]["R2"] > 0 for card in bundle["cards"].values())
            status.update(ready=True, estimate_target_count=count, withheld_target_count=12 - count,
                          runtime=bundle["versions"], reason=None)
    except PredictionError as exc:
        status["reason"] = str(exc)
        status["error_status"] = exc.status_code
    return status


def get_prediction_demo():
    return {"is_demo": True, "notice": "合成填表示例，不是真实患者、NHANES参与者或治疗建议；点击预测时才运行真实模型。",
            "payload": {
                "person": {"id": "DEMO-SYNTHETIC-001", "age": 45, "gender": "male", "gender_confirmed": True,
                           "bmi": 25.0, "pb": 1.5, "cd": 0.4, "hg": 1.2},
                "measurements": {key: {"sample": "whole_blood", "unit": value[2], "analyte": value[1], "confirmed": True}
                                 for key, value in METALS.items()},
                "covariates": {"education": "high_school_ged", "marital": "married",
                               "smoking": "less_than_100_lifetime", "alcohol_any_past_year": False}}}


def predict_person(payload: PersonPredictionRequest):
    with _inference_slot():
        return _person_prediction_in_slot(payload)


def _person_prediction_in_slot(payload: PersonPredictionRequest, bundle=None):
    """Shared by predict/dashboard; caller MUST already own _inference_slot."""
    started = time.perf_counter()
    encoded, audit = _encode(payload)
    bundle = _ensure_bundle() if bundle is None else bundle
    predictions = _predictions(bundle, [encoded])
    warnings = list(WARNINGS)
    unknown = [key for key in ("education", "marital", "smoking", "alcohol_any_past_year")
               if getattr(payload.covariates, key) is None]
    if unknown:
        warnings.append("以下可选资料未知，保留缺失而非补零：" + "、".join(unknown))
    if payload.person.age == 80:
        warnings.append("年龄80对应NHANES的80岁及以上顶码，不能解释为精确高龄效应。")
    return {"model_version": MODEL_VERSION, "run_id": RUN_ID, "profile": "basic",
            "person_id": payload.person.id, "status": "ESTIMATES_NOT_DIAGNOSES", "scope": SCOPE,
            "results": _result_items(bundle, predictions, 0, encoded), "warnings": warnings,
            "measurement_audit": audit, "encoded_input": encoded, "provenance": _provenance(),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1)}


def _batch_frame(file_id):
    from . import data_service
    if not re.fullmatch(r"FILE-[0-9a-f]{8}", file_id):
        raise PredictionError("无效的已导入文件编号。")
    with data_service._cache_lock:
        frame = data_service.data_store.get(file_id)
        if frame is not None:
            return frame.copy(deep=True)
    # Restore only a genuine previously imported file; never accept an arbitrary
    # caller-supplied filesystem path or follow a symlink out of uploads.
    root = Path(data_service.UPLOAD_DIR).absolute()
    if root.is_symlink() or root.resolve() != root:
        raise PredictionError("群体文件存储路径校验失败。", 503)
    analysis = _safe_uploaded_file(root, file_id + "_analysis.json")
    if analysis is None:
        raise PredictionError("找不到已导入数据，请先重新导入群体文件。", 404)
    paths = [path for path in root.glob(file_id + "_*") if path.suffix.lower() in {".csv", ".xlsx"}]
    if len(paths) != 1:
        raise PredictionError("已导入源文件不唯一或不存在，请重新导入。", 404)
    path = _safe_uploaded_file(root, paths[0].name)
    if path is None or path.stat().st_size > data_service.MAX_UPLOAD_SIZE:
        raise PredictionError("已导入源文件不可恢复或超过大小限制。", 413)
    try:
        return data_service._read_tabular_file(path.read_bytes(), path.name)
    except data_service.DatasetValidationError as exc:
        raise PredictionError(str(exc), exc.status_code) from exc


def _safe_uploaded_file(root, name):
    path = root / name
    if path.is_symlink() or path.resolve().parent != root or not path.is_file():
        return None
    return path


def _nhanes_code(row, name, mapping):
    value = row.get(name)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return mapping.get(number) if math.isfinite(number) else None


def _participant_id(value):
    """SEQN is an integer identity: '93703.0' and '93703' are the same person."""
    try:
        number = Decimal(str(value).strip())
        if not number.is_finite() or number <= 0 or number > 10**12 or number != number.to_integral_value():
            raise InvalidOperation
        return str(int(number))
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise PredictionError("SEQN 必须是完整的正整数参与者编号，不能使用空值或非整数编号。") from exc


def _batch_payload(row, identifier, measurements):
    # Exact fields are the system's existing NHANES 2017–2018 columns. The
    # legacy shorthand metal columns have incompatible units and are refused.
    gender = _nhanes_code(row, "DEMO_J__RIAGENDR", {1: "male", 2: "female"})
    try:
        age = float(row["DEMO_J__RIDAGEYR"])
        if not math.isfinite(age) or not age.is_integer():
            raise ValueError("年龄缺失或不是整数")
        numbers = {key: float(row[column]) for key, column in {
            "bmi": "BMX_J__BMXBMI", "pb": "PBCD_J__LBXBPB",
            "cd": "PBCD_J__LBXBCD", "hg": "PBCD_J__LBXTHG"}.items()}
    except (TypeError, ValueError, OverflowError) as exc:
        raise PredictionError("必需的年龄、BMI或三项全血金属存在缺测或非法数值。") from exc
    covariates = {
        "education": _nhanes_code(row, "DEMO_J__DMDEDUC2", {1: "less_than_grade9", 2: "grade9_11",
                     3: "high_school_ged", 4: "some_college_aa", 5: "college_or_above"}),
        "marital": _nhanes_code(row, "DEMO_J__DMDMARTL", {1: "married", 2: "widowed", 3: "divorced",
                   4: "separated", 5: "never_married", 6: "living_with_partner"}),
        "smoking": None, "alcohol_any_past_year": None,
    }
    lifetime = _nhanes_code(row, "SMQ_J__SMQ020", {1: "at_least_100", 2: "less_than_100"})
    if lifetime == "less_than_100":
        covariates["smoking"] = "less_than_100_lifetime"
    elif lifetime == "at_least_100":
        covariates["smoking"] = _nhanes_code(row, "SMQ_J__SMQ040", {1: "current", 2: "current", 3: "former"})
    # ALQ111 is lifetime drinking, not past-year drinking. It cannot fill the
    # training feature; absent exact past-year information deliberately stays NA.
    try:
        return PersonPredictionRequest.model_validate({"person": {"id": identifier, "age": int(age), "gender": gender,
            "gender_confirmed": True, **numbers}, "measurements": measurements, "covariates": covariates})
    except ValidationError as exc:
        raise PredictionError("该行不满足成人18–80岁、明确性别、正BMI及非负有限全血金属的输入条件。") from exc


def predict_batch(payload: BatchPredictionRequest):
    with _inference_slot():
        _check_batch_metadata(payload.measurements)
        frame = _batch_frame(payload.file_id)
        missing = [column for column in CONTRACT["batch_required_columns"] if column not in frame.columns]
        if missing:
            raise PredictionError("已导入数据缺少模型必需字段（不能猜测或补零）：" + "、".join(missing))
        if not frame.columns.is_unique:
            raise PredictionError("数据存在重复列名，不能安全映射模型字段。")
        ids = frame["SEQN"].map(_participant_id)
        if ids.isna().any() or ids.eq("").any() or ids.duplicated().any():
            raise PredictionError("SEQN 必须完整且唯一；请清洗缺失或重复的参与者编号。")
        total = len(frame)
        if payload.offset >= total:
            raise PredictionError("请求行偏移超出已导入数据范围。")
        bundle = _ensure_bundle()
        page = frame.iloc[payload.offset:payload.offset + payload.limit]
        measurements = payload.measurements.model_dump()
        records, encoded_rows, accepted = [], [], []
        for position, (_, row) in enumerate(page.iterrows(), start=payload.offset):
            identifier = str(ids.iloc[position])
            try:
                person_payload = _batch_payload(row, identifier, measurements)
                encoded, audit = _encode(person_payload)
                accepted.append((len(records), encoded))
                encoded_rows.append(encoded)
                records.append({"row_number": position + 1, "person_id": identifier, "status": "ESTIMATES_NOT_DIAGNOSES",
                                "measurement_audit": audit, "input": person_payload.model_dump()})
            except PredictionError as exc:
                records.append({"row_number": position + 1, "person_id": identifier, "status": "INPUT_NOT_ELIGIBLE",
                                "reason": str(exc), "results": None})
        predictions = _predictions(bundle, encoded_rows) if encoded_rows else None
        for index, (record_index, encoded) in enumerate(accepted):
            records[record_index]["results"] = _result_items(bundle, predictions, index, encoded)
        summary = []
        for target in TARGETS:
            card = bundle["cards"][target]
            values = predictions[target] if predictions is not None else None
            summary.append({"target": target, "label_zh": card["label_zh"], "unit": card["unit"],
                            "estimated_count": len(values) if values is not None else 0,
                            "mean_prediction": float(values.mean()) if values is not None else None,
                            "withheld_count": len(accepted) if values is None else 0})
        return {"model_version": MODEL_VERSION, "run_id": RUN_ID, "profile": "basic", "file_id": payload.file_id,
                "status": "ESTIMATES_NOT_DIAGNOSES", "scope": SCOPE,
                "total_records": total, "offset": payload.offset, "limit": payload.limit,
                "processed_records": len(accepted), "skipped_records": len(page) - len(accepted),
                "has_more": payload.offset + len(page) < total, "records": records, "summary": summary,
                "warnings": list(WARNINGS) + ["仅映射明确的NHANES字段；终生饮酒ALQ111不等于过去一年饮酒，保留未知。",
                    "汇总只涵盖本批次中具备模型必需资料的记录，不代表全体人群；不计算疾病概率或高危名单。"],
                "provenance": _provenance()}
