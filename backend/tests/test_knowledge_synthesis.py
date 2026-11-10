"""Knowledge-first RAG orchestration, using synthetic fixtures only.

These tests establish request isolation, limits and citation bookkeeping, not
medical correctness or whether a model's cited claim is entailed by an excerpt.
"""
import asyncio
import copy
import json
import re
import unittest
from unittest.mock import patch

from app.rag_config import RagSettings
from app.services.local_llm_service import ModelUnavailableError
from app.services.rag_agent_service import (
    InvalidGenerationError, RagAgentService, evidence_context,
)


PRELIMINARY = "UNVERIFIED_BRIEF_MARKER: A preliminary explanation; the relation needs checking."
FINAL = "General background is distinguished from the supplied synthetic observation [E1]."


def generated(answer, *, finish="stop", usage=None):
    return {"answer": answer, "model": "fixture-no-model", "finish_reason": finish,
            "usage": usage or {"prompt_tokens": 21, "completion_tokens": 13, "total_tokens": 34}}


class FixtureModel:
    def __init__(self, responses, default_max_tokens=3200):
        self.responses = list(responses)
        self.default_max_tokens = default_max_tokens
        self.calls = []
        self.close_calls = 0

    def generate(self, messages, *, max_tokens=None):
        self.calls.append({"messages": copy.deepcopy(messages), "max_tokens": max_tokens,
                           "effective_max_tokens": self.default_max_tokens if max_tokens is None else max_tokens})
        if not self.responses:
            raise AssertionError("Unexpected additional model call")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return copy.deepcopy(response)

    def close(self):
        self.close_calls += 1


class FixtureRetriever:
    mode = "bm25"
    knowledge_bases = ["pubmed"]

    def __init__(self, count=5):
        self.calls = []
        self.hits = [{"chunk_id": f"synthetic/{index}", "source": "pubmed",
                      "title": f"Synthetic source {index}", "doi": None, "pmid": None,
                      "content": (f"EXCERPT_ONLY_MARKER_{index}: synthetic cadmium kidney paragraph. " * 7),
                      "score": -float(index + 1), "score_type": "fts5_bm25_lower_is_better",
                      "retrieval_channels": ["bm25"]} for index in range(count)]

    def search(self, query, **kwargs):
        self.calls.append({"query": query, **kwargs})
        hits = copy.deepcopy(self.hits)
        return {"mode": "bm25", "hits": hits, "sparse_hits": hits, "dense_hits": [], "degraded": False,
                "diagnostics": {"backend": "combined_bm25", "query_terms": ["cadmium", "kidney"],
                                "warnings": [], "candidates_retrieved": len(hits)}}


class KnowledgeSynthesisTests(unittest.TestCase):
    def make_service(self, responses=None, *, count=5, allow_general=True,
                     strategy="knowledge_evidence_synthesis", max_tokens=3200):
        settings = RagSettings(model="fixture-no-model", base_url="http://unused", model_api_key="",
                               timeout=5, max_tokens=max_tokens, context_chars=6000,
                               top_k=5, candidate_k=32, concurrency=1, context_window=16384,
                               answer_strategy=strategy)
        model = FixtureModel(responses if responses is not None else [generated(PRELIMINARY), generated(FINAL)],
                             default_max_tokens=max_tokens)
        retriever = FixtureRetriever(count)
        service = RagAgentService(retriever, lambda: model, settings, allow_general_fallback=allow_general)
        service.prompt_budget.checked = True  # Never inspect a tokenizer/model asset.
        return service, retriever, model

    @staticmethod
    def chat(service, question="cadmium kidney", **kwargs):
        return asyncio.run(service.chat(question, **kwargs))

    @staticmethod
    def text(call):
        return "\n".join(message["content"] for message in call["messages"])

    def test_preparation_is_question_only_and_final_retains_question_context_and_ranked_excerpts(self):
        service, retriever, model = self.make_service()
        question = "那么职业镉暴露是否不会影响儿童的未知新病？"
        history = [{"role": "user", "content": "PRIOR_USER_MARKER: cadmium kidney in children"},
                   {"role": "assistant", "content": "PRIOR_ASSISTANT_MARKER: invented conclusion."}]
        result = self.chat(service, question, history=history)
        self.assertEqual(len(model.calls), 2)
        self.assertEqual([call["effective_max_tokens"] for call in model.calls], [640, 3200])
        self.assertEqual(model.calls[0]["max_tokens"], 640)
        for call in model.calls:
            self.assertIn(question, self.text(call))
            self.assertIn("PRIOR_USER_MARKER", self.text(call))
            self.assertNotIn("PRIOR_ASSISTANT_MARKER", self.text(call))
            self.assertNotIn("assistant", [message["role"] for message in call["messages"]])
        self.assertNotIn("EXCERPT_ONLY_MARKER", self.text(model.calls[0]))
        self.assertNotIn("Synthetic source", self.text(model.calls[0]))
        self.assertIn(PRELIMINARY, self.text(model.calls[1]))
        for index in range(5):
            self.assertIn(f"EXCERPT_ONLY_MARKER_{index}", self.text(model.calls[1]))
        self.assertEqual([card["chunk_id"] for card in result["evidence_cards"]],
                         [hit["chunk_id"] for hit in retriever.hits])
        self.assertEqual(result["retrieval"]["selected_count"], 5)

    def test_mixed_support_and_usage_do_not_claim_full_grounding_or_expose_preliminary_text(self):
        prep_usage = {"prompt_tokens": 71, "completion_tokens": 19, "total_tokens": 90}
        final_usage = {"prompt_tokens": 181, "completion_tokens": 41, "total_tokens": 222}
        service, _, model = self.make_service([generated(PRELIMINARY, usage=prep_usage), generated(FINAL, usage=final_usage)])
        result = self.chat(service)
        self.assertEqual(result["answer_mode"], "knowledge_evidence_synthesis")
        self.assertEqual(result["evidence_support"], "mixed_model_knowledge_and_retrieved_excerpts")
        self.assertFalse(result["evidence_supported"])
        self.assertTrue(result["has_retrieval_support"])
        self.assertEqual([citation["id"] for citation in result["citations"]], ["E1"])
        self.assertEqual(result["preparation"]["usage"], prep_usage)
        self.assertTrue(result["preparation"]["invoked"])
        self.assertTrue(result["preparation"]["used"])
        self.assertEqual(result["usage"], final_usage)
        self.assertIsNone(result["think_process"])
        self.assertNotIn(PRELIMINARY, json.dumps(result, ensure_ascii=False))
        self.assertEqual(len(model.calls), 2)

    def test_no_hits_go_directly_to_one_general_generation(self):
        service, _, model = self.make_service([generated("A general explanation without literature claims.")], count=0)
        result = self.chat(service)
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(model.calls[0]["effective_max_tokens"], 3200)
        self.assertFalse(result.get("preparation", {}).get("invoked", False))
        self.assertEqual(result["answer_mode"], "general_knowledge")
        self.assertEqual(result["evidence_support"], "none")
        self.assertEqual(result["retrieval"]["selected_count"], 0)
        self.assertEqual(result["evidence_cards"], [])

    def test_final_without_citations_is_general_without_a_third_call_and_keeps_actual_context_count(self):
        answer = "This is a general explanation, without a supported conclusion from the excerpts."
        service, _, model = self.make_service([generated(PRELIMINARY), generated(answer)])
        result = self.chat(service)
        self.assertEqual(len(model.calls), 2)
        self.assertEqual(result["status"], "general_answer")
        self.assertEqual(result["answer_mode"], "general_knowledge")
        self.assertEqual(result["evidence_support"], "none")
        self.assertFalse(result["evidence_supported"])
        self.assertFalse(result["has_retrieval_support"])
        self.assertEqual(result["evidence_cards"], [])
        self.assertEqual(result["citations"], [])
        self.assertEqual(result["retrieval"]["selected_count"], 5)
        self.assertIn(answer, result["answer"])

    def test_final_abstention_is_returned_without_marker_or_extra_general_generation(self):
        service, _, model = self.make_service([generated(PRELIMINARY),
                                             generated("INSUFFICIENT_EVIDENCE: The relationship cannot be established.")])
        result = self.chat(service)
        self.assertEqual(len(model.calls), 2)
        self.assertEqual(result["answer_mode"], "strict_abstention")
        self.assertFalse(result["evidence_supported"])
        self.assertNotIn("INSUFFICIENT_EVIDENCE", result["answer"])
        self.assertIn("The relationship cannot be established.", result["answer"])

    def test_preliminary_citations_and_identifiers_are_discarded_not_promoted_to_sources(self):
        for brief in ("A preliminary unsupported source [E99].", "Preliminary DOI 10.1234/brief-only."):
            with self.subTest(brief=brief):
                service, _, model = self.make_service([generated(brief), generated(FINAL)])
                result = self.chat(service)
                self.assertEqual(len(model.calls), 2)
                self.assertFalse(result["preparation"]["used"])
                self.assertTrue(result["preparation"]["discard_reason"])
                self.assertNotIn(brief, self.text(model.calls[1]))
                self.assertEqual([citation["id"] for citation in result["citations"]], ["E1"])
                self.assertNotIn(brief, json.dumps(result, ensure_ascii=False))

    def test_final_unknown_citations_and_preliminary_only_identifier_still_fail_without_a_third_call(self):
        answers = ("Invented citation [E99].", "Real citation [E1] and invented [E1, E99].",
                   "Supplied [E1], unknown [E99], and [supplement](https://example.org/reading).",
                   "Copied preliminary DOI 10.1234/brief-only [E1].")
        for answer in answers:
            with self.subTest(answer=answer):
                brief = "Preliminary DOI 10.1234/brief-only."
                service, _, model = self.make_service([generated(brief), generated(answer)])
                with self.assertRaises(InvalidGenerationError):
                    self.chat(service)
                self.assertEqual(len(model.calls), 2)
                self.assertNotIn(brief, self.text(model.calls[1]))

    def test_external_links_and_doi_url_do_not_become_retrieved_citations(self):
        for external in ("[WHO](https://www.who.int/)", "http://example.org/supplement", "www.cdc.gov",
                         "[Supplementary reading](https://doi.org/10.1234/supplement-only)"):
            with self.subTest(external=external):
                service, _, model = self.make_service([
                    generated(PRELIMINARY), generated(f"Synthetic sourced finding [E1]. Further source: {external}.")])
                result = self.chat(service)
                self.assertEqual(len(model.calls), 2)
                self.assertIn(external, result["answer"])
                self.assertEqual(result["answer_mode"], "knowledge_evidence_synthesis")
                self.assertEqual([citation["id"] for citation in result["citations"]], ["E1"])
                self.assertEqual([citation["chunk_id"] for citation in result["citations"]], ["synthetic/0"])
                self.assertEqual([card["citation_id"] for card in result["evidence_cards"] if card["is_cited"]], ["E1"])
                self.assertNotIn("supplement-only", json.dumps(result["citations"]))
                self.assertNotIn("supplement-only", json.dumps(result["evidence_cards"]))

    def test_supplementary_reference_format_does_not_expand_retrieved_citations(self):
        for supplement in ("Supplementary reference [1].", "Supplementary references [1,2].",
                           "Supplementary references [1-3].",
                           "## References\n[Further reading](https://example.org/reading)",
                           "### 参考文献\n[补充阅读](https://example.org/reading)",
                           "**Sources:**\n[Further reading](https://example.org/reading)"):
            with self.subTest(supplement=supplement):
                service, _, model = self.make_service([
                    generated(PRELIMINARY), generated(f"Synthetic sourced finding [E1].\n\n{supplement}")])
                result = self.chat(service)
                self.assertEqual(len(model.calls), 2)
                self.assertIn(supplement, result["answer"])
                self.assertEqual([citation["id"] for citation in result["citations"]], ["E1"])
                self.assertEqual(result["cited_knowledge_bases"], ["pubmed"])

    def test_external_links_without_evidence_citations_remain_general_without_a_third_call(self):
        for external in ("[Further reading](https://example.org/reading)",
                         "[Further reading](https://doi.org/10.1234/supplement-only)"):
            with self.subTest(external=external):
                service, _, model = self.make_service([
                    generated(PRELIMINARY), generated(f"A general explanation. Supplementary reading: {external}.")])
                result = self.chat(service)
                self.assertEqual(len(model.calls), 2)
                self.assertIn(external, result["answer"])
                self.assertEqual(result["answer_mode"], "general_knowledge")
                self.assertEqual(result["status"], "general_answer")
                self.assertEqual(result["evidence_support"], "none")
                self.assertFalse(result["evidence_supported"])
                self.assertFalse(result["has_retrieval_support"])
                self.assertEqual(result["citations"], [])
                self.assertEqual(result["evidence_cards"], [])
                self.assertEqual(result["cited_knowledge_bases"], [])
                self.assertEqual(result["retrieval"]["selected_count"], 5)

    def test_no_hits_allows_supplemental_links_without_creating_retrieval_support(self):
        service, _, model = self.make_service(
            [generated("General explanation. Further reading: [WHO](https://www.who.int/).")], count=0)
        result = self.chat(service)
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(result["answer_mode"], "general_knowledge")
        self.assertEqual(result["citations"], [])
        self.assertEqual(result["evidence_cards"], [])
        self.assertFalse(result["supplemental_links"]["verified_by_retrieval"])
        self.assertIn("https://www.who.int/", result["answer"])

    def test_preliminary_numbers_do_not_enter_cards_or_citation_provenance(self):
        brief = "UNVERIFIED_NUMERIC_MARKER: 731 participants and a 42 percent estimate need verification."
        service, _, model = self.make_service([generated(brief), generated(FINAL)])
        result = self.chat(service)
        self.assertEqual(len(model.calls), 2)
        self.assertTrue(result["preparation"]["used"])
        self.assertIn(brief, self.text(model.calls[1]))
        self.assertNotIn("731", json.dumps(result["evidence_cards"]))
        self.assertNotIn("731", json.dumps(result["citations"]))
        self.assertNotIn("UNVERIFIED_NUMERIC_MARKER", json.dumps(result))
        self.assertEqual(result["citations"][0]["chunk_id"], "synthetic/0")

    def test_truncated_preparation_is_discarded_without_retry(self):
        service, _, model = self.make_service([generated(PRELIMINARY, finish="length"), generated(FINAL)])
        result = self.chat(service)
        self.assertEqual(len(model.calls), 2)
        self.assertTrue(result["preparation"]["invoked"])
        self.assertFalse(result["preparation"]["used"])
        self.assertTrue(result["preparation"]["discard_reason"])
        self.assertNotIn(PRELIMINARY, self.text(model.calls[1]))
        self.assertFalse(result.get("generation_truncated", False))

    def test_final_truncation_remains_visible(self):
        service, _, model = self.make_service([generated(PRELIMINARY), generated(FINAL, finish="length")])
        result = self.chat(service)
        self.assertEqual(len(model.calls), 2)
        self.assertTrue(result["generation_truncated"])

    def test_preparation_is_dropped_before_budget_shrinks_the_five_excerpts(self):
        service, _, model = self.make_service()
        original_count = service.prompt_budget.count

        def count(messages):
            if PRELIMINARY in "\n".join(message["content"] for message in messages):
                return service.settings.context_window
            return original_count(messages)

        with patch.object(service.prompt_budget, "count", side_effect=count):
            with patch("app.services.rag_agent_service.evidence_context", wraps=evidence_context) as context:
                result = self.chat(service)
        self.assertEqual(len(model.calls), 2)
        self.assertFalse(result["preparation"]["used"])
        self.assertNotIn(PRELIMINARY, self.text(model.calls[1]))
        self.assertEqual(result["retrieval"]["selected_count"], 5)
        self.assertTrue(context.call_args_list)
        self.assertTrue(all((call.args[1] if len(call.args) > 1 else call.kwargs["limit"]) == 6000
                            for call in context.call_args_list))
        self.assertLessEqual(result["prompt_budget"]["input_tokens_reserved"] +
                             result["prompt_budget"]["output_tokens_reserved"], 16384)

    def test_budget_shrink_after_dropping_preparation_reports_only_final_prompt_cards(self):
        service, _, model = self.make_service()
        original_count = service.prompt_budget.count

        def count(messages):
            text = "\n".join(message["content"] for message in messages)
            return 16384 if len(re.findall(r"\[E\d+\] SOURCE=", text)) > 3 else original_count(messages)

        with patch.object(service.prompt_budget, "count", side_effect=count):
            result = self.chat(service)
        self.assertEqual(len(model.calls), 2)
        self.assertFalse(result["preparation"]["used"])
        ids = re.findall(r"\[(E\d+)\] SOURCE=", self.text(model.calls[1]))
        self.assertGreater(len(ids), 0)
        self.assertLess(len(ids), 5)
        self.assertEqual(result["retrieval"]["selected_count"], len(ids))
        self.assertEqual([card["citation_id"] for card in result["evidence_cards"]], ids)
        self.assertLessEqual(result["prompt_budget"]["input_tokens_reserved"] +
                             result["prompt_budget"]["output_tokens_reserved"], 16384)

    def test_no_excerpt_fits_budget_uses_only_a_second_general_call(self):
        service, _, model = self.make_service([generated(PRELIMINARY), generated("A general explanation without citations.")])
        original_count = service.prompt_budget.count

        def count(messages):
            text = "\n".join(message["content"] for message in messages)
            return 16384 if "EXCERPT_ONLY_MARKER" in text else original_count(messages)

        with patch.object(service.prompt_budget, "count", side_effect=count):
            result = self.chat(service)
        self.assertEqual(len(model.calls), 2)
        self.assertEqual(result["answer_mode"], "general_knowledge")
        self.assertEqual(result["retrieval"]["selected_count"], 0)
        self.assertEqual(result["evidence_cards"], [])
        self.assertNotIn("EXCERPT_ONLY_MARKER", self.text(model.calls[1]))
        self.assertNotIn(PRELIMINARY, self.text(model.calls[1]))
        self.assertFalse(result["preparation"]["used"])

    def test_preparation_own_input_and_output_budget_is_checked_before_any_generation(self):
        service, _, model = self.make_service()
        with patch.object(service.prompt_budget, "count", return_value=16384):
            with self.assertRaises(ValueError):
                self.chat(service)
        self.assertEqual(model.calls, [])

    def test_transport_failures_at_either_stage_do_not_trigger_extra_calls_and_release_capacity(self):
        for responses, calls in (([ModelUnavailableError("fixture transport failure")], 1),
                                 ([generated(PRELIMINARY), ModelUnavailableError("fixture transport failure")], 2)):
            with self.subTest(calls=calls):
                service, _, model = self.make_service(responses)
                with self.assertRaises(ModelUnavailableError):
                    self.chat(service)
                self.assertEqual(len(model.calls), calls)
                self.assertTrue(service.capacity.acquire(blocking=False))
                service.capacity.release()

    def test_preparation_cap_never_exceeds_the_configured_output_limit(self):
        service, _, model = self.make_service(max_tokens=128)
        self.chat(service)
        self.assertEqual([call["effective_max_tokens"] for call in model.calls], [128, 128])

    def test_default_strategy_and_explicit_strict_fallback_preserve_single_grounded_generation(self):
        for strategy, allow_general in (("excerpt_only", True), ("knowledge_evidence_synthesis", False)):
            with self.subTest(strategy=strategy, allow_general=allow_general):
                service, _, model = self.make_service([generated(FINAL)], strategy=strategy, allow_general=allow_general)
                result = self.chat(service)
                self.assertEqual(len(model.calls), 1)
                self.assertEqual(result["answer_mode"], "retrieval_grounded")
                self.assertEqual(result["evidence_support"], "retrieved_excerpts")
                self.assertTrue(result["evidence_supported"])
        self.assertEqual(RagSettings.__dataclass_fields__["answer_strategy"].default, "excerpt_only")


if __name__ == "__main__":
    unittest.main()
