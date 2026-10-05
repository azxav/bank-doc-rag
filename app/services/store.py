"""Qdrant hybrid retrieval with a dense-plus-keyword fallback."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from qdrant_client import QdrantClient, models

from app.core.config import settings
from app.core.logging import logger
from app.services.chunking import Chunk
from app.services.sparse import keyword_overlap, sparse_tf

NAMESPACE = uuid.UUID("6b1e1a0a-5f3a-4d2c-9a1e-0c0a0b0c0d0e")
DENSE = "dense"
SPARSE = "bm25"


@dataclass
class Hit:
    doc_id: str
    topic: str
    title: str
    language: str
    page: int
    chunk_id: int
    text: str
    score: float

    def as_source(self) -> dict:
        excerpt = self.text if len(self.text) <= 240 else self.text[:237] + "..."
        return {
            "doc_id": self.doc_id,
            "topic": self.topic,
            "title": self.title,
            "language": self.language,
            "page": self.page,
            "chunk_id": self.chunk_id,
            "score": round(float(self.score), 4),
            "excerpt": excerpt,
        }


def make_client(
    *,
    location: str | None = None,
    path: str | None = None,
    url: str | None = None,
) -> QdrantClient:
    chosen_location = settings.QDRANT_LOCATION if location is None else location
    chosen_path = settings.QDRANT_PATH if path is None else path
    chosen_url = settings.QDRANT_URL if url is None else url
    if chosen_location == ":memory:":
        return QdrantClient(":memory:")
    if chosen_path:
        return QdrantClient(path=chosen_path)
    return QdrantClient(url=chosen_url, timeout=5)


class VectorStore:
    def __init__(self, client: QdrantClient | None = None, collection: str | None = None) -> None:
        self.client = client or make_client()
        self.collection = collection or settings.QDRANT_COLLECTION
        self.last_search_mode = "uninitialized"

    def ping(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception:
            logger.warning("qdrant_unreachable", collection=self.collection)
            return False

    def recreate(self, dim: int) -> None:
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config={DENSE: models.VectorParams(size=dim, distance=models.Distance.COSINE)},
            sparse_vectors_config={
                SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF),
            },
        )

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunk and vector counts differ")
        points = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            indices, values = sparse_tf(chunk.embed_text())
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid5(NAMESPACE, chunk.key)),
                    vector={
                        DENSE: vector,
                        SPARSE: models.SparseVector(indices=indices, values=values),
                    },
                    payload={
                        "doc_id": chunk.doc_id,
                        "topic": chunk.topic,
                        "title": chunk.title,
                        "language": chunk.language,
                        "page": chunk.page,
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.text,
                    },
                )
            )
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query: str, dense_vector: list[float], limit: int) -> list[Hit]:
        indices, values = sparse_tf(query)
        if indices:
            try:
                result = self.client.query_points(
                    collection_name=self.collection,
                    prefetch=[
                        models.Prefetch(query=dense_vector, using=DENSE, limit=limit * 3),
                        models.Prefetch(
                            query=models.SparseVector(indices=indices, values=values),
                            using=SPARSE,
                            limit=limit * 3,
                        ),
                    ],
                    query=models.FusionQuery(fusion=models.Fusion.RRF),
                    limit=limit,
                )
                self.last_search_mode = "hybrid"
                return [_hit_from_point(point) for point in result.points]
            except Exception:
                logger.warning("hybrid_search_failed_using_keyword_fallback")
        self.last_search_mode = "dense_keyword_fallback"
        return self._dense_keyword(query, dense_vector, limit)

    def _dense_keyword(self, query: str, dense_vector: list[float], limit: int) -> list[Hit]:
        result = self.client.query_points(
            collection_name=self.collection,
            query=dense_vector,
            using=DENSE,
            limit=max(limit * 3, limit),
        )
        hits = [_hit_from_point(point) for point in result.points]
        rescored = []
        for hit in hits:
            lexical = keyword_overlap(query, f"{hit.title}\n{hit.text}")
            blended = (0.65 * float(hit.score)) + (0.35 * lexical)
            rescored.append(
                Hit(
                    doc_id=hit.doc_id,
                    topic=hit.topic,
                    title=hit.title,
                    language=hit.language,
                    page=hit.page,
                    chunk_id=hit.chunk_id,
                    text=hit.text,
                    score=blended,
                )
            )
        rescored.sort(key=lambda item: item.score, reverse=True)
        return rescored[:limit]


def _hit_from_point(point) -> Hit:
    payload = point.payload or {}
    return Hit(
        doc_id=payload["doc_id"],
        topic=payload["topic"],
        title=payload["title"],
        language=payload["language"],
        page=int(payload["page"]),
        chunk_id=int(payload["chunk_id"]),
        text=payload["text"],
        score=float(point.score or 0.0),
    )
