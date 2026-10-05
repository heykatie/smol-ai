"""Anonymous demo session files. This expiry is not business-record retention."""

from __future__ import annotations

import os
import re
import sqlite3
import time
from pathlib import Path

_SESSION_FILE = re.compile(r"^[a-f0-9]{32}\.sqlite3$")


class SessionLimited(Exception):
    """The anonymous creation window is full."""


def demo_ttl_seconds() -> int:
    raw = os.environ.get("SMOL_DEMO_TTL_SECONDS", "86400").strip()
    try:
        value = int(raw)
    except ValueError:
        return 86400
    if value < 1:
        return 86400
    return value


def expire_demo_sessions(directory: str, now: float = None) -> int:
    """Delete demo session files and Postgres rows older than the anonymous TTL.

    Returns how many local files plus Postgres session ids were removed.
    """
    root = Path(directory)
    moment = time.time() if now is None else now
    ttl = demo_ttl_seconds()
    removed = 0
    if root.exists():
        for path in root.glob("*.sqlite3"):
            if not _SESSION_FILE.match(path.name):
                continue
            if moment - path.stat().st_mtime > ttl:
                path.unlink()
                removed += 1
    from smolstuff.database import expire_persisted_sessions

    removed += expire_persisted_sessions(now=moment)
    return removed


def reserve_session(directory: str, now: float = None) -> bool:
    """Record one new anonymous session, or refuse when the window is full."""
    limit = _positive("SMOL_SESSION_CREATE_LIMIT", 100)
    window = _positive("SMOL_SESSION_CREATE_WINDOW_SECONDS", 3600)
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    moment = time.time() if now is None else now
    store = sqlite3.connect(str(root.parent / "session-creations.sqlite3"))
    store.isolation_level = None
    try:
        store.execute("CREATE TABLE IF NOT EXISTS creations (created_at REAL NOT NULL)")
        store.execute("BEGIN IMMEDIATE")
        try:
            store.execute("DELETE FROM creations WHERE created_at < ?", (moment - window,))
            used = int(store.execute("SELECT COUNT(*) FROM creations").fetchone()[0])
            if used >= limit:
                store.commit()
                return False
            store.execute("INSERT INTO creations (created_at) VALUES (?)", (moment,))
            store.commit()
            return True
        except Exception:
            store.rollback()
            raise
    finally:
        store.close()


def _positive(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if value < 1:
        return default
    return value
