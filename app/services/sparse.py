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


def keyword_overlap(query: str, text: str) -> float:
    query_tokens = [tok for tok in tokenize(query) if tok not in STOPWORDS and len(tok) > 1]
    if not query_tokens:
        return 0.0
    doc_tokens = set(tokenize(text))
    hits = sum(1 for tok in query_tokens if tok in doc_tokens)
    return hits / len(query_tokens)
