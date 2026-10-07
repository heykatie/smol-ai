"""Explicit, transactional version-1 migration for shop identity/membership tables.

No .env loading, request-time DDL, data repair, or automatic production migration.
CLI defaults to read-only inspection. Errors name tables/reasons, never row values.
"""
import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

VERSION = 1
NAME = "shop_identity_membership_constraints"
COLUMNS = {
    "shop_users": ("user_id",),
    "shop_identities": ("provider", "subject", "user_id"),
    "shops": ("shop_id", "shop_type", "practice"),
    "shop_memberships": ("user_id", "shop_id", "role", "delegated", "active"),
    "shop_permission_events": ("event_id", "shop_id", "actor_id", "target_id",
                               "previous_grants", "new_grants", "created_at"),
    "shop_auth_sessions": ("token_hash", "user_id", "created_at", "expires_at"),
}
ALLOWED_GRANTS = {"approve_correction", "approve_spending"}
PRIMARY_KEYS = {
    "shop_users": ("user_id",), "shop_identities": ("provider", "subject"),
    "shops": ("shop_id",), "shop_memberships": ("user_id", "shop_id"),
    "shop_permission_events": ("event_id",), "shop_auth_sessions": ("token_hash",),
}

class MigrationError(RuntimeError):
    pass

class MigrationRequired(MigrationError):
    pass

def _quote(name):
    return '"' + name.replace('"', '""') + '"'

def _grant_check(column, postgres):
    values = "('approve_correction','approve_spending')"
    if postgres:
        value = "(" + column + "::jsonb)"
        size = "jsonb_array_length(" + value + ")"
        first, second = value + "->0", value + "->1"
        return ("CASE WHEN jsonb_typeof(" + value + ")='array' THEN "
                + size + " BETWEEN 0 AND 2 AND (" + size + "=0 OR "
                "(jsonb_typeof(" + first + ")='string' AND (" + value + "->>0) IN " + values + ")) AND ("
                + size + "<2 OR (jsonb_typeof(" + second + ")='string' AND (" + value + "->>1) IN "
                + values + " AND (" + value + "->>0)<>(" + value + "->>1))) ELSE FALSE END")
    size = "json_array_length(" + column + ")"
    first, second = "json_extract(" + column + ",'$[0]')", "json_extract(" + column + ",'$[1]')"
    return ("CASE WHEN json_valid(" + column + ") THEN CASE WHEN json_type(" + column
            + ")='array' THEN " + size + " BETWEEN 0 AND 2 AND (" + size
            + "=0 OR (json_type(" + column + ",'$[0]')='text' AND " + first + " IN " + values
            + ")) AND (" + size + "<2 OR (json_type(" + column + ",'$[1]')='text' AND "
            + second + " IN " + values + " AND " + first + "<>" + second
            + ")) ELSE 0 END ELSE 0 END")

def _schema(postgres):
    nonempty = lambda col: "length(trim(" + col + ")) > 0"
    schema = {
        "shop_users": (["user_id TEXT NOT NULL", "PRIMARY KEY(user_id)"], [nonempty("user_id")], []),
        "shop_identities": (["provider TEXT NOT NULL", "subject TEXT NOT NULL", "user_id TEXT NOT NULL",
                             "PRIMARY KEY(provider,subject)"],
                            [nonempty(x) for x in ("provider", "subject", "user_id")],
                            ["FOREIGN KEY(user_id) REFERENCES shop_users(user_id)"]),
        "shops": (["shop_id TEXT NOT NULL", "shop_type TEXT NOT NULL", "practice INTEGER NOT NULL",
                   "PRIMARY KEY(shop_id)"],
                  [nonempty("shop_id"), "shop_type IN ('keyboard','bakery')", "practice IN (0,1)"], []),
        "shop_memberships": (["user_id TEXT NOT NULL", "shop_id TEXT NOT NULL", "role TEXT NOT NULL",
                             "delegated TEXT NOT NULL", "active INTEGER NOT NULL",
                             "PRIMARY KEY(user_id,shop_id)"],
                            ["role IN ('owner','employee')", "active IN (0,1)",
                             _grant_check("delegated", postgres)],
                            ["FOREIGN KEY(user_id) REFERENCES shop_users(user_id)",
                             "FOREIGN KEY(shop_id) REFERENCES shops(shop_id)"]),
        "shop_permission_events": (["event_id TEXT NOT NULL", "shop_id TEXT NOT NULL", "actor_id TEXT NOT NULL",
                                   "target_id TEXT NOT NULL", "previous_grants TEXT NOT NULL",
                                   "new_grants TEXT NOT NULL", "created_at TEXT NOT NULL", "PRIMARY KEY(event_id)"],
                                  [nonempty("event_id"), nonempty("created_at"),
                                   _grant_check("previous_grants", postgres), _grant_check("new_grants", postgres)],
                                  ["FOREIGN KEY(actor_id,shop_id) REFERENCES shop_memberships(user_id,shop_id)",
                                   "FOREIGN KEY(target_id,shop_id) REFERENCES shop_memberships(user_id,shop_id)"]),
        "shop_auth_sessions": (["token_hash TEXT NOT NULL", "user_id TEXT NOT NULL", "created_at BIGINT NOT NULL",
                               "expires_at BIGINT NOT NULL", "PRIMARY KEY(token_hash)"],
                              ["length(token_hash)=64", "created_at >= 0", "expires_at > created_at",
                               "token_hash ~ '^[0-9a-f]{64}$'" if postgres
                               else "token_hash NOT GLOB '*[^0-9a-f]*'",
                               "TRUE" if postgres else "typeof(created_at)='integer' AND typeof(expires_at)='integer'"],
                              ["FOREIGN KEY(user_id) REFERENCES shop_users(user_id) ON DELETE CASCADE"]),
    }
    return schema

def _checksum(postgres):
    return hashlib.sha256(json.dumps(_schema(postgres), sort_keys=True).encode()).hexdigest()

def _exists(connection, name, postgres):
    if postgres:
        return bool(connection.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_schema=current_schema() AND table_name=?",
            (name,)).fetchone())
    return bool(connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())

def _version(connection, postgres):
    if not _exists(connection, "shop_schema_migrations", postgres):
        return 0
    rows = connection.execute("SELECT version,name,checksum FROM shop_schema_migrations ORDER BY version").fetchall()
    if not rows:
        return 0
    if (len(rows) != 1 or rows[0]["version"] != VERSION or rows[0]["name"] != NAME
            or rows[0]["checksum"] != _checksum(postgres)):
        raise MigrationError("Unsupported or inconsistent shop schema migration history.")
    return VERSION

def require_schema(connection, *, postgres=False):
    try:
        if _version(connection, postgres) != VERSION:
            raise MigrationRequired("Run the explicit shop schema migration before opening this store.")
    except MigrationError as error:
        raise MigrationRequired(str(error)) from None

def _columns(connection, name, postgres):
    if postgres:
        return tuple(row["column_name"] for row in connection.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema=current_schema() AND table_name=? ORDER BY ordinal_position", (name,)))
    return tuple(row["name"] for row in connection.execute("PRAGMA table_info(" + _quote(name) + ")"))

def _primary_key(connection, name, postgres):
    if postgres:
        rows = connection.execute(
            "SELECT k.column_name FROM information_schema.table_constraints t "
            "JOIN information_schema.key_column_usage k "
            "ON t.constraint_name=k.constraint_name AND t.constraint_schema=k.constraint_schema "
            "AND t.table_name=k.table_name "
            "WHERE t.table_schema=current_schema() AND t.table_name=? "
            "AND t.constraint_type='PRIMARY KEY' ORDER BY k.ordinal_position", (name,))
        return tuple(row["column_name"] for row in rows)
    rows = list(connection.execute("PRAGMA table_info(" + _quote(name) + ")"))
    return tuple(row["name"] for row in sorted(rows, key=lambda r: r["pk"]) if row["pk"])

def _grants(value):
    try:
        parsed = json.loads(value)
        return (isinstance(parsed, list) and len(parsed) <= 2
                and all(isinstance(x, str) and x in ALLOWED_GRANTS for x in parsed)
                and len(set(parsed)) == len(parsed))
    except (TypeError, ValueError):
        return False

def _text(value):
    return isinstance(value, str) and bool(value.strip())

def _preflight(connection, postgres):
    version = _version(connection, postgres)
    if version:
        return {"version": version, "ready": True}
    rows = {}
    for name, columns in COLUMNS.items():
        if not _exists(connection, name, postgres):
            rows[name] = []
            continue
        if _columns(connection, name, postgres) != columns:
            raise MigrationError(name + ": unexpected columns; explicit preservation review required.")
        if _primary_key(connection, name, postgres) != PRIMARY_KEYS[name]:
            raise MigrationError(name + ": unexpected primary key; preservation review required.")
        if not postgres:
            sql = connection.execute("SELECT sql FROM sqlite_master WHERE name=?", (name,)).fetchone()["sql"]
            if re.search(r"\b(CHECK|STRICT|WITHOUT\s+ROWID)\b", sql, re.I):
                raise MigrationError(name + ": additional schema rules require preservation review.")
            if any(r["origin"] == "u" for r in connection.execute("PRAGMA index_list(" + _quote(name) + ")")):
                raise MigrationError(name + ": additional unique constraints require preservation review.")
            foreign = list(connection.execute("PRAGMA foreign_key_list(" + _quote(name) + ")"))
            expected_session_fk = (name == "shop_auth_sessions" and len(foreign) == 1
                                   and foreign[0]["table"] == "shop_users"
                                   and foreign[0]["from"] == "user_id" and foreign[0]["to"] == "user_id"
                                   and foreign[0]["on_delete"] == "CASCADE"
                                   and foreign[0]["on_update"] == "NO ACTION")
            if foreign and not expected_session_fk:
                raise MigrationError(name + ": additional foreign keys require preservation review.")
        rows[name] = [dict(r) for r in connection.execute("SELECT * FROM " + _quote(name))]
    def reject(name):
        raise MigrationError(name + ": invalid legacy records; migration stopped without repair.")
    users = set()
    for row in rows["shop_users"]:
        if not _text(row["user_id"]): reject("shop_users")
        users.add(row["user_id"])
    shops = set()
    for row in rows["shops"]:
        if (not _text(row["shop_id"]) or row["shop_type"] not in {"keyboard", "bakery"}
                or type(row["practice"]) is not int or row["practice"] not in {0, 1}):
            reject("shops")
        shops.add(row["shop_id"])
    for row in rows["shop_identities"]:
        if not _text(row["provider"]) or not _text(row["subject"]) or row["user_id"] not in users:
            reject("shop_identities")
    members = set()
    for row in rows["shop_memberships"]:
        if (row["user_id"] not in users or row["shop_id"] not in shops
                or row["role"] not in {"owner", "employee"} or not _grants(row["delegated"])
                or type(row["active"]) is not int or row["active"] not in {0, 1}):
            reject("shop_memberships")
        members.add((row["user_id"], row["shop_id"]))
    for row in rows["shop_permission_events"]:
        if (not _text(row["event_id"]) or not _text(row["created_at"])
                or (row["actor_id"], row["shop_id"]) not in members
                or (row["target_id"], row["shop_id"]) not in members
                or not _grants(row["previous_grants"]) or not _grants(row["new_grants"])):
            reject("shop_permission_events")
    for row in rows["shop_auth_sessions"]:
        if (not isinstance(row["token_hash"], str) or re.fullmatch("[0-9a-f]{64}", row["token_hash"]) is None
                or row["user_id"] not in users or type(row["created_at"]) is not int
                or type(row["expires_at"]) is not int or row["created_at"] < 0
                or row["expires_at"] <= row["created_at"]):
            reject("shop_auth_sessions")
    return {"version": 0, "ready": True, "rows": {name: len(values) for name, values in rows.items()}}

def _create_ledger(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS shop_schema_migrations (
        version INTEGER NOT NULL PRIMARY KEY CHECK(version>0),
        name TEXT NOT NULL, checksum TEXT NOT NULL, applied_at TEXT NOT NULL)""")

def _stamp(connection, postgres):
    connection.execute("INSERT INTO shop_schema_migrations VALUES (?, ?, ?, ?)",
                       (VERSION, NAME, _checksum(postgres), datetime.now(timezone.utc).isoformat()))

def _rebuild_sqlite_table(connection, name):
    base, checks, foreign = _schema(False)[name]
    parts = base + ["CHECK(" + condition + ")" for condition in checks] + foreign
    if not _exists(connection, name, False):
        connection.execute("CREATE TABLE " + _quote(name) + " (" + ",".join(parts) + ")")
        return
    temporary = "__smol_v1_" + name
    if _exists(connection, temporary, False):
        raise MigrationError("Migration temporary-table name is already in use.")
    connection.execute("CREATE TABLE " + _quote(temporary) + " (" + ",".join(parts) + ")")
    columns = ",".join(_quote(c) for c in COLUMNS[name])
    connection.execute("INSERT INTO " + _quote(temporary) + " (" + columns + ") SELECT "
                       + columns + " FROM " + _quote(name))
    connection.execute("DROP TABLE " + _quote(name))
    connection.execute("ALTER TABLE " + _quote(temporary) + " RENAME TO " + _quote(name))

def _sqlite_connection(path, readonly=False):
    if readonly:
        c = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, isolation_level=None, timeout=10)
    else:
        c = sqlite3.connect(str(path), isolation_level=None, timeout=10)
    c.row_factory = sqlite3.Row
    return c

def check_sqlite(path):
    if not Path(path).exists():
        return {"version": 0, "ready": True, "new_database": True}
    c = _sqlite_connection(path, readonly=True)
    try:
        c.execute("BEGIN")
        return _preflight(c, False)
    finally:
        c.rollback()
        c.close()

def migrate_sqlite(path):
    c = _sqlite_connection(path)
    try:
        # SQLite's documented create/copy/drop/rename procedure, in one transaction.
        c.execute("PRAGMA foreign_keys=OFF")
        c.execute("BEGIN IMMEDIATE")
        status = _preflight(c, False)
        if status["version"] == VERSION:
            c.commit()
            return VERSION
        saved = [dict(row) for row in c.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE sql IS NOT NULL AND type IN ('index','trigger','view')")]
        indexes = [r for r in saved if r["type"] == "index" and r["tbl_name"] in COLUMNS]
        other = [r for r in saved if r["type"] in {"view", "trigger"}]
        # Temporarily remove dependent SQL objects; restore their exact definitions.
        for row in other:
            c.execute("DROP " + row["type"].upper() + " " + _quote(row["name"]))
        for name in COLUMNS:
            _rebuild_sqlite_table(c, name)
        for row in indexes + other:
            c.execute(row["sql"])
        c.execute("CREATE INDEX IF NOT EXISTS shop_auth_sessions_user ON shop_auth_sessions(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS shop_memberships_shop ON shop_memberships(shop_id,active,user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS shop_permission_events_shop ON shop_permission_events(shop_id,created_at,event_id)")
        if list(c.execute("PRAGMA foreign_key_check")):
            raise MigrationError("Foreign-key validation failed; all migration changes rolled back.")
        _create_ledger(c)
        _stamp(c, False)
        c.commit()
        return VERSION
    except Exception:
        c.rollback()
        raise
    finally:
        c.execute("PRAGMA foreign_keys=ON")
        c.close()

def check_postgres(connection):
    connection.execute("BEGIN TRANSACTION READ ONLY")
    try:
        return _preflight(connection, True)
    finally:
        connection.rollback()

def migrate_postgres(connection):
    """Explicit connection only. Caller chooses a disposable/staged database."""
    connection.execute("BEGIN")
    try:
        connection.execute("SELECT pg_advisory_xact_lock(736614701)")
        existing = [name for name in COLUMNS if _exists(connection, name, True)]
        if existing:
            connection.execute("LOCK TABLE " + ",".join(_quote(n) for n in existing) + " IN ACCESS EXCLUSIVE MODE")
        status = _preflight(connection, True)
        if status["version"] == VERSION:
            connection.commit()
            return VERSION
        for name, (base, checks, foreign) in _schema(True).items():
            connection.execute("CREATE TABLE IF NOT EXISTS " + _quote(name) + " (" + ",".join(base) + ")")
            for col in COLUMNS[name]:
                connection.execute("ALTER TABLE " + _quote(name) + " ALTER COLUMN " + _quote(col) + " SET NOT NULL")
            for number, clause in enumerate(["CHECK(" + x + ")" for x in checks] + foreign):
                constraint = "smol_v1_" + name + "_" + str(number)
                connection.execute("ALTER TABLE " + _quote(name) + " ADD CONSTRAINT "
                                   + _quote(constraint) + " " + clause)
        connection.execute("CREATE INDEX IF NOT EXISTS shop_auth_sessions_user ON shop_auth_sessions(user_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS shop_memberships_shop ON shop_memberships(shop_id,active,user_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS shop_permission_events_shop ON shop_permission_events(shop_id,created_at,event_id)")
        _create_ledger(connection)
        _stamp(connection, True)
        connection.commit()
        return VERSION
    except Exception:
        connection.rollback()
        raise

def main():
    parser = argparse.ArgumentParser(description="Inspect or explicitly migrate shop tables; never load .env.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sqlite", type=Path)
    group.add_argument("--postgres-env", help="Name of a privately configured DSN variable; never pass its value.")
    parser.add_argument("--apply", action="store_true", help="Explicitly apply after backup and preservation review.")
    args = parser.parse_args()
    if args.sqlite:
        result = {"version": migrate_sqlite(args.sqlite)} if args.apply else check_sqlite(args.sqlite)
    else:
        import os
        import psycopg
        from psycopg.rows import dict_row
        from smolstuff.pg_connection import PgConnection
        dsn = os.environ.get(args.postgres_env, "")
        if not dsn:
            parser.error("The selected private DSN variable is not configured.")
        raw = psycopg.connect(dsn, autocommit=True, row_factory=dict_row, connect_timeout=10)
        c = PgConnection(raw)
        try:
            result = {"version": migrate_postgres(c)} if args.apply else check_postgres(c)
        finally:
            c.close()
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
