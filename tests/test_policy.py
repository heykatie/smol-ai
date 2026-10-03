from dataclasses import replace
from decimal import Decimal

import pytest

from smol_ai.fixtures import (
    AUTO_ELIGIBLE_PURCHASE,
    EXAMPLE_POLICY,
    NEEDS_APPROVAL_PURCHASE,
    UNTRUSTED_OVERRIDE_ATTEMPT,
)
from smol_ai.money import Money
from smol_ai.policy import PolicyDecision, evaluate_purchase, proposal_from_mapping


def test_sixty_one_dollar_order_needs_approval_under_forty_dollar_limit():
    result = evaluate_purchase(NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)

    assert result.computed_total == Money(Decimal("61.00"))
    assert result.decision == PolicyDecision.NEEDS_APPROVAL
    assert any("auto limit" in reason for reason in result.reasons)


def test_smaller_order_auto_executes_only_when_every_rule_passes():
    result = evaluate_purchase(AUTO_ELIGIBLE_PURCHASE, EXAMPLE_POLICY)

    assert result.computed_total == Money(Decimal("12.20"))
    assert result.decision == PolicyDecision.AUTO_EXECUTE


def test_exact_forty_dollars_is_not_automatic():
    proposal = replace(
        AUTO_ELIGIBLE_PURCHASE,
        quantity=1,
        unit_price=Money(Decimal("40.00")),
        previous_unit_price=Money(Decimal("40.00")),
    )

    result = evaluate_purchase(proposal, EXAMPLE_POLICY)

    assert result.decision == PolicyDecision.NEEDS_APPROVAL


def test_one_failing_rule_blocks_auto_execution():
    proposal = replace(AUTO_ELIGIBLE_PURCHASE, supplier_allowlisted=False)

    result = evaluate_purchase(proposal, EXAMPLE_POLICY)

    assert result.decision == PolicyDecision.NEEDS_APPROVAL
    assert result.reasons == ("Supplier is not allowlisted.",)


def test_five_percent_price_increase_is_not_below_the_tolerance():
    proposal = replace(
        AUTO_ELIGIBLE_PURCHASE,
        unit_price=Money(Decimal("1.05")),
        previous_unit_price=Money(Decimal("1.00")),
    )

    result = evaluate_purchase(proposal, EXAMPLE_POLICY)

    assert result.computed_total == Money(Decimal("21.00"))
    assert result.decision == PolicyDecision.NEEDS_APPROVAL


def test_increase_just_under_five_percent_can_auto_execute():
    proposal = replace(
        AUTO_ELIGIBLE_PURCHASE,
        unit_price=Money(Decimal("1.04")),
        previous_unit_price=Money(Decimal("1.00")),
    )

    result = evaluate_purchase(proposal, EXAMPLE_POLICY)

    assert result.decision == PolicyDecision.AUTO_EXECUTE


def test_total_above_remaining_budget_needs_approval():
    policy = replace(EXAMPLE_POLICY, aggregate_budget_remaining=Money(Decimal("10.00")))

    result = evaluate_purchase(AUTO_ELIGIBLE_PURCHASE, policy)

    assert result.decision == PolicyDecision.NEEDS_APPROVAL
    assert any("aggregate" in reason for reason in result.reasons)


def test_incomplete_evidence_is_not_an_approval_request():
    proposal = replace(NEEDS_APPROVAL_PURCHASE, evidence_complete=False)

    result = evaluate_purchase(proposal, EXAMPLE_POLICY)

    assert result.decision == PolicyDecision.NOT_READY
    assert any("incomplete" in reason for reason in result.reasons)
    assert any("auto limit" in reason for reason in result.reasons)


def test_claimed_total_is_ignored_in_favor_of_computed_total():
    result = evaluate_purchase(NEEDS_APPROVAL_PURCHASE, EXAMPLE_POLICY)

    assert result.computed_total.amount == Decimal("61.00")


def test_untrusted_payload_cannot_raise_the_spending_limit():
    payload = {
        "supplier_id": NEEDS_APPROVAL_PURCHASE.supplier_id,
        "sku": NEEDS_APPROVAL_PURCHASE.sku,
        "supplier_allowlisted": NEEDS_APPROVAL_PURCHASE.supplier_allowlisted,
        "sku_previously_purchased": NEEDS_APPROVAL_PURCHASE.sku_previously_purchased,
        "quantity": NEEDS_APPROVAL_PURCHASE.quantity,
        "unit_price": NEEDS_APPROVAL_PURCHASE.unit_price,
        "fees": NEEDS_APPROVAL_PURCHASE.fees,
        "previous_unit_price": NEEDS_APPROVAL_PURCHASE.previous_unit_price,
        "evidence_current": NEEDS_APPROVAL_PURCHASE.evidence_current,
        "evidence_complete": NEEDS_APPROVAL_PURCHASE.evidence_complete,
        "verification_passed": NEEDS_APPROVAL_PURCHASE.verification_passed,
        "auto_execute_total_below": "10000",
        "ignore_policy": True,
        "message": UNTRUSTED_OVERRIDE_ATTEMPT,
    }

    proposal, ignored = proposal_from_mapping(payload)
    result = evaluate_purchase(proposal, EXAMPLE_POLICY, ignored)

    assert "auto_execute_total_below" in result.ignored_untrusted_fields
    assert "message" in result.ignored_untrusted_fields
    assert EXAMPLE_POLICY.auto_execute_total_below == Money(Decimal("40.00"))
    assert result.decision == PolicyDecision.NEEDS_APPROVAL
    assert result.computed_total == Money(Decimal("61.00"))


def test_string_boolean_is_rejected():
    payload = {
        "supplier_id": AUTO_ELIGIBLE_PURCHASE.supplier_id,
        "sku": AUTO_ELIGIBLE_PURCHASE.sku,
        "supplier_allowlisted": "false",
        "sku_previously_purchased": AUTO_ELIGIBLE_PURCHASE.sku_previously_purchased,
        "quantity": AUTO_ELIGIBLE_PURCHASE.quantity,
        "unit_price": AUTO_ELIGIBLE_PURCHASE.unit_price,
        "fees": AUTO_ELIGIBLE_PURCHASE.fees,
        "previous_unit_price": AUTO_ELIGIBLE_PURCHASE.previous_unit_price,
        "evidence_current": AUTO_ELIGIBLE_PURCHASE.evidence_current,
        "evidence_complete": AUTO_ELIGIBLE_PURCHASE.evidence_complete,
        "verification_passed": AUTO_ELIGIBLE_PURCHASE.verification_passed,
    }

    with pytest.raises(TypeError, match="boolean"):
        proposal_from_mapping(payload)
