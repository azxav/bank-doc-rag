"""Run the golden set against OpenRouter and write evals/reports/latest.json.

The published README table uses the test split. The val split is held out for
prompt changes: do not pick prompt text from test scores.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from qdrant_client import QdrantClient

from app.core.config import settings
from app.core.langgraph.graph import RAGGraph
from app.core.prompts import JUDGE_SYSTEM, PROMPT_VERSION
from app.services.ingest import ingest_samples
from app.services.llm import OpenRouterChat, OpenRouterEmbeddings
from app.services.store import VectorStore
from app.utils.json_extract import parse_json_object
from evals.scoring import context_precision, facts_present, has_valid_citation

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = Path(__file__).resolve().parent / "golden" / "questions.json"
REPORTS = Path(__file__).resolve().parent / "reports"


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def judge(chat: OpenRouterChat, question: str, answer: str, contexts: list[str]) -> dict:
    context_block = "\n".join(contexts) if contexts else "(no context)"
    user = f"Question: {question}\n\nAnswer: {answer}\n\nContext:\n{context_block}"
    raw = chat.complete(
        JUDGE_SYSTEM,
        user,
        max_tokens=200,
        json_mode=True,
        operation="judge",
    )
    parsed = parse_json_object(raw)
    return {
        "faithfulness": _clamp(parsed["faithfulness"]),
        "answer_relevancy": _clamp(parsed["answer_relevancy"]),
    }


def evaluate(split: str) -> dict:
    questions = json.loads(GOLDEN.read_text(encoding="utf-8"))
    selected = [item for item in questions if split == "all" or item["split"] == split]
    if len(questions) != 40:
        raise RuntimeError(f"Expected 40 golden questions, found {len(questions)}")
    store = VectorStore(client=QdrantClient(":memory:"), collection="eval_bank_docs")
    embedder = OpenRouterEmbeddings()
    chat = OpenRouterChat()
    started = time.perf_counter()
    chunk_count = ingest_samples(store=store, embedder=embedder)
    graph = RAGGraph(store, embedder, chat, top_k=settings.RETRIEVAL_TOP_K)
    rows = []
    for item in selected:
        row_started = time.perf_counter()
        result = graph.invoke(item["question"])
        latency_ms = (time.perf_counter() - row_started) * 1000
        retrieved = result.get("retrieved") or []
        sources = result.get("sources") or []
        answer = result.get("answer") or ""
        answerable = item["type"] != "unanswerable"
        precision = context_precision(
            [hit["topic"] for hit in retrieved],
            item["expected_topics"],
        )
        citation_ok = has_valid_citation(answer, sources) if answerable else None
        model_cited = bool(citation_ok) and not result.get("citations_appended")
        if not answerable:
            model_cited = False
        fact_ok = (
            facts_present(answer, item["required_facts"])
            if answerable
            else bool(result.get("abstained"))
        )
        top_language = retrieved[0]["language"] if retrieved else None
        judge_scores: dict | None = None
        judge_error = None
        try:
            judge_scores = judge(
                chat,
                item["question"],
                answer,
                [hit.get("text") or hit.get("excerpt", "") for hit in retrieved],
            )
        except Exception as exc:
            judge_error = str(exc)
        rows.append(
            {
                "id": item["id"],
                "split": item["split"],
                "type": item["type"],
                "language": item["language"],
                "abstained": bool(result.get("abstained")),
                "latency_ms": round(latency_ms, 1),
                "faithfulness": None if not judge_scores else judge_scores["faithfulness"],
                "answer_relevancy": None if not judge_scores else judge_scores["answer_relevancy"],
                "context_precision": precision,
                "citation_ok": citation_ok,
                "model_cited": model_cited if answerable else None,
                "key_fact_or_abstention": fact_ok,
                "top_language": top_language,
                "language_match": top_language == item["language"] if answerable else None,
                "search_mode": result.get("search_mode"),
                "judge_error": judge_error,
                "answer": answer,
            }
        )
        print(
            f"{item['id']} abstained={bool(result.get('abstained'))} "
            f"fact={fact_ok} cite={citation_ok} judge_error={bool(judge_error)}",
            flush=True,
        )

    def values(key: str, predicate) -> list[float]:
        found = []
        for row in rows:
            if not predicate(row):
                continue
            value = row[key]
            if value is None:
                continue
            found.append(float(value))
        return found

    answerable_rows = [row for row in rows if row["type"] != "unanswerable"]
    unanswerable_rows = [row for row in rows if row["type"] == "unanswerable"]
    summary = {
        "split": split,
        "n": len(rows),
        "n_answerable": len(answerable_rows),
        "n_unanswerable": len(unanswerable_rows),
        "prompt_version": PROMPT_VERSION,
        "chat_model_preferred": chat.preferred_model,
        "chat_model_resolved": chat.resolved_model,
        "embedding_model": settings.EMBEDDING_MODEL,
        "chunks_indexed": chunk_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": round(time.perf_counter() - started, 1),
        "faithfulness": _mean(values("faithfulness", lambda row: True)),
        "answer_relevancy": _mean(values("answer_relevancy", lambda row: True)),
        "context_precision": _mean(
            values("context_precision", lambda row: row["type"] != "unanswerable")
        ),
        "citation_rate_answerable": _mean(
            values("citation_ok", lambda row: row["type"] != "unanswerable")
        ),
        "model_citation_rate_answerable": _mean(
            values("model_cited", lambda row: row["type"] != "unanswerable")
        ),
        "key_fact_accuracy_answerable": _mean(
            values("key_fact_or_abstention", lambda row: row["type"] != "unanswerable")
        ),
        "abstention_accuracy": _mean(
            values("key_fact_or_abstention", lambda row: row["type"] == "unanswerable")
        ),
        "language_match_answerable": _mean(
            values("language_match", lambda row: row["type"] != "unanswerable")
        ),
        "mean_latency_ms": _mean(values("latency_ms", lambda row: True)),
        "judge_failures": sum(1 for row in rows if row["judge_error"]),
        "search_modes": sorted({row["search_mode"] for row in rows}),
    }
    return {"summary": summary, "rows": rows}


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate bank-doc-rag on the golden set")
    parser.add_argument("--split", choices=["val", "test", "all"], default="test")
    args = parser.parse_args()
    report = evaluate(args.split)
    REPORTS.mkdir(parents=True, exist_ok=True)
    target = REPORTS / f"{args.split}.json"
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (REPORTS / "latest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    summary = report["summary"]
    print()
    print(f"prompt {summary['prompt_version']}")
    print(f"chat {summary['chat_model_resolved']} (preferred {summary['chat_model_preferred']})")
    print(f"embeddings {summary['embedding_model']}")
    print(f"judge failures {summary['judge_failures']}")
    print("| metric | value |")
    print("| --- | --- |")
    for key in (
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "citation_rate_answerable",
        "model_citation_rate_answerable",
        "key_fact_accuracy_answerable",
        "abstention_accuracy",
        "language_match_answerable",
        "mean_latency_ms",
    ):
        value = summary[key]
        rendered = f"{value:.1f}" if key == "mean_latency_ms" and value is not None else _fmt(value)
        print(f"| {key} | {rendered} |")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
