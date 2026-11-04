"""Capture-to-answer flow, calling route functions directly.

The sandbox forbids the loopback sockets that anyio/asyncio need, so
TestClient cannot run here. Route cores are sync and are exercised against a
real (in-memory) SQLite database instead.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services"))

import os  # noqa: E402
import json  # noqa: E402

os.environ["VEYTAC_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["VEYTAC_STORAGE_ROOT"] = "./artifacts/test-storage"

import pytest  # noqa: E402
from fastapi import HTTPException, Request, Response  # noqa: E402

from api import main as routes  # noqa: E402
from api.routers_capture import (  # noqa: E402
    AnswerBody,
    DeliverBody,
    FrameBody,
    GapBody,
    StreamBody,
    answer,
    create_gap,
    defer,
    deliver,
    ingest_frame,
    propose,
    register_stream,
    store_chunk,
)
from api.routers_review import DecisionBody, create_decision  # noqa: E402


def _create_session(body):
    return routes.create_session(body, Request({"type": "http", "headers": []}), Response())


def test_full_capture_to_answer_flow():
    sid = _create_session(
        routes.CreateSessionBody(task_id="bench-demo")
    )["session"]["id"]

    routes.consent(
        sid, routes.ConsentBody(actor_id="u", purpose="capture", grant=True)
    )
    stream = register_stream(
        sid, StreamBody(source_type="screen", epoch_id="e0", clock_id="clk0")
    )["stream"]

    assert store_chunk(sid, stream["id"], "e0", 0, b"bytes-0", None, 2000)["ack"] == "stored"
    assert store_chunk(sid, stream["id"], "e0", 0, b"bytes-0", None, 2000)["ack"] == "duplicate"
    with pytest.raises(HTTPException) as exc:
        store_chunk(sid, stream["id"], "e0", 0, b"different", None, None)
    assert exc.value.status_code == 409

    obs = ingest_frame(sid, FrameBody(at_ms=2000, recording_elapsed_ms=1500))["observation"]
    assert obs["status"] == "proposed"
    assert obs["execution_mode"] == "mock"
    decision = create_decision(sid, DecisionBody(
        task_id="bench-demo", observed_action_description=obs["description"],
        expert_original_statement="I chose this route", observation_id=obs["id"],
    ))["decision"]
    assert decision["observed_action_evidence"] == obs["evidence_refs"]
    assert decision["decision_interval_start_ms"] == 1500
    assert decision["decision_interval_end_ms"] == 1500

    gap = create_gap(
        sid, GapBody(missing_fact="why this terminal?", observation_ids=[obs["id"]])
    )["gap"]
    prop = propose(sid, {})
    assert prop["question"]["gap_id"] == gap["id"]
    qid = prop["question"]["id"]

    denied = deliver(sid, DeliverBody(question_id=qid, now_ms=1000))
    assert denied["delivered"] is False  # gate closed

    routes.question_window(sid, routes.QuestionWindowBody(actor_id="u", allow=True))
    ok = deliver(sid, DeliverBody(question_id=qid, now_ms=100_000))
    assert ok["delivered"] is True

    prop2 = propose(sid, {})
    # The answered gap stays asked; a fresh observation-derived gap yields a
    # new mock-labeled question instead of a canned fallback.
    assert prop2["question"] is not None
    assert prop2["question"]["execution_mode"] == "mock"
    assert prop2["question"]["gap_id"] != gap["id"]

    turn = answer(sid, qid, AnswerBody(text="right block is PLC-wired"))["turn"]
    assert turn["original_text"].startswith("right block")

    with pytest.raises(HTTPException) as exc2:
        answer(sid, qid, AnswerBody(text="   "))
    assert exc2.value.status_code == 400  # silence is never an answer

    deferred = defer(sid, qid, {"reason": "noisy floor"})["question"]
    assert deferred["status"] == "deferred"


def test_live_observation_contract_can_reach_a_question_without_network(monkeypatch):
    """Provider-shaped output gets server evidence and can ground a question."""
    from veytac.providers.meta import LiveMetaClient

    assert routes.health()["observation_contract"] == "observation-inference-v2"
    assert routes.health()["interaction_contract"] == "task-briefing-v1"
    monkeypatch.setenv("VEYTAC_EXECUTION_MODE", "live")

    def observe_stub(self, *, schema, **kwargs):
        assert kwargs["task_context"] == "Inspecting a fitting with a wrench."
        assert set(schema["properties"]) == {
            "description", "objects", "candidate_action", "uncertainty", "unavailable_cues"
        }
        return {
            "model": "test-model", "usage": {},
            "raw_text": json.dumps({
                "description": "An expert holds a visible wrench near a fitting.",
                "objects": ["wrench", "fitting"],
                "candidate_action": None,
                "uncertainty": "The reason for this tool choice is not visible.",
                "unavailable_cues": [],
            }),
        }

    def propose_stub(self, **kwargs):
        context = json.loads(kwargs["gap_text"])
        assert context["task"] == "Inspecting a fitting with a wrench."
        assert context["language"] == "ja"
        assert context["gaps"][0]["missing_fact"] == "The reason for this tool choice is not visible."
        assert context["latest_observation"] == "An expert holds a visible wrench near a fitting."
        return {
            "model": "test-model", "usage": {},
            "raw_text": json.dumps({
                "no_question": False, "gap_id": "", "question_type": "clarify_observation",
                "wording": "Why did you choose the wrench for this fitting?",
            }),
        }

    monkeypatch.setattr(LiveMetaClient, "observe", observe_stub)
    monkeypatch.setattr(LiveMetaClient, "propose", propose_stub)
    sid = _create_session(routes.CreateSessionBody(
        task_id="synthetic-tool-choice", languages=["ja"]))["session"]["id"]
    routes.consent(sid, routes.ConsentBody(actor_id="u", purpose="capture", grant=True))
    routes.consent(sid, routes.ConsentBody(actor_id="u", purpose="external_inference", grant=True))
    routes.set_task_brief(sid, routes.TaskBriefBody(text="Inspecting a fitting with a wrench."))
    obs = ingest_frame(sid, FrameBody(at_ms=2000, clock_id="clk0"))["observation"]
    assert obs["status"] == "proposed"
    assert obs["execution_mode"] == "live"
    assert obs["evidence_refs"][0]["asset_id"].startswith("ast_")
    candidate = propose(sid, {})["question"]
    assert candidate is not None
    assert candidate["status"] == "candidate"
    assert "wrench" in candidate["wording"]
