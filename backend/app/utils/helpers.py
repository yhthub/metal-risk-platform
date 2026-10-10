import uuid
import os
from datetime import datetime
from typing import Optional


def generate_id(prefix: str = "") -> str:
    """生成唯一ID"""
    unique_id = str(uuid.uuid4())[:8]
    if prefix:
        return f"{prefix}-{unique_id}"
    return unique_id


def generate_assessment_id() -> str:
    """生成评估ID"""
    return generate_id("ASSESS")


def generate_file_id() -> str:
    """生成文件ID"""
    return generate_id("FILE")


def get_current_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_upload_dir(upload_dir: str) -> str:
    """确保上传目录存在"""
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(filename)[1].lower()


def validate_file_type(filename: str, allowed_extensions: list = None) -> bool:
    """验证文件类型"""
    if allowed_extensions is None:
        allowed_extensions = ['.csv', '.xlsx', '.xls']
    ext = get_file_extension(filename)
    return ext in allowed_extensions


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def calculate_risk_level(score: float) -> str:
    """根据分数计算风险等级"""
    if score > 45:
        return "high"
    elif score > 18:
        return "medium"
    else:
        return "low"


def get_metal_threshold(metal: str) -> Optional[float]:
    """获取金属安全阈值"""
    thresholds = {
        "pb": 100.0,  # μg/L
        "cd": 5.0,    # μg/g
        "hg": 10.0,   # μg/L
        "th": 0.1,    # μg/L
        "li": 1.0,    # μg/L
        "cr": 5.0,    # μg/L
        "ni": 5.0,    # μg/L
        "co": 5.0,    # μg/L
        "as_val": 5.0,  # μg/g
        "rn": 100.0   # Bq/m³
    }
    return thresholds.get(metal)


def calculate_relative_exposure(value: float, metal: str) -> float:
    """计算相对暴露指数"""
    threshold = get_metal_threshold(metal)
    if threshold is None or threshold == 0:
        return 0.0
    return round((value / threshold) * 100, 2)


def get_disease_name(disease_key: str) -> str:
    """获取疾病中文名称"""
    disease_names = {
        "nephrotoxicity": "肾毒性",
        "neurotoxicity": "神经毒性",
        "hepatotoxicity": "肝毒性",
        "cardiotoxicity": "心脏毒性",
        "carcinogenicity": "致癌性"
    }
    return disease_names.get(disease_key, disease_key)


def get_model_category(model_id: str) -> str:
    """获取模型类别"""
    categories = {
        "xgboost": "机器学习",
        "lightgbm": "机器学习",
        "random_forest": "机器学习",
        "catboost": "机器学习",
        "elastic_net": "机器学习",
        "gam": "机器学习",
        "dnn": "深度学习",
        "shap_mlp": "深度学习",
        "deepsurv": "深度学习",
        "aft_nn": "深度学习",
        "g_computation": "因果推断",
        "qg_comp": "因果推断",
        "tmle": "因果推断",
        "causal_forest": "因果推断",
        "bkmr": "贝叶斯",
        "bayesian_network": "贝叶斯",
        "bkmr_cs": "贝叶斯",
        "cox_ph": "生存分析",
        "weibull_aft": "生存分析",
        "super_learner": "集成框架"
    }
    return categories.get(model_id, "其他")


def get_model_description(model_id: str) -> str:
    """获取模型描述"""
    descriptions = {
        "xgboost": "极端梯度提升树，适合处理结构化数据的高精度预测模型",
        "lightgbm": "轻量级梯度提升机，训练速度快，内存占用低",
        "random_forest": "随机森林，基于多棵决策树的集成学习方法",
        "catboost": "类别型梯度提升，自动处理类别特征",
        "elastic_net": "弹性网络回归，结合L1和L2正则化",
        "gam": "广义可加模型，灵活的非线性建模方法",
        "dnn": "深度神经网络，多层感知机架构",
        "shap_mlp": "SHAP集成多层感知机，提供可解释的特征归因",
        "deepsurv": "深度生存分析模型，结合深度学习与生存分析",
        "aft_nn": "加速失效时间神经网络，用于生存数据预测",
        "g_computation": "G-computation因果推断方法，估计边际因果效应",
        "qg_comp": "分位数G-computation，适用于混合暴露场景",
        "tmle": "目标最大似然估计，双重稳健的因果推断方法",
        "causal_forest": "因果森林，异质性处理效应估计",
        "bkmr": "贝叶斯核机器回归，灵活的混合暴露效应估计",
        "bayesian_network": "贝叶斯网络，基于概率图模型的因果推断",
        "bkmr_cs": "BKMR变体，适用于截面数据的因果推断",
        "cox_ph": "Cox比例风险模型，经典的生存分析方法",
        "weibull_aft": "威布尔加速失效时间模型，参数化生存分析",
        "super_learner": "超级学习器，集成多种算法的最优组合"
    }
    return descriptions.get(model_id, "暂无描述")
