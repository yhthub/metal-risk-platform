"""
Prompt 模块

包含公共卫生与职业健康领域的专业 Prompt 模板
整合用户提供的专家角色定义与系统设计的结构化模板
支持知识图谱和RAG检索（预留接口）
"""

from .health_expert import (
    get_system_prompt,
    get_answer_principles,
    get_answer_template,
    build_professional_prompt,
    classify_question,
    extract_triples,
    get_quick_prompt,
    get_all_quick_prompts,
    QUESTION_PATTERNS,
    QUICK_PROMPTS
)

__all__ = [
    'get_system_prompt',
    'get_answer_principles',
    'get_answer_template',
    'build_professional_prompt',
    'classify_question',
    'extract_triples',
    'get_quick_prompt',
    'get_all_quick_prompts',
    'QUESTION_PATTERNS',
    'QUICK_PROMPTS'
]
