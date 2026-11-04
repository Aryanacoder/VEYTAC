"""Minimal SQLite store: sessions, consents, audit events (TRD 9.1 subset)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS consents (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  purpose TEXT NOT NULL,
  granted_at TEXT,
  revoked_at TEXT,
  notice_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
  event_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  sequence_no INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  payload TEXT NOT NULL DEFAULT '{}',
  UNIQUE (session_id, sequence_no)
);
CREATE TABLE IF NOT EXISTS entities (
  kind TEXT NOT NULL,
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
  session_id TEXT NOT NULL,
  stream_id TEXT NOT NULL,
  epoch_id TEXT NOT NULL,
  sequence_no INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  locator TEXT NOT NULL,
  PRIMARY KEY (session_id, stream_id, epoch_id, sequence_no)
);
"""


def connect(path: str) -> sqlite3.Connection:
    p = Path(path)
    if p.parent != Path("."):
        p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False, timeout=30.0)
    conn.executescript(SCHEMA)
    return conn


def insert_session(conn: sqlite3.Connection, session_id: str, payload: dict) -> None:
    conn.execute(
        "INSERT INTO sessions(id, payload) VALUES(?, ?)",
        (session_id, json.dumps(payload)),
    )
    conn.commit()


def get_session(conn: sqlite3.Connection, session_id: str) -> dict | None:
    row = conn.execute(
        "SELECT payload FROM sessions WHERE id=?", (session_id,)
    ).fetchone()
    return json.loads(row[0]) if row else None


def update_session(conn: sqlite3.Connection, session_id: str, payload: dict) -> None:
    conn.execute(
        "UPDATE sessions SET payload=? WHERE id=?",
        (json.dumps(payload), session_id),
    )
    conn.commit()


def mutate_session(conn: sqlite3.Connection, session_id: str,
                   change: Callable[[dict], T]) -> tuple[dict, T]:
    """Update the current session under a write lock, never a stale socket copy."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute("SELECT payload FROM sessions WHERE id=?", (session_id,)).fetchone()
        if row is None:
            raise KeyError(session_id)
        payload = json.loads(row[0])
        result = change(payload)
        conn.execute("UPDATE sessions SET payload=? WHERE id=?",
                     (json.dumps(payload), session_id))
        conn.commit()
        return payload, result
    except Exception:
        conn.rollback()
        raise


def reserve_session_call(conn: sqlite3.Connection, session_id: str,
                         call_id: str, estimate_micro: int) -> bool:
    from veytac.budget.ledger import reserve_call

    _, allowed = mutate_session(
        conn, session_id, lambda payload: reserve_call(payload, call_id, estimate_micro))
    return allowed


def reconcile_session_call(conn: sqlite3.Connection, session_id: str,
                           call_id: str, actual_micro: int | None) -> None:
    from veytac.budget.ledger import reconcile_call

    def change(payload: dict) -> None:
        if call_id not in payload.get("budget", {}).get("reserved", {}):
            raise ValueError(f"budget reservation missing for {call_id}")
        reconcile_call(payload, call_id, actual_micro)

    mutate_session(conn, session_id, change)


def put_entity(conn: sqlite3.Connection, kind: str, entity_id: str, session_id: str, payload: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO entities(kind, id, session_id, payload) VALUES(?,?,?,?)",
        (kind, entity_id, session_id, json.dumps(payload)),
    )
    conn.commit()


def list_entities(conn: sqlite3.Connection, kind: str, session_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT payload FROM entities WHERE kind=? AND session_id=?", (kind, session_id)
    ).fetchall()
    return [json.loads(r[0]) for r in rows]
