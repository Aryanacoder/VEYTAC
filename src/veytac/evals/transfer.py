"""Held-out knowledge-transfer evaluation (FR-30, VERIFICATION 6.2).

Compares conditions (passive observation, fixed questions, adaptive questions)
at equivalent expert-time budgets on frozen held-out cases. Abstention is
counted separately from correctness: a system that abstains on everything has
not achieved useful transfer. No improvement claim without a positive,
within-scope result.
"""

from __future__ import annotations

from veytac.schemas import (
    ApplicabilityResult,
    DecisionRecord,
    evaluate_applicability,
)


class HeldOutCase(dict):
    """{case_id, context: {field: value}, expected: applies|not_applies, budget_notes}"""


def predict(records: list[DecisionRecord], context: dict[str, str]) -> str:
    """First applicable verdict wins; no covering record (or all unknown) = abstain."""
    saw_unknown = False
    for rec in records:
        verdict = evaluate_applicability(rec.applicability, context)
        if verdict is ApplicabilityResult.APPLIES:
            return "applies"
        if verdict is ApplicabilityResult.UNKNOWN:
            saw_unknown = True
    # A NOT_APPLIES verdict anywhere with no APPLIES means the rule set refuses.
    for rec in records:
        if evaluate_applicability(rec.applicability, context) is ApplicabilityResult.NOT_APPLIES:
            return "not_applies"
    return "unknown" if saw_unknown or not records else "not_applies"


def run_condition(
    cases: list[HeldOutCase], records: list[DecisionRecord], *, condition: str, budget_notes: str = ""
) -> dict:
    correct = incorrect = abstained = 0
    per_case = []
    for case in cases:
        pred = predict(records, case["context"])
        if pred == "unknown":
            abstained += 1
            outcome = "abstained"
        elif pred == case["expected"]:
            correct += 1
            outcome = "correct"
        else:
            incorrect += 1
            outcome = "incorrect"
        per_case.append({"case_id": case["case_id"], "predicted": pred,
                         "expected": case["expected"], "outcome": outcome})
    return {
        "condition": condition,
        "budget_notes": budget_notes,
        "n": len(cases),
        "correct": correct,
        "incorrect": incorrect,
        "abstained": abstained,
        "per_case": per_case,
    }


def compare(results: list[dict]) -> dict:
    """Head-to-head report. Never claims improvement from an anecdote."""
    return {
        "conditions": results,
        "claim": "not_evaluated",
        "note": "positive_within_scope requires a predeclared protocol, matched "
        "budgets, and reviewer-approved expected distinctions",
    }
