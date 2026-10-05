# smolstuff current synchronization review

Reviewed October 4, 2026 against live main `d48c344` (the merged documentation review plus the subsequent local-demo/package update), then the dark UI synchronization branch. This file supersedes docs/REVIEW.md for current status; that first review is historical. Current docs use lowercase prd.md, mvp_scope.md and demo_spec.md, and the app/package/service is smolstuff.

## Vision and implementation

The vision remains an easy-to-use AI operations system for small local businesses: automatically triage permitted email without uploads, extract actionable work, investigate inventory, recommend/perform bounded reordering, identify staffing-light days, and potentially save a sale with nearby merchant agents. Privacy, least privilege, exact authority, auditability and trust are governing requirements.

The app is an interactive synthetic demonstration of that vision. It now includes the reorder lifecycle plus four persisted previews. Synchronization means documents agree about what is intended, built and verified; it does not mean real-world connectors or the whole production vision are implemented.

| Capability | Current implementation | Remaining gap |
| --- | --- | --- |
| Daily brief / Action Inbox | Persisted session counts and five discoverable scenarios, shared dark shell | Production onboarding, real background brief and authenticated owner |
| Email work | Simulated supplier arrival, optional Novita two-field extraction/parser fallback | Live provider ingestion, scoped metadata gate, categories and general task extraction |
| Replenishment | Ten-day velocity, seeded supplier terms, $61 approval, confirmation, receipt/reconciliation | Live inventory/supplier updates, timed supply and no-risk/general planner |
| Inventory Detective | Physical-count fixture, evidence confirmation, approved three-unit correction, original count/history and recount | General business investigation, input ranges and authenticated exact adjustment authority |
| Workshop | Editable attendees/deadline, deterministic materials/economics, simulated approval/receipt/completion | Distinct production purchase/customer approvals, evidence/capacity integrations, economic feasibility beyond default fixture |
| Sale rescue | Two synthetic offers, bounded counteroffer logic, contribution check, simulated authorization/transfer/fulfillment | Nearby real agents, offer expiry, reservation, disclosure, dispute and actual payment/fulfillment |
| Staffing | Weekday mean, workload hours, saved coverage plan; Tuesday owner-only/Saturday additional coverage | Production minimum coverage/work-hour constraints; no named-worker scheduling |
| Supplier research | Tavily client wired; output only affects research evidence, not seeded offer | Fresh provider verification in this review, public quotas, actual supplier validation |
| UI | Shared dark tokens/frame/navigation; lavender/mint, smile mark, responsive cards/forms/evidence/error states | Broader accessibility/user testing and hosted verification |
| Security/authority | Synthetic visitor isolation, deterministic policy, terms hash, session-scoped SQLite, request limits, and sponsor calls off by default | Authenticated roles, full material hashes, atomic spending reservations, and a hosted session that survives redeploy |

## Documentation repairs in this change

- Updated implementation contract for the actual smolstuff package, scenario store, optional model/research clients and shared UI.
- Replaced stale “no provider clients” / “previews absent” status with actual wiring, while separating old provider reports from fresh evidence.
- Corrected development settings: .env loader and ignores exist, and reorder reset preserves other previews. Render is retired. Vercel production returned the dark daily brief. Sessions on that host are temporary.
- Added docs/DESIGN.md and linked the confirmed visual direction from PRD, scope, fixture, project context, README and AGENTS.
- Retained the old review explicitly as history; all current status pointers use this file.
- Unified the formerly separate procurement/empty pages with the same dark shell.
- Added two numeric-error regression tests, observed them fail with dropped connections, then handled Decimal conversion errors as styled HTTP 400 without saving invalid scenario data.

## Evidence and limits

Source inspection verified optional Novita/Tavily wiring. The README's earlier successful Tavily, separate Moss query and account/probe reports were not rerun. Supplier offers, purchases, messages, and merchant participants remain fictional. The dark daily brief is deployed. That is not a production security certification.

The UI-sync review recorded 64 passing tests. The current suite, run on Python 3.9 after the public-demo fixes, is 85 passed and 1 skipped. The skip is the Postgres test when `psycopg` is not installed.

## Final verification for the synchronization change

- Earlier UI-sync run: **64 tests passed** on Python 3.14. The current suite is recorded above.
- Browser: completed reorder (21 unchanged at confirmation, 121 after receipt), workshop ($700/eight kits), detective (20 → 17, unresolved one → recount resolves), merchant rescue ($21/$27 offers, $27 reconciled fulfillment), and Saturday staffing (14 hours/two blocks; saved plan).
- Browser: refreshed awaiting-receipt state; all completed previews remain in session and Daily brief counts show five completed cases. Evidence correctly shows parser/Tavily simulated fallbacks in this run.
- Responsive: all six routes inspected at 390px and 320px, no horizontal document overflow. Desktop at 1280px has a 228px rail and two card columns without overflow. Mobile and full desktop screenshots visually inspected.
- Keyboard: visible skip-link focus verified, Enter moves focus to main content. Native form controls and evidence disclosure remain reachable; complete assistive-technology certification was not performed.
- Error: invalid owner capacity visibly renders the recoverable dark error page; returning home preserves the completed scenarios.
- Token contrast calculations: primary text/surface 15.30:1, secondary text/surface 8.10:1, primary-button text/fill 9.16:1, input boundary/fill 4.19:1. These sampled checks do not constitute a full accessibility audit.
- 41 local Markdown links, fenced JSON/fences and diff whitespace checked. Distribution metadata version reconciled to the already-declared runtime 0.2.0.

Unmet release gates remain explicit: fresh useful AI operations-task evidence, public paid-call budgets/request controls, deployment/persistent hosted storage, and production identity/connectors/authority/retention. This change establishes a consistent local UI and documentation; it does not close those gates.
