from http.server import HTTPServer
from threading import Thread
from urllib.request import Request, urlopen

from reorder_path import advance_reorder
from smolstuff.inbox import InboxApp, make_handler
from smolstuff.workflow import WorkflowStore


def test_email_opens_one_explained_reorder(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    empty = app.page()
    assert "Start interactive demo" in empty
    assert "Demo tour." in empty
    assert "decision-card" in empty

    app.apply("simulate_email")
    app.apply("simulate_email")
    page = app.page()

    assert "about 19 days" in page
    assert "about a 16-day gap" in page
    assert "about 16 days" in page
    assert "19.1" in page
    assert "15.9" in page
    assert "$182 merchandise + $7 shipping = $189 total" in page
    assert "Review the purchase packet" in page
    assert "Continue to terms" in page
    assert "Approve simulated $189 order" not in page
    assert "decision-actions" in page
    assert "Why this recommendation" in page
    assert "Demo tour." in page
    assert "below-$40" in page
    assert "Minimum order: 100 units" in page
    assert "Seeded offer, not a live web check." in page
    assert "Updated lead time for Quiet linear switch" in page
    assert page.index("Continue to terms") < page.index("Review evidence")
    store = WorkflowStore(app.path)
    try:
        assert store.count_workflows() == 1
    finally:
        store.close()


def test_prep_then_approve_does_not_submit_until_confirm(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    advance_reorder(app, through="approve")
    app.apply("approve")
    page = InboxApp(app.path).page()

    assert "Approved — submit the practice order" in page
    assert "Submit simulated order" in page
    assert "Order confirmed — awaiting receipt" not in page
    assert "Available inventory is still 21." in page or "Stock stays 21" in page
    store = WorkflowStore(app.path)
    try:
        assert store.count_executions() == 0
        assert store.count_confirmations() == 0
        assert store.count_movements() == 0
    finally:
        store.close()

    app.apply("submit_order")
    app.apply("submit_order")
    submitted = app.page()
    assert "Confirm supplier match" in submitted
    assert "Awaiting receipt" not in submitted

    app.apply("confirm")
    app.apply("confirm")
    waiting = InboxApp(app.path).page()
    assert "Order confirmed — awaiting receipt" in waiting
    assert "View confirmation" in waiting
    assert "Purchase receipt" in waiting
    assert 'href="#confirmation"' in waiting
    assert "View Quiet linear switch in inventory" not in waiting
    store = WorkflowStore(app.path)
    try:
        assert store.count_executions() == 1
        assert store.count_confirmations() == 1
        assert store.count_movements() == 0
    finally:
        store.close()


def test_negotiate_counter_holds_seeded_total(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    app.apply("simulate_email")
    app.apply("review_continue")
    app.apply("negotiate_counter", {"counter_price": ["150"]})
    page = app.page()

    assert "held" in page.lower() or "Held" in page
    assert "$189" in page
    assert "Accept $189 terms" in page
    app.apply("negotiate_accept")
    app.apply("draft_send")
    ready = app.page()
    assert "Approve simulated $189 order" in ready


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
    advance_reorder(app, through="confirm")
    waiting = app.page()
    assert "Stock has not changed." in waiting

    app.apply("receive_full")
    app.apply("receive_full")
    done = app.page()

    assert "Replenishment workflow completed" in done
    assert "Available inventory updated from 21 to 121." in done
    assert "1 owner approval. Simulated receipt recorded. Inventory reconciled." in done
    assert "View Quiet linear switch in inventory" in done
    assert "scenario=inventory" in done and "DEMO-ITM-001" in done
    store = WorkflowStore(app.path)
    try:
        assert store.count_executions() == 1
        assert store.count_movements() == 1
    finally:
        store.close()


def test_short_receipt_stays_open_until_the_rest_arrives(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    advance_reorder(app, through="confirm")
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


def test_daily_brief_is_guided_launcher(tmp_path):
    home = InboxApp(str(tmp_path / "inbox.sqlite3")).view("home")

    assert "Demo tour" in home
    assert "Start here. Follow one decision through." in home
    assert "launch-primary" in home
    assert "Open reorder →" in home
    assert "Best place to start" in home
    assert "More practice demos" in home
    assert "Save today’s walk-in sale" in home or "Save today's walk-in sale" in home
    assert "Two merchant simulators" not in home
    assert "Tool activity this session" in home
    assert "What ran" not in home
    assert 'id="inventory-attention"' in home
    assert "catalog lines need a look" in home
    assert (
        "/demo?scenario=inventory&view=attention" in home
        or "/demo?scenario=inventory&amp;view=attention" in home
    )
    assert "Demo tour." in home


def test_preview_loops_share_banner_and_decision_first_copy(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    for scenario in ("workshop", "detective", "rescue", "staffing"):
        page = app.view(scenario)
        assert "Demo tour." in page
        assert "decision-hero" in page
        assert "decision-card" in page

    app.route(
        "workshop_check",
        {"scenario": ["workshop"], "attendees": ["20"], "days_until": ["7"]},
    )
    workshop = app.view("workshop")
    assert "Expected contribution: $700" in workshop
    assert "Buy 10 bottleneck switch packs" in workshop
    assert "Why this recommendation" in workshop

    app.route(
        "detective_check",
        {"scenario": ["detective"], "physical_count": ["16"]},
    )
    detective = app.view("detective")
    assert "Needs evidence" in detective
    assert "Confirm workshop consumption" in detective

    app.route(
        "staffing_calculate",
        {
            "scenario": ["staffing"],
            "day": ["saturday"],
            "owner_hours": ["6"],
            "workshop": ["1"],
        },
    )
    staffing = app.view("staffing")
    assert "Workload hours: 14" in staffing
    assert "Plan 2 extra four-hour coverage blocks" in staffing


def test_inventory_needs_attention_links_to_daily_brief(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    assert 'href="/demo#inventory-attention"' in page
    assert "needs attention" in page
    assert 'data-attention="1"' in page
    assert 'id="attention-filter-note"' in page
    assert "params.get(\"view\") === \"attention\"" in page


def test_execution_records_do_not_include_secrets_or_sponsor_claims(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    advance_reorder(app, through="submit_order")
    app.apply("submit_order")
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
        for action in (
            "review_continue",
            "negotiate_accept",
            "draft_send",
            "approve",
            "submit_order",
            "confirm",
        ):
            _session_post(port, action, first)
        first_page = _session_get(port, first)
        second_page = _session_get(port, second)
        assert "Awaiting receipt" in first_page
        assert "Review the $189 decision" in second_page
        assert "Approve simulated $189 order" not in second_page
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
    connection.request("POST", "/demo", "action={0}".format(action), headers)
    response = connection.getresponse()
    response.read()
    set_cookie = response.getheader("Set-Cookie") or ""
    if set_cookie:
        return set_cookie.split(";", 1)[0]
    return cookie


def _session_get(port: int, cookie: str) -> str:
    from http.client import HTTPConnection

    connection = HTTPConnection("127.0.0.1", port)
    connection.request("GET", "/demo", headers={"Cookie": cookie})
    response = connection.getresponse()
    return response.read().decode("utf-8")


def test_reset_returns_to_the_email_trigger(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    advance_reorder(app, through="receive_full")
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
        review = _post(port, "simulate_email")
        assert "Continue to terms" in review
        assert "Approve simulated $189 order" not in review
        negotiate = _post(port, "review_continue")
        assert "Accept $189 terms" in negotiate
        draft = _post(port, "negotiate_accept")
        assert "Send simulated draft" in draft
        ready = _post(port, "draft_send")
        assert "Approve simulated $189 order" in ready
        approved = _post(port, "approve")
        assert "Submit simulated order" in approved
        assert "Awaiting receipt" not in approved
        submitted = _post(port, "submit_order")
        assert "Confirm supplier match" in submitted
        confirmed = _post(port, "confirm")
        assert "Awaiting receipt" in confirmed
        assert "Completed" not in confirmed
        replayed = _post(port, "confirm")
        assert "Awaiting receipt" in replayed
        done = _post(port, "receive_full")
        assert "Replenishment workflow completed" in done
        assert "View Quiet linear switch in inventory" in done
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
    with urlopen("http://127.0.0.1:{0}/demo".format(port)) as response:
        return response.read().decode("utf-8")


def _post(port: int, action: str) -> str:
    request = Request(
        "http://127.0.0.1:{0}/demo".format(port),
        data="action={0}".format(action).encode("utf-8"),
        method="POST",
    )
    with urlopen(request) as response:
        return response.read().decode("utf-8")


def test_supplier_sources_are_accessible_disclosures(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "0")
    app = InboxApp(str(tmp_path / "sources.sqlite3"))
    app.apply("simulate_email")
    page = app.page()
    assert "<summary>View supplier message</summary>" in page
    assert "<summary>View supplier offer</summary>" in page
    assert "Fictional supplier message" in page
    assert "Seeded offer, not a live web check." in page
    assert "Read by the local parser fallback" in page
    assert page.index("View supplier message") < page.index("Why this recommendation")
    assert "$189" in page


def test_healthy_result_persists_without_purchase_and_replays_without_extraction(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from smolstuff.extract import LeadTimeFact
    from smolstuff.fixtures import SUPPLIER_A_ID, WORKSHOP_SKU
    calls = []
    def extract(self, store=None):
        calls.append("extract")
        return SimpleNamespace(fact=LeadTimeFact(SUPPLIER_A_ID, WORKSHOP_SKU, 14, 1),
                               provider="Lead-time parser", result="Synthetic healthy stock check.",
                               status="simulated")
    monkeypatch.setattr(InboxApp, "_extract_supplier_fact", extract)
    def unexpected(self, *args):
        raise AssertionError("Healthy stock must not research or explain a purchase.")
    monkeypatch.setattr(InboxApp, "_record_supplier_research", unexpected)
    monkeypatch.setattr(InboxApp, "_record_zoowork", unexpected)
    app = InboxApp(str(tmp_path / "healthy.sqlite3"), session_id="healthy")
    app.apply("simulate_email")
    app.apply("simulate_email")
    for action in ("review_continue", "approve", "submit_order", "confirm", "receive_full"):
        app.apply(action)
    page = InboxApp(app.path, session_id="healthy").page()
    assert "No reorder needed" in page
    assert "Available inventory is still 21" in page
    assert 'value="approve"' not in page
    assert "No reorder needed" in app.view("home")
    assert calls == ["extract"]
    store = WorkflowStore(app.path, session_id="healthy")
    try:
        assert store.count_workflows() == store.count_approvals() == store.count_executions() == store.count_movements() == 0
    finally:
        store.close()
    app.apply("reset")
    assert "Start interactive demo" in app.page()
