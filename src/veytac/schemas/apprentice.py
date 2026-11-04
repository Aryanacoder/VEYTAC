"""Apprentice-loop entities: observations, gaps, questions, dialogue (TRD 4.2, 5.2, 6)."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import EvidenceRef, StrictModel


class ObservationStatus(str, Enum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    UNRESOLVED = "unresolved"


class Observation(StrictModel):
    id: str
    session_id: str
    window_start_ms: int
    window_end_ms: int
    description: str = Field(max_length=2000)
    objects: list[str] = []
    candidate_action: str | None = None
    observation_status: ObservationStatus = ObservationStatus.PROPOSED
    uncertainty: str = ""
    unavailable_cues: list[str] = []
    evidence_refs: list[EvidenceRef] = []
    model: str = ""
    prompt_version: str = ""
    schema_version: str = "0.1.0"


class ObservationInference(StrictModel):
    """Only visual claims the provider may return; IDs and evidence are server-owned."""

    description: str = Field(max_length=2000)
    objects: list[str] = []
    candidate_action: str | None = None
    uncertainty: str = ""
    unavailable_cues: list[str] = []


class GapState(str, Enum):
    OPEN = "open"
    ASKED = "asked"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class KnowledgeGap(StrictModel):
    id: str
    session_id: str
    observation_ids: list[str] = []
    competing_interpretations: list[str] = []
    missing_fact: str
    consequence: str = ""
    domain_scope: str = "general"
    state: GapState = GapState.OPEN


class QuestionType(str, Enum):
    CLARIFY_OBSERVATION = "clarify_observation"
    HIDDEN_CUE = "hidden_cue"
    DECISION_BOUNDARY = "decision_boundary"
    ALTERNATIVE = "alternative"
    EXCEPTION = "exception"
    VERIFICATION = "verification"


class QuestionState(str, Enum):
    CANDIDATE = "candidate"
    QUEUED = "queued"
    DELIVERED = "delivered"
    ANSWERING = "answering"
    ANSWERED = "answered"
    INCORPORATED = "incorporated"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    SKIPPED = "skipped"
    EXPIRED = "expired"
    NEEDS_CLARIFICATION = "needs_clarification"


class Question(StrictModel):
    id: str
    session_id: str
    gap_id: str
    wording: str
    language: str = "en"
    question_type: QuestionType = QuestionType.CLARIFY_OBSERVATION
    state: QuestionState = QuestionState.CANDIDATE
    rank_score: float | None = None
    rank_features: dict[str, float] = {}
    rank_reason: str = ""
    evidence_refs: list[EvidenceRef] = []
    superseded_reason: str | None = None


def rank_score(task_relevance: float, divergence: float, consequence: float,
               novelty: float, burden: float) -> float:
    """TRD 6.2 heuristic. Inputs normalized to [0,1]; heuristic, not calibrated."""
    for v in (task_relevance, divergence, consequence, novelty, burden):
        if not 0.0 <= v <= 1.0:
            raise ValueError("rank features must be in [0,1]")
    return (
        0.35 * task_relevance
        + 0.30 * divergence
        + 0.20 * consequence
        + 0.15 * novelty
        - 0.30 * burden
    )


class DialogueTurn(StrictModel):
    id: str
    session_id: str
    question_id: str
    speaker: str = "expert"  # expert | reviewer | system
    original_language: str = "en"
    original_text: str
    translated_text: str | None = None
    audio_asset_id: str | None = None
    status: str = "final"  # final | partial
    correction_history: list[str] = []
