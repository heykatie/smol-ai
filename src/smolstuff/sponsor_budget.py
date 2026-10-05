"""Call-count limits for anonymous sponsor tasks.

Calls stay off unless the process is explicitly enabled and both limits are set.
Without DATABASE_URL, counters live in a shared SQLite file. With Postgres
configured, the same table is shared across instances that use that database.
This is still a call-count limit, not a monetary spend cap. One task may make
multiple provider requests.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


class SponsorBudget:
    def __init__(self, path: str, connection=None) -> None:
        self.path = path
        owns = connection is None
        if connection is None:
            from smolstuff.database import postgres_connection

            connection = postgres_connection()
        if connection is not None:
            self._conn = connection
            self.dialect = "postgres"
        else:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(path)
            self._conn.isolation_level = None
            self.dialect = "sqlite"
        self._owns_connection = owns
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sponsor_calls (
                scope TEXT PRIMARY KEY,
                used INTEGER NOT NULL
            )
            """
        )

    def close(self) -> None:
        if self._owns_connection:
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
            session_used = self._used_for_update(session_id)
            global_used = self._used_for_update("global")
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
        return _row_used(row)

    def _used_for_update(self, scope: str) -> int:
        """Read the counter under the open transaction, locking the row when Postgres."""
        if self.dialect == "postgres":
            self._conn.execute(
                "INSERT INTO sponsor_calls (scope, used) VALUES (?, 0) ON CONFLICT (scope) DO NOTHING",
                (scope,),
            )
            row = self._conn.execute(
                "SELECT used FROM sponsor_calls WHERE scope = ? FOR UPDATE",
                (scope,),
            ).fetchone()
            return _row_used(row)
        return self._used(scope)

    def _set(self, scope: str, used: int) -> None:
        self._conn.execute(
            """
            INSERT INTO sponsor_calls (scope, used) VALUES (?, ?)
            ON CONFLICT(scope) DO UPDATE SET used = excluded.used
            """,
            (scope, used),
        )


def _row_used(row) -> int:
    if row is None:
        return 0
    if isinstance(row, dict):
        return int(row["used"])
    return int(row[0])


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
