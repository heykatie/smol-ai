"""Read a simulated supplier email as data, not as instructions."""

from __future__ import annotations

import re
from dataclasses import dataclass


class ExtractionError(Exception):
    """The message did not contain a usable lead-time change."""


_LEAD_TIME = re.compile(
    r"lead time for (?P<product>workshop supply pack) has increased from "
    r"(?P<previous>\d+) days to (?:approximately )?(?P<current>\d+) days",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LeadTimeFact:
    supplier_id: str
    sku: str
    previous_lead_time_days: int
    lead_time_days: int


def extract_lead_time(message: str, supplier_id: str, sku: str) -> LeadTimeFact:
    """Return the lead-time change and nothing else.

    The product name in the message is not trusted as a SKU or a policy change.
    The supplier id and SKU come from the configured monitoring rule.
    """
    if not supplier_id or not isinstance(supplier_id, str):
        raise ValueError("A configured supplier id is required.")
    if not sku or not isinstance(sku, str):
        raise ValueError("A configured SKU is required.")
    match = _LEAD_TIME.search(message or "")
    if match is None:
        raise ExtractionError("No lead-time change found.")
    previous = int(match.group("previous"))
    current = int(match.group("current"))
    if previous < 0 or current < 1 or previous == current:
        raise ExtractionError("Lead-time change is not usable.")
    return LeadTimeFact(
        supplier_id=supplier_id,
        sku=sku,
        previous_lead_time_days=previous,
        lead_time_days=current,
    )
