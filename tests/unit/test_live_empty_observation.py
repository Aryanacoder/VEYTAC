"""A reasoning-only live response must be charged, labeled, and stopped."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services"))

from api import routers_capture  # noqa: E402
from api.db import connect, get_session, insert_session, list_entities  # noqa: E402
from veytac.providers import meta  # noqa: E402


def test_reasoning_only_response_is_explicit_failure(monkeypatch):
    conn = connect(":memory:")
    session_id = "ses_empty_provider"
    payload = {"budget_cap_usd": "3.00"}
    insert_session(conn, session_id, payload)
    monkeypatch.setattr(routers_capture, "db", lambda: conn)

    class EmptyClient:
        def observe(self, **kwargs):
            return {
                "model": "muse-spark-1.3", "raw_text": None,
                "finish_reason": "length",
                "usage": {"completion_tokens": meta.OBSERVATION_OUTPUT_TOKENS},
            }

    monkeypatch.setattr(meta, "LiveMetaClient", EmptyClient)
    result = routers_capture._live_observe(
        session_id, payload, "ast_test",
        routers_capture.FrameBody(at_ms=1000), 1000,
    )
    assert result["status"] == "failed"
    assert result["findings"][0]["code"] == "PROVIDER_EMPTY"
    assert "finish_reason=length" in result["findings"][0]["message"]
    assert get_session(conn, session_id)["budget"]["spent_micro"] == meta.OBSERVATION_OUTPUT_TOKENS * 12
    calls = list_entities(conn, "model_call", session_id)
    assert len(calls) == 1
    assert calls[0]["status"] == "completed"
    assert calls[0]["kind"] == "observation"
    assert calls[0]["usage"]["completion_tokens"] == meta.OBSERVATION_OUTPUT_TOKENS
    assert "raw_text" not in calls[0]
