# smolstuff

**An operations team for small businesses. From incoming signal to verified resolution.**

smolstuff is a privacy-first AI operations system for small local businesses. The vision is automatic permitted-email triage, actionable work, inventory investigation and supplier-aware reordering, staffing-light-day recommendations, and sale rescue through nearby merchants’ agents. Owners set the boundaries once; sensitive commitments wait for approval. The current app demonstrates these operations with synthetic scenarios; it does not connect a real inbox or merchant network.

> **Automate the work, not the authority.**

This README describes what the code does now. Requirements, fixtures, scope, and engineering rules are linked under Documents. [The implementation contract](docs/IMPLEMENTATION_CONTRACT.md) records technical behavior and remaining requirements. [Current synchronization review](docs/STATUS.md) supersedes [the historical review](docs/REVIEW.md). [Design specification](docs/DESIGN.md) defines the shared dark UI.

## What runs today

A dark, responsive Daily brief with one simulated procurement workflow, four separate functional previews, and an Inventory tab that shows session stock after decisions. All screens share the smolstuff navigation, typography, controls, evidence styles, and synthetic-data notice. No fake live monitoring or business-impact metrics are displayed.

| Step | Behavior |
| --- | --- |
| Supplier email | **Start interactive demo** simulates a permitted Supplier A message: lead time increased from 14 days to about 35 days. Each visitor gets a separate session. This is a demonstration trigger, not a live mailbox subscription. |
| Extraction | Novita is wired. Anonymous calls stay off unless `SMOL_SPONSOR_CALLS=1` and both sponsor limits are set. Otherwise a local parser reads the synthetic email and is labeled a fallback. It cannot change prices or the spending limit. |
| Planning | The last 10 days sold 11 units. Velocity is 1.1/day. Supply is about 19 days (21 / 1.1 ≈ 19.1). The gap is about 16 days (≈ 15.9). |
| Internal check | Warehouse stock is 0 and open purchase orders are 0, so neither covers the gap. |
| Recommendation | Order 100 quiet linear switches from Supplier B because that is the minimum. $182 merchandise + $7 shipping = $189. That is more than the 17.5-unit immediate shortage. It is not a forecast. |
| Approval | Purchases auto-execute only under $40. Every other configured check passes, so the limit is the only reason this order waits. |
| After approval | The saved workflow submits one simulated order and records a matching confirmation. Stock does not change. A second click does not create a second order. |
| Receipt | **Simulate receiving 100 units** adds those units to the 21 already available. On hand becomes 121. No extra sales are subtracted. The workflow completes only after that receipt. |
| Refresh | Without `DATABASE_URL`, each visitor uses a SQLite file under `data/sessions/`. With it, workflow and preview rows use session-scoped Postgres. **Reset demo** clears the reorder workflow and its tool records while preserving the other previews. Commit `0847325` records one hosted approval surviving a redeploy; see [STATUS.md](docs/STATUS.md) for limits. |

Integration status: application wiring verified by this inspection; previous account/probe observations are repository-reported and were not rerun here:

| Tool | Observed status |
| --- | --- |
| Tavily | Wired. A previous local run recorded a live search. This checkout does not call Tavily unless sponsor calls are enabled, both limits are set, and a key is present. Links do not change the seeded $189 offer. |
| Novita | Wired for supplier-email extraction. Without `NOVITA_API_KEY`, the labeled parser fallback runs. |
| ZooWork | One stopped agent, `smolstuff-clerk`, is configured. It explains a case and cannot change the order. Calls stay off until launch. |
| BAND | The user key can list owned agents. The account owns none, so no handoff has run. |
| Moss | A local Python 3.12 query of the fictional `smol-policy` index returned the $40 approval rule. The Action Inbox does not call Moss, and the evidence panel does not show that query. |
| Entire | Development provenance only. This repository is not capturing sessions. |

The public site is [https://smolstuff.vercel.app](https://smolstuff.vercel.app). A normal browser does not need a Vercel login. Temporary files on Vercel are not durable. Workflow and preview rows use Postgres when `DATABASE_URL` is configured; one surviving approval is repository-recorded, not a general durability certification. Sponsor calls stay off unless `SMOL_SPONSOR_CALLS=1` and both limits are set. With `DATABASE_URL`, those call-count limits are shared in Postgres. Without it, they share one local budget file. They are not a provider-wide spend cap.

Confirmation does not complete the workflow. Completion is the reconciled receipt. The **Inventory** nav tab is a market-public keyboard-shop catalog (~492 SKUs) ordered Product → Category (desktop) → Status → Available → Reserved → Incoming → In transit → Unavailable → Last counted → Issue. Columns are sortable; the filter searches the catalog. Product shows name + differentiators; Issue combines workflow state with the problem link (Lead-time risk / Event shortfall / Count mismatch). Unavailable expands damaged + returns + display. Phone view keeps Product / Status / Available / Issue. Quiet linear switch starts at available 21 (Available + Lead-time risk); an approved order is Incoming / Waiting with inbound 100; a full receive is Available / Done at available 121. Workshop feasibility uses a per-seat **BOM** (not one sealed kit SKU). Detective tracks sample strips.

The same session can open four more synthetic workflows from the daily brief. They do not change the reorder product's 21 units.

| Workflow | What it does |
| --- | --- |
| Can we take this on? | Workshop feasibility via per-seat BOM (70-pack + film + pullers). Default: 20 attendees, 18 seats available, buy 10 bottleneck packs, contribution $700, 8 seats left. A two-day event with missing packs is blocked. |
| Where did the missing stock go? | Inventory Detective for 10-switch sample strips (system 20). It does not invent a cause. Confirming workshop use can correct 3 units and leave 1 unresolved until a matching recount. |
| Save the sale | Two merchant simulators. Default contributions are $21 and $27. A $90 selling price recommends neither. |
| Plan the right coverage | Historical averages and a 15-minute workload model. Saving a plan does not schedule a person. |

Collaboration inquiries and custom orders are not separate workflows. They would use the same feasibility engine later.

## Not running

These remain requirements or later work. They are not available in the demo:

- Broad hosted persistence/recovery verification beyond the single recorded reorder approval
- Live mailbox, Shopify, payment, or browser-verification integrations
- A verified Novita extraction, a public ZooWork task, a BAND handoff, or Moss retrieval inside the Action Inbox
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
2. Read the card. It should show about 19 days of stock, a 35-day supplier lead time, Supplier B at $182 + $7 shipping = $189, and **Approve simulated $189 order**.
3. Click **Approve simulated $189 order** once. The page should say the order is confirmed and awaiting receipt. Available inventory stays 21.
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
| [project_context.md](project_context.md) | Product philosophy, architecture intent, examples, and long-form reference |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Hosting/storage direction and the recorded single-session redeploy check |
| [docs/TARGET_STACK.md](docs/TARGET_STACK.md) | Planned Next + FastAPI + TypeScript migration (not implemented) |
| [docs/DOCUMENT_AUTHORITY.md](docs/DOCUMENT_AUTHORITY.md) | Which document owns each topic |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Future and post-MVP work, not current evidence |
| [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md) | Historical hackathon, sponsor, and demo-script context |

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
