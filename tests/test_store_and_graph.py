import json
import re

from qdrant_client import QdrantClient

from app.core.langgraph.graph import RAGGraph
from app.services.chunking import Chunk
from app.services.ingest import ingest_samples
from app.services.llm import HashEmbeddings
from app.services.store import VectorStore


def _store() -> VectorStore:
    return VectorStore(client=QdrantClient(":memory:"), collection="unit")


def test_hybrid_ingest_retrieves_loan_chunk() -> None:
    store = _store()
    count = ingest_samples(store=store, embedder=HashEmbeddings())
    assert count == 45
    vector = HashEmbeddings().embed_query("maximum consumer cash loan 150000000 salaried rate")
    hits = store.search("maximum consumer cash loan 150000000", vector, limit=5)
    assert store.last_search_mode == "hybrid"
    assert hits
    assert any(hit.topic == "retail-loan" for hit in hits)


def test_keyword_fallback_still_returns_hits() -> None:
    store = _store()
    ingest_samples(store=store, embedder=HashEmbeddings())
    original = store.client.query_points

    def flaky(*args, **kwargs):
        if "prefetch" in kwargs:
            raise RuntimeError("sparse fusion unavailable")
        return original(*args, **kwargs)

    store.client.query_points = flaky
    vector = HashEmbeddings().embed_query("Maple Savings 18%")
    hits = store.search("Maple Savings annual rate", vector, limit=4)
    assert store.last_search_mode == "dense_keyword_fallback"
    assert hits


class ScriptedChat:
    def __init__(self) -> None:
        self.operations: list[str] = []

    def complete(self, system: str, user: str, **kwargs) -> str:
        operation = kwargs.get("operation", "chat")
        self.operations.append(operation)
        if operation == "filter":
            if "leasing" in user.lower():
                return json.dumps({"relevant": []})
            relevant = []
            for line in user.splitlines():
                if "24.9" not in line:
                    continue
                match = re.search(r"\[([a-z0-9\-]+) p\.(\d+) c(\d+)\]", line)
                if match:
                    relevant.append(f"{match.group(1)}#{match.group(3)}")
            return json.dumps({"relevant": relevant[:1]})
        if kwargs.get("omit_citation"):
            return "The salaried rate is 24.9%."
        return "The salaried nominal rate is 24.9% [retail-loan-en p.1 c1]."


def _loan_chunk() -> Chunk:
    return Chunk(
        doc_id="retail-loan-en",
        topic="retail-loan",
        title="Synthetic retail loan terms",
        language="en",
        page=1,
        chunk_id=1,
        text="The nominal annual interest rate is 24.9% for salaried clients.",
    )


def _index_one() -> VectorStore:
    store = _store()
    embedder = HashEmbeddings()
    chunk = _loan_chunk()
    store.recreate(embedder.dim)
    store.upsert([chunk], embedder.embed_documents([chunk.embed_text()]))
    return store


def test_graph_answers_with_citation() -> None:
    store = _index_one()
    chat = ScriptedChat()
    graph = RAGGraph(store, HashEmbeddings(), chat, top_k=3)
    result = graph.invoke("What is the salaried rate?")
    assert result["abstained"] is False
    assert "24.9" in result["answer"]
    assert "[retail-loan-en p.1 c1]" in result["answer"]
    assert result["sources"][0]["doc_id"] == "retail-loan-en"
    assert result["citations_appended"] is False


def test_graph_refuses_when_filter_rejects() -> None:
    store = _index_one()
    chat = ScriptedChat()
    graph = RAGGraph(store, HashEmbeddings(), chat, top_k=3)
    result = graph.invoke("What annual rate does the sample charge for car leasing?")
    assert result["abstained"] is True
    assert result["sources"] == []
    assert "does not contain" in result["answer"].lower()
    assert chat.operations == ["filter"]


def test_graph_appends_citation_when_model_omits_it() -> None:
    store = _index_one()

    class OmitCitation(ScriptedChat):
        def complete(self, system: str, user: str, **kwargs) -> str:
            if kwargs.get("operation") == "answer":
                kwargs = {**kwargs, "omit_citation": True}
            return super().complete(system, user, **kwargs)

    graph = RAGGraph(store, HashEmbeddings(), OmitCitation(), top_k=3)
    result = graph.invoke("What is the salaried rate?")
    assert result["citations_appended"] is True
    assert "[retail-loan-en p.1 c1]" in result["answer"]
