"""Review → episode → export → lesson, route functions direct (no sockets)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services"))

import os  # noqa: E402

os.environ["VEYTAC_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["VEYTAC_STORAGE_ROOT"] = "./artifacts/test-storage"

import pytest  # noqa: E402
from fastapi import HTTPException, Request, Response  # noqa: E402

from api import main as routes  # noqa: E402
from api.routers_capture import AnswerBody, GapBody, StreamBody  # noqa: E402
from api.routers_capture import (  # noqa: E402
    FrameBody,
    answer,
    create_gap,
    ingest_frame,
    propose,
    register_stream,
    store_chunk,
)
from api.routers_review import (  # noqa: E402
    DecisionBody,
    RevisionBody,
    ReviewBody,
    assemble_episode,
    build_lesson,
    create_decision,
    export_episode,
    ExportBody,
    list_decisions,
    list_lessons,
    review,
    revise,
    validate_episode,
)


def _create_session(body):
    return routes.create_session(body, Request({"type": "http", "headers": []}), Response())


def _session_with_answer() -> tuple[str, str]:
    sid = _create_session(routes.CreateSessionBody(task_id="t"))["session"]["id"]
    stream = register_stream(
        sid, StreamBody(source_type="screen", epoch_id="e0", clock_id="c")
    )["stream"]
    store_chunk(sid, stream["id"], "e0", 0, b"x", None, 2000)
    obs = ingest_frame(sid, FrameBody(at_ms=2000))["observation"]
    create_gap(sid, GapBody(missing_fact="why?", observation_ids=[obs["id"]]))
    q = propose(sid, {})["question"]
    routes.question_window(sid, routes.QuestionWindowBody(actor_id="u", allow=True))
    from api.routers_capture import DeliverBody, deliver

    deliver(sid, DeliverBody(question_id=q["id"], now_ms=100_000))
    answer(sid, q["id"], AnswerBody(text="because the left block is a spare"))
    return sid, q["id"]


def test_review_revise_approve_episode_export_lesson():
    sid, _ = _session_with_answer()
    dec = create_decision(
        sid,
        DecisionBody(
            task_id="t",
            observed_action_description="used the right terminal",
            expert_original_statement="left block is a spare",
            scope_description="bench PLC wiring",
        ),
    )["decision"]
    rid = dec["record_id"]

    rev = revise(rid, RevisionBody(expected_revision=1, patch={
        "known_conditions": ["power off"],
    }))["decision"]
    assert rev["revision"] == 2
    assert rev["review"]["state"] == "draft"  # edit resets approval

    with pytest.raises(HTTPException) as stale:
        revise(rid, RevisionBody(expected_revision=1, patch={}))
    assert stale.value.status_code == 409

    approved = review(rid, ReviewBody(
        reviewer_id="rev1", action="approve", approved_scope="supervised bench PLC wiring",
    ))["decision"]
    assert approved["review"]["state"] == "approved"

    ep = assemble_episode(sid)["episode"]
    assert "expert_context" in ep["capabilities"]
    assert any("action_aligned" in m for m in ep["missing_fields"])

    qr = validate_episode(ep["episode_id"])["quality_report"]
    assert qr["valid"] is True

    with pytest.raises(HTTPException) as robot:
        export_episode(ep["episode_id"], ExportBody(profile="robot_actions_v0"))
    assert robot.value.status_code == 422  # phone-only cannot claim actions

    bundle = export_episode(ep["episode_id"], ExportBody(profile="skill_episode_v0"))["export"]
    assert (Path(bundle["dir"]) / "checksums.sha256").exists()

    lesson = build_lesson(ep["episode_id"])["lesson"]
    assert len(lesson["checkpoints"]) == 1
    assert lesson["source_revision"] == 1
    assert lesson["checkpoints"][0]["expected_distinction"] == "supervised bench PLC wiring"
    assert list_lessons(sid)["lessons"][0]["id"] == lesson["id"]

    listed = list_decisions(sid)["decisions"]
    assert len(listed) == 1 and listed[0]["revision"] == 2
