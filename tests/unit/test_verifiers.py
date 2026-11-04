"""Verifier tests: future evidence blocked, ungrounded measures blocked."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.schemas import (  # noqa: E402
    Applicability,
    Cue,
    CueOrigin,
    DecisionRecord,
    EvidenceRef,
    Locator,
    Observation,
    Question,
)
from veytac.verify.validators import (  # noqa: E402
    blocks,
    validate_decision_for_review,
    validate_observation,
    validate_question,
)


def _ref(asset="ast_1", start=1000, end=2000) -> EvidenceRef:
    return EvidenceRef(
        asset_id=asset,
        revision=1,
        locator=Locator(
            kind="time_range", clock_id="clk", start_ms=start, end_ms=end
        ),
    )


def _obs(**over) -> Observation:
    base = dict(
        id="obs_1",
        session_id="ses_1",
        window_start_ms=1000,
        window_end_ms=2000,
        description="the operator turned the dial",
    )
    base.update(over)
    return Observation(**base)


def test_future_window_blocked():
    findings = validate_observation(
        _obs(), capture_watermark_ms=1500, known_asset_ids=set()
    )
    assert blocks(findings)
    assert any(f["code"] == "OBS_FUTURE" for f in findings)


def test_unknown_asset_blocked():
    findings = validate_observation(
        _obs(evidence_refs=[_ref("ast_missing")]),
        capture_watermark_ms=5000,
        known_asset_ids={"ast_1"},
    )
    assert blocks(findings)
    assert any(f["code"] == "OBS_UNKNOWN_ASSET" for f in findings)


def test_clean_observation_passes():
    findings = validate_observation(
        _obs(evidence_refs=[_ref()]),
        capture_watermark_ms=5000,
        known_asset_ids={"ast_1"},
    )
    assert not blocks(findings)


def test_question_needs_open_gap():
    q = Question(id="q1", session_id="s", gap_id="g9", wording="What changed?")
    findings = validate_question(q, open_gap_ids={"g1"}, asked_gap_ids=set())
    assert blocks(findings)
    assert any(f["code"] == "Q_NO_GAP" for f in findings)


def test_redundant_question_warns_not_blocks():
    q = Question(id="q1", session_id="s", gap_id="g1", wording="What changed?")
    findings = validate_question(q, open_gap_ids={"g1"}, asked_gap_ids={"g1"})
    assert not blocks(findings)
    assert any(f["code"] == "Q_REDUNDANT" for f in findings)


def test_measured_cue_without_evidence_blocked():
    rec = DecisionRecord(
        record_id="dec_1",
        revision=1,
        session_id="ses_1",
        decision_interval_start_ms=1000,
        decision_interval_end_ms=2000,
        task_id="t",
        observed_action_description="act",
        expert_original_statement="it felt tight",
        applicability=Applicability(scope_description="bench"),
        cues=[Cue(description="4 Nm", origin=CueOrigin.MEASURED)],
    )
    findings = validate_decision_for_review(rec, known_asset_ids=set())
    assert blocks(findings)
