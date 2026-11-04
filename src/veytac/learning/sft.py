"""Glimmer SFT via Fireworks LoRA (FR-22, TRD 12.1). Stage 2.

Target behavior: grounded question selection / faithful decision-record
extraction from reviewed episodes. Splits preserve session groups (no
leakage). Launch requires an explicit approval id; dry-run never touches the
network. Unlimited partner budget (decision 0002) still means every launch
is logged as an ExperimentRun with data/config hashes.
"""

from __future__ import annotations

import hashlib
import os
from typing import Protocol

from veytac.schemas import DecisionRecord, StrictModel


class SFTExample(StrictModel):
    input_text: str
    output_json: str  # schema-validated decision record or question
    session_id: str
    split: str = "train"  # train | validation | test


class GlimmerLoRAConfig(StrictModel):
    base_model: str = "accounts/fireworks/models/muse-glimmer"
    lora_rank: int = 8
    epochs: int = 1
    learning_rate: float = 0.0001
    max_seq_len: int = 2048


def example_from_decision(rec: DecisionRecord, observation_text: str) -> SFTExample:
    """One training example: observation window → approved record extraction."""
    return SFTExample(
        input_text=(
            "Extract the reviewed decision record for this observation window.\n"
            f"Task: {rec.task_id}\nObservation: {observation_text}\n"
            f"Expert ({rec.expert_original_language}): {rec.expert_original_statement}"
        ),
        output_json=rec.model_dump_json(),
        session_id=rec.session_id,
    )


def split_by_session(
    examples: list[SFTExample], *, val_frac: float = 0.2
) -> list[SFTExample]:
    """Group-preserving split: a session never spans train/validation."""
    sessions = sorted({e.session_id for e in examples})
    n_val = max(1, round(len(sessions) * val_frac)) if sessions else 0
    val = set(sessions[:n_val])
    return [
        e.model_copy(update={"split": "validation" if e.session_id in val else "train"})
        for e in examples
    ]


def dataset_jsonl(examples: list[SFTExample]) -> str:
    return "\n".join(e.model_dump_json() for e in examples) + "\n"


def dataset_hash(examples: list[SFTExample]) -> str:
    return hashlib.sha256(dataset_jsonl(examples).encode()).hexdigest()


class FireworksClient(Protocol):
    def upload_dataset(self, name: str, jsonl: str) -> str: ...
    def create_lora_job(self, dataset_id: str, config: GlimmerLoRAConfig) -> str: ...


class LiveFireworksClient:
    """Real HTTP client. Reads FIREWORKS_API_KEY from the server environment."""

    def __init__(self, base_url: str = "https://api.fireworks.ai") -> None:
        import httpx

        key = os.getenv("FIREWORKS_API_KEY", "")
        if not key:
            raise RuntimeError("FIREWORKS_API_KEY is not set (server-side only)")
        self._http = httpx.Client(base_url=base_url,
                                  headers={"Authorization": f"Bearer {key}"})

    def upload_dataset(self, name: str, jsonl: str) -> str:
        res = self._http.post("/v1/datasets", json={"name": name, "data": jsonl})
        res.raise_for_status()
        return str(res.json()["id"])

    def create_lora_job(self, dataset_id: str, config: GlimmerLoRAConfig) -> str:
        res = self._http.post("/v1/supervised_fine_tuning/jobs", json={
            "dataset_id": dataset_id, **config.model_dump(),
        })
        res.raise_for_status()
        return str(res.json()["id"])


def plan_sft(
    examples: list[SFTExample], config: GlimmerLoRAConfig, *, job_name: str
) -> dict:
    split = split_by_session(examples)
    return {
        "job_name": job_name,
        "base_model": config.base_model,
        "n_train": sum(1 for e in split if e.split == "train"),
        "n_validation": sum(1 for e in split if e.split == "validation"),
        "data_hash": dataset_hash(split),
        "config": config.model_dump(),
        "status": "planned",
    }


def launch_sft(
    plan: dict,
    examples: list[SFTExample],
    config: GlimmerLoRAConfig,
    client: FireworksClient,
    *,
    approval_id: str,
) -> dict:
    """Paid launch. Requires a real approval id, never a magic string."""
    if not approval_id or not approval_id.startswith("apr_"):
        raise ValueError("launch requires an approval record id (apr_...)")
    if plan.get("status") != "planned":
        raise ValueError("plan is not in planned state")
    if plan.get("n_train", 0) < 1:
        raise ValueError("no training examples: refusing empty launch")
    jsonl = dataset_jsonl(split_by_session(examples))
    dataset_id = client.upload_dataset(plan["job_name"], jsonl)
    job_id = client.create_lora_job(dataset_id, config)
    return {**plan, "status": "running", "approval_id": approval_id,
            "dataset_id": dataset_id, "job_id": job_id}
