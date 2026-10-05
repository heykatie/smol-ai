import io

from app import app


def test_wsgi_post_sets_a_session_cookie(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SESSIONS", str(tmp_path / "sessions"))
    monkeypatch.delenv("SMOL_SPONSOR_CALLS", raising=False)
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/",
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
        "PATH_INFO": "/",
        "QUERY_STRING": "",
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": str(MAX_BODY_BYTES + 1),
        "HTTP_HOST": "127.0.0.1",
        "wsgi.input": Reader(),
    }
    app(environ, start_response)
    assert captured["status"].startswith("413")
    assert read_sizes == []
