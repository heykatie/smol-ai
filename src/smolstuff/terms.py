"""Hash the commercial terms an approval is allowed to cover."""

from __future__ import annotations

import hashlib
import json

from smolstuff.money import Money, transaction_total


def purchase_terms_hash(
    supplier_id: str,
    sku: str,
    quantity: int,
    unit_price: Money,
    fees: Money,
) -> str:
    """Bind supplier, SKU, quantity, unit price, fees, and computed total.

    Evidence flags and untrusted message text are intentionally absent. A later
    change to price or quantity produces a different hash, so the old approval
    does not apply.
    """
    total = transaction_total(unit_price, quantity, fees)
    if unit_price.currency != fees.currency or unit_price.currency != total.currency:
        raise ValueError("Purchase terms must use one currency.")
    payload = {
        "supplier_id": supplier_id,
        "sku": sku,
        "quantity": quantity,
        "unit_price": format(unit_price.amount, "f"),
        "fees": format(fees.amount, "f"),
        "total": format(total.amount, "f"),
        "currency": total.currency,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
