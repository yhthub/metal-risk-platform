"""Raw-file demographics, separate from model eligibility and predictions.

These are unweighted counts of every uploaded record, not an adult/BP subset,
display preview, risk classification or survey-population estimate. Only the
same named NHANES fields/codes already accepted by the importer are decoded.
"""
from __future__ import annotations

import math
from statistics import mean

import pandas as pd


SEX = ((1, "male", "男性"), (2, "female", "女性"))
MARITAL = ((1, "married", "已婚"), (2, "widowed", "丧偶"),
           (3, "divorced", "离异"), (4, "separated", "分居"),
           (5, "never_married", "未婚"), (6, "living_with_partner", "同居"))
EDUCATION = ((1, "less_than_grade9", "九年级以下"), (2, "grade9_11", "9–11年级"),
             (3, "high_school_ged", "高中/GED"), (4, "some_college_aa", "部分大学教育 / AA学位"),
             (5, "college_or_above", "本科及以上"))
AGE_BANDS = (("0_17", "0–17岁", 0, 17), ("18_39", "18–39岁", 18, 39),
             ("40_59", "40–59岁", 40, 59), ("60_80", "60–80岁", 60, 80))
UNKNOWN = ("unknown", "缺失或未明确")


def _missing(value):
    return value is None or (isinstance(value, str) and not value.strip()) or bool(pd.isna(value))


def _number(value):
    if isinstance(value, bool) or _missing(value):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _item(key, label, count, total):
    return {"key": key, "label": label, "count": count,
            "percent": count / total * 100 if total else 0.0}


def _column(frame, column):
    return frame[column].tolist() if column in frame.columns else [None] * len(frame)


def _median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    # statistics.median adds the middle pair before dividing, which can
    # overflow even when both source values and their true median are finite.
    return ordered[middle] if len(ordered) % 2 else mean(ordered[middle - 1:middle + 1])


def _categorical(frame, column, definitions):
    raw = _column(frame, column)
    numbers = [_number(value) for value in raw]
    total = len(raw)
    categories = [_item(key, label, sum(value == code for value in numbers), total)
                  for code, key, label in definitions]
    valid = sum(item["count"] for item in categories)
    unknown = total - valid
    categories.append(_item(*UNKNOWN, unknown, total))
    return {"source_columns": [column], "available": column in frame.columns,
            "valid_count": valid, "missing_count": sum(_missing(value) for value in raw),
            "unknown_count": unknown, "categories": categories}


def _continuous(frame, column, validator, age_bands=False):
    raw = _column(frame, column)
    numbers = [_number(value) for value in raw]
    values = [value for value in numbers if value is not None and validator(value)]
    total, valid = len(raw), len(values)
    missing = sum(_missing(value) for value in raw)
    bands = ([_item(key, label, sum(low <= value <= high for value in values), total)
              for key, label, low, high in AGE_BANDS] if age_bands else [])
    if age_bands:
        bands.append(_item(*UNKNOWN, total - valid, total))
    return {"source_columns": [column], "available": column in frame.columns,
            "valid_count": valid, "missing_count": missing, "invalid_count": total - valid - missing,
            "unknown_count": total - valid, "mean": mean(values) if values else None,
            "median": _median(values) if values else None, "min": min(values) if values else None,
            "max": max(values) if values else None, "bands": bands}


def _smoking(frame):
    lifetime_column, current_column = "SMQ_J__SMQ020", "SMQ_J__SMQ040"
    lifetime = _column(frame, lifetime_column)
    current = _column(frame, current_column)
    keys = []
    for history, frequency in zip(lifetime, current):
        code, frequency_code = _number(history), _number(frequency)
        keys.append("less_than_100_lifetime" if code == 2 else
                    "current" if code == 1 and frequency_code in {1, 2} else
                    "former" if code == 1 and frequency_code == 3 else "unknown")
    definitions = (("less_than_100_lifetime", "终生吸烟不足100支"),
                   ("former", "既往吸烟"), ("current", "目前吸烟"), UNKNOWN)
    return {"source_columns": [lifetime_column, current_column],
            "available": lifetime_column in frame.columns, "valid_count": len(keys) - keys.count("unknown"),
            "missing_count": sum(_missing(history) or (_number(history) == 1 and _missing(frequency))
                                 for history, frequency in zip(lifetime, current)),
            "unknown_count": keys.count("unknown"),
            "categories": [_item(key, label, keys.count(key), len(keys)) for key, label in definitions]}


def demographic_profile(frame):
    """Do not filter, mutate or impute the source frame used for inference."""
    return {
        "scope": "all_uploaded_records", "total_records": len(frame),
        "denominator": "all_uploaded_records", "weighted": False,
        "sex": _categorical(frame, "DEMO_J__RIAGENDR", SEX),
        "marital": _categorical(frame, "DEMO_J__DMDMARTL", MARITAL),
        "education": _categorical(frame, "DEMO_J__DMDEDUC2", EDUCATION),
        "smoking": _smoking(frame),
        "age": _continuous(frame, "DEMO_J__RIDAGEYR", lambda value: value.is_integer() and 0 <= value <= 80, True),
        "bmi": _continuous(frame, "BMX_J__BMXBMI", lambda value: value > 0),
        "notes": [
            "基本资料统计覆盖整份上传文件，包括未进入模型的记录；分类百分比以全文件总人数为分母，不是预览或模型合格人数。",
            "所有统计均为未加权的上传样本描述，不代表NHANES复杂抽样总体；不从预测结果反推原始资料。",
            "unknown_count包含missing_count；拒答、不知道及非法编码归入缺失或未明确，不推测分类或补零。",
            "年龄和BMI均值仅按各字段有效记录计算，分母为valid_count；NHANES年龄80为公开顶码，年龄摘要描述记录值。",
            "学历沿用NHANES编码，不直接等同中国学制；SMQ020终生不足100支不等于从不吸烟，缺少SMQ040不能判定当前或既往吸烟。",
        ],
    }
