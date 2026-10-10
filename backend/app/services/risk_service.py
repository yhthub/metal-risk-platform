from typing import List, Dict, Any
from ..models.schemas import (
    ModelInfo, RiskAssessmentResult, RiskAssessmentDetail,
    HighRiskPerson, ShapValue, DoseResponsePoint,
    JointEffectPoint, DiseaseRisk, RiskLevel
)
from ..utils.helpers import (
    generate_assessment_id, get_model_category,
    get_model_description, calculate_risk_level
)


# 预训练模型列表
AVAILABLE_MODELS = [
    {"id": "xgboost", "name": "XGBoost", "category": "机器学习"},
    {"id": "lightgbm", "name": "LightGBM", "category": "机器学习"},
    {"id": "random_forest", "name": "Random Forest", "category": "机器学习"},
    {"id": "catboost", "name": "CatBoost", "category": "机器学习"},
    {"id": "elastic_net", "name": "Elastic Net", "category": "机器学习"},
    {"id": "gam", "name": "GAM", "category": "机器学习"},
    {"id": "dnn", "name": "DNN", "category": "深度学习"},
    {"id": "shap_mlp", "name": "SHAP-Integrated MLP", "category": "深度学习"},
    {"id": "deepsurv", "name": "DeepSurv", "category": "深度学习"},
    {"id": "aft_nn", "name": "AFT-NN", "category": "深度学习"},
    {"id": "g_computation", "name": "G-computation", "category": "因果推断"},
    {"id": "qg_comp", "name": "QG-Comp", "category": "因果推断"},
    {"id": "tmle", "name": "TMLE", "category": "因果推断"},
    {"id": "causal_forest", "name": "Causal Forest", "category": "因果推断"},
    {"id": "bkmr", "name": "BKMR", "category": "贝叶斯"},
    {"id": "bayesian_network", "name": "Bayesian Network", "category": "贝叶斯"},
    {"id": "bkmr_cs", "name": "BKMR-CS", "category": "贝叶斯"},
    {"id": "cox_ph", "name": "Cox-PH", "category": "生存分析"},
    {"id": "weibull_aft", "name": "Weibull-AFT", "category": "生存分析"},
    {"id": "super_learner", "name": "SuperLearner", "category": "集成框架"}
]


# 模拟高危人员数据
MOCK_HIGH_RISK_PERSONS = [
    {"id": "SZ-284", "name": "张伟", "dept": "第一熔炼车间", "years": 15, "factors": "Pb, As, Cd", "score": 68.5},
    {"id": "SZ-105", "name": "李强", "dept": "第一熔炼车间", "years": 12, "factors": "Pb, As", "score": 62.1},
    {"id": "SZ-032", "name": "王刚", "dept": "原矿粉碎区", "years": 18, "factors": "Pb, Cd, Hg", "score": 55.4},
    {"id": "SZ-142", "name": "刘明", "dept": "尾气处理组", "years": 10, "factors": "As, Cr", "score": 48.2},
    {"id": "SZ-089", "name": "赵铁柱", "dept": "原矿粉碎区", "years": 11, "factors": "Cd, Cr", "score": 41.5},
    {"id": "SZ-311", "name": "陈刚", "dept": "第一熔炼车间", "years": 9, "factors": "Pb, As", "score": 36.8},
    {"id": "SZ-402", "name": "孙磊", "dept": "尾气处理组", "years": 8, "factors": "As, Ni", "score": 32.1},
    {"id": "SZ-175", "name": "周波", "dept": "第一熔炼车间", "years": 7, "factors": "Pb", "score": 28.5},
    {"id": "SZ-219", "name": "吴涛", "dept": "原矿粉碎区", "years": 6, "factors": "Cd, Hg", "score": 24.2},
    {"id": "SZ-056", "name": "郑凯", "dept": "尾气处理组", "years": 5, "factors": "Cr", "score": 18.6}
]


async def get_available_models() -> List[ModelInfo]:
    """获取可用模型列表"""
    models = []
    for model in AVAILABLE_MODELS:
        models.append(ModelInfo(
            id=model["id"],
            name=model["name"],
            category=model["category"],
            description=get_model_description(model["id"])
        ))
    return models


async def run_risk_assessment(model_id: str, file_id: str = None) -> RiskAssessmentResult:
    """执行风险评估"""
    assessment_id = generate_assessment_id()

    # 模拟风险评估结果
    high_risk_persons = []
    for person in MOCK_HIGH_RISK_PERSONS:
        level = calculate_risk_level(person["score"])
        high_risk_persons.append(HighRiskPerson(
            id=person["id"],
            name=person["name"],
            dept=person["dept"],
            years=person["years"],
            factors=person["factors"],
            score=person["score"],
            level=RiskLevel(level)
        ))

    return RiskAssessmentResult(
        assessment_id=assessment_id,
        model_name=model_id,
        total_population=1245,
        high_risk_count=10,
        high_risk_ratio=0.8,
        high_risk_persons=high_risk_persons,
        warning_level="重大规模健康风险预警",
        warning_message="结合 G方法 (G-computation) 与贝叶斯核机器回归 (BKMR) 测算，系统已完成全员因果效应模拟。当前车间若污染等级上升一档，将引发严重的多靶器官致病暴发。已为您精准锁定特异性高危易感10人，亟需立即采取干预与隔离措施！"
    )


async def get_high_risk_persons(assessment_id: str) -> List[HighRiskPerson]:
    """获取高危人员列表"""
    persons = []
    for person in MOCK_HIGH_RISK_PERSONS:
        level = calculate_risk_level(person["score"])
        persons.append(HighRiskPerson(
            id=person["id"],
            name=person["name"],
            dept=person["dept"],
            years=person["years"],
            factors=person["factors"],
            score=person["score"],
            level=RiskLevel(level)
        ))
    return persons


async def get_risk_assessment_detail(assessment_id: str) -> RiskAssessmentDetail:
    """获取风险评估详情"""

    # SHAP值数据
    shap_values = [
        ShapValue(name="Pb 铅", value=0.45),
        ShapValue(name="As 砷", value=0.25),
        ShapValue(name="Cd 镉", value=0.15),
        ShapValue(name="Cr 铬", value=0.10),
        ShapValue(name="Hg 汞", value=-0.03),
        ShapValue(name="Ni 镍", value=-0.05),
        ShapValue(name="Co 钴", value=-0.02),
        ShapValue(name="Th 钍", value=-0.01),
        ShapValue(name="Li 锂", value=-0.04),
        ShapValue(name="Rn 氡", value=-0.02)
    ]

    # 剂量响应曲线数据（Sigmoid函数）
    dose_response = []
    for i in range(50):
        x = i * 2
        y = 100 / (1 + 2.718 ** (-0.15 * (x - 60)))  # Sigmoid
        dose_response.append(DoseResponsePoint(dose=float(x), response=round(y, 1)))

    # 联合暴露效应数据
    joint_effects = []
    pb_levels = ["低", "较低", "中等", "高", "极高"]
    as_levels = ["低", "较低", "中等", "高", "极高"]
    for i, as_level in enumerate(as_levels):
        for j, pb_level in enumerate(pb_levels):
            risk = (i + 1) * (j + 1) * 3.5 + 5.0
            joint_effects.append(JointEffectPoint(
                pb_level=pb_level,
                as_level=as_level,
                risk=round(risk, 1)
            ))

    # 疾病风险预测
    disease_risks = [
        DiseaseRisk(name="慢性肾病 (CKD)", probability=78.5, status="danger"),
        DiseaseRisk(name="周围神经病变", probability=65.2, status="danger"),
        DiseaseRisk(name="高血压", probability=58.3, status="warning"),
        DiseaseRisk(name="贫血", probability=45.1, status="warning"),
        DiseaseRisk(name="骨质疏松", probability=32.8, status="normal")
    ]

    return RiskAssessmentDetail(
        shap_values=shap_values,
        dose_response=dose_response,
        joint_effects=joint_effects,
        disease_risks=disease_risks
    )
