# smolstuff implementation status and verification evidence

## Documentation/source inspection — October 4, 2026 (America/Los_Angeles)

Inspected source and tracked evidence at `7cd4647` on live main. This is a documentation/source review, not a fresh runtime, provider, dashboard, database, or deployment test. No private configuration was loaded; no permissions, budgets, connectors, or runtime behavior were changed. The earlier synchronization review below retains its recorded evidence and does not certify later commits.

| Topic | Evidence inspected in this cleanup | Limit / remaining work |
| --- | --- | --- |
| Document authority | PRD owns requirements; AGENTS owns engineering instructions; project context is supporting philosophy/architecture/examples; this file owns verification evidence | Reference material does not override governing requirements or decisions |
| Storage wiring | `database.py`, `WorkflowStore`, and `ScenarioStore` select Postgres when `DATABASE_URL` is set, otherwise SQLite. `app.py` and `inbox.py` recognize persisted Postgres sessions without a surviving local file | Source inspection does not verify current hosted configuration, every preview, or backup/restore |
| Hosted persistence | Architecture and commit `0847325` report Neon connected and the same approved reorder awaiting receipt with stock 21 after redeploy. Commit authored October 4 Pacific / October 5 UTC | Repository-recorded single-session result; not rerun here. Backup/restore, database retention/cleanup, and broader hosted recovery remain unresolved |
| Sponsor limits | `SponsorBudget.claim` requires the enable switch and two positive call limits and reserves counts atomically in local SQLite. Inbox checks this gate before Novita, Tavily, and ZooWork calls | Counters cover sessions sharing that file. They are not a shared multi-instance/redeploy cap or a monetary budget; D3 remains open |
| Provider wiring | Novita extraction, Tavily research, and ZooWork explanation are wired; ZooWork cannot set the calculated order or approval | Commit `4e704e3` reports one local explanation; no fresh provider call or hosted credential verification here. BAND and Moss remain outside the inbox |
| Tests | Inspected existing sponsor-budget, Postgres-store, WSGI, and ZooWork tests as supporting source | No tests executed for this documentation cleanup. Earlier counts below are historical reports, not current-suite results |

Documentation verification for this cleanup: 78 local Markdown link targets across 11 edited documents resolved; code fences were balanced; targeted stale-wording searches and diff whitespace checks passed. Runtime tests and hosted/provider checks were not run.

Remaining production gates include authenticated identity/roles, real connectors, exact authority and reservation semantics, approved paid-call budgets with hosted enforcement, retention/erasure and backup/restore. A single recorded redeploy check does not close those gates.

## Source-description follow-up — October 4, 2026

At source baseline `e7d65bb`, corrected storage and sponsor-limit docstrings in `app.py`, `workflow.py`, `ops_demos.py`, `inbox.py`, `sponsor_budget.py`, and `database.py`. All six edited files parsed successfully; syntax trees were identical after removing docstrings, confirming no executable code changed. Sponsor limits count task attempts; one ZooWork task can issue multiple provider requests. Diff whitespace and local Markdown links were checked. No runtime tests, paid calls, hosted state changes, or deployment were performed.

## Local regression verification — October 4, 2026 (America/Los_Angeles)

Tested source commit `d7df032` on Python 3.14.7. The existing environment ran **92 passed, 1 skipped**; the Postgres module skipped because `psycopg` was absent. Seven initial failures were sandbox restrictions on localhost socket binding, and passed with local-server access.

A separate temporary environment with pytest 9.1.1 and psycopg 3.3.6, plus an isolated local Postgres cluster, then ran the complete suite: **97 passed, no failures or skips**. Command: `python -m pytest -q -ra`, with `PGHOST`/`PGPORT` pointing only to that test cluster, `DATABASE_URL` and provider keys removed from the test environment, and `SMOL_SPONSOR_CALLS=0`. Tests use mocked provider transports and synthetic records. Coverage includes existing session-isolation, duplicate approval/receipt, workflow, sponsor-limit, WSGI, and Postgres behavior tests. The temporary database server was stopped afterward.

No application or test code changed. This verifies the existing local suite; it does not establish hosted Neon configuration, production redeploy/recovery, browser accessibility, fresh provider integration, or a shared hosted spending cap. Previous test counts remain historical below.

## Earlier synchronization review — historical evidence

The sections below describe the earlier review scope. The source/evidence table above supersedes older storage, quota, and provider-wiring statements; historical browser/test results are retained without rerunning them.

Reviewed October 4, 2026 against live main `d48c344` (the merged documentation review plus the subsequent local-demo/package update), then the dark UI synchronization branch. This file supersedes docs/REVIEW.md for the status recorded here; that first review is historical. Later commits are not re-certified by this page until a new inspection is written. Document ownership is in [DOCUMENT_AUTHORITY.md](DOCUMENT_AUTHORITY.md). Current docs use lowercase prd.md, mvp_scope.md and demo_spec.md, and the app/package/service is smolstuff.

### Vision and implementation

The vision remains an easy-to-use AI operations system for small local businesses: automatically triage permitted email without uploads, extract actionable work, investigate inventory, recommend/perform bounded reordering, identify staffing-light days, and potentially save a sale with nearby merchant agents. Privacy, least privilege, exact authority, auditability and trust are governing requirements.

The app is an interactive synthetic demonstration of that vision. It now includes the reorder lifecycle plus four persisted previews. Synchronization means documents agree about what is intended, built and verified; it does not mean real-world connectors or the whole production vision are implemented.

| Capability | Current implementation | Remaining gap |
| --- | --- | --- |
| Daily brief / Action Inbox | Persisted session counts and five discoverable scenarios, shared dark shell | Production onboarding, real background brief and authenticated owner |
| Email work | Simulated supplier arrival, optional Novita two-field extraction/parser fallback | Live provider ingestion, scoped metadata gate, categories and general task extraction |
| Replenishment | Ten-day velocity, seeded supplier terms, $189 approval, confirmation, receipt/reconciliation | Live inventory/supplier updates, timed supply and no-risk/general planner |
| Inventory Detective | Physical-count fixture, evidence confirmation, approved three-unit correction, original count/history and recount | General business investigation, input ranges and authenticated exact adjustment authority |
| Workshop | Editable attendees/deadline, deterministic materials/economics, simulated approval/receipt/completion | Distinct production purchase/customer approvals, evidence/capacity integrations, economic feasibility beyond default fixture |
| Sale rescue | Two synthetic offers, bounded counteroffer logic, contribution check, simulated authorization/transfer/fulfillment | Nearby real agents, offer expiry, reservation, disclosure, dispute and actual payment/fulfillment |
| Staffing | Weekday mean, workload hours, saved coverage plan; Tuesday owner-only/Saturday additional coverage | Production minimum coverage/work-hour constraints; no named-worker scheduling |
| Supplier research | Tavily client wired; output only affects research evidence, not seeded offer | Fresh provider verification in this review, public quotas, actual supplier validation |
| UI | Shared dark tokens/frame/navigation; lavender/mint, smile mark, responsive cards/forms/evidence/error states | Broader accessibility/user testing and hosted verification |
| Security/authority | Synthetic visitor isolation, deterministic policy, terms hash, session-scoped SQLite, request limits, and sponsor calls off by default | Authenticated roles, full material hashes, atomic spending reservations, and a hosted session that survives redeploy |

### Documentation repairs in this change

- Updated implementation contract for the actual smolstuff package, scenario store, optional model/research clients and shared UI.
- Replaced stale “no provider clients” / “previews absent” status with actual wiring, while separating old provider reports from fresh evidence.
- Corrected development settings: .env loader and ignores exist, and reorder reset preserves other previews. Render is retired. Vercel production returned the dark daily brief. Sessions on that host are temporary.
- Added docs/DESIGN.md and linked the confirmed visual direction from PRD, scope, fixture, project context, README and AGENTS.
- Retained the old review explicitly as history; all current status pointers use this file.
- Unified the formerly separate procurement/empty pages with the same dark shell.
- Added two numeric-error regression tests, observed them fail with dropped connections, then handled Decimal conversion errors as styled HTTP 400 without saving invalid scenario data.

### Evidence and limits

Source inspection verified optional Novita/Tavily wiring. The README's earlier successful Tavily, separate Moss query and account/probe reports were not rerun. Supplier offers, purchases, messages, and merchant participants remain fictional. The dark daily brief is deployed. That is not a production security certification.

The UI-sync review recorded 64 passing tests. A later repository edit reported 85 passed and 1 skipped on Python 3.9 after the public-demo fixes; this cleanup did not rerun or establish the exact commit covered by that count. The skip is the Postgres test when `psycopg` is not installed.

### Final verification for the synchronization change

- Earlier UI-sync run: **64 tests passed** on Python 3.14. The later repository-reported count is recorded above; neither count is a current-suite certification.
- Browser: completed reorder (21 unchanged at confirmation, 121 after receipt), workshop ($700/eight kits), detective (20 → 17, unresolved one → recount resolves), merchant rescue ($21/$27 offers, $27 reconciled fulfillment), and Saturday staffing (14 hours/two blocks; saved plan).
- Browser: refreshed awaiting-receipt state; all completed previews remain in session and Daily brief counts show five completed cases. Evidence correctly shows parser/Tavily simulated fallbacks in this run.
- Responsive: all six routes inspected at 390px and 320px, no horizontal document overflow. Desktop at 1280px has a 228px rail and two card columns without overflow. Mobile and full desktop screenshots visually inspected.
- Keyboard: visible skip-link focus verified, Enter moves focus to main content. Native form controls and evidence disclosure remain reachable; complete assistive-technology certification was not performed.
- Error: invalid owner capacity visibly renders the recoverable dark error page; returning home preserves the completed scenarios.
- Token contrast calculations: primary text/surface 15.30:1, secondary text/surface 8.10:1, primary-button text/fill 9.16:1, input boundary/fill 4.19:1. These sampled checks do not constitute a full accessibility audit.
- 41 local Markdown links, fenced JSON/fences and diff whitespace checked. Distribution metadata version reconciled to the already-declared runtime 0.2.0.

Unmet release gates remain explicit: fresh useful AI operations-task evidence, public paid-call budgets/request controls, deployment/persistent hosted storage, and production identity/connectors/authority/retention. This change establishes a consistent local UI and documentation; it does not close those gates.
