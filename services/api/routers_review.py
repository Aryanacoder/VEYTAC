"""Review, episode, export, lesson flow (TRD 4.4-4.6, 5.3, 10-11).

Review and publication are separate states. Approval pins attribution and
scope; it never converts a report into a measurement. Any payload change
invalidates publication confirmation.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from veytac.schemas import (
    Applicability,
    DecisionRecord,
    Lesson,
    LessonCheckpoint,
    Review,
    ReviewState,
    SkillEpisode,
    make_id,
    utcnow_iso,
)
from veytac.verify.validators import blocks, validate_decision_for_review

from .db import get_session, list_entities, put_entity
from .deps import db

router = APIRouter()


def _payload(session_id: str) -> dict:
    payload = get_session(db(), session_id)
    if payload is None:
        raise HTTPException(404, "session not found")
    return payload


def _decisions(session_id: str) -> list[dict]:
    return list_entities(db(), "decision", session_id)


def _latest(records: list[dict], record_id: str) -> dict | None:
    cands = [r for r in records if r["record_id"] == record_id]
    return max(cands, key=lambda r: r["revision"]) if cands else None


class DecisionBody(BaseModel):
    task_id: str
    observed_action_description: str
    expert_original_statement: str
    expert_original_language: str = "en"
    decision_interval_start_ms: int = 0
    decision_interval_end_ms: int = 0
    known_conditions: list[str] = []
    unobserved_conditions: list[str] = []
    scope_description: str = ""
    observation_id: str | None = None


@router.post("/api/v1/sessions/{session_id}/decisions")
def create_decision(session_id: str, body: DecisionBody) -> dict:
    _payload(session_id)
    observed = None
    if body.observation_id:
        observed = next((item for item in list_entities(db(), "observation", session_id)
                         if item["id"] == body.observation_id and item.get("status") == "proposed"), None)
        if observed is None:
            raise HTTPException(422, "observation must be a proposed record in this session")
    at_ms = observed.get("recording_elapsed_ms") if observed else None
    rec = DecisionRecord(
        record_id=make_id("dec"),
        revision=1,
        session_id=session_id,
        decision_interval_start_ms=at_ms if at_ms is not None else body.decision_interval_start_ms,
        decision_interval_end_ms=at_ms if at_ms is not None else body.decision_interval_end_ms,
        task_id=body.task_id,
        known_conditions=body.known_conditions,
        unobserved_conditions=body.unobserved_conditions,
        observed_action_description=body.observed_action_description,
        observed_action_evidence=observed.get("evidence_refs", []) if observed else [],
        expert_original_statement=body.expert_original_statement,
        expert_original_language=body.expert_original_language,
        applicability=Applicability(scope_description=body.scope_description),
    )
    put_entity(db(), "decision", f"{rec.record_id}:1", session_id, rec.model_dump())
    return {"request_id": make_id("req"), "decision": rec.model_dump()}


@router.get("/api/v1/sessions/{session_id}/decisions")
def list_decisions(session_id: str) -> dict:
    _payload(session_id)
    latest: dict[str, dict] = {}
    for r in _decisions(session_id):
        cur = latest.get(r["record_id"])
        if cur is None or r["revision"] > cur["revision"]:
            latest[r["record_id"]] = r
    return {"request_id": make_id("req"), "decisions": list(latest.values())}


class RevisionBody(BaseModel):
    expected_revision: int
    patch: dict


@router.post("/api/v1/decisions/{record_id}/revisions")
def revise(record_id: str, body: RevisionBody) -> dict:
    conn = db()
    rows = conn.execute(
        "SELECT session_id, payload FROM entities WHERE kind='decision' AND id LIKE ?",
        (f"{record_id}:%",),
    ).fetchall()
    if not rows:
        raise HTTPException(404, "decision not found")
    session_id = rows[0][0]
    latest = max((json.loads(r[1]) for r in rows), key=lambda d: d["revision"])
    if latest["revision"] != body.expected_revision:
        raise HTTPException(409, "stale revision: reload before editing")
    allowed = {
        "observed_action_description", "expert_original_statement",
        "known_conditions", "unobserved_conditions", "scope_description",
        "alternatives", "exceptions", "outcome_checks", "cues",
    }
    for key in body.patch:
        if key not in allowed:
            raise HTTPException(400, f"field {key} is not reviewer-editable")
    merged = dict(latest)
    for key, value in body.patch.items():
        if key == "scope_description":
            merged["applicability"]["scope_description"] = value
        else:
            merged[key] = value
    merged["revision"] = latest["revision"] + 1
    merged["review"] = Review(state=ReviewState.DRAFT).model_dump()
    rec = DecisionRecord(**merged)  # revalidate
    put_entity(conn, "decision", f"{record_id}:{rec.revision}", session_id, rec.model_dump())
    return {"request_id": make_id("req"), "decision": rec.model_dump()}


class ReviewBody(BaseModel):
    reviewer_id: str
    action: str  # approve | reject | needs_clarification
    approved_scope: str | None = None


@router.post("/api/v1/decisions/{record_id}/reviews")
def review(record_id: str, body: ReviewBody) -> dict:
    conn = db()
    rows = conn.execute(
        "SELECT session_id, payload FROM entities WHERE kind='decision' AND id LIKE ?",
        (f"{record_id}:%",),
    ).fetchall()
    if not rows:
        raise HTTPException(404, "decision not found")
    session_id = rows[0][0]
    assets = {a["id"] for a in list_entities(conn, "asset", session_id)}
    latest = max((json.loads(r[1]) for r in rows), key=lambda d: d["revision"])
    rec = DecisionRecord(**latest)
    if body.action == "approve":
        candidate = DecisionRecord(
            **{**rec.model_dump(), "review": {
                "state": "approved", "reviewer_id": body.reviewer_id,
                "reviewed_at": utcnow_iso(), "approved_scope": body.approved_scope,
            }}
        )
        findings = validate_decision_for_review(candidate, known_asset_ids=assets)
        if blocks(findings):
            raise HTTPException(422, f"approval blocked: {findings}")
        rec = candidate
    elif body.action == "reject":
        rec.review = Review(state=ReviewState.REJECTED, reviewer_id=body.reviewer_id)
    elif body.action == "needs_clarification":
        rec.review = Review(state=ReviewState.NEEDS_CLARIFICATION, reviewer_id=body.reviewer_id)
    else:
        raise HTTPException(400, "unknown review action")
    put_entity(conn, "decision", f"{record_id}:{rec.revision}", session_id, rec.model_dump())
    return {"request_id": make_id("req"), "decision": rec.model_dump()}


@router.post("/api/v1/sessions/{session_id}/episodes")
def assemble_episode(session_id: str) -> dict:
    """Immutable snapshot of approved records only (TRD 4.5)."""
    conn = db()
    payload = _payload(session_id)
    approved = [
        r for r in _decisions(session_id) if r["review"]["state"] == "approved"
    ]
    if not approved:
        raise HTTPException(422, "no approved decisions to snapshot")
    by_record: dict[str, dict] = {}
    for r in approved:
        cur = by_record.get(r["record_id"])
        if cur is None or r["revision"] > cur["revision"]:
            by_record[r["record_id"]] = r
    capabilities = ["observation", "expert_context"]
    missing = ["action_aligned: no genuine action/state trajectories in episode"]
    ep = SkillEpisode(
        episode_id=make_id("ep"),
        revision=1,
        title=f"episode for {payload.get('task_id', session_id)}",
        task_context=str(payload.get("task_id", "")),
        evidence_assets=[a["id"] for a in list_entities(conn, "asset", session_id)],
        observations=[o["id"] for o in list_entities(conn, "observation", session_id)],
        dialogue_turns=[t["id"] for t in list_entities(conn, "turn", session_id)],
        decisions=[r["record_id"] for r in by_record.values()],
        review_summary=f"{len(by_record)} approved decision(s)",
        permissions={"redistribution": False},
        capabilities=capabilities,  # type: ignore[arg-type]
        missing_fields=missing,
        split_group="train",
        lineage=[session_id],
    )
    put_entity(conn, "episode", ep.episode_id, session_id, ep.model_dump())
    return {"request_id": make_id("req"), "episode": ep.model_dump()}


@router.post("/api/v1/episodes/{episode_id}/validate")
def validate_episode(episode_id: str) -> dict:
    conn = db()
    rows = conn.execute(
        "SELECT session_id, payload FROM entities WHERE kind='episode' AND id=?",
        (episode_id,),
    ).fetchone()
    if not rows:
        raise HTTPException(404, "episode not found")
    session_id, ep = rows[0], SkillEpisode(**json.loads(rows[1]))
    assets = {a["id"] for a in list_entities(conn, "asset", session_id)}
    broken = [a for a in ep.evidence_assets if a not in assets]
    per_record: dict[str, list] = {}
    for rid in ep.decisions:
        rec_rows = conn.execute(
            "SELECT payload FROM entities WHERE kind='decision' AND id LIKE ?",
            (f"{rid}:%",),
        ).fetchall()
        latest = max((json.loads(r[0]) for r in rec_rows), key=lambda d: d["revision"])
        per_record[rid] = validate_decision_for_review(
            DecisionRecord(**latest), known_asset_ids=assets
        )
    report = {
        "id": make_id("qr"),
        "episode_id": episode_id,
        "broken_references": broken,
        "per_record": per_record,
        "valid": not broken and not any(blocks(f) for f in per_record.values()),
    }
    put_entity(conn, "quality_report", report["id"], session_id, report)
    return {"request_id": make_id("req"), "quality_report": report}


class ExportBody(BaseModel):
    profile: str = "skill_episode_v0"


@router.post("/api/v1/episodes/{episode_id}/exports")
def export_episode(episode_id: str, body: ExportBody) -> dict:
    """Canonical bundle (TRD 10.2). Robot profiles rejected for phone-only data."""
    conn = db()
    rows = conn.execute(
        "SELECT session_id, payload FROM entities WHERE kind='episode' AND id=?",
        (episode_id,),
    ).fetchone()
    if not rows:
        raise HTTPException(404, "episode not found")
    session_id, ep = rows[0], SkillEpisode(**json.loads(rows[1]))
    if body.profile in ("robot_actions_v0", "lerobot_v3", "rlds"):
        raise HTTPException(
            422,
            f"profile {body.profile} rejected: episode capabilities "
            f"{ep.capabilities} lack action alignment (FR-18)",
        )
    if body.profile not in ("skill_episode_v0", "lesson_v0"):
        raise HTTPException(400, f"unknown export profile {body.profile}")
    out = Path(os.getenv("VEYTAC_STORAGE_ROOT", "./artifacts/storage")) / "exports" / f"{episode_id}_v1"
    out.mkdir(parents=True, exist_ok=True)
    bundle = {
        "episode.json": ep.model_dump(),
        "observations.jsonl": list_entities(conn, "observation", session_id),
        "decisions.jsonl": [r for r in _decisions(session_id)
                            if r["record_id"] in set(ep.decisions)],
        "dialogue.jsonl": list_entities(conn, "turn", session_id),
    }
    for name, data in bundle.items():
        (out / name).write_text(json.dumps(data, indent=2))
    checksums = {
        name: hashlib.sha256((out / name).read_bytes()).hexdigest()
        for name in bundle
    }
    (out / "checksums.sha256").write_text(
        "".join(f"{h}  {n}\n" for n, h in sorted(checksums.items()))
    )
    manifest = {"episode_id": episode_id, "profile": body.profile,
                "files": checksums, "dir": str(out)}
    put_entity(conn, "export", make_id("exp"), session_id, manifest)
    return {"request_id": make_id("req"), "export": manifest}


@router.post("/api/v1/episodes/{episode_id}/lessons")
def build_lesson(episode_id: str) -> dict:
    """Evidence-linked lesson with decision checkpoints (TRD 11)."""
    conn = db()
    rows = conn.execute(
        "SELECT session_id, payload FROM entities WHERE kind='episode' AND id=?",
        (episode_id,),
    ).fetchone()
    if not rows:
        raise HTTPException(404, "episode not found")
    session_id, ep = rows[0], SkillEpisode(**json.loads(rows[1]))
    checkpoints = []
    for rid in ep.decisions:
        rec_rows = conn.execute(
            "SELECT payload FROM entities WHERE kind='decision' AND id LIKE ?",
            (f"{rid}:%",),
        ).fetchall()
        latest = max((json.loads(r[0]) for r in rec_rows), key=lambda d: d["revision"])
        rec = DecisionRecord(**latest)
        checkpoints.append(LessonCheckpoint(
            prompt=f"When should you '{rec.observed_action_description}', and when not?",
            expected_distinction=rec.review.approved_scope or rec.applicability.scope_description or "scope under review",
            explanation=rec.expert_original_statement,
            evidence_refs=rec.observed_action_evidence,
        ))
    lesson = Lesson(
        id=make_id("les"),
        source_episode_id=episode_id,
        source_revision=ep.revision,
        title=f"lesson: {ep.title}",
        task_context=ep.task_context,
        checkpoints=checkpoints,
        limitations=[
            "covers only the approved scope; out-of-scope conditions require abstention",
            "expert report, not independently validated engineering truth",
        ],
    )
    put_entity(conn, "lesson", lesson.id, session_id, lesson.model_dump())
    return {"request_id": make_id("req"), "lesson": lesson.model_dump()}


@router.get("/api/v1/sessions/{session_id}/lessons")
def list_lessons(session_id: str) -> dict:
    """Return the session's persisted reviewed lessons for human study."""
    _payload(session_id)
    return {"request_id": make_id("req"), "lessons": list_entities(db(), "lesson", session_id)}
