from decimal import Decimal, ROUND_HALF_UP

import pytest

from smolstuff.fixtures import WORKSHOP_SUPPLY_PACK
from smolstuff.inventory import InventoryInputs, assess_supply


def _cents(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def test_canonical_fixture_matches_the_contract():
    assessment = assess_supply(WORKSHOP_SUPPLY_PACK)

    assert assessment.available_now == Decimal("21")
    assert _cents(assessment.days_of_supply) == Decimal("19.09")
    assert _cents(assessment.projected_gap_days) == Decimal("15.91")
    assert assessment.demand_over_lead_time == Decimal("38.5")
    assert assessment.reorder_point == Decimal("38.5")
    assert assessment.stockout_risk is True


def test_inbound_is_not_sellable_and_reservations_count_once():
    inputs = InventoryInputs(
        sellable_on_hand=Decimal("21"),
        reservations=Decimal("4"),
        confirmed_inbound=Decimal("10"),
        other_committed_demand=Decimal("0"),
        average_daily_demand=Decimal("1.1"),
        lead_time_days=Decimal("35"),
    )

    assessment = assess_supply(inputs)

    assert assessment.available_now == Decimal("17")
    assert inputs.committed_demand == Decimal("4")
    assert assessment.inventory_position == Decimal("27")


def test_other_committed_demand_is_separate_from_reservations():
    inputs = InventoryInputs(
        sellable_on_hand=Decimal("21"),
        reservations=Decimal("4"),
        confirmed_inbound=Decimal("0"),
        other_committed_demand=Decimal("3"),
        average_daily_demand=Decimal("1"),
        lead_time_days=Decimal("10"),
    )

    assessment = assess_supply(inputs)

    assert assessment.available_now == Decimal("17")
    assert assessment.inventory_position == Decimal("14")


def test_zero_demand_does_not_invent_a_stockout():
    inputs = InventoryInputs(
        sellable_on_hand=Decimal("21"),
        reservations=Decimal("0"),
        confirmed_inbound=Decimal("0"),
        other_committed_demand=Decimal("0"),
        average_daily_demand=Decimal("0"),
        lead_time_days=Decimal("35"),
        safety_stock=Decimal("2"),
    )

    assessment = assess_supply(inputs)

    assert assessment.days_of_supply is None
    assert assessment.projected_gap_days is None
    assert assessment.stockout_risk is False
    assert assessment.reorder_point == Decimal("2")


def test_reservations_above_on_hand_are_rejected():
    with pytest.raises(ValueError, match="Reservations"):
        InventoryInputs(
            sellable_on_hand=Decimal("5"),
            reservations=Decimal("6"),
            confirmed_inbound=Decimal("0"),
            other_committed_demand=Decimal("0"),
            average_daily_demand=Decimal("1"),
            lead_time_days=Decimal("7"),
        )
