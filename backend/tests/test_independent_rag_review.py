"""Narrow offline review regressions; no scientific or clinical validation claim."""
import unittest

from app.services.rag_agent_service import (
    InvalidGenerationError, evidence_context, validate_citations,
)


class IndependentReviewRegressions(unittest.TestCase):
    def test_identifier_prefix_is_not_authorized_by_longer_source_identifier(self):
        for excerpt, answer in [
            ("PMID 12345", "PMID 123 [E1]"),
            ("DOI 10.1000/abc", "DOI 10.1000/ab [E1]"),
            ("GBZ 2.1-2019", "GBZ 2 [E1]"),
        ]:
            cards = [{"citation_id": "E1", "chunk_id": "fixture", "title": "Fixture",
                      "context_excerpt": excerpt}]
            with self.subTest(excerpt=excerpt), self.assertRaises(InvalidGenerationError):
                validate_citations(answer, cards)

    def test_exact_pmid_is_not_rejected_only_for_colon_or_spacing(self):
        cards = [{"citation_id": "E1", "chunk_id": "fixture", "title": "Fixture",
                  "context_excerpt": "PMID:12345"}]
        result = validate_citations("PMID 12345 [E1]", cards)
        self.assertEqual(result[0]["chunk_id"], "fixture")

    def test_balanced_doi_parentheses_and_standard_spacing_are_exact(self):
        cards = [{"citation_id": "E1", "chunk_id": "fixture", "title": "Fixture",
                  "context_excerpt": "DOI 10.1000/abc(def); GBZ/T 123-2020."}]
        self.assertEqual(validate_citations("10.1000/abc(def) and GBZ / T 123-2020 [E1]", cards)[0]["id"], "E1")

    def test_budget_includes_separators_between_excerpts(self):
        hits = [{"chunk_id": str(index), "title": "Fixture", "source": "pubmed",
                 "content": "lead kidney fixture excerpt. " * 200} for index in range(4)]
        for limit in (600, 1000, 2200):
            with self.subTest(limit=limit):
                context, _ = evidence_context(hits, limit, ["lead", "kidney"])
                self.assertLessEqual(len(context), limit)

    def test_short_first_chunk_does_not_discard_later_valid_excerpt(self):
        short = {"chunk_id": "short", "title": "lead kidney", "source": "pubmed",
                 "content": "lead kidney"}
        long = {"chunk_id": "long", "title": "lead kidney", "source": "pubmed",
                "content": "lead kidney fixture excerpt. " * 30}
        _, cards = evidence_context([short, long], 2000, ["lead", "kidney"])
        self.assertEqual([card["chunk_id"] for card in cards], ["long"])

    def test_returned_excerpt_is_exact_source_slice_at_reported_offset(self):
        content = "fixture introduction " * 180 + "lead kidney fixture. " * 40
        hit = {"chunk_id": "original", "title": "Fixture", "source": "pubmed",
               "content": content}
        context, cards = evidence_context([hit], 1800, ["lead", "kidney"])
        self.assertEqual(len(cards), 1)
        card = cards[0]
        start = card["context_offset"]
        self.assertEqual(card["context_excerpt"], content[start:start + len(card["context_excerpt"])])
        self.assertIn(card["context_excerpt"], context)
        self.assertLessEqual(len(context), 1800)


if __name__ == "__main__":
    unittest.main()
