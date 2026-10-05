"""Persisted purchase workflow.

The SQLite file is the source of truth. An approval covers one terms hash.
Submitting the same purchase twice returns the original simulated order.
"""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Callable, Optional

from smolstuff.fixtures import RecordOrigin
from smolstuff.lifecycle import WorkflowState, can_transition
from smolstuff.money import Money, transaction_total
from smolstuff.policy import GuardedPurchasePolicy, PolicyDecision, PurchaseProposal, evaluate_purchase
from smolstuff.terms import purchase_terms_hash


class WorkflowError(Exception):
    """Caller asked for a workflow or transition that does not exist."""


@dataclass(frozen=True)
class WorkflowView:
    workflow_id: str
    state: WorkflowState
    dedup_key: str
    origin: str
    action_id: Optional[str]
    supplier_id: Optional[str]
    sku: Optional[str]
    quantity: Optional[int]
    total: Optional[Money]
    terms_hash: Optional[str]
    policy_decision: Optional[PolicyDecision]
    replayed: bool = False


@dataclass(frozen=True)
class ApprovalView:
    approval_id: str
    action_id: str
    terms_hash: str
    decision: str
    actor: str
    workflow_state: WorkflowState
    replayed: bool


@dataclass(frozen=True)
class ExecutionView:
    executed: bool
    replayed: bool
    order_id: Optional[str]
    idempotency_key: Optional[str]
    workflow_state: WorkflowState
    reason: str


@dataclass(frozen=True)
class FulfillmentView:
    """Confirmation and receipt status for one purchase.

    `on_hand` is the caller-supplied baseline plus recorded receipt movements.
    A confirmation does not change it.
    """

    workflow_state: WorkflowState
    ordered_quantity: int
    received_quantity: int
    unresolved_quantity: int
    on_hand: Decimal
    confirmation_matched: Optional[bool]
    accepted: bool
    replayed: bool
    reason: str


@dataclass(frozen=True)
class IntegrationEvent:
    provider: str
    task: str
    result: str
    effect: str
    recorded_at: str
    status: str


_INTEGRATION_STATUSES = frozenset({"live", "simulated", "replayed"})
_SECRET_TEXT = re.compile(
    r"(api[_-]?key|secret|token|password|zwp_|sk-|sk_|tvly-|band_|bearer\s)",
    re.IGNORECASE,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


class WorkflowStore:
    def __init__(
        self,
        path: str,
        now: Callable[[], datetime] = _utc_now,
        session_id: str = "local",
        connection=None,
    ) -> None:
        self.path = path
        self.now = now
        self.session_id = session_id or "local"
        self._session_scoped = False
        self.dialect = "postgres" if connection is not None else "sqlite"
        if connection is None:
            self._conn = sqlite3.connect(path)
            self._conn.row_factory = sqlite3.Row
            self._conn.isolation_level = None
            self._conn.execute("PRAGMA foreign_keys = ON")
        else:
            self._conn = connection
        self._migrate()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "WorkflowStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def start_purchase(
        self,
        dedup_key: str,
        proposal: PurchaseProposal,
        policy: GuardedPurchasePolicy,
    ) -> WorkflowView:
        """Open a workflow for one supplier signal. The same key returns the first run."""
        if not dedup_key:
            raise ValueError("A supplier signal needs a deduplication key.")
        self._begin()
        try:
            existing = self._dedup_row(dedup_key)
            if existing is not None:
                view = self._view(existing["id"], replayed=True)
                self._conn.commit()
                return view

            workflow_id = uuid.uuid4().hex
            timestamp = _iso(self.now())
            self._conn.execute(
                """
                INSERT INTO workflows (
                    id, session_id, dedup_key, state, origin, action_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    workflow_id,
                    self.session_id,
                    dedup_key,
                    WorkflowState.DETECTED.value,
                    RecordOrigin,
                    timestamp,
                    timestamp,
                ),
            )
            self._transition(workflow_id, WorkflowState.INVESTIGATING, "Permitted supplier signal accepted.")
            self._transition(workflow_id, WorkflowState.PLAN_READY, "Purchase drafted from current evidence.")
            action_id = self._insert_action(workflow_id, proposal, policy)
            self._transition(workflow_id, WorkflowState.POLICY_CHECK, "Deterministic purchase policy evaluated.")
            self._apply_policy_state(workflow_id, action_id)
            view = self._view(workflow_id, replayed=False)
            self._conn.commit()
            return view
        except Exception:
            self._conn.rollback()
            raise

    def approve(
        self,
        workflow_id: str,
        actor: str,
        reason: str = "Owner approved these purchase terms.",
        ttl_seconds: Optional[int] = None,
    ) -> ApprovalView:
        actor = _actor(actor)
        self._begin()
        try:
            workflow = self._require(workflow_id)
            action = self._current_action(workflow)
            if workflow["state"] == WorkflowState.APPROVED.value:
                approval = self._approval_row(action["id"])
                if approval is None or approval["decision"] != "approved":
                    raise WorkflowError("Approved workflow is missing its approval.")
                view = self._approval_view(approval, WorkflowState.APPROVED, replayed=True)
                self._conn.commit()
                return view
            self._ensure(workflow_id, WorkflowState.WAITING_FOR_APPROVAL)
            if self._approval_row(action["id"]) is not None:
                raise WorkflowError("This action already has a decision.")

            expires_at = None
            if ttl_seconds is not None:
                if ttl_seconds < 1:
                    raise ValueError("Approval TTL must be positive.")
                expires_at = _iso(self.now() + timedelta(seconds=ttl_seconds))
            approval_id = uuid.uuid4().hex
            self._conn.execute(
                """
                INSERT INTO approvals (
                    id, action_id, terms_hash, decision, actor, reason,
                    created_at, expires_at, revoked_at
                ) VALUES (?, ?, ?, 'approved', ?, ?, ?, ?, NULL)
                """,
                (
                    approval_id,
                    action["id"],
                    action["terms_hash"],
                    actor,
                    reason,
                    _iso(self.now()),
                    expires_at,
                ),
            )
            self._transition(workflow_id, WorkflowState.APPROVED, "Approval bound to the purchase terms.")
            approval = self._approval_row(action["id"])
            view = self._approval_view(approval, WorkflowState.APPROVED, replayed=False)
            self._conn.commit()
            return view
        except Exception:
            self._conn.rollback()
            raise

    def decline(
        self,
        workflow_id: str,
        actor: str,
        reason: str = "Owner declined these purchase terms.",
    ) -> ApprovalView:
        actor = _actor(actor)
        self._begin()
        try:
            workflow = self._require(workflow_id)
            if workflow["state"] == WorkflowState.DECLINED.value:
                action = self._current_action(workflow)
                approval = self._approval_row(action["id"])
                view = self._approval_view(approval, WorkflowState.DECLINED, replayed=True)
                self._conn.commit()
                return view
            self._ensure(workflow_id, WorkflowState.WAITING_FOR_APPROVAL)
            action = self._current_action(workflow)
            approval_id = uuid.uuid4().hex
            self._conn.execute(
                """
                INSERT INTO approvals (
                    id, action_id, terms_hash, decision, actor, reason,
                    created_at, expires_at, revoked_at
                ) VALUES (?, ?, ?, 'declined', ?, ?, ?, NULL, NULL)
                """,
                (
                    approval_id,
                    action["id"],
                    action["terms_hash"],
                    actor,
                    reason,
                    _iso(self.now()),
                ),
            )
            self._transition(workflow_id, WorkflowState.DECLINED, reason)
            approval = self._approval_row(action["id"])
            view = self._approval_view(approval, WorkflowState.DECLINED, replayed=False)
            self._conn.commit()
            return view
        except Exception:
            self._conn.rollback()
            raise

    def revoke(self, workflow_id: str, actor: str, reason: str = "Owner revoked the approval.") -> ApprovalView:
        actor = _actor(actor)
        self._begin()
        try:
            workflow = self._require(workflow_id)
            action = self._current_action(workflow)
            approval = self._approval_row(action["id"])
            if approval is None or approval["decision"] != "approved":
                raise WorkflowError("There is no approval to revoke.")
            if approval["revoked_at"] is not None:
                view = self._approval_view(approval, WorkflowState(workflow["state"]), replayed=True)
                self._conn.commit()
                return view
            self._ensure(workflow_id, WorkflowState.APPROVED)
            self._conn.execute(
                "UPDATE approvals SET revoked_at = ? WHERE id = ?",
                (_iso(self.now()), approval["id"]),
            )
            self._transition(
                workflow_id,
                WorkflowState.CANCELLED,
                "{0} revoked the approval. {1}".format(actor, reason),
            )
            approval = self._approval_row(action["id"])
            view = self._approval_view(approval, WorkflowState.CANCELLED, replayed=False)
            self._conn.commit()
            return view
        except Exception:
            self._conn.rollback()
            raise

    def revise(
        self,
        workflow_id: str,
        proposal: PurchaseProposal,
        policy: GuardedPurchasePolicy,
    ) -> WorkflowView:
        """Replace the current terms. The previous approval stays bound to the old hash."""
        self._begin()
        try:
            workflow = self._require(workflow_id)
            state = WorkflowState(workflow["state"])
            if state not in (
                WorkflowState.WAITING_FOR_APPROVAL,
                WorkflowState.APPROVED,
                WorkflowState.AUTHORIZED,
            ):
                raise WorkflowError("Terms can be revised only before purchase submission.")
            previous = self._current_action(workflow)
            self._transition(workflow_id, WorkflowState.POLICY_CHECK, "Purchase terms changed. Approval must be renewed.")
            action_id = self._insert_action(workflow_id, proposal, policy)
            self._conn.execute(
                "UPDATE actions SET superseded_by = ? WHERE id = ?",
                (action_id, previous["id"]),
            )
            self._apply_policy_state(workflow_id, action_id)
            view = self._view(workflow_id, replayed=False)
            self._conn.commit()
            return view
        except Exception:
            self._conn.rollback()
            raise

    def execute(
        self,
        workflow_id: str,
        proposal: PurchaseProposal,
        policy: GuardedPurchasePolicy,
    ) -> ExecutionView:
        """Submit the saved purchase once. A retry returns the same simulated order."""
        self._begin()
        try:
            view = self._execute(workflow_id, proposal, policy)
            self._conn.commit()
            return view
        except Exception:
            self._conn.rollback()
            raise

    def get(self, workflow_id: str) -> WorkflowView:
        self._require(workflow_id)
        return self._view(workflow_id, replayed=False)

    def count_workflows(self) -> int:
        return self._count("workflows")

    def count_approvals(self) -> int:
        return self._count("approvals")

    def count_executions(self) -> int:
        return self._count("executions")

    def current_order(self, workflow_id: str) -> Optional[tuple]:
        """Return the saved order id and idempotency key, without submitting again."""
        workflow = self._require(workflow_id)
        if workflow["action_id"] is None:
            return None
        row = self._conn.execute(
            "SELECT order_id, idempotency_key FROM executions WHERE action_id = ?",
            (workflow["action_id"],),
        ).fetchone()
        if row is None:
            return None
        return (row["order_id"], row["idempotency_key"])

    def find_by_dedup(self, dedup_key: str) -> Optional[WorkflowView]:
        row = self._dedup_row(dedup_key)
        if row is None:
            return None
        return self._view(row["id"], replayed=False)

    def progress(self, workflow_id: str, baseline: Decimal) -> FulfillmentView:
        workflow = self._require(workflow_id)
        action = self._current_action(workflow)
        return self._fulfillment(workflow, action, baseline, accepted=True, replayed=False, reason="")

    def confirm(
        self, workflow_id: str, proposal: PurchaseProposal, baseline: Decimal
    ) -> FulfillmentView:
        """Check a supplier confirmation against the approved terms. Stock does not change."""
        self._begin()
        try:
            view = self._confirm(workflow_id, proposal, baseline)
            self._conn.commit()
            return view
        except Exception:
            self._conn.rollback()
            raise

    def receive(
        self, workflow_id: str, quantity: int, receipt_key: str, baseline: Decimal
    ) -> FulfillmentView:
        """Record units that arrived. The same receipt key cannot add stock twice."""
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError("Receipt quantity must be a positive integer.")
        if not isinstance(receipt_key, str) or not receipt_key.strip():
            raise ValueError("Receipt key is required.")
        self._begin()
        try:
            view = self._receive(workflow_id, quantity, receipt_key.strip(), baseline)
            self._conn.commit()
            return view
        except Exception:
            self._conn.rollback()
            raise

    def count_confirmations(self) -> int:
        return self._count("confirmations")

    def count_receipts(self) -> int:
        return self._count("receipts")

    def count_movements(self) -> int:
        return self._count("inventory_movements")

    def record_integration(
        self, provider: str, task: str, result: str, effect: str, status: str
    ) -> None:
        """Store a public execution record. Secrets are rejected, not redacted into the log."""
        if status not in _INTEGRATION_STATUSES:
            raise ValueError("Integration status must be live, simulated, or replayed.")
        fields = (
            _public_text(provider, "Provider"),
            _public_text(task, "Task"),
            _public_text(result, "Result"),
            _public_text(effect, "Effect"),
        )
        self._begin()
        try:
            self._conn.execute(
                """
                INSERT INTO integration_events (
                    session_id, provider, task, result, effect, recorded_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (self.session_id,) + fields + (_iso(self.now()), status),
            )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def list_integration_events(self) -> Tuple[IntegrationEvent, ...]:
        rows = self._conn.execute(
            """
            SELECT provider, task, result, effect, recorded_at, status
            FROM integration_events
            WHERE session_id = ?
            ORDER BY id
            """,
            (self.session_id,),
        ).fetchall()
        return tuple(
            IntegrationEvent(
                provider=row["provider"],
                task=row["task"],
                result=row["result"],
                effect=row["effect"],
                recorded_at=row["recorded_at"],
                status=row["status"],
            )
            for row in rows
        )

    def reset_signal(self, dedup_key: str) -> bool:
        """Delete one signal's workflow so the local demo can be replayed."""
        self._begin()
        try:
            row = self._dedup_row(dedup_key)
            if row is None:
                self._conn.commit()
                return False
            workflow_id = row["id"]
            self._conn.execute(
                """
                DELETE FROM inventory_movements
                WHERE receipt_id IN (
                    SELECT id FROM receipts
                    WHERE action_id IN (SELECT id FROM actions WHERE workflow_id = ?)
                )
                """,
                (workflow_id,),
            )
            self._conn.execute(
                """
                DELETE FROM receipts
                WHERE action_id IN (SELECT id FROM actions WHERE workflow_id = ?)
                """,
                (workflow_id,),
            )
            self._conn.execute(
                """
                DELETE FROM confirmations
                WHERE action_id IN (SELECT id FROM actions WHERE workflow_id = ?)
                """,
                (workflow_id,),
            )
            self._conn.execute(
                """
                DELETE FROM executions
                WHERE action_id IN (SELECT id FROM actions WHERE workflow_id = ?)
                """,
                (workflow_id,),
            )
            self._conn.execute(
                """
                DELETE FROM approvals
                WHERE action_id IN (SELECT id FROM actions WHERE workflow_id = ?)
                """,
                (workflow_id,),
            )
            self._conn.execute(
                "DELETE FROM workflow_transitions WHERE workflow_id = ?",
                (workflow_id,),
            )
            self._conn.execute("DELETE FROM actions WHERE workflow_id = ?", (workflow_id,))
            self._conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
            if self._session_scoped:
                self._conn.execute(
                    "DELETE FROM integration_events WHERE session_id = ?", (self.session_id,)
                )
            else:
                self._conn.execute("DELETE FROM integration_events")
            self._conn.commit()
            return True
        except Exception:
            self._conn.rollback()
            raise

    def _confirm(
        self, workflow_id: str, proposal: PurchaseProposal, baseline: Decimal
    ) -> FulfillmentView:
        workflow = self._require(workflow_id)
        action = self._current_action(workflow)
        state = WorkflowState(workflow["state"])
        terms_hash = purchase_terms_hash(
            proposal.supplier_id,
            proposal.sku,
            proposal.quantity,
            proposal.unit_price,
            proposal.fees,
        )
        existing = self._conn.execute(
            "SELECT matched FROM confirmations WHERE action_id = ?",
            (action["id"],),
        ).fetchone()
        if existing is not None:
            matched = bool(existing["matched"])
            reason = (
                "Existing confirmation returned."
                if matched
                else "The supplier confirmation did not match the approved terms."
            )
            return self._fulfillment(
                self._require(workflow_id),
                action,
                baseline,
                accepted=matched,
                replayed=True,
                reason=reason,
            )
        if state != WorkflowState.EXECUTING:
            return self._fulfillment(
                workflow,
                action,
                baseline,
                accepted=False,
                replayed=False,
                reason="Confirmation requires a submitted purchase.",
            )

        matched = terms_hash == action["terms_hash"]
        self._conn.execute(
            """
            INSERT INTO confirmations (id, action_id, terms_hash, matched, origin, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                action["id"],
                terms_hash,
                int(matched),
                RecordOrigin,
                _iso(self.now()),
            ),
        )
        self._transition(workflow_id, WorkflowState.VERIFYING, "Supplier confirmation received.")
        if matched:
            self._transition(
                workflow_id,
                WorkflowState.AWAITING_RECEIPT,
                "Confirmation matches the approved purchase.",
            )
            reason = "Confirmation matches the approved purchase. Inventory has not been received."
        else:
            self._transition(
                workflow_id,
                WorkflowState.RECOVERY,
                "Confirmation does not match the approved terms.",
            )
            reason = "The supplier confirmation did not match the approved terms."
        return self._fulfillment(
            self._require(workflow_id),
            action,
            baseline,
            accepted=matched,
            replayed=False,
            reason=reason,
        )

    def _receive(
        self, workflow_id: str, quantity: int, receipt_key: str, baseline: Decimal
    ) -> FulfillmentView:
        workflow = self._require(workflow_id)
        action = self._current_action(workflow)
        state = WorkflowState(workflow["state"])
        if self._session_scoped:
            existing = self._conn.execute(
                "SELECT action_id FROM receipts WHERE session_id = ? AND receipt_key = ?",
                (self.session_id, receipt_key),
            ).fetchone()
        else:
            existing = self._conn.execute(
                "SELECT action_id FROM receipts WHERE receipt_key = ?",
                (receipt_key,),
            ).fetchone()
        if existing is not None:
            return self._fulfillment(
                workflow,
                action,
                baseline,
                accepted=existing["action_id"] == action["id"],
                replayed=True,
                reason="Existing receipt returned. No second inventory movement was created.",
            )
        if state not in (WorkflowState.AWAITING_RECEIPT, WorkflowState.RECONCILING):
            return self._fulfillment(
                workflow,
                action,
                baseline,
                accepted=False,
                replayed=False,
                reason="A matching confirmation is required before receipt.",
            )

        received = self._received_quantity(action["id"])
        ordered = int(action["quantity"])
        if received + quantity > ordered:
            return self._fulfillment(
                workflow,
                action,
                baseline,
                accepted=False,
                replayed=False,
                reason="Receipt exceeds the remaining obligation.",
            )

        receipt_id = uuid.uuid4().hex
        self._conn.execute(
            """
            INSERT INTO receipts (
                id, session_id, action_id, receipt_key, quantity, origin, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                receipt_id,
                self.session_id,
                action["id"],
                receipt_key,
                quantity,
                RecordOrigin,
                _iso(self.now()),
            ),
        )
        self._conn.execute(
            """
            INSERT INTO inventory_movements (
                id, sku, delta, reason, receipt_id, origin, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                action["sku"],
                quantity,
                "Simulated receipt",
                receipt_id,
                RecordOrigin,
                _iso(self.now()),
            ),
        )
        if state == WorkflowState.AWAITING_RECEIPT:
            self._transition(
                workflow_id,
                WorkflowState.RECONCILING,
                "Receipt recorded. Reconciling against the purchase.",
            )
        remaining = ordered - (received + quantity)
        if remaining == 0:
            self._transition(
                workflow_id,
                WorkflowState.COMPLETED,
                "Received quantity matches the purchase. Obligation is closed.",
            )
            reason = "Full receipt reconciled. No units remain owed."
        else:
            reason = "{0} units remain unreceived and are not in stock.".format(remaining)
        return self._fulfillment(
            self._require(workflow_id),
            action,
            baseline,
            accepted=True,
            replayed=False,
            reason=reason,
        )

    def _fulfillment(
        self,
        workflow: sqlite3.Row,
        action: sqlite3.Row,
        baseline: Decimal,
        accepted: bool,
        replayed: bool,
        reason: str,
    ) -> FulfillmentView:
        if not isinstance(baseline, Decimal):
            raise TypeError("On-hand baseline must be Decimal.")
        received = self._received_quantity(action["id"])
        ordered = int(action["quantity"])
        confirmation = self._conn.execute(
            "SELECT matched FROM confirmations WHERE action_id = ?",
            (action["id"],),
        ).fetchone()
        matched = None if confirmation is None else bool(confirmation["matched"])
        if self._session_scoped:
            row = self._conn.execute(
                """
                SELECT COALESCE(SUM(movement.delta), 0) AS n
                FROM inventory_movements AS movement
                JOIN receipts ON receipts.id = movement.receipt_id
                WHERE movement.sku = ? AND receipts.session_id = ?
                """,
                (action["sku"], self.session_id),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT COALESCE(SUM(delta), 0) AS n FROM inventory_movements WHERE sku = ?",
                (action["sku"],),
            ).fetchone()
        return FulfillmentView(
            workflow_state=WorkflowState(workflow["state"]),
            ordered_quantity=ordered,
            received_quantity=received,
            unresolved_quantity=ordered - received,
            on_hand=baseline + Decimal(row["n"]),
            confirmation_matched=matched,
            accepted=accepted,
            replayed=replayed,
            reason=reason,
        )

    def _received_quantity(self, action_id: str) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) AS n FROM receipts WHERE action_id = ?",
            (action_id,),
        ).fetchone()
        return int(row["n"])

    def _execute(
        self,
        workflow_id: str,
        proposal: PurchaseProposal,
        policy: GuardedPurchasePolicy,
    ) -> ExecutionView:
        workflow = self._require(workflow_id)
        action = self._current_action(workflow)
        terms_hash = purchase_terms_hash(
            proposal.supplier_id,
            proposal.sku,
            proposal.quantity,
            proposal.unit_price,
            proposal.fees,
        )
        state = WorkflowState(workflow["state"])
        if terms_hash != action["terms_hash"]:
            return self._refused(state, "These terms do not match the saved purchase.")

        existing = self._conn.execute(
            "SELECT order_id, idempotency_key FROM executions WHERE action_id = ?",
            (action["id"],),
        ).fetchone()
        if existing is not None:
            return ExecutionView(
                executed=True,
                replayed=True,
                order_id=existing["order_id"],
                idempotency_key=existing["idempotency_key"],
                workflow_state=state,
                reason="Existing purchase returned. No second order was created.",
            )

        if state == WorkflowState.DECLINED:
            return self._refused(state, "The owner declined this purchase.")
        if state == WorkflowState.CANCELLED:
            return self._refused(state, "This purchase was cancelled.")
        if state == WorkflowState.BLOCKED:
            return self._refused(state, "Evidence is not ready for a decision.")
        if state not in (WorkflowState.APPROVED, WorkflowState.AUTHORIZED):
            return self._refused(state, "This workflow is not authorized to purchase.")

        decision = evaluate_purchase(proposal, policy)
        if decision.decision == PolicyDecision.NOT_READY:
            return self._refused(state, "Evidence or verification is not ready for execution.")

        if decision.decision == PolicyDecision.NEEDS_APPROVAL:
            if state != WorkflowState.APPROVED:
                return self._refused(state, "This purchase needs an approval for these terms.")
            refusal = self._validate_approval(workflow_id, action, terms_hash)
            if refusal is not None:
                return refusal

        idempotency_key = "purchase:{0}".format(action["id"])
        order_id = "simulated-po-{0}".format(uuid.uuid4().hex[:8])
        self._conn.execute(
            """
            INSERT INTO executions (idempotency_key, action_id, order_id, origin, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (idempotency_key, action["id"], order_id, RecordOrigin, _iso(self.now())),
        )
        self._transition(
            workflow_id,
            WorkflowState.EXECUTING,
            "Purchase submitted. Supplier confirmation is still required.",
        )
        return ExecutionView(
            executed=True,
            replayed=False,
            order_id=order_id,
            idempotency_key=idempotency_key,
            workflow_state=WorkflowState.EXECUTING,
            reason="Purchase submitted. Awaiting supplier confirmation.",
        )

    def _validate_approval(self, workflow_id: str, action: sqlite3.Row, terms_hash: str) -> Optional[ExecutionView]:
        approval = self._approval_row(action["id"])
        state = WorkflowState.APPROVED
        if approval is None or approval["decision"] != "approved":
            return self._refused(state, "This purchase needs an approval for these terms.")
        if approval["terms_hash"] != terms_hash:
            return self._refused(state, "The approval is bound to different purchase terms.")
        if approval["revoked_at"] is not None:
            return self._refused(state, "The approval was revoked.")
        if approval["expires_at"] is not None and self.now() >= _parse_time(approval["expires_at"]):
            self._transition(workflow_id, WorkflowState.CANCELLED, "Approval expired before execution.")
            return self._refused(WorkflowState.CANCELLED, "The approval expired.")
        return None

    def _apply_policy_state(self, workflow_id: str, action_id: str) -> None:
        action = self._conn.execute("SELECT * FROM actions WHERE id = ?", (action_id,)).fetchone()
        decision = PolicyDecision(action["policy_decision"])
        self._conn.execute(
            "UPDATE workflows SET action_id = ?, updated_at = ? WHERE id = ?",
            (action_id, _iso(self.now()), workflow_id),
        )
        if decision == PolicyDecision.AUTO_EXECUTE:
            self._transition(workflow_id, WorkflowState.AUTHORIZED, "Every guarded-auto rule passed.")
        elif decision == PolicyDecision.NEEDS_APPROVAL:
            self._transition(workflow_id, WorkflowState.WAITING_FOR_APPROVAL, "Owner decision required.")
        else:
            self._transition(workflow_id, WorkflowState.BLOCKED, "Evidence is not ready for a decision.")

    def _insert_action(
        self,
        workflow_id: str,
        proposal: PurchaseProposal,
        policy: GuardedPurchasePolicy,
    ) -> str:
        result = evaluate_purchase(proposal, policy)
        total = transaction_total(proposal.unit_price, proposal.quantity, proposal.fees)
        terms_hash = purchase_terms_hash(
            proposal.supplier_id,
            proposal.sku,
            proposal.quantity,
            proposal.unit_price,
            proposal.fees,
        )
        action_id = uuid.uuid4().hex
        previous_amount = None
        previous_currency = None
        if proposal.previous_unit_price is not None:
            previous_amount = format(proposal.previous_unit_price.amount, "f")
            previous_currency = proposal.previous_unit_price.currency
        self._conn.execute(
            """
            INSERT INTO actions (
                id, workflow_id, supplier_id, sku, quantity, currency,
                unit_price, fees, total, previous_unit_price, previous_currency,
                supplier_allowlisted, sku_previously_purchased,
                evidence_current, evidence_complete, verification_passed,
                terms_hash, policy_decision, policy_reasons, superseded_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            (
                action_id,
                workflow_id,
                proposal.supplier_id,
                proposal.sku,
                proposal.quantity,
                total.currency,
                format(proposal.unit_price.amount, "f"),
                format(proposal.fees.amount, "f"),
                format(total.amount, "f"),
                previous_amount,
                previous_currency,
                int(proposal.supplier_allowlisted),
                int(proposal.sku_previously_purchased),
                int(proposal.evidence_current),
                int(proposal.evidence_complete),
                int(proposal.verification_passed),
                terms_hash,
                result.decision.value,
                json.dumps(list(result.reasons)),
                _iso(self.now()),
            ),
        )
        return action_id

    def _transition(self, workflow_id: str, nxt: WorkflowState, reason: str) -> None:
        workflow = self._require(workflow_id)
        current = WorkflowState(workflow["state"])
        if not can_transition(current, nxt):
            raise WorkflowError(
                "Cannot move from {0} to {1}.".format(current.value, nxt.value)
            )
        timestamp = _iso(self.now())
        self._conn.execute(
            "UPDATE workflows SET state = ?, updated_at = ? WHERE id = ?",
            (nxt.value, timestamp, workflow_id),
        )
        self._conn.execute(
            """
            INSERT INTO workflow_transitions (workflow_id, from_state, to_state, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (workflow_id, current.value, nxt.value, reason, timestamp),
        )

    def _view(self, workflow_id: str, replayed: bool) -> WorkflowView:
        workflow = self._require(workflow_id)
        action = None
        if workflow["action_id"] is not None:
            action = self._conn.execute(
                "SELECT * FROM actions WHERE id = ?", (workflow["action_id"],)
            ).fetchone()
        return WorkflowView(
            workflow_id=workflow["id"],
            state=WorkflowState(workflow["state"]),
            dedup_key=workflow["dedup_key"],
            origin=workflow["origin"],
            action_id=None if action is None else action["id"],
            supplier_id=None if action is None else action["supplier_id"],
            sku=None if action is None else action["sku"],
            quantity=None if action is None else action["quantity"],
            total=None if action is None else Money(action["total"], action["currency"]),
            terms_hash=None if action is None else action["terms_hash"],
            policy_decision=None if action is None else PolicyDecision(action["policy_decision"]),
            replayed=replayed,
        )

    def _current_action(self, workflow: sqlite3.Row) -> sqlite3.Row:
        if workflow["action_id"] is None:
            raise WorkflowError("Workflow has no current purchase.")
        action = self._conn.execute(
            "SELECT * FROM actions WHERE id = ?", (workflow["action_id"],)
        ).fetchone()
        if action is None:
            raise WorkflowError("Current purchase is missing.")
        return action

    def _approval_row(self, action_id: str) -> Optional[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM approvals WHERE action_id = ?", (action_id,)
        ).fetchone()

    def _approval_view(self, approval: sqlite3.Row, state: WorkflowState, replayed: bool) -> ApprovalView:
        return ApprovalView(
            approval_id=approval["id"],
            action_id=approval["action_id"],
            terms_hash=approval["terms_hash"],
            decision=approval["decision"],
            actor=approval["actor"],
            workflow_state=state,
            replayed=replayed,
        )

    def _ensure(self, workflow_id: str, expected: WorkflowState) -> None:
        workflow = self._require(workflow_id)
        if workflow["state"] != expected.value:
            raise WorkflowError(
                "Expected {0}, found {1}.".format(expected.value, workflow["state"])
            )

    def _require(self, workflow_id: str) -> sqlite3.Row:
        if self._session_scoped:
            workflow = self._conn.execute(
                "SELECT * FROM workflows WHERE id = ? AND session_id = ?",
                (workflow_id, self.session_id),
            ).fetchone()
        else:
            workflow = self._conn.execute(
                "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
            ).fetchone()
        if workflow is None:
            raise WorkflowError("Unknown workflow.")
        return workflow

    def _refused(self, state: WorkflowState, reason: str) -> ExecutionView:
        return ExecutionView(
            executed=False,
            replayed=False,
            order_id=None,
            idempotency_key=None,
            workflow_state=state,
            reason=reason,
        )

    def _count(self, table: str) -> int:
        if table not in (
            "workflows",
            "approvals",
            "executions",
            "confirmations",
            "receipts",
            "inventory_movements",
        ):
            raise ValueError("Unknown table.")
        if self._session_scoped and table == "workflows":
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM workflows WHERE session_id = ?",
                (self.session_id,),
            ).fetchone()
            return int(row["n"])
        if self._session_scoped and table == "receipts":
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM receipts WHERE session_id = ?",
                (self.session_id,),
            ).fetchone()
            return int(row["n"])
        if self._session_scoped and table == "inventory_movements":
            row = self._conn.execute(
                """
                SELECT COUNT(*) AS n FROM inventory_movements AS movement
                JOIN receipts ON receipts.id = movement.receipt_id
                WHERE receipts.session_id = ?
                """,
                (self.session_id,),
            ).fetchone()
            return int(row["n"])
        row = self._conn.execute("SELECT COUNT(*) AS n FROM {0}".format(table)).fetchone()
        return int(row["n"])

    def _begin(self) -> None:
        self._conn.execute("BEGIN IMMEDIATE")

    def _dedup_row(self, dedup_key: str):
        if self._session_scoped:
            return self._conn.execute(
                "SELECT id FROM workflows WHERE session_id = ? AND dedup_key = ?",
                (self.session_id, dedup_key),
            ).fetchone()
        return self._conn.execute(
            "SELECT id FROM workflows WHERE dedup_key = ?", (dedup_key,)
        ).fetchone()

    def _migrate(self) -> None:
        if self.dialect == "postgres":
            self._conn.executescript(
                _SCOPED_SCHEMA.replace(
                    "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY",
                )
            )
            self._session_scoped = True
            return
        existing = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workflows'"
        ).fetchone()
        if existing is None:
            self._conn.executescript(_SCOPED_SCHEMA)
            self._session_scoped = True
            return
        columns = {
            row[1] for row in self._conn.execute("PRAGMA table_info(workflows)").fetchall()
        }
        self._session_scoped = "session_id" in columns
        if self._session_scoped:
            return
        self._conn.execute(
            "ALTER TABLE workflows ADD COLUMN session_id TEXT NOT NULL DEFAULT 'local'"
        )
        self._conn.execute(
            "ALTER TABLE receipts ADD COLUMN session_id TEXT NOT NULL DEFAULT 'local'"
        )
        self._conn.execute(
            "ALTER TABLE integration_events ADD COLUMN session_id TEXT NOT NULL DEFAULT 'local'"
        )
        self._session_scoped = True


_SCOPED_SCHEMA = """
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                dedup_key TEXT NOT NULL,
                state TEXT NOT NULL,
                origin TEXT NOT NULL,
                action_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (session_id, dedup_key)
            );

            CREATE TABLE IF NOT EXISTS actions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL REFERENCES workflows(id),
                supplier_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                currency TEXT NOT NULL,
                unit_price TEXT NOT NULL,
                fees TEXT NOT NULL,
                total TEXT NOT NULL,
                previous_unit_price TEXT,
                previous_currency TEXT,
                supplier_allowlisted INTEGER NOT NULL,
                sku_previously_purchased INTEGER NOT NULL,
                evidence_current INTEGER NOT NULL,
                evidence_complete INTEGER NOT NULL,
                verification_passed INTEGER NOT NULL,
                terms_hash TEXT NOT NULL,
                policy_decision TEXT NOT NULL,
                policy_reasons TEXT NOT NULL,
                superseded_by TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                action_id TEXT NOT NULL UNIQUE REFERENCES actions(id),
                terms_hash TEXT NOT NULL,
                decision TEXT NOT NULL,
                actor TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                revoked_at TEXT
            );

            CREATE TABLE IF NOT EXISTS executions (
                idempotency_key TEXT PRIMARY KEY,
                action_id TEXT NOT NULL UNIQUE REFERENCES actions(id),
                order_id TEXT NOT NULL,
                origin TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS confirmations (
                id TEXT PRIMARY KEY,
                action_id TEXT NOT NULL UNIQUE REFERENCES actions(id),
                terms_hash TEXT NOT NULL,
                matched INTEGER NOT NULL,
                origin TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS receipts (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                action_id TEXT NOT NULL REFERENCES actions(id),
                receipt_key TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                origin TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (session_id, receipt_key)
            );

            CREATE TABLE IF NOT EXISTS inventory_movements (
                id TEXT PRIMARY KEY,
                sku TEXT NOT NULL,
                delta INTEGER NOT NULL,
                reason TEXT NOT NULL,
                receipt_id TEXT NOT NULL UNIQUE REFERENCES receipts(id),
                origin TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS integration_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                task TEXT NOT NULL,
                result TEXT NOT NULL,
                effect TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS workflow_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL REFERENCES workflows(id),
                from_state TEXT NOT NULL,
                to_state TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
"""


def _actor(actor: str) -> str:
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError("Approval actor is required.")
    return actor.strip()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _public_text(value: str, field: str) -> str:
    text = str(value).strip()
    if not text or len(text) > 400:
        raise ValueError("{0} must be a short public sentence.".format(field))
    if _SECRET_TEXT.search(text):
        raise ValueError("{0} looks like a secret and was not stored.".format(field))
    return text
