"""Retired mock risk routes; real saved-model prediction is in prediction.py."""
from typing import List
from fastapi import APIRouter, HTTPException
from ..models.schemas import ModelInfo

router = APIRouter(prefix="/api/risk", tags=["指标估计与旧接口迁移"])


@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    return [ModelInfo(id="nhanes_v5_basic", name="NHANES v5（XGBoost / CatBoost）",
                      category="真实CPU回归模型",
                      description="基础资料版12项当次连续指标估计；就绪状态见/api/risk/status。非发病概率、诊断或因果效应。")]


def retired():
    raise HTTPException(status_code=410, detail={
        "code": "MOCK_RISK_ENDPOINT_RETIRED",
        "message": "旧模拟风险/因果结果已停用。请使用 POST /api/risk/predict 或 /predict-batch；真实报告由这些结果生成，不再返回固定高危名单或模拟患病概率。",
    })


@router.post("/assess")
async def assess_risk():
    retired()


@router.get("/high-risk/{assessment_id}")
async def list_high_risk_persons(assessment_id: str):
    retired()


@router.get("/detail/{assessment_id}")
async def get_assessment_detail(assessment_id: str):
    retired()


@router.get("/report/{assessment_id}")
async def generate_report(assessment_id: str):
    retired()
