"""Dashboard and scenario pages. Synthetic data, simulated external actions."""

from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import Optional

from smolstuff.ops_demos import (
    RESCUE_FIXTURE,
    ScenarioStore,
    WORKSHOP_FIXTURE,
    apply_recount,
    apply_usage_correction,
    assess_workshop,
    confirm_workshop_evidence,
    default_offers,
    detective_days_of_supply,
    investigate_stock,
    negotiate,
    staffing_plan,
    workshop_approve,
    workshop_complete,
    workshop_receive,
)

from smolstuff.ui_theme import STYLE


def shell(title: str, body: str) -> str:
    nav = [("Daily brief", "/", "✦"), ("Reorder", "/?scenario=reorder", "↗"),
           ("Workshop feasibility", "/?scenario=workshop", "◇"),
           ("Inventory Detective", "/?scenario=detective", "⌕"),
           ("Sale rescue", "/?scenario=rescue", "♡"),
           ("Staffing coverage", "/?scenario=staffing", "☷")]
    links = "".join('<a href="{href}"{active}><span class="nav-icon" aria-hidden="true">{icon}</span>{label}</a>'.format(
        href=href, active=' aria-current="page"' if title == label else "",
        icon=icon, label=escape(label)) for label, href, icon in nav)
    home = "" if title == "Daily brief" else '<a class="home" href="/">← Daily brief</a>'
    return ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="theme-color" content="#101115">'
        '<title>smolstuff — {title}</title><style>{style}</style></head>'
        '<body><a class="skip" href="#content">Skip to content</a><div class="app-layout">'
        '<aside class="rail"><a class="brand" href="/" aria-label="smolstuff daily brief">'
        '<span class="brand-mark" aria-hidden="true">:)</span>smolstuff</a>'
        '<div><p class="rail-label">Your operations</p><nav aria-label="Main navigation">{nav}</nav></div>'
        '<div class="rail-note"><strong>Small but mighty.</strong>One less thing for you to carry. You keep the final say.</div></aside>'
        '<main id="content" tabindex="-1"><header class="top"><span class="workspace"><strong>Your workspace</strong> / {title}</span>'
        '<span class="demo-tag">Interactive demo</span>{home}</header>{body}'
        '<footer class="footer-note">Fictional business data. Purchases, messages, and deliveries are simulated. '
        'This demo does not monitor a real inbox. Provider calls are labeled in the evidence.</footer>'
        '</main></div></body></html>').format(title=escape(title), style=STYLE, nav=links, home=home, body=body)


def error_page(message: str = "That action or value could not be accepted.") -> str:
    return shell("Check your input", '<h1>Let’s try that again.</h1><article class="alert" role="alert"><p>{}</p>'
                 '<p>Return to the daily brief, open the workflow, and check the values before submitting.</p>'
                 '<a class="open" href="/">Back to daily brief</a></article>'.format(escape(message)))


def _hidden(scenario: str) -> str:
    return '<input type="hidden" name="scenario" value="{0}">'.format(escape(scenario))


def _button(scenario: str, action: str, label: str, kind: str = "primary") -> str:
    return (
        '<form method="post" action="/">'
        "{hidden}<input type=\"hidden\" name=\"action\" value=\"{action}\">"
        '<button class="{kind}" type="submit">{label}</button></form>'
    ).format(hidden=_hidden(scenario), action=escape(action), kind=escape(kind), label=escape(label))


_BUCKET_CLASS = {
    "Needs your decision": "decision",
    "In progress": "progress",
    "Completed": "done",
    "Not started": "idle",
}


def dashboard_page(cards: list, events=()) -> str:
    groups = {"Needs your decision": [], "In progress": [], "Completed": [], "Not started": []}
    for card in cards:
        groups.setdefault(card["bucket"], []).append(card)
    order = ("Needs your decision", "In progress", "Not started", "Completed")
    sections = [
        '<section class="hero"><span class="hero-spark" aria-hidden="true">✧</span><p class="kicker">Daily brief · small but mighty</p><h1>A little less on your plate.</h1><p class="lede">A home for the details, decisions, and follow-through. Explore your operations team with five hands-on demos.</p></section>',
        '<p class="note">Counts come from this session only.</p>',
        '<p class="counts">{0}</p>'.format(
            "".join(
                "<span>{1}<strong>{0}</strong></span>".format(len(groups[name]), escape(name).lower())
                for name in order
            )
        ),
    ]
    for name in order:
        items = groups.get(name, [])
        if not items:
            continue
        sections.append("<h2>{0} ({1})</h2>".format("Explore your operations" if name == "Not started" else escape(name), len(items)))
        sections.append('<div class="grid">')
        for card in items:
            tone = _BUCKET_CLASS.get(card["bucket"], "idle")
            sections.append(
                "<article><div class=\"card-top\"><span class=\"card-icon\" aria-hidden=\"true\">{icon}</span><p class=\"status {tone}\">{status}</p></div><h3>{title}</h3><p>{description}</p>"
                '<div class="card-actions"><a class="open" href="{href}" aria-label="Open {title}">Open →</a>{action}</div></article>'.format(
                    tone=tone,
                    icon={"reorder": "↗", "workshop": "◇", "detective": "⌕", "rescue": "♡", "staffing": "☷"}.get(card["href"].split("=")[-1], "✦"),
                    status=escape(card["status"]),
                    title=escape(card["title"]),
                    description=escape(card["description"]),
                    href=escape(card["href"]),
                    action=card.get("action", ""),
                )
            )
        sections.append("</div>")
    sections.append(
        "<p class=\"note\">Collaboration inquiries and custom orders are future variants of the workshop feasibility engine. They are not separate workflows.</p>"
    )
    sections.append("<h2>What ran</h2>")
    if events:
        sections.append("<ul class=\"activity\">")
        for event in events:
            sections.append(
                "<li><strong>{0}</strong> · {1}. {2} {3}</li>".format(
                    escape(event.provider), escape(event.status), escape(event.result), escape(event.effect)
                )
            )
        sections.append("</ul>")
    else:
        sections.append("<p class=\"note empty\">No tool has run in this session. No sponsor call is claimed.</p>")
    return shell("Daily brief", "".join(sections))


def workshop_page(saved: Optional[dict], message: str = "") -> str:
    attendees = WORKSHOP_FIXTURE["attendees"] if saved is None else saved.get("attendees", 20)
    days_until = WORKSHOP_FIXTURE["days_until"] if saved is None else saved.get("days_until", 7)
    body = [
        "<h1>Can we take this on?</h1>",
        "<p>Check materials, timing, staffing, and profitability before making a customer promise.</p>",
        "<article class=\"card\"><p>Inquiry: Could you run a creative workshop for 20 people next week, including all materials, for $1,500?</p>",
        "<form method=\"post\" action=\"/\">{0}".format(_hidden("workshop")),
        "<label>Attendees <input name=\"attendees\" type=\"number\" min=\"1\" value=\"{0}\"></label>".format(attendees),
        "<label>Days until the event <input name=\"days_until\" type=\"number\" min=\"0\" value=\"{0}\"></label>".format(days_until),
        "<button class=\"primary\" name=\"action\" value=\"workshop_check\">Check feasibility</button></form>",
    ]
    if message:
        body.append("<p>{0}</p>".format(escape(message)))
    if saved and saved.get("verdict"):
        labels = {
            "feasible": "Feasible",
            "feasible_with_conditions": "Feasible with conditions",
            "blocked": "Blocked",
        }
        body.append("<p class=\"status\">{0}</p>".format(labels.get(saved["verdict"], saved["verdict"])))
        body.append(
            "<ul><li>Required kits: {required}</li><li>Shortage: {shortage}</li><li>Purchase: {purchase} kits</li><li>Procurement cash: ${procurement_cash}</li><li>Materials consumed: ${materials_consumed}</li><li>Expected contribution: ${contribution}</li><li>Inventory after purchase and the event: {inventory_after} kits</li></ul>".format(
                **{key: escape(str(saved[key])) for key in (
                    "required", "shortage", "purchase", "procurement_cash", "materials_consumed", "contribution", "inventory_after"
                )}
            )
        )
        body.append("<p class=\"note\">Procurement cash is not subtracted again. Consumed kits are the materials cost. Unused kits stay in inventory. Calendar and staffing are available in this fixture.</p>")
        phase = saved.get("phase")
        if saved["verdict"] != "blocked" and phase == "assessed":
            body.append(_button("workshop", "workshop_approve", "Approve simulated commitment"))
        if phase == "approved" and saved.get("purchase", 0) > 0:
            body.append("<p>Preparations scheduled.</p>")
            body.append(_button("workshop", "workshop_receive", "Simulate materials received"))
        if (phase == "approved" and saved.get("purchase", 0) == 0) or phase == "materials_in":
            body.append("<p>Preparations scheduled. Required kits are available.</p>")
            body.append(_button("workshop", "workshop_complete", "Simulate event completion"))
        if phase == "completed":
            body.append("<p>Event reconciled. Kits consumed once. Remaining inventory: {0}. Contribution: ${1}.</p>".format(
                escape(str(saved["inventory_after"])), escape(str(saved["contribution"]))
            ))
        if saved.get("history"):
            body.append("<ol>{0}</ol>".format("".join("<li>{0}</li>".format(escape(line)) for line in saved["history"])))
    body.append(_button("workshop", "workshop_reset", "Reset demo", "secondary"))
    body.append("</article>")
    return shell("Workshop feasibility", "".join(body))


def detective_page(saved: Optional[dict], message: str = "") -> str:
    count = 16 if saved is None else saved.get("physical_count", 16)
    body = [
        "<h1>Where did the missing stock go?</h1>",
        "<p>Investigate discrepancies without inventing an explanation. This stock is not the reorder product.</p>",
        "<article><form method=\"post\" action=\"/\">{0}".format(_hidden("detective")),
        "<label>Physical count <input name=\"physical_count\" type=\"number\" min=\"0\" value=\"{0}\"></label>".format(count),
        "<button class=\"primary\" name=\"action\" value=\"detective_check\">Investigate discrepancy</button></form>",
    ]
    if message:
        body.append("<p>{0}</p>".format(escape(message)))
    if saved and saved.get("phase"):
        body.append("<ul>")
        body.append("<li>Discrepancy: {0} units.</li>".format(saved["discrepancy"]))
        body.append("<li>Fact: system quantity started at 20. Recorded workshop usage is 9. Attendance was 12.</li>")
        body.append("<li>Possible explanation: {0} more workshop units, only if consumption is confirmed. Attendance does not prove that.</li>".format(saved["hypothesis_units"]))
        body.append("<li>Missing evidence: one unit is still unexplained if those {0} units are verified.</li>".format(saved["hypothesis_units"]))
        body.append("<li>System inventory now: {0}. Unresolved: {1}. Days of supply for this scenario: {2}.</li>".format(
            saved["system_inventory"], saved["unresolved"], saved.get("days_of_supply", "")
        ))
        body.append("</ul>")
        if saved.get("discrepancy", 0) <= 0 and not saved.get("corrected"):
            body.append("<p>The count matches system inventory. No correction is offered.</p>")
        elif not saved.get("evidence_confirmed"):
            body.append(_button("detective", "detective_confirm", "Simulate confirming workshop consumption"))
        elif not saved.get("corrected"):
            body.append(_button(
                "detective",
                "detective_correct",
                "Approve {0}-unit workshop-usage correction".format(saved["hypothesis_units"]),
            ))
        elif not saved.get("closed"):
            body.append(
                "<form method=\"post\" action=\"/\">{0}".format(_hidden("detective"))
                + "<label>Recount <input name=\"recount\" type=\"number\" min=\"0\" value=\"{0}\"></label>".format(
                    saved["system_inventory"]
                )
                + "<button class=\"primary\" name=\"action\" value=\"detective_recount\">Record recount</button></form>"
            )
        else:
            body.append("<p>Discrepancy closed. The earlier count and the correction stay in the history.</p>")
        if saved.get("history"):
            body.append("<ol>{0}</ol>".format("".join("<li>{0}</li>".format(escape(line)) for line in saved["history"])))
    body.append(_button("detective", "detective_reset", "Reset demo", "secondary"))
    body.append("</article>")
    return shell("Inventory Detective", "".join(body))


def rescue_page(saved: Optional[dict], message: str = "") -> str:
    price = "119" if saved is None else saved.get("selling_price", "119")
    body = [
        "<h1>Save the sale</h1>",
        "<p>Find a viable local fulfillment option when your own stock cannot meet a deadline. These are merchant simulators, not live merchants or agents.</p>",
        "<article><form method=\"post\" action=\"/\">{0}".format(_hidden("rescue")),
        "<label>Customer selling price <input name=\"selling_price\" value=\"{0}\"></label>".format(escape(str(price))),
        "<button class=\"primary\" name=\"action\" value=\"rescue_offers\">Request simulated merchant offers</button></form>",
    ]
    if message:
        body.append("<p>{0}</p>".format(escape(message)))
    if saved and saved.get("offers"):
        for offer in saved["offers"]:
            body.append("<p><strong>{0}</strong> acquisition ${1}, transfer ${2}, contribution ${3}. {4}</p>".format(
                escape(offer["name"]), escape(offer["acquisition"]), escape(offer["transfer"]),
                escape(offer["contribution"]), escape(offer.get("note", offer["status"]))
            ))
            if saved.get("phase") == "quoted":
                body.append(
                    "<form method=\"post\" action=\"/\">{hidden}<input type=\"hidden\" name=\"action\" value=\"rescue_counter\">"
                    "<input type=\"hidden\" name=\"merchant_id\" value=\"{mid}\">"
                    "<label>Counteroffer <input name=\"counter_price\" value=\"{floor}\"></label>"
                    "<button class=\"secondary\" type=\"submit\">Submit counteroffer</button></form>".format(
                        hidden=_hidden("rescue"), mid=escape(offer["id"]), floor=escape(offer["floor"])
                    )
                )
        acceptable = [offer for offer in saved["offers"] if offer.get("acceptable")]
        if acceptable and saved.get("phase") in ("quoted", "negotiated"):
            best = max(acceptable, key=lambda item: Decimal(item["contribution"]))
            body.append("<p>Recommended simulator: {0}, contribution ${1}. No binding transaction yet.</p>".format(
                escape(best["name"]), escape(best["contribution"])
            ))
            body.append(_button("rescue", "rescue_authorize", "Authorize simulated fulfillment"))
        elif saved.get("phase") == "quoted":
            body.append("<p>No simulator meets the ${0} minimum contribution and the fulfillment rules.</p>".format(
                escape(str(RESCUE_FIXTURE["minimum_contribution"]))
            ))
        if saved.get("phase") == "authorized":
            body.append(_button("rescue", "rescue_transfer", "Simulate transfer"))
        if saved.get("phase") == "transferred":
            body.append(_button("rescue", "rescue_fulfill", "Simulate customer fulfillment"))
        if saved.get("phase") == "completed":
            body.append("<p>Fulfillment reconciled. Contribution ${0}. This was not a real purchase.</p>".format(
                escape(str(saved.get("final_contribution", "")))
            ))
        if saved.get("history"):
            body.append("<ol>{0}</ol>".format("".join("<li>{0}</li>".format(escape(line)) for line in saved["history"])))
    body.append(_button("rescue", "rescue_reset", "Reset demo", "secondary"))
    body.append("</article>")
    return shell("Sale rescue", "".join(body))


def staffing_page(saved: Optional[dict], message: str = "") -> str:
    day = "tuesday" if saved is None else saved.get("day", "tuesday")
    owner = "6" if saved is None else saved.get("owner_hours", "6")
    workshop = False if saved is None else bool(saved.get("workshop"))
    body = [
        "<h1>Plan the right coverage</h1>",
        "<p>Estimate workload before scheduling the team. This is a planning estimate, not an hourly schedule, and it does not choose which person works.</p>",
        "<article><form method=\"post\" action=\"/\">{0}".format(_hidden("staffing")),
        "<label>Day <select name=\"day\"><option value=\"tuesday\"{0}>Tuesday</option><option value=\"saturday\"{1}>Saturday</option></select></label>".format(
            " selected" if day == "tuesday" else "", " selected" if day == "saturday" else ""
        ),
        "<label>Workshop <input type=\"checkbox\" name=\"workshop\" value=\"1\"{0}> Add four staff-hours</label>".format(
            " checked" if workshop else ""
        ),
        "<label>Owner capacity in hours <input name=\"owner_hours\" value=\"{0}\"></label>".format(escape(str(owner))),
        "<button class=\"primary\" name=\"action\" value=\"staffing_calculate\">Calculate coverage</button></form>",
    ]
    if message:
        body.append("<p>{0}</p>".format(escape(message)))
    if saved and saved.get("workload_hours"):
        body.append("<ul><li>History: {0}</li><li>Expected transactions: {1}</li><li>Pickups: {2}</li><li>Workload hours: {3}</li><li>Hours beyond owner capacity: {4}</li><li>Four-hour blocks, rounded up: {5}</li></ul>".format(
            escape(str(saved["history"])), escape(str(saved["expected_transactions"])), saved["pickups"],
            escape(str(saved["workload_hours"])), escape(str(saved["extra_hours"])), saved["coverage_blocks"],
        ))
        body.append("<p class=\"note\">Each transaction and pickup is 15 minutes, plus one baseline hour. A workshop adds four staff-hours. The owner assigns people.</p>")
        if not saved.get("saved"):
            body.append(_button("staffing", "staffing_save", "Save simulated coverage plan"))
        else:
            body.append("<p>Saved recommendation for {0}. This is not an employee schedule.</p>".format(escape(saved["day"])))
    body.append(_button("staffing", "staffing_reset", "Reset demo", "secondary"))
    body.append("</article>")
    return shell("Staffing coverage", "".join(body))


def apply_ops(path: str, action: str, fields: dict, session_id: str = "local") -> None:
    store = ScenarioStore(path, session_id)
    try:
        if action == "workshop_check":
            result = assess_workshop(_int_field(fields, "attendees", 20), _int_field(fields, "days_until", 7))
            result["history"] = ["Checked feasibility for {0} attendees in {1} days.".format(result["attendees"], result["days_until"])]
            store.save("workshop", result)
            return
        if action == "workshop_approve":
            current = _require(store, "workshop")
            updated = workshop_approve(current)
            if not updated.get("replayed"):
                updated["history"] = list(current.get("history", [])) + ["Preparations scheduled. Simulated authorization recorded."]
            store.save("workshop", updated)
            return
        if action == "workshop_receive":
            current = _require(store, "workshop")
            updated = workshop_receive(current)
            if not updated.get("replayed"):
                updated["history"] = list(current.get("history", [])) + ["Simulated materials received. No supplier was contacted."]
            store.save("workshop", updated)
            return
        if action == "workshop_complete":
            current = _require(store, "workshop")
            updated = workshop_complete(current)
            if not updated.get("replayed"):
                updated["history"] = list(current.get("history", [])) + [
                    "Event completed once. Consumed kits reconciled. Remaining inventory {0}.".format(updated["inventory_after"])
                ]
            store.save("workshop", updated)
            return
        if action == "workshop_reset":
            store.reset("workshop")
            return
        if action == "detective_check":
            case = investigate_stock(_int_field(fields, "physical_count", 16))
            case["days_of_supply"] = str(detective_days_of_supply(case["system_inventory"]))
            store.save("detective", case)
            return
        if action == "detective_confirm":
            updated = confirm_workshop_evidence(_require(store, "detective"))
            updated["days_of_supply"] = str(detective_days_of_supply(updated["system_inventory"]))
            store.save("detective", updated)
            return
        if action == "detective_correct":
            updated = apply_usage_correction(_require(store, "detective"))
            updated["days_of_supply"] = str(detective_days_of_supply(updated["system_inventory"]))
            store.save("detective", updated)
            return
        if action == "detective_recount":
            current = _require(store, "detective")
            updated = apply_recount(current, _int_field(fields, "recount", current["system_inventory"]))
            updated["days_of_supply"] = str(detective_days_of_supply(updated["system_inventory"]))
            if updated.get("closed"):
                updated["phase"] = "completed"
            store.save("detective", updated)
            return
        if action == "detective_reset":
            store.reset("detective")
            return
        if action == "rescue_offers":
            price = Decimal(fields.get("selling_price", ["119"])[0])
            offers = default_offers(price)
            store.save("rescue", {"phase": "quoted", "selling_price": _money_plain(price), "offers": offers, "history": ["Requested simulated offers."]})
            return
        if action == "rescue_counter":
            current = _require(store, "rescue")
            if current.get("phase") in ("authorized", "transferred", "completed"):
                raise ValueError("This sale is already past negotiation.")
            merchant_id = fields.get("merchant_id", [""])[0]
            counter = Decimal(fields.get("counter_price", ["0"])[0])
            offers = []
            for offer in current["offers"]:
                if offer["id"] == merchant_id:
                    offers.append(negotiate(offer, counter, Decimal(current["selling_price"])))
                else:
                    offers.append(offer)
            current["offers"] = offers
            current["phase"] = "negotiated"
            current["history"] = list(current.get("history", [])) + ["Counteroffer sent to a merchant simulator."]
            store.save("rescue", current)
            return
        if action == "rescue_authorize":
            current = _require(store, "rescue")
            acceptable = [offer for offer in current["offers"] if offer.get("acceptable")]
            if not acceptable:
                raise ValueError("No acceptable simulated offer.")
            if current.get("phase") in ("authorized", "transferred", "completed"):
                return
            best = max(acceptable, key=lambda item: Decimal(item["contribution"]))
            current["phase"] = "authorized"
            current["chosen"] = best["id"]
            current["final_contribution"] = best["contribution"]
            current["history"] = list(current.get("history", [])) + ["Simulated authorization for {0}.".format(best["name"])]
            store.save("rescue", current)
            return
        if action == "rescue_transfer":
            current = _require(store, "rescue")
            if current.get("phase") == "transferred" or current.get("phase") == "completed":
                return
            if current.get("phase") != "authorized":
                raise ValueError("Authorize the simulator before transfer.")
            current["phase"] = "transferred"
            current["history"] = list(current.get("history", [])) + ["Simulated transfer. No merchant was contacted."]
            store.save("rescue", current)
            return
        if action == "rescue_fulfill":
            current = _require(store, "rescue")
            if current.get("phase") == "completed":
                return
            if current.get("phase") != "transferred":
                raise ValueError("Transfer before fulfillment.")
            current["phase"] = "completed"
            current["history"] = list(current.get("history", [])) + ["Customer fulfillment reconciled."]
            store.save("rescue", current)
            return
        if action == "rescue_reset":
            store.reset("rescue")
            return
        if action == "staffing_calculate":
            day = fields.get("day", ["tuesday"])[0]
            workshop = fields.get("workshop", ["0"])[0] == "1"
            owner = Decimal(fields.get("owner_hours", ["6"])[0])
            plan = staffing_plan(day, workshop, owner)
            plan["phase"] = "calculated"
            store.save("staffing", plan)
            return
        if action == "staffing_save":
            current = _require(store, "staffing")
            if current.get("saved"):
                return
            current["saved"] = True
            current["phase"] = "completed"
            store.save("staffing", current)
            return
        if action == "staffing_reset":
            store.reset("staffing")
            return
        raise ValueError("Unknown scenario action.")
    finally:
        store.close()


def _require(store: ScenarioStore, name: str) -> dict:
    current = store.get(name)
    if current is None:
        raise ValueError("Check the scenario before acting on it.")
    return current


def _int_field(fields: dict, name: str, default: int) -> int:
    raw = fields.get(name, [str(default)])[0]
    return int(raw)


def _money_plain(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def empty_cards() -> list:
    return load_cards_from(None, None, None, None, "Not started", "Not started", _start_form())


def _start_form() -> str:
    return (
        '<form method="post" action="/"><input type="hidden" name="scenario" value="reorder">'
        '<input type="hidden" name="action" value="simulate_email">'
        '<button class="primary" type="submit">Start interactive demo</button></form>'
    )


def load_cards(path: str, reorder_status: str, reorder_bucket: str, reorder_action: str = "", session_id: str = "local") -> list:
    store = ScenarioStore(path, session_id)
    try:
        return load_cards_from(
            store.get("workshop"), store.get("detective"), store.get("rescue"), store.get("staffing"),
            reorder_status, reorder_bucket, reorder_action,
        )
    finally:
        store.close()


def load_cards_from(workshop, detective, rescue, staffing, reorder_status, reorder_bucket, reorder_action) -> list:
    return [
        {"title": "Reorder the quiet linear switches", "description": "Supplier delay, one approval, simulated receipt.", "href": "/?scenario=reorder", "status": reorder_status, "bucket": reorder_bucket, "action": reorder_action},
        _card("Can we take this on?", "Workshop feasibility before a customer promise.", "/?scenario=workshop", workshop, "Not checked"),
        _card("Where did the missing stock go?", "A count discrepancy with no invented cause.", "/?scenario=detective", detective, "Not investigated"),
        _card("Save the sale", "Two merchant simulators and a contribution check.", "/?scenario=rescue", rescue, "Not requested"),
        _card("Plan the right coverage", "Workload estimate before anyone is scheduled.", "/?scenario=staffing", staffing, "Not calculated"),
    ]


def _card(title: str, description: str, href: str, saved: Optional[dict], empty_status: str) -> dict:
    if saved is None:
        return {"title": title, "description": description, "href": href, "status": empty_status, "bucket": "Not started"}
    phase = saved.get("phase", "")
    if phase == "completed" and "contribution" in saved:
        bucket = "Completed"
        status = "Completed. Contribution ${0}. {1} kits left.".format(
            saved["contribution"], saved.get("inventory_after", "")
        )
    elif phase == "completed" or saved.get("closed") or saved.get("saved"):
        bucket = "Completed"
        status = "Completed"
    elif phase in ("assessed", "investigated", "quoted", "negotiated", "calculated"):
        bucket = "Needs your decision"
        status = phase.replace("_", " ")
    else:
        bucket = "In progress"
        status = phase.replace("_", " ")
    return {"title": title, "description": description, "href": href, "status": status, "bucket": bucket}
