"""Shared API state: per-thread SQLite connections + execution mode.

Uvicorn runs sync routes in worker threads; a connection created in one
thread may never be used in another, so each thread gets its own connection
to the same file (WAL mode, busy timeout for writer contention).
"""

from __future__ import annotations

import os
import sqlite3
import threading

from .db import connect


class _State:
    execution_mode: str = os.getenv("VEYTAC_EXECUTION_MODE", "mock")


state = _State()
_local = threading.local()


def db() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None:
        url = os.getenv("VEYTAC_DATABASE_URL", "sqlite:///./artifacts/veytac.db")
        conn = connect(url.split("sqlite:///")[-1])
        _local.conn = conn
    return conn
