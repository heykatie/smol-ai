from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from smol_ai.fixtures import AUTO_ELIGIBLE_PURCHASE, EXAMPLE_POLICY, NEEDS_APPROVAL_PURCHASE
from smol_ai.lifecycle import WorkflowState
from smol_ai.money import Money
from smol_ai.policy import PolicyDecision
from smol_ai.workflow import WorkflowStore


def _open(tmp_path, name="demo.sqlite3"):
    return WorkflowStore(str(tmp_path / name))


def test_approval_survives_restart_and_second_submit_replays_one_order(tmp_path):
    path = str(tmp_path / "restart.sqlite3")
    store = WorkflowStore(path)
    started = store.start_purchase("lead-time-email", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    assert started.state == WorkflowState.WAITING_FOR_APPROVAL
    assert started.total == Money(Decimal("61.00"))
    assert started.origin == "simulated"
    store.approve(started.workflow_id, actor="owner")
    store.close()

    resumed = WorkflowStore(path)
    saved = resumed.get(started.workflow_id)
    assert saved.state == WorkflowState.APPROVED
    assert saved.supplier_id == "supplier-b"
    assert saved.sku == "DEMO-SKU-001"
    assert saved.quantity == 100
    assert saved.total == Money(Decimal("61.00"))

    first = resumed.execute(started.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    second = resumed.execute(started.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)

    assert first.executed is True
    assert first.replayed is False
    assert first.order_id.startswith("simulated-po-")
    assert first.idempotency_key == "purchase:{0}".format(saved.action_id)
    assert first.workflow_state == WorkflowState.EXECUTING
    assert second.replayed is True
    assert second.order_id == first.order_id
    assert resumed.count_executions() == 1
    resumed.close()


def test_duplicate_signal_does_not_open_a_second_workflow(tmp_path):
    store = _open(tmp_path)
    first = store.start_purchase("lead-time-email", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    other_terms = replace(NEEDS_APPROVAL_PURCHASE, quantity=40)
    second = store.start_purchase("lead-time-email", other_terms, EXAMPLE_POLICY)

    assert second.replayed is True
    assert second.workflow_id == first.workflow_id
    assert second.quantity == 100
    assert second.total == Money(Decimal("61.00"))
    assert store.count_workflows() == 1
    store.close()


def test_changed_price_cannot_reuse_the_approval(tmp_path):
    store = _open(tmp_path)
    started = store.start_purchase("lead-time-email", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    store.approve(started.workflow_id, actor="owner")
    changed = replace(
        NEEDS_APPROVAL_PURCHASE,
        unit_price=Money(Decimal("0.75")),
    )

    mismatched = store.execute(started.workflow_id, changed, EXAMPLE_POLICY)
    assert mismatched.executed is False
    assert store.get(started.workflow_id).state == WorkflowState.APPROVED

    revised = store.revise(started.workflow_id, changed, EXAMPLE_POLICY)
    assert revised.state == WorkflowState.WAITING_FOR_APPROVAL
    assert revised.total == Money(Decimal("82.00"))
    assert revised.total != Money(Decimal("75.00"))
    assert started.total == Money(Decimal("61.00"))
    assert started.total != Money(Decimal("54.00"))
    assert revised.terms_hash != started.terms_hash
    assert store.count_approvals() == 1

    reused = store.execute(started.workflow_id, changed, EXAMPLE_POLICY)
    assert reused.executed is False
    assert store.count_executions() == 0
    store.close()


def test_duplicate_approval_click_stores_one_approval(tmp_path):
    store = _open(tmp_path)
    started = store.start_purchase("lead-time-email", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    first = store.approve(started.workflow_id, actor="owner")
    second = store.approve(started.workflow_id, actor="owner")

    assert first.replayed is False
    assert second.replayed is True
    assert second.approval_id == first.approval_id
    assert second.terms_hash == started.terms_hash
    assert store.count_approvals() == 1
    store.close()


def test_decline_prevents_execution(tmp_path):
    store = _open(tmp_path)
    started = store.start_purchase("lead-time-email", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    declined = store.decline(started.workflow_id, actor="owner")
    result = store.execute(started.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)

    assert declined.decision == "declined"
    assert result.executed is False
    assert result.workflow_state == WorkflowState.DECLINED
    assert store.count_executions() == 0
    store.close()


def test_revocation_prevents_execution(tmp_path):
    store = _open(tmp_path)
    started = store.start_purchase("lead-time-email", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    store.approve(started.workflow_id, actor="owner")
    revoked = store.revoke(started.workflow_id, actor="owner")
    result = store.execute(started.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)

    assert revoked.workflow_state == WorkflowState.CANCELLED
    assert revoked.actor == "owner"
    assert result.executed is False
    assert result.workflow_state == WorkflowState.CANCELLED
    assert store.count_executions() == 0
    store.close()


def test_expired_approval_prevents_execution(tmp_path):
    clock = {"now": datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)}
    store = WorkflowStore(str(tmp_path / "expiry.sqlite3"), now=lambda: clock["now"])
    started = store.start_purchase("lead-time-email", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    store.approve(started.workflow_id, actor="owner", ttl_seconds=60)
    clock["now"] = clock["now"] + timedelta(minutes=2)

    result = store.execute(started.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)

    assert result.executed is False
    assert result.workflow_state == WorkflowState.CANCELLED
    assert "expired" in result.reason.lower()
    assert store.count_executions() == 0
    store.close()


def test_stale_evidence_blocks_execution_after_approval(tmp_path):
    store = _open(tmp_path)
    started = store.start_purchase("lead-time-email", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    store.approve(started.workflow_id, actor="owner")
    stale = replace(NEEDS_APPROVAL_PURCHASE, evidence_current=False)

    result = store.execute(started.workflow_id, stale, EXAMPLE_POLICY)

    assert result.executed is False
    assert "not ready" in result.reason.lower()
    assert store.get(started.workflow_id).state == WorkflowState.APPROVED
    assert store.count_executions() == 0
    store.close()


def test_auto_purchase_executes_once_without_an_approval(tmp_path):
    store = _open(tmp_path)
    started = store.start_purchase("small-restock", AUTO_ELIGIBLE_PURCHASE, EXAMPLE_POLICY)
    assert started.state == WorkflowState.AUTHORIZED
    assert started.policy_decision == PolicyDecision.AUTO_EXECUTE

    first = store.execute(started.workflow_id, AUTO_ELIGIBLE_PURCHASE, EXAMPLE_POLICY)
    second = store.execute(started.workflow_id, AUTO_ELIGIBLE_PURCHASE, EXAMPLE_POLICY)

    assert first.executed is True
    assert second.order_id == first.order_id
    assert store.count_approvals() == 0
    assert store.count_executions() == 1
    store.close()


def test_auto_purchase_stops_if_policy_no_longer_allows_it(tmp_path):
    store = _open(tmp_path)
    started = store.start_purchase("small-restock", AUTO_ELIGIBLE_PURCHASE, EXAMPLE_POLICY)
    tighter = replace(EXAMPLE_POLICY, auto_execute_total_below=Money(Decimal("10.00")))

    result = store.execute(started.workflow_id, AUTO_ELIGIBLE_PURCHASE, tighter)

    assert result.executed is False
    assert store.get(started.workflow_id).state == WorkflowState.AUTHORIZED
    assert store.count_executions() == 0
    store.close()
