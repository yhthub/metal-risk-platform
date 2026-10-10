from fastapi import APIRouter, HTTPException
from ..models.schemas import (
    DAGData, CounterfactualRequest, CounterfactualResult,
    CausalKPI
)
from ..services.causal_service import (
    get_dag_data, run_counterfactual_analysis, get_causal_kpi
)

router = APIRouter(prefix="/api/causal", tags=["因果推理"])


@router.get("/dag", response_model=DAGData, summary="获取DAG数据")
async def get_causal_dag():
    """
    获取因果知识推理的有向无环图(DAG)数据

    包含：
    - 30+ 节点，5层结构
    - 暴露源、生物分子机制、细胞信号通路、器官损伤、疾病
    - 干预节点（抗氧化剂、EDTA螯合等）
    - 35+ 因果连线及权重
    """
    try:
        return await get_dag_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取DAG数据失败: {str(e)}")


@router.post("/counterfactual", response_model=CounterfactualResult, summary="反事实推演")
async def counterfactual_analysis(request: CounterfactualRequest):
    """
    执行反事实因果推演

    - **metals**: 各金属浓度调整值（负值表示降低）
    - **antioxidant**: 是否启用抗氧化干预
    - **edta**: 是否启用EDTA螯合治疗

    返回：
    - 原始风险评分
    - 调整后风险评分
    - 风险降低幅度(%)
    - 各干预措施效果
    """
    try:
        return await run_counterfactual_analysis(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反事实推演失败: {str(e)}")


@router.get("/kpi", response_model=CausalKPI, summary="获取因果推理KPI")
async def get_kpi():
    """
    获取因果推理的关键绩效指标

    - 综合因果风险评分
    - 主导致病因子
    - 推断置信度
    - 最优干预优先级
    """
    try:
        return await get_causal_kpi()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes", summary="获取DAG节点列表")
async def list_dag_nodes():
    """获取所有DAG节点信息"""
    dag_data = await get_dag_data()
    return [node.model_dump() for node in dag_data.nodes]


@router.get("/edges", summary="获取DAG边列表")
async def list_dag_edges():
    """获取所有DAG边信息"""
    dag_data = await get_dag_data()
    return [edge.model_dump() for edge in dag_data.edges]


@router.get("/pathway/{metal}", summary="获取金属致病路径")
async def get_metal_pathway(metal: str):
    """
    获取特定金属的致病因果路径

    - **metal**: 金属名称，如 Pb, As, Cd, Hg 等

    返回从该金属到疾病的完整因果链路
    """
    dag_data = await get_dag_data()

    # 查找以该金属为起点的路径
    pathways = []
    for edge in dag_data.edges:
        if edge.source == metal:
            pathway = [edge.source, edge.target]
            # 递归查找后续路径
            current = edge.target
            while True:
                next_edges = [e for e in dag_data.edges if e.source == current]
                if not next_edges:
                    break
                next_edge = next_edges[0]  # 取第一条路径
                pathway.append(next_edge.target)
                current = next_edge.target
            pathways.append(pathway)

    return {
        "metal": metal,
        "pathways": pathways,
        "pathway_count": len(pathways)
    }
