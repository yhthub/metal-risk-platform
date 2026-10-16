"""A real local model client; no model download or fabricated answer fallback."""
from typing import Dict, List
import requests
from ..rag_config import RagSettings


class ModelUnavailableError(RuntimeError):
    pass


MODEL_DISABLED_NOTICE = "生成端尚未启用：等待允许供共享网站后端调用的模型接口，当前不会发起模型请求。"


class LocalLlmService:
    def __init__(self, settings=None):
        self.settings = settings or RagSettings.from_env()
        self.session = requests.Session()
        self.session.trust_env = False  # local/private model traffic must not use desktop proxies
        if self.settings.model_api_key:
            self.session.headers["Authorization"] = "Bearer " + self.settings.model_api_key

    def status(self) -> Dict:
        native = self.settings.provider == "ollama"
        backend = "ollama_native" if native else "openai_compatible"
        if not self.settings.model_enabled:
            return {"ready": False, "name": self.settings.model,
                    "backend": backend, "available_models": [],
                    "error": MODEL_DISABLED_NOTICE}
        try:
            response = self.session.get(self.settings.base_url + ("/api/tags" if native else "/models"),
                                        timeout=3, allow_redirects=False)
            response.raise_for_status()
            if isinstance(response.status_code, int) and not 200 <= response.status_code < 300:
                raise requests.HTTPError("Model endpoint did not return HTTP success")
            names = [str(item.get("name" if native else "id", "")) for item in
                     response.json().get("models" if native else "data", [])]
            ready = self.settings.model in names
            return {"ready": ready, "name": self.settings.model,
                    "backend": backend, "available_models": names,
                    "error": None if ready else "Configured model is not served by the local endpoint"}
        except (requests.RequestException, ValueError, TypeError, AttributeError, KeyError) as error:
            return {"ready": False, "name": self.settings.model,
                    "backend": backend, "available_models": [],
                    "error": type(error).__name__ + ": local model endpoint unavailable"}

    def generate(self, messages: List[Dict[str, str]]) -> Dict:
        if not self.settings.model_enabled:
            raise ModelUnavailableError(MODEL_DISABLED_NOTICE)
        native = self.settings.provider == "ollama"
        try:
            payload = {"model": self.settings.model, "messages": messages, "stream": False}
            if native:
                # Native options bind the *actual* allocated context to the
                # RAG budget; old Ollama versions otherwise default to 2k.
                payload.update(options={"temperature": 0, "num_ctx": self.settings.context_window,
                                        "num_predict": self.settings.max_tokens, "num_batch": 128,
                                        "num_thread": 4}, keep_alive="2m")
            else:
                payload.update(temperature=0, max_tokens=self.settings.max_tokens)
                # Provider extension is opt-in. A small public-demo output
                # budget must not be consumed entirely by hidden reasoning.
                if self.settings.enable_thinking is not None:
                    payload["enable_thinking"] = self.settings.enable_thinking
            response = self.session.post(
                self.settings.base_url + ("/api/chat" if native else "/chat/completions"),
                json=payload, timeout=(5, self.settings.timeout), allow_redirects=False,
            )
            response.raise_for_status()
            if isinstance(response.status_code, int) and not 200 <= response.status_code < 300:
                raise requests.HTTPError("Model endpoint did not return HTTP success")
            result = response.json()
            reported_model = result.get("model", "" if native else self.settings.model)
            if reported_model != self.settings.model:
                raise ModelUnavailableError("Local endpoint returned a different model than configured")
            if native and result.get("done") is not True:
                raise ModelUnavailableError("Ollama returned an incomplete non-streaming response")
            answer = result["message"]["content"] if native else result["choices"][0]["message"]["content"]
            if not isinstance(answer, str) or not answer.strip():
                raise ModelUnavailableError("Local model returned an empty answer")
            usage = ({"prompt_tokens": result.get("prompt_eval_count"),
                      "completion_tokens": result.get("eval_count")} if native else result.get("usage", {}))
            finish = result.get("done_reason") if native else result["choices"][0].get("finish_reason")
            if finish in {"length", "limit"}:
                finish = "length"
            return {"answer": answer.strip(), "usage": usage,
                    "model": reported_model,
                    "finish_reason": finish}
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, AttributeError) as error:
            # Never echo server response bodies: they can contain prompt text or secrets.
            raise ModelUnavailableError("Local model inference failed: " + type(error).__name__) from error

    def close(self):
        self.session.close()
