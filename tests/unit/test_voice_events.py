"""Voice event normalization + relay contract tests (no sockets, no key).

Covers TRD 7.4: partials belong to the latest open turn, speechEnd is a
boundary (not text), speechComplete is the authoritative preserved text,
out-of-order finals are marked late, and the Meta handshake carries the
credential in the first frame (never an HTTP header).
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.voice import MockVoiceRelay, build_handshake, normalize_event  # noqa: E402
from veytac.voice.relay import (  # noqa: E402
    AUDIO_ENCODING, END_STREAM, REALTIME_URL, MetaVoiceRelay, VoiceError,
)


def test_relay_contract_constants():
    assert REALTIME_URL == "wss://api.meta.ai/v1/asr/realtime"
    assert AUDIO_ENCODING == "PCM_24KHZ"
    assert json.loads(END_STREAM) == {"type": "endStream"}


def test_handshake_carries_credential_not_header():
    hs = build_handshake("KEY123", mode="ENDPOINTING", language="en",
                         model="muse-voice-transcribe-1.0")
    assert hs["authorization"] == {"accessToken": "Bearer KEY123"}
    assert hs["audioEncoding"] == AUDIO_ENCODING
    assert hs["mode"] == "ENDPOINTING"
    assert hs["model"] == "muse-voice-transcribe-1.0"
    assert hs["languageBias"] == ["English"]
    assert hs["partialMode"] == "CUMULATIVE"
    assert "sessionId" not in hs
    assert build_handshake("KEY123", language="ja")["languageBias"] == ["Japanese"]
    assert build_handshake("KEY123", language="zh")["languageBias"] == ["Mandarin Chinese"]


def test_relay_sends_documented_handshake_and_wraps_disconnect(monkeypatch):
    import websockets

    class FakeSocket:
        sent: list[str | bytes] = []

        async def send(self, data):
            if isinstance(data, bytes):
                raise RuntimeError("provider closed")
            self.sent.append(data)

        async def recv(self):
            return json.dumps({"sessionId": "provider-session"})

        async def close(self):
            return None

    socket = FakeSocket()
    urls = []

    async def fake_connect(url, **_kwargs):
        urls.append(url)
        return socket

    monkeypatch.setenv("VEYTAC_ALLOW_PAID_CALLS", "true")
    monkeypatch.setattr(websockets, "connect", fake_connect)
    relay = MetaVoiceRelay(api_key="TEST_ONLY", language="ja", session_id="veytac session")
    assert asyncio.run(relay.connect())["sessionId"] == "provider-session"
    assert urls == [f"{REALTIME_URL}?sessionId=veytac%20session"]
    handshake = json.loads(socket.sent[0])
    assert handshake["languageBias"] == ["Japanese"]
    assert "sessionId" not in handshake
    with pytest.raises(VoiceError, match="disconnected during audio"):
        asyncio.run(relay.send_audio(b"\x00" * 3840))
    asyncio.run(relay.finish_input())
    assert json.loads(socket.sent[-1]) == {"type": "endStream"}


def test_partial_belongs_to_open_turn_and_final_is_authoritative():
    state: dict = {}
    assert normalize_event({"type": "speechStart", "turnId": 7}, state) == {
        "kind": "boundary", "phase": "start", "turn": 7}
    assert normalize_event(
        {"type": "transcript", "transcript": "how is", "final": False}, state) == {
        "kind": "partial", "turn": 7, "text": "how is"}
    # boundary marks the edge; it is not text
    assert normalize_event({"type": "speechEnd", "turnId": 7}, state)["kind"] == "boundary"
    final = normalize_event(
        {"type": "speechComplete", "turnId": 7, "transcript": "How is it?"}, state)
    assert final == {"kind": "final", "turn": 7, "text": "How is it?", "late": False}


def test_unattributable_partial_dropped_and_speaker_labeled():
    state: dict = {}
    assert normalize_event(
        {"type": "transcript", "transcript": "orphan", "final": False}, state) is None
    state["open_turn"] = 3
    assert normalize_event({"type": "speaker", "label": "A"}, state) == {
        "kind": "speaker", "turn": 3, "label": "A"}


def test_late_final_flagged_not_merged():
    state: dict = {}
    normalize_event({"type": "speechComplete", "turnId": 1, "transcript": "First."}, state)
    normalize_event({"type": "speechComplete", "turnId": 2, "transcript": "Second."}, state)
    late = normalize_event({"type": "speechComplete", "turnId": 1, "transcript": "First?"}, state)
    assert late["late"] is True
    assert late["turn"] == 1  # stays with its own turn


def test_error_passthrough():
    evt = normalize_event({"type": "error", "message": "boom"}, {})
    assert evt is not None and evt["kind"] == "error"


def _drive(coro):
    """Run a coroutine to completion without an event loop.

    Valid only because MockVoiceRelay performs no real I/O: every await
    resolves synchronously. A coroutine that actually blocked would raise
    here instead of hanging.
    """
    try:
        coro.send(None)
    except StopIteration as done:
        return done.value
    raise AssertionError("coroutine needs a real event loop (unexpected I/O)")


def test_mock_relay_script_and_label():
    relay = MockVoiceRelay()
    assert relay.execution_mode == "mock"
    ack = _drive(relay.connect())
    assert ack["execution_mode"] == "mock"
    _drive(relay.send_audio(b"\x00" * 480))
    seen = []
    for _ in range(6):
        evt = _drive(relay.recv())
        if evt is None:
            break
        seen.append(evt["type"])
    _drive(relay.finish_input())
    _drive(relay.close())
    assert relay.finished is True
    assert seen == ["speechStart", "transcript", "speechEnd", "speechComplete"]
