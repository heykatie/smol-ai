from decimal import Decimal

from smolstuff.fixtures import NEEDS_APPROVAL_PURCHASE
from smolstuff.money import Money
from smolstuff.terms import purchase_terms_hash


def test_terms_hash_binds_price_quantity_and_supplier():
    original = purchase_terms_hash(
        NEEDS_APPROVAL_PURCHASE.supplier_id,
        NEEDS_APPROVAL_PURCHASE.sku,
        NEEDS_APPROVAL_PURCHASE.quantity,
        NEEDS_APPROVAL_PURCHASE.unit_price,
        NEEDS_APPROVAL_PURCHASE.fees,
    )
    repeated = purchase_terms_hash(
        "supplier-b",
        "DEMO-ITM-001",
        100,
        Money(Decimal("1.82")),
        Money(Decimal("7.00")),
    )
    changed_price = purchase_terms_hash(
        "supplier-b",
        "DEMO-ITM-001",
        100,
        Money(Decimal("0.75")),
        Money(Decimal("0.00")),
    )

    assert original == repeated
    assert original != changed_price
