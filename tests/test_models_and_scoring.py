import json
from pathlib import Path

import pytest

from app.services.models import ModelNotFoundError, choose_chat_model
from app.services.sparse import sparse_tf
from evals.scoring import context_precision, facts_present, number_tokens


def test_preferred_model_wins_when_listed() -> None:
    assert choose_chat_model("openai/gpt-6-luna", {"openai/gpt-6-luna"}) == "openai/gpt-6-luna"


def test_fallback_skips_missing_id_and_batch() -> None:
    available = {"openai/gpt-6-luna:batch", "openai/gpt-5.6-luna", "sao10k/l3-lunaris-8b"}
    assert choose_chat_model("openai/gpt-6-luna", available) == "openai/gpt-5.6-luna"


def test_missing_luna_raises() -> None:
    with pytest.raises(ModelNotFoundError):
        choose_chat_model("openai/gpt-6-luna", {"openai/gpt-4o-mini"})


def test_sparse_indices_are_stable() -> None:
    assert sparse_tf("Loan fee 24.9") == sparse_tf("Loan fee 24.9")


def test_context_precision_rewards_early_relevant_hits() -> None:
    score = context_precision(["retail-loan", "card-fees", "retail-loan"], ["retail-loan"])
    assert score == pytest.approx((1 + (2 / 3)) / 2)


def test_context_precision_zero_when_nothing_relevant() -> None:
    assert context_precision(["card-fees"], ["retail-loan"]) == 0.0


def test_context_precision_undefined_for_unanswerable() -> None:
    assert context_precision(["card-fees"], []) is None


def test_golden_set_has_forty_unique_questions() -> None:
    path = Path(__file__).resolve().parents[1] / "evals" / "golden" / "questions.json"
    questions = json.loads(path.read_text(encoding="utf-8"))
    assert len(questions) == 40
    assert sum(1 for item in questions if item["split"] == "val") == 8
    assert sum(1 for item in questions if item["split"] == "test") == 32
    texts = [item["question"] for item in questions]
    assert len(texts) == len(set(texts))


def test_number_tokens_ignore_grouping_spaces() -> None:
    assert "150000000" in number_tokens("maximum 150 000 000 UZS")
    assert facts_present("The rate is 24.9% and the cap is 15%.", ["24.9", "15"])
    assert not facts_present("The rate is 24.9%.", ["15"])
