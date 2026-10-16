"""Real local NHANES saved-model inference; never fabricates fallback results."""
import math

from fastapi import APIRouter, HTTPException, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from ..models.prediction_schemas import BatchPredictionRequest, CohortPredictionRequest, DashboardPredictionRequest, PersonPredictionRequest
from ..services import nhanes_prediction_service as prediction
from ..services.nhanes_dashboard_service import build_dashboard
from ..services.data_service import DatasetValidationError
from ..services.nhanes_risk_demo_service import RiskDemoError, get_risk_demo_metadata, import_risk_demo
from ..services.nhanes_cohort_service import predict_cohort


NO_STORE = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}


def _safe_validation_value(value):
    # Python's JSON parser accepts NaN/Infinity, but JSON error responses must
    # not echo these invalid literals and crash while explaining a 422 error.
    if isinstance(value, dict):
        return {key: _safe_validation_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_safe_validation_value(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


class PredictionRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request):
            try:
                return await original(request)
            except RequestValidationError as exc:
                return JSONResponse(status_code=422, content={"detail": _safe_validation_value(exc.errors())},
                                    headers=NO_STORE)

        return handler


router = APIRouter(prefix="/api/risk", tags=["真实健康指标估计（NHANES）"], route_class=PredictionRoute)


async def _call(function, *args):
    try:
        return await run_in_threadpool(function, *args)
    except prediction.PredictionError as exc:
        headers = dict(NO_STORE)
        if exc.status_code == 429:
            headers["Retry-After"] = "2"
        raise HTTPException(status_code=exc.status_code, detail=str(exc), headers=headers) from exc


@router.get("/status", summary="核验本地模型、完整性及推理运行时")
async def prediction_status(response: Response):
    response.headers.update(NO_STORE)
    return await _call(prediction.get_prediction_status)


@router.get("/demo", summary="取得显式合成的单人填表示例（不是患者资料）")
async def prediction_demo(response: Response):
    response.headers.update(NO_STORE)
    return prediction.get_prediction_demo()


@router.post("/predict", summary="使用已保存的 NHANES 模型估计12项当前连续指标")
async def predict_person(payload: PersonPredictionRequest, response: Response):
    response.headers.update(NO_STORE)
    return await _call(prediction.predict_person, payload)


@router.post("/predict-batch", summary="对已导入且具备明确NHANES字段的数据分批推理")
async def predict_batch(payload: BatchPredictionRequest, response: Response):
    response.headers.update(NO_STORE)
    return await _call(prediction.predict_batch, payload)


@router.post("/predict-cohort", summary="一次处理整份群体文件的全部合格对象并返回全量描述统计")
async def prediction_cohort(payload: CohortPredictionRequest):
    result = await _call(predict_cohort, payload)
    # Avoid FastAPI's recursive jsonable_encoder duplicating a large all-record
    # response in memory. Serialization is also off the event loop.
    return await run_in_threadpool(JSONResponse, content=result, headers=NO_STORE)


@router.post("/dashboard", summary="为原风险分析仪表板计算真实个体解释和条件预测响应")
async def prediction_dashboard(payload: DashboardPredictionRequest, response: Response):
    response.headers.update(NO_STORE)
    return await _call(build_dashboard, payload)


@router.get("/demo-batch", summary="取得20人真实公开NHANES预测体验样本来源")
async def risk_demo_metadata(response: Response):
    response.headers.update(NO_STORE)
    try:
        return await run_in_threadpool(get_risk_demo_metadata)
    except RiskDemoError as exc:
        raise HTTPException(status_code=503, detail=str(exc), headers=NO_STORE) from exc


@router.post("/demo-batch/import", summary="独立导入20人真实公开样本，供现有批量模型实时计算")
async def risk_demo_import(response: Response):
    response.headers.update(NO_STORE)
    try:
        return await import_risk_demo()
    except RiskDemoError as exc:
        raise HTTPException(status_code=503, detail=str(exc), headers=NO_STORE) from exc
    except DatasetValidationError as exc:
        headers = {**NO_STORE, **({"Retry-After": "5"} if exc.status_code == 429 else {})}
        raise HTTPException(status_code=exc.status_code, detail={"message": str(exc),
            "missing_columns": exc.missing_columns}, headers=headers) from exc
