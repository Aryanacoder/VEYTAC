"""Stage-2 gate tests: rights default deny, phone-only fails robot gate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.datasets.robot import (  # noqa: E402
    SourceRecord,
    check_use,
    validate_robot_bundle,
)
from veytac.schemas import SkillEpisode  # noqa: E402


def _episode() -> SkillEpisode:
    return SkillEpisode(
        episode_id="ep_1",
        revision=1,
        title="t",
        task_context="t",
        capabilities=["observation", "expert_context"],  # type: ignore[list-item]
        missing_fields=["action_aligned"],
    )


def test_unknown_rights_deny():
    src = SourceRecord(id="s1", origin="example", version="v0")
    ok, _ = check_use(src, "training")
    assert not ok


def test_phone_only_episode_fails_robot_gate():
    accepted, reasons = validate_robot_bundle(_episode(), {})
    assert not accepted
    assert any("action_aligned" in r for r in reasons)


def test_empty_action_keys_rejected_not_filled():
    ep = _episode()
    ep.capabilities = ["observation", "expert_context", "action_aligned"]  # type: ignore[list-item]
    accepted, reasons = validate_robot_bundle(ep, {
        "embodiment_id": "e", "task_version": "v", "observation_keys": ["q"],
        "action_keys": [], "units": "SI", "coordinate_frames": "base",
        "action_type": "delta", "control_rate_hz": 20,
        "termination": "success-flag", "reward_provenance": "env",
    })
    assert not accepted
    assert any("action_keys" in r for r in reasons)
