"""Voice relay: browser mic -> VEYTAC backend -> Meta live ASR (TRD 7.4).

Provider contract (Meta speech-to-text docs + realtime API reference):
- Connect ``wss://api.meta.ai/v1/asr/realtime`` (optional ``?sessionId=``).
- First frame (within 10 s) is a JSON handshake carrying the credential:
  ``{"authorization": {"accessToken": "Bearer KEY"}, "audioEncoding":
  "PCM_24KHZ", "model": "muse-voice-transcribe-1.0", "mode": "ENDPOINTING", ...}``. Never an HTTP header, and the
  key never leaves the server.
- Audio goes as raw binary frames: 16-bit little-endian mono PCM at 24 kHz,
  paced near real time (~80 ms per frame).
- The only other client text frame is the ``endStream`` marker.
- Server replies: handshake ack (has ``sessionId``), then ordered events;
  socket closes with 1000 when done.

``MetaVoiceRelay`` implements this. ``MockVoiceRelay`` replays a scripted
event list for deterministic tests and keyless rehearsal; everything it
emits carries ``execution_mode=mock``.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from urllib.parse import quote

REALTIME_URL = "wss://api.meta.ai/v1/asr/realtime"
AUDIO_ENCODING = "PCM_24KHZ"
SAMPLE_RATE = 24000
FRAME_MS = 80
END_STREAM = json.dumps({"type": "endStream"})
LANGUAGE_BIAS = {"en": "English", "ja": "Japanese", "zh": "Mandarin Chinese"}


class VoiceError(Exception):
    def __init__(self, message: str, *, transient: bool = False) -> None:
        super().__init__(message)
        self.transient = transient


def build_handshake(api_key: str, *, mode: str = "ENDPOINTING",
                    language: str = "en", model: str | None = None) -> dict:
    handshake: dict = {
        "authorization": {"accessToken": f"Bearer {api_key}"},
        "audioEncoding": AUDIO_ENCODING,
        "model": model or os.getenv("VEYTAC_MODEL_ASR", "muse-voice-transcribe-1.0"),
        "mode": mode,
        "partialMode": "CUMULATIVE",
        "languageBias": [LANGUAGE_BIAS.get(language, language)],
    }
    return handshake


class VoiceRelay:
    """Transport interface both relays implement (sync-friendly for tests)."""

    execution_mode = "live"

    async def connect(self) -> dict:
        raise NotImplementedError

    async def send_audio(self, pcm: bytes) -> None:
        raise NotImplementedError

    async def recv(self) -> dict | None:
        raise NotImplementedError

    async def finish_input(self) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


class MetaVoiceRelay(VoiceRelay):
    def __init__(self, *, api_key: str = "", mode: str = "ENDPOINTING",
                 language: str = "en", session_id: str | None = None) -> None:
        key = api_key or os.getenv("VEYTAC_META_API_KEY", "")
        if not key:
            raise VoiceError("VEYTAC_META_API_KEY is not set", transient=False)
        if os.getenv("VEYTAC_ALLOW_PAID_CALLS", "false") != "true":
            raise VoiceError("paid calls are disabled (VEYTAC_ALLOW_PAID_CALLS)", transient=False)
        self._handshake = build_handshake(key, mode=mode, language=language)
        self._session_id = session_id
        self._ws = None
        self.started_ms = 0

    async def connect(self) -> dict:
        import websockets

        url = REALTIME_URL
        sid = self._session_id
        if sid:
            url += f"?sessionId={quote(sid, safe='')}"
        try:
            self._ws = await websockets.connect(url, max_size=4 * 1024 * 1024)
            await self._ws.send(json.dumps(self._handshake))
            raw = await asyncio.wait_for(self._ws.recv(), timeout=5)
        except Exception as exc:
            await self.close()
            raise VoiceError(f"voice connect failed: {exc}", transient=True) from exc
        try:
            ack = json.loads(raw) if isinstance(raw, str) else {}
        except ValueError as exc:
            await self.close()
            raise VoiceError("voice provider sent an invalid handshake", transient=False) from exc
        if "sessionId" not in ack:
            await self.close()
            raise VoiceError("voice provider rejected the handshake", transient=False)
        self.started_ms = int(time.time() * 1000)
        return ack

    async def send_audio(self, pcm: bytes) -> None:
        if not self._ws:
            raise VoiceError("relay not connected", transient=False)
        try:
            await self._ws.send(pcm)
        except Exception as exc:
            raise VoiceError(f"voice provider disconnected during audio ({type(exc).__name__})",
                             transient=True) from exc

    async def recv(self) -> dict | None:
        if not self._ws:
            return None
        try:
            raw = await self._ws.recv()
        except Exception as exc:
            raise VoiceError(f"voice provider disconnected ({type(exc).__name__})",
                             transient=True) from exc
        if isinstance(raw, bytes):
            return None  # server events are text frames; ignore binary
        try:
            evt = json.loads(raw)
        except ValueError as exc:
            raise VoiceError("voice provider sent invalid event JSON", transient=False) from exc
        if evt.get("type") == "error":
            raise VoiceError(str(evt.get("message", "voice error")), transient=False)
        return evt

    async def finish_input(self) -> None:
        if self._ws:
            try:
                await self._ws.send(END_STREAM)
            except Exception as exc:
                raise VoiceError(f"voice provider disconnected at end of input ({type(exc).__name__})",
                                 transient=True) from exc

    async def close(self) -> None:
        ws, self._ws = self._ws, None
        if ws:
            try:
                await ws.close()
            except Exception:
                pass


class MockVoiceRelay(VoiceRelay):
    """Deterministic scripted relay. Labeled mock, never billed, never live."""

    execution_mode = "mock"

    def __init__(self, script: list[dict] | None = None) -> None:
        self._script = list(script or [
            {"type": "speechStart", "turnId": 1},
            {"type": "transcript", "transcript": "mock rehearsal turn", "final": False},
            {"type": "speechEnd", "turnId": 1},
            {"type": "speechComplete", "turnId": 1, "transcript": "Mock rehearsal turn."},
        ])
        self.audio_bytes = 0
        self.finished = False

    async def connect(self) -> dict:
        return {"sessionId": "mock-voice-session", "execution_mode": "mock"}

    async def send_audio(self, pcm: bytes) -> None:
        self.audio_bytes += len(pcm)

    async def recv(self) -> dict | None:
        if not self._script:
            return None
        return self._script.pop(0)

    async def finish_input(self) -> None:
        self.finished = True

    async def close(self) -> None:
        return None
