"""Canonical Pydantic contracts for VEYTAC (TRD section 4).

These models are the single source of truth for API payloads, database
records, and export bundles. JSON Schema and TypeScript types are generated
from them; no contract is invented separately on the frontend.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

SCHEMA_VERSION = "0.1.0"

FiniteFloat = Annotated[float, Field(strict=False)]


def make_id(prefix: str) -> str:
    """Opaque server-created ID, e.g. ses_<32 hex chars>."""
    return f"{prefix}_{uuid.uuid4().hex}"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrictModel(BaseModel):
    model_config = {"extra": "forbid", "use_enum_values": True}


class Role(str, Enum):
    OWNER = "owner"
    EXPERT = "expert"
    REVIEWER = "reviewer"
    LEARNER = "learner"
    DEVELOPER = "developer"


class SessionMode(str, Enum):
    LIVE_CAPTURE = "LIVE_CAPTURE"
    RECORDED_REPLAY = "RECORDED_REPLAY"
    SIMULATED = "SIMULATED"


class SessionLifecycle(str, Enum):
    CREATED = "created"
    CONSENT_PENDING = "consent_pending"
    READY = "ready"
    CAPTURING = "capturing"
    PAUSED = "paused"
    FINALIZING = "finalizing"
    REVIEW = "review"
    CLOSED = "closed"
    FAILED = "failed"
    DELETION_REQUESTED = "deletion_requested"
    DELETED = "deleted"


class ConsentPurpose(str, Enum):
    CAPTURE = "capture"
    EXTERNAL_INFERENCE = "external_inference"
    INTERNAL_REVIEW = "internal_review"
    TRAINING = "training"
    INTERNAL_SHARING = "internal_sharing"
    PUBLIC_DISTRIBUTION = "public_distribution"


class EvidenceKind(str, Enum):
    TIME_RANGE = "time_range"
    DOCUMENT_PAGE = "document_page"
    AUDIO_SPAN = "audio_span"


class EvidenceRelationship(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXT_ONLY = "context_only"


class Locator(StrictModel):
    kind: EvidenceKind
    clock_id: str | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    page: int | None = None
    region_xyxy_normalized: list[float] | None = None
    line_start: int | None = None
    line_end: int | None = None

    @model_validator(mode="after")
    def check_kind_fields(self) -> Locator:
        if self.kind in (EvidenceKind.TIME_RANGE, EvidenceKind.AUDIO_SPAN):
            if self.start_ms is None or self.end_ms is None:
                raise ValueError(f"{self.kind} locator requires start_ms and end_ms")
            if self.end_ms < self.start_ms:
                raise ValueError("end_ms must be >= start_ms")
            if self.clock_id is None:
                raise ValueError(f"{self.kind} locator requires clock_id")
        if self.kind == EvidenceKind.DOCUMENT_PAGE and self.page is None:
            raise ValueError("document_page locator requires page")
        box = self.region_xyxy_normalized
        if box is not None:
            if len(box) != 4 or not all(0.0 <= v <= 1.0 for v in box):
                raise ValueError("region box must be 4 normalized values in [0,1]")
            x1, y1, x2, y2 = box
            if not (x2 > x1 and y2 > y1):
                raise ValueError("region box requires x2>x1 and y2>y1")
        return self


class EvidenceRef(StrictModel):
    asset_id: str
    revision: int = Field(gt=0)
    locator: Locator
    relationship: EvidenceRelationship = EvidenceRelationship.SUPPORTS
    alignment_uncertainty_ms: int | None = Field(default=None, ge=0)
