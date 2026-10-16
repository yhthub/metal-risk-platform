import asyncio
import unittest
from unittest.mock import patch
import test_rag_agent_service as rag_fixtures
from test_rag_agent_service import hit
from app.services.rag_agent_service import retrieval_query, evidence_context, select_evidence, validate_citations, InvalidGenerationError
from app.services.prompt_budget import PromptBudget
from app.services.hybrid_retrieval_service import untranslated_segments


class GuardrailTests(unittest.TestCase):
    def test_independent_short_question_does_not_inherit_prior_topic(self):
        self.assertEqual(retrieval_query("What causes hypertension?", [{"role": "user", "content": "lead toxicity"}]),
                         "What causes hypertension?")

    def test_explicit_followup_uses_prior_user_only(self):
        query = retrieval_query("那它有什么影响？", [{"role": "user", "content": "铅"},
                                                    {"role": "assistant", "content": "fake"}])
        self.assertIn("铅", query)
        self.assertNotIn("fake", query)

    def test_missing_core_entity_does_not_pass_by_partial_overlap(self):
        candidate = hit(coverage=0.8, content="Kidney injury and occupational exposure " * 20)
        self.assertEqual(select_evidence([candidate], 3, ["novelcompound", "kidney", "occupational", "exposure"]), [])

    def test_excerpt_window_keeps_critical_entity_in_tail(self):
        candidate = hit(content="irrelevant introduction " * 150 + "cadmium kidney injury " * 30)
        context, cards = evidence_context([candidate], 2200, ["cadmium", "kidney"])
        self.assertEqual(len(cards), 1)
        self.assertGreater(cards[0]["context_offset"], 0)
        self.assertIn("cadmium", cards[0]["context_excerpt"])
        self.assertLessEqual(len(context), 2200)

    def test_separate_distant_entities_do_not_pass_excerpt_coverage(self):
        candidate = hit(content="cadmium " + "irrelevant " * 700 + "kidney " * 30)
        self.assertEqual(evidence_context([candidate], 1000, ["cadmium", "kidney"])[1], [])

    def test_invented_doi_pmid_and_standard_rejected(self):
        cards = [{"citation_id": "E1", "chunk_id": "one", "title": "Fixture", "context_excerpt": "No identifiers."}]
        for answer in ("10.1234/fake [E1]", "PMID: 123456 [E1]", "GBZ 2.1-2019 [E1]"):
            with self.assertRaises(InvalidGenerationError):
                validate_citations(answer, cards)

    def test_identifier_in_prompt_excerpt_can_be_quoted(self):
        cards = [{"citation_id": "E1", "chunk_id": "one", "title": "Fixture", "context_excerpt": "DOI 10.1234/test"}]
        self.assertEqual(validate_citations("DOI 10.1234/test [E1]", cards)[0]["id"], "E1")

    def test_abstention_without_citation_is_not_an_answered_result(self):
        fixture = rag_fixtures.RagOrchestrationTests()
        fixture.setUp()
        fixture.model.answer = "INSUFFICIENT_EVIDENCE: snippets do not answer this question."
        result = fixture.chat()
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["citations"], [])
        self.assertTrue(result["model"]["invoked"])

    def test_utf8_budget_fallback_is_explicit_and_conservative(self):
        budget = PromptBudget()
        budget.checked = True
        messages = [{"role": "user", "content": "中文question"}]
        self.assertGreater(budget.count(messages), len("中文question".encode("utf-8")))
        self.assertIn("conservative", budget.method)

    def test_unknown_chinese_entity_is_not_silently_dropped(self):
        self.assertIn("新型未知病", untranslated_segments("镉与新型未知病有关吗"))
        self.assertEqual(untranslated_segments("职业铅暴露与高血压的关系"), [])

    def test_requested_human_population_does_not_accept_rat_only_excerpt(self):
        candidate = hit(content="Rat cadmium kidney injury " * 20)
        self.assertEqual(select_evidence([candidate], 3, ["cadmium", "kidney", "humans"]), [])
