"""Small literal bilingual aliases shared by local retrieval and excerpt checks.

This is lexical matching, not translation, entailment, or evidence grading.
Unknown terms remain exact terms; negation and population terms are not removed.
"""
from __future__ import annotations

import re

from .corpus_retrieval_service import TERMS


_CJK = re.compile(r"[\u3400-\u9fff]")
_ALIASES: dict[str, set[str]] = {}


def _add_group(*values: str) -> None:
    normalized = {value.casefold().strip() for value in values if value.strip()}
    for value in normalized:
        _ALIASES.setdefault(value, set()).update(normalized)


# Whole concepts are reversible. Do not treat any word in a multiword phrase
# as a synonym for the whole phrase (e.g. "cancer" is not "lung cancer").
for _chinese, _english in TERMS.items():
    _add_group(_chinese, _english)

for _group in (
    ("kidney", "renal", "肾"),
    ("injury", "损伤"),
    ("blood", "血"),
    ("pressure", "血压"),
    ("tubular", "小管"),
    ("function", "功能"),
    ("heavy", "重金属"),
    ("mixture", "混合", "复合"),
    ("lung", "肺"),
    ("randomized", "随机"),
    ("trial", "试验"),
    ("systematic", "系统"),
    ("review", "综述"),
    ("meta", "荟萃"),
    ("analysis", "分析"),
    ("children", "child", "pediatric", "儿童"),
    ("adult", "adults", "成人", "成年人"),
    ("human", "humans", "人体", "人群"),
    ("worker", "workers", "工人"),
    ("cognition", "cognitive", "认知"),
):
    _add_group(*_group)


def term_aliases(term: str) -> list[str]:
    """Return the literal term first, followed by fixed reviewed aliases."""
    normalized = str(term).casefold().strip()
    if not normalized:
        return []
    return [normalized, *sorted(_ALIASES.get(normalized, set()) - {normalized})]


def term_present(text: str, term: str) -> bool:
    """Chinese literals use substring matching; Latin literals keep boundaries."""
    folded = str(text).casefold()
    for alias in term_aliases(term):
        if _CJK.search(alias):
            if alias in folded:
                return True
        elif re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", folded):
            return True
    return False
