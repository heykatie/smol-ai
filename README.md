# smolstuff

**An operations team for small businesses. From incoming signal to verified resolution.**

smolstuff is a privacy-first AI operations system for small local businesses. The intended product automatically triages permitted email, extracts actionable work, investigates inventory discrepancies, plans replenishment using sales velocity and supplier facts, identifies days needing less coverage, and can coordinate a sale rescue with participating merchants. Owners set access and authority once; routine analysis runs in the background and sensitive commitments wait for approval. The working demo today covers one simulated reorder loop.

> **Automate the work, not the authority.**

Read [PRD.md](PRD.md) for release requirements, [MVP_SCOPE.md](MVP_SCOPE.md) for staged scope, and [project_context.md](project_context.md) for the broader vision. [The implementation contract](docs/IMPLEMENTATION_CONTRACT.md) maps requirements to the existing code; [the review](docs/REVIEW.md) records gaps against the inspected live commit. These documents describe targets separately from current behavior.

## What runs today

One simulated procurement workflow for one fictional product, the workshop supply pack.

| Step | Behavior |
| --- | --- |
| Supplier email | **Start interactive demo** simulates a permitted Supplier A message: lead time increased from 14 days to about 35 days. Each visitor gets a separate session. This is a demonstration trigger, not a live mailbox subscription. |
| Extraction | A parser returns the configured supplier and `DEMO-SKU-001`, plus lead times 14 and 35. Other sentences cannot change policy. |
| Planning | The last 10 days sold 11 units. Velocity is 1.1/day. Supply is about 19 days (21 / 1.1 ≈ 19.1). The gap is about 16 days (≈ 15.9). |
| Internal check | Warehouse stock is 0 and open purchase orders are 0, so neither covers the gap. |
| Recommendation | Order 100 units from Supplier B because that is the minimum. $54 merchandise + $7 shipping = $61. That is more than the 17.5-unit immediate shortage. It is not a forecast. |
| Approval | Purchases auto-execute only under $40. Every other configured check passes, so the limit is the only reason this order waits. |
| After approval | The saved workflow submits one simulated order and records a matching confirmation. Stock does not change. A second click does not create a second order. |
| Receipt | **Simulate receiving 100 units** adds those units to the 21 already available. On hand becomes 121. No extra sales are subtracted. The workflow completes only after that receipt. |
| Refresh | Each visitor's workflow is a separate SQLite file under `data/sessions/`. Reloading the page resumes that session. **Reset demo** deletes only that file. This persists while the host retains its disk; the current hosting configuration does not establish durable storage across redeploys. |

Live integrations: none. Email intake, purchase submission, confirmation, and receipt run through local demo adapters. Their records are `simulated` or `replayed`. ZooWork, BAND, Moss, Tavily, Novita, and browser verification are not called. Entire is development provenance and is not part of the runtime feed.

Confirmation does not complete the workflow. Completion is the reconciled receipt.

## Planned, not built

These are not implemented at the inspected commit. The next release targets are defined in PRD.md; absence today does not remove them from the product:

- Live mailbox, Shopify, or payment integrations
- Model extraction, search, browser verification, or multi-agent coordination
- Merchant negotiation, staffing forecasts, opportunity feasibility, and returns
- Account onboarding, multiple privacy modes, and analytics dashboards

The purchase store can record a short receipt without closing the workflow. That branch is not a button on the submitted demo. The demo receipt control receives the full order.

## Demo

Requirements: Python 3.9+.

```bash
git clone https://github.com/heykatie/smolstuff.git
cd smolstuff
python3 -m venv .venv
.venv/bin/python -m pip install "pytest>=8.0"
PYTHONPATH=src .venv/bin/python -m smol_ai.inbox
```

Open http://127.0.0.1:8765

1. Click **Start interactive demo**.
2. Read the card. It should show about 19 days of stock, a 35-day supplier lead time, Supplier B at $54 + $7 shipping = $61, and **Approve simulated $61 order**.
3. Click **Approve simulated $61 order** once. The page should say the order is confirmed and awaiting receipt. Available inventory stays 21.
4. Refresh the browser. The same awaiting-receipt state should still be there.
5. Click **Simulate receiving 100 units**. Available inventory becomes 121 and the workflow is complete.
6. Click **Reset demo** to run it again. **Decline** on the approval card submits no order. **Review evidence** opens the calculations, the seeded Supplier B offer, and the tool records.

```bash
.venv/bin/python -m pytest -q
```

## Repository

```text
smolstuff/
├── README.md
├── AGENTS.md             # Cursor working instructions
├── PRD.md                # Product/release requirements
├── docs/                 # Technical contracts, security, decisions, setup, review
├── MVP_SCOPE.md          # What this hackathon build includes
├── DEMO_SPEC.md          # Numbers and copy for this demo
├── project_context.md    # Broader product vision
├── render.yaml           # Render web service settings
├── src/smol_ai/          # Python core and local inbox
├── tests/
└── data/sessions/        # Created at runtime, one SQLite file per visitor. Not committed.
```

See [development and deployment](docs/DEVELOPMENT.md), [security and pending decisions](docs/SECURITY_AND_DECISIONS.md), and [integration contracts](docs/INTEGRATIONS.md). The product name and GitHub repo are smolstuff. The existing Python import path `smol_ai`, package metadata, cookie name, and hosting service identifier remain legacy technical names pending a separate migration.

Examples use fictional businesses and synthetic numbers. Do not commit credentials or real merchant data.

## License

Licensed under the [MIT License](LICENSE).
