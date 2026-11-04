"""Transfer harness tests: abstention is not correctness."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.evals.transfer import compare, run_condition  # noqa: E402
from veytac.schemas import (  # noqa: E402
    Applicability,
    DecisionRecord,
)


def _rec(scope_predicates, record_id="dec_1") -> DecisionRecord:
    return DecisionRecord(
        record_id=record_id,
        revision=1,
        session_id="s",
        decision_interval_start_ms=0,
        decision_interval_end_ms=1,
        task_id="t",
        observed_action_description="use right terminal",
        expert_original_statement="left is spare",
        applicability=Applicability(
            scope_description="right terminal only",
            predicates=scope_predicates,
        ),
    )


def test_enriched_beats_empty_and_abstention_counted():
    cases = [
        {"case_id": "c1", "context": {"terminal": "right"}, "expected": "applies"},
        {"case_id": "c2", "context": {"terminal": "left"}, "expected": "not_applies"},
        {"case_id": "c3", "context": {}, "expected": "applies"},
    ]
    rec = _rec([{"field": "terminal", "op": "eq", "value": "right"}])
    enriched = run_condition(cases, [rec], condition="adaptive")
    assert enriched["correct"] == 2
    assert enriched["abstained"] == 1  # c3: unknown field → abstain, not correct
    empty = run_condition(cases, [], condition="passive")
    assert empty["abstained"] == 3 and empty["correct"] == 0
    report = compare([empty, enriched])
    assert report["claim"] == "not_evaluated"  # harness never auto-claims


def test_conflicting_records_do_not_silently_merge():
    rec = _rec([{"field": "terminal", "op": "eq", "value": "right"}], "dec_1")
    other = _rec([{"field": "terminal", "op": "eq", "value": "left"}], "dec_2")
    res = run_condition(
        [{"case_id": "c1", "context": {"terminal": "right"}, "expected": "applies"}],
        [rec, other],
        condition="adaptive",
    )
    assert res["correct"] == 1
