# Shop schema migrations

Version 1 adds database integrity for shop users, provider identities, shops, memberships, permission audit events and authentication sessions. It does not migrate the anonymous workflow tables, connector snapshot harness or private shop workflows.

The migration is explicit: store/session constructors no longer create these tables. Opening an unmigrated database raises MigrationRequired rather than silently upgrading it. SQLite application connections enable foreign-key enforcement. The PostgreSQL path uses the existing connection wrapper and the same database; no additional database product is introduced.

## Version 1 rules

- Identity user IDs reference existing application users; provider/subject remains the identity key.
- Memberships reference existing users and shops. Roles are owner/employee, active/practice flags are 0 or 1, and shop types are keyboard/bakery.
- Delegation fields and audit before/after values must be JSON arrays containing only correction/spending approval grants, with no duplicates. JSON whitespace and either valid ordering remain accepted.
- Audit actor and target must belong to the recorded shop. Historical membership rows are retained; deactivate rather than delete referenced memberships. No audit history is automatically cascaded away.
- Session hashes reference users, contain exactly 64 lowercase hexadecimal characters, and have nonnegative creation time and a later expiry time.
- IDs and required text cannot be null/empty. Existing application-owned IDs, roles, delegation strings, audit strings, timestamps and session values are copied unchanged.
- The version/name/backend-specific schema checksum is recorded in shop_schema_migrations. Unsupported/newer or inconsistent migration history is refused; a checksum ledger is not a tamper-evident security boundary.

These constraints cannot replace current membership authorization in domain services and routes. They do not enable login, external messages, purchases or new permissions.

## Preservation and failure behavior

Read-only preflight inspects schema and checks legacy records without creating or rewriting a database. Invalid/orphaned rows block migration. Errors identify the affected table/reason, not provider subjects or row values. No record is removed, reclassified or granted authority to make migration pass.

Unexpected legacy columns or primary keys require an explicit preservation review. SQLite additional inline checks, inline unique constraints or unexpected foreign keys also stop rather than being silently removed. Existing custom indexes, triggers and views are restored with their definitions unchanged; unrelated tables/data are retained.

SQLite uses a create/copy/drop/rename sequence inside BEGIN IMMEDIATE, validates foreign keys and stamps only after successful completion. This follows [SQLite's table-change guidance](https://www.sqlite.org/lang_altertable.html); foreign-key enforcement is connection-specific as described in [SQLite's foreign-key documentation](https://www.sqlite.org/foreignkeys.html).

Postgres uses native constraint changes in a transaction, a transaction-scoped advisory migration lock and exclusive locks on existing affected tables before validation. Concurrent migration calls result in a single recorded version. Existing indexes/extra constraints are retained. See [Postgres constraints](https://www.postgresql.org/docs/current/ddl-constraints.html).

A failure rolls back schema/data/version changes. Tests inject interruptions after SQLite table replacement and after Postgres constraint changes, then verify legacy records/schema remain intact. This verifies failed-migration rollback, not an automatic downgrade after a successful release. Future schema changes need a new reviewed migration; do not edit version 1 in place.

## Maintenance sequence

1. Stop relevant writers and obtain a restorable backup before applying to an existing database. Review retention/recovery requirements before using private records. No automated backup/restore service is added here.
2. Run read-only preflight. If blocked, preserve the database and review the reported table; choose an explicit repair with the owner rather than deleting rows.
3. Apply first to a disposable/restored copy and verify records and application behavior.
4. Apply to the intended database only under its deployment approval, then verify version, constraints and record counts. Coordinate application rollout because this code requires version 1.
5. Keep the backup and migration evidence. Do not downgrade constraints or modify historical migration records to bypass a failure.

This work inspected six SQLite files under the repository's local data directory; none had membership tables. **No existing app database or Neon database was migrated.** All applied migrations during verification used synthetic disposable databases.

## Local command interface

The CLI never loads .env. Inspection is the default; --apply is required for writes. Use a stable account database outside the anonymous data/sessions directory.

From the repository root, inspect a proposed local path:

```sh
PYTHONPATH=src .venv/bin/python -m smolstuff.shop_migrations --sqlite data/shop-accounts.sqlite3
```

After backup/preservation review and a successful disposable-copy check:

```sh
PYTHONPATH=src .venv/bin/python -m smolstuff.shop_migrations --sqlite data/shop-accounts.sqlite3 --apply
```

For Postgres, a maintainer may select a privately configured DSN variable using --postgres-env VARIABLE_NAME; never pass its secret value in a command or documentation. Inspection remains read-only, and --apply remains explicit. Do not reuse a production connection for automated tests. No production DSN was selected in this work.

MembershipStore(path) now requires prior migrate_sqlite(path), or the explicit Postgres migration against the selected connection. AuthSessions reuses that migrated store and performs no schema DDL.

## Verification — 2026-10-06

- Migration-specific checks: 51 passed across SQLite and a disposable local PostgreSQL 14.15 cluster, including direct-write rejection, exact legacy preservation, invalid-data refusal, custom SQL-object preservation, interrupted rollback, read-only inspection and concurrent migration replay.
- Existing membership/session behavior remains covered.
- Full offline and disposable-Postgres suite: final result recorded in [STATUS.md](STATUS.md).
- The project virtual environment now has the declared psycopg binary dependency available after updating its old pip. This is a local tooling repair, not a hosting change.
- No UI changed; no browser or live identity verification was claimed. Neon version, production data, staged rollout, backups and restored-production-copy checks remain unverified.
