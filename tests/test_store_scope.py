from smolstuff.fixtures import EXAMPLE_POLICY, NEEDS_APPROVAL_PURCHASE
from smolstuff.ops_demos import ScenarioStore
from smolstuff.workflow import WorkflowStore


def test_two_visitors_can_start_the_same_demo_in_one_database(tmp_path):
    path = str(tmp_path / "shared.sqlite3")
    first = WorkflowStore(path, session_id="visitor-a")
    second = WorkflowStore(path, session_id="visitor-b")
    try:
        first.start_purchase("demo-supplier-lead-time-35", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        second.start_purchase("demo-supplier-lead-time-35", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        assert first.count_workflows() == 1
        assert second.count_workflows() == 1
        first.reset_signal("demo-supplier-lead-time-35")
        assert first.find_by_dedup("demo-supplier-lead-time-35") is None
        assert second.find_by_dedup("demo-supplier-lead-time-35") is not None
    finally:
        first.close()
        second.close()


def test_receipt_keys_do_not_collide_across_visitors(tmp_path):
    path = str(tmp_path / "shared.sqlite3")
    first = WorkflowStore(path, session_id="visitor-a")
    second = WorkflowStore(path, session_id="visitor-b")
    try:
        started = first.start_purchase("demo-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        other = second.start_purchase("demo-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        first.approve(started.workflow_id, actor="owner")
        second.approve(other.workflow_id, actor="owner")
        first.execute(started.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        second.execute(other.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        from decimal import Decimal

        baseline = Decimal("21")
        first.confirm(started.workflow_id, NEEDS_APPROVAL_PURCHASE, baseline)
        second.confirm(other.workflow_id, NEEDS_APPROVAL_PURCHASE, baseline)
        first.receive(started.workflow_id, 100, "demo-receipt-full", baseline)
        second.receive(other.workflow_id, 100, "demo-receipt-full", baseline)
        assert first.count_receipts() == 1
        assert second.count_receipts() == 1
        assert first.count_movements() == 1
        assert second.count_movements() == 1
        third = WorkflowStore(path, session_id="visitor-c")
        started = third.start_purchase("demo-signal-c", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        third.approve(started.workflow_id, actor="owner")
        third.execute(started.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        third.confirm(started.workflow_id, NEEDS_APPROVAL_PURCHASE, baseline)
        assert third.progress(started.workflow_id, baseline).on_hand == baseline
        third.close()
    finally:
        first.close()
        second.close()


def test_preview_state_is_scoped_by_session(tmp_path):
    path = str(tmp_path / "shared.sqlite3")
    first = ScenarioStore(path, "visitor-a")
    second = ScenarioStore(path, "visitor-b")
    try:
        first.save("workshop", {"phase": "assessed", "contribution": "700"})
        assert second.get("workshop") is None
        second.reset("workshop")
        assert first.get("workshop")["contribution"] == "700"
    finally:
        first.close()
        second.close()


def test_money_is_stored_as_exact_text(tmp_path):
    path = str(tmp_path / "money.sqlite3")
    store = WorkflowStore(path, session_id="visitor-a")
    try:
        store.start_purchase("demo-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        row = store._conn.execute(
            "SELECT unit_price, fees, total FROM actions"
        ).fetchone()
        assert row["unit_price"] == "1.82"
        assert row["fees"] == "7.00"
        assert row["total"] == "189.00"
        assert "." in row["total"]
    finally:
        store.close()


def test_all_workflow_counts_are_isolated_across_visitors(tmp_path):
    from decimal import Decimal

    path = str(tmp_path / "counts.sqlite3")
    first = WorkflowStore(path, session_id="visitor-a")
    second = WorkflowStore(path, session_id="visitor-b")
    try:
        started = first.start_purchase("same-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        first.approve(started.workflow_id, actor="owner")
        first.execute(started.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        first.confirm(started.workflow_id, NEEDS_APPROVAL_PURCHASE, Decimal("21"))
        first.receive(started.workflow_id, 100, "receipt", Decimal("21"))
        count_methods = ("count_workflows", "count_approvals", "count_executions",
                         "count_confirmations", "count_receipts", "count_movements")
        for name in count_methods:
            assert getattr(first, name)() == 1, name
            assert getattr(second, name)() == 0, name
        other = second.start_purchase("same-signal", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
        second.decline(other.workflow_id, actor="owner")
        assert first.count_approvals() == second.count_approvals() == 1
        assert second.count_executions() == second.count_confirmations() == 0
    finally:
        first.close()
        second.close()
