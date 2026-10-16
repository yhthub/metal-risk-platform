"""All-record NHANES inference and descriptive summaries, not a display page.

Every eligible uploaded record is predicted exactly once in this invocation.
Internal vector chunks bound working-memory use; they never limit the study
population, return a sample as the cohort, or loosen withheld-outcome guards.
No fitting, survey-weighted inference, causal analysis or external IO occurs.
"""
from __future__ import annotations

import math
import time

from ..models.prediction_schemas import CohortPredictionRequest
from . import data_service
from . import nhanes_prediction_service as native
from .nhanes_demographic_service import demographic_profile


CHUNK_ROWS = 512
OPTIONAL_COLUMNS = ("DEMO_J__DMDEDUC2", "DEMO_J__DMDMARTL", "SMQ_J__SMQ020", "SMQ_J__SMQ040")
AGE_BANDS = (("18_39", "18–39岁", 18, 39), ("40_59", "40–59岁", 40, 59),
             ("60_80", "60–80岁（80含公开年龄顶码）", 60, 80))


def _check_table_limits(frame):
    # The cohort API inherits the existing importer limits instead of silently
    # adding a 20/300/500-person display cap to an already accepted upload.
    rows, columns = frame.shape
    bounds = (
        rows <= data_service._batch_limit("BATCH_MAX_ROWS", 50_000, 100_000),
        columns <= data_service._batch_limit("BATCH_MAX_COLUMNS", 300, 300),
        rows * columns <= data_service._batch_limit("BATCH_MAX_CELLS", 2_000_000, 2_000_000),
        int(frame.memory_usage(index=True, deep=True).sum()) <=
            data_service._batch_limit("BATCH_MAX_DATAFRAME_BYTES", 64 * 1024 * 1024, 128 * 1024 * 1024),
    )
    if not all(bounds):
        raise native.PredictionError("整份群体文件超过现有导入容量限制；未进行抽样或部分预测，请先减少非必要字段或核对文件。", 413)
    if rows == 0:
        raise native.PredictionError("已导入文件没有可处理记录。")


def _row_reason(row, message):
    required = {"DEMO_J__RIDAGEYR": "年龄", "DEMO_J__RIAGENDR": "性别",
                "BMX_J__BMXBMI": "BMI", "PBCD_J__LBXBPB": "全血铅",
                "PBCD_J__LBXBCD": "全血镉", "PBCD_J__LBXTHG": "全血总汞"}
    problems = []
    for column, label in required.items():
        try:
            value = float(row[column])
            valid = math.isfinite(value)
            if column == "DEMO_J__RIDAGEYR":
                valid = valid and value.is_integer() and 18 <= value <= 80
            elif column == "DEMO_J__RIAGENDR":
                valid = valid and value in {1, 2}
            elif column == "BMX_J__BMXBMI":
                valid = valid and value > 0
            else:
                valid = valid and value >= 0
        except (ValueError, TypeError, OverflowError):
            valid = False
        if not valid:
            problems.append(label + "（" + column + "）")
    return message + (" 缺失或不符合输入条件的字段：" + "、".join(problems) if problems else "")


def _statistics(np, values):
    count = len(values)
    if count == 0:
        return {"n": 0, "mean": None, "median": None, "q1": None, "q3": None,
                "min": None, "max": None, "std": None, "std_definition": "population_ddof_0",
                "quantile_method": "linear"}
    q1, median, q3 = np.quantile(values, [0.25, 0.5, 0.75], method="linear")
    return {"n": count, "mean": float(np.mean(values)), "median": float(median), "q1": float(q1),
            "q3": float(q3), "min": float(np.min(values)), "max": float(np.max(values)),
            "std": float(np.std(values, ddof=0)), "std_definition": "population_ddof_0",
            "quantile_method": "linear"}


def _distribution(np, values, status):
    if len(values) == 0:
        return {"status": status, "bin_edges": [], "counts": [], "counted_records": 0,
                "method": "equal_width_10_bins", "bin_rule": "left_closed_right_open_except_last_closed"}
    counts, edges = np.histogram(values, bins=10)
    if int(counts.sum()) != len(values):
        raise native.PredictionError("全量预测分布计数核验失败，未返回部分汇总。", 503)
    return {"status": status, "bin_edges": [float(value) for value in edges],
            "counts": [int(value) for value in counts], "counted_records": len(values),
            "method": "equal_width_10_bins", "bin_rule": "left_closed_right_open_except_last_closed"}


def _summaries(bundle, predictions, genders, ages):
    np = bundle["np"]
    eligible = len(ages)
    sex_array = np.asarray(genders, dtype="str")
    age_array = np.asarray(ages, dtype="int16")
    result = []
    for target in native.TARGETS:
        card = bundle["cards"][target]
        withheld = card["metrics_original_units"]["selection"]["R2"] <= 0
        values = np.concatenate(predictions[target]) if predictions[target] else np.asarray([], dtype="float64")
        if (not withheld and len(values) != eligible) or (withheld and len(values)) or not np.isfinite(values).all():
            raise native.PredictionError("全量预测的有效记录与目标计数不一致，未返回不完整汇总。", 503)
        status = ("INSUFFICIENT_VALIDATED_ACCURACY" if withheld else
                  "AVAILABLE" if eligible else "NO_ELIGIBLE_RECORDS")
        stats = _statistics(np, values)

        def group(group_id, label, mask):
            members = int(mask.sum())
            selected = values[mask] if not withheld else np.asarray([], dtype="float64")
            summary = _statistics(np, selected)
            return {"group": group_id, "label_zh": label, "eligible_count": members,
                    "estimated_count": len(selected), "withheld_count": members if withheld else 0,
                    "mean_prediction": summary["mean"], "statistics": summary}

        by_gender = [group("male", "男性", sex_array == "male"), group("female", "女性", sex_array == "female")]
        by_age = [group(key, label, (age_array >= low) & (age_array <= high)) for key, label, low, high in AGE_BANDS]
        if sum(item["eligible_count"] for item in by_gender) != eligible or sum(item["eligible_count"] for item in by_age) != eligible:
            raise native.PredictionError("全人群分组计数不闭合，未返回不完整汇总。", 503)
        histogram = _distribution(np, values, status)
        result.append({"target": target, "label_zh": card["label_zh"], "unit": card["unit"], "status": status,
                       "reason": "验证表现未优于常数参考，暂不显示该结局估计。" if withheld else
                                 "没有符合模型输入条件的记录。" if not eligible else None,
                       "estimated_count": len(values), "withheld_count": eligible if withheld else 0,
                       "mean_prediction": stats["mean"], "statistics": stats,
                       "histogram": histogram, "distribution": histogram,
                       "by_gender": by_gender, "by_age_band": by_age})
    return result


def _compact_results(bundle, predictions, index):
    """Cohort rows carry estimates, not thousands of copies of model cards."""
    items = []
    for target in native.TARGETS:
        card = bundle["cards"][target]
        value = None if predictions[target] is None else float(predictions[target][index])
        items.append({"target": target, "label_zh": card["label_zh"], "unit": card["unit"], "prediction": value,
                      "status": "EXPLORATORY_ESTIMATE" if value is not None else "INSUFFICIENT_VALIDATED_ACCURACY",
                      "reason": None if value is not None else "验证表现不足，暂不显示估计值。"})
    return items


def _outcome_metadata(bundle):
    result = []
    for target in native.TARGETS:
        card = bundle["cards"][target]
        withheld = card["metrics_original_units"]["selection"]["R2"] <= 0
        interval = card["reference_interval"]
        result.append({"target": target, "label_zh": card["label_zh"], "unit": card["unit"],
                       "status": "INSUFFICIENT_VALIDATED_ACCURACY" if withheld else "EXPLORATORY_ESTIMATE",
                       "reason": "基本资料条件下验证表现未优于常数参考，暂不显示估计值。" if withheld else None,
                       "selection_R2": card["metrics_original_units"]["selection"]["R2"],
                       "test_metrics": {key: card["metrics_original_units"]["test"][key] for key in ("MAE", "RMSE", "R2", "n")},
                       "model_family": sorted({component["config"]["family"] for component in card["components"]}),
                       "candidate_id": card["candidate_id"],
                       "residual_reference_range": None if withheld else {
                           "radius_original_units": interval["radius_original_units"], "nominal_calibration_level": 0.9,
                           "guaranteed_coverage": False, "heldout_empirical_coverage": interval["test_empirical_coverage"]}})
    return result


def predict_cohort(payload: CohortPredictionRequest):
    started = time.perf_counter()
    with native._inference_slot():
        native._check_batch_metadata(payload.measurements)
        frame = native._batch_frame(payload.file_id)
        _check_table_limits(frame)
        if not frame.columns.is_unique:
            raise native.PredictionError("群体文件存在重复列名，不能安全映射模型字段。")
        missing = [column for column in native.CONTRACT["batch_required_columns"] if column not in frame.columns]
        if missing:
            raise native.PredictionError("整份文件缺少模型必需列（不会猜测或补零）：" + "、".join(missing))
        ids = frame["SEQN"].map(native._participant_id)
        if ids.duplicated().any():
            raise native.PredictionError("SEQN参与者编号规范化后重复，请先处理重复记录；未擅自保留其中一条。")
        # This original-file profile has its own all-record denominator and
        # remains independent of model eligibility, target selection or paging.
        profile = demographic_profile(frame)
        bundle = native._ensure_bundle()
        selected_columns = list(dict.fromkeys(native.CONTRACT["batch_required_columns"] +
                                [column for column in OPTIONAL_COLUMNS if column in frame.columns]))
        # All source records remain present; narrowing columns only reduces the
        # amount of unrelated laboratory data retained in each worker row.
        source = frame[selected_columns]
        measurements = payload.measurements.model_dump()
        records, genders, ages = [], [], []
        collected = {target: [] for target in native.TARGETS}
        waiting = []
        chunks = 0

        def flush():
            nonlocal chunks
            if not waiting:
                return
            encoded_rows = [encoded for _, encoded in waiting]
            predictions = native._predictions(bundle, encoded_rows)
            for index, (record_index, encoded) in enumerate(waiting):
                records[record_index]["results"] = _compact_results(bundle, predictions, index)
            for target in native.TARGETS:
                if predictions[target] is not None:
                    collected[target].append(predictions[target])
            waiting.clear()
            chunks += 1

        with bundle["threadpools"].threadpool_limits(limits=native.THREADS):
            for position, (_, row) in enumerate(source.iterrows()):
                identifier = str(ids.iloc[position])
                try:
                    person = native._batch_payload(row, identifier, measurements)
                    encoded, audit = native._encode(person)
                except native.PredictionError as exc:
                    records.append({"row_number": position + 1, "person_id": identifier,
                                    "status": "INPUT_NOT_ELIGIBLE", "reason": _row_reason(row, str(exc)), "results": None})
                    continue
                waiting.append((len(records), encoded))
                records.append({"row_number": position + 1, "person_id": identifier,
                                "status": "ESTIMATES_NOT_DIAGNOSES", "input": person.model_dump(),
                                "measurement_audit": audit})
                genders.append(person.person.gender)
                ages.append(person.person.age)
                if len(waiting) == CHUNK_ROWS:
                    flush()
            flush()
            summary = _summaries(bundle, collected, genders, ages)
        total, processed = len(frame), len(ages)
        skipped = total - processed
        if len(records) != total or processed + skipped != total:
            raise native.PredictionError("整份文件处理记录数不闭合，未返回部分结果。", 503)
        warnings = list(native.WARNINGS) + [
            "本次统计覆盖整份上传文件中全部合格对象，不是当前页面、前20人或抽样结果；不合格记录逐行保留原因。",
            "所有群体均值、分位数和分组均为未加权描述性结果，不是复杂抽样总体推断或暴露因果效应。",
            "性别和年龄组仅用于描述模型估计分布，不能据此判定高危人群；60–80岁组中的80可为公开数据年龄顶码。",
            "ALQ111终生饮酒不等于过去一年饮酒，缺少确切信息时仍保留未知；不把缺失资料补成零。",
        ]
        if skipped:
            warnings.append(f"全文件共{total}条，其中{processed}条满足输入条件，{skipped}条未进入模型；请查看逐行原因。")
        provenance = {**native._provenance(), "analysis_scope": "all_uploaded_records",
                      "source_file_id": payload.file_id, "page_limiting_used": False,
                      "sampling_used": False, "eligible_records_used": processed,
                      "internal_vector_chunk_size": CHUNK_ROWS, "native_vector_chunks": chunks,
                      "aggregation": "unweighted descriptive statistics over every eligible uploaded record"}
        return {"model_version": native.MODEL_VERSION, "run_id": native.RUN_ID, "profile": "basic",
                "file_id": payload.file_id, "status": "ESTIMATES_NOT_DIAGNOSES" if processed else "NO_ELIGIBLE_RECORDS",
                "scope": native.SCOPE, "analysis_scope": "all_uploaded_records", "complete": True,
                "total_records": total, "offset": 0, "limit": total, "has_more": False,
                "processed_records": processed, "skipped_records": skipped, "records": records,
                "demographic_profile": profile,
                "summary": summary, "outcome_metadata": _outcome_metadata(bundle),
                "warnings": warnings, "provenance": provenance,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 1)}
