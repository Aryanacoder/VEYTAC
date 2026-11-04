"""Baseten lane: open-model inference/training plans (decision 0002).

Plans are local and free. Deployment requires an approval id and the
BASETEN_API_KEY server-side. Scale-to-zero by default; every launch records
stop/delete confirmation or marks cost uncertain (TRD 13.4).
"""

from __future__ import annotations

import os
from typing import Protocol

from veytac.schemas import StrictModel


class BasetenDeployment(StrictModel):
    model_id: str
    instance: str = "trt-llm-a10g"
    min_replicas: int = 0  # scale-to-zero
    max_replicas: int = 1
    purpose: str = ""


class BasetenClient(Protocol):
    def deploy(self, plan: BasetenDeployment) -> str: ...
    def terminate(self, deployment_id: str) -> bool: ...


def plan_deployment(model_id: str, purpose: str) -> BasetenDeployment:
    return BasetenDeployment(model_id=model_id, purpose=purpose)


def launch_deployment(
    plan: BasetenDeployment, client: BasetenClient, *, approval_id: str
) -> dict:
    if not approval_id or not approval_id.startswith("apr_"):
        raise ValueError("launch requires an approval record id (apr_...)")
    deployment_id = client.deploy(plan)
    return {"deployment_id": deployment_id, "approval_id": approval_id,
            "status": "running", "cleanup": "scale-to-zero on idle; terminate on done"}


def require_key() -> str:
    key = os.getenv("BASETEN_API_KEY", "")
    if not key:
        raise RuntimeError("BASETEN_API_KEY is not set (server-side only)")
    return key
