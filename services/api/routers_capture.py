"""Capture → observation → question flow (TRD 3, 6, 8.1 slice 2).

Chunk bytes are stored under opaque IDs; idempotency is
(session, stream, epoch, seq) with hash-conflict detection (409).
Frame snapshots trigger a mock observation through the verifier gate.
No server clock is ever mixed with client clocks without marking.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from veytac.apprentice.gates import delivery_allowed, pick_question
from veytac.providers.mock import observe_plan, question_plan
from veytac.schemas import (
    EvidenceKind,
    EvidenceRef,
    GapState,
    KnowledgeGap,
    Locator,
    MediaStream,
    Observation,
    ObservationInference,
    Question,
    make_id,
)
from veytac.verify.validators import (
    blocks,
    validate_observation,
    validate_question,
)

from .db import (get_session, list_entities, mutate_session, put_entity,
                 reconcile_session_call, reserve_session_call)
from .deps import db

router = APIRouter()


def storage_root() -> Path:
    root = Path(os.getenv("VEYTAC_STORAGE_ROOT", "./artifacts/storage"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _payload(session_id: str) -> dict:
    payload = get_session(db(), session_id)
    if payload is None:
        raise HTTPException(404, "session not found")
    return payload


class StreamBody(BaseModel):
    source_type: str
    epoch_id: str
    clock_id: str
    codec: str = ""


@router.post("/api/v1/sessions/{session_id}/streams")
def register_stream(session_id: str, body: StreamBody) -> dict:
    _payload(session_id)
    stream = MediaStream(
        id=make_id("str"),
        session_id=session_id,
        source_type=body.source_type,
        epoch_id=body.epoch_id,
        clock_id=body.clock_id,
        codec=body.codec,
    )
    put_entity(db(), "stream", stream.id, session_id, stream.model_dump())
    return {"request_id": make_id("req"), "stream": stream.model_dump()}


def store_chunk(
    session_id: str,
    stream_id: str,
    epoch_id: str,
    seq: int,
    body: bytes,
    declared_sha: str | None,
    interval_end_ms: int | None,
    recording_elapsed_ms: int | None = None,
    gap_before_ms: int | None = None,
) -> dict:
    """Sync idempotent core (directly testable without an event loop)."""
    if len(body) > 16 * 1024 * 1024:
        raise HTTPException(413, "chunk exceeds 16 MB; renegotiate, not silently dropped")
    if recording_elapsed_ms is not None and not 0 <= recording_elapsed_ms <= 900_000:
        raise HTTPException(422, "invalid recording clock")
    if gap_before_ms is not None and gap_before_ms < 0:
        raise HTTPException(422, "invalid recording gap")
    digest = hashlib.sha256(body).hexdigest()
    if declared_sha and declared_sha != digest:
        raise HTTPException(400, "sha256 mismatch: bytes do not match manifest")
    conn = db()
    row = conn.execute(
        "SELECT sha256 FROM chunks WHERE session_id=? AND stream_id=? AND epoch_id=? AND sequence_no=?",
        (session_id, stream_id, epoch_id, seq),
    ).fetchone()
    if row:
        if row[0] != digest:
            raise HTTPException(409, "sequence already stored with different bytes")
        return {"request_id": make_id("req"), "ack": "duplicate", "sha256": digest}
    locator = storage_root() / session_id / stream_id / epoch_id / f"{seq}.bin"
    locator.parent.mkdir(parents=True, exist_ok=True)
    locator.write_bytes(body)
    conn.execute(
        "INSERT INTO chunks(session_id, stream_id, epoch_id, sequence_no, sha256, size_bytes, locator)"
        " VALUES(?,?,?,?,?,?,?)",
        (session_id, stream_id, epoch_id, seq, digest, len(body), str(locator)),
    )
    conn.commit()
    if recording_elapsed_ms is not None:
        timing_id = f"{stream_id}:{epoch_id}:{seq}"
        put_entity(conn, "chunk_timing", timing_id, session_id, {
            "id": timing_id, "stream_id": stream_id, "epoch_id": epoch_id,
            "sequence_no": seq, "clock_id": "recording_elapsed",
            "elapsed_end_ms": recording_elapsed_ms,
            "gap_before_ms": gap_before_ms,
        })
    # Advance the capture watermark from client-reported interval ends only.
    if interval_end_ms is not None:
        mutate_session(conn, session_id, lambda payload: payload.update(
            watermark_ms=max(int(payload.get("watermark_ms", 0)), interval_end_ms)))
    return {"request_id": make_id("req"), "ack": "stored", "sha256": digest}


@router.put("/api/v1/sessions/{session_id}/streams/{stream_id}/chunks/{seq}")
async def upload_chunk(
    session_id: str, stream_id: str, seq: int, request: Request
) -> dict:
    """Idempotent byte upload. Same hash replays ack; hash conflict is 409."""
    q = request.query_params
    body = await request.body()
    end = q.get("interval_end_ms")
    elapsed = q.get("recording_elapsed_ms")
    gap = q.get("gap_before_ms")
    try:
        end_ms = int(end) if end is not None else None
        elapsed_ms = int(elapsed) if elapsed is not None else None
        gap_ms = int(gap) if gap is not None else None
    except ValueError as exc:
        raise HTTPException(422, "invalid chunk timing") from exc
    return store_chunk(
        session_id,
        stream_id,
        q.get("epoch_id", "e0"),
        seq,
        body,
        q.get("sha256"),
        end_ms,
        elapsed_ms,
        gap_ms,
    )


class FrameBody(BaseModel):
    at_ms: int
    jpeg_b64: str = ""  # snapshot bytes optional in this slice; lineage kept via at_ms
    clock_id: str = "clk_demo"
    trigger: str = ""  # why this frame was sent, e.g. "held_object_new:cup"; empty = timed poll
    frame_w: int = 0  # source pixels; required with prompts for SAM box grammar
    frame_h: int = 0
    prompts: list[dict] = []  # [{id, label, x, y, w, h}] normalized 0..1, from on-device tracking
    recording_elapsed_ms: int | None = Field(default=None, ge=0, le=900_000)


def _segment_frame(session_id: str, payload: dict, body: FrameBody) -> tuple[list, str | None]:
    """SAM masks for on-device box prompts (TRD 7.5).

    Enrichment only: masks never block the observation. Boxes come from the
    client's tracker (normalized 0..1); the server converts them to the SAM
    box grammar in source pixels. Failures return a message, not silence.
    """
    if not body.prompts or not body.frame_w or not body.frame_h or not body.jpeg_b64:
        return [], None
    valid: list[dict] = []
    labels: dict[str, str] = {}
    for p in body.prompts:
        try:
            oid = int(p.get("id"))
        except (TypeError, ValueError):
            continue
        x1 = max(0, min(body.frame_w - 1, int(float(p.get("x", 0)) * body.frame_w)))
        y1 = max(0, min(body.frame_h - 1, int(float(p.get("y", 0)) * body.frame_h)))
        x2 = max(x1, min(body.frame_w - 1, int((float(p.get("x", 0)) + float(p.get("w", 0))) * body.frame_w)))
        y2 = max(y1, min(body.frame_h - 1, int((float(p.get("y", 0)) + float(p.get("h", 0))) * body.frame_h)))
        if x2 == x1 and y2 == y1:
            continue  # degenerate after pixel rounding; SAM needs area
        valid.append({"id": oid, "x1": x1, "y1": y1, "x2": x2, "y2": y2})
        labels[str(oid)] = str(p.get("label", "object"))
    if not valid:
        return [], "no valid box prompts"
    live = _live_enabled(payload)
    if live:
        from veytac.providers.sam import SamClient, SamError, build_box_prompt, estimate_sam_micro
    else:
        from veytac.providers.sam import MockSamClient, build_box_prompt
    try:
        prompt_text = build_box_prompt((body.frame_w, body.frame_h), valid)
    except SamError as exc:
        return [], f"prompt build failed: {exc}"
    if live:
        call_id = make_id("call")
        if not reserve_session_call(db(), session_id, call_id, estimate_sam_micro(len(valid))):
            return [], "session budget exhausted: SAM skipped"
        from .model_calls import begin_model_call, finish_model_call
        from veytac.providers.sam import SamConfig
        begin_model_call(db(), session_id, call_id, kind="segmentation", provider="Meta",
                         model=SamConfig().model, estimated_micro=estimate_sam_micro(len(valid)))
        try:
            out = SamClient().segment_image(image_url=body.jpeg_b64, prompt_text=prompt_text)
        except SamError as exc:
            reconcile_session_call(db(), session_id, call_id, None)
            finish_model_call(db(), session_id, call_id, status="error")
            return [], f"live segmentation failed ({exc})"
        reconcile_session_call(db(), session_id, call_id, None)  # conservatively held until billed
        finish_model_call(db(), session_id, call_id, status="completed")
    else:
        out = MockSamClient().segment_image(image_url="", prompt_text=prompt_text)
    masks: list[dict] = []
    for r in out.get("records", []):
        mid = make_id("msk")
        rec = {"id": mid, "session_id": session_id, "frame_at_ms": body.at_ms,
               "recording_elapsed_ms": body.recording_elapsed_ms,
               "frame_w": body.frame_w, "frame_h": body.frame_h,
               "object_id": r["id"], "label": labels.get(str(r["id"]), "object"),
               "box": r["box"], "mask": r["mask"], "svg": r.get("svg"),
               "rle": r.get("rle"), "decoded": r.get("decoded", False),
               "confidence": r.get("c"), "execution_mode": out["execution_mode"],
               "model": out["model"]}
        put_entity(db(), "mask", mid, session_id, rec)
        masks.append(rec)
    return masks, None


@router.post("/api/v1/sessions/{session_id}/frames")
def ingest_frame(session_id: str, body: FrameBody) -> dict:
    """Snapshot → provider observation → verifier. Errors block, never silent."""
    from veytac.schemas import EvidenceAsset

    payload = _payload(session_id)
    watermark = int(payload.get("watermark_ms", body.at_ms))
    asset = EvidenceAsset(
        id=make_id("ast"),
        session_id=session_id,
        origin="recorded",
        sha256=hashlib.sha256(f"{session_id}:{body.at_ms}".encode()).hexdigest(),
        media_type="image/jpeg",
    )
    put_entity(db(), "asset", asset.id, session_id, asset.model_dump())
    if _live_enabled(payload):
        record = _live_observe(session_id, payload, asset.id, body, watermark)
        put_entity(db(), "observation", record["id"], session_id, record)
        masks, sam_error = _segment_frame(session_id, payload, body)
        return {"request_id": make_id("req"), "observation": record,
                "masks": masks, "sam_error": sam_error}
    plan = observe_plan(
        {
            "session_id": session_id,
            "window_start_ms": max(0, body.at_ms - 8000),
            "window_end_ms": min(body.at_ms, watermark),
        }
    )
    obs = Observation(**plan["observation"])
    findings = validate_observation(
        obs,
        capture_watermark_ms=watermark,
        known_asset_ids={asset.id},
    )
    record = {
        **obs.model_dump(),
        "execution_mode": plan["execution_mode"],
        "status": "failed" if blocks(findings) else "proposed",
        "findings": findings,
        "trigger": body.trigger,
        "recording_elapsed_ms": body.recording_elapsed_ms,
    }
    put_entity(db(), "observation", obs.id, session_id, record)
    masks, sam_error = _segment_frame(session_id, payload, body)
    return {"request_id": make_id("req"), "observation": record,
            "masks": masks, "sam_error": sam_error}


def _live_enabled(payload: dict) -> bool:
    import os

    return os.getenv("VEYTAC_EXECUTION_MODE", "mock") == "live" and bool(
        payload.get("processing_granted")
    )


def _live_observe(session_id: str, payload: dict, asset_id: str,
                  body: FrameBody, watermark: int) -> dict:
    """Reserve → live call → reconcile → validate. Failure is stored, not hidden."""
    import json as _json

    from veytac.providers.meta import (
        LiveMetaClient,
        OBSERVATION_OUTPUT_TOKENS,
        ProviderError,
        estimate_micro,
        usage_to_micro,
    )

    call_id = make_id("call")
    estimate = estimate_micro(frames=1, max_output_tokens=OBSERVATION_OUTPUT_TOKENS)
    if not reserve_session_call(db(), session_id, call_id, estimate):
        raise HTTPException(402, "session budget exhausted: live observation refused")
    from .model_calls import begin_model_call, finish_model_call
    from veytac.providers.meta import MetaConfig
    begin_model_call(db(), session_id, call_id, kind="observation", provider="Meta",
                     model=MetaConfig().observer_model, estimated_micro=estimate)
    window = {
        "start_ms": max(0, body.at_ms - 8000), "end_ms": min(body.at_ms, watermark),
        "clock_id": body.clock_id, "with_pixels": bool(body.jpeg_b64),
    }
    expert_notes = sorted(list_entities(db(), "expert_note", session_id),
                          key=lambda note: note.get("at_ms", 0))[-3:]
    task_context = payload.get("task_brief") or payload.get("task_id", "")
    if expert_notes:
        task_context = _json.dumps({
            "task": task_context,
            "expert_reported_unreviewed": [note["text"] for note in expert_notes],
        }, ensure_ascii=False)
    try:
        out = LiveMetaClient().observe(
            window_text=_json.dumps(window),
            task_context=task_context,
            schema=ObservationInference.model_json_schema(),
            image_data_urls=[body.jpeg_b64] if body.jpeg_b64 else None,
        )
    except ProviderError as exc:
        reconcile_session_call(db(), session_id, call_id, None)  # may still be billed
        finish_model_call(db(), session_id, call_id, status="error")
        raise HTTPException(502, f"live observation failed ({exc}); no mock substituted")
    reconcile_session_call(db(), session_id, call_id,
                           usage_to_micro(out.get("usage", {})))
    finish_model_call(db(), session_id, call_id, status="completed", usage=out.get("usage"),
                      cost_micro=usage_to_micro(out.get("usage", {})))
    if not isinstance(out.get("raw_text"), str) or not out["raw_text"].strip():
        return {
            "id": make_id("obs"), "session_id": session_id,
            "execution_mode": "live", "status": "failed",
            "findings": [{"code": "PROVIDER_EMPTY", "severity": "error",
                          "message": f"model returned no observation text (finish_reason={out.get('finish_reason')})"}],
            "model": out["model"], "usage": out.get("usage", {}),
        }
    try:
        parsed = _json.loads(out["raw_text"])
        draft = ObservationInference.model_validate(parsed)
        frame_ms = window["end_ms"]
        obs = Observation(
            id=make_id("obs"), session_id=session_id,
            window_start_ms=window["start_ms"], window_end_ms=window["end_ms"],
            model=out["model"], prompt_version="live-3-minimal-reasoning",
            evidence_refs=[EvidenceRef(
                asset_id=asset_id, revision=1,
                locator=Locator(kind=EvidenceKind.TIME_RANGE,
                                clock_id=body.clock_id,
                                start_ms=frame_ms, end_ms=frame_ms),
            )],
            **draft.model_dump(),
        )
    except Exception as exc:
        return {
            "id": make_id("obs"), "session_id": session_id,
            "execution_mode": "live", "status": "failed",
            "findings": [{"code": "PROVIDER_INVALID",
                          "severity": "error",
                          "message": f"unparseable provider output ({type(exc).__name__}, finish_reason={out.get('finish_reason')})"}],
            "model": out["model"], "usage": out.get("usage", {}),
        }
    findings = validate_observation(
        obs, capture_watermark_ms=watermark, known_asset_ids={asset_id})
    return {**obs.model_dump(), "execution_mode": "live",
            "status": "failed" if blocks(findings) else "proposed",
            "findings": findings, "usage": out.get("usage", {}),
            "trigger": body.trigger,
            "recording_elapsed_ms": body.recording_elapsed_ms}


@router.get("/api/v1/sessions/{session_id}/observations")
def get_observations(session_id: str) -> dict:
    _payload(session_id)
    return {
        "request_id": make_id("req"),
        "observations": list_entities(db(), "observation", session_id),
    }


class GapBody(BaseModel):
    missing_fact: str
    competing_interpretations: list[str] = []
    consequence: str = ""
    observation_ids: list[str] = []


@router.post("/api/v1/sessions/{session_id}/gaps")
def create_gap(session_id: str, body: GapBody) -> dict:
    _payload(session_id)
    gap = KnowledgeGap(
        id=make_id("gap"),
        session_id=session_id,
        missing_fact=body.missing_fact,
        competing_interpretations=body.competing_interpretations,
        consequence=body.consequence,
        observation_ids=body.observation_ids,
    )
    put_entity(db(), "gap", gap.id, session_id, gap.model_dump())
    return {"request_id": make_id("req"), "gap": gap.model_dump()}


@router.post("/api/v1/sessions/{session_id}/questions/propose")
def propose(session_id: str, body: dict | None = None) -> dict:
    payload = _payload(session_id)
    gaps = list_entities(db(), "gap", session_id)
    asked = {q["gap_id"] for q in list_entities(db(), "question", session_id)}
    if _live_enabled(payload):
        record = _live_propose(session_id, payload, gaps, asked)
        if record is not None:
            put_entity(db(), "question", record["id"], session_id, record)
            return {"request_id": make_id("req"), "question": record}
        return {"request_id": make_id("req"), "question": None,
                "reason": "live provider returned no question"}
    heuristic_wording: str | None = None
    if not any(g["id"] not in asked and g["state"] == GapState.OPEN.value for g in gaps):
        # No stored uncertainty: derive one from the latest observation's own
        # words (mock heuristic, always labeled) instead of a canned fallback.
        from veytac.apprentice.heuristics import heuristic_gap_and_question

        observations = list_entities(db(), "observation", session_id)
        proposed = [o for o in observations if o.get("status") == "proposed"]
        if proposed:
            latest = max(proposed, key=lambda o: o.get("window_end_ms", 0))
            fact, wording = heuristic_gap_and_question(latest.get("description", ""))
            gap = KnowledgeGap(
                id=make_id("gap"), session_id=session_id, missing_fact=fact,
                observation_ids=[latest["id"]],
            )
            put_entity(db(), "gap", gap.id, session_id, gap.model_dump())
            gaps = list_entities(db(), "gap", session_id)
            heuristic_wording = wording
    plan = question_plan(
        {"session_id": session_id, "gaps": gaps, "asked_targets": sorted(asked)}
    )
    if not plan["questions"]:
        return {"request_id": make_id("req"), "question": None, "reason": plan["no_question_reason"]}
    cand = Question(**plan["questions"][0])
    if heuristic_wording is not None and cand.gap_id == gap.id:
        cand.wording = heuristic_wording
    findings = validate_question(
        cand,
        open_gap_ids={g["id"] for g in gaps if g["state"] == GapState.OPEN.value},
        asked_gap_ids=asked,
    )
    record = {
        **cand.model_dump(),
        "execution_mode": plan["execution_mode"],
        "status": "rejected" if blocks(findings) else "candidate",
        "findings": findings,
    }
    put_entity(db(), "question", cand.id, session_id, record)
    return {"request_id": make_id("req"), "question": record}


class AnswerBody(BaseModel):
    text: str
    language: str = "en"
    speaker: str = "expert"


@router.post("/api/v1/sessions/{session_id}/questions/{question_id}/answers")
def answer(session_id: str, question_id: str, body: AnswerBody) -> dict:
    """Final answers only. Silence/unknown/skip are explicit, never invented."""
    from veytac.schemas import DialogueTurn

    conn = db()
    _payload(session_id)
    stored = list_entities(conn, "question", session_id)
    match = next((q for q in stored if q["id"] == question_id), None)
    if match is None:
        raise HTTPException(404, "question not found")
    if not body.text.strip():
        raise HTTPException(400, "empty answer refused: record unknown/skip explicitly")
    turn = DialogueTurn(
        id=make_id("turn"),
        session_id=session_id,
        question_id=question_id,
        speaker=body.speaker,
        original_language=body.language,
        original_text=body.text,
    )
    put_entity(conn, "turn", turn.id, session_id, turn.model_dump())
    match["status"] = "answered"
    put_entity(conn, "question", match["id"], session_id, match)
    return {"request_id": make_id("req"), "turn": turn.model_dump()}


@router.post("/api/v1/sessions/{session_id}/questions/{question_id}/defer")
def defer(session_id: str, question_id: str, body: dict | None = None) -> dict:
    conn = db()
    _payload(session_id)
    stored = list_entities(conn, "question", session_id)
    match = next((q for q in stored if q["id"] == question_id), None)
    if match is None:
        raise HTTPException(404, "question not found")
    match["status"] = "deferred"
    match["superseded_reason"] = (body or {}).get("reason", "deferred by human")
    put_entity(conn, "question", match["id"], session_id, match)
    return {"request_id": make_id("req"), "question": match}


class DeliverBody(BaseModel):
    question_id: str
    now_ms: int


@router.post("/api/v1/sessions/{session_id}/questions/deliver")
def deliver(session_id: str, body: DeliverBody) -> dict:
    """Human-gated delivery: safe-pause gate decides, never the model."""
    conn = db()
    payload = _payload(session_id)
    questions = list_entities(conn, "question", session_id)
    match = next((q for q in questions if q["id"] == body.question_id), None)
    if match is None:
        raise HTTPException(404, "question not found")
    outstanding = sum(1 for q in questions if q.get("status") == "delivered")
    ok, reason = delivery_allowed(
        questions_allowed=bool(payload.get("questions_allowed")),
        outstanding=outstanding,
        now_ms=body.now_ms,
        window_expires_ms=payload.get("window_expires_ms"),
        last_delivered_ms=payload.get("last_delivered_ms"),
        delivered_this_session=int(payload.get("delivered_count", 0)),
    )
    if not ok:
        return {"request_id": make_id("req"), "delivered": False, "reason": reason}
    match["status"] = "delivered"
    put_entity(conn, "question", match["id"], session_id, match)
    mutate_session(conn, session_id, lambda current: current.update(
        last_delivered_ms=body.now_ms,
        delivered_count=int(current.get("delivered_count", 0)) + 1))
    return {"request_id": make_id("req"), "delivered": True, "question": match}


def _live_propose(session_id: str, payload: dict, gaps: list[dict],
                  asked: set[str]) -> dict | None:
    """Reserve → live question call → reconcile → validate. No mock fallback."""
    import json as _json

    from veytac.providers.meta import (
        LiveMetaClient,
        QUESTION_OUTPUT_TOKENS,
        ProviderError,
        estimate_micro,
        usage_to_micro,
    )

    fresh = [g for g in gaps
             if g["id"] not in asked and g["state"] == GapState.OPEN.value]
    derived_from_observation = False
    if not fresh:
        # No stored uncertainty: ask the model what is missing straight from
        # the latest observations, then persist that as a gap (TRD 6.1).
        observations = [o for o in list_entities(db(), "observation", session_id)
                        if o.get("status") == "proposed"]
        if not observations:
            return None
        latest = max(observations, key=lambda o: o.get("window_end_ms", 0))
        missing = latest.get("uncertainty") or latest.get("description", "")
        fresh = [{"id": "", "missing_fact": missing,
                  "competing_interpretations": [],
                  "observation_ids": [latest["id"]]}]
        derived_from_observation = True
    call_id = make_id("call")
    estimate = estimate_micro(frames=0, max_output_tokens=QUESTION_OUTPUT_TOKENS)
    if not reserve_session_call(db(), session_id, call_id, estimate):
        raise HTTPException(402, "session budget exhausted: live question refused")
    from .model_calls import begin_model_call, finish_model_call
    from veytac.providers.meta import MetaConfig
    begin_model_call(db(), session_id, call_id, kind="question", provider="Meta",
                     model=MetaConfig().observer_model, estimated_micro=estimate)
    gap_text = _json.dumps({
        "task": payload.get("task_brief") or payload.get("task_id", ""),
        "expert_reported_unreviewed": [note["text"] for note in
            sorted(list_entities(db(), "expert_note", session_id),
                   key=lambda note: note.get("at_ms", 0))[-3:]],
        "language": (payload.get("languages") or ["en"])[0],
        "latest_observation": latest.get("description", "") if derived_from_observation else "",
        "gaps": [{"id": g["id"], "missing_fact": g["missing_fact"],
                  "competing": g.get("competing_interpretations", [])}
                 for g in fresh[:3]],
    })
    try:
        out = LiveMetaClient().propose(
            gap_text=gap_text,
            schema={"type": "object",
                    "properties": {
                        "no_question": {"type": "boolean"},
                        "gap_id": {"type": "string"},
                        "wording": {"type": "string"},
                        "question_type": {"type": "string"}},
                    "required": ["no_question"]},
        )
    except ProviderError as exc:
        reconcile_session_call(db(), session_id, call_id, None)
        finish_model_call(db(), session_id, call_id, status="error")
        raise HTTPException(502, f"live question failed ({exc}); no mock substituted")
    reconcile_session_call(db(), session_id, call_id,
                           usage_to_micro(out.get("usage", {})))
    finish_model_call(db(), session_id, call_id, status="completed", usage=out.get("usage"),
                      cost_micro=usage_to_micro(out.get("usage", {})))
    try:
        parsed = _json.loads(out["raw_text"])
    except Exception:
        return None
    if parsed.get("no_question") or not parsed.get("wording"):
        return None
    try:
        cand = Question(id=make_id("q"), session_id=session_id,
                        gap_id=parsed.get("gap_id", fresh[0]["id"]),
                        wording=parsed["wording"],
                        question_type=parsed.get("question_type",
                                                 "clarify_observation"))
    except Exception:
        return None
    if derived_from_observation:
        gap_rec = KnowledgeGap(
            id=make_id("gap"), session_id=session_id,
            missing_fact=fresh[0]["missing_fact"],
            observation_ids=fresh[0].get("observation_ids", []),
        )
        put_entity(db(), "gap", gap_rec.id, session_id, gap_rec.model_dump())
        cand.gap_id = gap_rec.id
        fresh = [{**fresh[0], "id": gap_rec.id}]
    findings = validate_question(
        cand,
        open_gap_ids={g["id"] for g in fresh},
        asked_gap_ids=asked,
    )
    return {**cand.model_dump(), "execution_mode": "live",
            "status": "rejected" if blocks(findings) else "candidate",
            "findings": findings, "usage": out.get("usage", {})}


def pick_ranked(session_id: str, features: dict[str, dict[str, float]]) -> dict | None:
    """Ranking entry point used by the worker slice (TRD 6.2)."""
    conn = db()
    stored = list_entities(conn, "question", session_id)
    cands = [Question(**q) for q in stored if q.get("status") == "candidate"]
    asked = {q["gap_id"] for q in stored}
    best = pick_question(
        cands,
        task_relevance=features.get("task_relevance", {}),
        divergence=features.get("divergence", {}),
        consequence=features.get("consequence", {}),
        novelty=features.get("novelty", {}),
        burden=features.get("burden", {}),
        asked_gap_ids=asked,
    )
    return best.model_dump() if best else None
