"""Combined BM25 -> top-k -> prompt regressions; fixtures only, no model/network.

Generated fixture answers test plumbing and mechanical citations, not medical
truth, semantic entailment, or a real model's compliance with the prompt.
"""
import asyncio
import copy
import re
import unittest
from unittest.mock import patch

from app.rag_config import RagSettings
from app.services.local_evidence_service import query_terms
from app.services.rag_agent_service import (
    InvalidGenerationError, RagAgentService, evidence_context, select_evidence,
    normalize_evidence_citations, validate_citations, validate_general_answer,
)
from app.services.retrieval_text import term_present
from test_rag_agent_service import FixtureModel


def candidate(identifier, *, content=None, title="Synthetic fixture", source="pubmed"):
    return {"chunk_id": identifier, "source": source, "title": title,
            "content": content or (f"Synthetic paragraph {identifier}: cadmium exposure and renal injury. " * 8),
            "score": -1.0, "score_type": "fts5_bm25_lower_is_better", "doi": None, "pmid": None,
            "retrieval_channels": ["bm25"]}


class CombinedFixtureRetriever:
    mode = "bm25"
    medcpt_rerank = False

    def __init__(self, candidates):
        self.candidates = candidates
        self.calls = []
        self.backend = "combined_bm25"
        self.result_mode = "bm25"

    def search(self, query, **kwargs):
        self.calls.append({"query": query, **kwargs})
        terms, _ = query_terms(query)
        pool = copy.deepcopy(self.candidates[:min(kwargs["candidate_k"], 32)])
        for hit in pool:
            matched = [term for term in terms if term_present(hit["title"] + " " + hit["content"], term)]
            hit["matched_query_terms"] = matched
            hit["query_term_coverage"] = len(matched) / len(terms) if terms else 0
        return {"hits": pool[:min(kwargs["top_k"], 12)], "sparse_hits": pool, "dense_hits": [],
                "mode": self.result_mode, "degraded": False,
                "diagnostics": {"backend": self.backend, "query_terms": terms,
                                "untranslated_segments": [], "candidates_retrieved": len(pool),
                                "independent_dense_recall": False, "warnings": []}}


class CombinedBm25PromptTests(unittest.TestCase):
    def make_service(self, hits, *, top_k=2, candidate_k=32, context_chars=3500, context_window=32768):
        retriever = CombinedFixtureRetriever(hits)
        model = FixtureModel()
        model.answer = "Synthetic response referring to the supplied excerpt [E1]."
        settings = RagSettings(model="fixture-no-model", base_url="http://unused", model_api_key="",
                               timeout=5, max_tokens=128, context_chars=context_chars,
                               top_k=top_k, candidate_k=candidate_k, concurrency=1,
                               context_window=context_window)
        service = RagAgentService(retriever, lambda: model, settings, allow_general_fallback=False)
        service.prompt_budget.checked = True  # Never inspect/load tokenizer assets.
        return service, retriever, model

    def chat(self, service, message="cadmium kidney", **kwargs):
        return asyncio.run(service.chat(message, **kwargs))

    def test_normal_chinese_question_uses_ranked_hits_despite_leftover_function_words(self):
        question = "职业镉暴露对肾脏有什么危害？"
        hit = candidate("synthetic/normal", title="Occupational cadmium exposure and renal tubular injury",
                        content="Occupational cadmium exposure and renal tubular injury are discussed in this synthetic fixture. " * 5)
        terms, _ = query_terms(question)
        hit["query_term_coverage"] = 4 / 6
        self.assertEqual(select_evidence([hit], 2, terms), [])  # Reproduces the previous gate.
        service, _, model = self.make_service([hit])
        result = self.chat(service, question)
        self.assertEqual(result["retrieval"]["selected_count"], 1)
        self.assertEqual(result["retrieval"]["diagnostics"]["query_terms"], terms)
        self.assertEqual(result["retrieval"]["diagnostics"]["selection_policy"], "bm25_rank_then_content_dedup_top_k")
        self.assertIn(question, model.calls[0][1]["content"])
        self.assertIn("renal tubular injury", model.calls[0][1]["content"])
        self.assertEqual(result["dense_hits"], [])

    def test_distant_query_terms_do_not_delete_an_otherwise_usable_excerpt(self):
        hit = candidate("synthetic/long", content="Cadmium exposure. " + "Background context. " * 130 + " Kidney injury was examined.")
        terms = ["cadmium", "exposure", "kidney", "injury"]
        self.assertEqual(evidence_context([hit], 3500, terms)[1], [])  # Previous all-window gate.
        service, _, model = self.make_service([hit])
        result = self.chat(service, "cadmium exposure kidney injury")
        self.assertEqual(result["retrieval"]["selected_count"], 1)
        card = result["evidence_cards"][0]
        self.assertTrue(card["excerpt_truncated"])
        offset = card["context_offset"]
        self.assertEqual(card["context_excerpt"], hit["content"][offset:offset + len(card["context_excerpt"])] )
        self.assertIn(card["context_excerpt"], model.calls[0][1]["content"])

    def test_full_candidate_pool_fills_top_k_after_duplicate_first_twelve(self):
        first = candidate("synthetic/first")
        duplicates = [{**copy.deepcopy(first), "chunk_id": f"synthetic/duplicate/{index}"} for index in range(12)]
        later = candidate("synthetic/later", content="Another distinct synthetic discussion of cadmium and kidney injury. " * 8)
        pool = duplicates + [later]
        service, _, _ = self.make_service(pool)
        result = self.chat(service)
        self.assertEqual([row["chunk_id"] for row in result["evidence_cards"]], ["synthetic/duplicate/0", "synthetic/later"])
        self.assertEqual(result["retrieval"]["configured_top_k"], 2)
        self.assertEqual(result["retrieval"]["candidate_count"], 13)
        self.assertEqual(result["retrieval"]["selection_candidate_count"], 13)
        self.assertEqual(result["retrieval"]["selected_before_context_count"], 2)
        self.assertEqual(result["retrieval"]["selected_count"], 2)

    def test_existing_rank_order_and_raw_scores_survive_selection(self):
        first, second = candidate("synthetic/first"), candidate("synthetic/second")
        first["score"], second["score"] = -.000001, -999999
        service, _, _ = self.make_service([first, second])
        result = self.chat(service)
        self.assertEqual([row["chunk_id"] for row in result["evidence_cards"]], [first["chunk_id"], second["chunk_id"]])
        self.assertEqual([row["score"] for row in result["evidence_cards"]], [first["score"], second["score"]])

    def test_empty_contents_and_duplicate_contents_are_still_removed(self):
        empty = {**candidate("synthetic/empty"), "content": "   "}
        first = candidate("synthetic/first")
        duplicate = {**first, "chunk_id": "synthetic/duplicate", "content": "\n" + first["content"] + "  "}
        last = candidate("synthetic/last")
        service, _, _ = self.make_service([empty, first, duplicate, last])
        result = self.chat(service)
        self.assertEqual([row["chunk_id"] for row in result["evidence_cards"]], [first["chunk_id"], last["chunk_id"]])

    def test_original_unknown_negation_and_population_constraints_reach_prompt(self):
        question = "职业镉暴露是否不会影响儿童的未知新病？"
        service, _, model = self.make_service([candidate("synthetic/incomplete")])
        model.answer = "INSUFFICIENT_EVIDENCE: the supplied excerpt does not establish the requested conditions."
        result = self.chat(service, question)
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertFalse(result["evidence_supported"])
        self.assertIn(question, model.calls[0][1]["content"])
        self.assertEqual(result["retrieval"]["diagnostics"]["query_terms"], query_terms(question)[0])
        self.assertIn("negation", model.calls[0][0]["content"])
        self.assertIn("population constraint", model.calls[0][0]["content"])

    def test_prompt_warns_about_templates_without_altering_retrieved_material(self):
        text = "SYNTHETIC TEMPLATE: A study result placeholder about cadmium and kidney injury. " * 8
        original = candidate("synthetic/template", content=text, source="scientific")
        original.update(source_url="https://example.org/fixture", standard_no_or_doi="", page=4,
                        source_metadata={"document_type": "template", "source_verified": False})
        service, retriever, model = self.make_service([original])
        result = self.chat(service)
        self.assertEqual(retriever.candidates[0], original)
        system = model.calls[0][0]["content"]
        self.assertIn("Templates, examples, placeholders", system)
        self.assertIn("not verified", system)
        self.assertIn("unverified template assertions", system)
        card = result["evidence_cards"][0]
        self.assertEqual(card["source_metadata"], original["source_metadata"])
        self.assertEqual(card["url"], original["source_url"])
        self.assertEqual(card["page"], 4)
        self.assertEqual(card["evidence_priority"], "UNASSESSED")
        self.assertIsNone(card["doi"])

    def test_counts_match_final_prompt_after_context_budget_shrink(self):
        long_hits = [candidate("synthetic/one", content="First synthetic cadmium kidney paragraph. " * 200),
                     candidate("synthetic/two", content="Second synthetic cadmium kidney paragraph. " * 200)]
        service, _, model = self.make_service(long_hits,
                                             context_chars=4000, context_window=4096)
        with patch("app.services.rag_agent_service.evidence_context", wraps=evidence_context) as excerpts:
            result = self.chat(service)
        self.assertGreaterEqual(excerpts.call_count, 2)
        self.assertLess(excerpts.call_args.args[1], excerpts.call_args_list[0].args[1])
        self.assertTrue(all(call.kwargs["require_lexical_match"] is False for call in excerpts.call_args_list))
        ids = re.findall(r"\[(E\d+)\] SOURCE=", model.calls[0][1]["content"])
        self.assertEqual(result["retrieval"]["selected_count"], len(ids))
        self.assertEqual([row["citation_id"] for row in result["evidence_cards"]], ids)
        self.assertLessEqual(result["prompt_budget"]["input_tokens_reserved"] +
                             result["prompt_budget"]["output_tokens_reserved"], 4096)
        self.assertEqual(result["retrieval"]["configured_top_k"], 2)

    def test_no_hits_still_do_not_generate_in_strict_fallback_mode(self):
        service, _, model = self.make_service([])
        result = self.chat(service)
        self.assertEqual(result["retrieval"]["selected_count"], 0)
        self.assertEqual(result["retrieval"]["configured_top_k"], 2)
        self.assertFalse(result["model"]["invoked"])
        self.assertEqual(model.calls, [])

    def test_legacy_path_keeps_existing_lexical_guardrails(self):
        service, retriever, model = self.make_service([candidate("synthetic/partial", content="Occupational kidney injury " * 20)])
        retriever.backend = "medrr"
        result = self.chat(service, "novelcompound kidney occupational exposure")
        self.assertEqual(result["retrieval"]["selected_count"], 0)
        self.assertEqual(model.calls, [])

    def test_unknown_citations_and_invented_identifiers_still_fail(self):
        for answer in ("Synthetic [E99].", "Synthetic DOI 10.1234/madeup [E1].", "No citation."):
            with self.subTest(answer=answer):
                service, _, model = self.make_service([candidate("synthetic/citation")])
                model.answer = answer
                with self.assertRaises(InvalidGenerationError):
                    self.chat(service)

    def test_combined_and_range_citations_are_normalized_in_returned_answer(self):
        hits = [candidate(f"synthetic/group/{index}") for index in range(5)]
        for answer, expected, expected_ids in (
            ("Synthetic list [E1, E4, E5].", "Synthetic list [E1] [E4] [E5].", ["E1", "E4", "E5"]),
            ("Synthetic range [E1–E5].", "Synthetic range [E1] [E2] [E3] [E4] [E5].", ["E1", "E2", "E3", "E4", "E5"]),
        ):
            with self.subTest(answer=answer):
                service, _, model = self.make_service(hits, top_k=5, context_chars=8000)
                model.answer = answer
                result = self.chat(service)
                self.assertEqual(result["answer"], expected)
                self.assertIn(expected, result["message"])
                self.assertEqual([row["id"] for row in result["citations"]], expected_ids)
                self.assertEqual([row["citation_id"] for row in result["evidence_cards"] if row["is_cited"]], expected_ids)

    def test_unknown_group_member_is_rejected_even_with_other_valid_single_citation(self):
        service, _, model = self.make_service([candidate("synthetic/group-unknown")])
        model.answer = "Synthetic [E1]. Another statement [E1, E99]."
        with self.assertRaises(InvalidGenerationError):
            self.chat(service)


class EvidenceCitationGroupTests(unittest.TestCase):
    def cards(self):
        return [{"citation_id": f"E{index}", "chunk_id": f"synthetic/{index}", "source": "pubmed",
                 "title": "Synthetic", "context_excerpt": "Synthetic fixture with no publication identifier."}
                for index in range(1, 6)]

    def test_single_citations_and_ordinary_bracketed_prose_are_unchanged(self):
        answer = "[Example] Synthetic [E1]. [Evidence quality] [Vitamin E] [Vitamins E, C] [E-value] Additional [E4]."
        self.assertEqual(normalize_evidence_citations(answer), answer)
        self.assertEqual([row["id"] for row in validate_citations(answer, self.cards())], ["E1", "E4"])

    def test_mixed_short_groups_are_bounded_and_preserve_first_reference_order(self):
        answer = "Synthetic [E4, E1-E3, E1]."
        normalized = "Synthetic [E4] [E1] [E2] [E3]."
        self.assertEqual(normalize_evidence_citations(answer), normalized)
        self.assertEqual(normalize_evidence_citations(normalized), normalized)
        self.assertEqual([row["id"] for row in validate_citations(answer, self.cards())], ["E4", "E1", "E2", "E3"])

    def test_malformed_reversed_and_excessive_groups_are_never_ignored(self):
        invalid = ["[E5–E1]", "[E1–E100000]", "[E1, X2]", "[E1; E2]", "[E1,]",
                   "[E0]", "[E01]", "[E1, E]", "[E?]", "[E 1]", "[e1, e2]",
                   "[E１, E２]",
                   "[E1, [E2]]", "[E1, E2", "[E1,\nE2]", "[E1 " + "prose " * 50 + "]"]
        for group in invalid:
            with self.subTest(group=group), self.assertRaises(InvalidGenerationError):
                validate_citations("Valid single [E1]. Malformed " + group, self.cards())

    def test_unknown_list_and_range_ids_are_checked_after_expansion(self):
        for group in ("[E1, E99]", "[E1–E6]"):
            with self.subTest(group=group), self.assertRaises(InvalidGenerationError):
                validate_citations("Synthetic " + group, self.cards())

    def test_general_answers_cannot_bypass_source_prohibition_with_group_citations(self):
        for group in ("[E1, E4, E5]", "[E1–E5]", "[E1, E999]", "[E1, X2]"):
            with self.subTest(group=group), self.assertRaises(InvalidGenerationError):
                validate_general_answer("Synthetic general explanation " + group)


if __name__ == "__main__":
    unittest.main()
