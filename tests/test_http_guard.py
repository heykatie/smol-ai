from http.server import HTTPServer
from threading import Thread

from smolstuff.http_guard import RequestRejected, read_form
from smolstuff.inbox import make_session_handler
from smolstuff.session_files import expire_demo_sessions


def _header(values):
    def getter(name):
        return values.get(name)
    return getter


def test_bad_content_length_is_rejected():
    try:
        read_form(_header({"Content-Length": "nope", "Host": "127.0.0.1"}), lambda n: b"", "127.0.0.1")
    except RequestRejected as rejected:
        assert rejected.status == 400
    else:
        raise AssertionError("expected a rejection")


def test_oversized_body_is_rejected():
    try:
        read_form(
            _header({"Content-Length": "999999", "Host": "127.0.0.1"}),
            lambda n: b"",
            "127.0.0.1",
        )
    except RequestRejected as rejected:
        assert rejected.status == 413
    else:
        raise AssertionError("expected a rejection")


def test_cross_origin_post_is_refused():
    try:
        read_form(
            _header({
                "Origin": "https://evil.example",
                "Host": "127.0.0.1:8765",
                "Content-Length": "0",
            }),
            lambda n: b"",
            "127.0.0.1:8765",
        )
    except RequestRejected as rejected:
        assert rejected.status == 403
    else:
        raise AssertionError("expected a rejection")


def test_unknown_content_type_is_refused():
    try:
        read_form(
            _header({
                "Content-Type": "application/json",
                "Host": "127.0.0.1",
                "Content-Length": "2",
            }),
            lambda n: b"{}",
            "127.0.0.1",
        )
    except RequestRejected as rejected:
        assert rejected.status == 415
    else:
        raise AssertionError("expected a rejection")


def test_malformed_post_does_not_change_state(tmp_path):
    server = HTTPServer(("127.0.0.1", 0), make_session_handler(str(tmp_path / "sessions")))
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    port = server.server_address[1]
    try:
        from http.client import HTTPConnection

        connection = HTTPConnection("127.0.0.1", port)
        connection.request(
            "POST",
            "/demo",
            "not-a-length",
            {"Content-Length": "nope", "Content-Type": "application/x-www-form-urlencoded"},
        )
        response = connection.getresponse()
        assert response.status == 400
        assert list((tmp_path / "sessions").glob("*.sqlite3")) == []
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_forged_cookie_cannot_skip_the_creation_limit(tmp_path, monkeypatch):
    from http.client import HTTPConnection

    monkeypatch.setenv("SMOL_SESSION_CREATE_LIMIT", "1")
    root = tmp_path / "sessions"
    server = HTTPServer(("127.0.0.1", 0), make_session_handler(str(root)))
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    port = server.server_address[1]
    forged = "c" * 32
    try:
        first = HTTPConnection("127.0.0.1", port)
        first.request("POST", "/demo", "action=simulate_email", {"Content-Type": "application/x-www-form-urlencoded"})
        first_response = first.getresponse()
        assert first_response.status == 303
        first_response.read()
        second = HTTPConnection("127.0.0.1", port)
        second.request(
            "POST",
            "/demo",
            "action=simulate_email",
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": "smol_session={0}".format(forged),
            },
        )
        second_response = second.getresponse()
        assert second_response.status == 429
        second_response.read()
        assert not (root / "{0}.sqlite3".format(forged)).exists()
        sessions = [
            path for path in root.glob("*.sqlite3")
            if len(path.stem) == 32 and path.stem.isalnum()
        ]
        assert len(sessions) == 1
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_scenario_value_cannot_inject_a_response_header(tmp_path):
    from http.client import HTTPConnection

    server = HTTPServer(("127.0.0.1", 0), make_session_handler(str(tmp_path / "sessions")))
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    port = server.server_address[1]
    try:
        connection = HTTPConnection("127.0.0.1", port)
        connection.request(
            "POST",
            "/demo",
            "action=simulate_email&scenario=x%0d%0aX-Injected:%20yes",
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = connection.getresponse()
        response.read()
        assert response.status == 303
        assert response.getheader("X-Injected") is None
        assert response.getheader("Location") == "/demo"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_expired_demo_file_is_removed_and_a_fresh_one_remains(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_DEMO_TTL_SECONDS", "10")
    root = tmp_path / "sessions"
    root.mkdir()
    old = root / ("a" * 32 + ".sqlite3")
    fresh = root / ("b" * 32 + ".sqlite3")
    old.write_text("old")
    fresh.write_text("fresh")
    import os
    old_time = os.path.getmtime(str(fresh)) - 30
    os.utime(str(old), (old_time, old_time))
    assert expire_demo_sessions(str(root)) == 1
    assert not old.exists()
    assert fresh.exists()


def test_localhost_answers_on_ipv4_and_ipv6(tmp_path):
    import socket
    from http.client import HTTPConnection

    from smolstuff.inbox import _serve_loopback

    probe = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        probe.bind(("::1", 0))
    except OSError:
        return
    finally:
        probe.close()
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.bind(("127.0.0.1", 0))
    port = holder.getsockname()[1]
    holder.close()
    thread = Thread(
        target=_serve_loopback,
        args=(make_session_handler(str(tmp_path / "sessions")), port),
        daemon=True,
    )
    thread.start()
    # Server startup happens in another thread; wait for each listener rather
    # than depending on machine scheduling speed.
    import time
    for address in ("127.0.0.1", "::1"):
        deadline = time.monotonic() + 3
        while True:
            try:
                with socket.create_connection((address, port), timeout=0.2):
                    break
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.01)
    for address in ("127.0.0.1", "::1"):
        connection = HTTPConnection(address, port, timeout=2)
        connection.request("GET", "/")
        response = connection.getresponse()
        home = response.read().decode("utf-8")
        assert response.status == 200
        assert "Start demo tour" in home
        connection.close()
        connection = HTTPConnection(address, port, timeout=2)
        connection.request("GET", "/demo")
        response = connection.getresponse()
        page = response.read().decode("utf-8")
        assert response.status == 200
        assert "Daily brief" in page
        connection.close()
