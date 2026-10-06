import io

import pytest

from app import app


def test_wsgi_root_serves_product_home_and_try_serves_sandbox(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SESSIONS", str(tmp_path / "sessions"))
    monkeypatch.delenv("SMOL_SPONSOR_CALLS", raising=False)

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    captured = {}
    home = b"".join(
        app(
            {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "/",
                "QUERY_STRING": "",
                "HTTP_HOST": "127.0.0.1",
                "wsgi.input": io.BytesIO(b""),
            },
            start_response,
        )
    ).decode()
    assert captured["status"].startswith("200")
    assert "Start demo tour" in home
    assert "Practice owner" in home
    assert "492" in home
    assert "Sign in is not available" in home

    captured.clear()
    sandbox = b"".join(
        app(
            {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "/try",
                "QUERY_STRING": "",
                "HTTP_HOST": "127.0.0.1",
                "wsgi.input": io.BytesIO(b""),
            },
            start_response,
        )
    ).decode()
    assert captured["status"].startswith("200")
    assert "Demo tour" in sandbox
    assert 'action="/try"' in sandbox
    assert "specialty-shop assortment (~492" not in sandbox


def test_wsgi_post_sets_a_session_cookie(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SESSIONS", str(tmp_path / "sessions"))
    monkeypatch.delenv("SMOL_SPONSOR_CALLS", raising=False)
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/try",
        "QUERY_STRING": "",
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": "26",
        "HTTP_HOST": "127.0.0.1",
        "wsgi.input": io.BytesIO(b"action=simulate_email"),
    }
    body = b"".join(app(environ, start_response))
    assert captured["status"].startswith("303")
    cookie = dict(captured["headers"]).get("Set-Cookie", "")
    assert cookie.startswith("smol_session=")
    assert "HttpOnly" in cookie
    assert body == b""


def test_wsgi_rejects_an_oversized_length_before_reading_the_body():
    from smolstuff.http_guard import MAX_BODY_BYTES

    captured = {}
    read_sizes = []

    class Reader:
        def read(self, size):
            read_sizes.append(size)
            return b""

    def start_response(status, headers):
        captured["status"] = status

    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/try",
        "QUERY_STRING": "",
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": str(MAX_BODY_BYTES + 1),
        "HTTP_HOST": "127.0.0.1",
        "wsgi.input": Reader(),
    }
    app(environ, start_response)
    assert captured["status"].startswith("413")
    assert read_sizes == []


@pytest.mark.parametrize("scenario,action,valid,invalid", [
    ("staffing", "staffing_calculate", {"day": ["saturday"], "owner_hours": ["6"]}, {"owner_hours": "not-a-number"}),
    ("rescue", "rescue_offers", {"selling_price": ["150"]}, {"selling_price": "not-a-number"}),
    ("workshop", "workshop_check", {"attendees": ["20"], "days_until": ["7"]}, {"attendees": "not-a-number"}),
])
def test_wsgi_invalid_input_returns_recoverable_error_and_preserves_saved_result(tmp_path, monkeypatch, scenario, action, valid, invalid):
    from urllib.parse import urlencode
    from smolstuff.inbox import InboxApp
    from smolstuff.ops_demos import ScenarioStore

    root = tmp_path / "sessions"
    root.mkdir()
    monkeypatch.setenv("SMOL_SESSIONS", str(root))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    session = "a" * 32
    path = str(root / (session + ".sqlite3"))
    InboxApp(path, session_id=session).route(action, dict(valid, scenario=[scenario]))
    store = ScenarioStore(path, session)
    try:
        before = store.get(scenario)
    finally:
        store.close()
    raw = urlencode(dict(invalid, action=action, scenario=scenario)).encode()
    captured = {}

    def start_response(status, headers):
        captured.update(status=status, headers=dict(headers))

    body = b"".join(app({
        "REQUEST_METHOD": "POST", "PATH_INFO": "/try", "HTTP_HOST": "localhost",
        "HTTP_COOKIE": "smol_session=" + session,
        "CONTENT_TYPE": "application/x-www-form-urlencoded", "CONTENT_LENGTH": str(len(raw)),
        "wsgi.input": io.BytesIO(raw),
    }, start_response)).decode()
    assert captured["status"] == "400 Bad Request"
    assert captured["headers"]["Content-Type"].startswith("text/html")
    assert 'role="alert"' in body
    assert "Back to sandbox" in body
    store = ScenarioStore(path, session)
    try:
        assert store.get(scenario) == before
    finally:
        store.close()
