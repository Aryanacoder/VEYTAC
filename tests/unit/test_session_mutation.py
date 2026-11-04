"""A long-running voice call must not erase newer capture/session fields."""

from services.api.db import (connect, get_session, mutate_session,
                             reconcile_session_call, reserve_session_call)


def test_voice_reconciliation_keeps_spoken_brief_and_consent(tmp_path):
    path = tmp_path / "session.db"
    voice = connect(str(path))
    request = connect(str(path))
    session_id = "ses_test"
    voice.execute("INSERT INTO sessions(id,payload) VALUES(?,?)",
                  (session_id, '{"capture_granted":true,"budget_cap_usd":"3.00"}'))
    voice.commit()

    assert reserve_session_call(voice, session_id, "call_voice", 12000)
    mutate_session(request, session_id,
                   lambda current: current.update(task_brief="I am holding a screw."))
    reconcile_session_call(voice, session_id, "call_voice", 3000)

    saved = get_session(request, session_id)
    assert saved["task_brief"] == "I am holding a screw."
    assert saved["capture_granted"] is True
    assert saved["budget"]["spent_micro"] == 3000
    assert saved["budget"]["reserved"] == {}
