# smolstuff

**An operations team for small businesses. From incoming signal to verified resolution.**

smolstuff is a privacy-first AI operations system for small local businesses. The vision is automatic permitted-email triage, actionable work, inventory investigation and supplier-aware reordering, staffing-light-day recommendations, and sale rescue through nearby merchants’ agents. Owners set the boundaries once; sensitive commitments wait for approval. The current app demonstrates these operations with synthetic scenarios; it does not connect a real inbox or merchant network.

> **Automate the work, not the authority.**

This README describes what the code does now. Requirements, fixtures, scope, and engineering rules are linked under Documents. [The implementation contract](docs/IMPLEMENTATION_CONTRACT.md) record technical behavior and remaining requirements. [Current synchronization review](docs/STATUS.md) supersedes [the historical review](docs/REVIEW.md). [Design specification](docs/DESIGN.md) defines the shared dark UI.

## What runs today

A dark, responsive Daily brief with one simulated procurement workflow and four separate functional previews. All screens share the smolstuff navigation, typography, controls, evidence styles, and synthetic-data notice. No fake live monitoring or business-impact metrics are displayed.

| Step | Behavior |
| --- | --- |
| Supplier email | **Start interactive demo** simulates a permitted Supplier A message: lead time increased from 14 days to about 35 days. Each visitor gets a separate session. This is a demonstration trigger, not a live mailbox subscription. |
| Extraction | Novita is wired. Anonymous calls stay off unless `SMOL_SPONSOR_CALLS=1` and both sponsor limits are set. Otherwise a local parser reads the synthetic email and is labeled a fallback. It cannot change prices or the spending limit. |
| Planning | The last 10 days sold 11 units. Velocity is 1.1/day. Supply is about 19 days (21 / 1.1 ≈ 19.1). The gap is about 16 days (≈ 15.9). |
| Internal check | Warehouse stock is 0 and open purchase orders are 0, so neither covers the gap. |
| Recommendation | Order 100 units from Supplier B because that is the minimum. $54 merchandise + $7 shipping = $61. That is more than the 17.5-unit immediate shortage. It is not a forecast. |
| Approval | Purchases auto-execute only under $40. Every other configured check passes, so the limit is the only reason this order waits. |
| After approval | The saved workflow submits one simulated order and records a matching confirmation. Stock does not change. A second click does not create a second order. |
| Receipt | **Simulate receiving 100 units** adds those units to the 21 already available. On hand becomes 121. No extra sales are subtracted. The workflow completes only after that receipt. |
| Refresh | Each visitor has one SQLite file under `data/sessions/`. Reloading the page resumes that file. **Reset demo** clears the reorder workflow and its tool records. It does not delete the file, so the other previews in that session remain. This persists while the host retains its disk; the current hosting configuration does not establish durable storage across redeploys. |

Integration status: application wiring verified by this inspection; previous account/probe observations are repository-reported and were not rerun here:

| Tool | Observed status |
| --- | --- |
| Tavily | Wired. A previous local run recorded a live search. This checkout does not call Tavily unless sponsor calls are enabled, both limits are set, and a key is present. Links do not change the seeded $61 offer. |
| Novita | Wired for supplier-email extraction. Without `NOVITA_API_KEY`, the labeled parser fallback runs. |
| ZooWork | A models read and an empty agent create succeeded, and that agent was deleted. No operations task has run. |
| BAND | The user key can list owned agents. The account owns none, so no handoff has run. |
| Moss | A local Python 3.12 query of the fictional `smol-policy` index returned the $40 approval rule. The Action Inbox does not call Moss, and the evidence panel does not show that query. |
| Entire | Development provenance only. This repository is not capturing sessions. |

The public site is [https://smolstuff.vercel.app](https://smolstuff.vercel.app). A normal browser does not need a Vercel login. Hosted session files are temporary and do not survive a redeploy. Sponsor calls stay off unless `SMOL_SPONSOR_CALLS=1` and both limits are set. Those limits share one budget file on each server instance. They are not a provider-wide spend cap.

Confirmation does not complete the workflow. Completion is the reconciled receipt.

The same session can open four more synthetic workflows from the daily brief. They do not change the reorder product's 21 units.

| Workflow | What it does |
| --- | --- |
| Can we take this on? | Workshop feasibility. Default: 20 attendees, 18 kits, buy the minimum 10, contribution $700, 8 kits left. A two-day event with missing kits is blocked. |
| Where did the missing stock go? | Inventory Detective for a separate 20-unit count. It does not invent a cause. Confirming workshop use can correct 3 units and leave 1 unresolved until a matching recount. |
| Save the sale | Two merchant simulators. Default contributions are $21 and $27. A $90 selling price recommends neither. |
| Plan the right coverage | Historical averages and a 15-minute workload model. Saving a plan does not schedule a person. |

Collaboration inquiries and custom orders are not separate workflows. They would use the same feasibility engine later.

## Not running

These remain requirements or later work. They are not available in the demo:

- A hosted session that survives a redeploy
- Live mailbox, Shopify, payment, or browser-verification integrations
- A verified Novita extraction, ZooWork operations task, BAND handoff, or Moss retrieval inside the Action Inbox
- Returns, account onboarding, multiple privacy modes, and analytics dashboards

The purchase store can record a short receipt without closing the workflow. That branch is not a button on the submitted demo. The demo receipt control receives the full order.

## Stack

Python 3.9 or newer, using the standard library for the local HTTP server and SQLite. Money is `Decimal`, not floating point. Tests use pytest. Vercel is the host and Render is retired. Local sessions are still SQLite files. A separate `.venv-moss` directory can query Moss with Python 3.12. It is gitignored and is not required to run the demo.

## Run locally

```bash
git clone https://github.com/heykatie/smolstuff.git
cd smolstuff
python3 -m venv .venv
.venv/bin/python -m pip install "pytest>=8.0"
PYTHONPATH=src .venv/bin/python -m smolstuff.inbox
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). If `PORT` is set, the server binds `0.0.0.0` on that port.

1. Click **Start interactive demo**.
2. Read the card. It should show about 19 days of stock, a 35-day supplier lead time, Supplier B at $54 + $7 shipping = $61, and **Approve simulated $61 order**.
3. Click **Approve simulated $61 order** once. The page should say the order is confirmed and awaiting receipt. Available inventory stays 21.
4. Refresh the browser. The same awaiting-receipt state should still be there.
5. Click **Simulate receiving 100 units**. Available inventory becomes 121 and the workflow is complete.
6. Click **Reset demo** to run the reorder again. **Decline** submits no order. **Review evidence** opens the calculations, the seeded Supplier B offer, and the tool records.

```bash
.venv/bin/python -m pytest -q
```

## Configuration

Copy `.env.example` to `.env`. The server reads that file on startup and does not print the values. `.env` is gitignored. When a Vercel project exists, set the same names in that project's environment, not in source. Do not put secrets in source, Git, or chat.

| Name | Role |
| --- | --- |
| `NOVITA_API_KEY` | Optional supplier-email extraction. Missing key uses the labeled parser. |
| `NOVITA_MODEL` | Optional model name. |
| `TAVILY_API_KEY` | Public supplier-research links for the reorder demo. |
| `ZOOWORK_API_KEY` | Operations agent. A funded balance is required before a paid task. |
| `ZOOWORK_PROJECT_ID` | Local label. Requests use the API key’s project, not this field. |
| `MOSS_PROJECT_ID`, `MOSS_PROJECT_KEY` | Policy retrieval. Both are required. The inbox does not call Moss. |
| `BAND_USER_KEY` | Lists and can register agents. |
| `BAND_RESEARCH_AGENT_KEY`, `BAND_CLERK_AGENT_KEY` | One-time agent keys for a future handoff. Not created yet. |

## Documents

| File | Role |
| --- | --- |
| [prd.md](prd.md) | Requirements and acceptance criteria |
| [demo_spec.md](demo_spec.md) | Reorder numbers and screen copy |
| [mvp_scope.md](mvp_scope.md) | Current product boundary |
| [project_context.md](project_context.md) | Product philosophy, architecture intent, and [engineering rules](project_context.md#25-engineering-rules) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Hosting direction. A hosted session is not durable until a redeploy keeps it |

If a reorder number disagrees, `demo_spec.md` wins. If the documents disagree about what is built, this README, the code, and the tests win. If they disagree about what is required, `prd.md` wins.

## Repository

```text
smolstuff/
├── README.md
├── AGENTS.md
├── prd.md
├── mvp_scope.md
├── demo_spec.md
├── project_context.md
├── docs/
├── .env.example
├── src/smolstuff/
├── tests/
└── data/sessions/        # Created at runtime. Not committed.
```

See [development and deployment](docs/DEVELOPMENT.md), [security and pending decisions](docs/SECURITY_AND_DECISIONS.md), and [integration contracts](docs/INTEGRATIONS.md). The product name, GitHub repo, and Python package are smolstuff.

Examples use fictional businesses and synthetic numbers. Do not commit credentials or real merchant data.

## License

Licensed under the [MIT License](LICENSE).

## UI direction and review status

Modern, clean, sleek, dark, stylish and gently playful is the product design direction. Shared tokens live in `src/smolstuff/ui_theme.py`; all screen shells use them. See [docs/DESIGN.md](docs/DESIGN.md) for tokens, responsive behavior and accessibility criteria. [docs/STATUS.md](docs/STATUS.md) records what was checked and what remains open. A local preview is not a deployed site.
