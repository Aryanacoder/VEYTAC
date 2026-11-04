"""Rehearsal question heuristics (mock mode only, always labeled).

These templates turn an observation's own words into a spoken question so the
voice loop is exercisable without a paid key. They are NOT understanding:
every question carries execution_mode=mock, and live mode replaces them with
model-grounded questions. A rehearsal question is never training data.
"""

from __future__ import annotations

_RULES: list[tuple[tuple[str, ...], str, str]] = [
    (
        ("eat", "food", "meal", "drink", "bite"),
        "what is being eaten or drunk",
        "What are you having, and what made you choose it right now?",
    ),
    (
        ("wire", "cable", "screw", "tool", "fix", "repair", "terminal", "plc"),
        "why this component or tool",
        "What told you to pick this one over the alternatives in front of you?",
    ),
    (
        ("screen", "click", "cad", "scada", "code", "typing", "button", "display"),
        "why this on-screen action",
        "What are you doing on screen, and what decides the next step?",
    ),
    (
        ("walk", "carry", "move", "lift", "place", "put"),
        "why this movement or placement",
        "What decided that movement — what were you responding to?",
    ),
]


def heuristic_gap_and_question(observation_text: str) -> tuple[str, str]:
    """Return (missing_fact, wording) derived from the observation's words."""
    lowered = observation_text.lower()
    for keywords, fact, wording in _RULES:
        if any(k in lowered for k in keywords):
            return fact, wording
    return (
        "what the person is deciding right now",
        "Talk me through what you are doing right now — what is the key decision?",
    )
