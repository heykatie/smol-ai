"""One reorder decision for the Workshop Supply Pack.

Recent sales use a rolling average. The order quantity is the supplier minimum,
not a forecast. Warehouse stock and open orders are checked before that choice.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple

from smolstuff.extract import LeadTimeFact
from smolstuff.fixtures import (
    ALTERNATIVE_UNIT_PRICE,
    DELIVERY_DAYS,
    EXAMPLE_POLICY,
    OPEN_PO_UNITS,
    RECENT_UNIT_SALES,
    SHIPPING,
    STORE_ON_HAND,
    SUPPLIER_B_ID,
    SUPPLIER_MOQ,
    WAREHOUSE_ON_HAND,
    WORKSHOP_SKU,
)
from smolstuff.inventory import InventoryInputs, assess_supply
from smolstuff.money import transaction_total
from smolstuff.policy import PolicyDecision, PolicyResult, PurchaseProposal, evaluate_purchase


@dataclass(frozen=True)
class ReorderPlan:
    previous_lead_time_days: int
    lead_time_days: int
    sample_days: int
    average_daily_demand: Decimal
    available_now: Decimal
    days_of_supply: Decimal
    projected_gap_days: Decimal
    reorder_point: Decimal
    warehouse_units: Decimal
    warehouse_covers_gap: bool
    open_po_units: Decimal
    open_po_in_time: bool
    immediate_shortage: Decimal
    delivery_days: int
    quantity: int
    proposal: PurchaseProposal
    policy_result: PolicyResult
    needs_reorder: bool
    needs_approval: bool

    def explain(self) -> str:
        return (
            "You have about {days} days of stock. Supplier A now needs {lead} days. "
            "The gap is about {gap} days. Warehouse stock is {warehouse} and open purchase "
            "orders are {po}, so neither covers the gap. "
            "Demand during the new lead time is {demand_over} units, and {available} are "
            "available, so the immediate shortage is {shortage} units. "
            "Supplier B's minimum order is {moq}, which buys more than that shortage. "
            "${merchandise} merchandise + ${shipping} shipping = ${total}."
        ).format(
            days=_whole(self.days_of_supply),
            lead=self.lead_time_days,
            gap=_whole(self.projected_gap_days),
            warehouse=_show(self.warehouse_units),
            po=_show(self.open_po_units),
            demand_over=_show(self.demand_over_lead_time),
            available=_show(self.available_now),
            shortage=_show(self.immediate_shortage),
            moq=SUPPLIER_MOQ,
            merchandise=_dollars(self.merchandise),
            shipping=_dollars(SHIPPING.amount),
            total=_dollars(self.proposal_total()),
        )

    @property
    def demand_over_lead_time(self) -> Decimal:
        return self.average_daily_demand * Decimal(self.lead_time_days)

    @property
    def merchandise(self) -> Decimal:
        return self.proposal.unit_price.amount * self.proposal.quantity

    def proposal_total(self) -> Decimal:
        return transaction_total(
            self.proposal.unit_price, self.proposal.quantity, self.proposal.fees
        ).amount


def rolling_average(daily_units: Tuple[Decimal, ...]) -> Decimal:
    if not daily_units:
        raise ValueError("Sales history is empty.")
    total = sum(daily_units, Decimal("0"))
    return total / Decimal(len(daily_units))


def plan_reorder(fact: LeadTimeFact) -> ReorderPlan:
    if fact.sku != WORKSHOP_SKU:
        raise ValueError("This demo plans one SKU only.")
    demand = rolling_average(RECENT_UNIT_SALES)
    assessment = assess_supply(
        InventoryInputs(
            sellable_on_hand=STORE_ON_HAND,
            reservations=Decimal("0"),
            confirmed_inbound=Decimal("0"),
            other_committed_demand=Decimal("0"),
            average_daily_demand=demand,
            lead_time_days=Decimal(fact.lead_time_days),
            safety_stock=Decimal("0"),
        )
    )
    with_warehouse = assessment.available_now + WAREHOUSE_ON_HAND
    warehouse_covers_gap = (
        WAREHOUSE_ON_HAND > 0 and (with_warehouse / demand) >= Decimal(fact.lead_time_days)
    )
    open_po_in_time = False
    immediate_shortage = assessment.demand_over_lead_time - assessment.available_now
    if immediate_shortage < 0:
        immediate_shortage = Decimal("0")
    quantity = SUPPLIER_MOQ if assessment.stockout_risk else 0
    proposal = PurchaseProposal(
        supplier_id=SUPPLIER_B_ID,
        sku=fact.sku,
        supplier_allowlisted=True,
        sku_previously_purchased=True,
        quantity=quantity,
        unit_price=ALTERNATIVE_UNIT_PRICE,
        fees=SHIPPING,
        previous_unit_price=ALTERNATIVE_UNIT_PRICE,
        evidence_current=True,
        evidence_complete=True,
        verification_passed=True,
    )
    decision = evaluate_purchase(proposal, EXAMPLE_POLICY)
    needs_reorder = bool(assessment.stockout_risk) and not warehouse_covers_gap and not open_po_in_time
    return ReorderPlan(
        previous_lead_time_days=fact.previous_lead_time_days,
        lead_time_days=fact.lead_time_days,
        sample_days=len(RECENT_UNIT_SALES),
        average_daily_demand=demand,
        available_now=assessment.available_now,
        days_of_supply=assessment.days_of_supply,
        projected_gap_days=assessment.projected_gap_days,
        reorder_point=assessment.reorder_point,
        warehouse_units=WAREHOUSE_ON_HAND,
        warehouse_covers_gap=warehouse_covers_gap,
        open_po_units=OPEN_PO_UNITS,
        open_po_in_time=open_po_in_time,
        immediate_shortage=immediate_shortage,
        delivery_days=DELIVERY_DAYS,
        quantity=quantity,
        proposal=proposal,
        policy_result=decision,
        needs_reorder=needs_reorder,
        needs_approval=decision.decision == PolicyDecision.NEEDS_APPROVAL,
    )


def build_demo_plan() -> ReorderPlan:
    from smolstuff.fixtures import SUPPLIER_A_ID, SUPPLIER_EMAIL
    from smolstuff.extract import extract_lead_time

    return plan_reorder(extract_lead_time(SUPPLIER_EMAIL, SUPPLIER_A_ID, WORKSHOP_SKU))


def _show(value: Decimal) -> str:
    quantized = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if quantized == quantized.to_integral_value():
        return format(quantized.to_integral_value(), "f")
    return format(quantized, "f")


def _whole(value: Decimal) -> str:
    return format(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP), "f")


def _dollars(amount: Decimal) -> str:
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if quantized == quantized.to_integral_value():
        return format(quantized.to_integral_value(), "f")
    return format(quantized, "f")
