"""Live Meta contract tests. Explicit opt-in only: never run in default CI.

Requires VEYTAC_META_API_KEY + VEYTAC_ALLOW_PAID_CALLS=true + VEYTAC_LIVE_CONTRACT=1.
Each test records endpoint/model/mode/timing/usage and redacts keys.
An unavailable capability is BLOCKED (skip with reason), never fabricated.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.providers.meta import LiveMetaClient, ProviderError  # noqa: E402
from veytac.schemas import ObservationInference  # noqa: E402

LIVE = (
    os.getenv("VEYTAC_LIVE_CONTRACT") == "1"
    and bool(os.getenv("VEYTAC_META_API_KEY"))
    and os.getenv("VEYTAC_ALLOW_PAID_CALLS") == "true"
)

pytestmark = pytest.mark.skipif(not LIVE, reason="live contract needs key + opt-in")


def test_probe_records_capability():
    try:
        out = LiveMetaClient().probe()
    except ProviderError as exc:
        pytest.skip(f"BLOCKED: provider unavailable ({exc})")
    assert out["model"] and out["elapsed_ms"] >= 0
    assert "usage" in out and "rate_card" in out


def test_structured_observation_validates():
    try:
        out = LiveMetaClient().observe(
            window_text='{"note": "contract probe, synthetic window"}',
            task_context="contract probe",
            schema=ObservationInference.model_json_schema(),
        )
    except ProviderError as exc:
        pytest.skip(f"BLOCKED: provider unavailable ({exc})")
    import json

    parsed = json.loads(out["raw_text"])  # must be JSON, else the client is wrong
    assert isinstance(parsed, dict)
    assert out["execution_mode"] == "live"
