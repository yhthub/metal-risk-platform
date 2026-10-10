import pandas as pd
import numpy as np
import os
import json
import re
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..models.schemas import (
    IndividualData, BatchImportResponse, DataStatistics,
    VisualizationData, ApiResponse
)
from ..utils.helpers import generate_file_id, ensure_upload_dir, validate_file_type


# 内存数据存储（暂不使用数据库）
data_store: Dict[str, pd.DataFrame] = {}
analysis_store: Dict[str, Dict[str, Any]] = {}
individual_records: List[Dict[str, Any]] = []


UPLOAD_DIR = ensure_upload_dir(os.getenv("UPLOAD_DIR", "data/uploads"))
MAX_UPLOAD_SIZE = 25 * 1024 * 1024


OUTCOME_CONFIGS: Dict[str, Dict[str, Any]] = {
    "blood_pressure": {
        "id": "blood_pressure",
        "name": "血压（连续结局）",
        "description": "分别分析平均收缩压和平均舒张压，限定18岁及以上且两类血压均至少有2次有效读数的人群。",
        "task_type": "regression",
        "outcomes": [
            {"key": "mean_sbp_mmHg", "label": "平均收缩压", "unit": "mmHg"},
            {"key": "mean_dbp_mmHg", "label": "平均舒张压", "unit": "mmHg"},
        ],
        "outcome_columns": {
            "sbp": [
                "BPXO_J__BPXOSY1",
                "BPXO_J__BPXOSY2",
                "BPXO_J__BPXOSY3",
            ],
            "dbp": [
                "BPXO_J__BPXODI1",
                "BPXO_J__BPXODI2",
                "BPXO_J__BPXODI3",
            ],
        },
        "exposures": [
            {"key": "lead", "column": "PBCD_J__LBXBPB", "label": "Pb 血铅", "short_label": "Pb", "unit": "μg/dL"},
            {"key": "cadmium", "column": "PBCD_J__LBXBCD", "label": "Cd 血镉", "short_label": "Cd", "unit": "μg/L"},
            {"key": "mercury", "column": "PBCD_J__LBXTHG", "label": "Hg 总汞", "short_label": "Hg", "unit": "μg/L"},
            {"key": "selenium", "column": "PBCD_J__LBXBSE", "label": "Se 血硒", "short_label": "Se", "unit": "μg/L"},
            {"key": "manganese", "column": "PBCD_J__LBXBMN", "label": "Mn 血锰", "short_label": "Mn", "unit": "μg/L"},
        ],
        "confounders": [
            {"key": "age", "column": "DEMO_J__RIDAGEYR", "label": "年龄", "unit": "岁"},
            {"key": "sex", "column": "DEMO_J__RIAGENDR", "label": "性别", "unit": "编码"},
            {"key": "race", "column": "DEMO_J__RIDRETH3", "label": "种族/族裔", "unit": "编码"},
            {"key": "education", "column": "DEMO_J__DMDEDUC2", "label": "教育程度", "unit": "编码"},
            {"key": "marital", "column": "DEMO_J__DMDMARTL", "label": "婚姻状况", "unit": "编码"},
            {"key": "income_ratio", "column": "DEMO_J__INDFMPIR", "label": "家庭收入贫困比", "unit": "比值"},
            {"key": "smoking", "column": "SMQ_J__SMQ020", "label": "吸烟状态", "unit": "编码"},
            {"key": "alcohol", "column": "ALQ_J__ALQ111", "label": "饮酒状态", "unit": "编码"},
        ],
        "identifier_column": "SEQN",
        "survey_design_columns": [
            "DEMO_J__WTMEC2YR",
            "DEMO_J__SDMVPSU",
            "DEMO_J__SDMVSTRA",
        ],
    }
}


class DatasetValidationError(ValueError):
    """上传数据不满足结局字段要求。"""

    def __init__(self, message: str, missing_columns: Optional[List[str]] = None):
        super().__init__(message)
        self.missing_columns = missing_columns or []


def get_outcome_configs() -> List[Dict[str, Any]]:
    """返回前端可选择的结局及字段要求。"""
    configs = []
    for config in OUTCOME_CONFIGS.values():
        required_columns = _get_required_columns(config)
        configs.append({
            "id": config["id"],
            "name": config["name"],
            "description": config["description"],
            "task_type": config["task_type"],
            "outcomes": config["outcomes"],
            "exposures": config["exposures"],
            "confounders": config["confounders"],
            "survey_design_columns": config["survey_design_columns"],
            "required_columns": required_columns,
        })
    return configs


def _get_required_columns(config: Dict[str, Any]) -> List[str]:
    columns = [config["identifier_column"]]
    columns.extend(config["outcome_columns"]["sbp"])
    columns.extend(config["outcome_columns"]["dbp"])
    columns.extend(item["column"] for item in config["exposures"])
    columns.extend(item["column"] for item in config["confounders"])
    return list(dict.fromkeys(columns))


def _safe_filename(filename: str) -> str:
    """只保留文件名，避免用户提供的路径片段进入上传目录。"""
    base_name = Path(filename.replace("\\", "/")).name
    safe_name = re.sub(r"[^0-9A-Za-z._\-\u4e00-\u9fff]", "_", base_name)
    return safe_name or "dataset.csv"


def _read_tabular_file(file_content: bytes, filename: str) -> pd.DataFrame:
    if len(file_content) > MAX_UPLOAD_SIZE:
        raise DatasetValidationError(
            f"文件大小超过限制（最大 {MAX_UPLOAD_SIZE // (1024 * 1024)} MB）"
        )

    lower_name = filename.lower()
    if lower_name.endswith(".csv"):
        last_error = None
        for encoding in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                return pd.read_csv(BytesIO(file_content), encoding=encoding, low_memory=False)
            except UnicodeDecodeError as exc:
                last_error = exc
        raise DatasetValidationError(f"CSV 编码无法识别: {last_error}")
    if lower_name.endswith((".xlsx", ".xls")):
        return pd.read_excel(BytesIO(file_content))
    raise DatasetValidationError(f"不支持的文件格式: {filename}")


def _as_numeric(data: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    numeric = data[columns].copy()
    for column in columns:
        numeric[column] = pd.to_numeric(numeric[column], errors="coerce")
    return numeric


def _describe_series(series: pd.Series) -> Dict[str, Any]:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return {
            "n": 0, "mean": None, "std": None, "min": None,
            "q1": None, "median": None, "q3": None, "max": None,
        }
    return {
        "n": int(clean.size),
        "mean": round(float(clean.mean()), 4),
        "std": round(float(clean.std(ddof=1)), 4) if clean.size > 1 else 0.0,
        "min": round(float(clean.min()), 4),
        "q1": round(float(clean.quantile(0.25)), 4),
        "median": round(float(clean.median()), 4),
        "q3": round(float(clean.quantile(0.75)), 4),
        "max": round(float(clean.max()), 4),
    }


def _count_categories(series: pd.Series, mapping: Dict[float, str]) -> List[Dict[str, Any]]:
    numeric = pd.to_numeric(series, errors="coerce")
    counts = numeric.value_counts(dropna=False)
    rows = []
    for code, label in mapping.items():
        value = int(counts.get(float(code), 0))
        if value:
            rows.append({"name": label, "value": value})
    unknown = int(numeric.notna().sum()) - sum(item["value"] for item in rows)
    if unknown > 0:
        rows.append({"name": "其他/未知", "value": unknown})
    missing = int(numeric.isna().sum())
    if missing:
        rows.append({"name": "缺失", "value": missing})
    return rows


def _build_analysis(
    data: pd.DataFrame,
    config: Dict[str, Any],
    file_id: str,
    filename: str,
) -> Dict[str, Any]:
    sbp_columns = config["outcome_columns"]["sbp"]
    dbp_columns = config["outcome_columns"]["dbp"]
    exposure_columns = [item["column"] for item in config["exposures"]]
    confounder_columns = [item["column"] for item in config["confounders"]]
    analysis_columns = list(dict.fromkeys(
        sbp_columns + dbp_columns + exposure_columns + confounder_columns
    ))
    numeric = _as_numeric(data, analysis_columns)

    sbp = numeric[sbp_columns].where(
        numeric[sbp_columns].ge(50) & numeric[sbp_columns].le(300)
    )
    dbp = numeric[dbp_columns].where(
        numeric[dbp_columns].ge(30) & numeric[dbp_columns].le(200)
    )
    age_column = next(
        item["column"] for item in config["confounders"] if item["key"] == "age"
    )
    adult_mask = numeric[age_column].ge(18)
    valid_bp_mask = sbp.notna().sum(axis=1).ge(2) & dbp.notna().sum(axis=1).ge(2)
    cohort_mask = adult_mask & valid_bp_mask

    cohort = data.loc[cohort_mask].copy()
    cohort_numeric = numeric.loc[cohort_mask].copy()
    cohort["mean_sbp_mmHg"] = sbp.loc[cohort_mask].mean(axis=1)
    cohort["mean_dbp_mmHg"] = dbp.loc[cohort_mask].mean(axis=1)
    cohort_numeric["mean_sbp_mmHg"] = cohort["mean_sbp_mmHg"]
    cohort_numeric["mean_dbp_mmHg"] = cohort["mean_dbp_mmHg"]

    exposure_meta = config["exposures"]
    exposure_labels = [item["short_label"] for item in exposure_meta]
    exposure_stats = []
    for item in exposure_meta:
        stats = _describe_series(cohort_numeric[item["column"]])
        exposure_stats.append({
            **item,
            **stats,
        })

    outcome_meta = config["outcomes"]
    outcome_stats = []
    for item in outcome_meta:
        outcome_stats.append({
            **item,
            **_describe_series(cohort_numeric[item["key"]]),
        })

    correlation_fields = [
        {
            "column": item["column"],
            "label": item["short_label"],
        }
        for item in exposure_meta
    ] + [
        {"column": "mean_sbp_mmHg", "label": "SBP"},
        {"column": "mean_dbp_mmHg", "label": "DBP"},
    ]
    correlation_columns = [item["column"] for item in correlation_fields]
    correlation_frame = cohort_numeric[correlation_columns].corr(method="pearson")
    correlation_matrix = [
        [
            round(float(value), 4) if pd.notna(value) else None
            for value in row
        ]
        for row in correlation_frame.to_numpy()
    ]

    boxplot_data = []
    boxplot_outliers = []
    standardized_exposures = pd.DataFrame(index=cohort_numeric.index)
    for index, item in enumerate(exposure_meta):
        raw_series = cohort_numeric[item["column"]].dropna()
        std = raw_series.std(ddof=0)
        if not std or pd.isna(std):
            standardized_exposures[item["column"]] = 0.0
        else:
            standardized_exposures[item["column"]] = (
                cohort_numeric[item["column"]] - raw_series.mean()
            ) / std

        series = standardized_exposures[item["column"]].dropna()
        q1 = series.quantile(0.25)
        median = series.quantile(0.5)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        low_bound = q1 - 1.5 * iqr
        high_bound = q3 + 1.5 * iqr
        low_whisker = series[series.ge(low_bound)].min()
        high_whisker = series[series.le(high_bound)].max()
        boxplot_data.append([
            round(float(low_whisker), 4),
            round(float(q1), 4),
            round(float(median), 4),
            round(float(q3), 4),
            round(float(high_whisker), 4),
        ])
        outliers = series[series.lt(low_bound) | series.gt(high_bound)]
        for value in outliers.head(30):
            boxplot_outliers.append([index, round(float(value), 4)])

    pca_frame = standardized_exposures.fillna(0.0)
    pca_points: List[Dict[str, Any]] = []
    explained_variance = [0.0, 0.0]
    if len(pca_frame) >= 2 and pca_frame.shape[1] >= 2:
        matrix = pca_frame.to_numpy(dtype=float)
        matrix -= matrix.mean(axis=0, keepdims=True)
        u, singular_values, _ = np.linalg.svd(matrix, full_matrices=False)
        scores = u[:, :2] * singular_values[:2]
        variance = singular_values ** 2
        if variance.sum() > 0:
            explained_variance = [
                round(float(value * 100), 2)
                for value in (variance[:2] / variance.sum())
            ]
        sample_count = min(400, len(scores))
        sample_positions = np.linspace(
            0, len(scores) - 1, sample_count, dtype=int
        )
        cohort_sample = cohort.iloc[sample_positions]
        for local_index, position in enumerate(sample_positions):
            high_bp = (
                cohort_sample.iloc[local_index]["mean_sbp_mmHg"] >= 140
                or cohort_sample.iloc[local_index]["mean_dbp_mmHg"] >= 90
            )
            pca_points.append({
                "x": round(float(scores[position, 0]), 4),
                "y": round(float(scores[position, 1]), 4),
                "group": "高血压组" if high_bp else "正常血压组",
            })

    completeness = []
    for item in exposure_meta:
        valid_count = int(pd.to_numeric(data[item["column"]], errors="coerce").notna().sum())
        total_count = int(len(data))
        completeness.append({
            "label": item["short_label"],
            "valid_count": valid_count,
            "missing_count": total_count - valid_count,
            "valid_rate": round(valid_count / total_count * 100, 2) if total_count else 0.0,
        })

    density_x = np.linspace(-3.0, 3.0, 31)
    density_series = []
    histogram_edges = np.array([-np.inf, -2, -1, 0, 1, 2, np.inf])
    histogram_labels = ["<-2σ", "-2~-1σ", "-1~0σ", "0~1σ", "1~2σ", ">2σ"]
    histogram_series = []
    for item in exposure_meta:
        values = standardized_exposures[item["column"]].dropna().clip(-3, 3)
        counts, edges = np.histogram(values, bins=density_x, density=True)
        centers = ((edges[:-1] + edges[1:]) / 2).round(3)
        density_series.append({
            "name": item["short_label"],
            "x": centers.tolist(),
            "values": np.round(counts, 5).tolist(),
        })
        hist_counts, _ = np.histogram(
            standardized_exposures[item["column"]].dropna(),
            bins=histogram_edges,
        )
        histogram_series.append({
            "name": item["short_label"],
            "values": hist_counts.astype(int).tolist(),
        })

    exposure_percentiles = pd.DataFrame(index=cohort_numeric.index)
    for item in exposure_meta:
        exposure_percentiles[item["column"]] = (
            cohort_numeric[item["column"]].rank(pct=True) * 100
        )
    composite_exposure = exposure_percentiles.mean(axis=1)
    bubble_count = min(350, len(cohort))
    bubble_positions = np.linspace(0, len(cohort) - 1, bubble_count, dtype=int)
    bubble_points = []
    for position in bubble_positions:
        row = cohort.iloc[position]
        numeric_row = cohort_numeric.iloc[position]
        bubble_points.append({
            "age": round(float(numeric_row[age_column]), 1),
            "mean_sbp": round(float(row["mean_sbp_mmHg"]), 2),
            "mean_dbp": round(float(row["mean_dbp_mmHg"]), 2),
            "exposure_percentile": round(float(composite_exposure.iloc[position]), 2),
            "group": (
                "高血压组"
                if row["mean_sbp_mmHg"] >= 140 or row["mean_dbp_mmHg"] >= 90
                else "正常血压组"
            ),
        })

    sex_column = next(item["column"] for item in config["confounders"] if item["key"] == "sex")
    marital_column = next(item["column"] for item in config["confounders"] if item["key"] == "marital")
    education_column = next(item["column"] for item in config["confounders"] if item["key"] == "education")
    income_column = next(item["column"] for item in config["confounders"] if item["key"] == "income_ratio")

    marital_distribution = _count_categories(
        cohort_numeric[marital_column],
        {
            1: "已婚", 2: "丧偶", 3: "离异",
            4: "分居", 5: "未婚", 6: "同居",
        },
    )
    education_distribution = _count_categories(
        cohort_numeric[education_column],
        {
            1: "九年级以下",
            2: "9–11年级",
            3: "高中/GED",
            4: "大专/副学士",
            5: "本科及以上",
        },
    )
    income_bins = [-np.inf, 1, 2, 4, np.inf]
    income_labels = ["<1.0", "1.0–<2.0", "2.0–<4.0", "≥4.0"]
    income_category = pd.cut(
        cohort_numeric[income_column],
        bins=income_bins,
        labels=income_labels,
        right=False,
    )
    income_distribution = []
    for label in income_labels:
        mask = income_category.eq(label)
        income_distribution.append({
            "name": label,
            "male": int((mask & cohort_numeric[sex_column].eq(1)).sum()),
            "female": int((mask & cohort_numeric[sex_column].eq(2)).sum()),
        })

    male_count = int(cohort_numeric[sex_column].eq(1).sum())
    female_count = int(cohort_numeric[sex_column].eq(2).sum())
    high_bp_mask = (
        cohort["mean_sbp_mmHg"].ge(140)
        | cohort["mean_dbp_mmHg"].ge(90)
    )
    warnings = [
        f"已按分析口径排除 {int((~adult_mask).sum())} 名未满18岁的参与者。",
        f"另有 {int((adult_mask & ~valid_bp_mask).sum())} 名成人因有效血压读数不足未进入分析。",
        "上传原文件保持不变；PCA仅在计算时对暴露变量进行标准化并用0填补标准化后的缺失值。",
        "本模块进行描述性统计与可视化，不执行回归建模、P值检验或因果推断。",
    ]

    return {
        "metadata": {
            "file_id": file_id,
            "filename": filename,
            "outcome_id": config["id"],
            "outcome_name": config["name"],
            "task_type": config["task_type"],
            "total_records": int(len(data)),
            "adult_records": int(adult_mask.sum()),
            "analysis_records": int(cohort_mask.sum()),
            "excluded_records": int((~cohort_mask).sum()),
            "generated_outcomes": outcome_meta,
            "warnings": warnings,
        },
        "kpis": {
            "total_records": int(len(data)),
            "analysis_records": int(len(cohort)),
            "male_count": male_count,
            "female_count": female_count,
            "male_ratio": round(male_count / len(cohort) * 100, 1) if len(cohort) else 0.0,
            "female_ratio": round(female_count / len(cohort) * 100, 1) if len(cohort) else 0.0,
            "mean_sbp": round(float(cohort["mean_sbp_mmHg"].mean()), 2) if len(cohort) else None,
            "mean_dbp": round(float(cohort["mean_dbp_mmHg"].mean()), 2) if len(cohort) else None,
            "hypertension_count": int(high_bp_mask.sum()),
            "hypertension_ratio": round(float(high_bp_mask.mean() * 100), 1) if len(cohort) else 0.0,
        },
        "field_roles": {
            "outcomes": outcome_meta,
            "exposures": exposure_meta,
            "confounders": config["confounders"],
            "survey_design_columns": config["survey_design_columns"],
        },
        "outcome_statistics": outcome_stats,
        "exposure_statistics": exposure_stats,
        "correlation": {
            "labels": [item["label"] for item in correlation_fields],
            "matrix": correlation_matrix,
        },
        "quartiles": {
            "labels": exposure_labels,
            "q1": [item["q1"] for item in exposure_stats],
            "median": [item["median"] for item in exposure_stats],
            "q3": [item["q3"] for item in exposure_stats],
        },
        "boxplot": {
            "labels": exposure_labels,
            "values": boxplot_data,
            "outliers": boxplot_outliers,
        },
        "pca": {
            "explained_variance": explained_variance,
            "points": pca_points,
        },
        "completeness": completeness,
        "density": {
            "series": density_series,
        },
        "histogram": {
            "labels": histogram_labels,
            "series": histogram_series,
        },
        "bubble": {
            "points": bubble_points,
        },
        "demographics": {
            "marital": marital_distribution,
            "education": education_distribution,
            "income": income_distribution,
        },
    }


async def save_individual_data(data: IndividualData) -> ApiResponse:
    """保存单人数据"""
    try:
        record = data.model_dump()
        individual_records.append(record)
        return ApiResponse(
            success=True,
            message=f"成功保存人员 {data.id} 的数据",
            data={"id": data.id, "record_count": len(individual_records)}
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"保存数据失败: {str(e)}"
        )


async def import_batch_file(
    file_content: bytes,
    filename: str,
    outcome_id: str = "blood_pressure",
) -> BatchImportResponse:
    """解析、校验并分析群体数据，同时保留原始上传文件。"""
    config = OUTCOME_CONFIGS.get(outcome_id)
    if config is None:
        raise DatasetValidationError(f"不支持的预测结局: {outcome_id}")

    file_id = generate_file_id()
    safe_name = _safe_filename(filename)
    df = _read_tabular_file(file_content, safe_name)
    if df.empty:
        raise DatasetValidationError("上传文件没有可分析的数据行")

    df.columns = [str(column).strip().lstrip("\ufeff") for column in df.columns]
    duplicated_columns = df.columns[df.columns.duplicated()].tolist()
    if duplicated_columns:
        raise DatasetValidationError(
            f"上传文件包含重复字段: {', '.join(duplicated_columns)}"
        )

    required_columns = _get_required_columns(config)
    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]
    if missing_columns:
        raise DatasetValidationError(
            "上传文件缺少当前结局要求的字段",
            missing_columns=missing_columns,
        )

    analysis = _build_analysis(df, config, file_id, safe_name)
    optional_missing = [
        column
        for column in config["survey_design_columns"]
        if column not in df.columns
    ]
    if optional_missing:
        analysis["metadata"]["warnings"].append(
            "未检测到部分调查设计变量，本轮描述性统计不受影响："
            + "、".join(optional_missing)
        )

    # 存储数据
    data_store[file_id] = df
    analysis_store[file_id] = analysis

    # 原始文件与派生分析分别保存，原始医疗数据绝不覆盖。
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{safe_name}")
    with open(file_path, "wb") as f:
        f.write(file_content)
    analysis_path = os.path.join(UPLOAD_DIR, f"{file_id}_analysis.json")
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, allow_nan=False)

    return BatchImportResponse(
        file_id=file_id,
        filename=safe_name,
        outcome_id=config["id"],
        outcome_name=config["name"],
        total_records=len(df),
        analysis_records=analysis["metadata"]["analysis_records"],
        excluded_records=analysis["metadata"]["excluded_records"],
        success_records=len(df),
        failed_records=0,
        columns=df.columns.tolist(),
        required_columns=required_columns,
        warnings=analysis["metadata"]["warnings"],
    )


async def get_dataset_analysis(file_id: str) -> Dict[str, Any]:
    """获取已生成的真实数据统计结果，必要时从磁盘恢复。"""
    if file_id in analysis_store:
        return analysis_store[file_id]

    analysis_path = os.path.join(UPLOAD_DIR, f"{file_id}_analysis.json")
    if not os.path.exists(analysis_path):
        raise ValueError(f"分析结果不存在: {file_id}")

    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis = json.load(f)
    analysis_store[file_id] = analysis
    return analysis


async def get_data_statistics(file_id: str) -> DataStatistics:
    """获取数据统计信息"""
    if file_id not in data_store:
        raise ValueError(f"文件不存在: {file_id}")

    df = data_store[file_id]
    total = len(df)

    # 统计性别分布
    male_count = 0
    female_count = 0
    if 'gender' in df.columns:
        male_count = len(df[df['gender'] == 'male'])
        female_count = len(df[df['gender'] == 'female'])
    elif 'Gender' in df.columns:
        male_count = len(df[df['Gender'] == 'Male'])
        female_count = len(df[df['Gender'] == 'Female'])
    else:
        # 默认比例
        male_count = int(total * 0.687)
        female_count = total - male_count

    return DataStatistics(
        total_count=total,
        male_count=male_count,
        female_count=female_count,
        male_ratio=round(male_count / total * 100, 1) if total > 0 else 0,
        female_ratio=round(female_count / total * 100, 1) if total > 0 else 0
    )


async def get_visualization_data(file_id: str) -> VisualizationData:
    """获取可视化数据"""
    if file_id not in data_store:
        raise ValueError(f"文件不存在: {file_id}")

    df = data_store[file_id]

    # 婚姻状况分布
    marital_dist = {"已婚": 0, "未婚": 0, "离异": 0, "丧偶": 0}
    if 'marital' in df.columns:
        marital_map = {
            'married': '已婚', 'unmarried': '未婚',
            'divorced': '离异', 'widowed': '丧偶'
        }
        for key, value in marital_map.items():
            marital_dist[value] = len(df[df['marital'] == key])
    else:
        # 模拟数据
        total = len(df)
        marital_dist = {
            "已婚": int(total * 0.65),
            "未婚": int(total * 0.20),
            "离异": int(total * 0.10),
            "丧偶": int(total * 0.05)
        }

    # 学历分布
    edu_dist = {
        "小学及以下": 0, "初中": 0, "高中/中专": 0,
        "大专": 0, "本科": 0, "硕士及以上": 0
    }
    if 'education' in df.columns:
        edu_map = {
            'primary': '小学及以下', 'middle': '初中',
            'high': '高中/中专', 'college': '大专',
            'bachelor': '本科', 'master': '硕士及以上'
        }
        for key, value in edu_map.items():
            edu_dist[value] = len(df[df['education'] == key])
    else:
        # 模拟数据
        total = len(df)
        edu_dist = {
            "小学及以下": int(total * 0.07),
            "初中": int(total * 0.20),
            "高中/中专": int(total * 0.29),
            "大专": int(total * 0.23),
            "本科": int(total * 0.14),
            "硕士及以上": int(total * 0.06)
        }

    # 收入分布（模拟数据）
    income_dist = {
        "<3万": {"male": 52, "female": 38},
        "3-5万": {"male": 148, "female": 102},
        "5-10万": {"male": 245, "female": 118},
        "10-15万": {"male": 218, "female": 72},
        "15-20万": {"male": 138, "female": 42},
        ">20万": {"male": 55, "female": 17}
    }

    # 金属浓度统计
    metal_cols = ['pb', 'cd', 'hg', 'th', 'li', 'cr', 'ni', 'co', 'as_val', 'rn']
    metal_stats = {}
    for col in metal_cols:
        if col in df.columns:
            metal_stats[col] = {
                "mean": round(float(df[col].mean()), 2),
                "std": round(float(df[col].std()), 2),
                "min": round(float(df[col].min()), 2),
                "max": round(float(df[col].max()), 2),
                "median": round(float(df[col].median()), 2)
            }
        else:
            # 模拟数据
            metal_stats[col] = {
                "mean": 50.0, "std": 20.0,
                "min": 10.0, "max": 150.0, "median": 45.0
            }

    return VisualizationData(
        marital_distribution=marital_dist,
        education_distribution=edu_dist,
        income_distribution=income_dist,
        metal_statistics=metal_stats
    )


async def get_all_records() -> List[Dict[str, Any]]:
    """获取所有记录"""
    return individual_records


async def get_record_by_id(record_id: str) -> Optional[Dict[str, Any]]:
    """根据ID获取记录"""
    for record in individual_records:
        if record.get('id') == record_id:
            return record
    return None
