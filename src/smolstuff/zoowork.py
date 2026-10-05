"""One scoped ZooWork explanation. It cannot change price, quantity, or approval."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://clawapi.ecap.gsmo.ai/service/v1"
_TASK = "Explain a synthetic supplier delay without changing the order"


@dataclass(frozen=True)
class ZooWorkAttempt:
    provider: str
    status: str
    task: str
    result: str
    effect: str
    fallback: bool


def explain_supplier_delay(
    message: str,
    transport: Optional[Callable] = None,
    key: Optional[str] = None,
) -> ZooWorkAttempt:
    """Ask ZooWork for an explanation. The caller keeps the calculated decision."""
    secret = (key if key is not None else os.environ.get("ZOOWORK_API_KEY", "")).strip()
    if not secret:
        return _fallback("ZooWork is not configured. No agent task was started.")
    send = transport or _http
    agent_id = None
    try:
        created = send(
            "POST",
            "/agents",
            {
                "resource": {
                    "name": "smolstuff-explainer",
                    "persona": {
                        "docs": [{
                            "name": "AGENTS.md",
                            "content": (
                                "Explain the supplier delay in one sentence. "
                                "Do not change prices, quantities, or approval."
                            ),
                        }]
                    },
                }
            },
            secret,
        )
        agent_id = str(created.get("agent_id") or created.get("resource", {}).get("agent_id") or "")
        if not agent_id:
            return _fallback("ZooWork did not return an agent id. The calculated order is unchanged.")
        send("POST", "/agents/{0}/start".format(agent_id), None, secret)
        session = send(
            "POST",
            "/agents/{0}/sessions".format(agent_id),
            {"initial_events": [{"type": "user.message", "content": message[:2000]}]},
            secret,
        )
        session_id = str(session.get("session_id") or session.get("id") or "")
        summary = _assistant_text(session)
        if agent_id and session_id and not summary:
            for _ in range(6):
                time.sleep(2)
                later = send(
                    "GET",
                    "/agents/{0}/sessions/{1}/events".format(agent_id, session_id),
                    None,
                    secret,
                )
                summary = _assistant_text(later)
                if summary:
                    break
        if not summary:
            return _fallback("ZooWork accepted the task but returned no explanation. The calculated order is unchanged.")
        return ZooWorkAttempt(
            provider="ZooWork",
            status="live",
            task=_TASK,
            result=summary,
            effect="The explanation is evidence only. Quantity, total, and approval stay in application code.",
            fallback=False,
        )
    except (OSError, URLError, HTTPError, ValueError, KeyError, TypeError) as error:
        return _fallback(_safe_error(error))
    finally:
        if agent_id:
            try:
                send("DELETE", "/agents/{0}".format(agent_id), None, secret)
            except (OSError, URLError, HTTPError, ValueError):
                pass


def _assistant_text(payload: dict) -> str:
    chunks = []
    if payload.get("summary"):
        chunks.append(str(payload["summary"]))
    for event in payload.get("events") or []:
        if not isinstance(event, dict) or event.get("event_type") not in (None, "agent.assistant"):
            if event.get("event_type") != "agent.assistant":
                continue
        message = (event.get("payload") or {}).get("message") if isinstance(event.get("payload"), dict) else None
        content = message.get("content") if isinstance(message, dict) else event.get("content")
        if isinstance(content, str):
            chunks.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("text"):
                    chunks.append(str(block["text"]))
    text = " ".join(" ".join(chunks).split())
    return text[:400]


def _fallback(result: str) -> ZooWorkAttempt:
    return ZooWorkAttempt(
        provider="ZooWork",
        status="failed" if "not configured" not in result else "simulated",
        task=_TASK,
        result=result,
        effect="The calculated order is unchanged.",
        fallback=True,
    )


def _safe_error(error: Exception) -> str:
    text = " ".join(str(error).split())
    if "zwp_" in text:
        text = "ZooWork rejected the request."
    return (text or "ZooWork request failed.")[:240]


def _http(method: str, path: str, body, key: str) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer {0}".format(key),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "curl/8.7.1",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:180]
        raise ValueError("ZooWork HTTP {0}. {1}".format(error.code, detail)) from None
    if not raw:
        return {}
    parsed = json.loads(raw)
    return parsed if isinstance(parsed, dict) else {"result": parsed}
