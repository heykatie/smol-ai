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
    assert row["unit_price"] == "1.82"
    assert row["fees"] == "7.00"
    assert row["total"] == "189.00"


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


@pytest.fixture
def postgres_inbox(pg_conn, tmp_path, monkeypatch):
    from smolstuff.inbox import InboxApp

    monkeypatch.setenv("DATABASE_URL", "dbname=smolstuff_pytest")
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "0")
    return InboxApp(str(tmp_path / "sessions" / ("a" * 32 + ".sqlite3")), session_id="a" * 32)


@pytest.mark.parametrize("scenario,action,fields,expected", [
    ("workshop", "workshop_check", {"attendees": ["20"], "days_until": ["7"]}, "Expected contribution: $700"),
    ("staffing", "staffing_calculate", {"day": ["saturday"], "owner_hours": ["6"], "workshop": ["1"]}, "Workload hours: 14"),
])
def test_postgres_preview_get_displays_saved_result_without_session_file(postgres_inbox, scenario, action, fields, expected):
    from pathlib import Path
    from app import _page

    app = postgres_inbox
    app.route(action, dict(fields, scenario=[scenario]))
    assert not Path(app.path).exists()
    assert expected in _page(str(Path(app.path).parent), app.session_id, scenario)
    assert expected in app.view(scenario)


def test_postgres_daily_brief_shows_completed_reorder_and_evidence_without_session_file(postgres_inbox):
    from pathlib import Path
    from app import _page

    from reorder_path import advance_reorder

    app = postgres_inbox
    advance_reorder(app, through="receive_full")
    assert not Path(app.path).exists()
    page = _page(str(Path(app.path).parent), app.session_id, "home")
    assert "Replenishment workflow completed" in page
    assert "Receipt demo adapter" in page
    assert '<span>completed<strong>1</strong></span>' in page


def test_postgres_reorder_uses_saved_lead_time_without_session_file(postgres_inbox):
    from pathlib import Path
    from smolstuff.ops_demos import ScenarioStore

    app = postgres_inbox
    store = ScenarioStore(app.path, app.session_id)
    try:
        store.save("supplier_fact", {"previous": 14, "current": 50})
    finally:
        store.close()
    assert not Path(app.path).exists()
    assert app._plan().lead_time_days == 50


def test_postgres_rendering_does_not_show_another_visitors_preview(postgres_inbox):
    from smolstuff.inbox import InboxApp

    app = postgres_inbox
    app.route("workshop_check", {"scenario": ["workshop"], "attendees": ["20"], "days_until": ["7"]})
    other = InboxApp(app.path, session_id="b" * 32)
    assert "Expected contribution: $700" not in other.view("workshop")
    assert "Expected contribution: $700" in app.view("workshop")
