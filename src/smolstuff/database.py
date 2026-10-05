"""Optional Neon Postgres connection.

An empty DATABASE_URL keeps the local demo on SQLite. The value is never printed.
"""

from __future__ import annotations

import os


def database_url() -> str:
    return os.environ.get("DATABASE_URL", "").strip()


def postgres_connection():
    """Return a Postgres connection, or None when Neon is not configured."""
    url = database_url()
    if not url:
        return None
    import psycopg
    from psycopg.rows import dict_row

    from smolstuff.pg_connection import PgConnection

    raw = psycopg.connect(url, autocommit=True, row_factory=dict_row, connect_timeout=10)
    return PgConnection(raw)
