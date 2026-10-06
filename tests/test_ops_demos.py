from decimal import Decimal

import pytest

from smolstuff.ops_demos import (
    apply_recount,
    apply_usage_correction,
    assess_workshop,
    confirm_workshop_evidence,
    default_offers,
    detective_days_of_supply,
    investigate_stock,
    merchant_contribution,
    negotiate,
    staffing_plan,
    workshop_approve,
    workshop_complete,
    workshop_receive,
)


def test_default_workshop_is_feasible_with_a_minimum_order():
    result = assess_workshop(20, 7)

    assert result["shortage"] == 2
    assert result["purchase"] == 10
    # Procurement buys only the bottleneck 70-pack line ($14), not a sealed kit.
    assert result["procurement_cash"] == "140.00"
    assert result["materials_consumed"] == "400.00"
    assert result["contribution"] == "700.00"
    assert result["inventory_after"] == 8
    assert result["verdict"] == "feasible_with_conditions"
    assert len(result["bom"]) == 3
    pack = next(item for item in result["bom"] if item["bottleneck"])
    assert pack["sku"] == "DEMO-ITM-WS-PACK"
    assert pack["purchase"] == 10
    assert pack["after_units"] == 8


def test_no_shortage_does_not_force_a_minimum_order():
    result = assess_workshop(18, 2)

    assert result["shortage"] == 0
    assert result["purchase"] == 0
    assert result["verdict"] == "feasible"
    assert result["inventory_after"] == 0


def test_short_lead_time_blocks_a_missing_kit_purchase():
    result = assess_workshop(20, 2)

    assert result["verdict"] == "blocked"
    with pytest.raises(ValueError, match="blocked"):
        workshop_approve(result)


def test_workshop_completion_consumes_kits_once():
    assessed = assess_workshop(20, 7)
    approved = workshop_approve(assessed)
    with pytest.raises(ValueError, match="Materials"):
        workshop_complete(approved)
    received = workshop_receive(approved)
    done = workshop_complete(received)
    again = workshop_complete(done)

    assert done["phase"] == "completed"
    assert done["inventory_after"] == 8
    assert again["replayed"] is True
    assert again["inventory_after"] == 8


def test_detective_separates_fact_hypothesis_and_unknown():
    case = investigate_stock(16)

    assert case["discrepancy"] == 4
    assert case["hypothesis_units"] == 3
    with pytest.raises(ValueError, match="not confirmed"):
        apply_usage_correction(case)
    confirmed = confirm_workshop_evidence(case)
    corrected = apply_usage_correction(confirmed)

    assert corrected["system_inventory"] == 17
    assert corrected["original_physical_count"] == 16
    assert corrected["unresolved"] == 1
    assert corrected["closed"] is False
    assert detective_days_of_supply(corrected["system_inventory"]) == Decimal("17")

    still_open = apply_recount(corrected, 16)
    closed = apply_recount(corrected, 17)
    assert still_open["closed"] is False
    assert closed["closed"] is True
    assert "16" in closed["history"][0]


def test_sale_rescue_rejects_a_low_selling_price():
    offers = default_offers(Decimal("119"))
    assert offers[0]["contribution"] == "21.00"
    assert offers[1]["contribution"] == "27.00"
    low = default_offers(Decimal("90"))
    assert all(item["acceptable"] is False for item in low)
    accepted = negotiate(offers[1], Decimal("76"), Decimal("119"))
    assert accepted["status"] == "accepted"
    assert accepted["contribution"] == "27.00"
    assert merchant_contribution(Decimal("119"), Decimal("76"), Decimal("7")) == Decimal("27")


def test_losing_workshop_is_blocked():
    result = assess_workshop(100, 7)

    assert Decimal(result["contribution"]) < 0
    assert result["verdict"] == "blocked"
    with pytest.raises(ValueError, match="blocked"):
        workshop_approve(result)


def test_detective_does_not_correct_a_matching_count():
    case = investigate_stock(20)
    confirmed = confirm_workshop_evidence(case)

    assert case["closed"] is True
    with pytest.raises(ValueError, match="no missing stock"):
        apply_usage_correction(confirmed)


def test_counteroffer_cannot_worsen_or_exceed_the_quote():
    offers = default_offers(Decimal("119"))
    original = offers[1]
    with pytest.raises(ValueError, match="below the simulator floor"):
        negotiate(original, Decimal("70"), Decimal("119"))
    with pytest.raises(ValueError, match="cannot cost more"):
        negotiate(original, Decimal("85"), Decimal("119"))
    assert original["acquisition"] == "76.00"
    assert original["acceptable"] is True


def test_staffing_uses_history_not_the_day_name_alone():
    tuesday = staffing_plan("tuesday", False, Decimal("6"))
    saturday = staffing_plan("saturday", True, Decimal("6"))

    assert tuesday["expected_transactions"] == "5.20"
    assert tuesday["coverage_blocks"] == 0
    assert saturday["expected_transactions"] == "36.00"
    assert saturday["workload_hours"] == "14.00"
    assert saturday["coverage_blocks"] == 2
    busy_tuesday = staffing_plan("tuesday", True, Decimal("2"))
    assert busy_tuesday["coverage_blocks"] > tuesday["coverage_blocks"]
