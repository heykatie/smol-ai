import json
import sqlite3
import pytest
from smolstuff.shop_migrations import migrate_sqlite, check_sqlite, MigrationError, MigrationRequired
from smolstuff.shop_memberships import MembershipStore
from smolstuff.auth_sessions import AuthSessions

LEGACY = """
CREATE TABLE shop_users (user_id TEXT PRIMARY KEY);
CREATE TABLE shop_identities (provider TEXT NOT NULL, subject TEXT NOT NULL, user_id TEXT NOT NULL, PRIMARY KEY(provider, subject));
CREATE TABLE shops (shop_id TEXT PRIMARY KEY, shop_type TEXT NOT NULL, practice INTEGER NOT NULL);
CREATE TABLE shop_memberships (user_id TEXT NOT NULL, shop_id TEXT NOT NULL, role TEXT NOT NULL, delegated TEXT NOT NULL, active INTEGER NOT NULL, PRIMARY KEY(user_id, shop_id));
CREATE TABLE shop_permission_events (event_id TEXT PRIMARY KEY, shop_id TEXT NOT NULL, actor_id TEXT NOT NULL, target_id TEXT NOT NULL, previous_grants TEXT NOT NULL, new_grants TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE shop_auth_sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES shop_users(user_id) ON DELETE CASCADE, created_at BIGINT NOT NULL, expires_at BIGINT NOT NULL);
CREATE INDEX shop_auth_sessions_user ON shop_auth_sessions(user_id);
"""

@pytest.fixture(autouse=True)
def local_only(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

def legacy(path):
    c = sqlite3.connect(path, isolation_level=None)
    c.executescript(LEGACY)
    c.executemany("INSERT INTO shop_users VALUES (?)", [("owner",), ("employee",)])
    c.execute("INSERT INTO shop_identities VALUES ('auth0:test', 'subject-owner', 'owner')")
    c.executemany("INSERT INTO shops VALUES (?, ?, ?)", [("keyboard", "keyboard", 1), ("bakery", "bakery", 0)])
    c.executemany("INSERT INTO shop_memberships VALUES (?, ?, ?, ?, ?)",
                 [("owner", "keyboard", "owner", "[]", 1),
                  ("employee", "keyboard", "employee", '["approve_correction"]', 1)])
    c.execute("INSERT INTO shop_permission_events VALUES ('event-1','keyboard','owner','employee','[]',?,?)",
              ('["approve_correction"]', "2026-10-06T12:00:00+00:00"))
    c.execute("INSERT INTO shop_auth_sessions VALUES (?, 'owner', 100, 200)", ("a" * 64,))
    c.execute("CREATE TABLE unrelated (value TEXT)")
    c.execute("INSERT INTO unrelated VALUES ('preserve me')")
    c.execute("CREATE INDEX custom_identity_user ON shop_identities(user_id)")
    return c

def snapshot(c):
    names = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    return {name: list(c.execute('SELECT * FROM "' + name + '"')) for name in names}

def test_constructor_requires_explicit_migration_and_never_creates_tables(tmp_path):
    path = tmp_path / "new.sqlite3"
    with pytest.raises(MigrationRequired): MembershipStore(str(path))
    c = sqlite3.connect(path)
    assert list(c.execute("SELECT name FROM sqlite_master WHERE type='table'")) == []
    c.close()

def test_legacy_data_audit_sessions_and_custom_index_survive_idempotent_migration(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    c = legacy(path)
    before = snapshot(c)
    c.close()
    assert check_sqlite(path)["version"] == 0
    assert migrate_sqlite(path) == 1
    assert migrate_sqlite(path) == 1
    c = sqlite3.connect(path)
    after = snapshot(c)
    assert {name: after[name] for name in before} == before
    assert c.execute("SELECT COUNT(*) FROM shop_schema_migrations").fetchone()[0] == 1
    assert c.execute("SELECT name FROM sqlite_master WHERE name='custom_identity_user'").fetchone()
    assert list(c.execute("PRAGMA foreign_key_check")) == []
    c.close()
    store = MembershipStore(str(path))
    assert store.connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert store.membership("employee", "keyboard").delegated == frozenset({"approve_correction"})
    store.close()

@pytest.mark.parametrize("sql,args", [
    ("INSERT INTO shop_identities VALUES ('p','new','missing')", ()),
    ("INSERT INTO shop_memberships VALUES ('missing','keyboard','owner','[]',1)", ()),
    ("INSERT INTO shop_memberships VALUES ('owner','missing','owner','[]',1)", ()),
    ("UPDATE shop_memberships SET role='manager'", ()),
    ("UPDATE shop_memberships SET active=2", ()),
    ("UPDATE shops SET shop_type='unsupported'", ()),
    ("UPDATE shops SET practice=-1", ()),
    ("UPDATE shop_memberships SET delegated=?", ('["manage_members"]',)),
    ("UPDATE shop_memberships SET delegated=?", ('{"approve_spending": true}',)),
    ("UPDATE shop_memberships SET delegated=?", ('["approve_spending", "approve_spending"]',)),
    ("UPDATE shop_memberships SET delegated=?", ("not-json",)),
    ("UPDATE shop_permission_events SET shop_id='bakery'", ()),
    ("UPDATE shop_permission_events SET actor_id='missing'", ()),
    ("UPDATE shop_auth_sessions SET user_id='missing'", ()),
    ("UPDATE shop_auth_sessions SET expires_at=created_at", ()),
    ("UPDATE shop_users SET user_id=''", ()),
    ("DELETE FROM shop_memberships WHERE user_id='employee'", ()),
])
def test_database_rejects_invalid_direct_writes(tmp_path, sql, args):
    path = tmp_path / "constraints.sqlite3"
    c = legacy(path); c.close()
    migrate_sqlite(path)
    store = MembershipStore(str(path))
    try:
        with pytest.raises(sqlite3.IntegrityError):
            store.connection.execute(sql, args)
    finally:
        store.close()

@pytest.mark.parametrize("sql,args", [
    ("INSERT INTO shop_identities VALUES ('p','orphan','missing')", ()),
    ("UPDATE shop_memberships SET role='manager'", ()),
    ("UPDATE shop_memberships SET active=2", ()),
    ("UPDATE shop_memberships SET delegated=?", ("not-json",)),
    ("UPDATE shop_permission_events SET target_id='missing'", ()),
    ("UPDATE shop_auth_sessions SET user_id='missing'", ()),
])
def test_invalid_legacy_data_stops_without_changes_or_sensitive_error_values(tmp_path, sql, args):
    path = tmp_path / "invalid.sqlite3"
    c = legacy(path)
    c.execute(sql, args)
    before = snapshot(c)
    definition = list(c.execute("SELECT name, sql FROM sqlite_master ORDER BY name"))
    with pytest.raises(MigrationError) as error:
        check_sqlite(path)
    assert "subject-owner" not in str(error.value)
    with pytest.raises(MigrationError):
        migrate_sqlite(path)
    assert snapshot(c) == before
    assert list(c.execute("SELECT name, sql FROM sqlite_master ORDER BY name")) == definition
    c.close()

def test_failure_after_copy_and_drop_rolls_back_everything(tmp_path, monkeypatch):
    import smolstuff.shop_migrations as module
    path = tmp_path / "rollback.sqlite3"
    c = legacy(path)
    before = snapshot(c)
    definition = list(c.execute("SELECT name, sql FROM sqlite_master ORDER BY name"))
    original = module._rebuild_sqlite_table
    def fail_after_rebuild(connection, name):
        original(connection, name)
        if name == "shops":
            raise RuntimeError("injected interruption")
    monkeypatch.setattr(module, "_rebuild_sqlite_table", fail_after_rebuild)
    with pytest.raises(RuntimeError):
        migrate_sqlite(path)
    assert snapshot(c) == before
    assert list(c.execute("SELECT name, sql FROM sqlite_master ORDER BY name")) == definition
    assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    c.close()
    monkeypatch.setattr(module, "_rebuild_sqlite_table", original)
    assert migrate_sqlite(path) == 1

def test_extra_legacy_column_stops_instead_of_discarding_information(tmp_path):
    path = tmp_path / "extra.sqlite3"
    c = legacy(path)
    c.execute("ALTER TABLE shops ADD COLUMN custom_note TEXT")
    c.execute("UPDATE shops SET custom_note='keep this'")
    before = snapshot(c)
    with pytest.raises(MigrationError): migrate_sqlite(path)
    assert snapshot(c) == before
    c.close()

def test_json_whitespace_and_field_order_do_not_change_authority(tmp_path):
    path = tmp_path / "json.sqlite3"
    c = legacy(path); c.close()
    migrate_sqlite(path)
    store = MembershipStore(str(path))
    grants = ' [ "approve_spending", "approve_correction" ] '
    store.connection.execute("UPDATE shop_memberships SET delegated=? WHERE user_id='employee'", (grants,))
    assert store.membership("employee", "keyboard").delegated == frozenset({"approve_spending", "approve_correction"})
    store.close()

def test_store_constructors_do_not_run_ddl_after_migration(tmp_path, monkeypatch):
    path = tmp_path / "no-ddl.sqlite3"
    migrate_sqlite(path)
    statements = []
    store = MembershipStore(str(path))
    store.connection.set_trace_callback(statements.append)
    AuthSessions(store)
    assert not any(s.lstrip().upper().startswith(("CREATE", "ALTER", "DROP")) for s in statements)
    store.close()

def test_schema_versions_newer_than_this_code_are_not_used(tmp_path):
    path = tmp_path / "future.sqlite3"
    migrate_sqlite(path)
    c = sqlite3.connect(path)
    c.execute("UPDATE shop_schema_migrations SET version=99")
    c.commit(); c.close()
    with pytest.raises(MigrationError): migrate_sqlite(path)
    with pytest.raises(MigrationRequired): MembershipStore(str(path))

def test_custom_views_and_triggers_are_preserved_and_still_work(tmp_path):
    path = tmp_path / "objects.sqlite3"
    c = legacy(path)
    c.execute("CREATE VIEW custom_members AS SELECT user_id,role FROM shop_memberships")
    c.execute("CREATE TRIGGER custom_shop_change AFTER UPDATE ON shops BEGIN INSERT INTO unrelated VALUES ('shop changed'); END")
    original = dict(c.execute("SELECT name,sql FROM sqlite_master WHERE type IN ('view','trigger')"))
    c.close()
    migrate_sqlite(path)
    store = MembershipStore(str(path))
    assert {r["name"]:r["sql"] for r in store.connection.execute("SELECT name,sql FROM sqlite_master WHERE type IN ('view','trigger')")} == original
    assert len(store.connection.execute("SELECT * FROM custom_members").fetchall()) == 2
    store.connection.execute("UPDATE shops SET practice=1 WHERE shop_id='bakery'")
    assert store.connection.execute("SELECT COUNT(*) AS n FROM unrelated").fetchone()["n"] == 2
    store.close()

def test_read_only_inspection_never_creates_or_rewrites_database(tmp_path):
    path = tmp_path / "read-only.sqlite3"
    assert check_sqlite(path)["new_database"] is True
    assert not path.exists()
    c = legacy(path); c.close()
    before = path.read_bytes()
    assert check_sqlite(path)["ready"] is True
    assert path.read_bytes() == before

def test_simultaneous_sqlite_migrations_stamp_one_version(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    path = tmp_path / "concurrent.sqlite3"
    c = legacy(path); c.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(lambda _: migrate_sqlite(path), range(2))) == [1, 1]
    c = sqlite3.connect(path)
    assert c.execute("SELECT COUNT(*) FROM shop_schema_migrations").fetchone()[0] == 1
    assert c.execute("SELECT COUNT(*) FROM shop_permission_events").fetchone()[0] == 1
    c.close()
