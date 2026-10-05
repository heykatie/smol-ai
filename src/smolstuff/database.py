"""Optional Neon Postgres connection.

An empty DATABASE_URL keeps the local demo on SQLite. The value is never printed.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone


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


def expire_persisted_sessions(now: float = None) -> int:
    """Delete Postgres demo session rows older than the anonymous TTL.

    Returns how many session ids were removed. No-op without DATABASE_URL.
    This is anonymous demo cleanup, not business-record retention.
    """
    if not database_url():
        return 0
    from smolstuff.session_files import demo_ttl_seconds

    connection = postgres_connection()
    if connection is None:
        return 0
    moment = time.time() if now is None else now
    cutoff = datetime.fromtimestamp(moment, tz=timezone.utc) - timedelta(seconds=demo_ttl_seconds())
    cutoff_text = cutoff.isoformat()
    try:
        expired = _expired_session_ids(connection, cutoff_text)
        for session_id in expired:
            _delete_session_rows(connection, session_id)
        return len(expired)
    finally:
        connection.close()


def _expired_session_ids(connection, cutoff_text: str) -> list:
    parts = []
    for table, column in (
        ("workflows", "updated_at"),
        ("scenario_state", "updated_at"),
        ("integration_events", "recorded_at"),
        ("receipts", "created_at"),
    ):
        try:
            connection.execute(
                "SELECT 1 AS found FROM {0} WHERE {1} IS NOT NULL LIMIT 1".format(table, column)
            ).fetchone()
        except Exception:
            connection.rollback()
            continue
        parts.append(
            "SELECT session_id, {0} AS ts FROM {1} WHERE session_id IS NOT NULL AND {0} IS NOT NULL".format(
                column, table
            )
        )
    if not parts:
        return []
    rows = connection.execute(
        """
        SELECT session_id FROM (
            SELECT session_id, MAX(ts) AS last_seen
            FROM ({0}) AS activity
            GROUP BY session_id
        ) AS ages
        WHERE last_seen < ?
        """.format(
            " UNION ALL ".join(parts)
        ),
        (cutoff_text,),
    ).fetchall()
    return [_row_value(row, "session_id") for row in rows or []]


def _delete_session_rows(connection, session_id: str) -> None:
    connection.execute("BEGIN IMMEDIATE")
    try:
        _delete_session_core(connection, session_id)
        if _table_exists(connection, "sponsor_calls"):
            connection.execute("DELETE FROM sponsor_calls WHERE scope = ?", (session_id,))
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _delete_session_core(connection, session_id: str) -> None:
    if _table_exists(connection, "inventory_movements") and _table_exists(connection, "receipts"):
        connection.execute(
            """
            DELETE FROM inventory_movements
            WHERE receipt_id IN (SELECT id FROM receipts WHERE session_id = ?)
            """,
            (session_id,),
        )
    if _table_exists(connection, "receipts"):
        connection.execute("DELETE FROM receipts WHERE session_id = ?", (session_id,))
    if _table_exists(connection, "confirmations") and _table_exists(connection, "actions") and _table_exists(
        connection, "workflows"
    ):
        connection.execute(
            """
            DELETE FROM confirmations
            WHERE action_id IN (
                SELECT actions.id FROM actions
                JOIN workflows ON workflows.id = actions.workflow_id
                WHERE workflows.session_id = ?
            )
            """,
            (session_id,),
        )
    if _table_exists(connection, "executions") and _table_exists(connection, "actions") and _table_exists(
        connection, "workflows"
    ):
        connection.execute(
            """
            DELETE FROM executions
            WHERE action_id IN (
                SELECT actions.id FROM actions
                JOIN workflows ON workflows.id = actions.workflow_id
                WHERE workflows.session_id = ?
            )
            """,
            (session_id,),
        )
    if _table_exists(connection, "approvals") and _table_exists(connection, "actions") and _table_exists(
        connection, "workflows"
    ):
        connection.execute(
            """
            DELETE FROM approvals
            WHERE action_id IN (
                SELECT actions.id FROM actions
                JOIN workflows ON workflows.id = actions.workflow_id
                WHERE workflows.session_id = ?
            )
            """,
            (session_id,),
        )
    if _table_exists(connection, "workflow_transitions") and _table_exists(connection, "workflows"):
        connection.execute(
            """
            DELETE FROM workflow_transitions
            WHERE workflow_id IN (SELECT id FROM workflows WHERE session_id = ?)
            """,
            (session_id,),
        )
    if _table_exists(connection, "actions") and _table_exists(connection, "workflows"):
        connection.execute(
            """
            DELETE FROM actions
            WHERE workflow_id IN (SELECT id FROM workflows WHERE session_id = ?)
            """,
            (session_id,),
        )
    if _table_exists(connection, "workflows"):
        connection.execute("DELETE FROM workflows WHERE session_id = ?", (session_id,))
    if _table_exists(connection, "integration_events"):
        connection.execute("DELETE FROM integration_events WHERE session_id = ?", (session_id,))
    if _table_exists(connection, "scenario_state"):
        connection.execute("DELETE FROM scenario_state WHERE session_id = ?", (session_id,))


def _table_exists(connection, name: str) -> bool:
    try:
        row = connection.execute(
            """
            SELECT 1 AS found
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = ?
            """,
            (name,),
        ).fetchone()
        return bool(row)
    except Exception:
        return False


def _row_value(row, key: str):
    if isinstance(row, dict):
        return row[key]
    return row[0]
