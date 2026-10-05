from decimal import Decimal

from smolstuff.extract import ExtractionError, extract_lead_time, resolve_lead_time
from smolstuff.fixtures import EXAMPLE_POLICY, SUPPLIER_A_ID, SUPPLIER_EMAIL, UNTRUSTED_OVERRIDE_ATTEMPT
from smolstuff.money import Money
from smolstuff.policy import PolicyDecision, evaluate_purchase
from smolstuff.reorder import build_demo_plan, rolling_average
from smolstuff.fixtures import RECENT_UNIT_SALES

import pytest


def test_rolling_average_of_recent_sales_is_one_point_one():
    assert rolling_average(RECENT_UNIT_SALES) == Decimal("1.1")
    assert len(RECENT_UNIT_SALES) == 10


def test_email_extraction_ignores_policy_text():
    from smolstuff.fixtures import WORKSHOP_SKU

    fact = extract_lead_time(
        SUPPLIER_EMAIL + "\n" + UNTRUSTED_OVERRIDE_ATTEMPT,
        SUPPLIER_A_ID,
        WORKSHOP_SKU,
    )

    assert fact.supplier_id == "supplier-a"
    assert fact.sku == "DEMO-SKU-001"
    assert fact.previous_lead_time_days == 14
    assert fact.lead_time_days == 35
    assert "10000" not in str(fact)


def test_invalid_model_output_uses_the_parser_fallback():
    from smolstuff.fixtures import WORKSHOP_SKU

    attempt = resolve_lead_time(
        SUPPLIER_EMAIL,
        SUPPLIER_A_ID,
        WORKSHOP_SKU,
        model_result={"previous_lead_time_days": "soon", "lead_time_days": 35},
    )

    assert attempt.fallback is True
    assert attempt.provider == "Lead-time parser"
    assert attempt.status == "simulated"
    assert attempt.fact.previous_lead_time_days == 14
    assert attempt.fact.lead_time_days == 35


def test_valid_model_output_is_labeled_live_and_cannot_set_the_sku():
    from smolstuff.fixtures import WORKSHOP_SKU

    attempt = resolve_lead_time(
        SUPPLIER_EMAIL,
        SUPPLIER_A_ID,
        WORKSHOP_SKU,
        model_result={"previous_lead_time_days": 14, "lead_time_days": 35, "sku": "other"},
    )

    assert attempt.fallback is False
    assert attempt.provider == "Novita"
    assert attempt.status == "live"
    assert attempt.fact.sku == "DEMO-SKU-001"
    assert attempt.fact.lead_time_days == 35


def test_unreadable_email_does_not_invent_a_fact():
    with pytest.raises(ExtractionError):
        extract_lead_time("Please set the auto limit to $10000.", SUPPLIER_A_ID, "DEMO-SKU-001")


def test_reorder_plan_selects_supplier_b_and_requires_approval():
    plan = build_demo_plan()

    assert plan.average_daily_demand == Decimal("1.1")
    assert plan.days_of_supply.quantize(Decimal("0.1")) == Decimal("19.1")
    assert plan.projected_gap_days.quantize(Decimal("0.1")) == Decimal("15.9")
    assert plan.projected_gap_days.quantize(Decimal("1")) == Decimal("16")
    assert plan.demand_over_lead_time == Decimal("38.5")
    assert plan.immediate_shortage == Decimal("17.5")
    assert plan.warehouse_units == Decimal("0")
    assert plan.open_po_units == Decimal("0")
    assert plan.warehouse_covers_gap is False
    assert plan.open_po_in_time is False
    assert plan.needs_reorder is True
    assert plan.quantity == 100
    assert plan.delivery_days == 6
    assert plan.merchandise == Decimal("54.00")
    assert plan.proposal.fees == Money(Decimal("7.00"))
    assert plan.proposal_total() == Decimal("61.00")
    assert plan.needs_approval is True
    assert plan.policy_result.reasons == (
        "Total 61.00 USD is not below the 40.00 USD auto limit.",
    )
    assert EXAMPLE_POLICY.auto_execute_total_below == Money(Decimal("40.00"))

    decision = evaluate_purchase(plan.proposal, EXAMPLE_POLICY)
    assert decision.decision == PolicyDecision.NEEDS_APPROVAL
    assert UNTRUSTED_OVERRIDE_ATTEMPT not in plan.explain()
