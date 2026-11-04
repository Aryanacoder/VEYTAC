"""Session, consent, stream, and asset entities (TRD 4.2, 5.1)."""

from __future__ import annotations

from .base import (
    ConsentPurpose,
    EvidenceRef,
    Role,
    SessionLifecycle,
    SessionMode,
    StrictModel,
    utcnow_iso,
)


class Principal(StrictModel):
    id: str
    workspace_id: str
    role: Role
    auth_provenance: str


class ConsentGrant(StrictModel):
    id: str
    actor_id: str
    session_id: str
    purpose: ConsentPurpose
    granted_at: str | None = None
    revoked_at: str | None = None
    notice_version: str = "1"
    notice_hash: str
    scope: str = ""


class Session(StrictModel):
    id: str
    owner_id: str
    workspace_id: str
    task_id: str
    domain: str = "general"
    languages: list[str] = ["en"]
    mode: SessionMode = SessionMode.LIVE_CAPTURE
    lifecycle: SessionLifecycle = SessionLifecycle.CREATED
    created_at: str = ""
    capture_granted: bool = False
    processing_granted: bool = False
    sharing_granted: bool = False
    training_granted: bool = False
    questions_allowed: bool = False
    budget_cap_usd: str = "3.00"


class MediaStream(StrictModel):
    id: str
    session_id: str
    source_type: str  # camera | microphone | screen | upload
    epoch_id: str
    clock_id: str
    codec: str = ""
    status: str = "active"


class MediaChunk(StrictModel):
    session_id: str
    stream_id: str
    epoch_id: str
    sequence_no: int
    interval_start_ms: int | None = None
    interval_end_ms: int | None = None
    mime: str
    codec: str = ""
    sha256: str
    size_bytes: int
    capture_mode: str = "live"


class EvidenceAsset(StrictModel):
    id: str
    session_id: str
    origin: str  # recorded | uploaded | derived | external_reference
    sha256: str
    media_type: str
    rights: str = "private"
    derivation_lineage: list[str] = []
    available: bool = True
    evidence: EvidenceRef | None = None


def new_session(owner: Principal, task_id: str, **kwargs) -> Session:
    from .base import make_id

    return Session(
        id=make_id("ses"),
        owner_id=owner.id,
        workspace_id=owner.workspace_id,
        task_id=task_id,
        created_at=utcnow_iso(),
        **kwargs,
    )
