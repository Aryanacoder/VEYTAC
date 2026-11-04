"""Provider protocols and deterministic mock adapters (TRD 7)."""

from __future__ import annotations

from typing import AsyncIterator, Protocol


class ObservationProvider(Protocol):
    async def observe(self, request: dict) -> dict: ...


class QuestionProvider(Protocol):
    async def propose_questions(self, request: dict) -> dict: ...


class SpeechProvider(Protocol):
    async def transcribe_stream(
        self, audio: AsyncIterator[dict]
    ) -> AsyncIterator[dict]: ...


def observe_plan(request: dict) -> dict:
    """Sync deterministic core for mock observation."""
    from veytac.schemas import make_id

    window = f"{request['window_start_ms']}-{request['window_end_ms']}"
    return {
        "execution_mode": "mock",
        "model": "mock-observer-0",
        "prompt_version": "mock-1",
        "observation": {
            "id": make_id("obs"),
            "session_id": request["session_id"],
            "window_start_ms": request["window_start_ms"],
            "window_end_ms": request["window_end_ms"],
            "description": f"mock observation for window {window}",
            "objects": [],
            "candidate_action": None,
            "observation_status": "proposed",
            "uncertainty": "mock fixture; no real perception",
            "unavailable_cues": ["all physical quantities"],
            "evidence_refs": [],
            "model": "mock-observer-0",
            "prompt_version": "mock-1",
        },
    }


def question_plan(request: dict) -> dict:
    """Sync deterministic core for mock question proposals."""
    from veytac.schemas import make_id

    gaps = request.get("gaps", [])
    asked = set(request.get("asked_targets", []))
    fresh = [g for g in gaps if g["id"] not in asked and g["state"] == "open"]
    if not fresh:
        return {
            "execution_mode": "mock",
            "questions": [],
            "no_question_reason": "no open unasked gaps",
        }
    gap = fresh[0]
    return {
        "execution_mode": "mock",
        "no_question_reason": None,
        "questions": [
            {
                "id": make_id("q"),
                "session_id": request["session_id"],
                "gap_id": gap["id"],
                "wording": f"mock question about: {gap['missing_fact']}",
                "language": "en",
                "question_type": "clarify_observation",
                "state": "candidate",
                "evidence_refs": [],
            }
        ],
    }


class MockObservationProvider:
    """Deterministic fixture: reports exactly what the manifest lists."""

    async def observe(self, request: dict) -> dict:
        return observe_plan(request)


class MockQuestionProvider:
    """One deterministic candidate per open gap, or no_question."""

    async def propose_questions(self, request: dict) -> dict:
        return question_plan(request)


class MockSpeechProvider:
    async def transcribe_stream(
        self, audio: AsyncIterator[dict]
    ) -> AsyncIterator[dict]:
        async for chunk in audio:
            yield {
                "kind": "final",
                "text": f"mock transcript of chunk {chunk.get('sequence_no')}",
                "language": "en",
            }
