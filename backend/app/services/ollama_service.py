"""
Ollama 本地模型服务

通过 Ollama API 调用本地大语言模型
"""

import logging
import time
import requests
from typing import Optional, List, Dict, Any

from ..prompts import get_system_prompt, build_professional_prompt, extract_triples

logger = logging.getLogger(__name__)

# Ollama API 配置
OLLAMA_BASE_URL = "http://localhost:11434"

# 默认模型
DEFAULT_MODEL = "deepseek-r1:latest"

# 避免 Windows 系统代理（如 127.0.0.1:12000 等）拦截本地 Ollama 连接
LOCAL_PROXIES = {"http": None, "https": None}


class OllamaService:
    """Ollama 本地模型服务"""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.default_model = DEFAULT_MODEL

    def check_connection(self) -> bool:
        """检查 Ollama 服务是否连接"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", proxies=LOCAL_PROXIES, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"无法连接到 Ollama 服务: {e}")
            return False

    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用的模型列表"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", proxies=LOCAL_PROXIES, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("models", []):
                    models.append({
                        "name": model["name"],
                        "size_mb": round(model["size"] / (1024 * 1024), 1),
                        "modified": model.get("modified_at", "")
                    })
                return models
            return []
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_professional_prompt: bool = True
    ) -> Dict[str, Any]:
        """
        生成回答

        Args:
            prompt: 用户问题
            model: 模型名称
            system_prompt: 自定义系统提示（如不提供则使用专业公卫专家提示）
            max_tokens: 最大生成token数
            temperature: 温度参数
            use_professional_prompt: 是否使用专业prompt模板（默认True）
        """
        model_name = model or self.default_model

        # 使用专业 prompt 模板
        if use_professional_prompt and not system_prompt:
            system_prompt = get_system_prompt()
            professional_prompt = build_professional_prompt(prompt)
        elif system_prompt:
            professional_prompt = prompt
        else:
            professional_prompt = prompt

        # 构建请求数据
        data = {
            "model": model_name,
            "prompt": professional_prompt,
            "stream": False,
            "options": {}
        }

        if system_prompt:
            data["system"] = system_prompt

        if temperature:
            data["options"]["temperature"] = temperature

        if max_tokens:
            data["options"]["num_predict"] = max_tokens

        try:
            start_time = time.time()

            # 调用 Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=180  # 增加超时时间到3分钟
            )

            generation_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "")

                # 提取三元组信息
                triples = extract_triples(prompt)

                return {
                    "success": True,
                    "answer": answer,
                    "model": model_name,
                    "generation_time": round(generation_time, 2),
                    "total_tokens": result.get("eval_count", 0),
                    "tokens_per_second": round(
                        result.get("eval_count", 0) / generation_time if generation_time > 0 else 0,
                        1
                    ),
                    "triples": triples
                }
            else:
                return {
                    "success": False,
                    "error": f"API 错误: {response.status_code}",
                    "answer": None
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "请求超时",
                "answer": None
            }
        except Exception as e:
            logger.error(f"生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": None
            }

    def generate_rag_answer(
        self,
        prompt: str,
        system_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.5,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        基于双通路检索切块与法定红线上下文执行大模型循证推理生成规范答案
        """
        model_name = model or self.default_model
        data = {
            "model": model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                proxies=LOCAL_PROXIES,
                timeout=timeout
            )
            generation_time = time.time() - start_time
            if response.status_code == 200:
                raw_text = response.json().get("response", "").strip()
                think_process = None
                clean_answer = raw_text
                # 支持提取 deepseek-r1 等模型的 <think> 标签
                if "<think>" in raw_text and "</think>" in raw_text:
                    parts = raw_text.split("</think>", 1)
                    think_raw = parts[0].replace("<think>", "").strip()
                    clean_answer = parts[1].strip()
                    think_process = f"<div style='color: #64748B; font-size: 0.88rem; line-height: 1.6; white-space: pre-wrap;'>{think_raw}</div>"

                return {
                    "success": True,
                    "answer": clean_answer,
                    "think_process": think_process,
                    "model": model_name,
                    "generation_time": round(generation_time, 2)
                }
            else:
                return {
                    "success": False,
                    "error": f"Ollama HTTP {response.status_code}",
                    "answer": None
                }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "模型推理超时 (已达到时限)",
                "answer": None
            }
        except Exception as e:
            logger.error(f"Ollama RAG generate failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": None
            }

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        use_professional_prompt: bool = True
    ) -> Dict[str, Any]:
        """
        聊天接口

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            use_professional_prompt: 是否使用专业prompt模板
        """
        model_name = model or self.default_model

        # 如果使用专业 prompt，添加系统提示
        if use_professional_prompt:
            # 检查是否已有系统消息
            has_system = any(m.get("role") == "system" for m in messages)
            if not has_system:
                messages = [{"role": "system", "content": get_system_prompt()}] + messages

            # 获取最后一条用户消息并构建专业 prompt
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].get("role") == "user":
                    original_question = messages[i]["content"]
                    professional_prompt = build_professional_prompt(original_question)
                    messages[i]["content"] = professional_prompt
                    break

        data = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {}
        }

        if temperature:
            data["options"]["temperature"] = temperature

        try:
            start_time = time.time()

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=data,
                timeout=180  # 增加超时时间到3分钟
            )

            generation_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                answer = result.get("message", {}).get("content", "")

                # 提取三元组信息（从原始问题）
                triples = None
                for m in messages:
                    if m.get("role") == "user":
                        # 尝试从原始消息提取
                        try:
                            triples = extract_triples(m["content"])
                        except:
                            pass
                        break

                return {
                    "success": True,
                    "answer": answer,
                    "model": model_name,
                    "generation_time": round(generation_time, 2),
                    "triples": triples
                }
            else:
                return {
                    "success": False,
                    "error": f"API 错误: {response.status_code}",
                    "answer": None
                }

        except Exception as e:
            logger.error(f"聊天失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": None
            }


# 全局服务实例
_ollama_service = None


def get_ollama_service() -> OllamaService:
    """获取 Ollama 服务实例"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
