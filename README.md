# bank-doc-rag

Personal portfolio project: a multilingual RAG service over **synthetic** bank-style documents. It is not a bank product, it does not use customer data, and it is not affiliated with any employer or bank.

Ask a question in Uzbek, Russian, or English. A LangGraph flow retrieves hybrid hits from Qdrant, drops chunks that do not state the needed fact, and answers with citations of the form `[doc_id p.N cM]`.

## Architecture

```mermaid
flowchart LR
  client[Client] -->|POST /ask| api[FastAPI]
  api --> graph[LangGraph]
  graph --> retrieve[Retrieve]
  retrieve --> qdrant[(Qdrant dense + BM25)]
  qdrant --> filter[Filter]
  filter --> answer[Answer with citations]
  answer --> api
  api --> metrics["/metrics"]
  graph -.-> langfuse[Langfuse if keys are set]
```

Retrieval uses a dense OpenRouter embedding and a hashed BM25-style sparse vector, fused with Qdrant reciprocal rank fusion. If that fusion call fails, retrieval falls back to dense search blended with keyword overlap.

The chat model defaults to `openai/gpt-6-luna` on OpenRouter. If that id returns HTTP 404, the client lists models and switches to the closest available Luna chat model, then logs the id it actually used. Embeddings stay on `openai/text-embedding-3-small`.

## Run

```bash
cp .env.example .env
# put your OpenRouter key in OPENROUTER_API_KEY

docker compose up -d --build
docker compose run --rm api python -m scripts.ingest

curl -s http://localhost:8000/ask \
  -H 'content-type: application/json' \
  -d '{"question":"What is the maximum consumer cash loan amount in the Northwind sample?"}'
```

`docker compose run --rm api python -m scripts.ingest` is the one-command ingest. It talks to the `qdrant` service on the compose network.

Without Docker, point `QDRANT_URL` at a local Qdrant and run:

```bash
make ingest
make dev
```

Demo login (optional; `/ask` is open unless `AUTH_REQUIRED=true`):

```bash
curl -s http://localhost:8000/api/v1/auth/login \
  -H 'content-type: application/json' \
  -d '{"username":"demo","password":"demo-not-a-bank"}'
```

Health: `GET /health`. Metrics: `GET /metrics`. Interactive docs: `GET /docs`.

`make eval` indexes the sample corpus in an in-memory Qdrant, runs the golden set, and writes `evals/reports/test.json`. It needs `OPENROUTER_API_KEY`. CI does not call OpenRouter.

```bash
make test    # unit tests, no API key
make lint
make eval    # local only
```

## Evaluation

40 golden questions: 8 validation, 32 test. The validation split is reserved for prompt changes. The table below is the **test** split only. Prompts are `v1` and were not edited from test scores.

Metrics:

- **Faithfulness** and **answer relevancy** are an LLM judge in the RAGAS style (0–1), not the RAGAS library.
- **Context precision** is the RAGAS rank-weighted formula over retrieved topics that the golden item marks as relevant. Unanswerable items are excluded because they have no relevant topic.
- **Citation rate** is the share of answerable items whose final answer contains at least one `[doc_id p.N cM]` that matches a filtered source. If the model omits citations, the answer node appends them. **Model citation rate** is the same check before that safety net.
- **Key-fact accuracy** checks that required figures appear as numeric tokens. **Abstention accuracy** is the share of unanswerable items that refused.

<!-- EVAL_TABLE_START -->
Ran `python -m evals.main --split val` on 2026-10-05. Chat model resolved to `openai/gpt-6-luna` (the requested id; no 404 fallback). Embeddings: `openai/text-embedding-3-small`. Search mode on every validation question: `hybrid`. 45 chunks indexed. The **test split did not run.**

The key then stopped working. OpenRouter returned HTTP 402: first a completion-token cap ("can only afford 255"), then `Prompt tokens limit exceeded: 998 > 871`, then `Insufficient credits. This account never purchased credits.` A probe after the run got 402 for both a one-token embedding and a 16-token chat completion, so the test split could not be scored. Report file: `evals/reports/val.json`.

Every validation answer abstained. On the calls that returned HTTP 200, the grader's relevant set was empty, so citation rate and key-fact accuracy are 0 because no answer was generated. That is a failure of this run, not a completed quality score. Abstention accuracy is 1.0 because the two unanswerable items also abstained. Faithfulness 0.667 and answer relevancy 1.000 are the mean of the **3** items the judge managed to score (5 judge calls failed). One of those three is an answerable question whose refusal was scored faithfulness 0.

| Metric | Validation (n=8) | Test (n=32) |
| --- | ---: | ---: |
| Faithfulness | 0.667 (3 judged, 5 failed) | not run |
| Answer relevancy | 1.000 (3 judged, 5 failed) | not run |
| Context precision | 0.932 | not run |
| Citation rate (answerable) | 0.000 | not run |
| Model citation rate before the safety net | 0.000 | not run |
| Key-fact accuracy (answerable) | 0.000 | not run |
| Abstention accuracy | 1.000 | not run |
| Top-hit language match (answerable) | 1.000 | not run |
| Mean latency | 1372 ms | not run |

Context precision is real for this validation slice: hybrid retrieval put the expected topics high in the top 8. The answer path did not use those hits.

After this run, the filter prompt sent to the model was limited to 4 chunks of 450 characters, and an empty grader now falls back to distinctive-token overlap. Those changes are in the code and are **not** reflected in the table above. Re-run `make eval` with a funded OpenRouter key before treating any answer metric as a result.
<!-- EVAL_TABLE_END -->

## Sample corpus

`data/samples/` has 15 short markdown files: five fictional topics (retail loan, debit-card fees, KYC, deposits, SWIFT) in English, Russian, and Uzbek. Every file is marked sample / synthetic and is not affiliated with any bank. The institution name Northwind Community Bank is fictional. Regenerate with `python data/build_samples.py`.

## Limitations

- The corpus is tiny and synthetic. Scores do not transfer to a real bank archive.
- The judge is one model scoring another, so faithfulness and relevancy move when the model or prompt changes.
- Hybrid search depends on Qdrant sparse vectors. The keyword fallback is there when fusion is unavailable.
- There is no speech-to-text, orchestration scheduler, or live core-banking connector.
- Demo JWT uses one shared password. Do not point this at real customers.
- Langfuse tracing is a no-op unless `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set and the `langfuse` package imports.

## License and credit

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

Scaffold inspired by [wassim249/fastapi-langgraph-agent-production-ready-template](https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template) (MIT, Copyright (c) 2025 Wassim EL BAKKOURI): FastAPI layout, LangGraph workflow shape, Prometheus metrics, optional Langfuse hook, demo JWT, Compose, CI, and a scripted eval harness. The README, sample documents, retrieval flow, and golden set here were written for this portfolio.
