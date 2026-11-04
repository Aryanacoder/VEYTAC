"""Private, metadata-only provider call receipts for the live demo.

Never store prompts, frame/audio bytes, API keys, raw responses or provider
error bodies here. This is observability, not proof of answer correctness.
"""

from __future__ import annotations

import time
import sqlite3

from veytac.schemas import utcnow_iso

from .db import list_entities, put_entity


def begin_model_call(conn: sqlite3.Connection, session_id: str, call_id: str, *, kind: str,
                     model: str, provider: str, estimated_micro: int = 0) -> None:
    put_entity(conn, "model_call", call_id, session_id, {
        "id": call_id, "kind": kind, "provider": provider,
        "model": model, "status": "running", "started_at": utcnow_iso(),
        "started_perf": time.perf_counter(),
        "estimated_cost_micro": estimated_micro,
    })


def finish_model_call(conn: sqlite3.Connection, session_id: str, call_id: str, *, status: str,
                      usage: dict | None = None, cost_micro: int | None = None) -> None:
    receipt = next((item for item in list_entities(conn, "model_call", session_id)
                    if item["id"] == call_id), None)
    if receipt is None:
        return
    started_perf = receipt.pop("started_perf", None)
    receipt["status"] = status
    receipt["finished_at"] = utcnow_iso()
    receipt["latency_ms"] = max(0, round((time.perf_counter() - started_perf) * 1000)) if started_perf else None
    receipt["usage"] = {key: value for key, value in (usage or {}).items()
                        if key in ("prompt_tokens", "completion_tokens", "total_tokens",
                                   "input_tokens", "output_tokens")
                        and isinstance(value, int) and not isinstance(value, bool) and value >= 0}
    receipt["cost_estimate_micro"] = cost_micro
    put_entity(conn, "model_call", call_id, session_id, receipt)
