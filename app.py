"""WSGI entry point for Vercel.

Local development still uses `python -m smolstuff.inbox`.
Workflow and preview rows use Postgres when DATABASE_URL is configured,
otherwise SQLite. Local session markers and sponsor counters remain temporary
files on Vercel. See docs/STATUS.md for recorded hosted checks and their limits.
"""

import os
import sys
from decimal import InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from smolstuff.demo_ui import SANDBOX_PREFIX, error_page, product_home_page
from smolstuff.http_guard import MAX_BODY_BYTES, RequestRejected, read_form
from smolstuff.inbox import (
    InboxApp,
    _blank_scenario,
    _load_local_env,
    _scenario_location,
    _session_cookie,
    open_session,
)
from smolstuff.session_files import SessionLimited, expire_demo_sessions


def _sessions_directory() -> str:
    if os.environ.get("VERCEL") == "1":
        directory = os.environ.get("SMOL_SESSIONS", "/tmp/smol-sessions")
    else:
        directory = os.environ.get(
            "SMOL_SESSIONS",
            str(Path(__file__).resolve().parent / "data" / "sessions"),
        )
    Path(directory).mkdir(parents=True, exist_ok=True)
    return directory


def app(environ, start_response):
    _load_local_env()
    directory = _sessions_directory()
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/") or "/"
    headers = {
        key[5:].replace("_", "-").title(): value
        for key, value in environ.items()
        if key.startswith("HTTP_")
    }
    headers["Content-Type"] = environ.get("CONTENT_TYPE", "")
    headers["Content-Length"] = environ.get("CONTENT_LENGTH", "")
    host = environ.get("HTTP_HOST", "")

    def header(name):
        return headers.get(name)

    if path == "/":
        if method != "GET":
            start_response("405 Method Not Allowed", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"Method not allowed"]
        encoded = product_home_page().encode("utf-8")
        start_response(
            "200 OK",
            [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(encoded))),
            ],
        )
        return [encoded]

    if path != SANDBOX_PREFIX:
        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Not found"]

    if method == "GET":
        expire_demo_sessions(directory)
        from urllib.parse import parse_qs

        scenario = parse_qs(environ.get("QUERY_STRING", "")).get("scenario", ["home"])[0]
        session_id = _cookie_session(headers.get("Cookie", ""))
        body = _page(directory, session_id, scenario)
        encoded = body.encode("utf-8")
        start_response(
            "200 OK",
            [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(encoded))),
            ],
        )
        return [encoded]

    if method != "POST":
        start_response("405 Method Not Allowed", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Method not allowed"]

    expire_demo_sessions(directory)
    try:
        length = int(environ.get("CONTENT_LENGTH") or "0")
    except ValueError:
        length = -1
    if length > MAX_BODY_BYTES:
        start_response("413 Payload Too Large", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Request body is too large."]
    raw = environ["wsgi.input"].read(length if length > 0 else 0)

    def read(_length):
        return raw

    try:
        fields = read_form(header, read, host)
    except RequestRejected as rejected:
        encoded = rejected.message.encode("utf-8")
        start_response(
            "{0} Error".format(rejected.status),
            [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(encoded)))],
        )
        return [encoded]

    try:
        session_id, new_cookie = open_session(directory, headers.get("Cookie", ""))
    except SessionLimited:
        start_response("429 Too Many Requests", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Too many new demos. Try again later."]
    action = fields.get("action", [""])[0]
    try:
        scenario = InboxApp(
            str(Path(directory) / "{0}.sqlite3".format(session_id)),
            session_id=session_id,
        ).route(action, fields)
    except (ValueError, InvalidOperation):
        encoded = error_page().encode("utf-8")
        start_response(
            "400 Bad Request",
            [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(encoded)))],
        )
        return [encoded]
    response_headers = [("Location", _scenario_location(scenario))]
    if new_cookie:
        response_headers.append(("Set-Cookie", _session_cookie(session_id)))
    start_response("303 See Other", response_headers)
    return [b""]


def _cookie_session(cookie_header: str):
    from smolstuff.inbox import _read_session

    return _read_session(cookie_header)


def _page(directory: str, session_id, scenario: str) -> str:
    from smolstuff.database import persisted_session

    if session_id is None:
        return _blank_scenario(scenario)
    path = Path(directory) / "{0}.sqlite3".format(session_id)
    if not path.is_file() and not persisted_session(session_id):
        return _blank_scenario(scenario)
    return InboxApp(str(path), session_id=session_id).view(scenario)
