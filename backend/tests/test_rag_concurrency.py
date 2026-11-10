"""Concurrent HTTP requests through the real QA pipeline, with a controlled provider."""
import asyncio
import re
import threading
from collections import Counter

import httpx
from fastapi import FastAPI
import pytest

from app.api import agent
from app.rag_config import RagSettings
from app.services.rag_agent_service import RagAgentService


def test_twenty_simultaneous_chats_are_isolated_and_share_four_model_keys(monkeypatch):
    keys = ["fixture-primary", "fixture-second", "fixture-third", "fixture-fourth"]
    monkeypatch.setenv("RAG_MAX_CONCURRENT_GENERATIONS", "20")
    monkeypatch.setenv("RAG_LLM_API_KEY", keys[0])
    monkeypatch.setenv("RAG_LLM_EXTRA_API_KEYS", '["fixture-second","fixture-third","fixture-fourth"]')
    monkeypatch.setenv("RAG_ANSWER_STRATEGY", "knowledge_evidence_synthesis")
    monkeypatch.setenv("RAG_LLM_CONTEXT_WINDOW", "16384")
    monkeypatch.setenv("RAG_LLM_MODEL", "fixture-model")
    settings = RagSettings.from_env()
    all_inside = threading.Event()
    finish = threading.Event()
    lock = threading.Lock()
    auth = []

    class Retriever:
        mode = "bm25"
        knowledge_bases = ["pubmed"]

        def search(self, query, **kwargs):
            return dict(mode="bm25", hits=[], sparse_hits=[], dense_hits=[], degraded=False,
                        diagnostics={"backend": "combined_bm25", "warnings": []})

    def post(session, url, *, json, headers, **kwargs):
        question = json["messages"][-1]["content"]
        visitor, = re.findall(r"visitor-\d+", question)
        with lock:
            auth.append(headers["Authorization"])
            if len(auth) == 20:
                all_inside.set()
        assert finish.wait(15)
        return httpx.Response(200, request=httpx.Request("POST", url), json={
            "model": settings.model, "choices": [{"message": {"content": f"Own answer for {visitor}."},
                                                  "finish_reason": "stop"}]})

    monkeypatch.setattr("requests.Session.post", post)
    service = RagAgentService(Retriever(), settings=settings, allow_general_fallback=True)
    monkeypatch.setattr(agent, "get_rag_service", lambda: service)
    app = FastAPI()
    app.include_router(agent.router)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            url = "/api/agent/chat"
            tasks = [asyncio.create_task(client.post(url, json={"message": f"Question from visitor-{i}"}))
                     for i in range(20)]
            try:
                assert await asyncio.to_thread(all_inside.wait, 10)
                assert Counter(auth) == Counter({"Bearer " + key: 5 for key in keys})
                assert (await client.post(url, json={"message": "overflow"})).status_code == 429
            finally:
                finish.set()
            for i, response in enumerate(await asyncio.gather(*tasks)):
                assert response.status_code == 200
                result = response.json()
                assert result["answer"].endswith(f"Own answer for visitor-{i}.")
                assert result["answer_mode"] == "general_knowledge"
            assert (await client.post(url, json={"message": "Next visitor-20"})).status_code == 200

    try:
        asyncio.run(exercise())
    finally:
        finish.set()
        service.chat_executor.shutdown(wait=True)


def test_config_limits_and_hides_model_credentials(monkeypatch):
    monkeypatch.setenv("RAG_MAX_CONCURRENT_GENERATIONS", "50")
    monkeypatch.setenv("RAG_LLM_API_KEY", "fixture-primary")
    monkeypatch.setenv("RAG_LLM_EXTRA_API_KEYS", '["fixture-second"]')
    settings = RagSettings.from_env()
    assert settings.concurrency == 20 and settings.extra_model_keys == ("fixture-second",)
    assert "fixture-primary" not in repr(settings) and "fixture-second" not in repr(settings)
    monkeypatch.setenv("RAG_LLM_EXTRA_API_KEYS", '"fixture-second"')
    with pytest.raises(ValueError, match="JSON array"):
        RagSettings.from_env()
