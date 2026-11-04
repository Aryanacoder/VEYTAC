"""Export canonical JSON Schemas for API + TypeScript generation."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from veytac.schemas import (  # noqa: E402
    AuditEvent,
    ConsentGrant,
    DatasetRelease,
    DecisionRecord,
    DialogueTurn,
    EvidenceAsset,
    EvidenceRef,
    ExperimentRun,
    KnowledgeGap,
    Lesson,
    MediaChunk,
    MediaStream,
    Observation,
    Principal,
    Question,
    Session,
    SkillEpisode,
)

MODELS = {
    "principal": Principal,
    "consent_grant": ConsentGrant,
    "session": Session,
    "media_stream": MediaStream,
    "media_chunk": MediaChunk,
    "evidence_asset": EvidenceAsset,
    "evidence_ref": EvidenceRef,
    "observation": Observation,
    "knowledge_gap": KnowledgeGap,
    "question": Question,
    "dialogue_turn": DialogueTurn,
    "decision_record": DecisionRecord,
    "skill_episode": SkillEpisode,
    "lesson": Lesson,
    "dataset_release": DatasetRelease,
    "experiment_run": ExperimentRun,
    "audit_event": AuditEvent,
}

out_dir = Path(__file__).resolve().parents[1] / "schemas" / "json"
out_dir.mkdir(parents=True, exist_ok=True)
for name, model in MODELS.items():
    (out_dir / f"{name}.schema.json").write_text(
        json.dumps(model.model_json_schema(), indent=2) + "\n"
    )
print(f"wrote {len(MODELS)} schemas to {out_dir}")
