"""Normalize Meta realtime ASR server events into app voice events.

Reference: Meta speech-to-text docs (S04) + realtime API reference.
Server events: speechStart{turnId}, transcript{transcript,final} (partials
carry no turnId — they belong to the most recent open turn), speaker{label},
speechEnd{turnId} (boundary only, NOT the transcript), speechComplete{turnId,
transcript} (authoritative turn text), error{message}.

App events emitted: boundary{turn,phase}, partial{turn,text},
final{turn,text,late}, speaker{turn,label}, error{message,transient}.

Partials are ephemeral by design; only finals (speechComplete) are
preserved. Finals can arrive out of order relative to later turns —
a final for an older turn after a newer completed is marked late, never
rewritten into the newer turn (TRD 7.4).
"""

from __future__ import annotations


def normalize_event(raw: dict, state: dict) -> dict | None:
    """Fold one Meta server event. `state` tracks open_turn and completed turns."""
    kind = raw.get("type")
    if kind == "speechStart":
        turn = int(raw.get("turnId", 0))
        state["open_turn"] = turn
        return {"kind": "boundary", "phase": "start", "turn": turn}
    if kind == "transcript":
        turn = state.get("open_turn", 0)
        if turn == 0:
            return None  # no open turn: unattributable partial, drop loudly nowhere
        return {"kind": "partial", "turn": turn, "text": str(raw.get("transcript", ""))}
    if kind == "speaker":
        turn = state.get("open_turn", 0)
        return {"kind": "speaker", "turn": turn, "label": str(raw.get("label", "?"))}
    if kind == "speechEnd":
        turn = int(raw.get("turnId", state.get("open_turn", 0)))
        return {"kind": "boundary", "phase": "end", "turn": turn}
    if kind == "speechComplete":
        turn = int(raw.get("turnId", state.get("open_turn", 0)))
        done = state.setdefault("completed", [])
        late = bool(done and turn < max(done))
        done.append(turn)
        if state.get("open_turn") == turn:
            state["open_turn"] = 0
        return {"kind": "final", "turn": turn, "text": str(raw.get("transcript", "")), "late": late}
    if kind == "error":
        return {"kind": "error", "message": str(raw.get("message", "voice error")), "transient": False}
    return None
