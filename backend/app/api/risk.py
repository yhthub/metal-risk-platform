from fastapi import APIRouter, HTTPException
from typing import List
from ..models.schemas import (
    ModelInfo, RiskAssessmentResult, RiskAssessmentDetail,
    HighRiskPerson
)
from ..services.risk_service import (
    get_available_models, run_risk_assessment,
    get_high_risk_persons, get_risk_assessment_detail
)

router = APIRouter(prefix="/api/risk", tags=["风险量化"])


@router.get("/models", response_model=List[ModelInfo], summary="获取可用模型列表")
async def list_models():
    """
    获取所有可用的风险评估预训练模型

    包含六大类模型：
    - 机器学习：XGBoost、LightGBM、Random Forest、CatBoost、Elastic Net、GAM
    - 深度学习：DNN、SHAP-Integrated MLP、DeepSurv、AFT-NN
    - 因果推断：G-computation、QG-Comp、TMLE、Causal Forest
    - 贝叶斯：BKMR、Bayesian Network、BKMR-CS
    - 生存分析：Cox-PH、Weibull-AFT
    - 集成框架：SuperLearner
    """
    return await get_available_models()


@router.post("/assess", response_model=RiskAssessmentResult, summary="执行风险评估")
async def assess_risk(model_id: str, file_id: str = None):
    """
    使用指定模型执行风险评估

    - **model_id**: 模型ID，如 xgboost, dnn, bkmr 等
    - **file_id**: 数据文件ID（可选，不传则使用默认数据）

    返回：
    - 评估ID
    - 高危人员名单
    - 预警等级和信息
    """
    try:
        result = await run_risk_assessment(model_id, file_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险评估失败: {str(e)}")


@router.get("/high-risk/{assessment_id}", response_model=List[HighRiskPerson], summary="获取高危人员名单")
async def list_high_risk_persons(assessment_id: str):
    """
    获取风险评估识别的高危人员名单

    - **assessment_id**: 评估ID

    返回高危人员列表，包含：
    - 工号、姓名、部门、工龄
    - 风险因子
    - 因果风险增幅(%)
    - 风险等级
    """
    try:
        return await get_high_risk_persons(assessment_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{assessment_id}", response_model=RiskAssessmentDetail, summary="获取风险评估详情")
async def get_assessment_detail(assessment_id: str):
    """
    获取风险评估的详细数据

    包含：
    - SHAP特征归因值
    - 剂量响应曲线数据
    - 联合暴露效应数据
    - 疾病风险预测
    """
    try:
        return await get_risk_assessment_detail(assessment_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{assessment_id}", summary="生成风险评估报告")
async def generate_report(assessment_id: str):
    """
    生成风险评估报告数据

    返回可用于前端渲染报告页面的完整数据
    """
    try:
        # 获取评估详情
        detail = await get_risk_assessment_detail(assessment_id)
        high_risk_persons = await get_high_risk_persons(assessment_id)

        # 构建报告数据
        report = {
            "assessment_id": assessment_id,
            "report_title": "职业重金属复合暴露风险评估报告",
            "report_date": "2026-05-12",
            "total_population": 1245,
            "high_risk_count": len(high_risk_persons),
            "high_risk_persons": [p.model_dump() for p in high_risk_persons],
            "shap_values": [s.model_dump() for s in detail.shap_values],
            "dose_response": [d.model_dump() for d in detail.dose_response],
            "disease_risks": [d.model_dump() for d in detail.disease_risks],
            "primary_high_risk": high_risk_persons[0].model_dump() if high_risk_persons else None,
            "warning_level": "重大规模健康风险预警",
            "warning_message": "结合 G方法 (G-computation) 与贝叶斯核机器回归 (BKMR) 测算，系统已完成全员因果效应模拟。"
        }

        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")
