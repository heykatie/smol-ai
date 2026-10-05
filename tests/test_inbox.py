from http.server import HTTPServer
from threading import Thread
from urllib.request import Request, urlopen

from smolstuff.inbox import InboxApp, make_handler
from smolstuff.workflow import WorkflowStore


def test_email_opens_one_explained_reorder(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    assert "Start interactive demo" in app.page()

    app.apply("simulate_email")
    app.apply("simulate_email")
    page = app.page()

    assert "about 19 days" in page
    assert "about a 16-day gap" in page
    assert "about 16 days" in page
    assert "19.1" in page
    assert "15.9" in page
    assert "$54 merchandise + $7 shipping = $61 total" in page
    assert "Approve simulated $61 order" in page
    assert "below-$40" in page
    assert "Minimum order: 100 units" in page
    assert "Seeded offer, not a live web check." in page
    assert "Updated lead time for Workshop Supply Pack" in page
    store = WorkflowStore(app.path)
    try:
        assert store.count_workflows() == 1
    finally:
        store.close()


def test_approve_confirms_once_and_refresh_resumes(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    app.apply("simulate_email")
    app.apply("approve")
    app.apply("approve")
    page = InboxApp(app.path).page()

    assert "Order confirmed — awaiting receipt" in page
    assert "Available inventory is still 21." in page
    assert "Replenishment workflow completed" not in page
    assert "Approve simulated $61 order" not in page
    store = WorkflowStore(app.path)
    try:
        assert store.count_executions() == 1
        assert store.count_confirmations() == 1
        assert store.count_movements() == 0
    finally:
        store.close()


def test_decline_submits_nothing(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    app.apply("simulate_email")
    app.apply("decline")
    page = app.page()

    assert "No purchase was submitted." in page
    store = WorkflowStore(app.path)
    try:
        assert store.count_executions() == 0
    finally:
        store.close()


def test_simulated_receipt_reconciles_and_completes(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    app.apply("simulate_email")
    app.apply("approve")
    waiting = app.page()
    assert "Stock has not changed." in waiting

    app.apply("receive_full")
    app.apply("receive_full")
    done = app.page()

    assert "Replenishment workflow completed" in done
    assert "Available inventory updated from 21 to 121." in done
    assert "1 owner approval. Receipt verified. Inventory reconciled." in done
    store = WorkflowStore(app.path)
    try:
        assert store.count_executions() == 1
        assert store.count_movements() == 1
    finally:
        store.close()


def test_short_receipt_stays_open_until_the_rest_arrives(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    app.apply("simulate_email")
    app.apply("approve")
    app.apply("receive_short")
    app.apply("receive_short")
    short = app.page()

    assert "Shortage open" in short
    assert "Received 97 of 100" in short
    assert "not in stock" in short
    assert "No cause was inferred" in short
    assert "118" in short
    assert "Completed" not in short
    store = WorkflowStore(app.path)
    try:
        assert store.count_movements() == 1
    finally:
        store.close()

    app.apply("receive_rest")
    done = app.page()
    assert "Completed" in done
    assert "121" in done
    store = WorkflowStore(app.path)
    try:
        assert store.count_movements() == 2
    finally:
        store.close()


def test_execution_records_do_not_include_secrets_or_sponsor_claims(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    app.apply("simulate_email")
    app.apply("approve")
    app.apply("approve")
    page = app.page()

    assert "Review evidence" in page
    assert "Lead-time parser" in page
    assert "Not a verified live model call" in page
    assert "Purchase demo adapter" in page
    assert "simulated" in page
    assert "replayed" in page
    assert "ZooWork" not in page
    assert "10000" not in page
    assert "API key" not in page
    store = WorkflowStore(app.path)
    try:
        statuses = [event.status for event in store.list_integration_events()]
    finally:
        store.close()
    assert "live" not in statuses
    assert "simulated" in statuses
    assert "replayed" in statuses


def test_visitor_sessions_do_not_share_a_workflow(tmp_path):
    from smolstuff.inbox import make_session_handler

    server = HTTPServer(("127.0.0.1", 0), make_session_handler(str(tmp_path / "sessions")))
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    port = server.server_address[1]
    try:
        first = _session_post(port, "simulate_email")
        second = _session_post(port, "simulate_email")
        _session_post(port, "approve", first)
        first_page = _session_get(port, first)
        second_page = _session_get(port, second)
        assert "Awaiting receipt" in first_page
        assert "Approve simulated $61 order" in second_page
        assert "Awaiting receipt" not in second_page
    finally:
        server.shutdown()
        thread.join(timeout=2)


def _session_post(port: int, action: str, cookie: str = "") -> str:
    from http.client import HTTPConnection

    connection = HTTPConnection("127.0.0.1", port)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if cookie:
        headers["Cookie"] = cookie
    connection.request("POST", "/", "action={0}".format(action), headers)
    response = connection.getresponse()
    response.read()
    set_cookie = response.getheader("Set-Cookie") or ""
    if set_cookie:
        return set_cookie.split(";", 1)[0]
    return cookie


def _session_get(port: int, cookie: str) -> str:
    from http.client import HTTPConnection

    connection = HTTPConnection("127.0.0.1", port)
    connection.request("GET", "/", headers={"Cookie": cookie})
    response = connection.getresponse()
    return response.read().decode("utf-8")


def test_reset_returns_to_the_email_trigger(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    app.apply("simulate_email")
    app.apply("approve")
    app.apply("receive_full")
    app.apply("reset")
    page = app.page()

    assert "Start interactive demo" in page
    assert "121" not in page
    store = WorkflowStore(app.path)
    try:
        assert store.count_workflows() == 0
        assert store.count_movements() == 0
    finally:
        store.close()


def test_server_runs_the_demo_path(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    server = HTTPServer(("127.0.0.1", 0), make_handler(app))
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    port = server.server_address[1]
    try:
        assert "Start interactive demo" in _get(port)
        waiting = _post(port, "simulate_email")
        assert "Approve simulated $61 order" in waiting
        confirmed = _post(port, "approve")
        assert "Awaiting receipt" in confirmed
        assert "Completed" not in confirmed
        replayed = _post(port, "approve")
        assert "Awaiting receipt" in replayed
        done = _post(port, "receive_full")
        assert "Replenishment workflow completed" in done
        reset = _post(port, "reset")
        assert "Start interactive demo" in reset
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_configured_model_stays_on_parser_when_sponsor_calls_are_off(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVITA_API_KEY", "present")
    monkeypatch.delenv("SMOL_SPONSOR_CALLS", raising=False)
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    app.apply("simulate_email")
    page = app.page()
    assert "Sponsor calls are off. Parser read lead time 14 to 35 days." in page
    assert "No live model key is configured" not in page


def _get(port: int) -> str:
    with urlopen("http://127.0.0.1:{0}/".format(port)) as response:
        return response.read().decode("utf-8")


def _post(port: int, action: str) -> str:
    request = Request(
        "http://127.0.0.1:{0}/".format(port),
        data="action={0}".format(action).encode("utf-8"),
        method="POST",
    )
    with urlopen(request) as response:
        return response.read().decode("utf-8")
