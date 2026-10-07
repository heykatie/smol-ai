"""Run only against an explicitly selected disposable local test cluster."""
import os
import getpass
from uuid import uuid4

import pytest
pytest.importorskip("psycopg")
import psycopg
from psycopg.rows import dict_row

from smolstuff.pg_connection import PgConnection
from smolstuff.shop_migrations import migrate_postgres, check_postgres, MigrationError
from smolstuff.shop_memberships import MembershipStore
from test_shop_migrations import LEGACY

pytestmark = pytest.mark.skipif(not os.environ.get("SMOL_TEST_PG_SOCKET"), reason="Disposable Postgres cluster not selected.")

@pytest.fixture
def pg(monkeypatch):
    socket = os.environ["SMOL_TEST_PG_SOCKET"]
    if not socket.startswith(("/private/tmp/smolstuff-migrations-", "/tmp/smolstuff-migrations-")):
        pytest.fail("A disposable local migration-test socket is required.")
    raw = psycopg.connect(host=socket, port=55473, dbname="postgres",
                         user=getpass.getuser(), autocommit=True, row_factory=dict_row)
    schema = "smol_migration_" + uuid4().hex
    raw.execute('CREATE SCHEMA "' + schema + '"')
    raw.execute('SET search_path TO "' + schema + '"')
    wrapper = PgConnection(raw)
    monkeypatch.setattr("smolstuff.shop_memberships.postgres_connection", lambda: wrapper)
    try:
        yield wrapper
    finally:
        raw.execute("SET search_path TO public")
        raw.execute('DROP SCHEMA "' + schema + '" CASCADE')
        raw.close()

def prepare(pg):
    pg.executescript(LEGACY)
    pg.execute("INSERT INTO shop_users VALUES ('owner'), ('employee')")
    pg.execute("INSERT INTO shops VALUES ('keyboard','keyboard',1), ('bakery','bakery',0)")
    pg.execute("INSERT INTO shop_identities VALUES ('auth0:test','subject-owner','owner')")
    pg.execute("INSERT INTO shop_memberships VALUES ('owner','keyboard','owner','[]',1),"
               "('employee','keyboard','employee','[]',1)")
    pg.execute("INSERT INTO shop_permission_events VALUES ('event-1','keyboard','owner','employee','[]','[]',?)",
               ("2026-10-06T12:00:00+00:00",))
    pg.execute("INSERT INTO shop_auth_sessions VALUES (?, 'owner',100,200)", ("a" * 64,))

def test_postgres_preserves_memberships_audit_and_sessions_and_replays(pg):
    prepare(pg)
    before = {name: pg.execute("SELECT * FROM " + name).fetchall() for name in (
        "shop_users","shops","shop_identities","shop_memberships","shop_permission_events","shop_auth_sessions")}
    assert check_postgres(pg)["version"] == 0
    assert migrate_postgres(pg) == 1
    assert migrate_postgres(pg) == 1
    for name, values in before.items():
        assert pg.execute("SELECT * FROM " + name).fetchall() == values
    store = MembershipStore(":unused:")
    assert store.membership("owner","keyboard").role == "owner"

@pytest.mark.parametrize("sql,args", [
    ("INSERT INTO shop_identities VALUES ('p','orphan','missing')", ()),
    ("INSERT INTO shop_memberships VALUES ('missing','keyboard','owner','[]',1)", ()),
    ("UPDATE shop_memberships SET role='manager'", ()),
    ("UPDATE shops SET practice=2", ()),
    ("UPDATE shop_memberships SET active=-1", ()),
    ("UPDATE shop_memberships SET delegated=?", ('["manage_members"]',)),
    ("UPDATE shop_memberships SET delegated=?", ('[null]',)),
    ("UPDATE shop_memberships SET delegated=?", ('{"approve_spending": true}',)),
    ("UPDATE shop_memberships SET delegated=?", ('["approve_spending","approve_spending"]',)),
    ("UPDATE shop_permission_events SET shop_id='bakery'", ()),
    ("UPDATE shop_auth_sessions SET user_id='missing'", ()),
    ("UPDATE shop_auth_sessions SET expires_at=created_at", ()),
    ("DELETE FROM shop_memberships WHERE user_id='employee'", ()),
])
def test_postgres_direct_writes_fail_constraints(pg, sql, args):
    prepare(pg); migrate_postgres(pg)
    with pytest.raises(psycopg.IntegrityError):
        pg.execute(sql,args)
    assert pg.execute("SELECT COUNT(*) AS n FROM shop_memberships").fetchone()["n"] == 2

def test_postgres_valid_json_whitespace_and_order(pg):
    prepare(pg); migrate_postgres(pg)
    pg.execute("UPDATE shop_memberships SET delegated=? WHERE user_id='employee'",
               (' [ "approve_spending", "approve_correction" ] ',))
    store = MembershipStore(":unused:")
    assert store.membership("employee","keyboard").delegated == frozenset({"approve_spending","approve_correction"})

def test_postgres_legacy_orphan_stops_without_stamp_or_repair(pg):
    prepare(pg)
    pg.execute("INSERT INTO shop_identities VALUES ('p','orphan','missing')")
    with pytest.raises(MigrationError): migrate_postgres(pg)
    assert pg.execute("SELECT COUNT(*) AS n FROM shop_identities").fetchone()["n"] == 2
    assert pg.execute("SELECT to_regclass('shop_schema_migrations') AS table_name").fetchone()["table_name"] is None

def test_postgres_failure_after_constraint_changes_rolls_back(pg, monkeypatch):
    import smolstuff.shop_migrations as module
    prepare(pg)
    before = pg.execute("SELECT conname FROM pg_constraint WHERE conrelid='shop_memberships'::regclass ORDER BY conname").fetchall()
    def fail(*args): raise RuntimeError("injected interruption before stamp")
    monkeypatch.setattr(module, "_stamp", fail)
    with pytest.raises(RuntimeError): migrate_postgres(pg)
    assert pg.execute("SELECT conname FROM pg_constraint WHERE conrelid='shop_memberships'::regclass ORDER BY conname").fetchall() == before
    assert pg.execute("SELECT COUNT(*) AS n FROM shop_permission_events").fetchone()["n"] == 1
    assert pg.execute("SELECT to_regclass('shop_schema_migrations') AS table_name").fetchone()["table_name"] is None

def test_simultaneous_postgres_migrations_stamp_one_version(pg):
    from concurrent.futures import ThreadPoolExecutor
    prepare(pg)
    schema = pg.execute("SELECT current_schema() AS name").fetchone()["name"]
    def migrate(_):
        raw = psycopg.connect(host=os.environ["SMOL_TEST_PG_SOCKET"], port=55473, dbname="postgres",
                              user=getpass.getuser(), autocommit=True, row_factory=dict_row)
        try:
            raw.execute('SET search_path TO "' + schema + '"')
            return migrate_postgres(PgConnection(raw))
        finally:
            raw.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(migrate, range(2))) == [1, 1]
    assert pg.execute("SELECT COUNT(*) AS n FROM shop_schema_migrations").fetchone()["n"] == 1
    assert pg.execute("SELECT COUNT(*) AS n FROM shop_permission_events").fetchone()["n"] == 1
