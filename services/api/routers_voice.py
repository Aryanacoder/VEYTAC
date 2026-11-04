"""Live voice route: browser mic -> backend -> Meta realtime ASR (TRD 7.4, 8.1).

WebSocket ``/api/v1/sessions/{id}/voice``. The browser streams raw 16-bit
mono PCM @24 kHz binary frames; the server relays them to Meta (key stays
server-side) and returns normalized app voice events as JSON text frames
(see veytac.voice.events). Guards:

- session must exist with processing consent (``processing_granted``),
  else the socket closes with 4403;
- voice audio reserves session budget up front (TRD 13.2) and reconciles
  on close; exhaustion closes with 4402;
- mock relay when not live, always labeled ``execution_mode=mock``;
- only finals (speechComplete) are preserved downstream; partials are
  ephemeral and never stored.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Literal

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict

from veytac.schemas import make_id, utcnow_iso
from veytac.voice import MockVoiceRelay, VoiceError, normalize_event

from .db import (get_session, list_entities, put_entity,
                 reconcile_session_call, reserve_session_call)
from .deps import db, state

router = APIRouter()


class InteractionDiagnostic(BaseModel):
    """Bounded status only. Never accept audio, transcript, or provider keys."""

    model_config = ConfigDict(extra="forbid")
    event: Literal[
        "tts_requested", "tts_started", "tts_ended", "tts_error", "tts_timeout",
        "asr_relay_connecting", "asr_relay_ready", "asr_relay_failed",
        "asr_audio_started", "asr_final", "asr_browser_started",
        "asr_browser_failed", "mic_missing", "mic_muted",
        "camera_portrait", "camera_landscape",
        "question_propose_requested", "question_propose_empty",
        "question_delivered", "question_held", "question_error",
    ]


@router.post("/api/v1/sessions/{session_id}/diagnostics")
def record_interaction_diagnostic(session_id: str, body: InteractionDiagnostic) -> dict:
    conn = db()
    if get_session(conn, session_id) is None:
        raise HTTPException(404, "session not found")
    if len(list_entities(conn, "interaction_diagnostic", session_id)) >= 80:
        raise HTTPException(429, "diagnostic limit reached")
    event = {"id": make_id("diag"), "event": body.event, "at": utcnow_iso()}
    put_entity(conn, "interaction_diagnostic", event["id"], session_id, event)
    return {"accepted": True}


def _voice_estimate_micro(seconds: int) -> int:
    # Conservative placeholder: reuse the provider audio rate until the
    # first reconciled voice bill lands (same pattern as frames).
    from veytac.providers.meta import estimate_micro

    return estimate_micro(frames=0, max_output_tokens=0, audio_seconds=seconds)


@router.websocket("/api/v1/sessions/{session_id}/voice")
async def voice_relay(session_id: str, ws: WebSocket) -> None:
    await ws.accept()
    payload = get_session(db(), session_id)
    if payload is None:
        await ws.close(code=4404)
        return
    if not payload.get("processing_granted"):
        await ws.send_text(json.dumps({"kind": "error", "message": "processing consent required"}))
        await ws.close(code=4403)
        return

    live = state.execution_mode == "live"
    if live:
        from veytac.voice.relay import MetaVoiceRelay

        try:
            relay: MockVoiceRelay | MetaVoiceRelay = MetaVoiceRelay(
                language=str(payload.get("languages", ["en"])[0]
                             if payload.get("languages") else "en"),
                session_id=f"veytac-{session_id}",
            )
        except VoiceError as exc:
            await ws.send_text(json.dumps({"kind": "error", "message": str(exc)}))
            await ws.close(code=4401)
            return
    else:
        relay = MockVoiceRelay()

    call_id = make_id("call")
    if not reserve_session_call(db(), session_id, call_id, _voice_estimate_micro(120)):
        await ws.send_text(json.dumps({"kind": "error", "message": "session budget exhausted"}))
        await ws.close(code=4402)
        return
    if live:
        import os
        from .model_calls import begin_model_call, finish_model_call
        begin_model_call(db(), session_id, call_id, kind="voice", provider="Meta",
                         model=os.getenv("VEYTAC_MODEL_ASR", "muse-voice-transcribe-1.0"),
                         estimated_micro=_voice_estimate_micro(120))
    try:
        ack = await relay.connect()
    except VoiceError as exc:
        reconcile_session_call(db(), session_id, call_id, None)
        if live:
            finish_model_call(db(), session_id, call_id, status="error")
        await ws.send_text(json.dumps({"kind": "error", "message": str(exc)}))
        await ws.close(code=4401)
        return
    await ws.send_text(json.dumps({"kind": "hello", "execution_mode": relay.execution_mode,
                                   "provider_session": ack.get("sessionId"),
                                   "budget_reserved_call": call_id}))
    norm_state: dict = {}
    audio_seconds = 0.0
    started = time.time()

    async def pump_provider() -> None:
        while True:
            try:
                raw = await relay.recv()
            except VoiceError as exc:
                try:
                    await ws.send_text(json.dumps({"kind": "error", "message": str(exc)}))
                    await ws.close(code=1011)
                except (RuntimeError, WebSocketDisconnect):
                    pass
                return
            if raw is None:
                await asyncio.sleep(0.05)
                continue
            evt = normalize_event(raw, norm_state)
            if evt is not None:
                await ws.send_text(json.dumps(evt))

    pump = asyncio.ensure_future(pump_provider())
    try:
        while True:
            try:
                msg = await ws.receive()
            except (RuntimeError, WebSocketDisconnect):
                break
            if msg.get("type") == "websocket.disconnect":
                break
            if msg.get("bytes") is not None:
                chunk: bytes = msg["bytes"]
                audio_seconds += len(chunk) / 2 / 24000  # int16 mono @24k
                try:
                    await relay.send_audio(chunk)
                except VoiceError as exc:
                    await ws.send_text(json.dumps({"kind": "error", "message": str(exc)}))
                    break
            elif msg.get("text") is not None:
                try:
                    ctl = json.loads(msg["text"])
                except ValueError:
                    continue
                if ctl.get("type") in ("endStream", "endOfInput"):
                    try:
                        await relay.finish_input()
                    except VoiceError as exc:
                        await ws.send_text(json.dumps({"kind": "error", "message": str(exc)}))
                        break
    finally:
        pump.cancel()
        await asyncio.gather(pump, return_exceptions=True)
        await relay.close()
        elapsed = max(audio_seconds, time.time() - started if audio_seconds else 0.0)
        reconcile_session_call(db(), session_id, call_id,
                               _voice_estimate_micro(max(1, int(elapsed))))
        if live:
            finish_model_call(db(), session_id, call_id, status="completed",
                              cost_micro=_voice_estimate_micro(max(1, int(elapsed))))
        try:
            await ws.close()
        except Exception:
            pass
