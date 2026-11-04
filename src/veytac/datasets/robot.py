"""Source registry and robot-alignment gate (TRD 10.1, 10.4, FR-18/32).

Stage 2 workstream. Unknown rights mean denied. Phone-only episodes can never
pass the action-alignment gate: zeros or inferred joints are rejected, never
filled in.
"""

from __future__ import annotations

from veytac.schemas import SkillEpisode, StrictModel


class SourceRecord(StrictModel):
    id: str
    origin: str  # URL or owner description
    version: str
    checksum: str | None = None
    modalities: list[str] = []
    process_ok: bool = False
    train_ok: bool = False
    redistribute_ok: bool = False
    attribution: str = ""
    split_group: str = "train"


def check_use(source: SourceRecord, purpose: str) -> tuple[bool, str]:
    """purpose in processing | training | redistribution."""
    flag = {"processing": source.process_ok, "training": source.train_ok,
            "redistribution": source.redistribute_ok}.get(purpose)
    if flag is None:
        return False, f"unknown purpose {purpose}"
    if not flag:
        return False, f"{purpose} not permitted for source {source.id}"
    return True, "permitted"


REQUIRED_ROBOT_FIELDS = [
    "embodiment_id", "task_version", "observation_keys", "action_keys",
    "units", "coordinate_frames", "action_type", "control_rate_hz",
    "termination", "reward_provenance",
]


def validate_robot_bundle(episode: SkillEpisode, robot_meta: dict) -> tuple[bool, list[str]]:
    """Action-alignment gate. Returns (accepted, reasons)."""
    reasons: list[str] = []
    if "action_aligned" not in list(episode.capabilities):
        reasons.append("episode lacks action_aligned capability")
    missing = [f for f in REQUIRED_ROBOT_FIELDS if f not in robot_meta]
    if missing:
        reasons.append(f"missing robot metadata: {sorted(missing)}")
    for key in ("action_keys", "observation_keys"):
        if key in robot_meta and not robot_meta[key]:
            reasons.append(f"{key} is empty: no actions may be invented")
    placeholders = [k for k, v in robot_meta.items()
                    if isinstance(v, (list, str)) and len(v) == 0 and k in REQUIRED_ROBOT_FIELDS]
    if placeholders:
        reasons.append(f"placeholder fields present as data: {placeholders}")
    return (len(reasons) == 0, reasons)
