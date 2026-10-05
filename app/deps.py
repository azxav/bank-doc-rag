"""Process-wide store, models, and graph. Built lazily so tests can substitute them."""

from __future__ import annotations

from app.core.config import settings
from app.core.langgraph.graph import RAGGraph
from app.services.llm import OpenRouterChat, OpenRouterEmbeddings
from app.services.store import VectorStore

_store: VectorStore | None = None
_graph: RAGGraph | None = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


def get_graph() -> RAGGraph:
    global _graph
    if _graph is None:
        _graph = RAGGraph(
            store=get_store(),
            embedder=OpenRouterEmbeddings(),
            chat=OpenRouterChat(),
            top_k=settings.RETRIEVAL_TOP_K,
        )
    return _graph


def reset_dependencies() -> None:
    global _store, _graph
    _store = None
    _graph = None
