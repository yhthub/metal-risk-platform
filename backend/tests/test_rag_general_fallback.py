"""Visible general-knowledge fallback; fixture-only, no corpus/model requests."""
import asyncio
import copy
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.agent import router
from app.services.corpus_retrieval_service import CorpusUnavailable, RetrievalTimeout
from app.services.local_llm_service import ModelUnavailableError
from app.services.rag_agent_service import (
    GENERAL_KNOWLEDGE_NOTICE, InvalidGenerationError, RagAgentService,
)
import test_rag_agent_service as rag_fixtures
from test_rag_agent_service import hit


class GeneralFallbackTests(unittest.TestCase):
    def setUp(self):
        self.fixture = rag_fixtures.RagOrchestrationTests()
        self.fixture.setUp()
        self.service = self.fixture.service
        self.service.allow_general_fallback = True
        self.retriever = self.fixture.retriever
        self.model = self.fixture.model
        self.model.answer = "这是一般性医学知识说明。该问题仍需更多信息，不能据此作个人诊断。"
        # Do not even load a local tokenizer asset during these offline tests.
        self.service.prompt_budget.checked = True

    def chat(self, message="Fixture question", **kwargs):
        return asyncio.run(self.service.chat(message, **kwargs))

    def assert_general(self, result):
        self.assertEqual(result["status"], "general_answer")
        self.assertEqual(result["answer_mode"], "general_knowledge")
        self.assertEqual(result["evidence_support"], "none")
        self.assertFalse(result["evidence_supported"])
        self.assertTrue(result["model"]["invoked"])
        self.assertEqual(result["citations"], [])
        self.assertEqual(result["evidence_cards"], [])
        self.assertEqual(result["cited_knowledge_bases"], [])
        self.assertEqual(result["retrieval"]["selected_count"], 0)
        self.assertTrue(result["answer"].startswith(GENERAL_KNOWLEDGE_NOTICE))
        self.assertIn(GENERAL_KNOWLEDGE_NOTICE, result["warnings"])

    def test_no_hits_invokes_real_generation_interface_with_explicit_label(self):
        self.retriever.hits = []
        result = self.chat()
        self.assert_general(result)
        self.assertEqual(len(self.model.calls), 1)
        self.assertEqual(result["retrieval"]["diagnostics"]["fallback_reason"], "no_matching_excerpts")
        self.assertIn(self.model.answer, result["answer"])
        self.assertEqual(self.model.close_calls, 1)

    def test_low_coverage_is_not_passed_as_support_to_general_model(self):
        self.retriever.hits = [hit(coverage=0.5, content="UNRELATED CANDIDATE TEXT " * 15)]
        result = self.chat()
        self.assert_general(result)
        self.assertNotIn("UNRELATED CANDIDATE TEXT", str(self.model.calls[0]))

    def test_unknown_chinese_preserves_original_question_without_partial_chunks(self):
        candidate = hit(content="PARTIAL CADMIUM EVIDENCE " * 15)
        with patch.object(self.retriever, "search", return_value={
            "mode": "bm25", "hits": [candidate], "sparse_hits": [candidate], "dense_hits": [],
            "diagnostics": {"untranslated_segments": ["新型未知病"], "query_terms": [],
                            "warnings": ["中文术语字典未覆盖部分词语；不丢弃未知概念来生成回答，请提供完整英文问题。"]},
        }):
            result = self.chat("镉与新型未知病有关吗？")
        self.assert_general(result)
        self.assertEqual(result["retrieval"]["diagnostics"]["fallback_reason"], "query_translation_incomplete")
        prompt = self.model.calls[0][1]["content"]
        self.assertIn("镉与新型未知病有关吗？", prompt)
        self.assertNotIn("PARTIAL CADMIUM EVIDENCE", prompt)
        self.assertFalse(any("请提供完整英文问题" in value for value in result["warnings"]))

    def test_general_prompt_retains_medical_boundary_and_excludes_assistant_history(self):
        self.retriever.hits = []
        result = self.chat("那它应该怎么治疗？", history=[
            {"role": "user", "content": "铅暴露"},
            {"role": "assistant", "content": "UNVERIFIED PERSONAL TREATMENT"},
        ])
        self.assert_general(result)
        prompt = self.model.calls[0]
        self.assertIn("铅暴露", prompt[1]["content"])
        self.assertIn("那它应该怎么治疗？", prompt[1]["content"])
        self.assertNotIn("UNVERIFIED PERSONAL TREATMENT", str(prompt))
        self.assertIn("Do not diagnose, prescribe a dose", prompt[0]["content"])
        self.assertIn("if an unfamiliar term or relationship is unknown, say so", prompt[0]["content"])

    def test_retrieval_known_failures_are_diagnosed_not_reported_as_dual_success(self):
        for error, expected in [(CorpusUnavailable("private location"), "retrieval_unavailable"),
                                (RetrievalTimeout("private query"), "retrieval_timeout")]:
            with self.subTest(error=type(error).__name__), patch.object(self.retriever, "search", side_effect=error):
                result = self.chat()
            self.assert_general(result)
            self.assertEqual(result["retrieval"]["mode"], "unavailable")
            self.assertTrue(result["retrieval"]["degraded"])
            diagnostics = result["retrieval"]["diagnostics"]
            self.assertEqual(diagnostics["fallback_reason"], expected)
            self.assertEqual(diagnostics["error_type"], type(error).__name__)
            self.assertFalse(diagnostics["dual_route_executed"])
            self.assertFalse(diagnostics["independent_dense_recall"])
            self.assertFalse(diagnostics["channels"]["bm25"]["ready"])
            self.assertFalse(diagnostics["channels"]["medcpt"]["ready"])
            self.assertNotIn("private", str(result))

    def test_unexpected_retriever_bug_is_not_silently_swallowed(self):
        with patch.object(self.retriever, "search", side_effect=RuntimeError("fixture code failure")):
            with self.assertRaises(RuntimeError):
                self.chat()
        self.assertEqual(self.model.calls, [])

    def test_general_answer_rejects_invented_citations_identifiers_and_source_links(self):
        self.retriever.hits = []
        for answer in ("Fake [E1].", "Fake [E 99].", "Fake [1].", "DOI 10.1234/fake", "PMID: 12345",
                       "GBZ 2.1-2019", "Source https://example.invalid/paper", "PMID：12345",
                       "参考文献：\nFake author. Invented paper.", "## Sources\nAn invented paper."):
            with self.subTest(answer=answer):
                self.model.answer = answer
                with self.assertRaises(InvalidGenerationError):
                    self.chat()
        self.model.answer = "一般信息需要结合具体情况解读。"
        self.assert_general(self.chat())

    def test_model_transport_failure_is_not_converted_to_fake_answer(self):
        self.retriever.hits = []
        self.model.error = ModelUnavailableError("fixture unavailable")
        with self.assertRaises(ModelUnavailableError):
            self.chat()
        self.assertEqual(self.model.close_calls, 1)
        self.model.error = None
        self.assert_general(self.chat())

    def test_grounded_answer_preserves_original_citation_validation(self):
        self.model.answer = "Fixture supported explanation [E1]."
        result = self.chat()
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["answer_mode"], "retrieval_grounded")
        self.assertEqual(result["evidence_support"], "retrieved_excerpts")
        self.assertTrue(result["evidence_supported"])
        self.assertEqual(result["citations"][0]["id"], "E1")
        self.assertEqual(len(self.model.calls), 1)
        self.model.answer = "Unsupported missing citation."
        with self.assertRaises(InvalidGenerationError):
            self.chat()

    def test_model_excerpt_abstention_uses_separate_ungrounded_generation(self):
        answers = iter(["INSUFFICIENT_EVIDENCE: excerpt does not answer the question.",
                        "这个问题的一般性解释仍有不确定性。"])

        def generate(messages):
            self.model.calls.append(copy.deepcopy(messages))
            return {"answer": next(answers), "model": "Llama-3.1-8B", "finish_reason": "stop"}

        with patch.object(self.model, "generate", side_effect=generate):
            result = self.chat()
        self.assert_general(result)
        self.assertEqual(len(self.model.calls), 2)
        self.assertIn("BEGIN UNTRUSTED EXCERPTS", self.model.calls[0][1]["content"])
        self.assertNotIn("BEGIN UNTRUSTED EXCERPTS", self.model.calls[1][1]["content"])
        self.assertEqual(result["retrieval"]["candidate_evidence_count"], 1)
        self.assertEqual(result["retrieval"]["diagnostics"]["fallback_reason"], "excerpts_insufficient_for_answer")

    def test_explicit_strict_mode_preserves_no_model_absent_term_probe(self):
        self.service.allow_general_fallback = False
        self.retriever.hits = []
        result = self.chat("quazylophenezn42 kidney")
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["answer_mode"], "strict_abstention")
        self.assertFalse(result["model"]["invoked"])
        self.assertEqual(self.model.calls, [])
        with patch.object(self.retriever, "search", side_effect=RetrievalTimeout("fixture")):
            with self.assertRaises(RetrievalTimeout):
                self.chat()

    def test_default_and_environment_strict_switch_are_explicit(self):
        for value, expected in [("true", True), ("false", False)]:
            with self.subTest(value=value), patch.dict("os.environ", {"RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK": value}):
                service = RagAgentService(self.retriever, lambda: self.model, self.service.settings)
            self.assertEqual(service.allow_general_fallback, expected)
        with patch.dict("os.environ", {}, clear=True):
            self.assertTrue(RagAgentService(self.retriever, lambda: self.model, self.service.settings).allow_general_fallback)

    def test_model_ready_retrieval_missing_status_is_general_only_not_rag_ready(self):
        with patch.object(self.retriever, "status", return_value={"ready": False, "corpus_ready": False, "mode": "hybrid"}):
            result = self.service.status()
        self.assertEqual(result["status"], "general_only")
        self.assertTrue(result["can_chat"])
        self.assertFalse(result["rag_ready"])
        self.assertTrue(result["general_fallback_enabled"])

    def test_missing_model_cannot_chat_even_with_fallback(self):
        with patch.object(self.model, "status", return_value={"ready": False}):
            result = self.service.status()
        self.assertEqual(result["status"], "not_ready")
        self.assertFalse(result["can_chat"])
        self.assertFalse(result["rag_ready"])

    def test_strict_missing_retrieval_cannot_chat_even_when_model_ready(self):
        self.service.allow_general_fallback = False
        with patch.object(self.retriever, "status", return_value={"ready": False, "corpus_ready": False}):
            result = self.service.status()
        self.assertEqual(result["status"], "not_ready")
        self.assertFalse(result["can_chat"])
        self.assertFalse(result["rag_ready"])
        self.assertFalse(result["general_fallback_enabled"])

    def test_excerpts_outside_context_budget_fall_back_without_using_them(self):
        def count(messages):
            return 5000 if "BEGIN UNTRUSTED EXCERPTS" in str(messages) else 100

        with patch.object(self.service.prompt_budget, "count", side_effect=count):
            result = self.chat()
        self.assert_general(result)
        self.assertEqual(result["retrieval"]["diagnostics"]["fallback_reason"], "excerpts_do_not_fit_context_budget")
        self.assertNotIn("BEGIN UNTRUSTED EXCERPTS", self.model.calls[0][1]["content"])

    def test_general_html_is_escaped_and_truncation_remains_visible(self):
        self.retriever.hits = []
        self.model.answer = '<script>alert("fixture")</script>'
        self.model.finish_reason = "length"
        result = self.chat()
        self.assert_general(result)
        self.assertNotIn("<script>", result["message"])
        self.assertIn("&lt;script&gt;", result["message"])
        self.assertTrue(result["generation_truncated"])

    def test_context_budget_and_invalid_model_still_reject_before_generation(self):
        self.retriever.hits = []
        with self.assertRaises(ValueError):
            self.chat("中" * 2000)
        with self.assertRaises(ValueError):
            self.chat(model="unconfigured")
        self.assertEqual(self.model.calls, [])


class GeneralFallbackApiTests(unittest.TestCase):
    def setUp(self):
        self.fixture = GeneralFallbackTests()
        self.fixture.setUp()
        self.fixture.retriever.hits = []
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)
        self.service_patch = patch("app.api.agent.get_rag_service", return_value=self.fixture.service)
        self.service_patch.start()

    def tearDown(self):
        self.client.close()
        self.service_patch.stop()

    def test_chat_general_success_returns_explicit_ungrounded_contract(self):
        response = self.client.post("/api/agent/chat", json={"message": "Fixture question"})
        self.assertEqual(response.status_code, 200)
        self.fixture.assert_general(response.json())

    def test_missing_retrieval_with_missing_model_still_returns_503(self):
        self.fixture.model.error = ModelUnavailableError("fixture unavailable")
        with patch.object(self.fixture.retriever, "search", side_effect=CorpusUnavailable("fixture missing index")):
            response = self.client.post("/api/agent/chat", json={"message": "Fixture question"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(GENERAL_KNOWLEDGE_NOTICE, response.text)

    def test_unsupported_general_citation_returns_502(self):
        self.fixture.model.answer = "Fabricated result [E123]."
        response = self.client.post("/api/agent/chat", json={"message": "Fixture question"})
        self.assertEqual(response.status_code, 502)

    def test_strict_retrieval_errors_preserve_503_504(self):
        self.fixture.service.allow_general_fallback = False
        for error, code in [(CorpusUnavailable("fixture"), 503), (RetrievalTimeout("fixture"), 504)]:
            with self.subTest(code=code), patch.object(self.fixture.retriever, "search", side_effect=error):
                response = self.client.post("/api/agent/chat", json={"message": "Fixture question"})
            self.assertEqual(response.status_code, code)
        self.assertEqual(self.fixture.model.calls, [])


if __name__ == "__main__":
    unittest.main()
