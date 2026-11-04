"""M1 schema invariant tests: invalid refs rejected, no fabricated measurements."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.schemas import (  # noqa: E402
    Applicability,
    Cue,
    CueOrigin,
    DatasetRelease,
    DecisionRecord,
    EvidenceRef,
    Locator,
    ReleaseState,
    Review,
    ReviewState,
    evaluate_applicability,
    rank_score,
)


def _time_ref(start=1000, end=2000) -> EvidenceRef:
    return EvidenceRef(
        asset_id="ast_demo0001",
        revision=1,
        locator=Locator(
            kind="time_range", clock_id="clock_demo0001", start_ms=start, end_ms=end
        ),
    )


def _record(**over) -> DecisionRecord:
    base = dict(
        record_id="dec_demo0001",
        revision=1,
        session_id="ses_demo0001",
        decision_interval_start_ms=1000,
        decision_interval_end_ms=2000,
        task_id="task_demo",
        observed_action_description="tightened the terminal screw",
        observed_action_evidence=[_time_ref()],
        expert_original_statement="original statement",
        applicability=Applicability(scope_description="bench demo"),
    )
    base.update(over)
    return DecisionRecord(**base)


def test_time_locator_requires_clock_and_order():
    with pytest.raises(Exception):
        Locator(kind="time_range", start_ms=2000, end_ms=1000)
    with pytest.raises(Exception):
        Locator(kind="time_range", start_ms=1000, end_ms=2000)  # no clock


def test_document_locator_requires_page():
    with pytest.raises(Exception):
        Locator(kind="document_page")
    Locator(kind="document_page", page=3)


def test_region_box_bounds_checked():
    with pytest.raises(Exception):
        Locator(
            kind="document_page",
            page=1,
            region_xyxy_normalized=[0.0, 0.0, 1.5, 1.0],
        )


def test_approved_record_rejects_measurement_without_evidence():
    with pytest.raises(Exception):
        _record(
            cues=[Cue(description="torque 4Nm", origin=CueOrigin.MEASURED)],
            review=Review(state=ReviewState.APPROVED),
        )


def test_approved_record_keeps_reported_attribution():
    rec = _record(
        cues=[
            Cue(
                description="screw felt tight",
                origin=CueOrigin.EXPERT_REPORTED,
                evidence_refs=[_time_ref()],
            )
        ],
        review=Review(state=ReviewState.APPROVED),
    )
    assert rec.cues[0].origin == CueOrigin.EXPERT_REPORTED


def test_publish_requires_exact_manifest_hash():
    with pytest.raises(Exception):
        DatasetRelease(
            id="rel_1",
            episode_id="ep_1",
            episode_revision=1,
            manifest_hash="abc",
            state=ReleaseState.PUBLISHED,
            published_manifest_hash="different",
        )
    rel = DatasetRelease(
        id="rel_1",
        episode_id="ep_1",
        episode_revision=1,
        manifest_hash="abc",
        state=ReleaseState.PUBLISHED,
        published_manifest_hash="abc",
    )
    assert rel.state == ReleaseState.PUBLISHED


def test_applicability_unknown_on_missing_field():
    app = Applicability(
        scope_description="demo", predicates=[{"field": "x", "op": "eq", "value": "1"}]
    )
    from veytac.schemas import ApplicabilityResult

    assert evaluate_applicability(app, {}) is ApplicabilityResult.UNKNOWN


def test_rank_features_bounded():
    with pytest.raises(ValueError):
        rank_score(1.5, 0.5, 0.5, 0.5, 0.1)
    s = rank_score(1.0, 1.0, 1.0, 1.0, 0.0)
    assert abs(s - 1.0) < 1e-9
