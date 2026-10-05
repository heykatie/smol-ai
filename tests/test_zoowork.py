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


def test_zoowork_explanation_is_evidence_and_the_agent_is_deleted():
    calls = []

    def transport(method, path, body, key):
        calls.append((method, path))
        if method == "POST" and path == "/agents":
            return {"agent_id": "agent-1"}
        if path.endswith("/sessions"):
            return {"summary": "The supplier now needs 35 days. The order is unchanged."}
        return {}

    attempt = explain_supplier_delay("synthetic email", transport=transport, key="test-key")

    assert attempt.provider == "ZooWork"
    assert attempt.status == "live"
    assert attempt.fallback is False
    assert "35 days" in attempt.result
    assert "approval stay in application code" in attempt.effect
    assert ("DELETE", "/agents/agent-1") in calls
