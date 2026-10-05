"""Local Action Inbox.

A browser page over the saved purchase workflow. The numbers and the approval
come from the deterministic core. A configured sponsor may add a labeled record.
It cannot change quantity, price, or approval.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from pathlib import Path
import re
from string import Template
from typing import Optional
import uuid
from urllib.parse import parse_qs, urlparse

from smolstuff.fixtures import EXAMPLE_POLICY, WORKSHOP_SUPPLY_PACK
from smolstuff.inventory import SupplyAssessment, assess_supply
from smolstuff.lifecycle import WorkflowState
from smolstuff.reorder import ReorderPlan, build_demo_plan, plan_reorder
from smolstuff.demo_ui import (
    apply_ops,
    dashboard_page,
    detective_page,
    empty_cards,
    load_cards,
    rescue_page,
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
_ACTIONS = (
    "simulate_email",
    "approve",
    "decline",
    "reset",
    "confirm",
    "receive_full",
    "receive_short",
    "receive_rest",
)

_PAGE = Template(
    """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>smolstuff — Action Inbox</title>
  <style>
    :root { color-scheme: light; }
    body {
      margin: 0;
      font-family: Georgia, "Iowan Old Style", serif;
      background: #f6f3ec;
      color: #1c1915;
    }
    main { max-width: 40rem; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }
    .eyebrow { font-family: ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.04em; text-transform: uppercase; font-size: 0.75rem; color: #6b645b; }
    h1 { font-size: 2rem; line-height: 1.15; margin: 0.4rem 0 0.25rem; }
    .product { margin: 0 0 1.25rem; font-size: 1.15rem; }
    .card { background: #fffdf8; border: 1px solid #e2d9cc; border-radius: 14px; padding: 1.25rem; }
    .status { display: inline-block; font-family: ui-sans-serif, system-ui, sans-serif; font-size: 0.8rem; padding: 0.2rem 0.55rem; border-radius: 999px; background: #f3e2c4; }
    .status.executing, .status.completed { background: #d9ead8; }
    .status.declined, .status.cancelled, .status.recovery { background: #ece7e1; }
    dl { display: grid; grid-template-columns: 11rem 1fr; gap: 0.45rem 0.75rem; margin: 1rem 0; }
    dt { color: #6b645b; }
    dd { margin: 0; }
    .decision { font-size: 1.2rem; margin: 0.5rem 0 1rem; }
    form { display: inline; }
    button { font-family: ui-sans-serif, system-ui, sans-serif; font-size: 1rem; border-radius: 999px; padding: 0.55rem 0.95rem; margin: 0 0.4rem 0.4rem 0; cursor: pointer; }
    button.primary { background: #1c1915; color: #fffdf8; border: 1px solid #1c1915; }
    button.secondary, summary.evidence { background: transparent; border: 1px solid #c9bfb2; }
    summary.evidence { display: inline-block; border-radius: 999px; padding: 0.55rem 0.95rem; margin: 0 0.4rem 0.4rem 0; cursor: pointer; font-family: ui-sans-serif, system-ui, sans-serif; font-size: 1rem; }
    summary.evidence::-webkit-details-marker { display: none; }
    button:focus-visible, summary:focus-visible, a:focus-visible { outline: 2px solid #1c1915; outline-offset: 3px; }
    h2 { font-family: ui-sans-serif, system-ui, sans-serif; font-size: 1rem; margin: 1.25rem 0 0.4rem; }
    ol { margin: 0; padding-left: 1.2rem; font-family: ui-sans-serif, system-ui, sans-serif; font-size: 0.92rem; }
    li { margin: 0.25rem 0; }
    .note, .built-with { font-family: ui-sans-serif, system-ui, sans-serif; color: #6b645b; font-size: 0.9rem; }
  </style>
</head>
<body>
  <main>
    <p class="eyebrow">Fictional business data. Purchases and deliveries are simulated.</p>
    <h1>$headline</h1>
    <p class="product">$summary</p>
    <article class="card">
      <p class="status $status_class">$status_label</p>
      <p>$investigation</p>
      <p class="decision">$decision</p>
      <p class="note">$note</p>
      $actions
      <details id="evidence">
        <summary class="evidence">Review evidence</summary>
        $evidence
      </details>
      <p class="built-with"><strong>Built with</strong> $built_with</p>
    </article>
  </main>
</body>
</html>
"""
)


class InboxApp:
    def __init__(self, path: str) -> None:
        self.path = path

    def page(self) -> str:
        store = WorkflowStore(self.path)
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
                workflow, assess_supply(WORKSHOP_SUPPLY_PACK), order, progress, plan, events
            )
        finally:
            store.close()

    def apply(self, action: str) -> None:
        if action == "start":
            action = "simulate_email"
        if action not in _ACTIONS:
            raise ValueError("Unknown inbox action.")
        baseline = WORKSHOP_SUPPLY_PACK.sellable_on_hand
        store = WorkflowStore(self.path)
        try:
            if action == "reset":
                store.reset_signal(DEMO_SIGNAL_KEY)
                ScenarioStore(self.path).reset("supplier_fact")
                return
            if action == "simulate_email":
                attempt = self._extract_supplier_fact()
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
                self._approve(store, workflow, plan, baseline)
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

    def _approve(self, store, workflow, plan, baseline) -> None:
        workflow_id = workflow.workflow_id
        if workflow.state == WorkflowState.WAITING_FOR_APPROVAL:
            store.approve(workflow_id, actor="owner")
        current = store.get(workflow_id)
        executed = None
        if current.state in (WorkflowState.APPROVED, WorkflowState.AUTHORIZED):
            executed = store.execute(workflow_id, plan.proposal, EXAMPLE_POLICY)
            store.record_integration(
                PURCHASE_ADAPTER,
                "Submit the approved purchase",
                executed.reason,
                "No second order was created." if executed.replayed else "One simulated order is waiting for confirmation.",
                "replayed" if executed.replayed else "simulated",
            )
            current = store.get(workflow_id)
        if current.state == WorkflowState.EXECUTING:
            confirmed = store.confirm(workflow_id, plan.proposal, baseline)
            self._record_confirmation(store, confirmed)
            return
        if executed is None and current.state in (
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
            apply_ops(self.path, action, fields)
            return fields.get("scenario", ["home"])[0]
        self.apply(action)
        return fields.get("scenario", ["reorder"])[0]

    def _saved_page(self, name: str, renderer):
        if not os.path.exists(self.path):
            return renderer(None)
        store = ScenarioStore(self.path)
        try:
            return renderer(store.get(name))
        finally:
            store.close()

    def _home(self) -> str:
        status, bucket, action = self._reorder_card()
        if os.path.exists(self.path):
            cards = load_cards(self.path, status, bucket, action)
            event_store = WorkflowStore(self.path)
            try:
                events = event_store.list_integration_events()
            finally:
                event_store.close()
        else:
            cards = empty_cards()
            events = ()
        return dashboard_page(cards, events)

    def _reorder_card(self):
        start = (
            '<form method="post" action="/"><input type="hidden" name="scenario" value="reorder">'
            '<input type="hidden" name="action" value="simulate_email">'
            '<button class="primary" type="submit">Start interactive demo</button></form>'
        )
        if not os.path.exists(self.path):
            return "Not started", "Not started", start
        store = WorkflowStore(self.path)
        try:
            workflow = store.find_by_dedup(DEMO_SIGNAL_KEY)
        finally:
            store.close()
        if workflow is None:
            return "Not started", "Not started", start
        if workflow.state == WorkflowState.WAITING_FOR_APPROVAL:
            approve = (
                '<form method="post" action="/"><input type="hidden" name="scenario" value="reorder">'
                '<input type="hidden" name="action" value="approve">'
                '<button class="primary" type="submit">Approve simulated $61 order</button></form>'
            )
            return "Decision needed", "Needs your decision", approve
        if workflow.state == WorkflowState.AWAITING_RECEIPT:
            return "Awaiting receipt", "In progress", ""
        if workflow.state == WorkflowState.COMPLETED:
            return "Replenishment workflow completed", "Completed", ""
        if workflow.state == WorkflowState.DECLINED:
            return "Declined", "Completed", ""
        return workflow.state.value, "In progress", ""

    def _plan(self):
        saved = None
        if os.path.exists(self.path):
            store = ScenarioStore(self.path)
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

    def _record_supplier_research(self, store) -> None:
        from smolstuff.research import research_supplier

        attempt = research_supplier()
        store.record_integration(
            attempt.provider,
            attempt.task,
            attempt.result,
            attempt.effect,
            attempt.status,
        )

    def _extract_supplier_fact(self):
        from smolstuff.extract import call_novita, resolve_lead_time
        from smolstuff.fixtures import SUPPLIER_A_ID, SUPPLIER_EMAIL, WORKSHOP_SKU

        model_result = None
        model_error = False
        if os.environ.get("NOVITA_API_KEY"):
            try:
                model_result = call_novita(SUPPLIER_EMAIL)
            except Exception:
                model_error = True
        return resolve_lead_time(SUPPLIER_EMAIL, SUPPLIER_A_ID, WORKSHOP_SKU, model_result, model_error)

    def _save_supplier_fact(self, attempt) -> None:
        ScenarioStore(self.path).save("supplier_fact", {
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
) -> str:
    headline, summary, investigation, decision, note, status_label, status_class, actions = _status_copy(
        progress, order, plan
    )
    return _PAGE.substitute(
        headline=escape(headline),
        summary=escape(summary),
        investigation=escape(investigation),
        decision=escape(decision),
        note=escape(note),
        status_class=status_class,
        status_label=escape(status_label),
        actions=actions,
        evidence=_evidence(plan, progress, order, events),
        built_with=_built_with(events),
    )


def _status_copy(progress, order, plan: ReorderPlan):
    state = progress.workflow_state
    on_hand = _units(progress.on_hand)
    if state == WorkflowState.WAITING_FOR_APPROVAL:
        total = _cash(plan.proposal_total())
        return (
            "Supplier delay puts inventory at risk",
            "You have about {0} days of stock. Your supplier now needs {1} days to replenish it.".format(
                _whole_days(plan.days_of_supply), plan.lead_time_days
            ),
            "There is about a {0}-day gap. Warehouse stock and existing orders cannot cover the gap. Supplier B offers an alternative with an estimated {1}-day delivery.".format(
                _whole_days(plan.projected_gap_days), plan.delivery_days
            ),
            "Order {0} units from Supplier B".format(plan.quantity),
            "{0}. Minimum order: {1} units. This buys more than the immediate shortage. This purchase exceeds your below-$40 automatic spending limit. The other configured checks pass.".format(
                _price_breakdown(plan), plan.quantity
            ),
            "Decision needed",
            "waiting",
            _decision_buttons(total),
        )
    if state == WorkflowState.EXECUTING and order is not None:
        return (
            "Purchase submitted",
            "Order {0} is awaiting supplier confirmation.".format(order[0]),
            "Available inventory is still {0}. Confirmation has not finished.".format(
                _show_units(plan.available_now)
            ),
            "This step does not complete the workflow.",
            "On hand is still {0}.".format(on_hand),
            "Purchase submitted",
            "executing",
            "".join(
                [
                    _form("confirm", "Resume simulated confirmation", "primary"),
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
            "Stock has not changed.",
            "Awaiting receipt",
            "waiting",
            "".join(
                [
                    _form(
                        "receive_full",
                        "Simulate receiving {0} units".format(plan.quantity),
                        "primary",
                    ),
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
                    _form("reset", "Reset demo", "secondary"),
                ]
            ),
        )
    if state == WorkflowState.COMPLETED:
        return (
            "Replenishment workflow completed",
            "{0} units received. Available inventory updated from {1} to {2}.".format(
                progress.received_quantity, _units(plan.available_now), on_hand
            ),
            "The {0}-day delivery estimate was a supplier term. This receipt was an accelerated simulation.".format(
                plan.delivery_days
            ),
            "1 owner approval. Receipt verified. Inventory reconciled.",
            "On hand is now {0}.".format(on_hand),
            "Completed",
            "completed",
            _form("reset", "Reset demo", "secondary"),
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
        "<p>Seeded offer, not a live web check. Approved supplier. Previously purchased SKU. {qty} units available. Minimum order {qty}. Unit price ${price}, previous price ${price}. {breakdown}. Estimated delivery {days} days.</p>".format(
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
    if order is not None:
        sections.append("<h2>Approval and confirmation</h2>")
        sections.append(
            "<p>Simulated order {0}. Idempotency key {1}.</p>".format(escape(order[0]), escape(order[1]))
        )
    if progress.confirmation_matched:
        sections.append("<p>Confirmation matched the approved product, quantity, and total. Available inventory stayed at {0}.</p>".format(
            escape(_show_units(plan.available_now))
        ))
    if progress.received_quantity:
        sections.append("<h2>Receipt</h2>")
        sections.append(
            "<p>Simulated receipt of {0} units. Available inventory is now {1}. Accelerated simulation: six days of sales were not subtracted.</p>".format(
                progress.received_quantity, escape(_units(progress.on_hand))
            )
        )
    sections.append("<h2>Tool records</h2>")
    sections.append(_integration_html(events))
    return "".join(sections)


def _extraction_note(events) -> str:
    extraction = next((event for event in events if event.task.startswith("Extract")), None)
    if extraction is not None and extraction.status == "live":
        return "<p>Arrived through the configured monitoring rule. Lead times came from a verified Novita call. Prices and the spending limit did not.</p>"
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


_EMPTY_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>smolstuff — Action Inbox</title>
  <style>
    body { margin: 0; font-family: Georgia, serif; background: #f6f3ec; color: #1c1915; }
    main { max-width: 40rem; margin: 0 auto; padding: 2.5rem 1.25rem; }
    button { font-family: ui-sans-serif, system-ui, sans-serif; font-size: 1rem; border-radius: 999px; padding: 0.55rem 0.95rem; background: #1c1915; color: #fffdf8; border: 0; cursor: pointer; }
    p { font-family: ui-sans-serif, system-ui, sans-serif; }
  </style>
</head>
<body>
  <main>
    <p>Fictional business data. Purchases and deliveries are simulated.</p>
    <h1>Your operations, followed through.</h1>
    <p>smolstuff connects business signals, investigates what needs attention, and completes routine workflows within rules you control.</p>
    <form method="post" action="/">
      <input type="hidden" name="action" value="simulate_email">
      <button type="submit">Start interactive demo</button>
    </form>
  </main>
</body>
</html>
"""


def _decision_buttons(total: str) -> str:
    return "".join(
        [
            _form("approve", "Approve simulated ${0} order".format(total), "primary"),
            _form("decline", "Decline", "secondary"),
            _form("reset", "Reset demo", "secondary"),
        ]
    )


def _form(action: str, label: str, kind: str) -> str:
    return (
        '<form method="post" action="/">'
        '<input type="hidden" name="action" value="{0}">'
        '<button class="{1}" type="submit">{2}</button>'
        "</form>"
    ).format(escape(action), escape(kind), escape(label))


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
            if urlparse(self.path).path != "/":
                self._send(404, "Not found")
                return
            scenario = parse_qs(urlparse(self.path).query).get("scenario", ["home"])[0]
            self._send(200, app.view(scenario))

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/":
                self._send(404, "Not found")
                return
            length = int(self.headers.get("Content-Length", "0"))
            fields = parse_qs(self.rfile.read(length).decode("utf-8"))
            action = fields.get("action", [""])[0]
            try:
                scenario = app.route(action, fields)
            except ValueError:
                self._send(400, "Unknown action")
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
    """One SQLite file per visitor cookie. Visitors do not share a workflow."""
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if urlparse(self.path).path != "/":
                self._send(404, "Not found")
                return
            scenario = parse_qs(urlparse(self.path).query).get("scenario", ["home"])[0]
            session_id = _read_session(self.headers.get("Cookie", ""))
            path = None if session_id is None else root / "{0}.sqlite3".format(session_id)
            if path is None or not path.exists():
                self._send(200, _blank_scenario(scenario))
                return
            self._send(200, InboxApp(str(path)).view(scenario))

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/":
                self._send(404, "Not found")
                return
            length = int(self.headers.get("Content-Length", "0"))
            fields = parse_qs(self.rfile.read(length).decode("utf-8"))
            action = fields.get("action", [""])[0]
            session_id = _read_session(self.headers.get("Cookie", ""))
            new_cookie = False
            if session_id is None:
                session_id = uuid.uuid4().hex
                new_cookie = True
            path = root / "{0}.sqlite3".format(session_id)
            try:
                scenario = InboxApp(str(path)).route(action, fields)
            except ValueError:
                self._send(400, "Unknown action")
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
    server = HTTPServer((host, port), make_session_handler(directory))
    print("Action Inbox: http://{0}:{1}".format(host, port), flush=True)
    server.serve_forever()


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


def _scenario_location(scenario: str) -> str:
    if not scenario or scenario == "home":
        return "/"
    return "/?scenario={0}".format(scenario)


def _read_session(cookie_header: str) -> Optional[str]:
    for part in cookie_header.split(";"):
        name, _, value = part.strip().partition("=")
        if name == "smol_session" and _SESSION_ID.match(value):
            return value
    return None


def _session_cookie(session_id: str) -> str:
    cookie = "smol_session={0}; HttpOnly; SameSite=Lax; Path=/; Max-Age=86400".format(session_id)
    if os.environ.get("DEMO_COOKIE_SECURE") == "1":
        cookie += "; Secure"
    return cookie


if __name__ == "__main__":
    main()
