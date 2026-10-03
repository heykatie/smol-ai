"""Deterministic purchase authorization.

A model may propose an order. Only this module decides whether that order may
run by itself, needs the owner, or is not ready to decide.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping, Optional, Tuple

from smol_ai.money import Money, transaction_total


class PolicyDecision(Enum):
    AUTO_EXECUTE = "auto_execute"
    NEEDS_APPROVAL = "needs_approval"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class GuardedPurchasePolicy:
    """Owner-configured rules for one business. External text cannot edit these."""

    auto_execute_total_below: Money
    max_unit_price_increase_ratio: Decimal
    min_quantity: int
    max_quantity: int
    aggregate_budget_remaining: Money

    def __post_init__(self) -> None:
        if isinstance(self.max_unit_price_increase_ratio, float):
            raise TypeError("Price-increase ratio must be Decimal.")
        if self.max_unit_price_increase_ratio < 0:
            raise ValueError("Price-increase ratio cannot be negative.")
        if self.min_quantity < 1 or self.max_quantity < self.min_quantity:
            raise ValueError("Quantity range is invalid.")
        if self.auto_execute_total_below.currency != self.aggregate_budget_remaining.currency:
            raise ValueError("Policy currency must match.")


@dataclass(frozen=True)
class PurchaseProposal:
    supplier_id: str
    sku: str
    supplier_allowlisted: bool
    sku_previously_purchased: bool
    quantity: int
    unit_price: Money
    fees: Money
    previous_unit_price: Optional[Money]
    evidence_current: bool
    evidence_complete: bool
    verification_passed: bool


@dataclass(frozen=True)
class PolicyResult:
    decision: PolicyDecision
    reasons: Tuple[str, ...]
    computed_total: Money
    ignored_untrusted_fields: Tuple[str, ...] = ()


TRUSTED_PROPOSAL_FIELDS = frozenset(
    {
        "supplier_id",
        "sku",
        "supplier_allowlisted",
        "sku_previously_purchased",
        "quantity",
        "unit_price",
        "fees",
        "previous_unit_price",
        "evidence_current",
        "evidence_complete",
        "verification_passed",
    }
)


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError("{0} must be a real boolean.".format(field))
    return value


def _require_money(value: object, field: str) -> Money:
    if not isinstance(value, Money):
        raise TypeError("{0} must be Money.".format(field))
    return value


def proposal_from_mapping(
    data: Mapping[str, object]
) -> Tuple[PurchaseProposal, Tuple[str, ...]]:
    """Read only known proposal fields. Extra keys are ignored, not applied."""
    ignored = tuple(sorted(set(data) - TRUSTED_PROPOSAL_FIELDS))
    missing = sorted(TRUSTED_PROPOSAL_FIELDS - set(data))
    if missing:
        raise ValueError("Proposal is missing trusted fields: {0}".format(", ".join(missing)))

    quantity = data["quantity"]
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError("quantity must be an int.")

    previous = data["previous_unit_price"]
    if previous is not None and not isinstance(previous, Money):
        raise TypeError("previous_unit_price must be Money or None.")

    proposal = PurchaseProposal(
        supplier_id=str(data["supplier_id"]),
        sku=str(data["sku"]),
        supplier_allowlisted=_require_bool(data["supplier_allowlisted"], "supplier_allowlisted"),
        sku_previously_purchased=_require_bool(
            data["sku_previously_purchased"], "sku_previously_purchased"
        ),
        quantity=quantity,
        unit_price=_require_money(data["unit_price"], "unit_price"),
        fees=_require_money(data["fees"], "fees"),
        previous_unit_price=previous,
        evidence_current=_require_bool(data["evidence_current"], "evidence_current"),
        evidence_complete=_require_bool(data["evidence_complete"], "evidence_complete"),
        verification_passed=_require_bool(data["verification_passed"], "verification_passed"),
    )
    return proposal, ignored


def evaluate_purchase(
    proposal: PurchaseProposal,
    policy: GuardedPurchasePolicy,
    ignored_untrusted_fields: Tuple[str, ...] = (),
) -> PolicyResult:
    total = transaction_total(proposal.unit_price, proposal.quantity, proposal.fees)
    readiness = []
    authority = []

    if not proposal.evidence_current:
        readiness.append("Evidence is stale.")
    if not proposal.evidence_complete:
        readiness.append("Evidence is incomplete.")
    if not proposal.verification_passed:
        readiness.append("Verification has not passed.")

    if not proposal.supplier_allowlisted:
        authority.append("Supplier is not allowlisted.")
    if not proposal.sku_previously_purchased:
        authority.append("SKU was not previously purchased.")
    if not (total < policy.auto_execute_total_below):
        authority.append(
            "Total {0} is not below the {1} auto limit.".format(
                total, policy.auto_execute_total_below
            )
        )
    if total > policy.aggregate_budget_remaining:
        authority.append("Total exceeds the remaining aggregate budget.")
    if not (policy.min_quantity <= proposal.quantity <= policy.max_quantity):
        authority.append("Quantity is outside the configured range.")

    price_reason = _price_increase_reason(proposal, policy)
    if price_reason == "not_ready":
        readiness.append("Previous unit price is missing, so the price rule cannot be checked.")
    elif price_reason:
        authority.append(price_reason)

    if readiness:
        decision = PolicyDecision.NOT_READY
        reasons = tuple(readiness + authority)
    elif authority:
        decision = PolicyDecision.NEEDS_APPROVAL
        reasons = tuple(authority)
    else:
        decision = PolicyDecision.AUTO_EXECUTE
        reasons = ("Every guarded-auto purchase rule passed.",)

    return PolicyResult(
        decision=decision,
        reasons=reasons,
        computed_total=total,
        ignored_untrusted_fields=ignored_untrusted_fields,
    )


def _price_increase_reason(
    proposal: PurchaseProposal, policy: GuardedPurchasePolicy
) -> Optional[str]:
    previous = proposal.previous_unit_price
    if previous is None:
        return "not_ready"
    if previous.amount == 0:
        return "not_ready"
    if previous.currency != proposal.unit_price.currency:
        return "not_ready"
    increase = (proposal.unit_price.amount - previous.amount) / previous.amount
    # Strict inequality: a 5% increase does not pass a "< 5%" rule.
    if not (increase < policy.max_unit_price_increase_ratio):
        return "Unit-price increase is not below the configured tolerance."
    return None
