"""Retrieve, grade, and answer with mandatory citations."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.core.logging import logger
from app.core.prompts import ANSWER_SYSTEM, FILTER_SYSTEM
from app.services.sparse import lexical_fallback
from app.services.store import Hit, VectorStore
from app.utils.citations import append_missing_citations, format_citation
from app.utils.json_extract import parse_json_object
from app.utils.language import refusal_for


class RAGState(TypedDict, total=False):
    question: str
    top_k: int
    retrieved: list[dict]
    filtered: list[dict]
    answer: str
    sources: list[dict]
    abstained: bool
    citations_appended: bool
    search_mode: str


class RAGGraph:
    def __init__(self, store: VectorStore, embedder: Any, chat: Any, top_k: int = 8) -> None:
        self.store = store
        self.embedder = embedder
        self.chat = chat
        self.top_k = top_k
        self.graph = self._compile()

    def _compile(self):
        builder = StateGraph(RAGState)
        builder.add_node("retrieve", self._retrieve)
        builder.add_node("filter", self._filter)
        builder.add_node("answer", self._answer)
        builder.set_entry_point("retrieve")
        builder.add_edge("retrieve", "filter")
        builder.add_edge("filter", "answer")
        builder.add_edge("answer", END)
        return builder.compile()

    def invoke(self, question: str, top_k: int | None = None) -> RAGState:
        state: RAGState = {"question": question, "top_k": top_k or self.top_k}
        return self.graph.invoke(state)

    def _retrieve(self, state: RAGState) -> RAGState:
        question = state["question"]
        limit = int(state.get("top_k") or self.top_k)
        vector = self.embedder.embed_query(question)
        hits = self.store.search(question, vector, limit)
        logger.info("retrieved", count=len(hits), mode=self.store.last_search_mode)
        return {
            "retrieved": [hit.as_source() | {"text": hit.text} for hit in hits],
            "search_mode": self.store.last_search_mode,
        }

    def _filter(self, state: RAGState) -> RAGState:
        retrieved = state.get("retrieved") or []
        if not retrieved:
            return {"filtered": []}
        if self.chat is None:
            filtered = lexical_fallback(state["question"], retrieved)
            logger.info("filtered_offline", kept=len(filtered), retrieved=len(retrieved))
            return {"filtered": filtered}
        lines = [_chunk_line(item) for item in retrieved[:4]]
        user = f"Question: {state['question']}\n\nChunks:\n" + "\n".join(lines)
        wanted: set[str] = set()
        graded = False
        for attempt in range(2):
            try:
                raw = self.chat.complete(
                    FILTER_SYSTEM,
                    user,
                    max_tokens=160,
                    json_mode=True,
                    operation="filter",
                )
                parsed = parse_json_object(raw)
                wanted = {str(item) for item in parsed.get("relevant", [])}
                graded = True
                break
            except Exception:
                logger.warning("filter_parse_failed", attempt=attempt + 1)
                wanted = set()
        filtered = []
        for item in retrieved:
            key = f"{item['doc_id']}#{item['chunk_id']}"
            if key in wanted:
                filtered.append(item)
        if not filtered:
            filtered = lexical_fallback(state["question"], retrieved)
            if filtered:
                logger.info("lexical_fallback_kept", kept=len(filtered), graded=graded)
        logger.info("filtered", kept=len(filtered), retrieved=len(retrieved))
        return {"filtered": filtered}

    def _answer(self, state: RAGState) -> RAGState:
        filtered = state.get("filtered") or []
        sources = [_public_source(item) for item in filtered]
        if not filtered:
            return {
                "answer": refusal_for(state["question"]),
                "sources": [],
                "abstained": True,
                "citations_appended": False,
            }
        if self.chat is None:
            return {
                "answer": _extractive_answer(filtered[:2]),
                "sources": sources[:2],
                "abstained": False,
                "citations_appended": False,
            }
        lines = [_chunk_line(item) for item in filtered[:4]]
        user = f"Question: {state['question']}\n\nChunks:\n" + "\n".join(lines)
        answer = self.chat.complete(
            ANSWER_SYSTEM,
            user,
            max_tokens=220,
            operation="answer",
        )
        answer, appended = append_missing_citations(answer, sources)
        return {
            "answer": answer,
            "sources": sources,
            "abstained": False,
            "citations_appended": appended,
        }


def _extractive_answer(chunks: list[dict]) -> str:
    """Quote retrieved text and attach citations. No chat model."""
    lines = []
    for item in chunks:
        text = " ".join(item["text"].split())
        citation = format_citation(item["doc_id"], int(item["page"]), int(item["chunk_id"]))
        lines.append(f"{text} {citation}")
    return "\n".join(lines)


def _chunk_line(item: dict) -> str:
    text = item["text"]
    if len(text) > 450:
        text = text[:447] + "..."
    return f"[{item['doc_id']} p.{item['page']} c{item['chunk_id']}] {text}"


def _public_source(item: dict) -> dict:
    hit = Hit(
        doc_id=item["doc_id"],
        topic=item.get("topic", ""),
        title=item.get("title", ""),
        language=item.get("language", ""),
        page=int(item["page"]),
        chunk_id=int(item["chunk_id"]),
        text=item.get("text") or item.get("excerpt") or "",
        score=float(item.get("score") or 0.0),
    )
    return hit.as_source()
