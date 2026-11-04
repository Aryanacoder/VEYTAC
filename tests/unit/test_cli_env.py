"""CLI .env loading: the server must honor the repo-root .env.

Regression: live rehearsal silently ran mock because no code ever loaded
.env, so VEYTAC_META_API_KEY / VEYTAC_EXECUTION_MODE / VEYTAC_ALLOW_PAID_CALLS
were ignored even when correctly set in the file.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from veytac.cli import cmd_doctor, load_env_file  # noqa: E402


def test_missing_file_returns_none(tmp_path):
    assert load_env_file(tmp_path / ".env") is None


def test_env_file_values_applied_without_overriding_process_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "VEYTAC_TEST_LOAD_MARKER=from-file\n"
        "VEYTAC_TEST_LOAD_PINNED=from-file\n"
    )
    os.environ["VEYTAC_TEST_LOAD_PINNED"] = "from-process"
    try:
        assert load_env_file(env_file) == env_file
        assert os.environ["VEYTAC_TEST_LOAD_MARKER"] == "from-file"
        assert os.environ["VEYTAC_TEST_LOAD_PINNED"] == "from-process"
    finally:
        del os.environ["VEYTAC_TEST_LOAD_MARKER"]
        del os.environ["VEYTAC_TEST_LOAD_PINNED"]


def test_doctor_reports_effective_mode(monkeypatch, capsys):
    monkeypatch.setenv("VEYTAC_EXECUTION_MODE", "live")
    assert cmd_doctor(None) == 0
    assert "execution_mode=live (doctor made no paid call)" in capsys.readouterr().out
