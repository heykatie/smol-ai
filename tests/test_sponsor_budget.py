import pytest

from smolstuff.inbox import InboxApp
from smolstuff.sponsor_budget import SponsorBudget
from smolstuff.workflow import WorkflowStore


def test_keys_do_not_place_a_call_when_the_switch_is_off(tmp_path, monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "configured")
    monkeypatch.setenv("NOVITA_API_KEY", "configured")
    monkeypatch.delenv("SMOL_SPONSOR_CALLS", raising=False)

    def forbidden(*args, **kwargs):
        raise AssertionError("outbound call")

    monkeypatch.setattr("smolstuff.extract.call_novita", forbidden)
    monkeypatch.setattr("smolstuff.research._call_tavily", forbidden)
    app = InboxApp(str(tmp_path / "inbox.sqlite3"), session_id="visitor-a", budget_path=str(tmp_path / "budget.sqlite3"))
    app.apply("simulate_email")
    page = app.page()

    assert "Not a verified live model call" in page
    assert "Sponsor calls are off" in page
    assert "Tavily · live" not in page


def test_a_second_start_stops_at_the_session_cap(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.setenv("SMOL_SPONSOR_SESSION_LIMIT", "1")
    monkeypatch.setenv("SMOL_SPONSOR_GLOBAL_LIMIT", "5")
    budget = SponsorBudget(str(tmp_path / "budget.sqlite3"))
    try:
        assert budget.claim("visitor-a") is True
        assert budget.claim("visitor-a") is False
        assert budget.used("visitor-a") == 1
        assert budget.used("global") == 1
    finally:
        budget.close()


def test_sessions_share_one_global_cap(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.setenv("SMOL_SPONSOR_SESSION_LIMIT", "5")
    monkeypatch.setenv("SMOL_SPONSOR_GLOBAL_LIMIT", "1")
    budget = SponsorBudget(str(tmp_path / "budget.sqlite3"))
    try:
        assert budget.claim("visitor-a") is True
        assert budget.claim("visitor-b") is False
    finally:
        budget.close()


def test_missing_limits_block_even_when_the_switch_is_on(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.delenv("SMOL_SPONSOR_SESSION_LIMIT", raising=False)
    monkeypatch.delenv("SMOL_SPONSOR_GLOBAL_LIMIT", raising=False)
    budget = SponsorBudget(str(tmp_path / "budget.sqlite3"))
    try:
        assert budget.claim("visitor-a") is False
        assert budget.used("global") == 0
    finally:
        budget.close()


def test_replayed_email_does_not_consume_another_call(tmp_path, monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "configured")
    monkeypatch.setenv("NOVITA_API_KEY", "configured")
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.setenv("SMOL_SPONSOR_SESSION_LIMIT", "10")
    monkeypatch.setenv("SMOL_SPONSOR_GLOBAL_LIMIT", "10")
    calls = {"n": 0}

    def count_call(*args, **kwargs):
        from urllib.error import URLError

        calls["n"] += 1
        raise URLError("stop before the network")

    monkeypatch.setattr("smolstuff.extract.call_novita", count_call)
    monkeypatch.setattr("smolstuff.research._call_tavily", count_call)
    app = InboxApp(str(tmp_path / "inbox.sqlite3"), session_id="visitor-a", budget_path=str(tmp_path / "budget.sqlite3"))
    app.apply("simulate_email")
    app.apply("simulate_email")

    assert calls["n"] == 2
    assert "No new model call was made." in app.page()


def test_separate_session_files_share_one_global_budget(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.setenv("SMOL_SPONSOR_SESSION_LIMIT", "5")
    monkeypatch.setenv("SMOL_SPONSOR_GLOBAL_LIMIT", "1")
    monkeypatch.setenv("NOVITA_API_KEY", "configured")
    calls = {"n": 0}

    def count_call(*args, **kwargs):
        from urllib.error import URLError

        calls["n"] += 1
        raise URLError("stop before the network")

    monkeypatch.setattr("smolstuff.extract.call_novita", count_call)
    first = InboxApp(str(tmp_path / "a.sqlite3"), session_id="a" * 32)
    second = InboxApp(str(tmp_path / "b.sqlite3"), session_id="b" * 32)
    first.apply("simulate_email")
    second.apply("simulate_email")
    assert calls["n"] == 1
    assert first.budget_path == second.budget_path
