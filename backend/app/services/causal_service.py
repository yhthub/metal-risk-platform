from typing import List, Dict, Any
from ..models.schemas import (
    DAGData, DAGNode, DAGEdge,
    CounterfactualRequest, CounterfactualResult,
    CausalKPI
)


# 模拟DAG节点数据
MOCK_DAG_NODES = [
    # 第一层：暴露源
    {"id": "Pb", "name": "铅 (Pb)", "layer": 0, "node_type": "exposure"},
    {"id": "As", "name": "砷 (As)", "layer": 0, "node_type": "exposure"},
    {"id": "Cd", "name": "镉 (Cd)", "layer": 0, "node_type": "exposure"},
    {"id": "Hg", "name": "汞 (Hg)", "layer": 0, "node_type": "exposure"},
    {"id": "Cr", "name": "铬 (Cr)", "layer": 0, "node_type": "exposure"},
    {"id": "Ni", "name": "镍 (Ni)", "layer": 0, "node_type": "exposure"},

    # 第二层：生物分子机制
    {"id": "oxidative_stress", "name": "氧化应激", "layer": 1, "node_type": "mechanism"},
    {"id": "dna_damage", "name": "DNA损伤", "layer": 1, "node_type": "mechanism"},
    {"id": "protein_binding", "name": "蛋白质结合", "layer": 1, "node_type": "mechanism"},
    {"id": "mitochondrial", "name": "线粒体损伤", "layer": 1, "node_type": "mechanism"},
    {"id": "epigenetic", "name": "表观遗传变化", "layer": 1, "node_type": "mechanism"},

    # 第三层：细胞信号通路
    {"id": "nf_kb", "name": "NF-κB通路", "layer": 2, "node_type": "pathway"},
    {"id": "mapk", "name": "MAPK通路", "layer": 2, "node_type": "pathway"},
    {"id": "pi3k", "name": "PI3K/Akt通路", "layer": 2, "node_type": "pathway"},
    {"id": "jak_stat", "name": "JAK-STAT通路", "layer": 2, "node_type": "pathway"},

    # 第四层：器官损伤
    {"id": "kidney", "name": "肾脏损伤", "layer": 3, "node_type": "organ"},
    {"id": "liver", "name": "肝脏损伤", "layer": 3, "node_type": "organ"},
    {"id": "brain", "name": "神经系统损伤", "layer": 3, "node_type": "organ"},
    {"id": "lung", "name": "肺部损伤", "layer": 3, "node_type": "organ"},
    {"id": "bone", "name": "骨骼损伤", "layer": 3, "node_type": "organ"},

    # 第五层：疾病
    {"id": "ckd", "name": "慢性肾病", "layer": 4, "node_type": "disease"},
    {"id": "neuro", "name": "周围神经病变", "layer": 4, "node_type": "disease"},
    {"id": "hypertension", "name": "高血压", "layer": 4, "node_type": "disease"},
    {"id": "anemia", "name": "贫血", "layer": 4, "node_type": "disease"},
    {"id": "osteoporosis", "name": "骨质疏松", "layer": 4, "node_type": "disease"},
    {"id": "cancer", "name": "癌症", "layer": 4, "node_type": "disease"},

    # 干预节点
    {"id": "antioxidant", "name": "抗氧化剂", "layer": 1, "node_type": "intervention"},
    {"id": "edta", "name": "EDTA螯合", "layer": 1, "node_type": "intervention"},
    {"id": "calcium", "name": "钙锌补充", "layer": 1, "node_type": "intervention"},
    {"id": "ventilation", "name": "通风改善", "layer": 0, "node_type": "intervention"},
]


# 模拟DAG边数据
MOCK_DAG_EDGES = [
    # 暴露源 -> 生物分子机制
    {"source": "Pb", "target": "oxidative_stress", "weight": 0.85},
    {"source": "Pb", "target": "protein_binding", "weight": 0.75},
    {"source": "Pb", "target": "epigenetic", "weight": 0.60},
    {"source": "As", "target": "oxidative_stress", "weight": 0.80},
    {"source": "As", "target": "dna_damage", "weight": 0.70},
    {"source": "Cd", "target": "mitochondrial", "weight": 0.75},
    {"source": "Cd", "target": "oxidative_stress", "weight": 0.65},
    {"source": "Hg", "target": "protein_binding", "weight": 0.85},
    {"source": "Hg", "target": "mitochondrial", "weight": 0.70},
    {"source": "Cr", "target": "dna_damage", "weight": 0.75},
    {"source": "Cr", "target": "oxidative_stress", "weight": 0.60},
    {"source": "Ni", "target": "oxidative_stress", "weight": 0.55},

    # 生物分子机制 -> 细胞信号通路
    {"source": "oxidative_stress", "target": "nf_kb", "weight": 0.90},
    {"source": "oxidative_stress", "target": "mapk", "weight": 0.75},
    {"source": "dna_damage", "target": "pi3k", "weight": 0.80},
    {"source": "protein_binding", "target": "jak_stat", "weight": 0.70},
    {"source": "mitochondrial", "target": "nf_kb", "weight": 0.65},
    {"source": "epigenetic", "target": "pi3k", "weight": 0.60},

    # 细胞信号通路 -> 器官损伤
    {"source": "nf_kb", "target": "kidney", "weight": 0.85},
    {"source": "nf_kb", "target": "liver", "weight": 0.70},
    {"source": "mapk", "target": "brain", "weight": 0.75},
    {"source": "pi3k", "target": "lung", "weight": 0.65},
    {"source": "jak_stat", "target": "bone", "weight": 0.60},

    # 器官损伤 -> 疾病
    {"source": "kidney", "target": "ckd", "weight": 0.90},
    {"source": "brain", "target": "neuro", "weight": 0.85},
    {"source": "kidney", "target": "hypertension", "weight": 0.75},
    {"source": "liver", "target": "anemia", "weight": 0.70},
    {"source": "bone", "target": "osteoporosis", "weight": 0.80},
    {"source": "lung", "target": "cancer", "weight": 0.65},

    # 干预节点的阻断效果
    {"source": "antioxidant", "target": "oxidative_stress", "weight": -0.50},
    {"source": "edta", "target": "Pb", "weight": -0.60},
    {"source": "edta", "target": "Cd", "weight": -0.45},
    {"source": "calcium", "target": "Cd", "weight": -0.35},
    {"source": "calcium", "target": "Pb", "weight": -0.30},
    {"source": "ventilation", "target": "Pb", "weight": -0.40},
    {"source": "ventilation", "target": "As", "weight": -0.35},
]


async def get_dag_data() -> DAGData:
    """获取DAG数据"""
    nodes = [DAGNode(**node) for node in MOCK_DAG_NODES]
    edges = [DAGEdge(**edge) for edge in MOCK_DAG_EDGES]
    return DAGData(nodes=nodes, edges=edges)


async def run_counterfactual_analysis(request: CounterfactualRequest) -> CounterfactualResult:
    """执行反事实推演"""
    # 原始风险评分
    original_risk = 72.5

    # 计算金属调整效果
    metal_reduction = 0.0
    for metal, adjustment in request.metals.items():
        # 每降低10%的金属浓度，风险降低2%
        metal_reduction += adjustment * 0.02

    # 抗氧化干预效果
    antioxidant_reduction = 8.5 if request.antioxidant else 0.0

    # EDTA螯合治疗效果
    edta_reduction = 12.0 if request.edta else 0.0

    # 计算调整后风险
    adjusted_risk = max(0, original_risk - metal_reduction - antioxidant_reduction - edta_reduction)
    risk_reduction = ((original_risk - adjusted_risk) / original_risk) * 100

    # 各干预措施效果
    intervention_effects = {}
    if request.antioxidant:
        intervention_effects["抗氧化剂"] = antioxidant_reduction
    if request.edta:
        intervention_effects["EDTA螯合治疗"] = edta_reduction
    intervention_effects["金属浓度调整"] = metal_reduction

    return CounterfactualResult(
        original_risk=original_risk,
        adjusted_risk=round(adjusted_risk, 1),
        risk_reduction=round(risk_reduction, 1),
        intervention_effects=intervention_effects
    )


async def get_causal_kpi() -> CausalKPI:
    """获取因果推理KPI指标"""
    return CausalKPI(
        overall_risk_score=72.5,
        primary_factor="铅 (Pb)",
        confidence=0.89,
        intervention_priority="优先阻断 Pb 暴露源"
    )
