"""Knowledge entities: decision records, episodes, lessons, releases, runs (TRD 4.4-4.6)."""

from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from .base import EvidenceRef, StrictModel


class CueOrigin(str, Enum):
    OBSERVED = "observed"
    EXPERT_REPORTED = "expert_reported"
    MEASURED = "measured"
    MODEL_INFERRED = "model_inferred"


class SpeakerRole(str, Enum):
    DEMONSTRATOR = "demonstrator"
    RETROSPECTIVE_REVIEWER = "retrospective_reviewer"
    TRAINER = "trainer"


class ReviewState(str, Enum):
    DRAFT = "draft"
    NEEDS_CLARIFICATION = "needs_clarification"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class OutcomeStatus(str, Enum):
    DESCRIBED = "described"
    OBSERVED = "observed"
    INDEPENDENTLY_TESTED = "independently_tested"
    UNKNOWN = "unknown"


class Cue(StrictModel):
    description: str
    origin: CueOrigin
    evidence_refs: list[EvidenceRef] = []
    value: str | None = None
    unit: str | None = None
    uncertainty: str | None = None


class Alternative(StrictModel):
    description: str
    reason_not_selected: str | None = None
    evidence_refs: list[EvidenceRef] = []


class Applicability(StrictModel):
    scope_description: str
    predicates: list[dict[str, str]] = []
    unresolved_fields: list[str] = []


class ApplicabilityResult(str, Enum):
    APPLIES = "applies"
    NOT_APPLIES = "not_applies"
    UNKNOWN = "unknown"


ALLOWED_PREDICATE_OPS = {"eq", "neq", "in", "lt", "lte", "gt", "gte"}


def evaluate_applicability(app: Applicability, context: dict[str, str]) -> ApplicabilityResult:
    """Limited predicate language only. Unknown inputs -> unknown, never true."""
    if not app.predicates:
        return ApplicabilityResult.UNKNOWN
    verdicts: set[bool] = set()
    for pred in app.predicates:
        field = pred.get("field", "")
        op = pred.get("op", "")
        if op not in ALLOWED_PREDICATE_OPS or field not in context:
            return ApplicabilityResult.UNKNOWN
        want = pred.get("value", "")
        got = context[field]
        if op == "eq":
            verdicts.add(got == want)
        elif op == "neq":
            verdicts.add(got != want)
        elif op == "in":
            verdicts.add(got in want.split(","))
        else:
            try:
                if float(got) == float(got):  # numeric comparison with units declared
                    gv, wv = float(got), float(want)
                    verdicts.add(
                        {"lt": gv < wv, "lte": gv <= wv,
                         "gt": gv > wv, "gte": gv >= wv}[op]
                    )
            except (ValueError, KeyError):
                return ApplicabilityResult.UNKNOWN
    if not verdicts:
        return ApplicabilityResult.UNKNOWN
    return ApplicabilityResult.APPLIES if all(verdicts) else ApplicabilityResult.NOT_APPLIES


class ExceptionCase(StrictModel):
    condition_description: str
    alternative_response: str | None = None
    evidence_refs: list[EvidenceRef] = []


class OutcomeCheck(StrictModel):
    description: str
    status: OutcomeStatus = OutcomeStatus.UNKNOWN
    evidence_refs: list[EvidenceRef] = []


class Review(StrictModel):
    state: ReviewState = ReviewState.DRAFT
    reviewer_id: str | None = None
    reviewed_at: str | None = None
    approved_scope: str | None = None
    supersedes_revision: int | None = None


class DecisionRecord(StrictModel):
    record_id: str
    revision: int = Field(gt=0)
    session_id: str
    decision_interval_start_ms: int
    decision_interval_end_ms: int
    task_id: str
    equipment_or_software_id: str | None = None
    known_conditions: list[str] = []
    unobserved_conditions: list[str] = []
    observed_action_description: str
    observed_action_evidence: list[EvidenceRef] = []
    observation_status: str = "proposed"
    expert_original_language: str = "en"
    expert_original_statement: str
    expert_translated_statement: str | None = None
    speaker_role: SpeakerRole = SpeakerRole.DEMONSTRATOR
    cues: list[Cue] = []
    alternatives: list[Alternative] = []
    applicability: Applicability
    exceptions: list[ExceptionCase] = []
    outcome_checks: list[OutcomeCheck] = []
    review: Review = Review()
    ambiguity_flags: list[str] = []
    unsupported_inferences: list[str] = []
    missing_measurements: list[str] = []

    @model_validator(mode="after")
    def approval_keeps_attribution(self) -> DecisionRecord:
        """Approval must not relabel expert_reported cues as measured."""
        if self.review.state == ReviewState.APPROVED:
            for cue in self.cues:
                if cue.origin == CueOrigin.MEASURED and not cue.evidence_refs:
                    raise ValueError(
                        "measured cues require evidence refs; approval "
                        "cannot convert a report into a measurement"
                    )
        return self


class Capability(str, Enum):
    OBSERVATION = "observation"
    EXPERT_CONTEXT = "expert_context"
    ACTION_ALIGNED = "action_aligned"
    EMBODIMENT_SPECIFIC = "embodiment_specific"


class SkillEpisode(StrictModel):
    schema_version: str = "0.1.0"
    episode_id: str
    revision: int = Field(gt=0)
    title: str
    task_context: str
    capture_manifest: dict[str, str] = {}
    evidence_assets: list[str] = []
    observations: list[str] = []
    dialogue_turns: list[str] = []
    decisions: list[str] = []
    review_summary: str = ""
    permissions: dict[str, bool] = {}
    capabilities: list[Capability] = []
    missing_fields: list[str] = []
    quality_report_ref: str | None = None
    source_manifest_ref: str | None = None
    split_group: str = "train"
    lineage: list[str] = []


class LessonCheckpoint(StrictModel):
    prompt: str
    expected_distinction: str
    explanation: str
    evidence_refs: list[EvidenceRef] = []


class Lesson(StrictModel):
    id: str
    source_episode_id: str
    source_revision: int
    title: str
    task_context: str
    evidence_clip_refs: list[EvidenceRef] = []
    checkpoints: list[LessonCheckpoint] = []
    limitations: list[str] = []
    diagram_provenance: str | None = None  # recorded | illustration | ...


class ReleaseState(str, Enum):
    DRAFT = "draft"
    VALIDATION_PENDING = "validation_pending"
    READY_FOR_PUBLICATION = "ready_for_publication"
    PUBLISHED = "published"
    DELISTED = "delisted"
    FAILED = "failed"


class DatasetRelease(StrictModel):
    id: str
    episode_id: str
    episode_revision: int
    manifest_hash: str
    state: ReleaseState = ReleaseState.DRAFT
    licenses: list[str] = []
    publisher_id: str | None = None
    audience: str = "private"
    published_manifest_hash: str | None = None

    @model_validator(mode="after")
    def publish_pins_manifest(self) -> DatasetRelease:
        if self.state == ReleaseState.PUBLISHED and (
            not self.published_manifest_hash
            or self.published_manifest_hash != self.manifest_hash
        ):
            raise ValueError("publishing requires confirming the exact manifest hash")
        return self


class ExperimentStatus(str, Enum):
    PLANNED = "planned"
    BLOCKED = "blocked"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELED = "canceled"


class ExperimentConclusion(str, Enum):
    NOT_EVALUATED = "not_evaluated"
    INCONCLUSIVE = "inconclusive"
    NO_DETECTED_BENEFIT = "no_detected_benefit"
    POSITIVE_WITHIN_SCOPE = "positive_within_scope"


class ExperimentRun(StrictModel):
    id: str
    kind: str  # transfer_eval | bc_baseline | iql | sft | ...
    status: ExperimentStatus = ExperimentStatus.PLANNED
    conclusion: ExperimentConclusion = ExperimentConclusion.NOT_EVALUATED
    data_hash: str | None = None
    config_hash: str | None = None
    model: str | None = None
    seeds: list[int] = []
    costs_usd: str | None = None
    metrics: dict[str, float] = {}


class AuditEvent(StrictModel):
    event_id: str
    schema_version: str = "0.1.0"
    session_id: str
    sequence_no: int = Field(ge=0)
    event_type: str
    occurred_at: str
    actor_type: str  # human | system | provider
    actor_id: str
    aggregate_id: str
    aggregate_revision: int | None = None
    correlation_id: str = ""
    payload: dict[str, str] = {}
