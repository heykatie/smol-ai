"""Dashboard and scenario pages. Synthetic data, simulated external actions."""

from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import Optional

PRACTICE_BANNER = (
    '<p class="sim-banner" role="note">'
    "<strong>Demo tour.</strong> "
    "Practice run with simulated inbox, purchase, and money. "
    "Not a live shop catalog."
    "</p>"
)

# Demo-tour surface (try without signup). Product home is `/`; practice-owner login is later.
SANDBOX_PREFIX = "/try"
INVENTORY_MODE_SANDBOX = "sandbox"
INVENTORY_MODE_OWNER = "owner"

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


def sandbox_href(scenario: str = "", **params: str) -> str:
    """Build a sandbox URL under `/try`."""
    query = []
    if scenario and scenario != "home":
        query.append("scenario={0}".format(scenario))
    for key, value in params.items():
        if value:
            query.append("{0}={1}".format(key, value))
    if not query:
        return SANDBOX_PREFIX
    return "{0}?{1}".format(SANDBOX_PREFIX, "&".join(query))


def shell(title: str, body: str) -> str:
    """Demo-tour chrome — try-without-signup surface only."""
    nav = [
        ("Daily brief", sandbox_href(), "✦"),
        ("Inventory", sandbox_href("inventory"), "▣"),
        ("Reorder", sandbox_href("reorder"), "↗"),
        ("Workshop feasibility", sandbox_href("workshop"), "◇"),
        ("Inventory Detective", sandbox_href("detective"), "⌕"),
        ("Sale rescue", sandbox_href("rescue"), "♡"),
        ("Staffing coverage", sandbox_href("staffing"), "☷"),
    ]
    links = "".join(
        '<a href="{href}"{active}><span class="nav-icon" aria-hidden="true">{icon}</span>{label}</a>'.format(
            href=href,
            active=' aria-current="page"' if title == label else "",
            icon=icon,
            label=escape(label),
        )
        for label, href, icon in nav
    )
    home = (
        ""
        if title == "Daily brief"
        else '<a class="home" href="{0}">← Daily brief</a>'.format(sandbox_href())
    )
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="theme-color" content="#101115">'
        '<title>smolstuff — {title}</title><style>{style}</style></head>'
        '<body><a class="skip" href="#content">Skip to content</a><div class="app-layout">'
        '<aside class="rail"><a class="brand" href="{sandbox}" aria-label="smolstuff demo tour">'
        '<span class="brand-mark" aria-hidden="true">:)</span>smolstuff</a>'
        '<div><p class="rail-label">Demo tour</p><nav aria-label="Main navigation">{nav}</nav></div>'
        '<div class="rail-note"><strong>Try without signup.</strong> '
        "Demo workflows and a small demo catalog. No sponsor calls here.</div></aside>"
        '<main id="content" tabindex="-1"><header class="top">'
        '<span class="workspace"><strong>Demo tour</strong> / {title}</span>'
        '<span class="demo-tag">Demo tour</span>{home}'
        '<a class="home" href="/">Product home</a></header>{body}'
        '<footer class="footer-note">Fictional demo data. Purchases, messages, and deliveries are simulated. '
        "This tour does not monitor a real inbox. The full specialty-shop catalog belongs "
        "on the practice-owner app after login (not shipped yet). Sponsor calls stay off here.</footer>"
        "</main></div></body></html>"
    ).format(
        title=escape(title),
        style=STYLE,
        nav=links,
        home=home,
        body=body,
        sandbox=SANDBOX_PREFIX,
    )


def product_home_page() -> str:
    """Public product stub. `/try` is the demo tour; practice-owner login comes later."""
    body = (
        '<section class="hero"><span class="hero-spark" aria-hidden="true">✧</span>'
        '<p class="kicker">smolstuff</p>'
        "<h1>Operations help that keeps you in charge.</h1>"
        '<p class="lede">Connect the signals, see what needs a decision, and act within limits you set. '
        "Two surfaces: a public demo tour now, and a practice-owner app with seeded shop data after login.</p>"
        '<div class="card-actions decision-actions">'
        '<a class="open" href="{sandbox}">Start demo tour →</a>'
        "</div></section>"
        '<p class="sim-banner" role="note"><strong>Two surfaces.</strong> '
        "<strong>Demo tour</strong> (`/try`) = no login, simulated workflows, small demo catalog, "
        "no paid calls. <strong>Practice owner</strong> = login, dense seeded specialty-shop inventory, "
        "real working features, sponsor calls under budget. Practice-owner sign-in is not shipped yet.</p>"
        '<div class="grid">'
        "<article><h3>Demo tour</h3>"
        "<p>Walk reorder and four practice loops on demo products and demo data. "
        "Inventory shows only the tour SKUs (not a full shop assortment). Reset anytime.</p>"
        '<a class="open" href="{sandbox}">Open demo tour →</a></article>'
        "<article><h3>Practice owner</h3>"
        "<p>Real login and a seeded tenant with the full specialty-shop catalog "
        "(~492 fictional SKUs), disposable demo connectors, and capped sponsor calls.</p>"
        '<p class="note">Sign in is not available on this build. Dense inventory attaches here when login ships.</p></article>'
        "</div>"
    ).format(sandbox=SANDBOX_PREFIX)
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="theme-color" content="#101115">'
        "<title>smolstuff</title><style>{style}</style></head>"
        '<body><a class="skip" href="#content">Skip to content</a><div class="app-layout">'
        '<aside class="rail"><a class="brand" href="/" aria-label="smolstuff home">'
        '<span class="brand-mark" aria-hidden="true">:)</span>smolstuff</a>'
        '<div><p class="rail-label">Product</p><nav aria-label="Main navigation">'
        '<a href="/" aria-current="page"><span class="nav-icon" aria-hidden="true">✦</span>Home</a>'
        '<a href="{sandbox}"><span class="nav-icon" aria-hidden="true">▣</span>Demo tour</a>'
        "</nav></div>"
        '<div class="rail-note"><strong>Small but mighty.</strong>'
        "One less thing for you to carry. You keep the final say.</div></aside>"
        '<main id="content" tabindex="-1"><header class="top">'
        '<span class="workspace"><strong>smolstuff</strong> / Home</span></header>{body}'
        '<footer class="footer-note">No real business accounts on this page. '
        "Use the demo tour to explore with fictional data. Practice-owner login is next.</footer>"
        "</main></div></body></html>"
    ).format(style=STYLE, sandbox=SANDBOX_PREFIX, body=body)


def error_page(message: str = "That action or value could not be accepted.") -> str:
    return shell(
        "Check your input",
        '<h1>Let’s try that again.</h1><article class="alert" role="alert"><p>{0}</p>'
        "<p>Return to the sandbox daily brief, open the workflow, and check the values before submitting.</p>"
        '<a class="open" href="{1}">Back to sandbox</a></article>'.format(
            escape(message), SANDBOX_PREFIX
        ),
    )


def _hidden(scenario: str) -> str:
    return '<input type="hidden" name="scenario" value="{0}">'.format(escape(scenario))


def _button(scenario: str, action: str, label: str, kind: str = "primary") -> str:
    return (
        '<form method="post" action="{action_url}">'
        "{hidden}<input type=\"hidden\" name=\"action\" value=\"{action}\">"
        '<button class="{kind}" type="submit">{label}</button></form>'
    ).format(
        action_url=SANDBOX_PREFIX,
        hidden=_hidden(scenario),
        action=escape(action),
        kind=escape(kind),
        label=escape(label),
    )


_BUCKET_CLASS = {
    "Needs your decision": "decision",
    "In progress": "progress",
    "Completed": "done",
    "Not started": "idle",
}


def _dashboard_next_step(card: dict) -> str:
    """Plain next-step line for launcher cards (owner language, not phase jargon)."""
    href = str(card.get("href") or "")
    bucket = str(card.get("bucket") or "")
    scenario = href.split("=")[-1] if "=" in href else ""
    if bucket == "Needs your decision":
        return {
            "reorder": "Next: approve or decline the $189 practice order.",
            "workshop": "Next: say yes to the customer commitment, or adjust the ask.",
            "detective": "Next: choose how to handle the count gap.",
            "rescue": "Next: compare neighbor offers to the sale target.",
            "staffing": "Next: review the hours estimate and remember it if useful.",
        }.get(scenario, "Next: open this demo and choose what to do.")
    if bucket == "In progress":
        return {
            "reorder": "Next: confirm receipt so stock can update.",
            "workshop": "Next: finish materials prep or complete the event.",
            "detective": "Next: finish the count check or recount.",
            "rescue": "Next: decide if a neighbor offer saves the sale.",
            "staffing": "Next: finish the coverage estimate.",
        }.get(scenario, "Next: continue this practice run.")
    if bucket == "Completed":
        return "Done for this session. Open to review, or reset inside the demo."
    return {
        "reorder": "Best place to start — one approval, then a verified receipt.",
        "workshop": "Check whether you can take a build-night booking.",
        "detective": "Look at a count mismatch without guessing a cause.",
        "rescue": "See if nearby shops can cover a missing part.",
        "staffing": "Estimate Saturday hours — not who works the shift.",
    }.get(scenario, "Open this practice demo.")


def _product_needs_attention(product: dict) -> bool:
    """Catalog rows that should surface on the owner attention path."""
    totals = product.get("totals") or {}
    if int(totals.get("inbound", 0) or 0) > 0:
        return True
    if int(totals.get("in_transfer", 0) or 0) > 0:
        return True
    if int(totals.get("damaged", 0) or 0) > 0:
        return True
    if int(totals.get("returns_pending", 0) or 0) > 0:
        return True
    if product.get("status_class") in ("decision", "waiting", "progress"):
        return True
    stock_label, _, _ = _stock_condition(totals)
    return stock_label == "Out of stock"


def inventory_attention_count(snapshot: Optional[dict] = None) -> int:
    products = (snapshot or empty_inventory_snapshot()).get("products") or ()
    return sum(1 for product in products if _product_needs_attention(product))


def dashboard_page(cards: list, events=(), *, inventory_attention: int = 0) -> str:
    groups = {"Needs your decision": [], "In progress": [], "Completed": [], "Not started": []}
    for card in cards:
        groups.setdefault(card["bucket"], []).append(card)
    order = ("Needs your decision", "In progress", "Not started", "Completed")
    reorder = next(
        (card for card in cards if "scenario=reorder" in str(card.get("href", ""))),
        None,
    )
    sections = [
        '<section class="hero"><span class="hero-spark" aria-hidden="true">✧</span>'
        '<p class="kicker">Demo tour</p>'
        "<h1>Start here. Follow one decision through.</h1>"
        '<p class="lede">Five hands-on demo workflows on demo data. Begin with reorder — supplier delay, '
        "one approval, then stock that actually updates on the small tour catalog.</p>"
        "</section>",
        PRACTICE_BANNER,
    ]
    if inventory_attention > 0:
        sections.append(
            '<article class="card attention-card" id="inventory-attention">'
            '<p class="status waiting">Needs attention</p>'
            "<h2>{count} catalog lines need a look</h2>"
            "<p>Incoming, in-transit, damaged/returns, out of stock, or an open demo issue. "
            "Open the filtered inventory list to work them.</p>"
            '<div class="card-actions">'
            '<a class="open" href="{href}">'
            "Review inventory →</a>"
            "</div></article>".format(
                count=inventory_attention,
                href=escape(sandbox_href("inventory", view="attention")),
            )
        )
    if reorder is not None:
        sections.append(
            '<article class="card decision-card launch-primary">'
            '<p class="status {tone}">{status}</p>'
            "<h2 class=\"launch-title\">{title}</h2>"
            "<p>{description}</p>"
            '<p class="consequence">{next}</p>'
            '<div class="card-actions decision-actions">'
            '<a class="open" href="{href}" aria-label="Open {title}">Open reorder →</a>'
            "{action}"
            "</div></article>".format(
                tone=_BUCKET_CLASS.get(reorder["bucket"], "idle"),
                status=escape(reorder["status"]),
                title=escape(reorder["title"]),
                description=escape(reorder["description"]),
                next=escape(_dashboard_next_step(reorder)),
                href=escape(reorder["href"]),
                action=reorder.get("action", ""),
            )
        )
    sections.append('<p class="note">Session counts below. Other demos are optional after reorder.</p>')
    sections.append(
        '<p class="counts">{0}</p>'.format(
            "".join(
                "<span>{1}<strong>{0}</strong></span>".format(
                    len(groups[name]), escape(name).lower()
                )
                for name in order
            )
        )
    )
    for name in order:
        items = [
            card
            for card in groups.get(name, [])
            if "scenario=reorder" not in str(card.get("href", ""))
        ]
        if not items:
            continue
        heading = {
            "Not started": "More practice demos",
            "Needs your decision": "Needs your decision",
            "In progress": "In progress",
            "Completed": "Completed",
        }.get(name, name)
        sections.append("<h2>{0} ({1})</h2>".format(escape(heading), len(items)))
        sections.append('<div class="grid">')
        for card in items:
            tone = _BUCKET_CLASS.get(card["bucket"], "idle")
            sections.append(
                "<article><div class=\"card-top\"><span class=\"card-icon\" aria-hidden=\"true\">{icon}</span>"
                '<p class="status {tone}">{status}</p></div><h3>{title}</h3><p>{description}</p>'
                '<p class="note card-next">{next}</p>'
                '<div class="card-actions"><a class="open" href="{href}" aria-label="Open {title}">Open →</a>'
                "{action}</div></article>".format(
                    tone=tone,
                    icon={
                        "workshop": "◇",
                        "detective": "⌕",
                        "rescue": "♡",
                        "staffing": "☷",
                    }.get(card["href"].split("=")[-1], "✦"),
                    status=escape(card["status"]),
                    title=escape(card["title"]),
                    description=escape(card["description"]),
                    next=escape(_dashboard_next_step(card)),
                    href=escape(card["href"]),
                    action=card.get("action", ""),
                )
            )
        sections.append("</div>")
    sections.append("<h2>Tool activity this session</h2>")
    if events:
        sections.append('<ul class="activity">')
        for event in events:
            sections.append(
                "<li><strong>{0}</strong> · {1}. {2} {3}</li>".format(
                    escape(event.provider),
                    escape(event.status),
                    escape(event.result),
                    escape(event.effect),
                )
            )
        sections.append("</ul>")
    else:
        sections.append(
            '<p class="note empty">No tools have run in this session yet.</p>'
        )
    return shell("Daily brief", "".join(sections))


def _preview_hero(kicker: str, headline: str, lede: str) -> str:
    return (
        '<section class="hero decision-hero">'
        '<p class="kicker">{kicker}</p>'
        "<h1>{headline}</h1>"
        '<p class="lede">{lede}</p>'
        "</section>"
    ).format(kicker=escape(kicker), headline=escape(headline), lede=escape(lede))


def _workshop_decision(saved: dict) -> tuple[str, str, str]:
    labels = {
        "feasible": ("done", "Feasible"),
        "feasible_with_conditions": ("waiting", "Feasible with a purchase"),
        "blocked": ("decision", "Blocked"),
    }
    tone, status = labels.get(saved["verdict"], ("idle", saved["verdict"]))
    if saved["verdict"] == "blocked":
        decision = "Do not promise this workshop yet — timing or economics fail the check."
    elif int(saved.get("purchase", 0) or 0) > 0:
        decision = (
            "Buy {0} bottleneck switch packs so you can take the {1}-seat booking."
        ).format(saved["purchase"], saved["required"])
    else:
        decision = "You already have enough seat materials for this booking."
    consequence = (
        "Expected contribution: ${0}. Complete seats left after the event: {1}."
    ).format(saved["contribution"], saved["inventory_after"])
    return tone, status, '<p class="decision">{0}</p><p class="consequence">{1}</p>'.format(
        escape(decision), escape(consequence)
    )


def workshop_page(saved: Optional[dict], message: str = "") -> str:
    attendees = WORKSHOP_FIXTURE["attendees"] if saved is None else saved.get("attendees", 20)
    days_until = WORKSHOP_FIXTURE["days_until"] if saved is None else saved.get("days_until", 7)
    body = [
        PRACTICE_BANNER,
        _preview_hero(
            "Workshop · build night",
            "Can we take this on?",
            "A customer wants a paid build night. Check seats, cash, and timing before you promise — "
            "materials are per seat (switch pack + film + pullers), not one sealed kit.",
        ),
        '<article class="card decision-card">',
        "<p>Inquiry: Could you run a keyboard build night for 20 people next week, "
        "including all materials, for $1,500?</p>",
        "<form method=\"post\" action=\"{0}\">{1}".format(SANDBOX_PREFIX, _hidden("workshop")),
        "<label>Attendees <input name=\"attendees\" type=\"number\" min=\"1\" value=\"{0}\"></label>".format(attendees),
        "<label>Days until the event <input name=\"days_until\" type=\"number\" min=\"0\" value=\"{0}\"></label>".format(days_until),
        "<button class=\"primary\" name=\"action\" value=\"workshop_check\">Check feasibility</button></form>",
    ]
    if message:
        body.append("<p>{0}</p>".format(escape(message)))
    if saved and saved.get("verdict"):
        tone, status, decision_html = _workshop_decision(saved)
        body.append(
            '<p class="status {tone}">{status}</p>{decision}'.format(
                tone=tone, status=escape(status), decision=decision_html
            )
        )
        body.append('<div class="card-actions decision-actions">')
        phase = saved.get("phase")
        if saved["verdict"] != "blocked" and phase == "assessed":
            body.append(_button("workshop", "workshop_approve", "Approve simulated commitment"))
        if phase == "approved" and saved.get("purchase", 0) > 0:
            body.append(_button("workshop", "workshop_receive", "Simulate materials received"))
        if (phase == "approved" and saved.get("purchase", 0) == 0) or phase == "materials_in":
            body.append(_button("workshop", "workshop_complete", "Simulate event completion"))
        body.append("</div>")
        if phase == "approved" and saved.get("purchase", 0) > 0:
            body.append("<p class=\"note\">Commitment saved. Next: simulate the materials arriving.</p>")
        if (phase == "approved" and saved.get("purchase", 0) == 0) or phase == "materials_in":
            body.append("<p class=\"note\">Seat materials are ready. Next: simulate the event finishing.</p>")
        if phase == "completed":
            body.append(
                "<p>Event reconciled. Seat materials consumed once. "
                "Complete seats left: {0}. Contribution: ${1}.</p>".format(
                    escape(str(saved["inventory_after"])),
                    escape(str(saved["contribution"])),
                )
            )
        body.append('<details class="why-details"><summary>Why this recommendation</summary>')
        body.append(
            "<ul><li>Required seats: {required}</li><li>Seat shortage: {shortage}</li>"
            "<li>Buy bottleneck packs: {purchase}</li><li>Purchase cash: ${procurement_cash}</li>"
            "<li>Materials consumed: ${materials_consumed}</li><li>Expected contribution: ${contribution}</li>"
            "<li>Complete seats after event: {inventory_after}</li></ul>".format(
                **{key: escape(str(saved[key])) for key in (
                    "required", "shortage", "purchase", "procurement_cash",
                    "materials_consumed", "contribution", "inventory_after",
                )}
            )
        )
        if saved.get("bom"):
            body.append("<p><strong>Seat materials</strong></p><ul>")
            for line in saved["bom"]:
                body.append(
                    "<li>{name} ({sku}): need {need}, on hand {on_hand}, buy {buy}, after {after}</li>".format(
                        name=escape(line["name"]),
                        sku=escape(line["sku"]),
                        need=escape(str(line["required_units"])),
                        on_hand=escape(str(line["on_hand"])),
                        buy=escape(str(line.get("purchase", 0))),
                        after=escape(str(line.get("after_units", ""))),
                    )
                )
            body.append("</ul>")
        body.append(
            "<p class=\"note\">You only buy the bottleneck switch packs. "
            "Seat materials still cost $20. Unused component stock stays in inventory.</p>"
        )
        if saved.get("history"):
            body.append("<ol>{0}</ol>".format(
                "".join("<li>{0}</li>".format(escape(line)) for line in saved["history"])
            ))
        body.append("</details>")
    body.append(_button("workshop", "workshop_reset", "Reset demo", "secondary"))
    body.append("</article>")
    return shell("Workshop feasibility", "".join(body))


def detective_page(saved: Optional[dict], message: str = "") -> str:
    count = 16 if saved is None else saved.get("physical_count", 16)
    body = [
        PRACTICE_BANNER,
        _preview_hero(
            "Detective · sample strips",
            "Where did the missing stock go?",
            "System says 20 sample strips; the shelf count says 16. "
            "Investigate without inventing a cause — these are workshop try strips, not the quiet linear reorder line.",
        ),
        '<article class="card decision-card">',
        "<form method=\"post\" action=\"{0}\">{1}".format(SANDBOX_PREFIX, _hidden("detective")),
        "<label>Physical count <input name=\"physical_count\" type=\"number\" min=\"0\" value=\"{0}\"></label>".format(count),
        "<button class=\"primary\" name=\"action\" value=\"detective_check\">Investigate discrepancy</button></form>",
    ]
    if message:
        body.append("<p>{0}</p>".format(escape(message)))
    if saved and saved.get("phase"):
        if saved.get("closed"):
            tone, status = "done", "Closed"
            decision = "Counts agree after recount. Keep the earlier count and correction in history."
            consequence = "Case closed. No further inventory write-off."
        elif saved.get("corrected"):
            tone, status = "progress", "Corrected — recount next"
            decision = "Workshop usage correction applied. Record a recount to close the case."
            consequence = (
                "System inventory now {0}. Unresolved: {1}."
            ).format(saved["system_inventory"], saved["unresolved"])
        elif saved.get("evidence_confirmed"):
            tone, status = "waiting", "Evidence ready"
            decision = (
                "Approve a {0}-unit workshop-usage correction — only the confirmed uses."
            ).format(saved["hypothesis_units"])
            consequence = "Attendance alone is not proof. One unit may still stay unexplained."
        elif saved.get("discrepancy", 0) <= 0:
            tone, status = "done", "No mismatch"
            decision = "The count matches system inventory."
            consequence = "No correction is offered."
        else:
            tone, status = "decision", "Needs evidence"
            decision = (
                "Confirm workshop consumption before changing inventory "
                "({0} units unexplained)."
            ).format(saved["discrepancy"])
            consequence = (
                "Possible explanation: {0} more workshop uses — only if confirmed."
            ).format(saved["hypothesis_units"])
        body.append(
            '<p class="status {tone}">{status}</p>'
            '<p class="decision">{decision}</p>'
            '<p class="consequence">{consequence}</p>'.format(
                tone=tone,
                status=escape(status),
                decision=escape(decision),
                consequence=escape(consequence),
            )
        )
        body.append('<div class="card-actions decision-actions">')
        if saved.get("discrepancy", 0) > 0 and not saved.get("evidence_confirmed"):
            body.append(_button("detective", "detective_confirm", "Simulate confirming workshop consumption"))
        elif saved.get("evidence_confirmed") and not saved.get("corrected"):
            body.append(_button(
                "detective",
                "detective_correct",
                "Approve {0}-unit workshop-usage correction".format(saved["hypothesis_units"]),
            ))
        elif saved.get("corrected") and not saved.get("closed"):
            body.append(
                "<form method=\"post\" action=\"{0}\">{1}".format(
                    SANDBOX_PREFIX, _hidden("detective")
                )
                + "<label>Recount <input name=\"recount\" type=\"number\" min=\"0\" value=\"{0}\"></label>".format(
                    saved["system_inventory"]
                )
                + "<button class=\"primary\" name=\"action\" value=\"detective_recount\">Record recount</button></form>"
            )
        body.append("</div>")
        body.append('<details class="why-details"><summary>Why this recommendation</summary><ul>')
        body.append("<li>Discrepancy: {0} units.</li>".format(escape(str(saved["discrepancy"]))))
        body.append(
            "<li>Fact: system quantity started at 20. Recorded workshop usage is 9. "
            "Attendance was 12.</li>"
        )
        body.append(
            "<li>Possible explanation: {0} more workshop units, only if consumption is confirmed. "
            "Attendance does not prove that.</li>".format(escape(str(saved["hypothesis_units"])))
        )
        body.append(
            "<li>Missing evidence: one unit is still unexplained if those {0} units are verified.</li>".format(
                escape(str(saved["hypothesis_units"]))
            )
        )
        body.append(
            "<li>System inventory now: {0}. Unresolved: {1}. Days of supply for this scenario: {2}.</li>".format(
                escape(str(saved["system_inventory"])),
                escape(str(saved["unresolved"])),
                escape(str(saved.get("days_of_supply", ""))),
            )
        )
        body.append("</ul>")
        if saved.get("history"):
            body.append("<ol>{0}</ol>".format(
                "".join("<li>{0}</li>".format(escape(line)) for line in saved["history"])
            ))
        body.append("</details>")
    body.append(_button("detective", "detective_reset", "Reset demo", "secondary"))
    body.append("</article>")
    return shell("Inventory Detective", "".join(body))


def rescue_page(saved: Optional[dict], message: str = "") -> str:
    price = "119" if saved is None else saved.get("selling_price", "119")
    body = [
        PRACTICE_BANNER,
        _preview_hero(
            "Sale rescue · local fill",
            "Save the sale",
            "A walk-in needs a part you don’t have in time. "
            "Ask practice neighbor shops — simulators only, not live merchants or agents.",
        ),
        '<article class="card decision-card">',
        "<form method=\"post\" action=\"{0}\">{1}".format(SANDBOX_PREFIX, _hidden("rescue")),
        "<label>Customer selling price <input name=\"selling_price\" value=\"{0}\"></label>".format(escape(str(price))),
        "<button class=\"primary\" name=\"action\" value=\"rescue_offers\">Request simulated merchant offers</button></form>",
    ]
    if message:
        body.append("<p>{0}</p>".format(escape(message)))
    if saved and saved.get("offers"):
        acceptable = [offer for offer in saved["offers"] if offer.get("acceptable")]
        phase = saved.get("phase")
        if phase == "completed":
            tone, status = "done", "Completed"
            decision = "Customer fulfillment reconciled for this practice run."
            consequence = "Contribution ${0}. This was not a real purchase.".format(
                saved.get("final_contribution", "")
            )
        elif phase == "transferred":
            tone, status = "progress", "Transferred"
            decision = "Simulate handing the part to the customer to finish the loop."
            consequence = "Stock moved between practice merchants; sale not closed yet."
        elif phase == "authorized":
            tone, status = "progress", "Authorized"
            decision = "Simulate the transfer from the chosen practice merchant."
            consequence = "No binding transaction until transfer and fulfillment complete."
        elif acceptable and phase in ("quoted", "negotiated"):
            best = max(acceptable, key=lambda item: Decimal(item["contribution"]))
            tone, status = "waiting", "Choose a path"
            decision = (
                "Authorize {0} — contribution ${1}. No binding transaction yet."
            ).format(best["name"], best["contribution"])
            consequence = "Or counter another simulator before you commit."
        elif phase == "quoted":
            tone, status = "decision", "No viable offer"
            decision = (
                "No simulator meets the ${0} minimum contribution and fulfillment rules."
            ).format(RESCUE_FIXTURE["minimum_contribution"])
            consequence = "Try another selling price, or reset the demo."
        else:
            tone, status = "idle", phase or "In progress"
            decision = "Review the practice offers below."
            consequence = "Contribution must stay above the floor after fees."
        body.append(
            '<p class="status {tone}">{status}</p>'
            '<p class="decision">{decision}</p>'
            '<p class="consequence">{consequence}</p>'.format(
                tone=tone,
                status=escape(status),
                decision=escape(decision),
                consequence=escape(consequence),
            )
        )
        body.append('<div class="card-actions decision-actions">')
        if acceptable and phase in ("quoted", "negotiated"):
            body.append(_button("rescue", "rescue_authorize", "Authorize simulated fulfillment"))
        if phase == "authorized":
            body.append(_button("rescue", "rescue_transfer", "Simulate transfer"))
        if phase == "transferred":
            body.append(_button("rescue", "rescue_fulfill", "Simulate customer fulfillment"))
        body.append("</div>")
        body.append('<details class="why-details" open><summary>Practice merchant offers</summary>')
        for offer in saved["offers"]:
            body.append(
                "<p><strong>{0}</strong> acquisition ${1}, transfer ${2}, contribution ${3}. {4}</p>".format(
                    escape(offer["name"]),
                    escape(offer["acquisition"]),
                    escape(offer["transfer"]),
                    escape(offer["contribution"]),
                    escape(offer.get("note", offer["status"])),
                )
            )
            if phase == "quoted":
                body.append(
                    "<form method=\"post\" action=\"{action}\">{hidden}"
                    "<input type=\"hidden\" name=\"action\" value=\"rescue_counter\">"
                    "<input type=\"hidden\" name=\"merchant_id\" value=\"{mid}\">"
                    "<label>Counteroffer <input name=\"counter_price\" value=\"{floor}\"></label>"
                    "<button class=\"secondary\" type=\"submit\">Submit counteroffer</button></form>".format(
                        action=SANDBOX_PREFIX,
                        hidden=_hidden("rescue"),
                        mid=escape(offer["id"]),
                        floor=escape(offer["floor"]),
                    )
                )
        if saved.get("history"):
            body.append("<ol>{0}</ol>".format(
                "".join("<li>{0}</li>".format(escape(line)) for line in saved["history"])
            ))
        body.append("</details>")
    body.append(_button("rescue", "rescue_reset", "Reset demo", "secondary"))
    body.append("</article>")
    return shell("Sale rescue", "".join(body))


def staffing_page(saved: Optional[dict], message: str = "") -> str:
    day = "tuesday" if saved is None else saved.get("day", "tuesday")
    owner = "6" if saved is None else saved.get("owner_hours", "6")
    workshop = False if saved is None else bool(saved.get("workshop"))
    body = [
        PRACTICE_BANNER,
        _preview_hero(
            "Staffing · coverage hours",
            "Plan the right coverage",
            "Estimate how many hours the day needs before you schedule anyone. "
            "This does not pick who works the shift.",
        ),
        '<article class="card decision-card">',
        "<form method=\"post\" action=\"{0}\">{1}".format(SANDBOX_PREFIX, _hidden("staffing")),
        "<label>Day <select name=\"day\"><option value=\"tuesday\"{0}>Tuesday</option>"
        "<option value=\"saturday\"{1}>Saturday</option></select></label>".format(
            " selected" if day == "tuesday" else "",
            " selected" if day == "saturday" else "",
        ),
        "<label>Workshop <input type=\"checkbox\" name=\"workshop\" value=\"1\"{0}> "
        "Add four staff-hours</label>".format(" checked" if workshop else ""),
        "<label>Owner capacity in hours <input name=\"owner_hours\" value=\"{0}\"></label>".format(
            escape(str(owner))
        ),
        "<button class=\"primary\" name=\"action\" value=\"staffing_calculate\">Calculate coverage</button></form>",
    ]
    if message:
        body.append("<p>{0}</p>".format(escape(message)))
    if saved and saved.get("workload_hours"):
        blocks = int(saved.get("coverage_blocks", 0) or 0)
        day_label = str(saved.get("day", day)).title()
        if blocks <= 0:
            tone, status = "done", "Owner can cover"
            decision = "No extra coverage blocks needed for {0}.".format(day_label)
            consequence = "Workload hours: {0}. Stay within owner capacity.".format(
                saved["workload_hours"]
            )
        else:
            tone, status = "waiting", "Needs coverage"
            decision = (
                "Plan {0} extra four-hour coverage block{1} for {2}."
            ).format(blocks, "" if blocks == 1 else "s", day_label)
            consequence = (
                "Workload hours: {0}. Hours beyond owner capacity: {1}."
            ).format(saved["workload_hours"], saved["extra_hours"])
        body.append(
            '<p class="status {tone}">{status}</p>'
            '<p class="decision">{decision}</p>'
            '<p class="consequence">{consequence}</p>'.format(
                tone=tone,
                status=escape(status),
                decision=escape(decision),
                consequence=escape(consequence),
            )
        )
        body.append('<div class="card-actions decision-actions">')
        if not saved.get("saved"):
            body.append(_button("staffing", "staffing_save", "Save simulated coverage plan"))
        else:
            body.append(
                "<p>Saved recommendation for {0}. This is not an employee schedule.</p>".format(
                    escape(str(saved["day"]))
                )
            )
        body.append("</div>")
        body.append('<details class="why-details"><summary>Why this recommendation</summary>')
        body.append(
            "<ul><li>History: {0}</li><li>Expected transactions: {1}</li>"
            "<li>Pickups: {2}</li><li>Workload hours: {3}</li>"
            "<li>Hours beyond owner capacity: {4}</li>"
            "<li>Four-hour blocks, rounded up: {5}</li></ul>".format(
                escape(str(saved["history"])),
                escape(str(saved["expected_transactions"])),
                escape(str(saved["pickups"])),
                escape(str(saved["workload_hours"])),
                escape(str(saved["extra_hours"])),
                escape(str(saved["coverage_blocks"])),
            )
        )
        body.append(
            "<p class=\"note\">Each transaction and pickup is 15 minutes, plus one baseline hour. "
            "A workshop adds four staff-hours. You still assign people yourself.</p>"
        )
        body.append("</details>")
    body.append(_button("staffing", "staffing_reset", "Reset demo", "secondary"))
    body.append("</article>")
    return shell("Staffing coverage", "".join(body))


# Shared workflow set shown in the Workflow column. Detail phrases stay in tooltips.
WORKFLOW_FROM_LABEL = {
    "Seeded": "Idle",
    "On shelf": "Idle",
    "BOM ready": "Idle",
    "Not investigated": "Idle",
    "Decision needed": "Needs decision",
    "Assessed": "Needs decision",
    "Approved": "In progress",
    "Awaiting receipt": "Waiting",
    "Materials inbound": "Waiting",
    "In progress": "In progress",
    "Investigating": "In progress",
    "Partially updated": "In progress",
    "Corrected": "In progress",
    "Updated": "Done",
    "Reconciled": "Done",
    "Closed": "Done",
    "Unchanged": "Done",
}

# Short pill labels (tooltips keep the full shared meaning).
WORKFLOW_PILL = {
    "Idle": "Idle",
    "Needs decision": "Decide",
    "Waiting": "Waiting",
    "In progress": "Active",
    "Done": "Done",
}

WORKFLOW_TONE = {
    "Idle": "idle",
    "Needs decision": "decision",
    "Waiting": "waiting",
    "In progress": "progress",
    "Done": "done",
}

WORKFLOW_HELP = {
    "Idle": "No open owner action on this SKU.",
    "Needs decision": "Owner approval or next choice is required before stock moves.",
    "Waiting": "Work is approved; waiting on inbound materials or receipt.",
    "In progress": "Active demo step is underway (receipt, workshop, or detective).",
    "Done": "This demo path finished for the SKU (updated, reconciled, closed, or declined).",
}

# Specific tooltip detail (maps from internal phase labels set by demos).
WORKFLOW_DETAIL_HELP = {
    "Seeded": "Reorder demo baseline. No owner decision yet.",
    "BOM ready": "Workshop BOM line is ready to assess.",
    "Not investigated": "Detective has not started a count check.",
    "On shelf": "Browse row only; no workflow demo is attached.",
    "Decision needed": "Reorder waiting for purchase approval.",
    "Awaiting receipt": "Order confirmed; units stay inbound until receipt.",
    "Updated": "Full receipt reconciled into available.",
    "Unchanged": "Purchase declined; quantities unchanged.",
    "Partially updated": "Partial receipt posted; inbound may remain.",
    "Reconciled": "Workshop consumption written back to remaining units.",
    "Materials inbound": "Workshop packs purchased; inbound to warehouse.",
    "In progress": "Workshop approved; event steps still open.",
    "Assessed": "Workshop feasibility calculated; awaiting approval.",
    "Closed": "Detective case closed; counts agree.",
    "Corrected": "Detective correction applied; unresolved units may remain.",
    "Investigating": "Detective facts recorded; inventory unchanged until correction.",
}

# Industry-style availability labels → (tone, tooltip).
STOCK_CONDITION = {
    "Available": (
        "done",
        "Available — promiseable units on hand (some may also be held as damaged/returns/display).",
    ),
    "Incoming": (
        "progress",
        "Incoming — purchased or transferring in; not yet available to sell.",
    ),
    "Unavailable": (
        "waiting",
        "Unavailable — on hand only as damaged, returns, or display; nothing promiseable.",
    ),
    "In transit": (
        "progress",
        "In transit — units moving between locations; nothing promiseable yet.",
    ),
    "Out of stock": (
        "decision",
        "Out of stock — no available units and nothing incoming.",
    ),
}


def _workflow_status(phase_label: str) -> tuple[str, str, str]:
    """Return (pill label, tone class, tooltip) from an internal phase label."""
    label = str(phase_label or "On shelf")
    shared = WORKFLOW_FROM_LABEL.get(label, "Idle")
    tone = WORKFLOW_TONE.get(shared, "idle")
    pill = WORKFLOW_PILL.get(shared, shared)
    detail = WORKFLOW_DETAIL_HELP.get(label, WORKFLOW_HELP[shared])
    tip = "{0} — {1}".format(WORKFLOW_HELP[shared], detail)
    return pill, tone, tip


def _stock_condition(totals: dict) -> tuple[str, str, str]:
    """Derive compact stock-condition pill from quantity buckets (not workflow).

    Status describes whether you can promise stock, not whether any holds exist.
    Partial damaged/returns still show as Available when sellable units remain;
    Unavailable means on-hand only as holds (Available column is 0).
    """
    available = int(totals.get("available", totals.get("sellable", 0)) or 0)
    inbound = int(totals.get("inbound", 0) or 0)
    damaged = int(totals.get("damaged", 0) or 0)
    returns_pending = int(totals.get("returns_pending", 0) or 0)
    display_demo = int(totals.get("display_demo", 0) or 0)
    in_transfer = int(totals.get("in_transfer", 0) or 0)
    held = damaged + returns_pending + display_demo

    if inbound > 0:
        pill = "Incoming"
    elif available > 0:
        pill = "Available"
    elif held > 0:
        pill = "Unavailable"
    elif in_transfer > 0:
        pill = "In transit"
    else:
        pill = "Out of stock"
    tone, tip = STOCK_CONDITION[pill]
    return pill, tone, tip


# Stable problem labels for demo-linked SKUs (Issue column — not workflow names).
ISSUE_BY_ROLE = {
    "reorder": "Lead-time risk",
    "workshop_bom": "Event shortfall",
    "detective": "Count mismatch",
}


def _status_class_for_label(phase_label: str) -> str:
    """Keep status_class tone aligned with the Workflow pill mapping."""
    shared = WORKFLOW_FROM_LABEL.get(str(phase_label or "On shelf"), "Idle")
    return WORKFLOW_TONE.get(shared, "idle")


def _issue_link(product: dict) -> tuple[str, str, str]:
    """Return (label, href, title) for the open problem — not a workflow name."""
    href = str(product.get("href") or "")
    if not href:
        return "", "", ""
    role = str(product.get("role") or "browse")
    label = ISSUE_BY_ROLE.get(role) or product.get("link_label") or "Open issue"
    title = "Open the demo for this issue ({0})".format(label)
    return str(label), href, title


# Merchandising keys that differentiate SKUs in the Product column (not ops/SKU noise).
_PRODUCT_DIFF_KEYS = {
    "Switches": ("Switch type", "Sold as"),
    "Keycaps": ("Profile", "Material"),
    "Keyboards": ("Size", "Style"),
    "Desk mats": ("Material",),
    "Keyboard configs": (),  # Name already encodes platform/color/weight/PCB/plate.
    "Tools": ("Kind", "Sold as"),
}


def _product_diff_line(product: dict) -> str:
    """Short differentiator line under the product name — skip SKU, category, shelf status."""
    attrs = product.get("attrs") or {}
    category = str(product.get("category") or "")
    name = str(product.get("name") or "")
    name_l = name.lower()
    parts = []
    for key in _PRODUCT_DIFF_KEYS.get(category, ()):
        value = str(attrs.get(key) or "").strip()
        if not value or value == "—":
            continue
        if key == "Sold as" and value == "each":
            continue
        if key == "Kind" and value == "Counter tool":
            continue
        if value.lower() in name_l:
            continue
        parts.append(value)
    return " · ".join(parts)


def _issue_cell_html(
    product: dict,
    workflow_label: str,
    workflow_tone: str,
    workflow_help: str,
) -> str:
    """Combine workflow state + problem link into one Issue cell."""
    issue_label, issue_href, issue_title = _issue_link(product)
    pill = ""
    if workflow_label != "Idle":
        pill = (
            '<p class="status row-status {tone}" title="{help}">{label}</p>'
        ).format(
            tone=escape(workflow_tone),
            help=escape(workflow_help, quote=True),
            label=escape(workflow_label),
        )
    link = ""
    if issue_href:
        # When the workflow pill is hidden (Idle), keep phase detail on the link tooltip.
        title = issue_title
        if workflow_label == "Idle" and workflow_help:
            title = "{0}. {1}".format(issue_title, workflow_help)
        link = (
            '<a class="row-open" href="{href}" title="{title}">{label}</a>'
        ).format(
            href=escape(issue_href),
            title=escape(title, quote=True),
            label=escape(issue_label),
        )
    if not pill and not link:
        return '<span class="muted-zero" title="{0}">—</span>'.format(
            escape(workflow_help, quote=True)
        )
    return '<div class="issue-cell">{0}{1}</div>'.format(pill, link)


def _sort_th(
    label: str,
    key: str,
    *,
    classes: str = "",
    title: str = "",
    sort_type: str = "string",
) -> str:
    """Clickable column header for client-side catalog sorting."""
    return (
        '<th class="{classes}" scope="col" title="{title}" aria-sort="none">'
        '<button type="button" class="sort-btn" data-sort="{key}" data-type="{stype}">'
        "{label}</button></th>"
    ).format(
        classes=escape(classes),
        title=escape(title, quote=True),
        key=escape(key, quote=True),
        stype=escape(sort_type, quote=True),
        label=escape(label),
    )


# Desktop Category labels (also used as the Category sort key).
CATEGORY_SHORT = {
    "Switches": "Switches",
    "Keycaps": "Keycaps",
    "Keyboards": "Keyboards",
    "Desk mats": "Desk mats",
    "Keyboard configs": "Configs",
    "Tools": "Tools",
}

# Status severity: lower = more urgent (first click ascending).
STATUS_SEVERITY_RANK = {
    "Out of stock": 0,
    "Unavailable": 1,
    "Incoming": 2,
    "In transit": 3,
    "Available": 4,
}

# Issue column: demo problems follow sidebar tab order (Reorder → Workshop → Detective).
# Rows without an issue fall back to workflow attention order after those.
ISSUE_SIDEBAR_RANK = {
    "Lead-time risk": 0,  # Reorder
    "Event shortfall": 1,  # Workshop feasibility
    "Count mismatch": 2,  # Inventory Detective
}
ISSUE_WORKFLOW_RANK = {
    "Decide": 10,
    "Waiting": 11,
    "Active": 12,
    "Done": 13,
    "Idle": 14,
}


def _issue_sort_rank(issue_label: str, workflow_label: str) -> int:
    if issue_label in ISSUE_SIDEBAR_RANK:
        return ISSUE_SIDEBAR_RANK[issue_label]
    return ISSUE_WORKFLOW_RANK.get(workflow_label, 15)


def _stock_location(
    name: str,
    *,
    available: int,
    reserved: int = 0,
    inbound: int = 0,
    damaged: int = 0,
    returns_pending: int = 0,
    in_transfer: int = 0,
    display_demo: int = 0,
) -> dict:
    """One location row. available is promiseable stock (alias: sellable)."""
    return {
        "name": name,
        "sellable": int(available),
        "available": int(available),
        "reserved": int(reserved),
        "inbound": int(inbound),
        "damaged": int(damaged),
        "returns_pending": int(returns_pending),
        "in_transfer": int(in_transfer),
        "display_demo": int(display_demo),
    }


def _stock_totals(locations: list, *, last_counted: str = "") -> dict:
    available = sum(int(row.get("available", row.get("sellable", 0))) for row in locations)
    reserved = sum(int(row.get("reserved", 0)) for row in locations)
    inbound = sum(int(row.get("inbound", 0)) for row in locations)
    damaged = sum(int(row.get("damaged", 0)) for row in locations)
    returns_pending = sum(int(row.get("returns_pending", 0)) for row in locations)
    in_transfer = sum(int(row.get("in_transfer", 0)) for row in locations)
    display_demo = sum(int(row.get("display_demo", 0)) for row in locations)
    return {
        "sellable": available,
        "available": available,
        "reserved": reserved,
        "inbound": inbound,
        "damaged": damaged,
        "returns_pending": returns_pending,
        "in_transfer": in_transfer,
        "display_demo": display_demo,
        "on_hand": (
            available
            + reserved
            + damaged
            + returns_pending
            + display_demo
        ),
        "last_counted": last_counted,
    }


def inventory_page(snapshot: dict) -> str:
    """Multi-location catalog table. Sandbox = small tour set; owner = dense seeded shop."""
    mode = snapshot.get("mode") or INVENTORY_MODE_SANDBOX
    products = _sorted_catalog(snapshot["products"])
    movements = snapshot["movements"]
    total_available = sum(item["totals"].get("available", item["totals"]["sellable"]) for item in products)
    total_inbound = sum(item["totals"]["inbound"] for item in products)
    total_unsellable = sum(
        item["totals"].get("damaged", 0)
        + item["totals"].get("returns_pending", 0)
        + item["totals"].get("display_demo", 0)
        for item in products
    )
    total_transfer = sum(item["totals"].get("in_transfer", 0) for item in products)
    attention = sum(1 for item in products if _product_needs_attention(item))
    if mode == INVENTORY_MODE_OWNER:
        lede = (
            "Specialty-shop catalog positions first, then availability and open work. "
            "Expand a product for pricing, attributes, and location split."
        )
        catalog_note = (
            "Fictional specialty-shop assortment (~492 SKUs) for the practice-owner app. "
        )
    else:
        lede = (
            "Demo-tour catalog — focal reorder SKU, workshop/detective lines, and a few sample rows. "
            "Expand a product for pricing, attributes, and location split. "
            "The dense specialty-shop assortment belongs on the practice-owner surface after login."
        )
        catalog_note = (
            "Small demo catalog for the public tour (not a live shop assortment). "
        )
    body = [
        "<h1>Inventory</h1>",
        '<p class="lede">{0}</p>'.format(lede),
        '<p class="note">{0}'.format(catalog_note)
        + "<strong>Available</strong> can sell; <strong>Reserved</strong> is committed "
        "(hover a number for why — web/counter hold, deposit, workshop, etc.); "
        "<strong>Incoming</strong> / <strong>In transit</strong> are not sellable yet; "
        "Dashes mean none for that bucket. "
        "<strong>Unavailable</strong> status means nothing promiseable (holds only); "
        "the Unavailable column expands damaged, returns, and display. "
        "<strong>Status</strong> summarizes availability; <strong>Issue</strong> is workflow state "
        "plus the open problem link when a demo is attached. Click a column header to sort.</p>",
        '<p class="counts">'
        "<span>SKUs<strong>{skus}</strong></span>"
        "<span>available<strong>{available}</strong></span>"
        "<span>incoming<strong>{inbound}</strong></span>"
        "<span>in transit<strong>{transfer}</strong></span>"
        "<span>unavailable<strong>{unsellable}</strong></span>"
        '<a class="count-link" href="{brief_attention}" '
        'title="Open daily brief — owner attention for today">'
        "needs attention<strong>{attention}</strong></a>"
        "</p>".format(
            skus=len(products),
            available=total_available,
            inbound=total_inbound,
            transfer=total_transfer,
            unsellable=total_unsellable,
            attention=attention,
            brief_attention=escape(sandbox_href() + "#inventory-attention"),
        ),
        '<p class="note" id="attention-filter-note" hidden>'
        '<strong>Showing lines that need attention.</strong> '
        '<a href="{all_skus}">Show all SKUs</a> · '
        '<a href="{brief_attention}">Back to daily brief</a></p>'.format(
            all_skus=escape(sandbox_href("inventory")),
            brief_attention=escape(sandbox_href() + "#inventory-attention"),
        ),
        '<div class="catalog-toolbar">'
        '<label for="inventory-filter">Filter catalog'
        '<input id="inventory-filter" type="search" name="q" autocomplete="off" '
        'placeholder="Search name, Item ID, SKU, barcode, category, or status" '
        'aria-controls="inventory-catalog"></label>'
        '<p class="note" id="inventory-filter-count">{count} showing</p></div>'.format(
            count=len(products)
        ),
        '<p class="note catalog-mobile-hint">Phone view: Product, Status, Available, Issue. '
        "Open Details for Item ID, SKU, barcode, pricing, and locations.</p>",
        '<div class="catalog-wrap"><table class="catalog-table" id="inventory-catalog">'
        "<thead><tr>",
        _sort_th(
            "Product",
            "product",
            classes="col-product",
            title="Product name and differentiators",
        ),
        _sort_th(
            "Item ID",
            "itemid",
            classes="col-more col-itemid",
            title="Internal item id (always present)",
        ),
        _sort_th(
            "Category",
            "category",
            classes="col-more col-category",
            title="Catalog category",
        ),
        _sort_th(
            "Status",
            "status",
            classes="col-key",
            title="Availability summary from quantity positions",
            sort_type="number",
        ),
        _sort_th(
            "Available",
            "available",
            classes="num col-key",
            title="Promiseable units you can sell",
            sort_type="number",
        ),
        _sort_th(
            "Reserved",
            "reserved",
            classes="num col-more",
            title="Committed to an order or hold — hover a value for the reason; — means none",
            sort_type="number",
        ),
        _sort_th(
            "Incoming",
            "incoming",
            classes="num col-more",
            title="Purchased or inbound, not yet available",
            sort_type="number",
        ),
        _sort_th(
            "In transit",
            "transfer",
            classes="num col-more",
            title="Moving between locations",
            sort_type="number",
        ),
        _sort_th(
            "Unavailable",
            "unavailable",
            classes="num col-more",
            title="On hand but not for sale — expand for damaged, returns, display",
            sort_type="number",
        ),
        _sort_th(
            "Last counted",
            "counted",
            classes="col-more",
            title="Last cycle-count date",
            sort_type="date",
        ),
        _sort_th(
            "Issue",
            "issue",
            classes="col-key",
            title="Workflow state and open problem (if any)",
            sort_type="number",
        ),
        "</tr></thead><tbody>",
    ]

    def _qty_cell(value, *, blank_zero=False):
        number = int(value or 0)
        if blank_zero and number == 0:
            return "—"
        return str(number)

    for product in products:
        totals = product["totals"]
        available = totals.get("available", totals.get("sellable", 0))
        reserved = totals.get("reserved", 0)
        inbound = totals.get("inbound", 0)
        damaged = totals.get("damaged", 0)
        returns_pending = totals.get("returns_pending", 0)
        in_transfer = totals.get("in_transfer", 0)
        display_demo = totals.get("display_demo", 0)
        last_counted = (
            totals.get("last_counted")
            or product.get("last_counted")
            or "—"
        )
        inbound_class = " num inbound-hot" if inbound else " num"
        unavail_total = int(damaged) + int(returns_pending) + int(display_demo)
        transfer_hot = bool(in_transfer)
        transfer_class = " num inbound-hot" if transfer_hot else " num muted-zero"
        unavail_class = "hold-hot" if unavail_total else "muted-zero"
        stock_label, stock_tone, stock_help = _stock_condition(totals)
        workflow_label, workflow_tone, workflow_help = _workflow_status(
            str(product.get("status_label") or "On shelf")
        )
        if unavail_total:
            unavail_cell = (
                '<details class="unavail-split">'
                '<summary class="num {cls}" title="Unavailable on hand — expand for split">'
                "{total}</summary>"
                '<dl class="unavail-parts">'
                "<div><dt>Damaged</dt><dd>{damaged}</dd></div>"
                "<div><dt>Returns pending</dt><dd>{returns}</dd></div>"
                "<div><dt>Display / demo</dt><dd>{display}</dd></div>"
                "</dl></details>"
            ).format(
                cls=unavail_class,
                total=escape(_qty_cell(unavail_total)),
                damaged=escape(_qty_cell(damaged, blank_zero=True)),
                returns=escape(_qty_cell(returns_pending, blank_zero=True)),
                display=escape(_qty_cell(display_demo, blank_zero=True)),
            )
        else:
            unavail_cell = (
                '<span class="num muted-zero" title="No unavailable units">—</span>'
            )
        attrs = product.get("attrs") or {}
        attr_search = " ".join(
            "{0} {1}".format(key, value) for key, value in attrs.items()
        )
        diff_line = _product_diff_line(product)
        issue_label, issue_href, _issue_title = _issue_link(product)
        barcode = str(product.get("barcode") or "")
        merchant_sku = str(product.get("merchant_sku") or "")
        search = "{0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} unavailable {11}".format(
            product["name"],
            product["sku"],
            merchant_sku,
            barcode,
            product.get("category", ""),
            product.get("description", ""),
            attr_search,
            diff_line,
            last_counted,
            stock_label,
            "{0} {1}".format(workflow_label, issue_label),
            unavail_total,
        ).lower()
        detail_rows = "".join(
            "<tr><td>{name}</td>"
            '<td class="num">{available}</td>'
            '<td class="num">{reserved}</td>'
            '<td class="num">{inbound}</td>'
            '<td class="num">{transfer}</td>'
            '<td class="num">{damaged}</td>'
            '<td class="num">{returns}</td>'
            '<td class="num">{display}</td></tr>'.format(
                name=escape(row["name"]),
                available=escape(_qty_cell(row.get("available", row.get("sellable", 0)))),
                reserved=escape(_qty_cell(row.get("reserved", 0), blank_zero=True)),
                inbound=escape(_qty_cell(row.get("inbound", 0), blank_zero=True)),
                transfer=escape(_qty_cell(row.get("in_transfer", 0), blank_zero=True)),
                damaged=escape(_qty_cell(row.get("damaged", 0), blank_zero=True)),
                returns=escape(_qty_cell(row.get("returns_pending", 0), blank_zero=True)),
                display=escape(_qty_cell(row.get("display_demo", 0), blank_zero=True)),
            )
            for row in product["locations"]
        )
        attr_rows = "".join(
            "<div><dt>{key}</dt><dd>{value}</dd></div>".format(
                key=escape(str(key)),
                value=escape(str(value)),
            )
            for key, value in attrs.items()
        )
        issue_cell = _issue_cell_html(
            product, workflow_label, workflow_tone, workflow_help
        )
        list_price = product.get("list_price", "—")
        cost = product.get("cost", "—")
        meta_html = ""
        if diff_line:
            meta_html = '<span class="product-meta">{0}</span>'.format(
                escape(diff_line)
            )
        category = str(product.get("category") or "")
        category_short = CATEGORY_SHORT.get(category, category)
        sort_status = STATUS_SEVERITY_RANK.get(stock_label, 9)
        sort_issue = _issue_sort_rank(issue_label, workflow_label)
        # ISO dates sort as timestamps in JS; blank / — → 0 (oldest / never counted).
        sort_counted = str(last_counted) if str(last_counted) not in ("", "—") else ""
        store_avail = 0
        warehouse_avail = 0
        for row in product.get("locations") or ():
            qty = int(row.get("available", row.get("sellable", 0)) or 0)
            if row.get("name") == "Front store":
                store_avail = qty
            elif row.get("name") == "Warehouse":
                warehouse_avail = qty
        available_tip = "Front store {0} · Warehouse {1}".format(
            store_avail, warehouse_avail
        )
        reserved_reason = str(product.get("reserved_reason") or "").strip()
        if int(reserved or 0) > 0 and reserved_reason:
            reserved_tip = "Reserved for: {0}".format(reserved_reason)
        elif int(reserved or 0) > 0:
            reserved_tip = "Reserved / committed units"
        else:
            reserved_tip = "No reserved units"
        needs_attention = "1" if _product_needs_attention(product) else "0"
        body.append(
            '<tr data-search="{search}" '
            'data-attention="{attention}" '
            'data-sort-product="{sort_product}" '
            'data-sort-itemid="{sort_itemid}" '
            'data-sort-category="{sort_category}" '
            'data-sort-status="{sort_status}" '
            'data-sort-available="{sort_available}" '
            'data-sort-reserved="{sort_reserved}" '
            'data-sort-incoming="{sort_incoming}" '
            'data-sort-transfer="{sort_transfer}" '
            'data-sort-unavailable="{sort_unavailable}" '
            'data-sort-counted="{sort_counted}" '
            'data-sort-issue="{sort_issue}">'
            '<td class="col-product">'
            '<span class="product-name">{name}</span>'
            "{meta}"
            "<details><summary>Details</summary>"
            '<div class="product-detail">'
            '<dl class="product-prices">'
            "<div><dt>Item ID</dt><dd>{sku}</dd></div>"
            "<div><dt>SKU</dt><dd>{merchant_sku}</dd></div>"
            "<div><dt>Barcode</dt><dd>{barcode}</dd></div>"
            "<div><dt>Category</dt><dd>{category}</dd></div>"
            "<div><dt>List price</dt><dd>${list_price}</dd></div>"
            "<div><dt>Unit cost</dt><dd>${cost}</dd></div>"
            "<div><dt>Unit of measure</dt><dd>{unit}</dd></div>"
            "<div><dt>Last counted</dt><dd>{last_counted}</dd></div>"
            "</dl>"
            '<dl class="product-attrs">{attr_rows}</dl>'
            "<p class=\"product-desc\">{description}</p>"
            "<p>{note}</p>"
            '<table class="stock-table"><thead><tr>'
            '<th scope="col">Location</th>'
            '<th class="num" scope="col">Available</th>'
            '<th class="num" scope="col">Reserved</th>'
            '<th class="num" scope="col">Incoming</th>'
            '<th class="num" scope="col">In transit</th>'
            '<th class="num" scope="col">Damaged</th>'
            '<th class="num" scope="col">Returns</th>'
            '<th class="num" scope="col">Display</th>'
            "</tr></thead><tbody>{detail}</tbody></table>"
            "</div></details></td>"
            '<td class="col-more col-itemid">{sku}</td>'
            '<td class="col-more col-category" title="{category_full}">{category_short}</td>'
            '<td class="col-key">'
            '<p class="status row-status {stock_tone}" title="{stock_help}">{stock_label}</p>'
            "</td>"
            '<td class="num col-key" title="{available_tip}">{available}</td>'
            '<td class="num col-more" title="{reserved_tip}">{reserved}</td>'
            '<td class="{inbound_class} col-more">{inbound}</td>'
            '<td class="{transfer_class} col-more">{transfer}</td>'
            '<td class="num col-more unavail-cell">{unavail_cell}</td>'
            '<td class="date col-more">{last_counted}</td>'
            '<td class="col-key issue-col">{issue_cell}</td></tr>'.format(
                search=escape(search, quote=True),
                attention=needs_attention,
                sort_product=escape(str(product["name"]).lower(), quote=True),
                sort_itemid=escape(str(product["sku"]).lower(), quote=True),
                sort_category=escape(category_short.lower(), quote=True),
                sort_status=escape(str(sort_status), quote=True),
                sort_available=escape(str(int(available or 0)), quote=True),
                sort_reserved=escape(str(int(reserved or 0)), quote=True),
                sort_incoming=escape(str(int(inbound or 0)), quote=True),
                sort_transfer=escape(str(int(in_transfer or 0)), quote=True),
                sort_unavailable=escape(str(unavail_total), quote=True),
                sort_counted=escape(sort_counted, quote=True),
                sort_issue=escape(str(sort_issue), quote=True),
                name=escape(product["name"]),
                meta=meta_html,
                detail=detail_rows,
                attr_rows=attr_rows,
                note=escape(product["note"]),
                cost=escape(str(cost)),
                description=escape(product.get("description", "")),
                unit=escape(str(product.get("unit", "—"))),
                category=escape(category),
                category_short=escape(category_short),
                category_full=escape(category, quote=True),
                sku=escape(product["sku"]),
                merchant_sku=escape(merchant_sku or "—"),
                barcode=escape(barcode or "—"),
                list_price=escape(str(list_price)),
                available=escape(_qty_cell(available)),
                available_tip=escape(available_tip, quote=True),
                reserved=escape(_qty_cell(reserved, blank_zero=True)),
                reserved_tip=escape(reserved_tip, quote=True),
                inbound_class=inbound_class,
                transfer_class=transfer_class,
                inbound=escape(_qty_cell(inbound, blank_zero=True)),
                transfer=escape(_qty_cell(in_transfer, blank_zero=True)),
                unavail_cell=unavail_cell,
                last_counted=escape(str(last_counted)),
                stock_tone=escape(stock_tone),
                stock_label=escape(stock_label),
                stock_help=escape(stock_help, quote=True),
                issue_cell=issue_cell,
            )
        )
    body.append(
        "</tbody></table>"
        '<p class="catalog-empty" id="inventory-empty" hidden>No SKUs match that filter.</p>'
        "</div>"
    )
    body.append("<h2>Stock movements</h2>")
    if not movements:
        body.append(
            '<p class="note">No stock movements yet. Approve and receive a reorder to see Front store sellable update.</p>'
        )
    else:
        body.append('<details open><summary>Recent movements ({0})</summary><ul class="activity">'.format(len(movements)))
        for item in movements[:50]:
            sign = "+" if item["delta"] > 0 else ""
            body.append(
                "<li><strong>{sign}{delta}</strong> {sku} at {location} · {reason} · {when}</li>".format(
                    sign=sign,
                    delta=escape(str(item["delta"])),
                    sku=escape(item["sku"]),
                    location=escape(item.get("location", "Front store")),
                    reason=escape(item["reason"]),
                    when=escape(item["created_at"]),
                )
            )
        if len(movements) > 50:
            body.append("<li>Showing the 50 most recent movements.</li>")
        body.append("</ul></details>")
    body.append(_INVENTORY_CATALOG_SCRIPT)
    return shell("Inventory", "".join(body))


_INVENTORY_CATALOG_SCRIPT = """
<script>
(function () {
  var input = document.getElementById("inventory-filter");
  var table = document.getElementById("inventory-catalog");
  var count = document.getElementById("inventory-filter-count");
  var empty = document.getElementById("inventory-empty");
  var attentionNote = document.getElementById("attention-filter-note");
  if (!table || !table.tBodies || !table.tBodies[0]) return;
  // Only catalog rows — not nested location rows inside Details.
  var tbody = table.tBodies[0];
  var rows = Array.prototype.slice.call(tbody.rows);
  var sortKey = null;
  var sortDir = 1;
  var params = new URLSearchParams(window.location.search || "");
  var attentionOnly = params.get("view") === "attention";
  var qParam = params.get("q") || "";
  if (attentionNote) attentionNote.hidden = !attentionOnly;
  if (input && qParam) input.value = qParam;

  function applyFilter() {
    var q = input ? (input.value || "").trim().toLowerCase() : "";
    var shown = 0;
    rows.forEach(function (row) {
      var hay = row.getAttribute("data-search") || "";
      var match = !q || hay.indexOf(q) !== -1;
      if (attentionOnly && row.getAttribute("data-attention") !== "1") match = false;
      row.classList.toggle("is-hidden", !match);
      row.classList.remove("catalog-focus");
      if (match) shown += 1;
    });
    if (count) count.textContent = shown + " showing";
    if (empty) {
      empty.hidden = shown !== 0;
      empty.classList.toggle("is-visible", shown === 0);
    }
  }

  function valueFor(row, key, type) {
    var raw = row.getAttribute("data-sort-" + key);
    if (raw == null) raw = "";
    if (type === "number") {
      var n = parseFloat(raw);
      return isNaN(n) ? 0 : n;
    }
    if (type === "date") {
      var text = String(raw).trim();
      if (!text || text === "—" || text === "-") return 0;
      var t = Date.parse(text);
      return isNaN(t) ? 0 : t;
    }
    return String(raw).toLowerCase();
  }

  function applySort(key, type, button) {
    if (sortKey === key) {
      sortDir = -sortDir;
    } else {
      sortKey = key;
      sortDir = 1;
    }
    rows.sort(function (a, b) {
      var av = valueFor(a, key, type);
      var bv = valueFor(b, key, type);
      var cmp = 0;
      if (type === "number") {
        cmp = av === bv ? 0 : (av < bv ? -1 : 1);
      } else {
        cmp = av < bv ? -1 : (av > bv ? 1 : 0);
      }
      if (cmp === 0) {
        var ap = valueFor(a, "product", "string");
        var bp = valueFor(b, "product", "string");
        cmp = ap < bp ? -1 : (ap > bp ? 1 : 0);
      }
      return cmp * sortDir;
    });
    rows.forEach(function (row) { tbody.appendChild(row); });
    Array.prototype.forEach.call(table.querySelectorAll("thead th"), function (th) {
      th.setAttribute("aria-sort", "none");
    });
    Array.prototype.forEach.call(table.querySelectorAll(".sort-btn"), function (btn) {
      btn.removeAttribute("data-dir");
    });
    if (button && button.parentElement) {
      button.parentElement.setAttribute(
        "aria-sort",
        sortDir === 1 ? "ascending" : "descending"
      );
      button.setAttribute("data-dir", sortDir === 1 ? "asc" : "desc");
    }
  }

  if (input) input.addEventListener("input", applyFilter);
  Array.prototype.forEach.call(table.querySelectorAll(".sort-btn"), function (btn) {
    btn.addEventListener("click", function () {
      applySort(
        btn.getAttribute("data-sort") || "product",
        btn.getAttribute("data-type") || "string",
        btn
      );
    });
  });
  applyFilter();
  if (qParam) {
    var focusRow = rows.find(function (row) {
      return !row.classList.contains("is-hidden");
    });
    if (focusRow) {
      focusRow.classList.add("catalog-focus");
      if (focusRow.scrollIntoView) focusRow.scrollIntoView({ block: "nearest" });
    }
  }
})();
</script>
"""


def _location_qty(product: dict, location_name: str) -> int:
    for row in product.get("locations") or ():
        if row.get("name") == location_name:
            return int(row.get("sellable") or 0)
    return 0


def _sorted_catalog(products: list) -> list:
    """Attention first: inbound/workflow, then stock condition, then identity."""
    stock_rank = {
        "Out of stock": 0,
        "Incoming": 1,
        "Unavailable": 2,
        "In transit": 3,
        "Available": 4,
    }
    workflow_rank = {
        "Decide": 0,
        "Waiting": 1,
        "Active": 2,
        "Done": 3,
        "Idle": 4,
    }
    role_rank = {"reorder": 0, "workshop_bom": 1, "detective": 2, "browse": 3}

    def sort_key(item: dict):
        totals = item.get("totals") or {}
        stock_label, _, _ = _stock_condition(totals)
        workflow_label, _, _ = _workflow_status(str(item.get("status_label") or ""))
        return (
            workflow_rank.get(workflow_label, 9),
            stock_rank.get(stock_label, 9),
            0 if totals.get("inbound", 0) else 1,
            role_rank.get(item.get("role"), 9),
            str(item.get("category", "")).lower(),
            str(item.get("name", "")).lower(),
        )

    return sorted(products, key=sort_key)


def _product_card(
    *,
    name: str,
    sku: str,
    unit: str,
    icon: str,
    locations: list,
    status_label: str,
    status_class: str,
    note: str,
    href: str,
    link_label: str,
    category: str = "",
    list_price: str = "",
    cost: str = "",
    description: str = "",
    role: str = "browse",
    attrs: dict | None = None,
    last_counted: str = "",
    barcode: str = "",
    merchant_sku: str = "",
    reserved_reason: str = "",
) -> dict:
    return {
        "name": name,
        "sku": sku,
        "unit": unit,
        "icon": icon,
        "locations": locations,
        "totals": _stock_totals(locations, last_counted=last_counted),
        "status_label": status_label,
        "status_class": status_class,
        "note": note,
        "href": href,
        "link_label": link_label,
        "category": category,
        "list_price": list_price,
        "cost": cost,
        "description": description,
        "role": role,
        "attrs": dict(attrs or {}),
        "last_counted": last_counted,
        "barcode": barcode or "",
        "merchant_sku": merchant_sku or "",
        "reserved_reason": reserved_reason or "",
    }


def empty_inventory_snapshot(*, mode: str = INVENTORY_MODE_SANDBOX) -> dict:
    """Build a catalog snapshot. Sandbox = tour subset; owner = full seeded shop."""
    from smolstuff.fixtures import SANDBOX_CATALOG, SEEDED_CATALOG

    if mode == INVENTORY_MODE_OWNER:
        catalog = SEEDED_CATALOG
    else:
        catalog = SANDBOX_CATALOG
        mode = INVENTORY_MODE_SANDBOX

    products = []
    for item in catalog:
        damaged = int(item.get("damaged", 0))
        damaged_warehouse = int(item.get("damaged_warehouse", 0))
        returns_pending = int(item.get("returns_pending", 0))
        display_demo = int(item.get("display_demo", 0))
        in_transfer = int(item.get("in_transfer", 0))
        last_counted = str(item.get("last_counted") or "")
        # Front store: sellable + reserved + floor holds. Warehouse: bulk + PO + xfer + carton damage.
        locations = [
            _stock_location(
                "Front store",
                available=int(item["store"]),
                reserved=int(item.get("reserved_store", 0)),
                damaged=damaged,
                returns_pending=returns_pending,
                display_demo=display_demo,
            ),
            _stock_location(
                "Warehouse",
                available=int(item["warehouse"]),
                reserved=int(item.get("reserved_warehouse", 0)),
                inbound=int(item.get("inbound_warehouse", 0)),
                in_transfer=in_transfer,
                damaged=damaged_warehouse,
            ),
        ]
        if item["role"] == "reorder":
            note = (
                "Focal reorder SKU. Seeded store 21 / warehouse 0. "
                "Supplier B landed cost $1.82; list ${0}. Receipts land at Front store."
            ).format(item["list_price"])
            status_label = "Seeded"
        elif item["role"] == "workshop_bom":
            note = (
                "Workshop BOM line. Seat materials = switch 70-pack ($14) + film ($2.50) + pullers ($3.50). "
                "Reserved for the upcoming 20-seat workshop; Available is what remains uncommitted."
            )
            status_label = "BOM ready"
        elif item["role"] == "detective":
            note = (
                "Sample strips guests click during workshops. Detective demo starts at system 20 / count 16. "
                "Not the quiet linear switch."
            )
            status_label = "Not investigated"
        else:
            note = "Browse-only catalog row. Stock does not change in the current demos."
            status_label = "On shelf"
        status_class = _status_class_for_label(status_label)
        products.append(
            _product_card(
                name=item["name"],
                sku=item["sku"],
                unit=item["unit"],
                icon=item["icon"],
                locations=locations,
                status_label=status_label,
                status_class=status_class,
                note=note,
                href=item.get("href") or "",
                link_label=ISSUE_BY_ROLE.get(item["role"]) or item.get("link_label") or "",
                category=item["category"],
                list_price=item["list_price"],
                cost=item["cost"],
                description=item["description"],
                role=item["role"],
                attrs=item.get("attrs") or {},
                last_counted=last_counted,
                barcode=str(item.get("barcode") or ""),
                merchant_sku=str(item.get("merchant_sku") or ""),
                reserved_reason=str(item.get("reserved_reason") or ""),
            )
        )
    return {"products": products, "movements": [], "mode": mode}


def build_inventory_snapshot(
    path: str, session_id: str = "local", *, mode: str = INVENTORY_MODE_SANDBOX
) -> dict:
    """Assemble session-scoped multi-location catalog for the inventory tab."""
    from smolstuff.fixtures import (
        DETECTIVE_SKU,
        STORE_ON_HAND,
        WAREHOUSE_ON_HAND,
        WORKSHOP_SKU,
    )
    from smolstuff.lifecycle import WorkflowState
    from smolstuff.ops_demos import DETECTIVE_FIXTURE, ScenarioStore
    from smolstuff.workflow import WorkflowStore

    snapshot = empty_inventory_snapshot(mode=mode)
    products = {item["sku"]: item for item in snapshot["products"]}
    switch = products[WORKSHOP_SKU]
    detective_card = products[DETECTIVE_SKU]

    store = WorkflowStore(path, session_id=session_id)
    try:
        store_sellable = int(store.stock_on_hand(WORKSHOP_SKU, STORE_ON_HAND))
        movements = store.list_inventory_movements(WORKSHOP_SKU)
        workflow = store.find_by_dedup("demo-supplier-lead-time-35")
        progress = None
        if workflow is not None and workflow.action_id is not None:
            progress = store.progress(workflow.workflow_id, STORE_ON_HAND)
        inbound = 0
        if progress is not None and progress.unresolved_quantity > 0:
            inbound = progress.unresolved_quantity
        prior_store = switch["locations"][0] if switch.get("locations") else {}
        prior_wh = switch["locations"][1] if len(switch.get("locations") or []) > 1 else {}
        switch["locations"] = [
            _stock_location(
                "Front store",
                available=store_sellable,
                reserved=int(prior_store.get("reserved", 0)),
                inbound=inbound,
                damaged=int(prior_store.get("damaged", 0)),
                returns_pending=int(prior_store.get("returns_pending", 0)),
                display_demo=int(prior_store.get("display_demo", 0)),
            ),
            _stock_location(
                "Warehouse",
                available=int(WAREHOUSE_ON_HAND),
                reserved=int(prior_wh.get("reserved", 0)),
                inbound=int(prior_wh.get("inbound", 0)),
                damaged=int(prior_wh.get("damaged", 0)),
                returns_pending=int(prior_wh.get("returns_pending", 0)),
                in_transfer=int(prior_wh.get("in_transfer", 0)),
                display_demo=int(prior_wh.get("display_demo", 0)),
            ),
        ]
        switch["totals"] = _stock_totals(
            switch["locations"],
            last_counted=str(switch.get("last_counted") or ""),
        )
        snapshot["movements"] = [
            {
                "sku": item.sku,
                "delta": item.delta,
                "reason": item.reason,
                "created_at": item.created_at,
                "location": "Front store",
            }
            for item in movements
        ]
        if workflow is None:
            pass
        elif workflow.state == WorkflowState.WAITING_FOR_APPROVAL:
            switch["status_label"] = "Decision needed"
            switch["status_class"] = _status_class_for_label("Decision needed")
            switch["note"] = (
                "Reorder waiting for approval. Front store still {0}; warehouse {1}; no inbound yet."
            ).format(store_sellable, int(WAREHOUSE_ON_HAND))
        elif workflow.state == WorkflowState.APPROVED:
            switch["status_label"] = "Approved"
            switch["status_class"] = _status_class_for_label("Approved")
            switch["note"] = (
                "Spend authorized. Submit the simulated order next. Front store still {0}; no inbound yet."
            ).format(store_sellable)
        elif workflow.state in (
            WorkflowState.EXECUTING,
            WorkflowState.AWAITING_RECEIPT,
            WorkflowState.RECONCILING,
        ):
            switch["status_label"] = "Awaiting receipt"
            switch["status_class"] = _status_class_for_label("Awaiting receipt")
            switch["note"] = (
                "Confirmed order shows as Incoming until receipt. Available stays {0} at Front store until units arrive."
            ).format(store_sellable)
        elif workflow.state == WorkflowState.COMPLETED:
            switch["status_label"] = "Updated"
            switch["status_class"] = _status_class_for_label("Updated")
            switch["note"] = (
                "Full receipt reconciled at Front store. Available moved from {0} to {1}. Warehouse still {2}."
            ).format(int(STORE_ON_HAND), store_sellable, int(WAREHOUSE_ON_HAND))
        elif workflow.state == WorkflowState.DECLINED:
            switch["status_label"] = "Unchanged"
            switch["status_class"] = _status_class_for_label("Unchanged")
            switch["note"] = "Purchase declined. Store and warehouse quantities are unchanged."
        elif store_sellable != int(STORE_ON_HAND):
            switch["status_label"] = "Partially updated"
            switch["status_class"] = _status_class_for_label("Partially updated")
            switch["note"] = (
                "Partial receipts updated Front store available to {0}. Incoming still {1}."
            ).format(store_sellable, inbound)
    finally:
        store.close()

    scenarios = ScenarioStore(path, session_id)
    try:
        workshop = scenarios.get("workshop")
        detective = scenarios.get("detective")
    finally:
        scenarios.close()

    if workshop and workshop.get("bom"):
        phase = workshop.get("phase", "")
        for line in workshop["bom"]:
            card = products.get(line["sku"])
            if card is None:
                continue
            store_qty = int(line.get("store", 0))
            warehouse_qty = int(line.get("warehouse", 0))
            buy = int(line.get("purchase", 0) or 0)
            inbound = 0
            if phase in ("approved", "materials_in") and line.get("bottleneck"):
                inbound = buy
            if phase == "completed":
                after = int(line.get("after_units", store_qty + warehouse_qty))
                # Show remaining on Front store after reconcile.
                store_qty, warehouse_qty, inbound = after, 0, 0
                card["status_label"] = "Reconciled"
                card["status_class"] = _status_class_for_label("Reconciled")
                card["note"] = (
                    "Workshop BOM consumed. {0} units remain after the event."
                ).format(after)
            elif phase == "materials_in" and line.get("bottleneck"):
                card["status_label"] = "Materials inbound"
                card["status_class"] = _status_class_for_label("Materials inbound")
                card["note"] = (
                    "Bottleneck packs: +{0} Incoming at warehouse until the event completes."
                ).format(buy)
            elif phase in ("approved", "assessed") or workshop.get("verdict"):
                card["status_label"] = "In progress" if phase == "approved" else "Assessed"
                card["status_class"] = _status_class_for_label(card["status_label"])
                card["note"] = (
                    "BOM line reserved for the workshop demo. On hand {0}; Incoming {1}."
                ).format(store_qty + warehouse_qty, inbound)
            prior = card.get("locations") or []
            store_hold = prior[0] if prior else {}
            warehouse_hold = prior[1] if len(prior) > 1 else {}
            card["locations"] = [
                _stock_location(
                    "Front store",
                    available=store_qty,
                    reserved=int(store_hold.get("reserved", 0)),
                    damaged=int(store_hold.get("damaged", 0)),
                    returns_pending=int(store_hold.get("returns_pending", 0)),
                    display_demo=int(store_hold.get("display_demo", 0)),
                ),
                _stock_location(
                    "Warehouse",
                    available=warehouse_qty,
                    reserved=int(warehouse_hold.get("reserved", 0)),
                    inbound=inbound,
                    damaged=int(warehouse_hold.get("damaged", 0)),
                    returns_pending=int(warehouse_hold.get("returns_pending", 0)),
                    in_transfer=int(warehouse_hold.get("in_transfer", 0)),
                    display_demo=int(warehouse_hold.get("display_demo", 0)),
                ),
            ]
            card["totals"] = _stock_totals(
                card["locations"],
                last_counted=str(card.get("last_counted") or ""),
            )

    if detective and detective.get("phase"):
        system = int(detective.get("system_inventory", DETECTIVE_FIXTURE["system_inventory"]))
        prior = detective_card.get("locations") or []
        store_hold = prior[0] if prior else {}
        warehouse_hold = prior[1] if len(prior) > 1 else {}
        detective_card["locations"] = [
            _stock_location(
                "Front store",
                available=system,
                reserved=int(store_hold.get("reserved", 0)),
                damaged=int(store_hold.get("damaged", 0)),
                returns_pending=int(store_hold.get("returns_pending", 0)),
                display_demo=int(store_hold.get("display_demo", 0)),
            ),
            _stock_location(
                "Warehouse",
                available=0,
                reserved=int(warehouse_hold.get("reserved", 0)),
                inbound=int(warehouse_hold.get("inbound", 0)),
                in_transfer=int(warehouse_hold.get("in_transfer", 0)),
            ),
        ]
        detective_card["totals"] = _stock_totals(
            detective_card["locations"],
            last_counted=str(detective_card.get("last_counted") or ""),
        )
        if detective.get("closed"):
            detective_card["status_label"] = "Closed"
            detective_card["status_class"] = _status_class_for_label("Closed")
            detective_card["note"] = "Discrepancy closed. Front store system inventory is {0}.".format(
                system
            )
        elif detective.get("corrected"):
            detective_card["status_label"] = "Corrected"
            detective_card["status_class"] = _status_class_for_label("Corrected")
            detective_card["note"] = (
                "Approved correction applied at Front store. System inventory {0}. Unresolved: {1}."
            ).format(system, detective.get("unresolved", 0))
        else:
            detective_card["status_label"] = "Investigating"
            detective_card["status_class"] = _status_class_for_label("Investigating")
            detective_card["note"] = (
                "Facts recorded. Front store system inventory is still {0} until an approved correction."
            ).format(system)
    return snapshot



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
                    "Event completed once. BOM consumed. Complete seats left {0}.".format(updated["inventory_after"])
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
        '<form method="post" action="{0}"><input type="hidden" name="scenario" value="reorder">'
        '<input type="hidden" name="action" value="simulate_email">'
        '<button class="primary" type="submit">Start interactive demo</button></form>'
    ).format(SANDBOX_PREFIX)


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
        {
            "title": "Reorder the quiet linear switches",
            "description": "A supplier delay puts stock at risk. Approve one practice order, then receive it so available inventory updates.",
            "href": sandbox_href("reorder"),
            "status": reorder_status,
            "bucket": reorder_bucket,
            "action": reorder_action,
        },
        _card(
            "Can we take this workshop?",
            "A customer asks for a 20-person build night. Check seats, cash, and timing before you promise.",
            sandbox_href("workshop"),
            workshop,
            "Not checked",
        ),
        _card(
            "Where did the sample strips go?",
            "System says 20; the count says 16. Investigate without inventing a cause.",
            sandbox_href("detective"),
            detective,
            "Not investigated",
        ),
        _card(
            "Save today’s walk-in sale",
            "A customer needs a part you don’t have. See if practice neighbor shops can help.",
            sandbox_href("rescue"),
            rescue,
            "Not requested",
        ),
        _card(
            "How much coverage do we need?",
            "Estimate Saturday hours (with or without a workshop). This does not schedule people.",
            sandbox_href("staffing"),
            staffing,
            "Not calculated",
        ),
    ]


def _card(title: str, description: str, href: str, saved: Optional[dict], empty_status: str) -> dict:
    if saved is None:
        return {"title": title, "description": description, "href": href, "status": empty_status, "bucket": "Not started"}
    phase = saved.get("phase", "")
    if phase == "completed" and "contribution" in saved:
        bucket = "Completed"
        status = "Completed. Contribution ${0}. {1} seats of materials left.".format(
            saved["contribution"], saved.get("inventory_after", "")
        )
    elif phase == "completed" or saved.get("closed") or saved.get("saved"):
        bucket = "Completed"
        status = "Completed"
    elif phase in ("assessed", "investigated", "quoted", "negotiated", "calculated"):
        bucket = "Needs your decision"
        status = {
            "assessed": "Ready to decide",
            "investigated": "Needs evidence",
            "quoted": "Offers ready",
            "negotiated": "Offers ready",
            "calculated": "Coverage calculated",
        }.get(phase, "Needs a decision")
    else:
        bucket = "In progress"
        status = {
            "approved": "Commitment approved",
            "materials_in": "Materials inbound",
            "authorized": "Fulfillment authorized",
            "transferred": "Transfer simulated",
            "corrected": "Correction applied",
        }.get(phase, phase.replace("_", " ").capitalize() or "In progress")
    return {"title": title, "description": description, "href": href, "status": status, "bucket": bucket}
