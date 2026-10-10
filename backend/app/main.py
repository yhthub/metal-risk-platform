from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from .api import datainput, risk, causal, plan, agent
from .services.data_service import UPLOAD_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="职业金属复合暴露智能干预推荐与决策支持系统 API",
    description="职业金属复合暴露智能干预推荐与决策支持系统后端API",
    version="1.0.0"
)

# 配置CORS - 简化配置，确保跨域正常工作
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=False,  # 使用 * 时必须为 False
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

logger.info("CORS 已配置为允许所有源访问")

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 注册路由
app.include_router(datainput.router)
app.include_router(risk.router)
app.include_router(causal.router)
app.include_router(plan.router)
app.include_router(agent.router)


@app.get("/", tags=["根路径"])
async def root():
    """
    API根路径，返回系统基本信息
    """
    return {
        "name": "职业金属复合暴露智能干预推荐与决策支持系统",
        "version": "1.0.0",
        "description": "面向职业卫生与流行病学研究场景的智能决策支持系统",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_prefix": "/api",
        "modules": [
            {"name": "数据接入", "prefix": "/api/datainput", "description": "职业暴露数据的结构化录入与批量导入"},
            {"name": "风险量化", "prefix": "/api/risk", "description": "基于20种预训练模型的风险评估与预警"},
            {"name": "因果推理", "prefix": "/api/causal", "description": "全景DAG可视化与反事实推演"},
            {"name": "干预策略", "prefix": "/api/plan", "description": "个人化干预方案生成与成效预测"},
            {"name": "RAG问答", "prefix": "/api/agent", "description": "知识库智能问答与决策溯源"}
        ]
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "service": "occupational-health-api",
        "version": "1.0.0"
    }


@app.get("/api/info", tags=["系统"])
async def api_info():
    """
    API详细信息
    """
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "endpoints": {
            "datainput": {
                "single": "POST /api/datainput/single - 单人数据录入",
                "batch": "POST /api/datainput/batch - 群体数据批量导入",
                "statistics": "GET /api/datainput/statistics/{file_id} - 数据统计",
                "visualization": "GET /api/datainput/visualization/{file_id} - 可视化数据",
                "records": "GET /api/datainput/records - 获取所有记录",
                "record": "GET /api/datainput/records/{record_id} - 获取单条记录"
            },
            "risk": {
                "models": "GET /api/risk/models - 获取可用模型",
                "assess": "POST /api/risk/assess - 执行风险评估",
                "high_risk": "GET /api/risk/high-risk/{assessment_id} - 高危人员名单",
                "detail": "GET /api/risk/detail/{assessment_id} - 评估详情",
                "report": "GET /api/risk/report/{assessment_id} - 生成报告"
            },
            "causal": {
                "dag": "GET /api/causal/dag - 获取DAG数据",
                "counterfactual": "POST /api/causal/counterfactual - 反事实推演",
                "kpi": "GET /api/causal/kpi - KPI指标",
                "nodes": "GET /api/causal/nodes - 节点列表",
                "edges": "GET /api/causal/edges - 边列表",
                "pathway": "GET /api/causal/pathway/{metal} - 金属致病路径"
            },
            "plan": {
                "strategy": "GET /api/plan/strategies/{person_id} - 个人干预方案",
                "all": "GET /api/plan/all - 所有干预方案",
                "high_risk": "GET /api/plan/high-risk - 高危人群方案",
                "medium_risk": "GET /api/plan/medium-risk - 中危人群方案",
                "report": "GET /api/plan/report/{person_id} - 个人报告",
                "comparison": "GET /api/plan/comparison - 成效对比"
            },
            "agent": {
                "knowledge_bases": "GET /api/agent/knowledge-bases - 知识库列表",
                "chat": "POST /api/agent/chat - 问答消息",
                "upload": "POST /api/agent/upload-kb - 上传知识库",
                "models": "GET /api/agent/models - 模型列表",
                "quick_prompts": "GET /api/agent/quick-prompts - 快捷提问"
            }
        }
    }
