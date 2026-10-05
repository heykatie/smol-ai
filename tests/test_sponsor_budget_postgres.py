"""Shared sponsor counters when Postgres is configured."""

import threading

import pytest

from smolstuff.pg_connection import PgConnection
from smolstuff.sponsor_budget import SponsorBudget

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


def test_postgres_global_cap_is_shared_across_budget_files(pg_conn, tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.setenv("SMOL_SPONSOR_SESSION_LIMIT", "5")
    monkeypatch.setenv("SMOL_SPONSOR_GLOBAL_LIMIT", "1")

    first = SponsorBudget(str(tmp_path / "a.sqlite3"), connection=PgConnection(pg_conn))
    second_raw = psycopg.connect("dbname=smolstuff_pytest", autocommit=True, row_factory=dict_row)
    second = SponsorBudget(str(tmp_path / "b.sqlite3"), connection=PgConnection(second_raw))
    try:
        assert first.claim("visitor-a") is True
        assert second.claim("visitor-b") is False
        assert first.used("global") == 1
        assert second.used("global") == 1
    finally:
        first.close()
        second.close()
        second_raw.close()


def test_postgres_session_cap_still_applies(pg_conn, tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.setenv("SMOL_SPONSOR_SESSION_LIMIT", "1")
    monkeypatch.setenv("SMOL_SPONSOR_GLOBAL_LIMIT", "5")
    budget = SponsorBudget(str(tmp_path / "budget.sqlite3"), connection=PgConnection(pg_conn))
    try:
        assert budget.claim("visitor-a") is True
        assert budget.claim("visitor-a") is False
        assert budget.claim("visitor-b") is True
    finally:
        budget.close()


def test_postgres_concurrent_claims_respect_global_cap(pg_conn, tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.setenv("SMOL_SPONSOR_SESSION_LIMIT", "5")
    monkeypatch.setenv("SMOL_SPONSOR_GLOBAL_LIMIT", "1")
    # Seed schema through one budget so concurrent workers share the table.
    seed = SponsorBudget(str(tmp_path / "seed.sqlite3"), connection=PgConnection(pg_conn))
    seed.close()

    results = []

    def claim(session_id):
        raw = psycopg.connect("dbname=smolstuff_pytest", autocommit=True, row_factory=dict_row)
        budget = SponsorBudget(str(tmp_path / "x.sqlite3"), connection=PgConnection(raw))
        try:
            results.append(budget.claim(session_id))
        finally:
            budget.close()
            raw.close()

    threads = [
        threading.Thread(target=claim, args=("visitor-a",)),
        threading.Thread(target=claim, args=("visitor-b",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results.count(True) == 1
    assert results.count(False) == 1
    check = SponsorBudget(str(tmp_path / "check.sqlite3"), connection=PgConnection(pg_conn))
    try:
        assert check.used("global") == 1
    finally:
        check.close()


def test_database_url_selects_postgres_instead_of_the_file(pg_conn, tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "dbname=smolstuff_pytest")
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.setenv("SMOL_SPONSOR_SESSION_LIMIT", "5")
    monkeypatch.setenv("SMOL_SPONSOR_GLOBAL_LIMIT", "1")

    first = SponsorBudget(str(tmp_path / "ignored-a.sqlite3"))
    second = SponsorBudget(str(tmp_path / "ignored-b.sqlite3"))
    try:
        assert first.dialect == "postgres"
        assert second.dialect == "postgres"
        assert first.claim("visitor-a") is True
        assert second.claim("visitor-b") is False
        assert not (tmp_path / "ignored-a.sqlite3").exists()
        assert not (tmp_path / "ignored-b.sqlite3").exists()
    finally:
        first.close()
        second.close()
