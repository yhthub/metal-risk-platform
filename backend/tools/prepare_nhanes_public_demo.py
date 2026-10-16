"""Rebuild a bounded public-data demo from the user's five original CSV exports.

Mechanical transformation only: retain original selected cell strings, prefix
column names, one-to-one join by public SEQN and filter a deterministic subset.
Never writes back to sources and never imputes, winsorizes or recodes cells.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
from app.services.data_service import OUTCOME_CONFIGS, _get_required_columns  # noqa: E402

MODULES = ("DEMO_J", "BPXO_J", "PBCD_J", "SMQ_J", "ALQ_J")
MARKER = 5.397605346934028e-79
VALID_CODES = {
    "DEMO_J__RIAGENDR": [1, 2],
    "DEMO_J__RIDRETH3": [1, 2, 3, 4, 6, 7],
    "DEMO_J__DMDEDUC2": [1, 2, 3, 4, 5],
    "DEMO_J__DMDMARTL": [1, 2, 3, 4, 5, 6],
    "SMQ_J__SMQ020": [1, 2],
    "ALQ_J__ALQ111": [1, 2],
}
SOURCE_LINKS = [
    {"label": "NHANES 2017–2018 人口学与调查设计", "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.htm"},
    {"label": "NHANES 2017–2018 振荡式血压方法比较研究", "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/BPXO_J.htm"},
    {"label": "NHANES 2017–2018 血液铅、镉、汞、硒与锰", "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/PBCD_J.htm"},
    {"label": "NHANES 2017–2018 吸烟问卷", "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/SMQ_J.htm"},
    {"label": "NHANES 2017–2018 饮酒问卷", "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/ALQ_J.htm"},
]


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_demo(source_dir: Path, output_dir: Path, size: int = 300) -> dict:
    config = OUTCOME_CONFIGS["blood_pressure"]
    columns = _get_required_columns(config) + config["survey_design_columns"]
    sources = []
    frames = {}
    for module in MODULES:
        source = source_dir / f"{module}.csv"
        payload = source.read_bytes()
        data = pd.read_csv(source, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        if "SEQN" not in data.columns:
            raise ValueError(f"{source.name} lacks public SEQN")
        key = pd.to_numeric(data["SEQN"], errors="coerce")
        valid_key = key.notna() & np.isfinite(key) & (key > 0) & key.eq(np.floor(key))
        if not valid_key.all() or key.duplicated().any():
            raise ValueError(f"{source.name} has invalid or duplicate public keys; no guessed de-duplication")
        selected = [column.split("__", 1)[1] for column in columns if column.startswith(module + "__")]
        missing = set(selected) - set(data.columns)
        if missing:
            raise ValueError(f"{source.name} lacks allowlisted fields: {sorted(missing)}")
        subset = data[["SEQN"] + selected].copy()
        subset["_public_key"] = key.astype("int64")
        if module != "DEMO_J":
            subset = subset.drop(columns="SEQN")
        subset = subset.rename(columns={column: f"{module}__{column}" for column in selected})
        frames[module] = subset
        sources.append({"file": source.name, "sha256": sha256(payload), "rows": len(data),
                        "allowlisted_source_columns": ["SEQN"] + selected})
    data = frames["DEMO_J"]
    for module in MODULES[1:]:
        data = data.merge(frames[module], on="_public_key", how="left", validate="one_to_one", sort=False)
    data = data.fillna("")
    numeric = data[columns].apply(pd.to_numeric, errors="coerce")
    steps = []
    mask = pd.Series(True, index=data.index)
    def apply(stage: str, condition: pd.Series):
        nonlocal mask
        before = int(mask.sum())
        mask &= condition
        after = int(mask.sum())
        steps.append({"stage": stage, "before": before, "after": after, "removed": before - after})
    apply("adult_age_at_least_18", numeric["DEMO_J__RIDAGEYR"].ge(18))
    apply("all_23_allowlisted_fields_present_and_finite", numeric.notna().all(axis=1) & np.isfinite(numeric).all(axis=1))
    apply("exclude_unverified_tiny_export_marker_without_recoding", ~numeric.eq(MARKER).any(axis=1))
    for kind, bounds in (("sbp", (50, 300)), ("dbp", (30, 200))):
        # Existing backend admission ranges, not invented clinical risk thresholds.
        valid = numeric[config["outcome_columns"][kind]].apply(lambda series: series.between(*bounds)).all(axis=1)
        apply(f"all_three_{kind}_readings_within_existing_analysis_bounds", valid)
    paired = pd.Series(True, index=data.index)
    for systolic, diastolic in zip(config["outcome_columns"]["sbp"], config["outcome_columns"]["dbp"]):
        paired &= numeric[systolic].gt(numeric[diastolic])
    apply("all_three_pairs_sbp_above_dbp", paired)
    valid_codes = pd.Series(True, index=data.index)
    for column, allowed in VALID_CODES.items():
        valid_codes &= numeric[column].isin(allowed)
    apply("official_known_categorical_codes_only", valid_codes)
    exposure_columns = [field["column"] for field in config["exposures"]]
    apply("nonnegative_concentrations_and_income_ratio", numeric[exposure_columns + ["DEMO_J__INDFMPIR"]].ge(0).all(axis=1))
    valid_design = (numeric["DEMO_J__WTMEC2YR"].gt(0) & numeric["DEMO_J__SDMVPSU"].isin([1, 2]) &
                    numeric["DEMO_J__SDMVSTRA"].gt(0) & numeric["DEMO_J__SDMVSTRA"].eq(np.floor(numeric["DEMO_J__SDMVSTRA"])))
    apply("present_positive_survey_design_fields", valid_design)
    eligible = data.loc[mask].sort_values("_public_key", kind="stable")
    if len(eligible) < size:
        raise ValueError(f"Only {len(eligible)} eligible public records, cannot fabricate requested {size}")
    chosen = eligible.head(size)[columns].copy()
    payload = chosen.to_csv(index=False, lineterminator="\r\n").encode("utf-8-sig")
    manifest = {
        "id": f"nhanes_2017_2018_public_adults_{size}",
        "title": "NHANES 2017–2018 公开成人数据体验",
        "cycle": "2017–2018", "outcome_id": "blood_pressure", "rows": size,
        "columns": columns, "required_columns": _get_required_columns(config),
        "eligible_records": len(eligible), "joined_records": len(data),
        "source_kind": "local_csv_exports_of_public_nhanes_components",
        "source_files": sources, "source_links": SOURCE_LINKS,
        "sample_filename": f"NHANES_2017-2018_public_adults_{size}.csv",
        "sample_sha256": sha256(payload), "sample_bytes": len(payload),
        "sample_matrix_sha256": sha256(json.dumps(chosen.values.tolist(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
        "selection": {"sort": "public numeric SEQN ascending; retain DEMO source SEQN string in output",
                      "limit": size, "steps": steps, "valid_categorical_codes": VALID_CODES,
                      "imputation": False, "winsorization": False, "value_recoding": False,
                      "allowlisted_columns_only": True},
        "limitations": [
            "真实公开调查记录的固定完整病例子集，不是模拟数据，也不是职业暴露监测人群。",
            "按公开 SEQN 升序选取，非随机代表性抽样；不能据此推断美国人群发生率或职业人群风险。",
            "当前图表为未加权描述性统计；虽保留调查设计变量，但未执行复杂抽样加权推断。",
            "使用本地原始组件 CSV 转存值，未新增本地插补、缩尾或医学单位换算；保留官方发布值，可能含官方 LLOD/√2 检测限替代值，未逐格对照官方 XPT。",
            "含 5.397605346934028e-79 转存异常值的所需字段记录被排除，不解释为零或低于检出限。",
            "年龄 80 为官方公开数据的 80 岁及以上截顶编码；公开 SEQN 不是个人身份信息。",
            "教育与婚姻字段的官方适用年龄为 20 岁及以上，因此这个完整字段子集实际均为 20 岁及以上；INDFMPIR=5 表示 5 及以上截顶，而非精确比值 5。",
            "SMQ020 指终生累计吸烟至少 100 支；ALQ111 指终生曾喝过至少 1 杯酒，不等同于当前吸烟或当前饮酒状态。",
            "此子集用于体验系统的数据流程与可视化，不是已经训练或临床验证的预测模型。",
        ],
        "rebuild": {"script": "backend/tools/prepare_nhanes_public_demo.py",
                    "source_pattern": "csv/{DEMO_J,BPXO_J,PBCD_J,SMQ_J,ALQ_J}.csv",
                    "source_files_written": False},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / manifest["sample_filename"]).write_bytes(payload)
    (output_dir / "nhanes_public_demo.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=BACKEND_ROOT / "app" / "data")
    parser.add_argument("--size", type=int, default=300)
    args = parser.parse_args()
    if not 1 <= args.size <= 500:
        parser.error("Demo must remain bounded to 1–500 public records")
    built = build_demo(args.source_dir.resolve(), args.output_dir.resolve(), args.size)
    print(json.dumps({"rows": built["rows"], "eligible_records": built["eligible_records"], "sample_bytes": built["sample_bytes"], "sample_sha256": built["sample_sha256"], "selection_steps": built["selection"]["steps"]}, ensure_ascii=False))
