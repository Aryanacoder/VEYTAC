"""Session-budget book tests: reserve-before-dispatch enforced per session."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.budget.ledger import reconcile_call, reserve_call, usd_to_micro  # noqa: E402


def test_session_cap_blocks_live_call():
    payload = {"budget_cap_usd": "3.00"}
    assert reserve_call(payload, "c1", usd_to_micro("2.00"))
    assert not reserve_call(payload, "c2", usd_to_micro("2.00"))
    reconcile_call(payload, "c1", usd_to_micro("0.10"))
    assert payload["budget"]["spent_micro"] == usd_to_micro("0.10")
    assert reserve_call(payload, "c3", usd_to_micro("2.00"))


def test_failed_call_holds_unknown():
    payload = {"budget_cap_usd": "3.00"}
    assert reserve_call(payload, "c1", usd_to_micro("1.00"))
    reconcile_call(payload, "c1", None)
    assert payload["budget"]["unknown_micro"] == usd_to_micro("1.00")
