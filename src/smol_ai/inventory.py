"""Inventory planning formulas from the product contract.

Reservations are subtracted once. Confirmed inbound is not sellable until receipt.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


def _units(value: Decimal, name: str) -> Decimal:
    if isinstance(value, float) or isinstance(value, bool):
        raise TypeError("{0} rejects float. Use Decimal.".format(name))
    if not isinstance(value, Decimal):
        raise TypeError("{0} must be Decimal.".format(name))
    if value < 0:
        raise ValueError("{0} cannot be negative.".format(name))
    return value


@dataclass(frozen=True)
class InventoryInputs:
    """Quantities for one SKU at the moment of a planning decision.

    `other_committed_demand` is demand that is not already in `reservations`
    (for example a workshop that is promised but not yet reserved). Adding a
    reservation into both fields would count it twice.
    """

    sellable_on_hand: Decimal
    reservations: Decimal
    confirmed_inbound: Decimal
    other_committed_demand: Decimal
    average_daily_demand: Decimal
    lead_time_days: Decimal
    safety_stock: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        on_hand = _units(self.sellable_on_hand, "sellable_on_hand")
        reservations = _units(self.reservations, "reservations")
        inbound = _units(self.confirmed_inbound, "confirmed_inbound")
        other = _units(self.other_committed_demand, "other_committed_demand")
        demand = _units(self.average_daily_demand, "average_daily_demand")
        lead_time = _units(self.lead_time_days, "lead_time_days")
        safety = _units(self.safety_stock, "safety_stock")
        if reservations > on_hand:
            raise ValueError("Reservations cannot exceed sellable on-hand.")
        object.__setattr__(self, "sellable_on_hand", on_hand)
        object.__setattr__(self, "reservations", reservations)
        object.__setattr__(self, "confirmed_inbound", inbound)
        object.__setattr__(self, "other_committed_demand", other)
        object.__setattr__(self, "average_daily_demand", demand)
        object.__setattr__(self, "lead_time_days", lead_time)
        object.__setattr__(self, "safety_stock", safety)

    @property
    def committed_demand(self) -> Decimal:
        return self.reservations + self.other_committed_demand


@dataclass(frozen=True)
class SupplyAssessment:
    available_now: Decimal
    inventory_position: Decimal
    days_of_supply: Optional[Decimal]
    projected_gap_days: Optional[Decimal]
    demand_over_lead_time: Decimal
    reorder_point: Decimal

    @property
    def stockout_risk(self) -> bool:
        """True when known demand would run out before this lead time ends."""
        return self.projected_gap_days is not None and self.projected_gap_days > 0


def assess_supply(inputs: InventoryInputs) -> SupplyAssessment:
    available_now = inputs.sellable_on_hand - inputs.reservations
    inventory_position = (
        inputs.sellable_on_hand + inputs.confirmed_inbound - inputs.committed_demand
    )
    demand_over_lead_time = inputs.average_daily_demand * inputs.lead_time_days
    reorder_point = demand_over_lead_time + inputs.safety_stock

    if inputs.average_daily_demand == 0:
        days_of_supply = None
        projected_gap_days = None
    else:
        days_of_supply = available_now / inputs.average_daily_demand
        projected_gap_days = inputs.lead_time_days - days_of_supply

    return SupplyAssessment(
        available_now=available_now,
        inventory_position=inventory_position,
        days_of_supply=days_of_supply,
        projected_gap_days=projected_gap_days,
        demand_over_lead_time=demand_over_lead_time,
        reorder_point=reorder_point,
    )
