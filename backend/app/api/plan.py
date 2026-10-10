from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..models.schemas import (
    InterventionPlan, InterventionLevel
)
from ..services.plan_service import (
    get_intervention_plan, get_all_plans,
    get_high_risk_plans, get_medium_risk_plans
)

router = APIRouter(prefix="/api/plan", tags=["干预策略"])


@router.get("/strategies/{person_id}", response_model=InterventionPlan, summary="获取个人干预方案")
async def get_person_plan(person_id: str):
    """
    获取指定人员的干预方案

    - **person_id**: 工号，如 SZ-284

    返回完整的干预方案，包含：
    - 人员基本信息
    - 干预级别（一级/二级预防）
    - 工作流步骤
    - 预期成效
    """
    plan = await get_intervention_plan(person_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"未找到人员 {person_id} 的干预方案")
    return plan


@router.get("/all", response_model=List[InterventionPlan], summary="获取所有干预方案")
async def list_all_plans(level: Optional[InterventionLevel] = None):
    """
    获取所有干预方案

    - **level**: 干预级别筛选（可选）
      - level1: 一级预防（中危人群）
      - level2: 二级预防（高危人群）
    """
    return await get_all_plans(level)


@router.get("/high-risk", response_model=List[InterventionPlan], summary="获取高危人群干预方案")
async def list_high_risk_plans():
    """
    获取高危人群（二级预防）的干预方案

    包含 4 名高危人员：
    - SZ-284 张伟（因果风险增幅 68.5%）
    - SZ-105 李强（因果风险增幅 62.1%）
    - SZ-032 王刚（因果风险增幅 55.4%）
    - SZ-142 刘明（因果风险增幅 48.2%）
    """
    return await get_high_risk_plans()


@router.get("/medium-risk", response_model=List[InterventionPlan], summary="获取中危人群干预方案")
async def list_medium_risk_plans():
    """
    获取中危人群（一级预防）的干预方案

    包含 6 名中危人员：
    - SZ-089 赵铁柱（因果风险增幅 41.5%）
    - SZ-311 陈刚（因果风险增幅 36.8%）
    - SZ-402 孙磊（因果风险增幅 32.1%）
    - SZ-175 周波（因果风险增幅 28.5%）
    - SZ-219 吴涛（因果风险增幅 24.2%）
    - SZ-056 郑凯（因果风险增幅 18.6%）
    """
    return await get_medium_risk_plans()


@router.get("/report/{person_id}", summary="生成个人干预报告")
async def generate_person_report(person_id: str):
    """
    生成个人干预方案报告数据

    - **person_id**: 工号

    返回可用于前端渲染报告页面的完整数据
    """
    plan = await get_intervention_plan(person_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"未找到人员 {person_id} 的干预方案")

    # 构建报告数据
    report = {
        "person_id": plan.person_id,
        "name": plan.name,
        "dept": plan.dept,
        "years": plan.years,
        "factors": plan.factors,
        "score": plan.score,
        "level": plan.level.value,
        "level_name": "二级预防（高危人群早期筛查与临床干预）" if plan.level == InterventionLevel.LEVEL2 else "一级预防（中危人群健康教育与环境阻断）",
        "workflow": [step.model_dump() for step in plan.workflow],
        "outcomes": [outcome.model_dump() for outcome in plan.outcomes],
        "report_title": f"{plan.name}({plan.person_id}) 个人化干预方案报告",
        "report_date": "2026-05-12",
        "reviewer": "Dr. 李华 (职防所)",
        "review_date": "2026-05-15"
    }

    return report


@router.get("/comparison", summary="获取干预前后对比数据")
async def get_intervention_comparison():
    """
    获取所有人员干预前后的成效对比数据

    用于生成对比图表
    """
    all_plans = await get_all_plans()

    comparison_data = []
    for plan in all_plans:
        person_data = {
            "person_id": plan.person_id,
            "name": plan.name,
            "level": plan.level.value,
            "outcomes": {}
        }
        for outcome in plan.outcomes:
            person_data["outcomes"][outcome.label] = {
                "before": outcome.before,
                "after": outcome.after,
                "reduction": round((outcome.before - outcome.after) / outcome.before * 100, 1)
            }
        comparison_data.append(person_data)

    return comparison_data
