from fastapi.testclient import TestClient

from app.main import app


class FakeGraph:
    def invoke(self, question: str, top_k: int | None = None) -> dict:
        return {
            "answer": "The maximum is 150000000 UZS [retail-loan-en p.1 c1].",
            "sources": [
                {
                    "doc_id": "retail-loan-en",
                    "title": "Synthetic retail loan terms",
                    "language": "en",
                    "page": 1,
                    "chunk_id": 1,
                    "score": 0.5,
                    "excerpt": "The maximum amount is 150000000 UZS.",
                }
            ],
            "abstained": False,
        }


def test_health_and_root() -> None:
    client = TestClient(app)
    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["name"] == "bank-doc-rag"
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["components"]["qdrant"] == "healthy"
    metrics = client.get("/metrics")
    assert metrics.status_code == 200


def test_ask_returns_answer_sources_and_latency(monkeypatch) -> None:
    monkeypatch.setattr("app.api.v1.ask.get_graph", lambda: FakeGraph())
    client = TestClient(app)
    response = client.post("/ask", json={"question": "What is the maximum loan?"})
    assert response.status_code == 200
    body = response.json()
    assert "150000000" in body["answer"]
    assert body["sources"][0]["doc_id"] == "retail-loan-en"
    assert body["sources"][0]["page"] == 1
    assert body["sources"][0]["chunk_id"] == 1
    assert body["latency_ms"] >= 0
    assert body["trace_id"]
    alias = client.post("/api/v1/ask", json={"question": "What is the maximum loan?"})
    assert alias.status_code == 200


def test_demo_login_roundtrip() -> None:
    client = TestClient(app)
    rejected = client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": "wrong-password"},
    )
    assert rejected.status_code == 401
    token = client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": "demo-not-a-bank"},
    )
    assert token.status_code == 200
    access = token.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["username"] == "demo"


def test_compose_file_lists_api_and_qdrant() -> None:
    from pathlib import Path

    text = (Path(__file__).resolve().parents[1] / "docker-compose.yml").read_text(encoding="utf-8")
    assert "qdrant/qdrant" in text
    assert "api:" in text
