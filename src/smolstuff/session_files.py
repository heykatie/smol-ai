"""Anonymous demo session files. This expiry is not business-record retention."""

from __future__ import annotations

import os
import time
from pathlib import Path


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
    """Delete demo session files older than the anonymous TTL. Returns how many were removed."""
    root = Path(directory)
    if not root.exists():
        return 0
    moment = time.time() if now is None else now
    ttl = demo_ttl_seconds()
    removed = 0
    for path in root.glob("*.sqlite3"):
        if moment - path.stat().st_mtime > ttl:
            path.unlink()
            removed += 1
    return removed


def creation_allowed(directory: str, now: float = None) -> bool:
    """Limit how many new anonymous sessions can be minted in the window."""
    limit = _positive("SMOL_SESSION_CREATE_LIMIT", 100)
    window = _positive("SMOL_SESSION_CREATE_WINDOW_SECONDS", 3600)
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    moment = time.time() if now is None else now
    recent = 0
    for path in root.glob("*.sqlite3"):
        if moment - path.stat().st_mtime <= window:
            recent += 1
    return recent < limit


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
