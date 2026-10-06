"""Retrieve and cite sample chunks with no chat and no embedding API."""

import json

from app.deps import build_offline_graph

QUESTIONS = (
    "What is the maximum consumer cash loan amount in the Northwind sample?",
    "What is the Classic debit card issuance fee in the Northwind sample?",
    "What annual rate does the Northwind sample charge for car leasing?",
)


def main() -> None:
    graph = build_offline_graph()
    rows = []
    for question in QUESTIONS:
        result = graph.invoke(question)
        rows.append(
            {
                "question": question,
                "answer": result.get("answer"),
                "abstained": bool(result.get("abstained")),
                "search_mode": result.get("search_mode"),
                "sources": result.get("sources") or [],
                "mode": "offline-extractive",
            }
        )
    print(json.dumps(rows, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
