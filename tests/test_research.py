from smolstuff.research import research_supplier


def test_missing_tavily_key_is_a_labeled_fallback(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    attempt = research_supplier()

    assert attempt.provider == "Tavily"
    assert attempt.status == "simulated"
    assert attempt.fallback is True
    assert "https://" not in attempt.result


def test_tavily_sources_are_labeled_live_and_do_not_change_the_order(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "configured")
    payload = {
        "results": [
            {"url": "https://example.com/wholesale-kits"},
            {"url": "https://example.com/lead-times"},
            {"url": "http://insecure.example"},
            {"url": "https://evil.example/tvly-secret"},
        ]
    }

    attempt = research_supplier(transport=lambda query: payload)

    assert attempt.status == "live"
    assert attempt.fallback is False
    assert "https://example.com/wholesale-kits" in attempt.result
    assert "https://example.com/lead-times" in attempt.result
    assert "tvly-" not in attempt.result
    assert "unchanged" in attempt.effect


def test_empty_tavily_results_stay_a_fallback(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "configured")
    attempt = research_supplier(transport=lambda query: {"results": []})

    assert attempt.status == "simulated"
    assert attempt.fallback is True
    assert "https://" not in attempt.result
