from smolstuff.zoowork import explain_supplier_delay


def test_missing_zoowork_key_does_not_call():
    calls = []

    def transport(method, path, body, key):
        calls.append(method)
        return {}

    attempt = explain_supplier_delay("synthetic email", transport=transport, key="")

    assert calls == []
    assert attempt.status == "simulated"
    assert attempt.fallback is True


def test_missing_zoowork_agent_does_not_call():
    calls = []

    def transport(method, path, body, key):
        calls.append(method)
        return {}

    attempt = explain_supplier_delay(
        "synthetic email", transport=transport, key="test-key", agent_id=""
    )

    assert calls == []
    assert attempt.status == "simulated"
    assert attempt.fallback is True


def test_zoowork_uses_the_configured_agent_and_does_not_delete_it():
    calls = []

    def transport(method, path, body, key):
        calls.append((method, path))
        if path.endswith("/sessions"):
            return {"summary": "The supplier now needs 35 days. The order is unchanged."}
        return {}

    attempt = explain_supplier_delay(
        "synthetic email", transport=transport, key="test-key", agent_id="agent-1"
    )

    assert attempt.provider == "ZooWork"
    assert attempt.status == "live"
    assert attempt.fallback is False
    assert "35 days" in attempt.result
    assert ("POST", "/agents") not in calls
    assert ("DELETE", "/agents/agent-1") not in calls
    assert ("POST", "/agents/agent-1/start") in calls
