"""Deterministic RAG metrics used beside the LLM judge."""

from __future__ import annotations

import re

from app.utils.citations import valid_citations

NUMBER_RE = re.compile(r"\d+(?:[:.]\d+)?")


def squash(text: str) -> str:
    collapsed = text.lower().replace("\u00a0", " ")
    collapsed = re.sub(r"(?<=\d)[ ](?=\d)", "", collapsed)
    collapsed = collapsed.replace(",", ".")
    return collapsed


def number_tokens(text: str) -> set[str]:
    return set(NUMBER_RE.findall(squash(text)))


def facts_present(answer: str, required: list[str]) -> bool:
    if not required:
        return True
    numbers = number_tokens(answer)
    blob = squash(answer)
    for item in required:
        if NUMBER_RE.fullmatch(item):
            if item not in numbers:
                return False
        elif item.lower() not in blob:
            return False
    return True


def context_precision(ranked_topics: list[str], expected_topics: list[str]) -> float | None:
    """RAGAS-style context precision. None when the question has no relevant topic."""
    expected = set(expected_topics)
    if not expected:
        return None
    relevances = [1 if topic in expected else 0 for topic in ranked_topics]
    relevant_total = sum(relevances)
    if relevant_total == 0:
        return 0.0
    score = 0.0
    seen = 0
    for index, relevant in enumerate(relevances, start=1):
        if relevant:
            seen += 1
            score += seen / index
    return score / relevant_total


def has_valid_citation(answer: str, sources: list[dict]) -> bool:
    return bool(valid_citations(answer, sources))
