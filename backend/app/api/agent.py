"""Public RAG endpoints. Raw model/proxy and fake KB-upload APIs are disabled."""
import asyncio
from typing import Literal, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..services.corpus_retrieval_service import CorpusUnavailable, RetrievalTimeout
from ..services.local_llm_service import ModelUnavailableError
from ..services.rag_agent_service import get_rag_service, RagBusyError, InvalidGenerationError

router = APIRouter(prefix="/api/agent", tags=["真实本地RAG"])


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: List[HistoryMessage] = Field(default_factory=list, max_length=12)
    model: Optional[str] = Field(default=None, max_length=100)
    enable_deep_think: bool = True
    knowledge_bases: List[str] = Field(default_factory=list, max_length=9)
    sources: Optional[List[Literal["pubmed", "textbooks", "statpearls"]]] = None


class EvidenceSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=8, ge=1, le=12)
    sources: Optional[List[Literal["pubmed", "textbooks", "statpearls"]]] = None
    mode: Optional[Literal["bm25", "medcpt", "hybrid"]] = None
    candidate_k: Optional[int] = Field(default=None, ge=1, le=128)


@router.get("/status")
async def status():
    return await asyncio.to_thread(get_rag_service().status)


@router.get("/models")
async def models():
    service = get_rag_service()
    client = service.llm_factory()
    try:
        result = await asyncio.to_thread(client.status)
    finally:
        client.close()
    return {"models": [{"name": service.settings.model, "ready": result["ready"]}],
            "default": service.settings.model}


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        return await get_rag_service().chat(
            request.message, [item.model_dump() for item in request.history],
            request.model, request.enable_deep_think, request.sources)
    except CorpusUnavailable as error:
        raise HTTPException(503, detail=str(error)) from error
    except RetrievalTimeout as error:
        raise HTTPException(504, detail=str(error)) from error
    except ModelUnavailableError as error:
        raise HTTPException(503, detail=str(error)) from error
    except RagBusyError as error:
        raise HTTPException(429, detail=str(error), headers={"Retry-After": "5"}) from error
    except InvalidGenerationError as error:
        raise HTTPException(502, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(400, detail=str(error)) from error


@router.post("/evidence-search")
async def evidence_search(request: EvidenceSearchRequest):
    service = get_rag_service()
    try:
        kwargs = {"mode": request.mode} if request.mode else {}
        return await asyncio.to_thread(service.retriever.search, request.query,
                                        request.top_k, request.candidate_k or service.settings.candidate_k,
                                        request.sources, **kwargs)
    except CorpusUnavailable as error:
        raise HTTPException(503, detail=str(error)) from error
    except RetrievalTimeout as error:
        raise HTTPException(504, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(400, detail=str(error)) from error


@router.get("/knowledge-bases")
async def knowledge_bases():
    # No fictitious counts: declared counts are available through corpus status.
    return [{"id": value, "name": label} for value, label in
            [("pubmed", "PubMed标题/摘要"), ("textbooks", "医学教材"), ("statpearls", "StatPearls")]]


@router.post("/upload-kb")
async def upload_kb():
    raise HTTPException(501, detail="私有文档提取/切分/入库尚未实现；不会返回模拟上传成功。")


@router.post("/ollama/chat")
async def legacy_model_proxy():
    raise HTTPException(410, detail="旧的无检索模型代理已停用，请使用 /api/agent/chat。")
