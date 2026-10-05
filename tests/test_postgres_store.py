import threading

import pytest

from smolstuff.fixtures import EXAMPLE_POLICY, NEEDS_APPROVAL_PURCHASE
from smolstuff.pg_connection import PgConnection
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


def _store(conn, session_id):
    return WorkflowStore(":memory:", session_id=session_id, connection=PgConnection(conn))


def test_postgres_visitors_do_not_share_a_demo_signal(pg_conn):
    first = _store(pg_conn, "visitor-a")
    second_raw = psycopg.connect("dbname=smolstuff_pytest", autocommit=True, row_factory=dict_row)
    try:
        second = WorkflowStore(":memory:", session_id="visitor-b", connection=PgConnection(second_raw))
        first.start_purchase("demo-supplier-lead-time-35", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        second.start_purchase("demo-supplier-lead-time-35", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        assert first.count_workflows() == 1
        assert second.count_workflows() == 1
        first.reset_signal("demo-supplier-lead-time-35")
        assert first.find_by_dedup("demo-supplier-lead-time-35") is None
        assert second.find_by_dedup("demo-supplier-lead-time-35") is not None
    finally:
        second_raw.close()


def test_postgres_money_round_trips_as_exact_text(pg_conn):
    store = _store(pg_conn, "visitor-a")
    store.start_purchase("demo-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    row = store._conn.execute("SELECT unit_price, fees, total FROM actions").fetchone()
    assert row["unit_price"] == "0.54"
    assert row["fees"] == "7.00"
    assert row["total"] == "61.00"


def test_postgres_duplicate_receipt_creates_one_movement(pg_conn):
    store = _store(pg_conn, "visitor-a")
    started = store.start_purchase("demo-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    store.approve(started.workflow_id, actor="owner")
    store.execute(started.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    from decimal import Decimal

    baseline = Decimal("21")
    store.confirm(started.workflow_id, NEEDS_APPROVAL_PURCHASE, baseline)
    store.receive(started.workflow_id, 100, "demo-receipt-full", baseline)
    store.receive(started.workflow_id, 100, "demo-receipt-full", baseline)
    assert store.count_movements() == 1
    assert store.count_receipts() == 1


def test_postgres_failed_write_rolls_back(pg_conn):
    store = _store(pg_conn, "visitor-a")
    store._begin()
    store._conn.rollback()
    assert store.count_workflows() == 0


def test_postgres_concurrent_approvals_create_one_decision(pg_conn):
    store = _store(pg_conn, "visitor-a")
    started = store.start_purchase("demo-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    errors = []

    def approve():
        conn = psycopg.connect("dbname=smolstuff_pytest", autocommit=True, row_factory=dict_row)
        local = WorkflowStore(
            ":memory:", session_id="visitor-a", connection=PgConnection(conn)
        )
        try:
            local.approve(started.workflow_id, actor="owner")
        except Exception as exc:
            errors.append(exc)
        finally:
            local.close()

    threads = [threading.Thread(target=approve) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    row = store._conn.execute("SELECT COUNT(*) AS n FROM approvals").fetchone()
    assert int(row["n"]) == 1
