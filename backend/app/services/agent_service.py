from typing import List, Dict, Any, Optional
from ..models.schemas import (
    KnowledgeBase, ChatRequest, ChatResponse
)


# 知识库列表
KNOWLEDGE_BASES = [
    KnowledgeBase(
        id="kb_001",
        name="职业重金属复合暴露因果库",
        description="包含职业环境中重金属暴露的因果关系、剂量-反应关系、靶器官效应等结构化知识",
        document_count=1250
    ),
    KnowledgeBase(
        id="kb_002",
        name="IARC 致癌物风险评级报告",
        description="国际癌症研究机构(IARC)发布的致癌物分级评估报告，涵盖1类、2A类、2B类致癌物",
        document_count=890
    ),
    KnowledgeBase(
        id="kb_003",
        name="WHO 化学品安全与毒理库 (IPCS)",
        description="世界卫生组织国际化学品安全规划署(IPCS)发布的化学品安全评估文件",
        document_count=2100
    ),
    KnowledgeBase(
        id="kb_004",
        name="ToxNet 毒理学数据网络",
        description="美国国家医学图书馆毒理学数据网络，包含化学品毒理学和环境健康信息",
        document_count=3500
    ),
    KnowledgeBase(
        id="kb_005",
        name="NHANES 营养与健康调查库",
        description="美国国家健康与营养检查调查数据库，包含人群生物标志物监测数据",
        document_count=1800
    ),
    KnowledgeBase(
        id="kb_006",
        name="CTD 比较毒理基因组学数据库",
        description="比较毒理基因组学数据库，包含化学品-基因-疾病相互作用数据",
        document_count=4200
    ),
    KnowledgeBase(
        id="kb_007",
        name="EPA/ATSDR 毒物学概况库",
        description="美国环保署和有毒物质与疾病登记局发布的有毒物质概况文件",
        document_count=1600
    ),
    KnowledgeBase(
        id="kb_008",
        name="职业病临床诊疗指南 (2025版)",
        description="最新版职业病临床诊疗指南，包含各类职业病的诊断标准和治疗方案",
        document_count=450
    ),
    KnowledgeBase(
        id="kb_009",
        name="PubMed 职业流行病学文献库",
        description="PubMed数据库中职业流行病学相关文献的精选集合",
        document_count=8500
    )
]


# 模拟知识库内容
MOCK_KNOWLEDGE = {
    "铅": {
        "name": "铅 (Pb)",
        "source": "冶炼、废旧电池、含铅管道、含铅涂料、烟草烟雾等",
        "mechanism": "Pb²⁺可替代Ca²⁺干扰细胞信号通路，诱导氧化应激和表观遗传变化；与硫醇(-SH)结合损伤蛋白质。",
        "disease": "神经系统(认知发育迟缓、共济失调)、肾脏损伤(慢性肾病)、高血压、血液(贫血)",
        "biomarker": "血铅浓度、δ-氨基酯酶(ALAD)活性↓、ROS生成↑、尿β₂-微球蛋白↑",
        "evidence": "高（系统综述与队列研究证实低剂量可致血压升高和肾功能下降，IARC 2A类致癌）"
    },
    "砷": {
        "name": "砷 (As)",
        "source": "地下水污染、农用化学品、工业废气、含砷农产品",
        "mechanism": "在肝脏中甲基化代谢产生有毒形式，产生氧化应激、抑制DNA修复并改变DNA甲基化。",
        "disease": "皮肤(色素异常、皮肤癌)、肺(肺癌)、膀胱(膀胱癌)、心血管(动脉硬化)",
        "biomarker": "尿总砷及其代谢物(MMA/DMA)、血砷、DNA甲基化变化",
        "evidence": "高（无机砷为IARC 1类致癌物，慢性低剂量暴露可导致皮肤损伤、癌症）"
    },
    "镉": {
        "name": "镉 (Cd)",
        "source": "烟草烟雾、电镀/电池工业废气、矿山和冶炼尘埃",
        "mechanism": "镉在肝脏结合金属硫蛋白(MT)后累积于肾脏，长期释放产生氧化应激、线粒体损伤和DNA损伤。",
        "disease": "肾小管(蛋白尿、慢性肾功能衰竭)、骨骼(骨质疏松、'痛痛病')、呼吸(肺纤维化)",
        "biomarker": "尿镉、血镉、肾功能指标(肌酐、尿蛋白)、骨密度",
        "evidence": "高（IARC 1类致肺癌，广泛流行病学证据表明慢性暴露显著损伤肾脏和骨骼）"
    },
    "汞": {
        "name": "汞 (Hg)",
        "source": "海产品甲基汞、工业矿井和燃烧排放、水银采矿",
        "mechanism": "Hg⁰/MeHg与硫醇(-SH)强烈结合，跨越血脑屏障导致神经毒性和氧化应激。",
        "disease": "中枢神经系统(神经发育损伤、感觉障碍)；肾脏(蛋白尿)、免疫系统",
        "biomarker": "血/尿总汞和有机汞浓度、神经行为测试",
        "evidence": "中（孕期甲基汞神经发育毒性证据充分；高剂量致肾癌）"
    }
}


# 知识库推荐规则
KB_RECOMMENDATION_RULES = [
    {
        "keywords": ["铅", "Pb", "铅中毒", "驱铅", "EDTA"],
        "kbs": ["职业重金属复合暴露因果库", "职业病临床诊疗指南 (2025版)", "EPA/ATSDR 毒物学概况库"],
        "reason": "铅暴露因果机制与临床驱铅方案"
    },
    {
        "keywords": ["砷", "As", "砷中毒", "皮肤癌"],
        "kbs": ["IARC 致癌物风险评级报告", "CTD 比较毒理基因组学数据库", "PubMed 职业流行病学文献库"],
        "reason": "砷致癌性评估与基因组毒理学"
    },
    {
        "keywords": ["镉", "Cd", "肾病", "骨质疏松", "痛痛病"],
        "kbs": ["WHO 化学品安全与毒理库 (IPCS)", "NHANES 营养与健康调查库", "ToxNet 毒理学数据网络"],
        "reason": "镉的肾毒性与骨骼损伤机制"
    },
    {
        "keywords": ["汞", "Hg", "甲基汞", "神经毒性"],
        "kbs": ["ToxNet 毒理学数据网络", "WHO 化学品安全与毒理库 (IPCS)", "PubMed 职业流行病学文献库"],
        "reason": "汞的神经毒理学与甲基汞代谢"
    },
    {
        "keywords": ["癌症", "致癌", "肿瘤", "IARC"],
        "kbs": ["IARC 致癌物风险评级报告", "CTD 比较毒理基因组学数据库", "PubMed 职业流行病学文献库"],
        "reason": "致癌物分级与流行病学证据"
    },
    {
        "keywords": ["肾", "肾脏", "CKD", "肾衰竭", "蛋白尿"],
        "kbs": ["NHANES 营养与健康调查库", "职业病临床诊疗指南 (2025版)", "EPA/ATSDR 毒物学概况库"],
        "reason": "慢性肾病的营养流行病学与临床管理"
    },
    {
        "keywords": ["神经", "认知", "脑", "帕金森", "阿尔茨海默"],
        "kbs": ["PubMed 职业流行病学文献库", "职业重金属复合暴露因果库", "IARC 致癌物风险评级报告"],
        "reason": "神经退行性病变的职业暴露流行病学"
    },
    {
        "keywords": ["干预", "治疗", "防护", "方案", "策略"],
        "kbs": ["职业病临床诊疗指南 (2025版)", "EPA/ATSDR 毒物学概况库", "职业重金属复合暴露因果库"],
        "reason": "临床干预方案与毒物防护指南"
    },
    {
        "keywords": ["暴露", "监测", "生物标志", "筛查"],
        "kbs": ["NHANES 营养与健康调查库", "ToxNet 毒理学数据网络", "CTD 比较毒理基因组学数据库"],
        "reason": "暴露生物标志物与健康监测数据"
    }
]


async def get_knowledge_bases() -> List[KnowledgeBase]:
    """获取知识库列表"""
    return KNOWLEDGE_BASES


def get_recommended_kbs(query: str, selected_kbs: List[str]) -> Optional[Dict[str, Any]]:
    """获取推荐的知识库"""
    for rule in KB_RECOMMENDATION_RULES:
        if any(keyword in query or keyword.lower() in query.lower() for keyword in rule["keywords"]):
            recommended = [kb for kb in rule["kbs"] if kb not in selected_kbs]
            if recommended:
                return {"kbs": recommended, "reason": rule["reason"]}

    # 默认推荐
    all_kb_names = [kb.name for kb in KNOWLEDGE_BASES]
    fallback = [kb for kb in all_kb_names if kb not in selected_kbs][:2]
    if fallback:
        return {"kbs": fallback, "reason": "扩展检索以补充更多维度的毒理学证据"}

    return None


def retrieve_knowledge(query: str, selected_kbs: List[str]) -> Dict[str, Any]:
    """检索知识库"""
    matched_metal = None

    # 匹配金属关键词
    for key, data in MOCK_KNOWLEDGE.items():
        if key in query or data["name"].split(" ")[1].lower() in query.lower():
            matched_metal = data
            break

    if matched_metal:
        return {
            "found": True,
            "data": matched_metal,
            "cited_kbs": selected_kbs
        }

    return {
        "found": False,
        "data": None,
        "cited_kbs": selected_kbs
    }


from .dual_path_evidence_service import (
    execute_dual_path_search,
    build_rag_prompt_and_system,
    generate_expert_reasoning_answer,
    format_markdown_to_html
)
from .ollama_service import get_ollama_service


async def process_chat(request: ChatRequest) -> ChatResponse:
    """处理聊天请求 (集成双通路循证检索上下文 + 大模型/专家推理引擎生成规范答案)"""
    # 1. 执行真实双通路检索 (稀疏 Top-32 + 稠密 Top-32，评分去 fu 指数，P0/P1 独立提取)
    dual_result = execute_dual_path_search(request.message, top_k_per_channel=32)
    analysis = dual_result["analysis"]
    summary = dual_result["summary"]
    metals_text = "、".join(analysis.get("metals", [])) or "职业重金属复合暴露"
    intent_task = analysis.get("primary_task", "T01_EXPOSURE")

    # 2. 构建输入给模型的专业 RAG 上下文与系统 Prompt
    sys_prompt, user_prompt = build_rag_prompt_and_system(request.message, dual_result)

    # 3. 动态思考过程
    think_process = None
    if request.enable_deep_think:
        think_process = f"""
        <div style="color: #64748B; font-size: 0.9rem; line-height: 1.6;">
            <p>> 🔍 [问题意图与实体解析] 识别目标实体：{metals_text} | 意图任务类型：{intent_task} (进入重排公式 G(d,q))</p>
            <p>> ⚖️ [法定红线通道] 独立提取 P0/P1 国家法律与强制性标准 (GBZ 2.1 等，共 <strong>{summary.get('p0_p1_boundary_count', 0)}</strong> 条)，作为法定合规硬边界</p>
            <p>> 🔬 [双通路·稠密检索] BGE 语义向量编码与余弦相似度计算，召回 Top-<strong>{summary.get('dense_retrieved', 32)}</strong> 候选切块</p>
            <p>> 📑 [双通路·稀疏检索] FTS5 倒排索引与 BM25 关键词匹配，召回 Top-<strong>{summary.get('sparse_retrieved', 32)}</strong> 候选切块</p>
            <p>> ⚡ [Med-R²循证重排] RRF 融合语义 Sem(d,q) × 任务意图 G(d,q) × 证据先验 H(P) × 方法学 M(d,q) × 适用性 A(d,q) (已去除 fu 代理模型差分)</p>
            <p>> 🤖 [大模型循证推演] 将 P0/P1 硬约束与顶级切块注入上下文，驱动 <strong>{request.model}</strong> 综合生成规范答复</p>
        </div>
        """

    # 4. 驱动大模型进行深度推理生成规范答案
    ollama = get_ollama_service()
    is_ollama_online = ollama.check_connection()
    is_local_model = (
        request.model in ["deepseek-r1:latest", "qwen2.5:7b", "llama3.1:8b", "qwen2:7b"]
        or "deepseek" in request.model.lower()
        or "qwen" in request.model.lower()
        or "llama" in request.model.lower()
    )

    message = ""
    if is_ollama_online and is_local_model:
        # 使用选中的本地大模型执行真实 RAG 上下文推理
        target_model = request.model if request.model in ["qwen2.5:7b", "deepseek-r1:latest", "llama3.1:8b", "qwen2:7b"] else "qwen2.5:7b"
        llm_res = ollama.generate_rag_answer(
            prompt=user_prompt,
            system_prompt=sys_prompt,
            model=target_model,
            temperature=0.4,
            timeout=180
            timeout=120
        )
        if llm_res.get("success") and llm_res.get("answer"):
            message = format_markdown_to_html(llm_res["answer"])
            if llm_res.get("think_process"):
                think_process = llm_res["think_process"]
        else:
            # 本地模型异常或超时时，使用内建专家推理引擎保底
            message = generate_expert_reasoning_answer(request.message, dual_result)
    else:
        # 预训练模型模式 (如 XGBoost/DNN) 或 Ollama 离线时，调用高精度专家推理引擎生成
        message = generate_expert_reasoning_answer(request.message, dual_result)

    # 5. 添加推荐知识库
    recommendation = get_recommended_kbs(request.message, request.knowledge_bases)
    if recommendation:
        recommended_html = f"""
        <div class="kb-recommend">
            <div class="kb-rec-title">📚 推荐追加知识库 <span class="kb-rec-reason">{recommendation['reason']}</span></div>
            <div class="kb-rec-tags">{''.join([f'<span class="kb-rec-tag">{kb}</span>' for kb in recommendation['kbs']])}</div>
        </div>
        """
        message += recommended_html

    # 6. 顶级切块与候选切块
    top_ranked = dual_result.get("top_ranked", [])
    p0_p1_boundaries = dual_result.get("p0_p1_boundaries", [])
    sparse_hits = dual_result.get("sparse_hits", [])
    dense_hits = dual_result.get("dense_hits", [])

    return ChatResponse(
        message=message,
        think_process=think_process,
        cited_knowledge_bases=request.knowledge_bases,
        recommended_knowledge_bases=recommendation["kbs"] if recommendation else None,
        recommend_reason=recommendation["reason"] if recommendation else None,
        p0_p1_boundaries=p0_p1_boundaries,
        evidence_cards=top_ranked,
        sparse_hits=sparse_hits,
        dense_hits=dense_hits,
        dual_path_summary=summary
    )

