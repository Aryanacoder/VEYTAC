"""Partner-lane tests: no leakage, no approval → no launch."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.learning import serve  # noqa: E402
from veytac.learning import sft  # noqa: E402
from veytac.schemas import Applicability, DecisionRecord  # noqa: E402


def _rec(session: str, rid: str) -> DecisionRecord:
    return DecisionRecord(
        record_id=rid, revision=1, session_id=session,
        decision_interval_start_ms=0, decision_interval_end_ms=1,
        task_id="t", observed_action_description="a",
        expert_original_statement="s",
        applicability=Applicability(scope_description="x"),
    )


def test_split_keeps_sessions_together():
    examples = [sft.example_from_decision(_rec("s1", f"d{i}"), "o") for i in range(4)]
    examples += [sft.example_from_decision(_rec("s2", "d9"), "o")]
    split = sft.split_by_session(examples, val_frac=0.5)
    by_session: dict[str, set[str]] = {}
    for e in split:
        by_session.setdefault(e.session_id, set()).add(e.split)
    assert all(len(v) == 1 for v in by_session.values())


def test_launch_requires_approval_and_data():
    cfg = sft.GlimmerLoRAConfig()

    class Fake:
        def upload_dataset(self, name, jsonl):
            return "ds_1"

        def create_lora_job(self, dataset_id, config):
            return "job_1"

    plan = sft.plan_sft([], cfg, job_name="j")
    with pytest.raises(ValueError):
        sft.launch_sft(plan, [], cfg, Fake(), approval_id="magic")
    with pytest.raises(ValueError):
        sft.launch_sft(plan, [], cfg, Fake(), approval_id="apr_123")  # empty data

    examples = [sft.example_from_decision(_rec("s1", "d1"), "o"),
                sft.example_from_decision(_rec("s2", "d2"), "o")]
    plan = sft.plan_sft(examples, cfg, job_name="j")
    out = sft.launch_sft(plan, examples, cfg, Fake(), approval_id="apr_123")
    assert out["status"] == "running" and out["job_id"] == "job_1"


def test_baseten_plan_free_launch_gated():
    plan = serve.plan_deployment("meta-llama/Llama-3.1-8B", "rehearsal inference")
    assert plan.min_replicas == 0  # scale-to-zero default

    class Fake:
        def deploy(self, plan):
            return "dep_1"

        def terminate(self, deployment_id):
            return True

    with pytest.raises(ValueError):
        serve.launch_deployment(plan, Fake(), approval_id="nope")
    out = serve.launch_deployment(plan, Fake(), approval_id="apr_9")
    assert out["deployment_id"] == "dep_1"
