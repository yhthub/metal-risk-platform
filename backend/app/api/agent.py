from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from ..models.schemas import (
    KnowledgeBase, ChatRequest, ChatResponse, ApiResponse, DualPathRetrievalResult
)
from ..services.agent_service import (
    get_knowledge_bases, process_chat
)
from ..services.ollama_service import get_ollama_service
from ..services.dual_path_evidence_service import execute_dual_path_search

router = APIRouter(prefix="/api/agent", tags=["RAG问答"])


class OllamaChatRequest(BaseModel):
    """Ollama 聊天请求"""
    message: str
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None


class EvidenceSearchRequest(BaseModel):
    """双通路证据检索请求"""
    query: str
    top_k_per_channel: int = 256


@router.post("/evidence-search", response_model=DualPathRetrievalResult, summary="双通路循证证据检索")
async def search_evidence(request: EvidenceSearchRequest):
    """
    双通路循证检索接口 (每通路 Top-256，精选 Top-128 科学证据切块，评分去 fu 指数)
    - 通路 1: 稠密检索通道 (BGE 向量语义 Top-256)
    - 通路 2: 稀疏检索通道 (FTS5 / BM25 Top-256)
    - 法定红线: P0/P1 国家标准独立提取 Top-10
    - Med-R² 细排: DocScore 筛选精选 Top-128
    """
    try:
        return execute_dual_path_search(request.query, top_k_per_channel=request.top_k_per_channel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"双通路检索失败: {str(e)}")


@router.get("/knowledge-bases", response_model=List[KnowledgeBase], summary="获取知识库列表")
async def list_knowledge_bases():
    """
    获取所有可用的知识库

    包含 9 个毒理学数据库：
    - 职业重金属复合暴露因果库
    - IARC 致癌物风险评级报告
    - WHO 化学品安全与毒理库 (IPCS)
    - ToxNet 毒理学数据网络
    - NHANES 营养与健康调查库
    - CTD 比较毒理基因组学数据库
    - EPA/ATSDR 毒物学概况库
    - 职业病临床诊疗指南 (2025版)
    - PubMed 职业流行病学文献库
    """
    return await get_knowledge_bases()


@router.post("/chat", response_model=ChatResponse, summary="发送问答消息")
async def chat(request: ChatRequest):
    """
    发送问答消息给RAG Agent (集成双通路循证检索与真实依据卡片)

    - **message**: 用户提问内容
    - **model**: 使用的推理模型（默认 XGBoost）
    - **knowledge_bases**: 选中的知识库列表
    - **enable_deep_think**: 是否启用深度思考模式

    返回：
    - AI回复内容 (真实双通路综合研判)
    - 思考过程 (各通路检索推进链)
    - 引用的知识库
    - 推荐的补充知识库
    - 双通路证据卡片 (Top 真实切块条目)
    - 检索统计摘要
    """
    try:
        result = await process_chat(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")



@router.post("/upload-kb", response_model=ApiResponse, summary="上传知识库文件")
async def upload_knowledge_base(file: UploadFile = File(...)):
    """
    上传本地私有知识库文件

    - 支持 .pdf 和 .md 格式
    - 文件将被处理并添加到知识库中
    """
    # 验证文件类型
    if not file.filename.endswith(('.pdf', '.md')):
        raise HTTPException(status_code=400, detail="仅支持 PDF 和 MD 格式文件")

    try:
        content = await file.read()
        # TODO: 实际处理文件并添加到知识库
        # 这里仅模拟成功响应
        return ApiResponse(
            success=True,
            message=f"成功上传知识库文件: {file.filename}",
            data={
                "filename": file.filename,
                "size": len(content),
                "status": "processing"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/models", summary="获取可用模型列表")
async def list_agent_models():
    """
    获取RAG Agent可用的推理模型列表

    与风险量化模块共享 20 种预训练模型
    """
    models = [
        "XGBoost", "DNN", "LightGBM", "G-computation", "BKMR",
        "Random Forest", "CatBoost", "Elastic Net", "Cox-PH", "Weibull-AFT",
        "Bayesian Network", "GAM", "SHAP-Integrated MLP", "QG-Comp", "TMLE",
        "DeepSurv", "AFT-NN", "BKMR-CS", "SuperLearner", "Causal Forest"
    ]
    return {"models": models}


@router.get("/quick-prompts", summary="获取快捷提问列表")
async def get_quick_prompts():
    """
    获取预设的快捷提问示例
    """
    prompts = [
        {
            "id": "q1",
            "text": "详细解析一下铅(Pb)的致病机制与靶器官",
            "icon": "microphone"
        },
        {
            "id": "q2",
            "text": "重金属暴露导致的慢性肾病(CKD)有哪些前兆标志物？",
            "icon": "data-analysis"
        },
        {
            "id": "q3",
            "text": "对比砷(As)和镉(Cd)的暴露来源与致癌性差异",
            "icon": "scale-to-original"
        }
    ]
    return {"prompts": prompts}


@router.get("/ollama/status", summary="检查 Ollama 服务状态")
async def check_ollama_status():
    """
    检查 Ollama 服务是否正在运行
    """
    service = get_ollama_service()
    is_connected = service.check_connection()

    return {
        "status": "connected" if is_connected else "disconnected",
        "url": service.base_url,
        "message": "Ollama 服务正常" if is_connected else "无法连接到 Ollama 服务，请确保 Ollama 正在运行"
    }


@router.get("/ollama/models", summary="获取 Ollama 可用模型")
async def list_ollama_models():
    """
    获取 Ollama 中已下载的模型列表
    """
    service = get_ollama_service()

    if not service.check_connection():
        raise HTTPException(
            status_code=503,
            detail="无法连接到 Ollama 服务，请确保 Ollama 正在运行"
        )

    models = service.get_available_models()
    return {
        "models": models,
        "default": service.default_model
    }


@router.post("/ollama/chat", summary="使用 Ollama 进行聊天")
async def ollama_chat(request: OllamaChatRequest):
    """
    使用 Ollama 本地模型进行聊天

    - **message**: 用户消息
    - **model**: 模型名称（可选，默认使用 deepseek-r1:latest）
    - **system_prompt**: 系统提示词（可选，如不提供则使用专业公卫专家提示）
    - **temperature**: 温度参数（可选）

    注意：系统会自动使用公共卫生专家 Prompt 模板来提升回答质量
    """
    service = get_ollama_service()

    if not service.check_connection():
        raise HTTPException(
            status_code=503,
            detail="无法连接到 Ollama 服务，请确保 Ollama 正在运行"
        )

    result = service.generate(
        prompt=request.message,
        model=request.model,
        system_prompt=request.system_prompt,
        temperature=request.temperature,
        use_professional_prompt=True  # 使用专业 prompt
    )

    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result["error"])


@router.get("/ollama/quick-prompts", summary="获取快捷提问模板")
async def get_quick_prompts():
    """
    获取公共卫生领域的快捷提问模板

    返回预设的专业问题，用户可以直接使用或参考
    """
    from ..prompts import get_all_quick_prompts

    prompts = get_all_quick_prompts()
    return {
        "prompts": [
            {"id": key, "text": value, "category": "职业卫生"}
            for key, value in prompts.items()
        ]
    }


@router.get("/ollama/extract-triples", summary="提取问题三元组")
async def extract_question_triples(message: str):
    """
    从用户问题中提取关键信息三元组

    - **message**: 用户问题

    返回提取的暴露因素、靶器官、健康效应等信息
    """
    from ..prompts import extract_triples, classify_question

    triples = extract_triples(message)
    question_type = classify_question(message)

    return {
        "triples": triples,
        "question_type": question_type,
        "original_question": message
    }
