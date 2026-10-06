from pathlib import Path

from app.services.chunking import chunk_markdown, load_sample_chunks

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"


def test_chunk_markdown_assigns_pages() -> None:
    raw = """---
doc_id: retail-loan-en
topic: retail-loan
language: en
title: Synthetic retail loan terms
---
SAMPLE / SYNTHETIC — not affiliated with any bank.

## Page 1
Minimum 5000000 UZS.

## Page 2
Fee 1.0%.
"""
    chunks = chunk_markdown(raw, "sample.md")
    assert [chunk.chunk_id for chunk in chunks] == [1, 2]
    assert [chunk.page for chunk in chunks] == [1, 2]
    assert chunks[0].key == "retail-loan-en#1"


def test_banner_is_required() -> None:
    raw = """---
doc_id: x-en
topic: x
language: en
title: X
---
## Page 1
No banner here.
"""
    try:
        chunk_markdown(raw, "x.md")
    except ValueError as exc:
        assert "banner" in str(exc)
    else:
        raise AssertionError("expected banner failure")


def test_sample_corpus_is_multilingual_and_labelled() -> None:
    files = list(SAMPLES.glob("*.md"))
    assert len(files) == 15
    chunks = load_sample_chunks(SAMPLES)
    languages = {chunk.language for chunk in chunks}
    topics = {chunk.topic for chunk in chunks}
    assert languages == {"en", "ru", "uz"}
    assert topics == {"retail-loan", "card-fees", "kyc", "deposits", "fx-transfers"}
    assert len(chunks) == 45
    for path in files:
        text = path.read_text(encoding="utf-8").lower()
        assert "not affiliated with any bank" in text
        assert "synthetic" in text or "синтет" in text or "sun'iy" in text
