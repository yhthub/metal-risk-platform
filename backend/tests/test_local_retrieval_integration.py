"""Local retrieval routing and bilingual evidence checks; no models or network."""
import asyncio
import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.agent import router
from app.rag_config import RagSettings
from app.services import rag_agent_service as rag
from app.services.retrieval_text import term_aliases, term_present


def local_hit(content=None):
    return {
        "chunk_id": "normative:fixture:1", "title": "职业镉暴露记录",
        "content": content or "职业镉暴露与肾损伤的资料，仅用于匹配测试，不代表现行规范或临床建议。" * 12,
        "source": "normative", "channel": "normative", "query_term_coverage": 1.0,
        "standard_no_or_doi": "GBZ 188-2025", "section_title": "附录测试条目",
        "source_url": "https://example.org/fixture-standard", "page": 3,
        "evidence_priority": "CN-OH-P0", "retrieval_channels": ["bm25"],
        "doi": None, "pmid": None,
    }


class RetrievalTextTests(unittest.TestCase):
    def test_chinese_and_english_terms_match_without_cjk_word_boundaries(self):
        for term in ("cadmium", "kidney", "renal", "injury"):
            self.assertTrue(term_present("本段讨论镉暴露与肾损伤。", term), term)
        self.assertTrue(term_present("Whole blood lead and blood pressure.", "血铅"))
        self.assertTrue(term_present("全血铅与血压。", "blood"))
        self.assertTrue(term_present("全血铅与血压。", "pressure"))

    def test_latin_boundaries_remain_intact(self):
        self.assertFalse(term_present("leadership", "lead"))
        self.assertFalse(term_present("kidneyish", "kidney"))
        self.assertTrue(term_present("lead-induced", "lead"))

    def test_unknown_concepts_and_negation_are_not_discarded(self):
        self.assertEqual(term_aliases("未知新概念"), ["未知新概念"])
        self.assertFalse(rag.anchors_present("镉暴露与肾损伤。", ["cadmium", "kidney", "未知新概念"]))
        self.assertFalse(rag.anchors_present("Cadmium kidney damage.", ["cadmium", "kidney", "not"]))
        self.assertFalse(rag.anchors_present("镉暴露与肾损伤。", ["cadmium", "kidney", "无"]))

    def test_population_requirement_is_not_discarded(self):
        self.assertFalse(rag.anchors_present("成年人的镉暴露与肾损伤。", ["cadmium", "kidney", "children"]))
        self.assertTrue(rag.anchors_present("儿童的镉暴露与肾损伤。", ["cadmium", "kidney", "children"]))

    def test_multiterm_concept_is_not_reduced_to_one_word(self):
        self.assertFalse(term_present("Cancer was assessed.", "肺癌"))
        self.assertTrue(term_present("Lung cancer was assessed.", "肺癌"))

    def test_long_chinese_excerpt_window_finds_bilingual_anchors(self):
        text = "一般说明。" * 300 + "本段讨论职业镉暴露与肾损伤。" * 15
        hit = local_hit(text)
        selected = rag.select_evidence([hit], 1, ["cadmium", "kidney", "injury"])
        context, cards = rag.evidence_context(selected, 1600, ["cadmium", "kidney", "injury"])
        self.assertEqual(len(cards), 1)
        self.assertGreater(cards[0]["context_offset"], 0)
        self.assertIn("镉暴露与肾损伤", context)
        self.assertLessEqual(len(context), 1600)

    def test_source_metadata_is_preserved_without_automatic_evidence_grade(self):
        context, cards = rag.evidence_context([local_hit()], 2000, ["cadmium", "kidney"])
        self.assertTrue(context)
        card = cards[0]
        self.assertEqual(card["channel"], "normative")
        self.assertEqual(card["standard_no_or_doi"], "GBZ 188-2025")
        self.assertEqual(card["section_title"], "附录测试条目")
        self.assertEqual(card["page"], 3)
        self.assertEqual(card["source_url"], card["url"])
        self.assertEqual(card["source_evidence_priority"], "CN-OH-P0")
        self.assertEqual(card["evidence_priority"], "UNASSESSED")
        self.assertIsNone(card["doi"])
        self.assertIsNone(card["pmid"])
        self.assertNotIn("mostly PubMed", rag.SYSTEM_PROMPT)
        self.assertIn("current validity", rag.SYSTEM_PROMPT)


class RetrievalFactoryTests(unittest.TestCase):
    def setUp(self):
        self.local_module = types.ModuleType("app.services.local_evidence_service")
        self.local_module.LocalEvidenceRetrievalService = Mock(return_value=object())

    def factory(self, *, platform, env):
        with patch.dict(os.environ, env, clear=True), patch.object(rag.os, "name", platform), \
             patch.dict(sys.modules, {"app.services.local_evidence_service": self.local_module}), \
             patch.object(rag, "HybridRetrievalService", return_value=object()) as medrr:
            result = rag.create_retriever()
        return result, medrr

    def test_windows_default_never_constructs_hybrid_or_dense_service(self):
        result, medrr = self.factory(platform="nt", env={})
        self.assertIs(result, self.local_module.LocalEvidenceRetrievalService.return_value)
        self.local_module.LocalEvidenceRetrievalService.assert_called_once_with()
        medrr.assert_not_called()

    def test_linux_default_preserves_existing_cloud_retriever(self):
        result, medrr = self.factory(platform="posix", env={})
        self.assertIs(result, medrr.return_value)
        self.local_module.LocalEvidenceRetrievalService.assert_not_called()

    def test_explicit_corpus_root_preserves_medrr_on_windows(self):
        result, medrr = self.factory(platform="nt", env={"RAG_CORPUS_ROOT": "D:/fixture-corpus"})
        self.assertIs(result, medrr.return_value)
        self.local_module.LocalEvidenceRetrievalService.assert_not_called()

    def test_explicit_local_backend_wins_without_dense_initialization(self):
        result, medrr = self.factory(platform="posix", env={
            "RAG_RETRIEVAL_BACKEND": "local_evidence", "RAG_CORPUS_ROOT": "/fixture-existing"})
        self.assertIs(result, self.local_module.LocalEvidenceRetrievalService.return_value)
        medrr.assert_not_called()

    def test_explicit_medrr_on_windows_is_respected(self):
        result, medrr = self.factory(platform="nt", env={"RAG_RETRIEVAL_BACKEND": "medrr"})
        self.assertIs(result, medrr.return_value)

    def test_unknown_backend_fails_instead_of_falling_back(self):
        with patch.dict(os.environ, {"RAG_RETRIEVAL_BACKEND": "misspelled"}, clear=True):
            with self.assertRaises(ValueError):
                rag.create_retriever()


class LocalSourceApiTests(unittest.TestCase):
    def setUp(self):
        self.retriever = types.SimpleNamespace(
            knowledge_bases=[{"id": "normative", "name": "本地规范资料"}],
            search=Mock(return_value={"hits": [local_hit()], "mode": "bm25"}),
        )
        self.service = types.SimpleNamespace(retriever=self.retriever,
                                             settings=types.SimpleNamespace(candidate_k=8))
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)
        self.service_patch = patch("app.api.agent.get_rag_service", return_value=self.service)
        self.service_patch.start()

    def tearDown(self):
        self.client.close()
        self.service_patch.stop()

    def test_knowledge_base_list_comes_from_selected_retriever(self):
        response = self.client.get("/api/agent/knowledge-bases")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.retriever.knowledge_bases)

    def test_legacy_cloud_knowledge_base_labels_remain_available(self):
        del self.retriever.knowledge_bases
        response = self.client.get("/api/agent/knowledge-bases")
        self.assertEqual([row["id"] for row in response.json()], ["pubmed", "textbooks", "statpearls"])

    def test_local_source_filter_is_forwarded_to_adapter(self):
        response = self.client.post("/api/agent/evidence-search", json={
            "query": "镉暴露与肾损伤", "sources": ["normative"], "mode": "bm25"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.retriever.search.call_args.args[3], ["normative"])

    def test_unknown_source_filter_is_rejected(self):
        response = self.client.post("/api/agent/evidence-search", json={
            "query": "test", "sources": ["not-a-source"]})
        self.assertEqual(response.status_code, 422)
        self.retriever.search.assert_not_called()

    def test_runtime_corpus_name_is_preserved(self):
        retriever = types.SimpleNamespace(status=lambda: {
            "ready": True, "mode": "bm25", "name": "本地职业金属暴露证据库"})
        model = types.SimpleNamespace(status=lambda: {"ready": False}, close=lambda: None)
        settings = RagSettings(model="fixture", base_url="http://unused", model_api_key="",
                               timeout=5, max_tokens=128, context_chars=2000,
                               top_k=2, candidate_k=8, concurrency=1)
        service = rag.RagAgentService(retriever=retriever, llm_factory=lambda: model, settings=settings)
        result = service.status()
        self.assertEqual(result["corpus"]["name"], "本地职业金属暴露证据库")
        self.assertFalse(result["rag_ready"])


if __name__ == "__main__":
    unittest.main()
