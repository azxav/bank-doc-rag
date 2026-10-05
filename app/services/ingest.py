"""Load synthetic samples and index them in Qdrant."""

from __future__ import annotations

from pathlib import Path

from app.core.config import ROOT, settings
from app.core.logging import logger
from app.services.chunking import load_sample_chunks
from app.services.llm import HashEmbeddings, OpenRouterEmbeddings
from app.services.store import VectorStore

SAMPLES = ROOT / "data" / "samples"


def ingest_samples(
    store: VectorStore | None = None,
    embedder: OpenRouterEmbeddings | HashEmbeddings | None = None,
    sample_dir: Path | None = None,
) -> int:
    chunks = load_sample_chunks(sample_dir or SAMPLES)
    embedder = embedder or OpenRouterEmbeddings()
    vectors = embedder.embed_documents([chunk.embed_text() for chunk in chunks])
    if not vectors:
        raise RuntimeError("No embeddings produced")
    store = store or VectorStore()
    store.recreate(len(vectors[0]))
    store.upsert(chunks, vectors)
    logger.info(
        "ingest_complete",
        chunks=len(chunks),
        collection=store.collection,
        embedding_model=settings.EMBEDDING_MODEL,
    )
    return len(chunks)
