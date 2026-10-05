"""Parse and validate mandatory [doc_id p.N cM] citations."""

from __future__ import annotations

import re

CITATION_RE = re.compile(r"\[([A-Za-z0-9\-]+)\s+p\.(\d+)\s+c(\d+)\]")


def parse_citations(answer: str) -> list[tuple[str, int, int]]:
    return [
        (doc_id.lower(), int(page), int(chunk_id))
        for doc_id, page, chunk_id in CITATION_RE.findall(answer)
    ]


def source_keys(sources: list[dict]) -> set[tuple[str, int, int]]:
    return {
        (str(source["doc_id"]).lower(), int(source["page"]), int(source["chunk_id"]))
        for source in sources
    }


def valid_citations(answer: str, sources: list[dict]) -> list[tuple[str, int, int]]:
    allowed = source_keys(sources)
    return [item for item in parse_citations(answer) if item in allowed]


def format_citation(doc_id: str, page: int, chunk_id: int) -> str:
    return f"[{doc_id} p.{page} c{chunk_id}]"


def append_missing_citations(answer: str, sources: list[dict]) -> tuple[str, bool]:
    """Append a sources line when the model stated facts but omitted valid citations."""
    if not sources or valid_citations(answer, sources):
        return answer, False
    line = " ".join(
        format_citation(source["doc_id"], int(source["page"]), int(source["chunk_id"]))
        for source in sources
    )
    return f"{answer.rstrip()}\nSources: {line}", True
