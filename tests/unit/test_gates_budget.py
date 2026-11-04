"""M1 unit tests: budget ledger, question gates, mock providers."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.apprentice.gates import delivery_allowed, pick_question  # noqa: E402
from veytac.budget.ledger import BudgetLedger, usd_to_micro  # noqa: E402
from veytac.providers.mock import question_plan  # noqa: E402
from veytac.schemas import Question  # noqa: E402


def test_reserve_before_dispatch_and_cap():
    ledger = BudgetLedger(cap_micro=usd_to_micro("3.00"))
    assert ledger.reserve("call_1", usd_to_micro("2.00"))
    assert not ledger.reserve("call_2", usd_to_micro("2.00"))  # over cap denied
    ledger.reconcile("call_1", usd_to_micro("2.00"), usd_to_micro("0.50"))
    assert ledger.available_micro == usd_to_micro("2.50")


def test_unknown_billing_stays_charged():
    ledger = BudgetLedger(cap_micro=usd_to_micro("3.00"))
    assert ledger.reserve("call_1", usd_to_micro("1.00"))
    ledger.reconcile("call_1", usd_to_micro("1.00"), None)
    assert ledger.unknown_micro == usd_to_micro("1.00")
    assert ledger.available_micro == usd_to_micro("2.00")


def test_money_uses_decimal_not_float():
    assert usd_to_micro("0.10") + usd_to_micro("0.20") == usd_to_micro("0.30")


def test_gate_defaults_closed():
    ok, _ = delivery_allowed(
        questions_allowed=False, outstanding=0, now_ms=0,
        window_expires_ms=None, last_delivered_ms=None,
    )
    assert not ok


def test_gate_one_at_a_time_and_cooldown():
    ok, _ = delivery_allowed(
        questions_allowed=True, outstanding=1, now_ms=100_000,
        window_expires_ms=200_000, last_delivered_ms=None,
    )
    assert not ok
    ok, _ = delivery_allowed(
        questions_allowed=True, outstanding=0, now_ms=100_000,
        window_expires_ms=200_000, last_delivered_ms=90_000,
    )
    assert not ok  # 10s < 45s cooldown
    ok, reason = delivery_allowed(
        questions_allowed=True, outstanding=0, now_ms=200_000,
        window_expires_ms=300_000, last_delivered_ms=90_000,
    )
    assert ok, reason


def test_pick_dedups_by_gap():
    q1 = Question(id="q1", session_id="s", gap_id="g1", wording="a")
    q2 = Question(id="q2", session_id="s", gap_id="g1", wording="b")
    picked = pick_question(
        [q1, q2],
        task_relevance={"q1": 0.9, "q2": 0.1},
        divergence={}, consequence={}, novelty={}, burden={},
        asked_gap_ids=set(),
    )
    assert picked is not None and picked.id == "q1"
    assert pick_question(
        [q1, q2],
        task_relevance={}, divergence={}, consequence={}, novelty={},
        burden={}, asked_gap_ids={"g1"},
    ) is None


def test_mock_question_provider_labels_mock():
    # Sync core: the sandbox forbids the loopback sockets that Windows
    # asyncio needs, so unit tests exercise the plan directly.
    out = question_plan(
        {
            "session_id": "s",
            "gaps": [{"id": "g1", "missing_fact": "why?", "state": "open"}],
            "asked_targets": [],
        }
    )
    assert out["execution_mode"] == "mock"
    assert len(out["questions"]) == 1
