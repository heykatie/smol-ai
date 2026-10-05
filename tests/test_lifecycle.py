from decimal import Decimal

from smolstuff.lifecycle import (
    WorkflowSnapshot,
    WorkflowState,
    can_transition,
    completion_blockers,
    is_complete,
)


def test_happy_path_reaches_receipt_before_completion():
    assert can_transition(WorkflowState.DETECTED, WorkflowState.INVESTIGATING)
    assert can_transition(WorkflowState.POLICY_CHECK, WorkflowState.WAITING_FOR_APPROVAL)
    assert can_transition(WorkflowState.WAITING_FOR_APPROVAL, WorkflowState.APPROVED)
    assert can_transition(WorkflowState.APPROVED, WorkflowState.EXECUTING)
    assert can_transition(WorkflowState.VERIFYING, WorkflowState.AWAITING_RECEIPT)
    assert can_transition(WorkflowState.RECONCILING, WorkflowState.COMPLETED)


def test_terminal_states_do_not_resume():
    assert can_transition(WorkflowState.COMPLETED, WorkflowState.EXECUTING) is False
    assert can_transition(WorkflowState.DECLINED, WorkflowState.EXECUTING) is False
    assert can_transition(WorkflowState.DETECTED, WorkflowState.COMPLETED) is False


def test_confirmation_without_receipt_is_not_complete():
    snapshot = WorkflowSnapshot(
        state=WorkflowState.AWAITING_RECEIPT,
        purchase_confirmed=True,
        receipt_recorded=False,
        verified=True,
        reconciled=False,
        unresolved_units=Decimal("100"),
    )

    assert is_complete(snapshot) is False
    assert "Purchase confirmation is not receipt of inventory." in completion_blockers(snapshot)


def test_partial_receipt_keeps_the_shortage_open():
    snapshot = WorkflowSnapshot(
        state=WorkflowState.RECONCILING,
        purchase_confirmed=True,
        receipt_recorded=True,
        verified=True,
        reconciled=False,
        unresolved_units=Decimal("3"),
    )

    assert is_complete(snapshot) is False
    assert any("unresolved" in reason for reason in completion_blockers(snapshot))


def test_complete_requires_verification_reconciliation_and_no_obligation():
    snapshot = WorkflowSnapshot(
        state=WorkflowState.COMPLETED,
        purchase_confirmed=True,
        receipt_recorded=True,
        verified=True,
        reconciled=True,
        unresolved_units=Decimal("0"),
    )

    assert is_complete(snapshot) is True
    assert completion_blockers(snapshot) == ()
