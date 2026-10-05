from app.deps import build_offline_graph
from app.utils.citations import valid_citations


def test_offline_demo_cites_without_a_chat_model() -> None:
    graph = build_offline_graph(top_k=8)
    loan = graph.invoke("What is the maximum consumer cash loan amount in the Northwind sample?")
    assert loan["abstained"] is False
    assert loan["search_mode"] == "hybrid"
    assert "150" in loan["answer"]
    assert valid_citations(loan["answer"], loan["sources"])
    assert any(source["topic"] == "retail-loan" for source in loan["sources"])

    missing = graph.invoke("What annual rate does the Northwind sample charge for car leasing?")
    assert missing["abstained"] is True
    assert missing["sources"] == []
