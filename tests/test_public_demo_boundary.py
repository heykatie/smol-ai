"""Public demo stays offline even when private sponsor configuration exists."""
import io
import pytest
from app import app
from smolstuff.inbox import InboxApp

@pytest.mark.parametrize("provider", ["novita", "groq_gemini_parser", "groq_openrouter_parser"])
def test_public_demo_never_claims_budget_or_calls_provider(tmp_path, monkeypatch, provider):
    from smolstuff import extract, extraction_chain, research, zoowork
    from smolstuff.sponsor_budget import SponsorBudget
    calls = []
    def forbidden(*args, **kwargs):
        calls.append("external")
        raise AssertionError("Public demo attempted external execution")
    for module, name in [(extract, "call_novita"), (extraction_chain, "call_groq"),
                         (extraction_chain, "call_gemini"), (extraction_chain, "call_openrouter"),
                         (research, "research_supplier"), (zoowork, "explain_supplier_delay")]:
        monkeypatch.setattr(module, name, forbidden)
    monkeypatch.setattr(SponsorBudget, "claim", forbidden)
    for key in ["NOVITA_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY",
                "OPENROUTER_API_KEY", "TAVILY_API_KEY", "ZOOWORK_API_KEY", "ZOOWORK_AGENT_ID"]:
        monkeypatch.setenv(key, "fictional-test-placeholder")
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.setenv("SMOL_SPONSOR_SESSION_LIMIT", "100")
    monkeypatch.setenv("SMOL_SPONSOR_GLOBAL_LIMIT", "100")
    monkeypatch.setenv("SMOL_EXTRACTION_PROVIDER", provider)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    root = tmp_path / "sessions"
    monkeypatch.setenv("SMOL_SESSIONS", str(root))
    captured = {}
    raw = b"action=simulate_email"
    def start_response(status, headers):
        captured.update(status=status, headers=dict(headers))
    app({"REQUEST_METHOD": "POST", "PATH_INFO": "/demo", "HTTP_HOST": "localhost",
         "CONTENT_TYPE": "application/x-www-form-urlencoded", "CONTENT_LENGTH": str(len(raw)),
         "wsgi.input": io.BytesIO(raw)}, start_response)
    assert captured["status"].startswith("303")
    assert calls == []
    assert not (root / "sponsor-budget.sqlite3").exists()
    session = captured["headers"]["Set-Cookie"].split("=", 1)[1].split(";", 1)[0]
    from smolstuff.workflow import WorkflowStore
    store = WorkflowStore(str(root / (session + ".sqlite3")), session_id=session)
    try:
        events = store.list_integration_events()
        assert any(event.provider == "Lead-time parser" for event in events)
        assert all(event.status != "live" for event in events)
    finally:
        store.close()

def test_public_inbox_cannot_claim_sponsor_budget(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOL_SPONSOR_CALLS", "1")
    monkeypatch.setenv("SMOL_SPONSOR_SESSION_LIMIT", "100")
    monkeypatch.setenv("SMOL_SPONSOR_GLOBAL_LIMIT", "100")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    inbox = InboxApp(str(tmp_path / "demo.sqlite3"))
    assert inbox._claim_sponsor_call() is False
    assert not (tmp_path / "sponsor-budget.sqlite3").exists()
