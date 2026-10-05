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


@dataclass(frozen=True)
class ExtractionAttempt:
    fact: LeadTimeFact
    provider: str
    status: str
    result: str
    fallback: bool


def resolve_lead_time(message: str, supplier_id: str, sku: str, model_result=None, model_error: bool = False) -> ExtractionAttempt:
    """Use a validated model payload when it is usable. Otherwise use the parser.

    The model may only supply the two lead times. SKU, supplier, prices, and
    policy stay with the application.
    """
    if model_error:
        fact = extract_lead_time(message, supplier_id, sku)
        return ExtractionAttempt(
            fact=fact,
            provider="Lead-time parser",
            status="simulated",
            result="Novita request failed. Parser fallback read lead time {0} to {1} days.".format(
                fact.previous_lead_time_days, fact.lead_time_days
            ),
            fallback=True,
        )
    if model_result is not None:
        try:
            previous, current = _validated_model_days(model_result)
        except (ExtractionError, KeyError, TypeError, ValueError):
            fact = extract_lead_time(message, supplier_id, sku)
            return ExtractionAttempt(
                fact=fact,
                provider="Lead-time parser",
                status="simulated",
                result="Novita output failed validation. Parser fallback read lead time {0} to {1} days.".format(
                    fact.previous_lead_time_days, fact.lead_time_days
                ),
                fallback=True,
            )
        return ExtractionAttempt(
            fact=LeadTimeFact(supplier_id, sku, previous, current),
            provider="Novita",
            status="live",
            result="Novita extracted lead time {0} to {1} days from the synthetic supplier message.".format(
                previous, current
            ),
            fallback=False,
        )
    fact = extract_lead_time(message, supplier_id, sku)
    return ExtractionAttempt(
        fact=fact,
        provider="Lead-time parser",
        status="simulated",
        result="No live model key is configured. Parser read lead time {0} to {1} days.".format(
            fact.previous_lead_time_days, fact.lead_time_days
        ),
        fallback=True,
    )


def _validated_model_days(payload: dict):
    if not isinstance(payload, dict):
        raise ExtractionError("Model output was not an object.")
    previous = int(payload["previous_lead_time_days"])
    current = int(payload["lead_time_days"])
    if previous < 0 or current < 1 or previous == current or current > 365:
        raise ExtractionError("Model lead times are not usable.")
    return previous, current


def call_novita(message: str) -> dict:
    """Ask Novita for two lead-time numbers. The API key stays server-side and is sent only for provider authentication."""
    import json
    import os
    import urllib.request

    key = os.environ.get("NOVITA_API_KEY", "")
    if not key:
        raise ExtractionError("NOVITA_API_KEY is not configured.")
    model = os.environ.get("NOVITA_MODEL", "deepseek/deepseek-v4.1-flash")
    body = json.dumps({
        "model": model,
        "temperature": 0,
        "max_tokens": 80,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Extract only previous_lead_time_days and lead_time_days from the user message. "
                    "Reply with JSON only. Do not invent prices, suppliers, or policy."
                ),
            },
            {"role": "user", "content": message[:2000]},
        ],
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.novita.ai/openai/v1/chat/completions",
        data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end < start:
        raise ExtractionError("Novita did not return JSON.")
    return json.loads(content[start:end + 1])
