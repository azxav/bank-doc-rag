"""Process-wide store, models, and graph. Built lazily so tests can substitute them."""

from __future__ import annotations

from qdrant_client import QdrantClient

from app.core.config import settings
from app.core.langgraph.graph import RAGGraph
from app.services.ingest import ingest_samples
from app.services.llm import HashEmbeddings, OpenRouterChat, OpenRouterEmbeddings
from app.services.store import VectorStore

_store: VectorStore | None = None
_graph: RAGGraph | None = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        if settings.OFFLINE_DEMO:
            _store = VectorStore(client=QdrantClient(":memory:"), collection="offline_demo")
        else:
            _store = VectorStore()
    return _store


def build_offline_graph(top_k: int | None = None) -> RAGGraph:
    """In-memory hybrid index and extractive citations. Does not call OpenRouter."""
    store = VectorStore(client=QdrantClient(":memory:"), collection="offline_demo")
    embedder = HashEmbeddings()
    ingest_samples(store=store, embedder=embedder)
    return RAGGraph(
        store=store, embedder=embedder, chat=None, top_k=top_k or settings.RETRIEVAL_TOP_K
    )


def get_graph() -> RAGGraph:
    global _graph
    if _graph is None:
        if settings.OFFLINE_DEMO:
            embedder = HashEmbeddings()
            ingest_samples(store=get_store(), embedder=embedder)
            _graph = RAGGraph(
                store=get_store(),
                embedder=embedder,
                chat=None,
                top_k=settings.RETRIEVAL_TOP_K,
            )
        else:
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
