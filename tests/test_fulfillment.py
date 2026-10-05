from dataclasses import replace
from decimal import Decimal

from smolstuff.fixtures import EXAMPLE_POLICY, NEEDS_APPROVAL_PURCHASE
from smolstuff.lifecycle import WorkflowSnapshot, WorkflowState, is_complete
from smolstuff.workflow import WorkflowStore

BASELINE = Decimal("21")


def test_matching_confirmation_does_not_change_stock(tmp_path):
    store, workflow_id = _executing(tmp_path)
    first = store.confirm(workflow_id, NEEDS_APPROVAL_PURCHASE, BASELINE)
    second = store.confirm(workflow_id, NEEDS_APPROVAL_PURCHASE, BASELINE)

    assert first.accepted is True
    assert first.workflow_state == WorkflowState.AWAITING_RECEIPT
    assert first.on_hand == BASELINE
    assert first.confirmation_matched is True
    assert second.replayed is True
    assert store.count_confirmations() == 1
    assert store.count_movements() == 0
    store.close()


def test_mismatched_confirmation_enters_recovery(tmp_path):
    store, workflow_id = _executing(tmp_path)
    changed = replace(NEEDS_APPROVAL_PURCHASE, quantity=80)
    result = store.confirm(workflow_id, changed, BASELINE)

    assert result.accepted is False
    assert result.workflow_state == WorkflowState.RECOVERY
    assert result.on_hand == BASELINE
    refused = store.receive(workflow_id, 80, "should-not-land", BASELINE)
    assert refused.accepted is False
    assert store.count_movements() == 0
    store.close()


def test_full_receipt_closes_and_adds_stock_once(tmp_path):
    store, workflow_id = _confirmed(tmp_path)
    first = store.receive(workflow_id, 100, "full", BASELINE)
    second = store.receive(workflow_id, 100, "full", BASELINE)

    assert first.workflow_state == WorkflowState.COMPLETED
    assert first.received_quantity == 100
    assert first.unresolved_quantity == 0
    assert first.on_hand == Decimal("121")
    assert second.replayed is True
    assert store.count_movements() == 1
    assert is_complete(_snapshot(first)) is True
    store.close()


def test_short_receipt_stays_open_until_the_rest_arrives(tmp_path):
    store, workflow_id = _confirmed(tmp_path)
    short = store.receive(workflow_id, 97, "short", BASELINE)
    too_much = store.receive(workflow_id, 100, "too-much", BASELINE)
    rest = store.receive(workflow_id, 3, "rest", BASELINE)

    assert short.workflow_state == WorkflowState.RECONCILING
    assert short.received_quantity == 97
    assert short.unresolved_quantity == 3
    assert short.on_hand == Decimal("118")
    assert is_complete(_snapshot(short)) is False
    assert too_much.accepted is False
    assert too_much.on_hand == Decimal("118")
    assert rest.workflow_state == WorkflowState.COMPLETED
    assert rest.on_hand == Decimal("121")
    assert rest.unresolved_quantity == 0
    assert is_complete(_snapshot(rest)) is True
    store.close()


def test_receipt_before_confirmation_is_refused(tmp_path):
    store, workflow_id = _executing(tmp_path)
    result = store.receive(workflow_id, 100, "early", BASELINE)

    assert result.accepted is False
    assert result.on_hand == BASELINE
    assert store.count_receipts() == 0
    store.close()


def _executing(tmp_path):
    store = WorkflowStore(str(tmp_path / "fulfillment.sqlite3"))
    started = store.start_purchase("lead-time-email", NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    store.approve(started.workflow_id, actor="owner")
    store.execute(started.workflow_id, NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)
    return store, started.workflow_id


def _confirmed(tmp_path):
    store, workflow_id = _executing(tmp_path)
    store.confirm(workflow_id, NEEDS_APPROVAL_PURCHASE, BASELINE)
    return store, workflow_id


def _snapshot(view):
    return WorkflowSnapshot(
        state=view.workflow_state,
        purchase_confirmed=view.confirmation_matched is True,
        receipt_recorded=view.received_quantity == view.ordered_quantity,
        verified=view.confirmation_matched is True,
        reconciled=view.unresolved_quantity == 0 and view.workflow_state == WorkflowState.COMPLETED,
        unresolved_units=Decimal(view.unresolved_quantity),
    )
