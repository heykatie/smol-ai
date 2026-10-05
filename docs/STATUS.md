# smolstuff implementation status and verification evidence

## Postgres demo TTL expiry — October 5, 2026 (America/Los_Angeles)

Requirements: anonymous demo cleanup aligned with the one-day cookie TTL (D4 interim).

`expire_demo_sessions` now also deletes Postgres rows for session ids whose latest activity is older than `SMOL_DEMO_TTL_SECONDS`. Activity comes from workflow, preview (`scenario_state.updated_at`), receipt, and integration timestamps. Related workflow rows and per-session sponsor counters are removed; the global sponsor counter is kept. Three new local Postgres behavior tests cover old-vs-fresh workflows, preview-only sessions, and combined file+Postgres cleanup.

Local verification: **113 passed, no skips** on Python 3.14 with pytest, psycopg, and an isolated UTF-8 Postgres cluster. No paid provider calls. Backup/restore remains deferred.

## Shared Postgres sponsor counters — October 5, 2026 (America/Los_Angeles)

Requirements: public call budgets before paid execution (PRD), D3 hosted enforcement of call quotas (not yet a monetary budget).

`SponsorBudget` now uses the configured Postgres database when `DATABASE_URL` is set, including an atomic `FOR UPDATE` claim path, and keeps the previous SQLite file when it is not. Inbox still requires the enable switch and both positive limits before Novita, Tavily, or ZooWork calls. Four new local Postgres behavior tests cover shared global caps across budget paths/`DATABASE_URL`, session caps, and concurrent claims.

Local verification: **110 passed, no skips** for the full suite including `tests/test_sponsor_budget.py` and `tests/test_sponsor_budget_postgres.py` on Python 3.14 with pytest, psycopg, and an isolated UTF-8 local Postgres cluster. No paid provider calls, no sponsor switch enabled on Vercel, and no hosted claim exercised. D3 remains open for an approved monetary budget and public paid execution.

## Documentation/source inspection — October 4, 2026 (America/Los_Angeles)

Inspected source and tracked evidence at `7cd4647` on live main. This is a documentation/source review, not a fresh runtime, provider, dashboard, database, or deployment test. No private configuration was loaded; no permissions, budgets, connectors, or runtime behavior were changed. The earlier synchronization review below retains its recorded evidence and does not certify later commits.

| Topic | Evidence inspected in this cleanup | Limit / remaining work |
| --- | --- | --- |
| Document authority | PRD owns requirements; AGENTS owns engineering instructions; project context is supporting philosophy/architecture/examples; this file owns verification evidence | Reference material does not override governing requirements or decisions |
| Storage wiring | `database.py`, `WorkflowStore`, and `ScenarioStore` select Postgres when `DATABASE_URL` is set, otherwise SQLite. `app.py` and `inbox.py` recognize persisted Postgres sessions without a surviving local file | Source inspection does not verify current hosted configuration, every preview, or backup/restore |
| Hosted persistence | Architecture and commit `0847325` report Neon connected and the same approved reorder awaiting receipt with stock 21 after redeploy. Commit authored October 4 Pacific / October 5 UTC | Repository-recorded single-session result; not rerun here. Backup/restore, database retention/cleanup, and broader hosted recovery remain unresolved |
| Sponsor limits | `SponsorBudget.claim` requires the enable switch and two positive call limits and reserves counts atomically. Later work moved the store to Postgres when `DATABASE_URL` is set; see the October 5 entry above | Historical note for this cleanup only: counters were still local SQLite here |
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

## Hosted verification attempt — October 4, 2026 (America/Los_Angeles)

Opened `https://smolstuff.vercel.app` in a fresh in-app browser session. The daily brief and workshop/staffing forms loaded. Clicking **Check feasibility** with defaults and **Calculate coverage** for Saturday returned to the initial forms without visible results; refresh left them unchanged. Navigating to the daily brief still showed all five scenarios not started. These are observed UI failures, not proof that database writes failed or data was lost.

Source baseline `3ecb108` contains local-file existence checks in `InboxApp._saved_page`, `_home`, `_reorder_card`, and `_plan` that can bypass stored Postgres state without a local session file. This is a candidate explanation, not a confirmed production diagnosis; the deployed commit and database configuration were not verified.

Vercel dashboard access required sign-in. Paid-call settings could not be verified, so the provider-capable reorder start was not exercised. Approval, receipt, reset, two independent session isolation, and redeploy persistence remain **not verified in this attempt**. No deployment settings or application code changed. Continue after dashboard sign-in, first confirming sponsor calls are disabled.

## Hosted verification retry — October 4, 2026 (America/Los_Angeles)

Vercel project dashboard identified production deployment `2mLgaGwH9N8pGXbmJt31kGvVosNx` as ready at source `053e4a4`; GitHub's Vercel status agreed. The project and shared environment-variable searches listed no `SMOL_SPONSOR` switch/limits. `DATABASE_URL` was listed as Neon-linked in all environments; no secret values were revealed and no settings changed. The reorder UI reported the simulated lead-time parser.

In-app browser checks: starting reorder displayed the $189 decision, refresh preserved it, and approval reached awaiting receipt with stock still 21. Two independent HTTP cookie jars then passed nine checks: fresh sessions, synthetic start, B remaining unstarted while A starts, A approval and refresh with stock 21, independent B decline, A unchanged by B, distinct session ids, and B decline surviving refresh. These verify HTTP session separation, not two separate browser profiles or authenticated business tenancy.

Chrome control subsequently disconnected. Verification continued with the in-app browser and independent HTTP sessions. This documentation-only checkpoint will trigger the existing main-branch Vercel deployment while the in-app and HTTP A sessions remain awaiting receipt and HTTP B remains declined. Redeploy survival, receipt, replay, and reset will be recorded only after that deployment succeeds and those checks run. Earlier workshop/staffing UI failures remain open.

## Hosted results after redeploy — October 4, 2026 (America/Los_Angeles)

The documentation-only push `2cb075a` triggered Vercel deployment `FGVBzFo5ystrhosFx9Hao9VZLwpB`; GitHub's Vercel status changed from pending to success. Checks then used the production domain `https://smolstuff.vercel.app` with the same saved sessions. No application code, credentials, provider switches, budgets, or database settings changed.

| Check | Result and observed evidence |
| --- | --- |
| Saved approval across deployment | In-app browser and HTTP A still awaited receipt with stock 21 after the new deployment succeeded |
| Independent declined session | HTTP B remained declined, with no purchase submitted, after redeploy |
| Receipt and refresh | In-app browser and HTTP A completed the simulated receipt; stock became 121, one owner approval displayed, and refresh preserved completion |
| Receipt replay | Repeating HTTP A's full-receipt request left stock at 121 and one owner approval |
| Reset and separation | Resetting HTTP A returned it to the initial reorder; refresh preserved reset while HTTP B stayed declined |
| Daily brief | **Failed:** both browser and HTTP checks showed the completed reorder as not started; browser counts still showed five not started and zero completed. Returning to reorder still showed completion |
| Workshop / staffing | **Failed:** valid default workshop and Saturday staffing submissions displayed no calculated results. These reproduce the earlier hosted UI failures |

The HTTP checks comprised nine passing checks before redeploy and eight passing checks plus three failed UI-result checks afterward. Test-harness requests were corrected to use the actual lowercase staffing value and exact workshop fields before recording the preview failures. This is independent cookie-jar isolation and one in-app browser, not a two-browser-profile certification. No fresh paid provider calls were exercised; the UI labeled parser, purchase, confirmation, and receipt as simulated.

Reorder state persistence is verified within these synthetic scenarios. The broader hosted experience does not pass because dashboard and preview rendering remain broken. Local-file guards in `InboxApp` are a candidate cause requiring failing regression tests and a code fix; this verification did not change them. Backup/restore, retention, authenticated tenant isolation, and shared hosted spend enforcement remain unverified or unresolved.

## Postgres rendering fix — October 4, 2026 (America/Los_Angeles)

Requirements: FR-05 saved-state persistence, FR-06 workshop results, FR-09 staffing results, and the daily brief's session status/evidence. Five new real-Postgres behavior tests reproduced hidden preview results, missing completed dashboard/evidence, ignored saved lead-time facts, and owner-versus-other-visitor rendering when no local session file exists.

`InboxApp` now checks for either a surviving local file or session-scoped persisted database rows before loading saved previews, dashboard cards/evidence, reorder status, and supplier facts. Stores and permission rules remain unchanged. Existing WSGI/session entry points already recognize Postgres sessions. The staffing regression uses Saturday with the workshop enabled for the expected 14-hour result.

Local verification: **102 passed, no skips**, Python 3.14.7, pytest 9.1.1, psycopg 3.3.6, isolated local Postgres; no paid provider calls. Diff whitespace passed. Hosted rendering and post-deploy persistence will be recorded after deployment and browser/HTTP checks; prior hosted failures remain historical until those checks pass.

## Rendering verification and hosted input-error follow-up — October 4, 2026

Vercel reported deployment `2g6pSdrt8r6p7bcfhrt9PCVmvJRd` successful for `c912b58`. The recovered in-app browser displayed saved workshop and staffing results. Workshop default showed $700 contribution and eight remaining kits; changing its deadline to two days blocked the commitment, and restoring seven days plus refresh preserved the result. Saturday staffing showed 10 hours without workshop and 14 hours/two extra coverage blocks with it; save and refresh preserved the plan. Completing reorder produced stock 121 and the daily brief correctly showed both reorder and staffing completed, with simulated tool evidence.

Twenty independent-HTTP-session checks passed on this deployed version, including lifecycle, replay, reset, isolation, dashboard completion, and visible preview results. They were sequential checks on the same deployed version, not a new deployment boundary between scripts. The keyboard skip link focused `main#content`; at 390px the dashboard document width was 390px with no horizontal overflow. Temporary viewport override was reset.

The browser error check exposed an additional WSGI defect: invalid numeric staffing input produced a Vercel 500 although the local HTTP adapter handled it. Three new WSGI behavior tests demonstrated uncaught Decimal errors or a plain-text error instead of the recoverable page. The WSGI adapter now handles `InvalidOperation` and `ValueError` with the existing HTML 400 page. Tests verify saved staffing, rescue, and workshop results remain unchanged. Complete regression result: **105 passed, no skips** in the isolated local Postgres environment. Vercel reported deployment `2nA4YaGNLqj9kQr4NpbxJuRVbWmw` successful for `77a054a`. In the same in-app browser session after deployment, the saved Saturday workshop staffing plan still showed 14 hours/two coverage blocks and the completed reorder remained completed. Invalid owner-capacity input displayed the recoverable “Check your input” page; returning to Staffing preserved the saved plan. The daily brief correctly showed two completed, one needing a decision, and two not started, with simulated tool evidence. These browser checks establish persistence across this deployment boundary for the checked session; they do not establish backup, retention, or production identity guarantees.

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
