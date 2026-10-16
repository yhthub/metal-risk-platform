"""Frozen real-public-data demo for the risk page's one-click batch workflow.

This endpoint imports a small verified asset, not saved predictions. The UI
then invokes the normal batch and dashboard APIs. It does not depend on the
user's E drive after deployment, never downloads data and never fits a model.
"""
from __future__ import annotations

import csv
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
from io import StringIO
import json
import math
from pathlib import Path

from .data_service import OUTCOME_CONFIGS, _get_required_columns, import_batch_file


ASSET_DIR = Path(__file__).resolve().parents[1] / "data"
MANIFEST_NAME = "nhanes_risk_demo.manifest.json"
SAMPLE_NAME = "NHANES_2017-2018_risk_demo_20.csv"
DEMO_ID = "nhanes_2017_2018_risk_demo_20"
SAMPLE_SHA256 = "8c88eb746f06a24e6e2b642dd16bf0879af2d236a57c4a7d460b1a03049fa84f"
SOURCE_PINS = {
    "NHANES_2017-2018_public_adults_300.csv": (300, "eb3f0fa05f721fc95f96c30abcefb9c34751c6fa7a83648841e696a697bb2751"),
    "BMX_J.csv": (8704, "631901c63b0b01fcbe7d2c96cc63379228f5cefc8d29286006b5f038a0f49921"),
    "BMX_J.xpt": (8704, "8d675e42d8826ac98714b2c3dd4c5138a5e353fb4424f7eff5e6db4a01ce838a"),
}
MEASUREMENTS = {
    "pb": {"sample": "whole_blood", "unit": "ug/dL", "analyte": "lead", "confirmed": True},
    "cd": {"sample": "whole_blood", "unit": "ug/L", "analyte": "cadmium", "confirmed": True},
    "hg": {"sample": "whole_blood", "unit": "ug/L", "analyte": "total_mercury", "confirmed": True},
}


class RiskDemoError(ValueError):
    """A frozen demo asset is absent, altered or semantically incompatible."""


def _asset_file(name):
    root = Path(ASSET_DIR).absolute()
    source = root / name
    if (root.is_symlink() or root.resolve() != root or source.is_symlink()
            or source.resolve().parent != root or not source.is_file()):
        raise RiskDemoError("固定公开体验样本文件不完整或路径无效，请核对本地部署资产。")
    return source


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate manifest field")
        result[key] = value
    return result


def _public_id(value):
    try:
        number = Decimal(value.strip())
        if not number.is_finite() or number <= 0 or number > 10**12 or number != number.to_integral_value():
            raise InvalidOperation
        return int(number)
    except (InvalidOperation, ValueError, TypeError, OverflowError) as exc:
        raise RiskDemoError("公开体验样本包含无效参与者编号，未导入。") from exc


def _verify_semantics(rows, columns, config):
    ids = [_public_id(row["SEQN"]) for row in rows]
    if len(ids) != len(set(ids)) or ids != sorted(ids):
        raise RiskDemoError("公开体验样本编号重复或选择顺序改变，未导入。")
    codes = {"DEMO_J__RIAGENDR": {1, 2}, "DEMO_J__RIDRETH3": {1, 2, 3, 4, 6, 7},
             "DEMO_J__DMDEDUC2": {1, 2, 3, 4, 5}, "DEMO_J__DMDMARTL": {1, 2, 3, 4, 5, 6},
             "SMQ_J__SMQ020": {1, 2}, "ALQ_J__ALQ111": {1, 2}}
    for row in rows:
        try:
            numbers = {column: float(row[column]) for column in columns}
        except (ValueError, TypeError, OverflowError) as exc:
            raise RiskDemoError("公开体验样本包含缺失或非法数值，未导入。") from exc
        if any(not math.isfinite(value) or value == 5.397605346934028e-79 for value in numbers.values()):
            raise RiskDemoError("公开体验样本包含非有限值或已知转存异常标记，未导入。")
        age = numbers["DEMO_J__RIDAGEYR"]
        if not age.is_integer() or not 18 <= age <= 80 or numbers["BMX_J__BMXBMI"] <= 0:
            raise RiskDemoError("公开体验样本不满足成人年龄和已测正BMI条件，未导入。")
        if any(numbers[column] not in allowed for column, allowed in codes.items()):
            raise RiskDemoError("公开体验样本分类编码不符合声明的NHANES字段口径，未导入。")
        if any(numbers[item["column"]] < 0 for item in config["exposures"]) or numbers["DEMO_J__INDFMPIR"] < 0:
            raise RiskDemoError("公开体验样本存在非法浓度或收入比，未导入。")
        systolic, diastolic = config["outcome_columns"]["sbp"], config["outcome_columns"]["dbp"]
        if (any(not 50 <= numbers[column] <= 300 for column in systolic)
                or any(not 30 <= numbers[column] <= 200 for column in diastolic)
                or any(numbers[s] <= numbers[d] for s, d in zip(systolic, diastolic))):
            raise RiskDemoError("公开体验样本不符合既有血压读数导入规范，未导入。")
        if (numbers["DEMO_J__WTMEC2YR"] <= 0 or numbers["DEMO_J__SDMVPSU"] not in {1, 2}
                or numbers["DEMO_J__SDMVSTRA"] <= 0 or not numbers["DEMO_J__SDMVSTRA"].is_integer()):
            raise RiskDemoError("公开体验样本调查设计字段无效，未导入。")
    return ids


def _load_risk_demo():
    try:
        manifest_path = _asset_file(MANIFEST_NAME)
        if manifest_path.stat().st_size > 128 * 1024:
            raise RiskDemoError("公开体验样本来源说明超过大小限制。")
        manifest = json.loads(manifest_path.read_text("utf-8"), object_pairs_hook=_unique_json,
                              parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
        config = OUTCOME_CONFIGS["blood_pressure"]
        columns = _get_required_columns(config) + config["survey_design_columns"] + ["BMX_J__BMXBMI"]
        if (manifest.get("id") != DEMO_ID or manifest.get("cycle") != "2017-2018" or manifest.get("rows") != 20
                or manifest.get("outcome_id") != "blood_pressure" or manifest.get("sample_filename") != SAMPLE_NAME
                or manifest.get("columns") != columns
                or manifest.get("required_columns") != _get_required_columns(config) + ["BMX_J__BMXBMI"]
                or manifest.get("source_kind") != "verified_local_public_nhanes_same_cycle_one_to_one_join"
                or manifest.get("measurement_contract") != MEASUREMENTS):
            raise RiskDemoError("公开体验样本与冻结的字段、周期或测量口径不一致，未导入。")
        sources = manifest.get("source_files", [])
        if len(sources) != len(SOURCE_PINS) or {item.get("file") for item in sources} != set(SOURCE_PINS):
            raise RiskDemoError("公开体验样本来源组件不完整，未导入。")
        for item in sources:
            expected_rows, expected_hash = SOURCE_PINS[item["file"]]
            if item.get("cycle") != "2017-2018" or item.get("rows") != expected_rows or item.get("sha256") != expected_hash:
                raise RiskDemoError("公开体验样本来源校验值或周期改变，未导入。")
        join = manifest.get("join", {})
        if (join.get("validation") != "one_to_one" or join.get("same_cycle") is not True
                or join.get("selected_records") != 20 or join.get("selected_bmi_equal_raw_xpt") is not True
                or join.get("original_23_cell_strings_preserved") is not True
                or any(join.get(key) is not False for key in ("imputation", "winsorization", "unit_conversion"))):
            raise RiskDemoError("公开体验样本的关联或缺失处理说明不符合冻结规范，未导入。")
        if (manifest.get("preparation", {}).get("prediction_results_precomputed") is not False
                or not manifest.get("limitations")):
            raise RiskDemoError("公开体验样本缺少实时计算和使用边界说明，未导入。")
        source = _asset_file(SAMPLE_NAME)
        if source.stat().st_size > 256 * 1024:
            raise RiskDemoError("公开体验样本超过大小限制。")
        content = source.read_bytes()
        if (manifest.get("sample_sha256") != SAMPLE_SHA256 or hashlib.sha256(content).hexdigest() != SAMPLE_SHA256
                or len(content) != manifest.get("sample_bytes")):
            raise RiskDemoError("公开体验样本完整性校验失败，未导入任何记录。")
        parsed = list(csv.reader(StringIO(content.decode("utf-8-sig"), newline="")))
        if (not parsed or parsed[0] != columns or len(parsed) != 21
                or any(len(row) != len(columns) for row in parsed[1:])):
            raise RiskDemoError("公开体验样本字段或记录数不符，未导入。")
        rows = [dict(zip(columns, row)) for row in parsed[1:]]
        ids = _verify_semantics(rows, columns, config)
        if ids != join.get("selected_public_seqn"):
            raise RiskDemoError("公开体验样本的固定参与者编号与来源说明不一致，未导入。")
        return manifest, content
    except RiskDemoError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise RiskDemoError("固定公开体验样本暂不可用，请核对随网站部署的数据和来源说明。") from exc


def get_risk_demo_metadata():
    manifest, _ = _load_risk_demo()
    return deepcopy(manifest)


async def import_risk_demo():
    manifest, content = _load_risk_demo()
    # Only this allowlisted, code-pinned public asset may carry a server-verified
    # confirmed measurement context; user uploads still require confirmation.
    imported = await import_batch_file(content, SAMPLE_NAME, "blood_pressure", provenance=manifest)
    return {"import_result": imported.model_dump(), "provenance": deepcopy(manifest),
            "measurements": deepcopy(MEASUREMENTS)}
