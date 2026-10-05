"""Optional Neon Postgres connection.

An empty DATABASE_URL keeps the local demo on SQLite. The value is never printed.
"""

from __future__ import annotations

import os


def database_url() -> str:
    return os.environ.get("DATABASE_URL", "").strip()


def postgres_connection():
    """Return a Postgres connection, or None when DATABASE_URL is empty."""
    url = database_url()
    if not url:
        return None
    import psycopg
    from psycopg.rows import dict_row

    from smolstuff.pg_connection import PgConnection

    raw = psycopg.connect(url, autocommit=True, row_factory=dict_row, connect_timeout=10)
    return PgConnection(raw)


def persisted_session(session_id: str) -> bool:
    """True when this visitor has workflow or preview rows in configured Postgres."""
    if not database_url() or not session_id:
        return False
    connection = postgres_connection()
    if connection is None:
        return False
    try:
        for table in ("workflows", "scenario_state"):
            try:
                row = connection.execute(
                    "SELECT 1 AS found FROM {0} WHERE session_id = ? LIMIT 1".format(table),
                    (session_id,),
                ).fetchone()
            except Exception:
                continue
            if row:
                return True
        return False
    finally:
        connection.close()
