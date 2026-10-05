"""Stable hashed term frequencies for Qdrant sparse vectors."""

from __future__ import annotations

import re
import zlib
from collections import Counter

TOKEN_RE = re.compile(r"[0-9A-Za-z\u0400-\u04FFʻ'`]+", re.UNICODE)
SPARSE_MOD = 2**20

STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "and",
    "or",
    "to",
    "for",
    "in",
    "on",
    "is",
    "are",
    "what",
    "which",
    "does",
    "do",
    "how",
    "when",
    "this",
    "that",
    "with",
    "from",
    "by",
    "be",
    "и",
    "в",
    "на",
    "по",
    "для",
    "как",
    "что",
    "это",
    "или",
    "от",
    "va",
    "ham",
    "uchun",
    "bu",
    "qanday",
    "qancha",
    "nima",
}


def normalize_token(token: str) -> str:
    return token.lower().replace("ʻ", "'").replace("`", "'").replace("’", "'")


def tokenize(text: str) -> list[str]:
    return [normalize_token(tok) for tok in TOKEN_RE.findall(text)]


def sparse_tf(text: str) -> tuple[list[int], list[float]]:
    """Return merged CRC32 indices and raw term frequencies."""
    counts = Counter(tokenize(text))
    buckets: dict[int, float] = {}
    for token, tf in counts.items():
        index = zlib.crc32(token.encode("utf-8")) % SPARSE_MOD
        buckets[index] = buckets.get(index, 0.0) + float(tf)
    indices = sorted(buckets)
    values = [buckets[index] for index in indices]
    return indices, values


GENERIC_TOKENS = {
    "northwind",
    "community",
    "bank",
    "sample",
    "loan",
    "rate",
    "annual",
    "card",
    "fee",
    "fees",
    "client",
    "clients",
    "amount",
    "uzs",
    "usd",
    "banka",
    "образце",
    "образца",
    "намуна",
    "namuna",
    "qancha",
    "какова",
    "какой",
    "какая",
    "какие",
    "что",
    "это",
}


def distinctive_tokens(text: str) -> list[str]:
    return [
        token
        for token in tokenize(text)
        if token not in STOPWORDS and token not in GENERIC_TOKENS and len(token) >= 4
    ]


def lexical_fallback(question: str, chunks: list[dict], limit: int = 4) -> list[dict]:
    """Keep chunks that share distinctive tokens when the grader returns nothing.

    A single short overlap is not enough, so an unseen product name does not
    attach itself to a generic rate or fee paragraph.
    """
    wanted = distinctive_tokens(question)
    if not wanted:
        return []
    kept: list[dict] = []
    for chunk in chunks:
        text = f"{chunk.get('title', '')}\n{chunk.get('text', '')}"
        present = set(tokenize(text))
        overlap = [token for token in wanted if token in present]
        if len(overlap) >= 2 or any(len(token) >= 8 for token in overlap):
            kept.append(chunk)
        if len(kept) >= limit:
            break
    return kept


def keyword_overlap(query: str, text: str) -> float:
    query_tokens = [tok for tok in tokenize(query) if tok not in STOPWORDS and len(tok) > 1]
    if not query_tokens:
        return 0.0
    doc_tokens = set(tokenize(text))
    hits = sum(1 for tok in query_tokens if tok in doc_tokens)
    return hits / len(query_tokens)
