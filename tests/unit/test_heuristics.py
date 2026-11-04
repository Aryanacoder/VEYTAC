"""Heuristic rehearsal-question tests (mock-labeled, never training data)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.apprentice.heuristics import heuristic_gap_and_question  # noqa: E402


def test_eating_gets_food_question():
    fact, wording = heuristic_gap_and_question("the person is eating lunch")
    assert "eat" in fact
    assert "having" in wording or "choose" in wording


def test_wiring_gets_component_question():
    fact, wording = heuristic_gap_and_question("tightened the terminal screw for the plc")
    assert "component" in fact or "tool" in fact


def test_unknown_gets_open_invite_not_canned_jargon():
    fact, wording = heuristic_gap_and_question("something happens in the room")
    assert "window" not in wording
    assert len(wording) > 20
