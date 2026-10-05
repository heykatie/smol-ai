"""File-backed call-count limits for anonymous sponsor tasks.

Calls stay off unless the process is explicitly enabled and both limits are set.
Counters persist only while their shared SQLite file survives. They do not
provide a cap across separate files, Vercel instances, or redeploys, and they
do not measure monetary spend. One task may make multiple provider requests.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


class SponsorBudget:
    def __init__(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.isolation_level = None
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sponsor_calls (
                scope TEXT PRIMARY KEY,
                used INTEGER NOT NULL
            )
            """
        )

    def close(self) -> None:
        self._conn.close()

    def claim(self, session_id: str) -> bool:
        """Reserve one outbound call. False means the call must not leave the process."""
        if os.environ.get("SMOL_SPONSOR_CALLS") != "1":
            return False
        session_limit = _limit("SMOL_SPONSOR_SESSION_LIMIT")
        global_limit = _limit("SMOL_SPONSOR_GLOBAL_LIMIT")
        if session_limit is None or global_limit is None:
            return False
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            session_used = self._used(session_id)
            global_used = self._used("global")
            if session_used >= session_limit or global_used >= global_limit:
                self._conn.commit()
                return False
            self._set(session_id, session_used + 1)
            self._set("global", global_used + 1)
            self._conn.commit()
            return True
        except Exception:
            self._conn.rollback()
            raise

    def used(self, scope: str) -> int:
        return self._used(scope)

    def _used(self, scope: str) -> int:
        row = self._conn.execute(
            "SELECT used FROM sponsor_calls WHERE scope = ?", (scope,)
        ).fetchone()
        if row is None:
            return 0
        return int(row[0])

    def _set(self, scope: str, used: int) -> None:
        self._conn.execute(
            """
            INSERT INTO sponsor_calls (scope, used) VALUES (?, ?)
            ON CONFLICT(scope) DO UPDATE SET used = excluded.used
            """,
            (scope, used),
        )


def _limit(name: str):
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    if value < 1:
        return None
    return value
