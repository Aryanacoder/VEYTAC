"""VEYTAC API slice 1: health, sessions, consents, question window (TRD 8.1)."""

from __future__ import annotations

import hashlib
import secrets

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

from veytac.providers.meta import OBSERVATION_CONTRACT_VERSION
from veytac.schemas import ConsentPurpose, Principal, Role, make_id, new_session, utcnow_iso

from .db import get_session, insert_session, mutate_session
from .deps import db, state
from .routers_capture import router as capture_router
from .routers_library import router as library_router
from .routers_review import router as review_router
from .routers_voice import router as voice_router

app = FastAPI(title="VEYTAC API", version="0.1.0")
app.include_router(capture_router)
app.include_router(library_router)
app.include_router(review_router)
app.include_router(voice_router)


class CreateSessionBody(BaseModel):
    owner_id: str = "usr_owner"
    workspace_id: str = "ws_demo"
    task_id: str
    languages: list[str] = ["en"]
    mode: str = "LIVE_CAPTURE"


class ConsentBody(BaseModel):
    actor_id: str
    purpose: ConsentPurpose
    grant: bool = True
    notice_hash: str = "notice-v1"


class QuestionWindowBody(BaseModel):
    actor_id: str
    allow: bool
    duration_s: int = Field(default=30, ge=1, le=600)


class TaskBriefBody(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "execution_mode": state.execution_mode,
            "observation_contract": OBSERVATION_CONTRACT_VERSION,
            "interaction_contract": "task-briefing-v1"}


@app.post("/api/v1/sessions")
def create_session(body: CreateSessionBody, request: Request, response: Response) -> dict:
    owner = Principal(
        id=body.owner_id,
        workspace_id=body.workspace_id,
        role=Role.OWNER,
        auth_provenance="owner-account-prototype",
    )
    session = new_session(
        owner, body.task_id, languages=body.languages, mode=body.mode
    )
    owner_token = request.cookies.get("veytac_local_owner") or secrets.token_urlsafe(32)
    insert_session(db(), session.id, {
        **session.model_dump(),
        "owner_cookie_hash": hashlib.sha256(owner_token.encode()).hexdigest(),
    })
    response.set_cookie("veytac_local_owner", owner_token, httponly=True,
                        samesite="strict", max_age=30 * 24 * 3600, path="/")
    return {"request_id": make_id("req"), "session": session.model_dump()}


@app.get("/api/v1/sessions/{session_id}")
def get_session_route(session_id: str) -> dict:
    payload = get_session(db(), session_id)
    if payload is None:
        raise HTTPException(404, "session not found")
    return {"request_id": make_id("req"), "session": payload}


@app.post("/api/v1/sessions/{session_id}/task-brief")
def set_task_brief(session_id: str, body: TaskBriefBody) -> dict:
    payload = get_session(db(), session_id)
    if payload is None:
        raise HTTPException(404, "session not found")
    if not payload.get("capture_granted"):
        raise HTTPException(403, "capture consent required")
    mutate_session(db(), session_id,
                   lambda current: current.update(task_brief=body.text.strip()))
    return {"request_id": make_id("req"), "task_brief": body.text.strip()}


@app.post("/api/v1/sessions/{session_id}/consents")
def consent(session_id: str, body: ConsentBody) -> dict:
    payload = get_session(db(), session_id)
    if payload is None:
        raise HTTPException(404, "session not found")
    key = {
        "capture": "capture_granted",
        "external_inference": "processing_granted",
        "internal_sharing": "sharing_granted",
        "training": "training_granted",
    }.get(body.purpose.value)
    if key is None:  # internal_review / public_distribution tracked, no capture flag
        return {"request_id": make_id("req"), "recorded": True, "note": "tracked only"}
    payload, _ = mutate_session(db(), session_id,
                                lambda current: current.update({key: body.grant}))
    db().execute(
        "INSERT INTO consents(id, session_id, purpose, granted_at, revoked_at, notice_hash)"
        " VALUES(?,?,?,?,?,?)",
        (
            make_id("cns"),
            session_id,
            body.purpose.value,
            utcnow_iso() if body.grant else None,
            None if body.grant else utcnow_iso(),
            body.notice_hash,
        ),
    )
    db().commit()
    return {"request_id": make_id("req"), "session": payload}


@app.post("/api/v1/sessions/{session_id}/question-window")
def question_window(session_id: str, body: QuestionWindowBody) -> dict:
    """Human-only gate: the model can never open this (TRD 6.3)."""
    import time

    payload = get_session(db(), session_id)
    if payload is None:
        raise HTTPException(404, "session not found")
    expires = int(time.time() * 1000) + body.duration_s * 1000 if body.allow else 0
    mutate_session(db(), session_id, lambda current: current.update(
        questions_allowed=body.allow, window_expires_ms=expires))
    return {"request_id": make_id("req"), "questions_allowed": body.allow}
