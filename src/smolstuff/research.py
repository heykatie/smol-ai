"""Public supplier research.

Tavily may attach source links. It cannot change quantity, price, or approval.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Callable, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


SUPPLIER_QUERY = (
    "typical wholesale lead time and minimum order for a workshop supply kit"
)
_TASK = "Find public sources for a fictional workshop-kit reorder"
_UNCHANGED = "The reorder quantity, total, and approval rule are unchanged."


@dataclass(frozen=True)
class ResearchAttempt:
    provider: str
    status: str
    task: str
    result: str
    effect: str
    fallback: bool


def research_supplier(
    query: str = SUPPLIER_QUERY,
    transport: Optional[Callable[[str], dict]] = None,
    allow_network: bool = True,
) -> ResearchAttempt:
    if not allow_network:
        return ResearchAttempt(
            provider="Tavily",
            status="simulated",
            task=_TASK,
            result="Sponsor calls are off. No supplier sources were retrieved.",
            effect=_UNCHANGED,
            fallback=True,
        )
    key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not key:
        return ResearchAttempt(
            provider="Tavily",
            status="simulated",
            task=_TASK,
            result="Tavily is not configured. No supplier sources were retrieved.",
            effect=_UNCHANGED,
            fallback=True,
        )
    try:
        payload = transport(query) if transport is not None else _call_tavily(key, query)
        return _from_payload(payload)
    except (OSError, URLError, ValueError, KeyError, TypeError):
        return ResearchAttempt(
            provider="Tavily",
            status="simulated",
            task=_TASK,
            result="Tavily did not return usable public sources. No links were saved.",
            effect=_UNCHANGED,
            fallback=True,
        )


def _call_tavily(key: str, query: str) -> dict:
    body = json.dumps(
        {
            "query": query,
            "topic": "general",
            "search_depth": "basic",
            "max_results": 3,
            "include_answer": False,
        }
    ).encode("utf-8")
    request = Request(
        "https://api.tavily.com/search",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _from_payload(payload: dict) -> ResearchAttempt:
    if not isinstance(payload, dict):
        raise ValueError("Tavily response was not an object.")
    links = []
    for item in payload.get("results") or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "")
        if url.startswith("https://") and " " not in url and _safe_public_url(url):
            links.append(url)
    if not links:
        raise ValueError("Tavily returned no public sources.")
    result = "Public sources: {0}".format(" ".join(links[:2]))
    if len(result) > 400:
        result = result[:397].rstrip() + "..."
    return ResearchAttempt(
        provider="Tavily",
        status="live",
        task=_TASK,
        result=result,
        effect=_UNCHANGED,
        fallback=False,
    )


def _safe_public_url(url: str) -> bool:
    lowered = url.lower()
    return not any(marker in lowered for marker in ("tvly-", "zwp_", "sk-", "sk_", "band_", "bearer"))
