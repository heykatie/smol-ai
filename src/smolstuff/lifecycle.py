"""Legal workflow states. A purchase confirmation is not a completed receipt."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import FrozenSet, Tuple


class WorkflowState(Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    PLAN_READY = "plan_ready"
    POLICY_CHECK = "policy_check"
    AUTHORIZED = "authorized"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    APPROVED = "approved"
    BLOCKED = "blocked"
    DECLINED = "declined"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    AWAITING_RECEIPT = "awaiting_receipt"
    RECONCILING = "reconciling"
    RECOVERY = "recovery"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


TERMINAL_STATES = frozenset(
    {
        WorkflowState.COMPLETED,
        WorkflowState.DECLINED,
        WorkflowState.CANCELLED,
        WorkflowState.FAILED,
    }
)

_ALLOWED = {
    WorkflowState.DETECTED: frozenset(
        {WorkflowState.INVESTIGATING, WorkflowState.CANCELLED}
    ),
    WorkflowState.INVESTIGATING: frozenset(
        {WorkflowState.PLAN_READY, WorkflowState.RECOVERY, WorkflowState.CANCELLED, WorkflowState.FAILED}
    ),
    WorkflowState.PLAN_READY: frozenset(
        {WorkflowState.POLICY_CHECK, WorkflowState.CANCELLED}
    ),
    WorkflowState.POLICY_CHECK: frozenset(
        {
            WorkflowState.AUTHORIZED,
            WorkflowState.WAITING_FOR_APPROVAL,
            WorkflowState.BLOCKED,
            WorkflowState.DECLINED,
        }
    ),
    WorkflowState.AUTHORIZED: frozenset(
        {WorkflowState.EXECUTING, WorkflowState.CANCELLED, WorkflowState.POLICY_CHECK}
    ),
    WorkflowState.WAITING_FOR_APPROVAL: frozenset(
        {
            WorkflowState.APPROVED,
            WorkflowState.DECLINED,
            WorkflowState.CANCELLED,
            WorkflowState.POLICY_CHECK,
        }
    ),
    WorkflowState.APPROVED: frozenset(
        {WorkflowState.EXECUTING, WorkflowState.CANCELLED, WorkflowState.POLICY_CHECK}
    ),
    WorkflowState.BLOCKED: frozenset(
        {WorkflowState.RECOVERY, WorkflowState.CANCELLED}
    ),
    WorkflowState.EXECUTING: frozenset(
        {WorkflowState.VERIFYING, WorkflowState.RECOVERY, WorkflowState.FAILED}
    ),
    WorkflowState.VERIFYING: frozenset(
        {WorkflowState.AWAITING_RECEIPT, WorkflowState.RECOVERY, WorkflowState.FAILED}
    ),
    WorkflowState.AWAITING_RECEIPT: frozenset(
        {WorkflowState.RECONCILING, WorkflowState.RECOVERY}
    ),
    WorkflowState.RECONCILING: frozenset(
        {WorkflowState.COMPLETED, WorkflowState.RECOVERY}
    ),
    WorkflowState.RECOVERY: frozenset(
        {
            WorkflowState.PLAN_READY,
            WorkflowState.WAITING_FOR_APPROVAL,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
        }
    ),
    WorkflowState.COMPLETED: frozenset(),
    WorkflowState.DECLINED: frozenset(),
    WorkflowState.CANCELLED: frozenset(),
    WorkflowState.FAILED: frozenset(),
}


def allowed_transitions(state: WorkflowState) -> FrozenSet[WorkflowState]:
    return _ALLOWED[state]


def can_transition(current: WorkflowState, nxt: WorkflowState) -> bool:
    return nxt in _ALLOWED[current]


@dataclass(frozen=True)
class WorkflowSnapshot:
    state: WorkflowState
    purchase_confirmed: bool
    receipt_recorded: bool
    verified: bool
    reconciled: bool
    unresolved_units: Decimal

    def __post_init__(self) -> None:
        if isinstance(self.unresolved_units, float):
            raise TypeError("Unresolved units reject float.")
        units = self.unresolved_units
        if not isinstance(units, Decimal):
            units = Decimal(str(units))
        if units < 0:
            raise ValueError("Unresolved units cannot be negative.")
        object.__setattr__(self, "unresolved_units", units)


def completion_blockers(snapshot: WorkflowSnapshot) -> Tuple[str, ...]:
    blockers = []
    if snapshot.state != WorkflowState.COMPLETED:
        blockers.append("Workflow state is not completed.")
    if snapshot.purchase_confirmed and not snapshot.receipt_recorded:
        blockers.append("Purchase confirmation is not receipt of inventory.")
    if not snapshot.verified:
        blockers.append("Verification is missing.")
    if not snapshot.reconciled:
        blockers.append("Reconciliation is missing.")
    if snapshot.unresolved_units != 0:
        blockers.append("An unresolved obligation remains.")
    return tuple(blockers)


def is_complete(snapshot: WorkflowSnapshot) -> bool:
    return completion_blockers(snapshot) == ()
