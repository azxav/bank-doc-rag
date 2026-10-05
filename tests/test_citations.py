from app.utils.citations import (
    append_missing_citations,
    parse_citations,
    valid_citations,
)

SOURCES = [
    {"doc_id": "retail-loan-en", "page": 1, "chunk_id": 2},
]


def test_parse_citation() -> None:
    text = "The cap is 15% [retail-loan-en p.1 c2]."
    assert parse_citations(text) == [("retail-loan-en", 1, 2)]


def test_invalid_citation_does_not_count() -> None:
    text = "The cap is 15% [other-doc p.1 c2]."
    assert valid_citations(text, SOURCES) == []


def test_append_when_missing() -> None:
    updated, appended = append_missing_citations("The cap is 15%.", SOURCES)
    assert appended is True
    assert valid_citations(updated, SOURCES)


def test_do_not_append_when_present() -> None:
    text = "The cap is 15% [retail-loan-en p.1 c2]."
    updated, appended = append_missing_citations(text, SOURCES)
    assert appended is False
    assert updated == text
