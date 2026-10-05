# bank-doc-rag

I built a multilingual RAG system over synthetic bank-style documents. My stack is a LangGraph flow on Qdrant hybrid retrieval (dense plus BM25), answers with `[doc_id p.N cM]` citations, an offline demo that never calls a chat model, and a fixed golden set for evals. Prometheus exposes metrics. Docker Compose boots the API and Qdrant.

Northwind Community Bank exists only inside the sample files. The documents are synthetic. I did not use customer data.

OpenRouter is optional. `make test` and `make demo-offline` do not call it. Live `/ask` and `make eval` do, and they need a key with credit.

## Architecture

```mermaid
flowchart LR
  client[Client] -->|POST /ask| api[FastAPI]
  api --> graph[LangGraph]
  graph --> retrieve[Retrieve]
  retrieve --> qdrant[(Qdrant dense plus BM25)]
  qdrant --> filter[Filter]
  filter --> answer[Answer with citations]
  answer --> api
  api --> metrics["/metrics"]
  filter -.-> offline[Offline extractive citations]
  answer -.-> openrouter[OpenRouter chat when a key is set]
  retrieve -.-> embeddings[OpenRouter embeddings or local hash vectors]
  graph -.-> langfuse[Langfuse only if keys are set]
```

Default retrieval is hybrid: a dense vector plus a hashed BM25 sparse vector, fused in Qdrant with reciprocal rank fusion. If fusion fails, retrieval uses dense scores blended with keyword overlap.

Live chat defaults to `openai/gpt-6-luna`. If that id returns HTTP 404, the client picks the closest listed Luna chat model and logs the id it used. Live embeddings default to `openai/text-embedding-3-small`.

`make demo-offline` never calls chat. It indexes the samples with local hash vectors, keeps chunks by distinctive-token overlap, and quotes those chunks with citations.

## Run

Offline, no API key:

```bash
make demo-offline
```

That prints three questions as JSON. Two quote a sample chunk and cite it. The car-leasing question abstains because the corpus does not contain it.

To serve the same offline path:

```bash
OFFLINE_DEMO=true python -m uvicorn app.main:app --port 8000
curl -s http://localhost:8000/ask \
  -H 'content-type: application/json' \
  -d '{"question":"What is the maximum consumer cash loan amount in the Northwind sample?"}'
```

`OFFLINE_DEMO=true` uses an in-memory index and ignores `QDRANT_URL`.

Checks that CI runs, still with no key:

```bash
make test
make lint
```

Live stack, only after `OPENROUTER_API_KEY` is set in `.env`:

```bash
cp .env.example .env
docker compose up -d --build
docker compose run --rm api python -m scripts.ingest
curl -s http://localhost:8000/ask \
  -H 'content-type: application/json' \
  -d '{"question":"What is the maximum consumer cash loan amount in the Northwind sample?"}'
```

`docker compose run --rm api python -m scripts.ingest` is the one-command ingest against the Compose Qdrant. Without Docker, point `QDRANT_URL` at a local Qdrant and run `make ingest` then `make dev`.

Demo login is optional. `/ask` stays open unless `AUTH_REQUIRED=true`.

```bash
curl -s http://localhost:8000/api/v1/auth/login \
  -H 'content-type: application/json' \
  -d '{"username":"demo","password":"demo-not-a-bank"}'
```

Health: `GET /health`. Metrics: `GET /metrics`. Docs: `GET /docs`.

## Evaluation

I wrote 40 golden questions: 8 validation, 32 test. The validation split is the held-out slice for prompt changes. Prompts in the run below are `v1`. I did not edit them from test scores, and I did not score the test split.

- **Faithfulness** and **answer relevancy** are an LLM judge in the RAGAS style, 0 to 1. This repo does not import the RAGAS library.
- **Context precision** is the RAGAS rank-weighted score over retrieved topics listed on the golden item. Unanswerable items are left out because they have no relevant topic.
- **Citation rate** is the share of answerable items whose final answer has at least one `[doc_id p.N cM]` matching a filtered source. If a live model omits citations, the answer node appends them. **Model citation rate** is the check before that append.
- **Key-fact accuracy** requires the golden figures as numeric tokens. **Abstention accuracy** is the share of unanswerable items that refused.

<!-- EVAL_TABLE_START -->
Partial validation run only. I ran `python -m evals.main --split val` on 2026-10-05. Chat model resolved to `openai/gpt-6-luna`. Embeddings: `openai/text-embedding-3-small`. Search mode: `hybrid` on all 8 questions. 45 chunks indexed. Artifact: `evals/reports/val.json`.

I did not run the test split (n=32). OpenRouter returned HTTP 402: a completion-token cap ("can only afford 255"), then `Prompt tokens limit exceeded: 998 > 871`, then `Insufficient credits. This account never purchased credits.` A later one-token embedding and a 16-token chat completion also returned 402.

Every validation answer abstained. Citation rate and key-fact accuracy are 0 because no answer was generated. Faithfulness and answer relevancy average the 3 judge calls that returned a score. The other 5 judge calls failed. One of the three scored items is an answerable refusal marked faithfulness 0. Abstention accuracy is 1.0 because the two unanswerable items also abstained. Empty cells are not filled in.

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

Context precision is a retrieval result on this validation slice. The answer path did not use the hits.

After that run I limited grader prompts to 4 chunks of 450 characters, and an empty grader can fall back to distinctive-token overlap. Those edits are not in the table. Re-score before reading the table as the current answer quality.

When the key has credit:

```bash
cp .env.example .env   # set OPENROUTER_API_KEY
make eval              # test split, writes evals/reports/test.json
python -m evals.main --split val
python -m evals.main --split all
```
<!-- EVAL_TABLE_END -->

## Sample corpus

`data/samples/` has 15 short markdown files: retail loan, debit-card fees, KYC, deposits, and SWIFT, each in English, Russian, and Uzbek. Every file says it is synthetic and not affiliated with any bank. Regenerate with `python data/build_samples.py`.

## Limitations

- The corpus is small and synthetic. The validation numbers do not transfer to a real archive.
- I did not measure test-split faithfulness, relevancy, context precision, citation rate, or key-fact accuracy. The blocker is OpenRouter HTTP 402, not a missing harness.
- The offline demo quotes retrieved text. It is not the live chat model and it is not the eval.
- The judge is one model scoring another. Five of eight validation judge calls failed.
- Hybrid search needs Qdrant sparse vectors. Keyword blending is the fallback.
- I did not add speech-to-text, a scheduler, or a live core-banking connector.
- The demo JWT is one shared password.
- Langfuse stays off unless both Langfuse keys are set and the package imports.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE). FastAPI and LangGraph scaffold patterns follow [wassim249/fastapi-langgraph-agent-production-ready-template](https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template) (MIT, Copyright (c) 2025 Wassim EL BAKKOURI).
