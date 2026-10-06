"""Local Action Inbox.

A browser page over the saved purchase workflow. The numbers and the approval
come from the deterministic core. A configured sponsor may add a labeled record.
It cannot change quantity, price, or approval.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from pathlib import Path
import re
import socket
from string import Template
from threading import Thread
from typing import Optional
import uuid
from urllib.parse import parse_qs, urlparse

from smolstuff.fixtures import EXAMPLE_POLICY, WORKSHOP_SUPPLY_PACK
from smolstuff.http_guard import RequestRejected, read_form
from smolstuff.session_files import SessionLimited, expire_demo_sessions, reserve_session
from smolstuff.inventory import SupplyAssessment, assess_supply
from smolstuff.lifecycle import WorkflowState
from smolstuff.reorder import ReorderPlan, build_demo_plan, plan_reorder
from smolstuff.demo_ui import (
    PRACTICE_BANNER,
    SANDBOX_PREFIX,
    shell, error_page,
    apply_ops,
    build_inventory_snapshot,
    dashboard_page,
    detective_page,
    empty_cards,
    empty_inventory_snapshot,
    inventory_attention_count,
    inventory_page,
    load_cards,
    product_home_page,
    rescue_page,
    sandbox_href,
    staffing_page,
    workshop_page,
)
from smolstuff.ops_demos import ScenarioStore
from smolstuff.workflow import FulfillmentView, WorkflowStore, WorkflowView

DEMO_SIGNAL_KEY = "demo-supplier-lead-time-35"
MAIL_ADAPTER = "Mail demo adapter"
PURCHASE_ADAPTER = "Purchase demo adapter"
CONFIRMATION_ADAPTER = "Confirmation demo adapter"
RECEIPT_ADAPTER = "Receipt demo adapter"
FULL_RECEIPT_KEY = "demo-receipt-full"
SHORT_RECEIPT_KEY = "demo-receipt-short"
REST_RECEIPT_KEY = "demo-receipt-rest"
HOST = "127.0.0.1"
PORT = 8765
_PREP_ACTIONS = (
    "review_continue",
    "negotiate_accept",
    "negotiate_counter",
    "draft_send",
)
_ACTIONS = (
    "simulate_email",
    "approve",
    "decline",
    "reset",
    "submit_order",
    "confirm",
    "receive_full",
    "receive_short",
    "receive_rest",
) + _PREP_ACTIONS
REORDER_PREP_KEY = "reorder_prep"
REORDER_ITEM_ID = "DEMO-ITM-001"

_PAGE = Template(
    PRACTICE_BANNER
    + """
<section class="hero decision-hero">
<p class="kicker">Reorder · quiet linear switch</p>
<h1>$headline</h1>
<p class="lede">$summary</p>
</section>
<article class="card decision-card">
<p class="status $status_class">$status_label</p>
<p class="decision">$decision</p>
<p class="consequence">$note</p>
<div class="card-actions decision-actions">$actions</div>
$proofs
<details class="why-details"><summary>Why this recommendation</summary>
<p>$investigation</p>
</details>
<details id="evidence"><summary>Review evidence</summary>$evidence</details>
<p class="built-with"><strong>Built with</strong> $built_with</p>
</article>"""
)


class InboxApp:
    def __init__(self, path: str, session_id: str = "local", budget_path: str = None) -> None:
        self.path = path
        self.session_id = session_id
        self.budget_path = budget_path or str(Path(path).parent / "sponsor-budget.sqlite3")

    def page(self) -> str:
        store = WorkflowStore(self.path, session_id=self.session_id)
        try:
            workflow = store.find_by_dedup(DEMO_SIGNAL_KEY)
            if workflow is None:
                return _EMPTY_PAGE
            plan = self._plan()
            baseline = WORKSHOP_SUPPLY_PACK.sellable_on_hand
            progress = store.progress(workflow.workflow_id, baseline)
            order = store.current_order(workflow.workflow_id)
            events = store.list_integration_events()
            return render_inbox(
                workflow,
                assess_supply(WORKSHOP_SUPPLY_PACK),
                order,
                progress,
                plan,
                events,
                prep=self._get_prep(),
            )
        finally:
            store.close()

    def apply(self, action: str, fields: Optional[dict] = None) -> None:
        if action == "start":
            action = "simulate_email"
        if action not in _ACTIONS:
            raise ValueError("Unknown inbox action.")
        fields = fields or {}
        baseline = WORKSHOP_SUPPLY_PACK.sellable_on_hand
        store = WorkflowStore(self.path, session_id=self.session_id)
        try:
            if action == "reset":
                store.reset_signal(DEMO_SIGNAL_KEY)
                self._reset_scenario("supplier_fact")
                self._reset_scenario(REORDER_PREP_KEY)
                return
            if action == "simulate_email":
                if store.find_by_dedup(DEMO_SIGNAL_KEY) is not None:
                    store.record_integration(
                        "Lead-time parser",
                        "Extract supplier lead time from a synthetic email",
                        "No new model call was made.",
                        "Returned the existing decision.",
                        "replayed",
                    )
                    return
                attempt = self._extract_supplier_fact(store)
                plan = plan_reorder(attempt.fact)
                self._save_supplier_fact(attempt)
                started = store.start_purchase(DEMO_SIGNAL_KEY, plan.proposal, EXAMPLE_POLICY)
                store.record_integration(
                    attempt.provider,
                    "Extract supplier lead time from a synthetic email",
                    attempt.result,
                    "Returned the existing decision." if started.replayed else "Planning uses these lead times. Prices and approval stay in application code.",
                    "replayed" if started.replayed else attempt.status,
                )
                if not started.replayed:
                    self._record_supplier_research(store)
                    self._record_zoowork(store)
                    self._save_prep(
                        {
                            "phase": "review",
                            "countered": False,
                            "counter_price": "",
                            "draft_body": _default_draft_body(plan),
                        }
                    )
                return
            if action in _PREP_ACTIONS:
                self._apply_prep(action, fields)
                return
            plan = self._plan()
            workflow = store.find_by_dedup(DEMO_SIGNAL_KEY)
            if workflow is None:
                return
            workflow_id = workflow.workflow_id
            if action == "decline":
                if workflow.state == WorkflowState.WAITING_FOR_APPROVAL:
                    store.decline(workflow_id, actor="owner")
                return
            if action == "approve":
                if self._get_prep().get("phase") != "ready":
                    return
                self._approve(store, workflow)
                return
            if action == "submit_order":
                self._submit_order(store, workflow, plan)
                return
            if action == "confirm":
                confirmed = store.confirm(workflow_id, plan.proposal, baseline)
                self._record_confirmation(store, confirmed)
                return
            if action == "receive_full":
                self._record_receipt(
                    store,
                    store.receive(workflow_id, plan.quantity, FULL_RECEIPT_KEY, baseline),
                    "Record the full simulated receipt",
                )
                return
            if action == "receive_short":
                short_quantity = plan.quantity - 3
                if short_quantity >= 1:
                    self._record_receipt(
                        store,
                        store.receive(workflow_id, short_quantity, SHORT_RECEIPT_KEY, baseline),
                        "Record a short simulated receipt",
                    )
                return
            if action == "receive_rest":
                progress = store.progress(workflow_id, baseline)
                if progress.unresolved_quantity > 0:
                    self._record_receipt(
                        store,
                        store.receive(
                            workflow_id,
                            progress.unresolved_quantity,
                            REST_RECEIPT_KEY,
                            baseline,
                        ),
                        "Record the remaining simulated receipt",
                    )
        finally:
            store.close()

    def _approve(self, store, workflow) -> None:
        """Bind owner approval only. Submit and confirmation are separate steps."""
        workflow_id = workflow.workflow_id
        if workflow.state == WorkflowState.WAITING_FOR_APPROVAL:
            store.approve(workflow_id, actor="owner")
            store.record_integration(
                PURCHASE_ADAPTER,
                "Record owner approval for the purchase terms",
                "Approval bound to Supplier B, 100 units, $189.",
                "Order is not submitted until the next step.",
                "simulated",
            )
            return
        if workflow.state == WorkflowState.APPROVED:
            store.record_integration(
                PURCHASE_ADAPTER,
                "Record owner approval for the purchase terms",
                "Approval already recorded.",
                "Submit the order when ready.",
                "replayed",
            )

    def _submit_order(self, store, workflow, plan) -> None:
        workflow_id = workflow.workflow_id
        current = store.get(workflow_id)
        if current.state in (WorkflowState.APPROVED, WorkflowState.AUTHORIZED):
            executed = store.execute(workflow_id, plan.proposal, EXAMPLE_POLICY)
            store.record_integration(
                PURCHASE_ADAPTER,
                "Submit the approved purchase",
                executed.reason,
                "No second order was created."
                if executed.replayed
                else "One simulated order is waiting for confirmation.",
                "replayed" if executed.replayed else "simulated",
            )
            return
        if current.state in (
            WorkflowState.EXECUTING,
            WorkflowState.AWAITING_RECEIPT,
            WorkflowState.RECONCILING,
            WorkflowState.COMPLETED,
        ):
            store.record_integration(
                PURCHASE_ADAPTER,
                "Submit the approved purchase",
                "Existing order returned. No second purchase was submitted.",
                "The workflow stayed on its current step.",
                "replayed",
            )

    def _apply_prep(self, action: str, fields: dict) -> None:
        prep = self._get_prep()
        phase = prep.get("phase") or "review"
        plan = self._plan()
        if action == "review_continue" and phase == "review":
            prep["phase"] = "negotiate"
            prep.setdefault("draft_body", _default_draft_body(plan))
            self._save_prep(prep)
            return
        if action == "negotiate_counter" and phase == "negotiate":
            raw = fields.get("counter_price", ["180"])[0]
            prep["countered"] = True
            prep["counter_price"] = str(raw).strip() or "180"
            prep["hold_reply"] = (
                "Supplier B held the seeded offer at $189. "
                "No discount on this practice fixture."
            )
            self._save_prep(prep)
            return
        if action == "negotiate_accept" and phase == "negotiate":
            prep["phase"] = "draft"
            prep.setdefault("draft_body", _default_draft_body(plan))
            self._save_prep(prep)
            return
        if action == "draft_send" and phase == "draft":
            body = fields.get("draft_body", [prep.get("draft_body") or _default_draft_body(plan)])[0]
            prep["draft_body"] = str(body)
            prep["phase"] = "ready"
            prep["draft_sent"] = True
            self._save_prep(prep)
            return

    def _get_prep(self) -> dict:
        store = ScenarioStore(self.path, self.session_id)
        try:
            saved = store.get(REORDER_PREP_KEY)
        finally:
            store.close()
        if saved:
            return saved
        return {
            "phase": "review",
            "countered": False,
            "counter_price": "",
            "draft_body": "",
        }

    def _save_prep(self, payload: dict) -> None:
        store = ScenarioStore(self.path, self.session_id)
        try:
            store.save(REORDER_PREP_KEY, payload)
        finally:
            store.close()

    def _reset_scenario(self, name: str) -> None:
        store = ScenarioStore(self.path, self.session_id)
        try:
            store.reset(name)
        finally:
            store.close()

    def _record_confirmation(self, store, confirmed) -> None:
        if not confirmed.accepted and not confirmed.replayed:
            return
        store.record_integration(
            CONFIRMATION_ADAPTER,
            "Compare the supplier confirmation with the approved terms",
            confirmed.reason,
            "Receipt is next. The workflow is not complete."
            if confirmed.confirmation_matched
            else "The purchase stayed unmatched.",
            "replayed" if confirmed.replayed else "simulated",
        )

    def _record_receipt(self, store, receipt, task: str) -> None:
        if not receipt.accepted and not receipt.replayed:
            return
        if receipt.unresolved_quantity:
            effect = "{0} units are still owed, so the workflow stays open.".format(
                receipt.unresolved_quantity
            )
        else:
            effect = "Received quantity matches the order, so the workflow can close."
        store.record_integration(
            RECEIPT_ADAPTER,
            task,
            receipt.reason,
            effect,
            "replayed" if receipt.replayed else "simulated",
        )

    def view(self, scenario: str = "home") -> str:
        if scenario == "reorder":
            return self.page()
        if scenario == "inventory":
            return self._inventory()
        if scenario == "workshop":
            return self._saved_page("workshop", workshop_page)
        if scenario == "detective":
            return self._saved_page("detective", detective_page)
        if scenario == "rescue":
            return self._saved_page("rescue", rescue_page)
        if scenario == "staffing":
            return self._saved_page("staffing", staffing_page)
        return self._home()

    def route(self, action: str, fields: dict) -> str:
        if action.startswith(("workshop_", "detective_", "rescue_", "staffing_")):
            apply_ops(self.path, action, fields, self.session_id)
            return fields.get("scenario", ["home"])[0]
        self.apply(action, fields)
        return fields.get("scenario", ["reorder"])[0]

    def _inventory(self) -> str:
        if not self._has_saved_state():
            return inventory_page(empty_inventory_snapshot())
        return inventory_page(build_inventory_snapshot(self.path, self.session_id))

    def _has_saved_state(self) -> bool:
        return os.path.exists(self.path) or _session_in_database(self.session_id)

    def _saved_page(self, name: str, renderer):
        if not self._has_saved_state():
            return renderer(None)
        store = ScenarioStore(self.path, self.session_id)
        try:
            return renderer(store.get(name))
        finally:
            store.close()

    def _home(self) -> str:
        status, bucket, action = self._reorder_card()
        if self._has_saved_state():
            cards = load_cards(self.path, status, bucket, action, self.session_id)
            event_store = WorkflowStore(self.path, session_id=self.session_id)
            try:
                events = event_store.list_integration_events()
            finally:
                event_store.close()
        else:
            cards = empty_cards()
            events = ()
        if self._has_saved_state():
            snap = build_inventory_snapshot(self.path, self.session_id)
        else:
            snap = empty_inventory_snapshot()
        return dashboard_page(
            cards, events, inventory_attention=inventory_attention_count(snap)
        )

    def _reorder_card(self):
        start = (
            '<form method="post" action="{0}"><input type="hidden" name="scenario" value="reorder">'
            '<input type="hidden" name="action" value="simulate_email">'
            '<button class="primary" type="submit">Start interactive demo</button></form>'
        ).format(SANDBOX_PREFIX)
        if not self._has_saved_state():
            return "Not started", "Not started", start
        store = WorkflowStore(self.path, session_id=self.session_id)
        try:
            workflow = store.find_by_dedup(DEMO_SIGNAL_KEY)
        finally:
            store.close()
        if workflow is None:
            return "Not started", "Not started", start
        if workflow.state == WorkflowState.WAITING_FOR_APPROVAL:
            review = (
                '<a class="open" href="{0}">Review the $189 decision</a>'
            ).format(escape(sandbox_href("reorder")))
            return "Decision needed", "Needs your decision", review
        if workflow.state == WorkflowState.APPROVED:
            return "Approved — submit order", "In progress", ""
        if workflow.state == WorkflowState.EXECUTING:
            return "Awaiting confirmation", "In progress", ""
        if workflow.state == WorkflowState.AWAITING_RECEIPT:
            return "Awaiting receipt", "In progress", ""
        if workflow.state == WorkflowState.COMPLETED:
            return "Replenishment workflow completed", "Completed", ""
        if workflow.state == WorkflowState.DECLINED:
            return "Declined", "Completed", ""
        return workflow.state.value, "In progress", ""

    def _plan(self):
        saved = None
        if self._has_saved_state():
            store = ScenarioStore(self.path, self.session_id)
            try:
                saved = store.get("supplier_fact")
            finally:
                store.close()
        if saved and saved.get("current"):
            from smolstuff.extract import LeadTimeFact
            from smolstuff.fixtures import SUPPLIER_A_ID, WORKSHOP_SKU
            fact = LeadTimeFact(
                SUPPLIER_A_ID, WORKSHOP_SKU, int(saved["previous"]), int(saved["current"])
            )
            return plan_reorder(fact)
        return build_demo_plan()

    def _claim_sponsor_call(self) -> bool:
        from smolstuff.sponsor_budget import SponsorBudget

        budget = SponsorBudget(self.budget_path)
        try:
            return budget.claim(self.session_id)
        finally:
            budget.close()

    def _record_supplier_research(self, store) -> None:
        from smolstuff.research import research_supplier

        if not os.environ.get("TAVILY_API_KEY", "").strip() or not self._claim_sponsor_call():
            return
        attempt = research_supplier(allow_network=True)
        store.record_integration(
            attempt.provider,
            attempt.task,
            attempt.result,
            attempt.effect,
            attempt.status,
        )

    def _record_zoowork(self, store) -> None:
        if (
            not os.environ.get("ZOOWORK_API_KEY", "").strip()
            or not os.environ.get("ZOOWORK_AGENT_ID", "").strip()
            or not self._claim_sponsor_call()
        ):
            return
        from smolstuff.zoowork import explain_supplier_delay
        from smolstuff.fixtures import SUPPLIER_EMAIL

        attempt = explain_supplier_delay(SUPPLIER_EMAIL)
        store.record_integration(
            attempt.provider,
            attempt.task,
            attempt.result,
            attempt.effect,
            attempt.status,
        )

    def _extract_supplier_fact(self, store=None):
        if os.environ.get("SMOL_EXTRACTION_PROVIDER") in ("groq_gemini_parser", "groq_openrouter_parser"):
            from smolstuff.extraction_chain import extract_with_fallback
            from smolstuff.fixtures import SUPPLIER_A_ID, SUPPLIER_EMAIL, WORKSHOP_SKU

            def record(provider, result, status):
                if store is not None:
                    store.record_integration(provider, "Extract supplier lead time from a synthetic email",
                                             result, "No model fact accepted; fallback continues.", status)

            return extract_with_fallback(SUPPLIER_EMAIL, SUPPLIER_A_ID, WORKSHOP_SKU,
                                         self._claim_sponsor_call, record)
        from smolstuff.extract import call_novita, resolve_lead_time
        from smolstuff.fixtures import SUPPLIER_A_ID, SUPPLIER_EMAIL, WORKSHOP_SKU

        model_result = None
        model_error = False
        calls_off = False
        if os.environ.get("NOVITA_API_KEY", "").strip():
            if self._claim_sponsor_call():
                try:
                    model_result = call_novita(SUPPLIER_EMAIL)
                except Exception:
                    model_error = True
            else:
                calls_off = True
        return resolve_lead_time(
            SUPPLIER_EMAIL,
            SUPPLIER_A_ID,
            WORKSHOP_SKU,
            model_result,
            model_error,
            calls_off=calls_off,
        )

    def _save_supplier_fact(self, attempt) -> None:
        ScenarioStore(self.path, self.session_id).save("supplier_fact", {
            "phase": "extracted",
            "previous": attempt.fact.previous_lead_time_days,
            "current": attempt.fact.lead_time_days,
            "provider": attempt.provider,
            "status": attempt.status,
        })


def render_inbox(
    workflow: WorkflowView,
    supply: SupplyAssessment,
    order: Optional[tuple],
    progress: FulfillmentView,
    plan: ReorderPlan,
    events,
    prep: Optional[dict] = None,
) -> str:
    headline, summary, investigation, decision, note, status_label, status_class, actions = _status_copy(
        progress, order, plan, prep or {}
    )
    return shell("Reorder", _PAGE.substitute(
        headline=escape(headline),
        summary=escape(summary),
        investigation=escape(investigation),
        decision=escape(decision),
        note=escape(note),
        status_class=status_class,
        status_label=escape(status_label),
        proofs="",
        actions=actions,
        evidence=_evidence(plan, progress, order, events),
        built_with=_built_with(events),
    ))


def _status_copy(progress, order, plan: ReorderPlan, prep: dict):
    state = progress.workflow_state
    on_hand = _units(progress.on_hand)
    if state == WorkflowState.WAITING_FOR_APPROVAL:
        return _waiting_approval_copy(plan, prep)
    if state == WorkflowState.APPROVED:
        total = _cash(plan.proposal_total())
        return (
            "Approved — submit the practice order",
            "You authorized ${0} for {1} units from Supplier B.".format(total, plan.quantity),
            "Approval is bound. The next step sends the simulated purchase. Stock stays {0} until receipt.".format(
                _show_units(plan.available_now)
            ),
            "Submit the simulated order to Supplier B",
            "No confirmation or stock change yet.",
            "Approved",
            "progress",
            "".join(
                [
                    _form("submit_order", "Submit simulated order", "primary"),
                    _form("reset", "Reset demo", "secondary"),
                ]
            ),
        )
    if state == WorkflowState.EXECUTING and order is not None:
        return (
            "Purchase submitted",
            "Order {0} is awaiting supplier confirmation.".format(order[0]),
            "Available inventory is still {0}. Confirmation has not finished.".format(
                _show_units(plan.available_now)
            ),
            "Confirm the supplier match before receipt",
            "On hand is still {0}.".format(on_hand),
            "Purchase submitted",
            "executing",
            "".join(
                [
                    _form("confirm", "Confirm supplier match", "primary"),
                    _form("reset", "Reset demo", "secondary"),
                ]
            ),
        )
    if state == WorkflowState.AWAITING_RECEIPT:
        return (
            "Order confirmed — awaiting receipt",
            "Confirmation matches the approved product, quantity, and total.",
            "Estimated delivery is {0} days. The receipt control is an accelerated simulation and does not subtract sales.".format(
                plan.delivery_days
            ),
            "Available inventory is still {0}.".format(_show_units(plan.available_now)),
            "Stock has not changed. Review the confirmation below, then simulate receipt.",
            "Awaiting receipt",
            "waiting",
            "".join(
                [
                    _form(
                        "receive_full",
                        "Simulate receiving {0} units".format(plan.quantity),
                        "primary",
                    ),
                    '<a class="open" href="#confirmation">View confirmation</a>',
                    '<a class="open" href="#receipt">Purchase receipt</a>',
                    _form("reset", "Reset demo", "secondary"),
                ]
            ),
        )
    if state == WorkflowState.RECONCILING:
        return (
            "Shortage open",
            "Received {0} of {1}. {2} units are still owed and are not in stock.".format(
                progress.received_quantity,
                progress.ordered_quantity,
                progress.unresolved_quantity,
            ),
            "No cause was inferred.",
            "Available inventory is {0}.".format(on_hand),
            "Fact: the simulated receipt is short. Unknown: why the units are missing. They are not counted as stock, and the workflow is not closed.",
            "Shortage open",
            "reconciling",
            "".join(
                [
                    _form(
                        "receive_rest",
                        "Simulate receipt of the remaining {0}".format(progress.unresolved_quantity),
                        "primary",
                    ),
                    '<a class="open" href="#receipt">View receipt</a>',
                    _form("reset", "Reset demo", "secondary"),
                ]
            ),
        )
    if state == WorkflowState.COMPLETED:
        inv_href = sandbox_href("inventory", q=REORDER_ITEM_ID)
        return (
            "Replenishment workflow completed",
            "{0} units received. Available inventory updated from {1} to {2}.".format(
                progress.received_quantity, _units(plan.available_now), on_hand
            ),
            "The {0}-day delivery estimate was a supplier term. This receipt was an accelerated simulation.".format(
                plan.delivery_days
            ),
            "1 owner approval. Simulated receipt recorded. Inventory reconciled.",
            "On hand is now {0}. Open the catalog line to see Available at 121.".format(on_hand),
            "Completed",
            "completed",
            "".join(
                [
                    '<a class="open" href="{0}">View Quiet linear switch in inventory</a>'.format(
                        escape(inv_href)
                    ),
                    _form("reset", "Reset demo", "secondary"),
                ]
            ),
        )
    if state == WorkflowState.RECOVERY:
        return (
            "Recovery",
            "The supplier confirmation did not match the approved terms.",
            "Nothing was received.",
            "Available inventory is still {0}.".format(_show_units(plan.available_now)),
            "Reset the demo to try the matching confirmation.",
            "Recovery",
            "recovery",
            _form("reset", "Reset demo", "secondary"),
        )
    if state == WorkflowState.DECLINED:
        return (
            "Declined",
            "No purchase was submitted.",
            "Available inventory is still {0}.".format(_show_units(plan.available_now)),
            "No order was created.",
            "Reset the demo to see the decision again.",
            "Declined",
            "declined",
            _form("reset", "Reset demo", "secondary"),
        )
    return (
        state.value.replace("_", " "),
        "Reset the demo to start from the supplier signal.",
        "",
        "Workflow is {0}.".format(state.value.replace("_", " ")),
        "",
        state.value.replace("_", " "),
        state.value,
        _form("reset", "Reset demo", "secondary"),
    )


def _waiting_approval_copy(plan: ReorderPlan, prep: dict):
    total = _cash(plan.proposal_total())
    phase = prep.get("phase") or "review"
    risk_summary = (
        "You have about {0} days of stock. Your usual supplier now needs {1} days.".format(
            _whole_days(plan.days_of_supply), plan.lead_time_days
        )
    )
    investigation = (
        "There is about a {0}-day gap. Warehouse stock and existing orders cannot cover it. "
        "Supplier B can deliver in about {1} days. "
        "Minimum order: {2} units. This buys more than the immediate shortage. "
        "This purchase exceeds your below-$40 automatic spending limit. The other configured checks pass.".format(
            _whole_days(plan.projected_gap_days),
            plan.delivery_days,
            plan.quantity,
        )
    )
    if phase == "review":
        packet = (
            "Packet: about {gap}-day gap; Supplier B {qty} units at {breakdown}; "
            "MOQ {qty} (above immediate shortage); policy blocks auto-buy below $40. "
            "Stock stays {stock} until a simulated receipt."
        ).format(
            gap=_whole_days(plan.projected_gap_days),
            qty=plan.quantity,
            breakdown=_price_breakdown(plan),
            stock=_show_units(plan.available_now),
        )
        return (
            "Supplier delay puts inventory at risk",
            risk_summary,
            investigation,
            "Review the purchase packet before you negotiate or approve",
            packet,
            "Review packet",
            "waiting",
            "".join(
                [
                    _form("review_continue", "Continue to terms", "primary"),
                    _form("decline", "Decline this order", "secondary"),
                    _form("reset", "Reset demo", "secondary"),
                ]
            ),
        )
    if phase == "negotiate":
        countered = bool(prep.get("countered"))
        hold = escape(str(prep.get("hold_reply") or ""))
        counter_form = (
            '<form method="post" action="{0}">'
            '<input type="hidden" name="action" value="negotiate_counter">'
            '<label>Counter total <input name="counter_price" value="{1}"></label>'
            '<button class="secondary" type="submit">Send counteroffer</button></form>'
        ).format(SANDBOX_PREFIX, escape(str(prep.get("counter_price") or "180")))
        actions = [
            _form("negotiate_accept", "Accept $189 terms", "primary"),
        ]
        if not countered:
            actions.append(counter_form)
        else:
            actions.append("<p class=\"note\">{0}</p>".format(hold))
        actions.extend(
            [
                _form("decline", "Decline this order", "secondary"),
                _form("reset", "Reset demo", "secondary"),
            ]
        )
        decision = (
            "Supplier B held at $189 — accept to draft the purchase message"
            if countered
            else "Accept Supplier B’s seeded $189 terms, or try one counter"
        )
        return (
            "Negotiate the seeded offer",
            "Supplier B: {0} units · {1} · about {2}-day delivery.".format(
                plan.quantity, _price_breakdown(plan), plan.delivery_days
            ),
            investigation,
            decision,
            "This practice fixture does not invent a discount. Money approval comes after the draft.",
            "Negotiate",
            "waiting",
            "".join(actions),
        )
    if phase == "draft":
        body = prep.get("draft_body") or _default_draft_body(plan)
        draft_form = (
            '<form method="post" action="{0}">'
            '<input type="hidden" name="action" value="draft_send">'
            '<label>Practice purchase message'
            '<textarea name="draft_body" rows="8">{1}</textarea></label>'
            '<button class="primary" type="submit">Send simulated draft</button></form>'
        ).format(SANDBOX_PREFIX, escape(body))
        return (
            "Draft the purchase message",
            "Lock the terms in a practice PO email before money approval.",
            investigation,
            "Send a simulated draft to Supplier B",
            "Editable practice text only — nothing leaves this demo.",
            "Draft message",
            "progress",
            "".join(
                [
                    draft_form,
                    _form("decline", "Decline this order", "secondary"),
                    _form("reset", "Reset demo", "secondary"),
                ]
            ),
        )
    # ready — money approval
    return (
        "Supplier delay puts inventory at risk",
        risk_summary,
        investigation,
        "Order {0} units from Supplier B for ${1}".format(plan.quantity, total),
        "{0}. Approving authorizes spend only — you still submit and confirm before receipt. "
        "Stock stays {1} until you simulate receipt.".format(
            _price_breakdown(plan), _show_units(plan.available_now)
        ),
        "Decision needed",
        "waiting",
        _decision_buttons(total),
    )


def _default_draft_body(plan: ReorderPlan) -> str:
    total = _cash(plan.proposal_total())
    return (
        "To: Supplier B\n"
        "Subject: Purchase order — Quiet linear switch\n\n"
        "Please confirm {qty} units of Quiet linear switch at ${unit} each "
        "plus ${ship} shipping (${total} total), estimated delivery {days} days.\n\n"
        "— Practice shop (simulated)"
    ).format(
        qty=plan.quantity,
        unit=_cash(plan.proposal.unit_price.amount),
        ship=_cash(plan.proposal.fees.amount),
        total=total,
        days=plan.delivery_days,
    )


def _evidence(plan: ReorderPlan, progress: FulfillmentView, order: Optional[tuple], events) -> str:
    from smolstuff.fixtures import RECENT_UNIT_SALES, SUPPLIER_EMAIL

    days = plan.days_of_supply.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    gap = plan.projected_gap_days.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    sales = ", ".join(format(day, "f") for day in RECENT_UNIT_SALES)
    sections = [
        "<h2>Supplier message</h2><pre>{0}</pre>".format(escape(SUPPLIER_EMAIL)),
        _extraction_note(events),
        "<h2>Sales and calculations</h2>",
        "<p>Last {0} days: {1}. Total {2}. Velocity {2} / {0} = {3} units/day.</p>".format(
            plan.sample_days,
            escape(sales),
            escape(_show_units(sum(RECENT_UNIT_SALES, Decimal("0")))),
            escape(_show_units(plan.average_daily_demand)),
        ),
        "<p>Days of supply: {available} / {demand} = {days} days, about {about_days} days. Gap: {lead} − {days} = {gap} days, about {about_gap} days.</p>".format(
            available=escape(_show_units(plan.available_now)),
            demand=escape(_show_units(plan.average_daily_demand)),
            days=escape(format(days, "f")),
            about_days=escape(_whole_days(plan.days_of_supply)),
            lead=plan.lead_time_days,
            gap=escape(format(gap, "f")),
            about_gap=escape(_whole_days(plan.projected_gap_days)),
        ),
        "<h2>Inventory and existing orders</h2>",
        "<p>Available {0}. Reservations 0. Warehouse stock {1}. Open purchase orders {2}. Neither covers the {3}-day lead time.</p>".format(
            escape(_show_units(plan.available_now)),
            escape(_show_units(plan.warehouse_units)),
            escape(_show_units(plan.open_po_units)),
            plan.lead_time_days,
        ),
        "<h2>Supplier B offer</h2>",
        "<p>Seeded offer, not a live web check. Quiet linear switch, 5-pin, factory lubricated, sold by the switch. Approved supplier. Previously purchased SKU. {qty} units available. Minimum order {qty}. Unit price ${price}, previous price ${price}. {breakdown}. Estimated delivery {days} days.</p>".format(
            qty=plan.quantity,
            price=escape(_cash(plan.proposal.unit_price.amount)),
            breakdown=escape(_price_breakdown(plan)),
            days=plan.delivery_days,
        ),
        "<p>Immediate shortage during the new lead time is {0} units. Ordering {1} covers that shortage and buys more than it. This is not an optimized forecast.</p>".format(
            escape(_show_units(plan.immediate_shortage)), plan.quantity
        ),
        "<h2>Policy</h2>",
        "<p>{0}</p>".format(escape(" ".join(plan.policy_result.reasons))),
    ]
    sections.append('<h2 id="confirmation">Approval and confirmation</h2>')
    if order is not None:
        sections.append(
            "<p>Practice order {0}. Replay-safe reference {1}.</p>".format(
                escape(order[0]), escape(order[1])
            )
        )
    else:
        sections.append("<p>No simulated order has been submitted yet.</p>")
    if progress.confirmation_matched:
        sections.append(
            "<p>Confirmation matched the approved product, quantity, and total. "
            "Available inventory stayed at {0}.</p>".format(
                escape(_show_units(plan.available_now))
            )
        )
    elif order is not None:
        sections.append("<p>Supplier confirmation has not been matched yet.</p>")
    sections.append('<h2 id="receipt">Receipt</h2>')
    if progress.received_quantity:
        sections.append(
            "<p>Simulated receipt of {0} units. Available inventory is now {1}. "
            "Accelerated simulation: six days of sales were not subtracted.</p>".format(
                progress.received_quantity, escape(_units(progress.on_hand))
            )
        )
    else:
        sections.append(
            "<p>No simulated receipt recorded yet. Available stock is still {0}.</p>".format(
                escape(_show_units(plan.available_now))
            )
        )
    sections.append("<h2>Tool records</h2>")
    sections.append(_integration_html(events))
    return "".join(sections)


def _extraction_note(events) -> str:
    extraction = next((event for event in reversed(events) if event.task.startswith("Extract")
                       and (event.status == "live" or (event.provider == "Lead-time parser"
                                                      and event.status != "replayed"))), None)
    if extraction is not None and extraction.status == "live":
        return "<p>Arrived through the configured monitoring rule. Lead times came from a schema-checked {0} call. Prices and the spending limit did not.</p>".format(escape(extraction.provider))
    return "<p>Arrived through the configured monitoring rule. Read by the local parser fallback. Not a verified live model call.</p>"


def _cash(amount: Decimal) -> str:
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if quantized == quantized.to_integral_value():
        return format(quantized.to_integral_value(), "f")
    return format(quantized, "f")


def _whole_days(value: Decimal) -> str:
    return format(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP), "f")


def _price_breakdown(plan: ReorderPlan) -> str:
    return "${0} merchandise + ${1} shipping = ${2} total".format(
        _cash(plan.merchandise),
        _cash(plan.proposal.fees.amount),
        _cash(plan.proposal_total()),
    )


def _show_units(value: Decimal) -> str:
    quantized = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if quantized == quantized.to_integral_value():
        return format(quantized.to_integral_value(), "f")
    return format(quantized, "f")


_EMPTY_PAGE = shell(
    "Reorder",
    PRACTICE_BANNER
    + """
<section class="hero decision-hero">
<p class="kicker">Reorder · quiet linear switch</p>
<h1>A supplier delay. One decision. A verified receipt.</h1>
<p class="lede">Walk the full replenishment loop: review the packet, negotiate the seeded offer, draft a practice message, approve $189, submit, confirm, then simulate receipt so available inventory updates.</p>
</section>
<article class="card decision-card">
<p class="status idle">Ready to start</p>
<p class="decision">Start with a permitted supplier message</p>
<p class="consequence">No upload, real inbox, or real purchase. Everything in this path is a practice run.</p>
<div class="card-actions decision-actions">
<form method="post" action="{sandbox}">
<input type="hidden" name="scenario" value="reorder">
<input type="hidden" name="action" value="simulate_email">
<button class="primary" type="submit">Start interactive demo</button>
</form>
</div>
</article>
""".format(sandbox=SANDBOX_PREFIX),
)


def _decision_buttons(total: str) -> str:
    return "".join(
        [
            _form("approve", "Approve simulated ${0} order".format(total), "primary"),
            _form("decline", "Decline this order", "secondary"),
            _form("reset", "Reset demo", "secondary"),
        ]
    )


def _form(action: str, label: str, kind: str) -> str:
    return (
        '<form method="post" action="{0}">'
        '<input type="hidden" name="action" value="{1}">'
        '<button class="{2}" type="submit">{3}</button>'
        "</form>"
    ).format(SANDBOX_PREFIX, escape(action), escape(kind), escape(label))


def _units(value: Optional[Decimal]) -> str:
    if value is None:
        return "unknown"
    quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if quantized == quantized.to_integral_value():
        return format(quantized.to_integral_value(), "f")
    return format(quantized, "f")


def _integration_html(events) -> str:
    if not events:
        return "<p>No tool has run for this demo yet.</p>"
    items = []
    for event in events:
        items.append(
            "<li><strong>{provider}</strong> · {status}<br>{task}<br>{result} {effect}<br><span>{time}</span></li>".format(
                provider=escape(event.provider),
                status=escape(event.status),
                task=escape(event.task),
                result=escape(event.result),
                effect=escape(event.effect),
                time=escape(event.recorded_at),
            )
        )
    return "<ul>{0}</ul>".format("".join(items))


def _built_with(events) -> str:
    if not events:
        return "the local demo shell. No sponsor tool has run."
    labels = []
    for event in events:
        label = "{0} ({1})".format(event.provider, event.status)
        if label not in labels:
            labels.append(label)
    return escape(", ".join(labels))


_SESSION_ID = re.compile(r"^[a-f0-9]{32}$")


def make_handler(app: InboxApp):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                self._send(200, product_home_page())
                return
            if path != SANDBOX_PREFIX:
                self._send(404, error_page("This page could not be found."))
                return
            scenario = parse_qs(urlparse(self.path).query).get("scenario", ["home"])[0]
            self._send(200, app.view(scenario))

        def do_POST(self) -> None:
            if urlparse(self.path).path != SANDBOX_PREFIX:
                self._send(404, error_page("This page could not be found."))
                return
            try:
                fields = read_form(self.headers.get, self.rfile.read, self.headers.get("Host", ""))
            except RequestRejected as rejected:
                self._send(rejected.status, error_page(rejected.message))
                return
            action = fields.get("action", [""])[0]
            try:
                scenario = app.route(action, fields)
            except (ValueError, InvalidOperation):
                self._send(400, error_page())
                return
            self.send_response(303)
            self.send_header("Location", _scenario_location(scenario))
            self.end_headers()

        def log_message(self, fmt: str, *args) -> None:
            return

        def _send(self, status: int, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return Handler


def serve(path: str, host: str = HOST, port: int = PORT) -> None:
    server = HTTPServer((host, port), make_handler(InboxApp(path)))
    print("Action Inbox: http://{0}:{1}".format(host, port), flush=True)
    server.serve_forever()


def make_session_handler(directory: str):
    """Visitor sessions use local SQLite files or configured Postgres rows."""
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                self._send(200, product_home_page())
                return
            if path != SANDBOX_PREFIX:
                self._send(404, error_page("This page could not be found."))
                return
            expire_demo_sessions(str(root))
            scenario = parse_qs(urlparse(self.path).query).get("scenario", ["home"])[0]
            session_id = _read_session(self.headers.get("Cookie", ""))
            db_path = None if session_id is None else root / "{0}.sqlite3".format(session_id)
            if session_id is None or not (db_path.is_file() or _session_in_database(session_id)):
                self._send(200, _blank_scenario(scenario))
                return
            self._send(200, InboxApp(str(db_path), session_id=session_id).view(scenario))

        def do_POST(self) -> None:
            if urlparse(self.path).path != SANDBOX_PREFIX:
                self._send(404, error_page("This page could not be found."))
                return
            expire_demo_sessions(str(root))
            try:
                fields = read_form(self.headers.get, self.rfile.read, self.headers.get("Host", ""))
            except RequestRejected as rejected:
                self._send(rejected.status, error_page(rejected.message))
                return
            action = fields.get("action", [""])[0]
            try:
                session_id, new_cookie = open_session(str(root), self.headers.get("Cookie", ""))
            except SessionLimited:
                self._send(429, error_page("Too many new demos. Try again later."))
                return
            db_path = root / "{0}.sqlite3".format(session_id)
            try:
                scenario = InboxApp(str(db_path), session_id=session_id).route(action, fields)
            except (ValueError, InvalidOperation):
                self._send(400, error_page())
                return
            self._redirect(session_id if new_cookie else None, scenario)

        def log_message(self, fmt: str, *args) -> None:
            return

        def _redirect(self, session_id: Optional[str], scenario: str = "home") -> None:
            self.send_response(303)
            self.send_header("Location", _scenario_location(scenario))
            if session_id:
                self.send_header("Set-Cookie", _session_cookie(session_id))
            self.end_headers()

        def _send(self, status: int, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return Handler


def serve_sessions(directory: str, host: str = HOST, port: int = PORT) -> None:
    handler = make_session_handler(directory)
    if host in ("127.0.0.1", "localhost", "::1"):
        _serve_loopback(handler, port)
        return
    server = HTTPServer((host, port), handler)
    print("Action Inbox: http://{0}:{1}".format(host, port), flush=True)
    server.serve_forever()


def _serve_loopback(handler, port: int) -> None:
    """Accept both 127.0.0.1 and localhost. macOS resolves localhost to IPv6 first."""
    servers = []
    for family, address in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            servers.append(_bound_server(family, address, port, handler))
        except OSError:
            continue
    if not servers:
        raise OSError("The local demo could not bind to localhost.")
    print("Action Inbox: http://localhost:{0}".format(port), flush=True)
    for extra in servers[1:]:
        Thread(target=extra.serve_forever, daemon=True).start()
    servers[0].serve_forever()


def _bound_server(family: int, address: str, port: int, handler):
    class BoundServer(HTTPServer):
        address_family = family

    return BoundServer((address, port), handler)


def main() -> None:
    _load_local_env()
    root = Path(__file__).resolve().parents[2]
    directory = root / "data" / "sessions"
    port = int(os.environ.get("PORT", str(PORT)))
    host = "0.0.0.0" if "PORT" in os.environ else HOST
    serve_sessions(str(directory), host, port)


def _blank_scenario(scenario: str) -> str:
    if scenario == "workshop":
        return workshop_page(None)
    if scenario == "detective":
        return detective_page(None)
    if scenario == "rescue":
        return rescue_page(None)
    if scenario == "staffing":
        return staffing_page(None)
    if scenario == "inventory":
        return inventory_page(empty_inventory_snapshot())
    if scenario == "reorder":
        return _EMPTY_PAGE
    return dashboard_page(empty_cards())


def _load_local_env() -> None:
    """Read .env into the process. Never print the values."""
    path = Path(__file__).resolve().parents[2] / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = value


def _session_in_database(session_id: str) -> bool:
    from smolstuff.database import persisted_session

    return persisted_session(session_id)


def open_session(directory: str, cookie_header: str):
    """Return a server-issued session. A client-chosen id counts only when its file exists."""
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    requested = _read_session(cookie_header or "")
    if requested and (
        (root / "{0}.sqlite3".format(requested)).is_file()
        or _session_in_database(requested)
    ):
        return requested, False
    if not reserve_session(str(root)):
        raise SessionLimited()
    return uuid.uuid4().hex, True


_KNOWN_SCENARIOS = {"reorder", "inventory", "workshop", "detective", "rescue", "staffing"}


def _scenario_location(scenario: str) -> str:
    if scenario not in _KNOWN_SCENARIOS:
        return SANDBOX_PREFIX
    return sandbox_href(scenario)


def _read_session(cookie_header: str) -> Optional[str]:
    for part in cookie_header.split(";"):
        name, _, value = part.strip().partition("=")
        if name == "smol_session" and _SESSION_ID.match(value):
            return value
    return None


def _session_cookie(session_id: str) -> str:
    cookie = "smol_session={0}; HttpOnly; SameSite=Lax; Path=/; Max-Age=86400".format(session_id)
    if os.environ.get("DEMO_COOKIE_SECURE") == "1" or os.environ.get("VERCEL") == "1":
        cookie += "; Secure"
    return cookie


if __name__ == "__main__":
    main()
