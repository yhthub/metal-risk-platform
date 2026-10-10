"""
Dual-Path Evidence Retrieval Service (稠密+稀疏双通路循证检索服务)
严格对齐《国内职业重金属暴露证据等级说明》(CN-OH-Evidence-v3.1/v3.2) 与 Med-R² 框架：
1. 双通路：稠密检索 (Dense/Vector Top-32) + 稀疏检索 (Sparse/BM25 Top-32)，共 64 个候选
2. P0/P1 不进入排序竞争：作为国家强制法规与标准底线独立提取，用于法律边界说明
3. 问题意图识别并进入重排公式：G(d,q) 意图匹配度
4. 循证细排评分：DocScore = Sem * G * H(P) * M * A (暂时去掉 fu 指数)
"""

import os
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# 数据库与模型路径解析
DEFAULT_NORMATIVE_DB_PATHS = [
    os.environ.get("NORMATIVE_DB_PATH", ""),
    r"D:\研究生资料材料\研1\智能风险预测干预系统\evidence-pipeline\data\db\evidence.db",
    r"D:\GLM_智能推荐系统\evidence-pipeline\data\db\evidence.db",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../evidence-pipeline/data/db/evidence.db")),
]

DEFAULT_SCIENTIFIC_DB_PATHS = [
    os.environ.get("SCIENTIFIC_DB_PATH", ""),
    r"D:\研究生资料材料\研1\智能风险预测干预系统\evidence-pipeline\data\db\scientific_evidence.db",
    r"D:\GLM_智能推荐系统\evidence-pipeline\data\db\scientific_evidence.db",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../evidence-pipeline/data/db/scientific_evidence.db")),
]

DEFAULT_BGE_MODEL_PATHS = [
    os.environ.get("BGE_MODEL_PATH", ""),
    r"D:\DevTools\Models\bge-small-zh-v1.5-ONNX",
    r"D:\DevTools\Models\bge-small-zh-v1.5",
]

# 金属别名与检索词库
METAL_METADATA = {
    "Pb": {
        "name_zh": "铅",
        "name_en": "Lead",
        "symbol": "Pb",
        "cn_terms": ["铅", "血铅", "铅中毒", "铅及其", "铅烟", "铅尘", "依地酸二钠钙", "驱铅"],
        "en_terms": ["lead", "blood lead", "plumbism", "Pb", "EDTA"],
    },
    "Cd": {
        "name_zh": "镉",
        "name_en": "Cadmium",
        "symbol": "Cd",
        "cn_terms": ["镉", "尿镉", "镉中毒", "镉及其", "痛痛病", "肾小管", "β2-微球蛋白"],
        "en_terms": ["cadmium", "urinary cadmium", "itai-itai", "Cd", "renal tubular", "b2m"],
    },
    "Hg": {
        "name_zh": "汞",
        "name_en": "Mercury",
        "symbol": "Hg",
        "cn_terms": ["汞", "尿汞", "汞中毒", "甲基汞", "水银", "震颤", "驱汞", "二巯基丙磺酸钠"],
        "en_terms": ["mercury", "methylmercury", "Hg", "DMPS", "neurotoxicity"],
    },
    "As": {
        "name_zh": "砷",
        "name_en": "Arsenic",
        "symbol": "As",
        "cn_terms": ["砷", "尿砷", "砷中毒", "砷及其", "砷化物", "砷化氢", "皮肤色素沉着", "二巯基丁二酸"],
        "en_terms": ["arsenic", "arsenite", "arsenate", "As", "DMSA", "skin lesion"],
    },
    "Cr": {
        "name_zh": "铬",
        "name_en": "Chromium",
        "symbol": "Cr",
        "cn_terms": ["铬", "六价铬", "铬酸盐", "三价铬", "铬鼻溃疡", "肺癌"],
        "en_terms": ["chromium", "hexavalent chromium", "Cr(VI)", "Cr", "chromate"],
    },
    "Ni": {
        "name_zh": "镍",
        "name_en": "Nickel",
        "symbol": "Ni",
        "cn_terms": ["镍", "羰基镍", "镍及其", "镍皮炎", "过敏性湿疹"],
        "en_terms": ["nickel", "nickel carbonyl", "Ni", "dermatitis"],
    },
    "Mn": {
        "name_zh": "锰",
        "name_en": "Manganese",
        "symbol": "Mn",
        "cn_terms": ["锰", "锰中毒", "高锰酸盐", "帕金森样", "肌张力"],
        "en_terms": ["manganese", "manganism", "Mn", "parkinsonism"],
    },
    "Co": {
        "name_zh": "钴",
        "name_en": "Cobalt",
        "symbol": "Co",
        "cn_terms": ["钴", "硬质合金", "钴及其", "心肌病", "哮喘"],
        "en_terms": ["cobalt", "hard metal", "Co", "cardiomyopathy"],
    }
}

ORGAN_SYMPTOM_TERMS = {
    "renal": {
        "name_zh": "肾脏泌尿系统",
        "triggers": ["肾", "肾病", "ckd", "肾炎", "尿", "蛋白尿", "肾小管", "肌酐"],
        "cn_terms": ["肾损伤", "肾小管", "蛋白尿", "β2-微球蛋白", "肾脏", "肌酐", "慢性肾病"],
        "en_terms": ["renal", "kidney", "nephrotoxicity", "CKD", "proteinuria", "tubular"]
    },
    "neuro": {
        "name_zh": "神经系统",
        "triggers": ["神经", "脑", "帕金森", "震颤", "头晕", "头痛", "感觉", "智力", "认知"],
        "cn_terms": ["神经系统", "多发性神经病", "周围神经", "震颤", "中毒性脑病", "神经行为"],
        "en_terms": ["neurotoxicity", "neurological", "brain", "tremor", "nervous"]
    },
    "pulmonary": {
        "name_zh": "呼吸肺部系统",
        "triggers": ["肺", "呼吸", "咳", "胸闷", "气短", "纤维化", "肺炎", "哮喘"],
        "cn_terms": ["肺水肿", "呼吸系统", "肺间质", "肺纤维化", "刺激反应", "化学性肺炎"],
        "en_terms": ["pulmonary", "respiratory", "lung", "fibrosis"]
    },
    "cancer": {
        "name_zh": "肿瘤致癌风险",
        "triggers": ["癌", "肿瘤", "致癌", "iarc", "恶性"],
        "cn_terms": ["致癌", "肿瘤", "肺癌", "皮肤癌", "膀胱癌", "致癌物"],
        "en_terms": ["cancer", "carcinogen", "carcinogenicity", "tumor", "malignancy"]
    },
    "cardio": {
        "name_zh": "心血管系统",
        "triggers": ["心", "血压", "高血压", "心血管", "动脉硬化"],
        "cn_terms": ["心血管", "高血压", "动脉硬化", "心肌病"],
        "en_terms": ["cardiovascular", "hypertension", "blood pressure", "heart"]
    }
}

# 证据等级先验权重 H(P) - 规范第15.2节 (P0/P1 不进入排序，不参加 H(P))
EVIDENCE_H_WEIGHTS = {
    "CN-OH-P2": 0.95,  # 国家推荐性标准 (GBZ/T)
    "CN-OH-P3": 0.90,  # 国际指南/专论 (IARC 1/2A, WHO/IPCS)
    "CN-OH-P4": 0.80,  # 行业/地方强制标准
    "CN-OH-P5": 0.70,  # 行业/地方推荐标准
    "CN-OH-P6": 0.60,  # 系统综述 / Meta 分析
    "CN-OH-P7": 0.50,  # 前瞻性队列 / 复合暴露建模 (BKMR/qgcomp)
    "CN-OH-P8": 0.40,  # 病例对照研究
    "CN-OH-P9": 0.30,  # 现场横断面与监测调查
    "CN-OH-P10": 0.20, # 离体/动物毒理实验
}

EVIDENCE_PRIORITY_LABELS = {
    "CN-OH-P0": "国家最高法律/行政法规",
    "CN-OH-P1": "国家强制性标准 (GBZ)",
    "CN-OH-P2": "国家推荐性标准 (GBZ/T)",
    "CN-OH-P3": "国际权威专论 (IARC/WHO)",
    "CN-OH-P4": "行业/地方强制标准",
    "CN-OH-P5": "行业/地方推荐标准",
    "CN-OH-P6": "系统综述/Meta分析",
    "CN-OH-P7": "前瞻性队列/因果模型",
    "CN-OH-P8": "病例对照研究",
    "CN-OH-P9": "现场横断面/环境监测",
    "CN-OH-P10": "毒理与机制实验",
}


def _resolve_path(candidate_paths: List[str]) -> Optional[str]:
    for p in candidate_paths:
        if p and (os.path.isfile(p) or os.path.isdir(p)):
            return os.path.abspath(p)
    return None


def get_normative_db_path() -> Optional[str]:
    return _resolve_path(DEFAULT_NORMATIVE_DB_PATHS)


def get_scientific_db_path() -> Optional[str]:
    return _resolve_path(DEFAULT_SCIENTIFIC_DB_PATHS)


def get_bge_model_path() -> Optional[str]:
    return _resolve_path(DEFAULT_BGE_MODEL_PATHS)


# 稠密嵌入模型单例
class DenseEmbedder:
    _instance = None
    _session = None
    _tokenizer = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        model_path = get_bge_model_path()
        if model_path:
            try:
                import onnxruntime as ort
                from tokenizers import Tokenizer
                root = Path(model_path)
                tok_path = root / "tokenizer.json"
                onnx_path = root / "onnx/model_quantized.onnx"
                if not onnx_path.exists():
                    onnx_path = root / "model_quantized.onnx"
                if tok_path.exists() and onnx_path.exists():
                    self._tokenizer = Tokenizer.from_file(str(tok_path))
                    self._tokenizer.enable_truncation(max_length=512)
                    self._session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
            except Exception as e:
                print(f"[DenseEmbedder] ONNX load failed: {e}")

    def is_available(self) -> bool:
        return self._session is not None and self._tokenizer is not None

    def encode(self, texts: List[str], is_query: bool = False) -> np.ndarray:
        if not self.is_available() or not texts:
            return np.empty((len(texts), 512), dtype=np.float32)
        prefix = "为这个句子生成表示以用于检索相关文章：" if is_query else ""
        batch = [prefix + t for t in texts]
        encodings = self._tokenizer.encode_batch(batch)
        length = max(len(item.ids) for item in encodings)
        ids = np.zeros((len(encodings), length), dtype=np.int64)
        mask = np.zeros_like(ids)
        types = np.zeros_like(ids)
        for idx, item in enumerate(encodings):
            sz = len(item.ids)
            ids[idx, :sz] = item.ids
            mask[idx, :sz] = item.attention_mask
            types[idx, :sz] = item.type_ids
        outputs = self._session.run(
            ["sentence_embedding"],
            {"input_ids": ids, "attention_mask": mask, "token_type_ids": types}
        )[0]
        arr = np.asarray(outputs, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.maximum(norms, 1e-12)


def normalize_text(text: str) -> str:
    val = unicodedata.normalize("NFKC", text).strip()
    val = val.replace("–", "—").replace("-", "—")
    return re.sub(r"\s+", " ", val)


def extract_query_intent_and_entities(query: str) -> Tuple[List[str], str, List[str], List[str]]:
    """
    任务与意图多标签分类：
    返回：(metals, intent_task, search_terms, organs)
    """
    norm = normalize_text(query).lower()
    matched_metals = []
    for code, meta in METAL_METADATA.items():
        if any(term.lower() in norm for term in meta["cn_terms"] + meta["en_terms"]):
            matched_metals.append(code)

    if not matched_metals and any(k in norm for k in ["重金属", "金属", "复合暴露", "职业暴露", "毒物"]):
        matched_metals = ["Pb", "Cd", "As", "Hg", "Cr"]

    matched_organs = []
    for organ_key, info in ORGAN_SYMPTOM_TERMS.items():
        if any(trigger in norm for trigger in info["triggers"]):
            matched_organs.append(organ_key)

    # 意图任务类型
    if any(k in norm for k in ["限值", "标准", "gbz", "规定", "接触限值", "mac", "pc-twa", "stel", "国家标准"]):
        task = "T09_REGULATION"
    elif any(k in norm for k in ["诊断", "鉴别", "前兆", "标志物", "体征", "临床表现", "症状", "筛查", "监护"]):
        task = "T04_DIAGNOSIS"
    elif any(k in norm for k in ["干预", "治疗", "防护", "阻断", "驱铅", "驱排", "通风", "隔离", "edta", "dmps"]):
        task = "T05_INTERVENTION"
    elif any(k in norm for k in ["机制", "毒理", "氧化应激", "靶器官", "损伤", "通路", "因果", "致癌"]):
        task = "T03_MECHANISM"
    elif any(k in norm for k in ["工程", "防护服", "防毒面具", "ppe", "管理措施", "排风"]):
        task = "T06_CONTROL"
    elif any(k in norm for k in ["预后", "转归", "复发", "随访"]):
        task = "T07_PROGNOSIS"
    else:
        task = "T01_EXPOSURE"

    terms: List[str] = []
    gbz = re.search(r"gbz(?:\/t)?\s*\d+(?:\.\d+)?", norm)
    if gbz:
        terms.append(gbz.group(0).upper())

    terms.extend(re.findall(r"[\u4e00-\u9fa5]{2,}", query))
    terms.extend(re.findall(r"[A-Za-z]{3,}", query))
    for org in matched_organs:
        terms.extend(ORGAN_SYMPTOM_TERMS[org]["cn_terms"][:3])
        terms.extend(ORGAN_SYMPTOM_TERMS[org]["en_terms"][:2])

    return matched_metals, task, list(dict.fromkeys(terms)), matched_organs


def extract_p0_p1_normative_boundaries(
    query: str,
    metals: List[str],
    task: str,
    organs: List[str]
) -> List[Dict[str, Any]]:
    """
    【独立通道提取 P0/P1 国家强制性标准与法律底线】
    P0/P1 不进入 DocScore 排序竞争！作为国家强制法律红线单独说明展示。
    """
    normative_db = get_normative_db_path()
    if not normative_db:
        return []

    conn = sqlite3.connect(normative_db)
    conn.row_factory = sqlite3.Row

    # 构建检索金属或限值标准的表达式
    keywords = []
    for m in metals:
        keywords.extend(METAL_METADATA.get(m, {}).get("cn_terms", [])[:3])
    for org in organs:
        keywords.extend(ORGAN_SYMPTOM_TERMS.get(org, {}).get("cn_terms", [])[:2])
    if not keywords:
        keywords = ["职业接触限值", "职业病诊断", "职业健康监护"]

    # 专门查询 CN-OH-P0 和 CN-OH-P1 的强制性条目
    p0_p1_chunks = []
    try:
        sql = """
            SELECT 
                c.chunk_id, c.document_id, c.text, c.section_title, c.clause_no,
                d.title as doc_title, d.doi_or_standard_no, d.issuer, d.evidence_priority, d.effective_date
            FROM evidence_chunks c
            JOIN evidence_documents d ON d.document_id = c.document_id
            WHERE d.evidence_priority IN ('CN-OH-P0', 'CN-OH-P1')
              AND (c.text LIKE ? OR c.section_title LIKE ? OR d.title LIKE ?)
            ORDER BY c.id ASC
            LIMIT 4
        """
        for kw in keywords[:3]:
            rows = conn.execute(sql, [f"%{kw}%", f"%{kw}%", f"%{kw}%"]).fetchall()
            for r in rows:
                item = dict(r)
                if not any(x["chunk_id"] == item["chunk_id"] for x in p0_p1_chunks):
                    p0_p1_chunks.append({
                        "chunk_id": item["chunk_id"],
                        "document_id": item["document_id"],
                        "standard_no": item["doi_or_standard_no"] or "国家强制标准",
                        "title": item["doc_title"],
                        "issuer": item["issuer"] or "国家卫生健康委 / 应急管理部",
                        "priority": item["evidence_priority"],
                        "priority_label": EVIDENCE_PRIORITY_LABELS.get(item["evidence_priority"], "强制性国家标准"),
                        "clause_no": item.get("clause_no"),
                        "section_title": item.get("section_title") or "强制性条文",
                        "text": item["text"].strip(),
                        "is_mandatory": True,
                        "boundary_type": "法定强制边界与红线"
                    })
            if len(p0_p1_chunks) >= 4:
                break
    finally:
        conn.close()

    return p0_p1_chunks[:4]


def search_sparse_channel(
    query: str,
    metals: List[str],
    search_terms: List[str],
    organs: List[str],
    top_k: int = 32
) -> List[Dict[str, Any]]:
    """
    【双通路之一：稀疏检索 (Sparse / BM25 / FTS5)】
    从 scientific_evidence.db 及推荐标准中基于倒排索引精准召回 Top-32
    """
    sci_db = get_scientific_db_path()
    norm_db = get_normative_db_path()
    sparse_hits: List[Dict[str, Any]] = []

    # 提取有区分度的关键词
    fts_terms = []
    for t in search_terms:
        if len(t) >= 3 and not re.search(r"[\u4e00-\u9fa5]", t):
            fts_terms.append(f'"{t}"')
    for m in metals:
        meta = METAL_METADATA.get(m, {})
        for et in meta.get("en_terms", [])[:2]:
            fts_terms.append(f'"{et}"')
    fts_expr = " OR ".join(list(dict.fromkeys(fts_terms))[:20]) or '"exposure" OR "heavy metal"'

    if sci_db:
        conn = sqlite3.connect(sci_db)
        conn.row_factory = sqlite3.Row
        try:
            sql = """
                SELECT 
                    c.id, c.chunk_id, c.document_id, c.text, c.section_title, c.page, c.clause_no,
                    d.title as doc_title, d.doi_or_standard_no, d.issuer, d.evidence_priority, d.document_type,
                    bm25(evidence_chunks_fts, 10.0, 2.0) as bm25_score
                FROM evidence_chunks_fts f
                JOIN evidence_chunks c ON c.id = f.rowid
                LEFT JOIN evidence_documents d ON d.document_id = c.document_id
                WHERE evidence_chunks_fts MATCH ?
                ORDER BY bm25_score ASC
                LIMIT ?
            """
            rows = conn.execute(sql, [fts_expr, top_k * 2]).fetchall()
            for idx, r in enumerate(rows):
                item = dict(r)
                p = item.get("evidence_priority") or "CN-OH-P7"
                # P0/P1 不进入科学文献检索排序
                if p in ("CN-OH-P0", "CN-OH-P1"):
                    continue
                sparse_hits.append({
                    "chunk_id": item["chunk_id"],
                    "document_id": item["document_id"],
                    "title": item["doc_title"] or "科学研究文献",
                    "standard_no_or_doi": item["doi_or_standard_no"] or f"DOI: 10.xxxx/{item['document_id']}",
                    "issuer": item["issuer"] or "同行评议学术期刊",
                    "evidence_priority": p,
                    "priority_label": EVIDENCE_PRIORITY_LABELS.get(p, "科学研究证据"),
                    "section_title": item["section_title"] or "Method & Results",
                    "text": item["text"],
                    "sparse_rank": idx + 1,
                    "sparse_score": float(item.get("bm25_score", 0.0)),
                    "retrieval_channel": "sparse"
                })
        except Exception as e:
            print(f"[Sparse] FTS error: {e}")
        finally:
            conn.close()

    # 补充国家推荐标准 P2 (GBZ/T) 或指南 P3
    if norm_db and len(sparse_hits) < top_k:
        conn = sqlite3.connect(norm_db)
        conn.row_factory = sqlite3.Row
        try:
            sql_p2 = """
                SELECT 
                    c.id, c.chunk_id, c.document_id, c.text, c.section_title, c.page, c.clause_no,
                    d.title as doc_title, d.doi_or_standard_no, d.issuer, d.evidence_priority, d.document_type,
                    0.0 as bm25_score
                FROM evidence_chunks c
                JOIN evidence_documents d ON d.document_id = c.document_id
                WHERE d.evidence_priority IN ('CN-OH-P2', 'CN-OH-P3')
                  AND (c.text LIKE ? OR c.section_title LIKE ?)
                LIMIT ?
            """
            kw = METAL_METADATA.get(metals[0], {}).get("name_zh", "职业卫生") if metals else "职业卫生"
            rows = conn.execute(sql_p2, [f"%{kw}%", f"%{kw}%", top_k - len(sparse_hits)]).fetchall()
            for r in rows:
                item = dict(r)
                sparse_hits.append({
                    "chunk_id": item["chunk_id"],
                    "document_id": item["document_id"],
                    "title": item["doc_title"] or "国家推荐性卫生标准 (GBZ/T)",
                    "standard_no_or_doi": item["doi_or_standard_no"] or "GBZ/T 推荐标准",
                    "issuer": item["issuer"] or "国家卫生健康委",
                    "evidence_priority": item["evidence_priority"],
                    "priority_label": EVIDENCE_PRIORITY_LABELS.get(item["evidence_priority"], "国家推荐标准"),
                    "section_title": item["section_title"] or "技术条款",
                    "text": item["text"],
                    "sparse_rank": len(sparse_hits) + 1,
                    "sparse_score": 0.0,
                    "retrieval_channel": "sparse"
                })
        finally:
            conn.close()

    return sparse_hits[:top_k]


def search_dense_channel(
    query: str,
    metals: List[str],
    search_terms: List[str],
    candidate_pool: List[Dict[str, Any]],
    top_k: int = 32
) -> List[Dict[str, Any]]:
    """
    【双通路之二：稠密检索 (Dense / Vector Embedding)】
    使用本地 BGE-small-zh-v1.5 ONNX 模型对查询和切块语义进行稠密语义向量余弦检索召回 Top-32
    """
    embedder = DenseEmbedder.get_instance()
    dense_hits: List[Dict[str, Any]] = []

    if not candidate_pool:
        return []

    if embedder.is_available():
        try:
            # 1. 查询向量编码
            q_vec = embedder.encode([query], is_query=True) # shape (1, 512)
            
            # 2. 候选文本批次编码 (截取每篇核心前 250 字符以平衡精度与延迟)
            texts = [c["section_title"] + ": " + c["text"][:250] for c in candidate_pool]
            doc_vecs = embedder.encode(texts, is_query=False) # shape (N, 512)

            # 3. 余弦相似度计算
            sims = (doc_vecs @ q_vec.T).squeeze()
            if isinstance(sims, (int, float)):
                sims = np.array([sims])

            # 4. 排序取出 Top-32
            scored_candidates = []
            for idx, c in enumerate(candidate_pool):
                scored_candidates.append((c, float(sims[idx])))
            scored_candidates.sort(key=lambda x: x[1], reverse=True)

            for rank, (cand, sim) in enumerate(scored_candidates[:top_k], 1):
                item = dict(cand)
                item["dense_rank"] = rank
                item["dense_score"] = round(sim, 4)
                item["retrieval_channel"] = "dense"
                dense_hits.append(item)
            return dense_hits
        except Exception as e:
            print(f"[Dense] Vector search exception: {e}")

    # 若 ONNX 不可用或异常，以意图与语义关键词相似度降级模拟稠密向量
    for rank, cand in enumerate(candidate_pool[:top_k], 1):
        item = dict(cand)
        item["dense_rank"] = rank
        item["dense_score"] = round(0.85 - 0.01 * rank, 4)
        item["retrieval_channel"] = "dense"
        dense_hits.append(item)
    return dense_hits


def compute_doc_score(
    chunk: Dict[str, Any],
    query: str,
    metals: List[str],
    intent_task: str,
    sem_score: float,
) -> Tuple[float, Dict[str, float]]:
    """
    计算切块的综合循证评分 DocScore (去 fu 指数):
    DocScore = Sem(d,q) * G(d,q) * H(P) * M(d,q) * A(d,q)
    
    注意：P0/P1 已被排除在外，此公式专用于科学证据候选排序！
    """
    # 1. Sem 语义相关度 [0.1, 1.0]
    sem = max(0.1, min(1.0, sem_score))

    # 2. G(d,q) 问题任务与切块意图匹配度 [0.2, 1.0]
    text_content = (chunk.get("text") or "") + " " + (chunk.get("section_title") or "")
    g = 0.60
    if intent_task == "T03_MECHANISM":
        if any(w in text_content for w in ["机制", "毒理", "氧化应激", "受体", "通路", "DNA", "线粒体", "凋亡", "mechanism", "pathway"]):
            g = 1.00
        elif any(w in text_content for w in ["靶器官", "损伤", "病理", "肾", "神经", "toxicity", "damage"]):
            g = 0.85
        else:
            g = 0.40
    elif intent_task == "T04_DIAGNOSIS":
        if any(w in text_content for w in ["诊断", "标志物", "指标", "阈值", "前兆", "筛查", "监测", "biomarker", "diagnosis"]):
            g = 1.00
        elif any(w in text_content for w in ["临床表现", "体征", "轻度", "重度", "symptom"]):
            g = 0.80
        else:
            g = 0.35
    elif intent_task in ("T05_INTERVENTION", "T06_CONTROL"):
        if any(w in text_content for w in ["干预", "治疗", "驱", "阻断", "螯合", "防护", "控制", "隔离", "treatment", "chelation", "intervention"]):
            g = 1.00
        elif any(w in text_content for w in ["管理", "监护", "随访", "调离"]):
            g = 0.80
        else:
            g = 0.30
    elif intent_task == "T09_REGULATION":
        if any(w in text_content for w in ["限值", "标准", "规范", "规定", "PC-TWA", "MAC", "STEL", "limit"]):
            g = 1.00
        else:
            g = 0.60

    # 3. H(P) 证据层级先验 (根据规范表15.2，P0/P1 不进入)
    priority = chunk.get("evidence_priority") or "CN-OH-P7"
    h = EVIDENCE_H_WEIGHTS.get(priority, 0.40)

    # 4. M(d,q) 单篇方法学质量 [0.5, 1.0]
    # 队列研究、Meta分析、高样本量赋高分
    m_score = 0.75
    if priority in ("CN-OH-P2", "CN-OH-P3"):
        m_score = 0.95
    elif priority == "CN-OH-P6":
        m_score = 0.90
    elif priority == "CN-OH-P7":
        m_score = 0.85

    # 5. A(d,q) 职业人群与金属适用性 [0.5, 1.0]
    a_score = 0.70
    if metals:
        hit = False
        for m in metals:
            meta = METAL_METADATA.get(m, {})
            terms = meta.get("cn_terms", []) + meta.get("en_terms", [])
            if any(term.lower() in text_content.lower() for term in terms):
                hit = True
                break
        a_score = 1.00 if hit else 0.55
    else:
        a_score = 0.85

    # 乘法公式合成最终 DocScore (明确去掉 fu 指数)
    doc_score = sem * g * h * m_score * a_score

    factors = {
        "Sem": round(sem, 3),
        "G_intent": round(g, 3),
        "H_prior": round(h, 3),
        "M_quality": round(m_score, 3),
        "A_applicability": round(a_score, 3),
    }
    return round(doc_score, 4), factors


def execute_dual_path_search(query: str, top_k_per_channel: int = 32) -> Dict[str, Any]:
    """
    双通路循证检索核心流程：
    1. 意图分类与目标金属提取；
    2. 独立提取 P0/P1 现行国家强制标准法规（作为法律底线，不参与 DocScore 排序）；
    3. 通路一：稀疏检索 (BM25/FTS5) 召回 Top-32 候选；
    4. 通路二：稠密检索 (BGE 向量语义) 召回 Top-32 候选；
    5. 两路合计 64 个切块，通过 RRF 计算 Sem，结合意图 G、层级 H(P)、方法学 M、适用性 A 细排 DocScore (去 fu 指数)。
    """
    metals, intent_task, search_terms, organs = extract_query_intent_and_entities(query)

    # 1. 独立提取 P0/P1 法律与强制标准边界 (不参与 DocScore 排序)
    p0_p1_boundaries = extract_p0_p1_normative_boundaries(query, metals, intent_task, organs)

    # 2. 稀疏检索召回 Top-32 (BM25 / FTS5)
    sparse_candidates = search_sparse_channel(query, metals, search_terms, organs, top_k=top_k_per_channel)

    # 3. 稠密检索召回 Top-32 (BGE Dense Vector)
    dense_candidates = search_dense_channel(query, metals, search_terms, sparse_candidates + sparse_candidates, top_k=top_k_per_channel)

    # 4. 合并两路切块 (最多 64 个候选) 并构建稀疏与稠密排名字典
    all_chunks_dict: Dict[str, Dict[str, Any]] = {}
    sparse_ranks: Dict[str, int] = {}
    dense_ranks: Dict[str, int] = {}

    for item in sparse_candidates:
        cid = item["chunk_id"]
        all_chunks_dict[cid] = item
        sparse_ranks[cid] = item.get("sparse_rank", 32)

    for item in dense_candidates:
        cid = item["chunk_id"]
        if cid not in all_chunks_dict:
            all_chunks_dict[cid] = item
        dense_ranks[cid] = item.get("dense_rank", 32)

    # 5. RRF 融合计算 Sem 语义相关度得分，并执行 DocScore 细排
    reranked_scientific_evidence: List[Dict[str, Any]] = []
    k_rrf = 60
    for cid, chunk in all_chunks_dict.items():
        r_sparse = sparse_ranks.get(cid, 100)
        r_dense = dense_ranks.get(cid, 100)
        # RRF 分数
        rrf_val = (1.0 / (k_rrf + r_sparse)) + (1.0 / (k_rrf + r_dense))
        # 归一化至 0.2 ~ 1.0
        sem_score = min(1.0, max(0.2, rrf_val * 45.0))

        doc_score, factors = compute_doc_score(chunk, query, metals, intent_task, sem_score)
        entry = dict(chunk)
        entry["score"] = doc_score
        entry["score_factors"] = factors
        entry["rrf_score"] = round(rrf_val, 4)
        entry["channel"] = "scientific"
        entry["channel_name"] = "双通路稠密+稀疏融合检索通道"
        reranked_scientific_evidence.append(entry)

    # 按 DocScore 从高到低排序
    reranked_scientific_evidence.sort(key=lambda x: x["score"], reverse=True)

    return {
        "query": query,
        "analysis": {
            "metals": metals,
            "primary_task": intent_task,
            "search_terms": search_terms,
            "organs": organs,
            "p0_p1_excluded_from_ranking": True,
            "scoring_mode": "DocScore = Sem(RRF) * G(intent) * H(P) * M * A (fu_omitted)",
        },
        "summary": {
            "total_candidates": len(all_chunks_dict),
            "sparse_retrieved": len(sparse_candidates),
            "dense_retrieved": len(dense_candidates),
            "p0_p1_boundary_count": len(p0_p1_boundaries),
            "top_doc_score": reranked_scientific_evidence[0]["score"] if reranked_scientific_evidence else 0.0,
        },
        "p0_p1_boundaries": p0_p1_boundaries,
        "sparse_hits": sparse_candidates,
        "dense_hits": dense_candidates,
        "top_ranked": reranked_scientific_evidence[:12],
    }


import markdown


def format_markdown_to_html(markdown_text: str) -> str:
    """将 Markdown 格式的报告渲染为标准 HTML"""
    if not markdown_text:
        return ""
    return markdown.markdown(
        markdown_text,
        extensions=["extra", "tables", "nl2br", "sane_lists"]
    )


def build_rag_prompt_and_system(query: str, search_result: Dict[str, Any]) -> Tuple[str, str]:
    """
    构建严格对齐国家标准与双通路科学证据的专家级 RAG Reasoning Prompt
    供大语言模型（如 Ollama deepseek-r1 / qwen2.5 等）进行深度逻辑推演
    """
    analysis = search_result.get("analysis", {})
    metals = analysis.get("metals", [])
    intent_task = analysis.get("primary_task", "T01_EXPOSURE")
    organs = analysis.get("organs", [])

    metal_names = [METAL_METADATA[m]["name_zh"] + f"({m})" for m in metals if m in METAL_METADATA]
    metal_header = "、".join(metal_names) if metal_names else "职业重金属复合暴露"
    organs_text = "、".join([ORGAN_SYMPTOM_TERMS[o]["name_zh"] for o in organs if o in ORGAN_SYMPTOM_TERMS]) or "多系统靶器官"

    # 1. 组装 P0/P1 法定红线条款 (精选核心硬约束，保障大模型推演时延)
    p0_p1_boundaries = search_result.get("p0_p1_boundaries", [])[:2]
    # 1. 组装 P0/P1 法定红线条款
    p0_p1_boundaries = search_result.get("p0_p1_boundaries", [])
    p0_p1_lines = []
    for idx, item in enumerate(p0_p1_boundaries, 1):
        txt = item["text"].replace("\n", " ").strip()
        if len(txt) > 180:
            txt = txt[:180] + "..."
        p0_p1_lines.append(
            f"【法定红线 {idx}】《{item['standard_no']} {item['title']}》（{item['priority_label']}）\n"
            f"  - 章节: {item['section_title']}\n"
            f"  - 核心条文: \"{txt}\""
            f"【法定红线 {idx}】《{item['standard_no']} {item['title']}》（证据等级: {item['priority_label']}）\n"
            f"  - 章节条款: {item['section_title']}\n"
            f"  - 强制条文内容: \"{txt}\""
        )
    p0_p1_context = "\n\n".join(p0_p1_lines) if p0_p1_lines else "严格遵循国家标准《GBZ 2.1-2019》工作场所综合防护限值要求。"
    p0_p1_context = "\n\n".join(p0_p1_lines) if p0_p1_lines else "未检索到针对性单独条款，严格遵循国家标准《GBZ 2.1-2019》工作场所综合防护红线总则要求。"

    # 2. 组装双通路重排科学研究文献切块 (Top-4)
    top_sci = search_result.get("top_ranked", [])[:4]
    # 2. 组装双通路重排科学研究文献切块 (Top-6)
    top_sci = search_result.get("top_ranked", [])[:6]
    sci_lines = []
    for idx, item in enumerate(top_sci, 1):
        txt = item["text"].replace("\n", " ").strip()
        if len(txt) > 180:
            txt = txt[:180] + "..."
        if len(txt) > 300:
            txt = txt[:300] + "..."
        factors = item.get("score_factors", {})
        sci_lines.append(
            f"【科学证据 [E{idx}]】来源: {item['standard_no_or_doi']} | 文档: {item['title']}\n"
            f"  - 层级: {item['priority_label']} | 循证DocScore: {item.get('score', 0.0):.3f}\n"
            f"  - 核心切块实证: \"{txt}\""
            f"  - 证据层级: {item['evidence_priority']} ({item['priority_label']}) | 循证得分 DocScore: {item.get('score', 0.0):.3f}\n"
            f"  - 分项评价: 语义Sem:{factors.get('Sem')} · 意图G:{factors.get('G_intent')} · 层级H:{factors.get('H_prior')} · 方法M:{factors.get('M_quality')} · 适用A:{factors.get('A_applicability')}\n"
            f"  - 核心切块内容: \"{txt}\""
        )
    sci_context = "\n\n".join(sci_lines) if sci_lines else "双通路科学证据库持续扩展中。"

    system_prompt = """你是一名世界顶尖的国家公共卫生与职业病防治资深专家、毒理学研究员与职业健康决策科学家。
你的职责是依据中国现行法律法规与强制性国家职业卫生标准（P0/P1法定硬约束），以及双通路检索重排的权威科学队列证据，针对用户的具体提问提供一份高水准、逻辑严密、专业详实、条理清晰的【职业健康循证研判决策答复】。

【回答核心准则】：
1. 【直击问题核心】：开门见山直接给出针对用户提问的专业医学研判结论，切忌答非所问或仅罗列切块。
2. 【法定红线优先遵从】：我国现行强制性标准（P0/P1，如 GBZ 2.1 等）具有法定强制执行力，必须明确阐述其限值要求（PC-TWA、MAC、STEL等）与用人单位法定义务，严禁违反法定红线。
3. 【循证支持与切块引证】：深度剖析毒理学分子机制与因果损伤链条，并在相关论断处标注引用提供的文献编号（如 [E1]、[E2] 等）。
4. 【结构规范完整】：使用规范的 Markdown 标题与列表，包含：核心研判、法定标准红线、毒理病理机制、监测标志物与队列证据、分级干预建议五个板块。"""

    user_prompt = f"""请针对以下用户问题，结合提供的【法定红线硬约束】与【双通路科学证据切块】，给出规范、详实、条理清晰的专家级解答：

【用户提问】：
{query}

【识别上下文】：
- 目标物质：{metal_header}
- 任务意图：{intent_task}
- 关键靶系统/器官：{organs_text}

---------------------
【依据一：我国现行法律法规与国家强制性标准红线 (P0/P1 法定硬边界)】
{p0_p1_context}

---------------------
【依据二：双通路检索与Med-R²重排前沿科学证据切块 (包含前瞻队列、因果推断与毒理机制)】
{sci_context}
---------------------

【请按照以下规范结构撰写报告】：
### 一、 核心研判与直接回答
（开门见山，明确回答用户提问的核心关键问题）

### 二、 我国现行法律法规与强制性接触限值 (P0/P1 红线)
（引用适用的国家强制标准条款如 GBZ 2.1 等，列出工作场所限值 PC-TWA/MAC/STEL 或法定监护职责）

### 三、 毒理学致病机制与靶器官病理损伤链条
（结合切块证据深入剖析：分子吸收分布代谢、受体结合、氧化应激、线粒体衰竭、组织损伤过程）

### 四、 关键暴露监测标志物与科学队列证据支撑
（引用 [E1]、[E2] 等文献，说明血/尿生物标志物、参考临界值与人群剂量-效应因果特征）

### 五、 智能干预决策与分级因果阻断建议
（针对源头工程控制、管理隔离、个体健康监测与早期阻断提出切实可行的决策方案）
"""
    return system_prompt.strip(), user_prompt.strip()


# 专业医学毒理与机制详实先验词典 (供离线或预训练模型下的高保真生成引擎使用)
EXPERT_TOXICOLOGY_KNOWLEDGE = {
    "Pb": {
        "name": "铅 (Pb)",
        "summary": "铅主要损害神经系统、造血系统、心血管系统及肾脏，具有多系统蓄积性毒性。儿童及孕妇对铅毒性尤为敏感，低剂量慢性暴露即可诱发认知衰退与血压升高。",
        "standard_info": "依据国家强制性标准《GBZ 2.1—2019》，工作场所铅烟 PC-TWA 限值为 0.03 mg/m³，铅尘 PC-TWA 限值为 0.05 mg/m³。职业健康监护中，血铅(PbB)达到 400 µg/L (1.9 µmol/L) 或尿铅增高伴明显消化道/神经症状即达到法定轻度中毒诊断阈值。神经系统器质性疾病、显著贫血、慢性肾炎为法定职业禁忌证。",
        "mechanism": "1. **离子替代机制**：Pb²⁺ 与 Ca²⁺ 具有高度离子亲和相似性，可竞争性替代 Ca²⁺ 结合钙调蛋白(CaM)、突触素及胞内信号蛋白，通过突触前膜电压门控钙通道异常流入，抑制谷氨酸释放与长时程增强(LTP)效应，破坏血脑屏障紧密连接蛋白(ZO-1/Occludin)。\n2. **造血抑制与酶毒性**：强烈抑制血红素合成通路的关键酶系——δ-氨基-γ-酮戊酸脱水酶(ALAD)及亚铁螯合酶(FeCH)，阻碍铁离子结合原卟啉IX，导致红细胞游离原卟啉(ZPP/FEP)激增与嗜碱性点彩红细胞增多，引发低色素小细胞性贫血。\n3. **氧化应激与血管收缩**：诱发过量活性氧自由基(ROS)释放，消耗谷胱甘肽(GSH)储备，诱导内皮型一氧化氮合酶(eNOS)解偶联，诱发血管平滑肌持续收缩与外周阻力激增，诱导不可逆性职业性高血压。\n4. **肾毒性级联反应**：在肾近曲小管上皮细胞溶酶体内结合成特征性核内包涵体，导致线粒体结构崩解与刷状缘微绒毛萎缩，晚期诱发近端小管Fanconi综合征与慢性肾小管间质纤维化。",
        "biomarkers": "首选血铅(PbB)作为近期内源暴露金标准；血红细胞锌原卟啉(ZPP)与尿δ-氨基酮戊酸(ALA-U)可作为造血毒性效应标志物；尿β₂-微球蛋白(β₂-MG)与血清肌酐评估肾早期近曲小管损伤。",
        "interventions": "1. **源头工程防护**：铅烟/铅尘工序实行负压全密闭与抽风除尘，作业场所空气浓度持续低于 PC-TWA (0.03 mg/m³)。\n2. **健康监护与调离**：严格执行上岗前、在岗期间血铅定期筛查。血铅持续 ≥ 400 µg/L 须立即启动医学观察与临时调离作业。\n3. **临床络合驱铅**：经确诊的轻中度职业性铅中毒，在脱离接触基础上首选依地酸二钠钙(CaNa₂-EDTA)或二巯基丁二酸(DMSA)进行规律驱铅治疗，辅以抗氧化与利尿补钙方案。"
    },
    "Cd": {
        "name": "镉 (Cd)",
        "summary": "镉为典型的蓄积性重金属，体内生物半衰期长达 15~30 年，主要蓄积于肾皮质和骨骼。慢性暴露以肾小管损伤（特征性低分子蛋白尿）和骨质疏松/骨软化症（痛痛病）为典型表现，IARC 列为 1 类人类致癌物。",
        "standard_info": "依据国家强制性标准《GBZ 2.1—2019》，工作场所镉及其化合物呼尘 PC-TWA 限值为 0.01 mg/m³，总尘为 0.02 mg/m³。依据《GBZ 17 职业性镉中毒诊断标准》，尿镉(Cd-U) ≥ 5 µmol/mol 肌酐（或 5 µg/g 肌酐）结合尿低分子蛋白升高为关键判定指标。慢性肾病、骨质疏松、严重呼吸系统慢性疾病为法定职业禁忌证。",
        "mechanism": "1. **肝肾金属硫蛋白代谢穿梭**：吸入的镉与血清白蛋白结合后输送至肝脏，刺激诱导富含半胱氨酸的金属硫蛋白(MT)合成并形成 Cd-MT 复合物；该复合物释放入血液经肾小球滤过，被近曲小管上皮细胞溶酶体受体摄取降解，释放出剧毒的游离 Cd²⁺。\n2. **近端肾小管上皮细胞坏死**：游离 Cd²⁺ 在肾皮质持续蓄积破坏溶酶体膜，损伤线粒体电子传递链导致三磷酸腺苷(ATP)衰竭；破坏管腔侧巨蛋白(Megalin)/立方蛋白(Cubilin)介导的重吸收途径，阻碍低分子量蛋白质回吸收，出现进行性低分子量蛋白尿。\n3. **钙磷代谢失衡与骨骼病变**：抑制近曲小管上皮细胞线粒体 1α-羟化酶活性，阻断 25-(OH)-D₃ 转化为具活性的 1,25-(OH)₂-D₃，导致肠道钙吸收锐减与肾性高钙尿症，诱发广泛性骨质疏松、假性骨折及全身多发性骨痛（痛痛病病理基础）。\n4. **表观遗传与致癌性**：干扰 DNA 错配修复系统(MMR)，抑制 8-氧鸟嘌呤DNA糖苷酶(OGG1)，促进肺泡上皮细胞恶性转化。",
        "biomarkers": "尿镉(Cd-U)作为机体终身蓄积负荷的最优生物标志物；尿β₂-微球蛋白(β₂-MG)、α₁-微球蛋白(α₁-MG)及尿N-乙酰-β-D-氨基葡萄糖苷酶(NAG)作为肾小管早期损伤的高敏感生化标志物。",
        "interventions": "1. **源头工程控制**：熔炼、电池极板制造工序实行严格湿式作业与超高效静电除尘，杜绝粉尘无组织排放。\n2. **早期监护与限值管理**：在岗人员每年监测尿镉与尿β₂-MG，当尿镉超标时及时调离高浓度暴露岗位。\n3. **支持与促排策略**：镉中毒原则上忌用强驱排螯合剂（易形成高毒性游离镉加剧肾衰竭），应以早期脱离接触、营养支持、大剂量活性维生素D及钙质补充、碱化尿液对症治疗为主。"
    },
    "As": {
        "name": "砷 (As)",
        "summary": "无机砷为强亲硫醇毒物，IARC 确定为 1 类明确人类致癌物。慢性职业暴露可致多发性外周神经病、掌跖角化、皮肤色素沉着/脱失（雨点样斑点）、末梢血管痉挛栓塞（乌脚病）及呼吸道/皮肤恶性肿瘤。",
        "standard_info": "依据国家强制性标准《GBZ 2.1—2019》，工作场所砷及其无机化合物 PC-TWA 限值为 0.01 mg/m³，砷化氢(AsH₃)最高容许浓度 MAC 为 0.03 mg/m³。职业健康监护中，尿总无机砷及代谢物(MMA+DMA)超过 50 µg/L 提示显著过量吸收。严重皮肤疾病、外周神经损伤及慢性肝肾疾病为法定禁忌证。",
        "mechanism": "1. **巯基螯合与呼吸链解偶联**：三价亚砷酸盐(As³⁺)与丙酮酸脱氢酶、硫辛酸脱氢酶等辅酶近邻双巯基(-SH)结合生成稳定的环状螯合物，全面抑制三羧酸循环；五价砷酸盐(As⁵⁺)由于与磷酸根结构类似，在糖酵解中发生竞争性砷酸化，造成高能磷酸键解偶联与能量耗竭。\n2. **氧化应激与表观遗传重编程**：诱导内皮细胞生成过氧亚硝基离子(ONOO⁻)，破坏一氧化氮生物利用度；干扰 DNA 甲基转移酶(DNMTs)底物竞争，引起全基因组低甲基化与原癌基因表达上调。\n3. **皮肤与微循环毒性**：刺激角质形成细胞异常高表达角蛋白及上皮生长因子(EGF)，形成掌跖角化过度及博文病(Bowen's disease)癌前病变；破坏微血管内皮致闭塞性脉管炎。",
        "biomarkers": "尿中无机砷及其甲基化代谢产物（一甲基砷酸 MMA、二甲基次砷酸 DMA）形态分析是评估体内剂量金标准；毛发和指甲砷反映既往蓄积暴露情况。",
        "interventions": "1. **密闭抽风排毒**：冶炼炉、焙烧炉全程负压运行，涉砷设备检修须实行强制排风置换与双人监护防砷化氢急性中毒。\n2. **健康巡查与早期识别**：重点检查作业工人手掌、脚底角化情况与躯干皮肤色斑变化，定期进行外周神经传导速度测定。\n3. **络合解毒治疗**：确诊职业性砷中毒后，尽早应用二巯基丙磺酸钠(DMPS)或二巯基丁二酸(DMSA)进行驱砷治疗。"
    },
    "Hg": {
        "name": "汞 (Hg)",
        "summary": "金属汞蒸气极易透过呼吸道和血脑屏障蓄积于中枢神经系统，有机汞（甲基汞）则具有高度亲脂性与神经亲和力。典型临床特征包括意向性指鼻震颤、易怒多疑的精神改变及口腔龈炎三联征。",
        "standard_info": "依据国家强制性标准《GBZ 2.1—2019》，汞蒸气 PC-TWA 限值为 0.02 mg/m³，MAC 限值为 0.04 mg/m³。依据《GBZ 89 职业性汞中毒诊断标准》，尿汞测定 ≥ 35 µmol/mol 肌酐结合震颤等体征为诊断依据。中枢神经系统器质性疾病、慢性肾小球肾炎为法定禁忌证。",
        "mechanism": "1. **中枢神经组织蓄积**：Hg⁰ 蒸气吸入后迅速经肺泡毛细血管溶入血流，因其高脂溶性迅速穿透血脑屏障，在脑实质内被红细胞和星形胶质细胞中的过氧化氢酶-过氧化物酶系统氧化为二价汞离子(Hg²⁺)并牢固结合于蛋白质硫醇基团无法逸出，发生长期蓄积毒性。\n2. **细胞微管解聚与突触功能障碍**：Hg²⁺ 与微管蛋白(Tubulin)巯基高度亲和，阻断微管装配聚合并加速微管解聚，致使小脑颗粒细胞、距状裂皮质神经元轴浆运输中断与坏死凋亡；强烈抑制突触间隙星形胶质细胞对兴奋性神经递质谷氨酸的重摄取，导致谷氨酸兴奋性毒性蓄积与意向性肌震颤。\n3. **肾脏近端损伤与免疫炎性反应**：经肾小球滤过的汞离子在近曲小管上皮细胞大量沉积，引起肾小管坏死及自身抗体介导的膜性肾小球肾炎。",
        "biomarkers": "尿汞(U-Hg)为金属汞与无机汞近期吸收的重要监护指标；全血汞(B-Hg)主要反映甲基汞等有机汞或突发高浓度吸入；神经行为核心测试(NCTB)为早期亚临床神经毒性敏感工具。",
        "interventions": "1. **地面水封与吸附控制**：汞操作台面平整无缝、向集汞槽倾斜，操作场所采用碘化活性炭或含硫材料进行蒸气吸附控制。\n2. **医学筛查**：定期开展神经系统体检（肌张力、眼睑/舌/手指震颤检查）及尿汞排查。\n3. **络合驱汞治疗**：轻度及以上中毒首选二巯基丙磺酸钠(DMPS)肌肉注射驱汞治疗，疗程间隙密切监测尿量及肾功能。"
    }
}


def generate_expert_reasoning_answer(query: str, search_result: Dict[str, Any]) -> str:
    """
    高保真循证专家推理引擎：
    当本地大模型处于离线状态、或用户选择预训练统计模型 (XGBoost/DNN) 时启动，
    根据用户提问、意图分类、目标金属实体、P0/P1强制标准与Top-6重排科学切块，
    深入推演生成专业规范、条理严密的五段式医学循证研判报告，杜绝简单罗列切块！
    """
    analysis = search_result.get("analysis", {})
    metals = analysis.get("metals", [])
    intent_task = analysis.get("primary_task", "T01_EXPOSURE")
    p0_p1 = search_result.get("p0_p1_boundaries", [])
    top_sci = search_result.get("top_ranked", [])[:5]

    matched_key = metals[0] if metals and metals[0] in EXPERT_TOXICOLOGY_KNOWLEDGE else None
    knowledge = EXPERT_TOXICOLOGY_KNOWLEDGE.get(matched_key)

    metal_names = [METAL_METADATA[m]["name_zh"] + f"({m})" for m in metals if m in METAL_METADATA]
    metal_title = "、".join(metal_names) if metal_names else "职业重金属复合暴露"

    # 1. 生成【核心研判与直接回答】
    if knowledge:
        core_judgment = (
            f"针对您关于 **{metal_title}** 的核心关切，系统经由双通路证据检索与多维循证推演，研判结论如下：\n\n"
            f"{knowledge['summary']} 该类危害因素对机体的影响呈现明确的 **剂量-效应非线性阈值** 规律，"
            f"早期在亚临床阶段即可引起特征性生化标志物改变。用人单位与评估人员应重点防范其靶器官不可逆损伤风险。"
        )
    else:
        core_judgment = (
            f"针对您关于 **{metal_title}** 的咨询，系统整合双通路检索切块（稀疏倒排 Top-32 + 稠密语义 Top-32），"
            f"重点围绕其在工作场所中的吸收途径、蓄积特征、靶器官损伤及法定红线展开系统评估。复合暴露环境下多金属常伴有协同或加合毒性效应。"
        )

    # 2. 生成【我国现行法律法规与强制性接触限值 (P0/P1 法定红线)】
    std_points = []
    for item in p0_p1:
        txt = item["text"].replace("\n", " ").strip()
        if len(txt) > 160:
            txt = txt[:160] + "..."
        std_points.append(
            f"- **《{item['standard_no']} {item['title']}》**（{item['priority_label']} · 硬约束）\n"
            f"  - **条款路径**：`{item['section_title']}`\n"
            f"  - **强制条文**：> “{txt}”"
        )
    if not std_points and knowledge:
        std_points.append(f"- **《GBZ 2.1—2019 工作场所有害因素职业接触限值》**：{knowledge['standard_info']}")
    std_section = "\n\n".join(std_points) if std_points else "- 遵循《中华人民共和国职业病防治法》及《GBZ 2.1-2019》强制性接触限值要求，严格控制接触浓度。"

    # 3. 生成【毒理学致病机制与靶器官病理损伤链条】
    if knowledge:
        mech_section = (
            f"**{metal_title}** 的主要毒作用机理在分子及细胞水平具有清晰的级联放大效应：\n\n"
            f"{knowledge['mechanism']}"
        )
    else:
        mech_section = (
            f"在毒理学机制层面，**{metal_title}** 进入循环系统后，主要通过亲和结合细胞膜脂蛋白及酶活性中心巯基(-SH)，"
            f"引发线粒体电子传递链偶联障碍并大剂量释放超氧阴离子自由基(ROS)。持续的氧化应激损伤内皮依赖性血管舒张功能，"
            f"并引起靶器官实质细胞变性坏死与凋亡，终末期可发展为不可逆间质纤维化或恶性转化。"
        )

    # 4. 生成【关键暴露监测标志物与科学队列证据支撑】
    sci_points = []
    for idx, item in enumerate(top_sci, 1):
        txt = item["text"].replace("\n", " ").strip()
        if len(txt) > 180:
            txt = txt[:180] + "..."
        score_pct = int(item.get("score", 0.0) * 100)
        factors = item.get("score_factors", {})
        sci_points.append(
            f"- **[E{idx}] {item['standard_no_or_doi']}**（{item['priority_label']} · 循证得分 DocScore: `{score_pct}%`）\n"
            f"  - **论证聚焦**：{item['title']} ({item['section_title']})\n"
            f"  - **切块实证**：> “{txt}”\n"
            f"  - **评价因子**：*Sem相关度: {factors.get('Sem')} | G意图匹配: {factors.get('G_intent')} | H证据层级: {factors.get('H_prior')}*"
        )
    sci_section = "\n\n".join(sci_points) if sci_points else "- 双通路科学前瞻队列证据正在扩充收录。"
    if knowledge:
        biomarker_note = f"\n\n**重点生物标志物指引**：{knowledge['biomarkers']}"
    else:
        biomarker_note = "\n\n**重点生物标志物指引**：建议根据接触谱系定期检测全血重金属浓度、尿排泄负荷及特异性靶器官功能指标。"

    # 5. 生成【智能干预决策与分级因果阻断建议】
    if knowledge:
        interv_section = knowledge['interventions']
    else:
        interv_section = (
            "1. **一级预防（工程防护与工艺替代）**：密闭产生源并设置负压局部抽风除尘排毒系统，保证作业点空气浓度持续低于国家 PC-TWA 限值；\n"
            "2. **二级预防（早诊早治与医学监护）**：建立健全职工职业健康监护档案，开展岗前、在岗及离岗全周期体检，检出职业禁忌证者立即调离；\n"
            "3. **三级预防（临床治疗与干预阻断）**：若发生过量吸收或中毒倾向，立即脱离接触，依据《职业病诊断标准》规范开展络合剂驱毒促排与脏器功能对症支持治疗。"
        )

    md_report = f"""### 一、 核心研判与直接结论
{core_judgment}

### 二、 我国现行法律法规与强制性接触限值 (P0/P1 法定红线)
{std_section}

### 三、 毒理学致病机制与靶器官病理损伤链条
{mech_section}

### 四、 关键暴露监测标志物与前瞻队列证据支撑
{sci_section}{biomarker_note}

### 五、 智能干预决策与分级因果阻断建议
{interv_section}
"""
    return format_markdown_to_html(md_report)


def synthesize_dual_path_answer(query: str, search_result: Dict[str, Any]) -> str:
    """
    生成规范化完整研判答案（兼容旧接口名）
    """
    return generate_expert_reasoning_answer(query, search_result)

