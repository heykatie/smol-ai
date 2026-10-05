"""Postgres anonymous demo rows expire on the same TTL as local session files."""

from datetime import datetime, timedelta, timezone

import pytest

from smolstuff.database import expire_persisted_sessions, persisted_session
from smolstuff.fixtures import EXAMPLE_POLICY, NEEDS_APPROVAL_PURCHASE
from smolstuff.ops_demos import ScenarioStore
from smolstuff.pg_connection import PgConnection
from smolstuff.session_files import expire_demo_sessions
from smolstuff.workflow import WorkflowStore

pytest.importorskip("psycopg")
from psycopg.rows import dict_row
import psycopg


def _database_available():
    try:
        conn = psycopg.connect("dbname=postgres", connect_timeout=2)
    except Exception:
        return False
    conn.close()
    return True


pytestmark = pytest.mark.skipif(not _database_available(), reason="Local Postgres is not running.")


@pytest.fixture
def pg_conn():
    admin = psycopg.connect("dbname=postgres", autocommit=True)
    exists = admin.execute(
        "SELECT 1 FROM pg_database WHERE datname = 'smolstuff_pytest'"
    ).fetchone()
    if exists is None:
        admin.execute("CREATE DATABASE smolstuff_pytest")
    admin.close()
    conn = psycopg.connect("dbname=smolstuff_pytest", autocommit=True, row_factory=dict_row)
    conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
    conn.execute("CREATE SCHEMA public")
    yield conn
    conn.close()


def test_old_postgres_session_rows_are_removed_and_fresh_ones_remain(pg_conn, tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "dbname=smolstuff_pytest")
    monkeypatch.setenv("SMOL_DEMO_TTL_SECONDS", "10")
    now = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
    old_time = now - timedelta(seconds=30)
    fresh_time = now - timedelta(seconds=5)

    old = WorkflowStore(
        ":memory:",
        session_id="a" * 32,
        connection=PgConnection(pg_conn),
        now=lambda: old_time,
    )
    old.start_purchase("old-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)

    fresh = WorkflowStore(
        ":memory:",
        session_id="b" * 32,
        connection=PgConnection(pg_conn),
        now=lambda: fresh_time,
    )
    fresh.start_purchase("fresh-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)

    removed = expire_persisted_sessions(now=now.timestamp())
    assert removed == 1
    assert persisted_session("a" * 32) is False
    assert persisted_session("b" * 32) is True


def test_old_preview_only_postgres_session_is_removed(pg_conn, tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "dbname=smolstuff_pytest")
    monkeypatch.setenv("SMOL_DEMO_TTL_SECONDS", "10")
    now = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
    old_time = now - timedelta(seconds=30)

    store = ScenarioStore(":memory:", session_id="c" * 32, connection=PgConnection(pg_conn))
    store.save("workshop", {"phase": "saved"})
    pg_conn.execute(
        "UPDATE scenario_state SET updated_at = %s WHERE session_id = %s",
        (old_time.isoformat(), "c" * 32),
    )

    assert expire_persisted_sessions(now=now.timestamp()) == 1
    assert persisted_session("c" * 32) is False


def test_expire_demo_sessions_also_clears_postgres(pg_conn, tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "dbname=smolstuff_pytest")
    monkeypatch.setenv("SMOL_DEMO_TTL_SECONDS", "10")
    now = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
    old_time = now - timedelta(seconds=30)

    store = WorkflowStore(
        ":memory:",
        session_id="d" * 32,
        connection=PgConnection(pg_conn),
        now=lambda: old_time,
    )
    store.start_purchase("expire-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)

    root = tmp_path / "sessions"
    root.mkdir()
    stale_file = root / ("e" * 32 + ".sqlite3")
    stale_file.write_text("old")
    import os

    os.utime(str(stale_file), (now.timestamp() - 30, now.timestamp() - 30))

    removed = expire_demo_sessions(str(root), now=now.timestamp())
    assert removed == 2
    assert not stale_file.exists()
    assert persisted_session("d" * 32) is False
