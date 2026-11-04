"""Phone speech telemetry stores status, never speech content."""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services"))

from api import routers_voice  # noqa: E402
from api.db import connect, insert_session, list_entities  # noqa: E402


def test_diagnostic_accepts_only_bounded_event(monkeypatch):
    conn = connect(":memory:")
    insert_session(conn, "ses_voice", {"id": "ses_voice"})
    monkeypatch.setattr(routers_voice, "db", lambda: conn)
    body = routers_voice.InteractionDiagnostic(event="asr_relay_ready")
    assert routers_voice.record_interaction_diagnostic("ses_voice", body) == {"accepted": True}
    stored = list_entities(conn, "interaction_diagnostic", "ses_voice")
    assert len(stored) == 1
    assert set(stored[0]) == {"id", "event", "at"}
    with pytest.raises(ValidationError):
        routers_voice.InteractionDiagnostic.model_validate({
            "event": "asr_final", "transcript": "private speech",
        })
