"""Split synthetic markdown samples into page-aware chunks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
PAGE_RE = re.compile(r"^## Page (\d+)\s*$", re.MULTILINE)
BANNER = "not affiliated with any bank"
MAX_CHUNK_CHARS = 900


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    topic: str
    title: str
    language: str
    page: int
    chunk_id: int
    text: str

    @property
    def key(self) -> str:
        return f"{self.doc_id}#{self.chunk_id}"

    def embed_text(self) -> str:
        return f"{self.title}\n{self.text}"


def _parse_front_matter(block: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta


def _split_long(page: int, text: str) -> list[tuple[int, str]]:
    text = text.strip()
    if len(text) <= MAX_CHUNK_CHARS:
        return [(page, text)] if text else []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    groups: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if current and len(candidate) > MAX_CHUNK_CHARS:
            groups.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        groups.append(current)
    return [(page, group) for group in groups]


def chunk_markdown(raw: str, source_name: str = "") -> list[Chunk]:
    if BANNER not in raw.lower():
        raise ValueError(f"{source_name or 'document'} is missing the synthetic banner")
    match = FRONT_MATTER_RE.match(raw)
    if not match:
        raise ValueError(f"{source_name or 'document'} is missing front matter")
    meta = _parse_front_matter(match.group(1))
    for field in ("doc_id", "topic", "language", "title"):
        if field not in meta:
            raise ValueError(f"{source_name or 'document'} front matter lacks {field}")
    body = raw[match.end() :]
    pages = list(PAGE_RE.finditer(body))
    if not pages:
        raise ValueError(f"{source_name or 'document'} has no '## Page N' sections")
    pieces: list[tuple[int, str]] = []
    for index, page_match in enumerate(pages):
        start = page_match.end()
        end = pages[index + 1].start() if index + 1 < len(pages) else len(body)
        page_no = int(page_match.group(1))
        pieces.extend(_split_long(page_no, body[start:end]))
    chunks: list[Chunk] = []
    for chunk_id, (page, text) in enumerate(pieces, start=1):
        chunks.append(
            Chunk(
                doc_id=meta["doc_id"],
                topic=meta["topic"],
                title=meta["title"],
                language=meta["language"],
                page=page,
                chunk_id=chunk_id,
                text=text,
            )
        )
    return chunks


def load_sample_chunks(sample_dir: Path) -> list[Chunk]:
    files = sorted(sample_dir.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No markdown samples in {sample_dir}")
    chunks: list[Chunk] = []
    for path in files:
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), path.name))
    return chunks
