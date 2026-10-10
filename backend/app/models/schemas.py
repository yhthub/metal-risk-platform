from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class JobType(str, Enum):
    SMELTING = "smelting"
    MINING = "mining"
    WELDING = "welding"
    OTHER = "other"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class Education(str, Enum):
    PRIMARY = "primary"
    MIDDLE = "middle"
    HIGH = "high"
    COLLEGE = "college"
    BACHELOR = "bachelor"
    MASTER = "master"


class Marital(str, Enum):
    UNMARRIED = "unmarried"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


class Smoking(str, Enum):
    NEVER = "never"
    FORMER = "former"
    CURRENT_LT10 = "current_lt10"
    CURRENT_GE10 = "current_ge10"


class Drinking(str, Enum):
    NEVER = "never"
    OCCASIONAL = "occasional"
    FREQUENT = "frequent"
    DAILY = "daily"


class PPE(str, Enum):
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    FULL = "full"


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InterventionLevel(str, Enum):
    LEVEL1 = "level1"  # 一级预防
    LEVEL2 = "level2"  # 二级预防


# 个体数据模型
class IndividualData(BaseModel):
    """单人录入数据"""
    id: str = Field(..., description="工号，如 SZ-284")
    gender: Gender = Field(..., description="性别")
    age: int = Field(..., ge=18, le=100, description="年龄")
    work_years: float = Field(..., ge=0, description="暴露工龄(年)")
    job: JobType = Field(..., description="工种")

    # 个体影响因素
    education: Optional[Education] = Field(None, description="学历")
    marital: Optional[Marital] = Field(None, description="婚姻状况")
    smoking: Optional[Smoking] = Field(None, description="吸烟情况")
    drinking: Optional[Drinking] = Field(None, description="饮酒情况")
    bmi: Optional[float] = Field(None, ge=10, le=50, description="BMI体质指数")
    ppe: Optional[PPE] = Field(None, description="防护装备使用")
    history: Optional[str] = Field(None, description="既往职业病史")

    # 8种核心重金属暴露指标
    pb: float = Field(..., ge=0, description="铅 Pb (μg/L)")
    cd: float = Field(..., ge=0, description="镉 Cd (μg/g)")
    hg: float = Field(..., ge=0, description="汞 Hg (μg/L)")
    th: float = Field(..., ge=0, description="钍 Th (μg/L)")
    li: float = Field(..., ge=0, description="锂 Li (μg/L)")
    cr: float = Field(..., ge=0, description="铬 Cr (μg/L)")
    ni: float = Field(..., ge=0, description="镍 Ni (μg/L)")
    co: float = Field(..., ge=0, description="钴 Co (μg/L)")

    # 伴生非金属与标志物
    as_val: float = Field(..., ge=0, description="砷 As (μg/g)")
    rn: float = Field(..., ge=0, description="氡 Rn (Bq/m³)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "SZ-102",
                "gender": "male",
                "age": 45,
                "work_years": 12.5,
                "job": "smelting",
                "education": "high",
                "marital": "married",
                "smoking": "current_lt10",
                "drinking": "occasional",
                "bmi": 24.5,
                "ppe": "basic",
                "history": "2023年诊断轻度铅中毒，已治愈",
                "pb": 124.0,
                "cd": 89.0,
                "hg": 24.0,
                "th": 12.0,
                "li": 18.0,
                "cr": 34.0,
                "ni": 65.0,
                "co": 40.0,
                "as_val": 105.0,
                "rn": 30.0
            }
        }


# 批量导入响应
class BatchImportResponse(BaseModel):
    """批量导入响应"""
    file_id: str = Field(..., description="文件ID")
    filename: str = Field(..., description="文件名")
    outcome_id: str = Field(..., description="预测结局ID")
    outcome_name: str = Field(..., description="预测结局名称")
    total_records: int = Field(..., description="总记录数")
    analysis_records: int = Field(..., description="进入分析队列的记录数")
    excluded_records: int = Field(..., description="未进入分析队列的记录数")
    success_records: int = Field(..., description="成功记录数")
    failed_records: int = Field(..., description="失败记录数")
    columns: List[str] = Field(..., description="数据列名")
    required_columns: List[str] = Field(..., description="当前结局要求的字段")
    warnings: List[str] = Field(default_factory=list, description="数据处理提示")


# 数据统计响应
class DataStatistics(BaseModel):
    """数据统计信息"""
    total_count: int = Field(..., description="总人数")
    male_count: int = Field(..., description="男性人数")
    female_count: int = Field(..., description="女性人数")
    male_ratio: float = Field(..., description="男性比例")
    female_ratio: float = Field(..., description="女性比例")


# 可视化数据
class VisualizationData(BaseModel):
    """可视化数据"""
    marital_distribution: Dict[str, int] = Field(..., description="婚姻状况分布")
    education_distribution: Dict[str, int] = Field(..., description="学历分布")
    income_distribution: Dict[str, Dict[str, int]] = Field(..., description="收入分布")
    metal_statistics: Dict[str, Dict[str, float]] = Field(..., description="金属浓度统计")


# 模型信息
class ModelInfo(BaseModel):
    """风险评估模型信息"""
    id: str = Field(..., description="模型ID")
    name: str = Field(..., description="模型名称")
    category: str = Field(..., description="模型类别")
    description: str = Field(..., description="模型描述")


# 高危人员
class HighRiskPerson(BaseModel):
    """高危人员信息"""
    id: str = Field(..., description="工号")
    name: str = Field(..., description="姓名")
    dept: str = Field(..., description="部门")
    years: int = Field(..., description="工龄")
    factors: str = Field(..., description="风险因子")
    score: float = Field(..., description="因果风险增幅(%)")
    level: RiskLevel = Field(..., description="风险等级")


# 风险评估结果
class RiskAssessmentResult(BaseModel):
    """风险评估结果"""
    assessment_id: str = Field(..., description="评估ID")
    model_name: str = Field(..., description="使用的模型")
    total_population: int = Field(..., description="总人口数")
    high_risk_count: int = Field(..., description="高危人数")
    high_risk_ratio: float = Field(..., description="高危比例")
    high_risk_persons: List[HighRiskPerson] = Field(..., description="高危人员列表")
    warning_level: str = Field(..., description="预警等级")
    warning_message: str = Field(..., description="预警信息")


# SHAP值
class ShapValue(BaseModel):
    """SHAP特征归因"""
    name: str = Field(..., description="特征名称")
    value: float = Field(..., description="SHAP值")


# 剂量响应数据点
class DoseResponsePoint(BaseModel):
    """剂量响应数据点"""
    dose: float = Field(..., description="剂量")
    response: float = Field(..., description="响应(患病概率)")


# 联合暴露效应
class JointEffectPoint(BaseModel):
    """联合暴露效应数据点"""
    pb_level: str = Field(..., description="铅浓度水平")
    as_level: str = Field(..., description="砷浓度水平")
    risk: float = Field(..., description="联合致病概率")


# 疾病风险
class DiseaseRisk(BaseModel):
    """疾病风险"""
    name: str = Field(..., description="疾病名称")
    probability: float = Field(..., description="患病概率(%)")
    status: str = Field(..., description="风险状态")


# 风险评估详情
class RiskAssessmentDetail(BaseModel):
    """风险评估详情"""
    shap_values: List[ShapValue] = Field(..., description="SHAP特征归因")
    dose_response: List[DoseResponsePoint] = Field(..., description="剂量响应曲线")
    joint_effects: List[JointEffectPoint] = Field(..., description="联合暴露效应")
    disease_risks: List[DiseaseRisk] = Field(..., description="疾病风险预测")


# DAG节点
class DAGNode(BaseModel):
    """DAG节点"""
    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    layer: int = Field(..., description="所在层")
    node_type: str = Field(..., description="节点类型")


# DAG边
class DAGEdge(BaseModel):
    """DAG边"""
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    weight: float = Field(..., description="因果权重")


# DAG数据
class DAGData(BaseModel):
    """DAG图数据"""
    nodes: List[DAGNode] = Field(..., description="节点列表")
    edges: List[DAGEdge] = Field(..., description="边列表")


# 反事实推演请求
class CounterfactualRequest(BaseModel):
    """反事实推演请求"""
    metals: Dict[str, float] = Field(..., description="金属浓度调整值")
    antioxidant: bool = Field(False, description="是否启用抗氧化干预")
    edta: bool = Field(False, description="是否启用EDTA螯合治疗")


# 反事实推演结果
class CounterfactualResult(BaseModel):
    """反事实推演结果"""
    original_risk: float = Field(..., description="原始风险评分")
    adjusted_risk: float = Field(..., description="调整后风险评分")
    risk_reduction: float = Field(..., description="风险降低幅度(%)")
    intervention_effects: Dict[str, float] = Field(..., description="各干预措施效果")


# KPI指标
class CausalKPI(BaseModel):
    """因果推理KPI"""
    overall_risk_score: float = Field(..., description="综合因果风险评分")
    primary_factor: str = Field(..., description="主导致病因子")
    confidence: float = Field(..., description="推断置信度")
    intervention_priority: str = Field(..., description="最优干预优先级")


# 工作流步骤
class WorkflowStep(BaseModel):
    """干预工作流步骤"""
    title: str = Field(..., description="步骤标题")
    tag: str = Field(..., description="标签")
    type: str = Field(..., description="类型(danger/primary/warning/safe)")
    desc: str = Field(..., description="描述")
    detail: Optional[str] = Field(None, description="具体操作")
    indicator: Optional[str] = Field(None, description="关键指标")
    period: str = Field(..., description="时间周期")
    cost: Optional[str] = Field(None, description="费用")


# 干预成效
class OutcomeMetric(BaseModel):
    """干预成效指标"""
    label: str = Field(..., description="指标名称")
    before: float = Field(..., description="干预前值")
    after: float = Field(..., description="干预后值")


# 干预方案
class InterventionPlan(BaseModel):
    """干预方案"""
    person_id: str = Field(..., description="人员工号")
    name: str = Field(..., description="姓名")
    dept: str = Field(..., description="部门")
    years: int = Field(..., description="工龄")
    factors: str = Field(..., description="风险因子")
    score: float = Field(..., description="因果风险增幅(%)")
    level: InterventionLevel = Field(..., description="干预级别")
    workflow: List[WorkflowStep] = Field(..., description="工作流步骤")
    outcomes: List[OutcomeMetric] = Field(..., description="预期成效")


# 知识库信息
class KnowledgeBase(BaseModel):
    """知识库信息"""
    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: str = Field(..., description="知识库描述")
    document_count: int = Field(0, description="文档数量")


# 聊天消息
class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色(user/ai)")
    content: str = Field(..., description="消息内容")
    think_process: Optional[str] = Field(None, description="思考过程")


# 聊天请求
class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    model: str = Field("XGBoost", description="使用的模型")
    knowledge_bases: List[str] = Field(..., description="选中的知识库")
    knowledge_bases: Optional[List[str]] = Field(default_factory=list, description="选中的知识库 (已弃用)")
    enable_deep_think: bool = Field(True, description="是否启用深度思考")


# P0/P1 国家标准与法律红线边界 (独立说明，不参与 DocScore 排序)
class NormativeBoundaryItem(BaseModel):
    """P0/P1 法律与强制性国家职业卫生标准红线边界说明"""
    chunk_id: str = Field(..., description="切块ID")
    document_id: Optional[str] = Field(None, description="文档ID")
    standard_no: str = Field(..., description="标准号/法律编号")
    title: str = Field(..., description="标准名称")
    issuer: Optional[str] = Field(None, description="发布机构")
    priority: str = Field(..., description="证据层级 (CN-OH-P0 或 CN-OH-P1)")
    priority_label: str = Field(..., description="层级说明")
    clause_no: Optional[str] = Field(None, description="条款号")
    section_title: str = Field(..., description="章节/条款名称")
    text: str = Field(..., description="原文内容")
    is_mandatory: bool = Field(True, description="是否属于法定强制约束")
    boundary_type: Optional[str] = Field("法定强制边界与红线", description="边界类型")


# 循证证据切块卡片 (双通路检索)
class EvidenceChunkCard(BaseModel):
    """循证切块卡片信息 (稀疏/稠密检索科学证据候选与重排)"""
    chunk_id: str = Field(..., description="切块ID")
    document_id: Optional[str] = Field(None, description="文档ID")
    title: str = Field(..., description="文档标题")
    standard_no_or_doi: str = Field(..., description="标准号或DOI")
    issuer: Optional[str] = Field(None, description="发布机构或期刊")
    evidence_priority: str = Field(..., description="证据等级编码 (如 CN-OH-P2/P6/P7)")
    priority_label: str = Field(..., description="证据等级说明")
    section_title: str = Field(..., description="章节/条款名称")
    page: Optional[int] = Field(None, description="页码")
    clause_no: Optional[str] = Field(None, description="条款号")
    text: str = Field(..., description="原文切块内容")
    score: Optional[float] = Field(0.0, description="综合循证评分 (DocScore，去 fu 指数)")
    score_factors: Optional[Dict[str, float]] = Field(None, description="分项评分 (Sem, G_intent, H_prior, M_quality, A_applicability)")
    channel: Optional[str] = Field("scientific", description="检索通道 ('dense' 或 'sparse')")
    channel_name: Optional[str] = Field("双通路科学证据", description="通道展示名称")
    sparse_rank: Optional[int] = Field(None, description="稀疏通道排名")
    dense_rank: Optional[int] = Field(None, description="稠密通道排名")
    sparse_score: Optional[float] = Field(None, description="稀疏BM25分数")
    dense_score: Optional[float] = Field(None, description="稠密余弦相似度")


# 双通路检索结果
class DualPathRetrievalResult(BaseModel):
    """双通路检索响应结果 (稠密Top-32 + 稀疏Top-32，P0/P1法律红线独立提取)"""
    query: str = Field(..., description="原始提问")
    analysis: Dict[str, Any] = Field(..., description="意图分析与金属识别")
    summary: Dict[str, Any] = Field(..., description="检索概览统计")
    p0_p1_boundaries: List[NormativeBoundaryItem] = Field(default_factory=list, description="P0/P1 法律与强制性标准红线边界 (独立说明，不参与排序)")
    sparse_hits: List[EvidenceChunkCard] = Field(default_factory=list, description="稀疏倒排检索候选切块 (Top-32)")
    dense_hits: List[EvidenceChunkCard] = Field(default_factory=list, description="稠密语义检索候选切块 (Top-32)")
    top_ranked: List[EvidenceChunkCard] = Field(default_factory=list, description="多维重排科学切块 (Sem*G*H*M*A)")


# 聊天响应
class ChatResponse(BaseModel):
    """聊天响应"""
    message: str = Field(..., description="AI回复")
    think_process: Optional[str] = Field(None, description="思考过程")
    cited_knowledge_bases: List[str] = Field(..., description="引用的知识库")
    recommended_knowledge_bases: Optional[List[str]] = Field(None, description="推荐的知识库")
    recommend_reason: Optional[str] = Field(None, description="推荐理由")
    cited_knowledge_bases: Optional[List[str]] = Field(default_factory=list, description="引用的知识库")
    recommended_knowledge_bases: Optional[List[str]] = Field(None, description="推荐的知识库 (已弃用)")
    recommend_reason: Optional[str] = Field(None, description="推荐理由 (已弃用)")
    p0_p1_boundaries: Optional[List[NormativeBoundaryItem]] = Field(None, description="P0/P1 法律与强制性国家标准红线边界 (独立说明)")
    evidence_cards: Optional[List[EvidenceChunkCard]] = Field(None, description="双通路检索重排科学证据切块卡片")
    sparse_hits: Optional[List[EvidenceChunkCard]] = Field(None, description="稀疏检索候选切块 (Top-32)")
    dense_hits: Optional[List[EvidenceChunkCard]] = Field(None, description="稠密检索候选切块 (Top-32)")
    dual_path_summary: Optional[Dict[str, Any]] = Field(None, description="双通路检索统计摘要")


# 通用响应
class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool = Field(True, description="是否成功")
    message: str = Field("操作成功", description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


# 错误响应
class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(False, description="是否成功")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="错误详情")

