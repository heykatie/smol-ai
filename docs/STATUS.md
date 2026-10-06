# smolstuff implementation status and verification evidence

## Local sponsor-verification baseline — October 6, 2026

Fixed a reorder rendering crash caused by an unfilled `proofs` template field. The field is empty pending the separate supplier-evidence UI work.

Local verification: **119 passed, 3 skipped** using `.venv` Python. Existing tests cover sponsor-disabled behavior, call-count limits, replay protection and provider fallbacks with mocked calls. No fresh live provider calls or hosted verification were performed in this pass.

## Bounded local sponsor checks — October 6, 2026

Owner authorized one Tavily search and one Novita extraction using fictional inputs, with at most two attempts total. A temporary local SQLite budget enforced the cap; no private settings, hosted configuration or public-demo sponsor switch changed.

- **Tavily: live adapter check succeeded**, 20:18:51 UTC. The existing basic-search adapter searched generic wholesale keyboard-switch lead times and minimum orders, and accepted public links from `darshion.com/productcategory/keyboard-manufacturers` and `marketresearchfuture.com/reports/mechanical-keyboard-market-1215`. These are research links, not verification of the fictional Supplier B offer. No purchase terms or authority changed; this standalone check did not persist a workflow event or verify the UI.
- **Novita: not configured**, zero requests. `NOVITA_API_KEY` was absent from the loaded local environment. Extraction and a persisted live workflow remain unverified. Total provider attempts: **1**. No retries, Moss calls, or hosted checks were made. Actual billed credits were not inspected.

## Demo tour vs practice-owner catalog split — October 5, 2026 (America/Los_Angeles)

Requirement: clear surface split (SECURITY access model; owner-confirmed product decision).

- **`/try` demo tour** (no login): demo workflows, demo wording, `PRACTICE_BANNER` / Demo-tour chrome, and a **small `SANDBOX_CATALOG`** on Inventory (focal reorder `DEMO-ITM-001` + workshop/detective lines + a few browse samples). Not a full specialty-shop assortment.
- **Practice owner / logged-in** (not shipped): real working features + dense **`SEEDED_CATALOG` (~492 SKUs)**. `empty_inventory_snapshot(mode="owner")` / `inventory_page` already render that catalog; product home `/` states sign-in is unavailable and that dense inventory attaches after login. No Tiny / real-shop identity invented.
- Reorder fixture economics unchanged on `/try` ($189 / 21→121 / deep-link `q=DEMO-ITM-001`).

Local verification: **77 passed** on `.venv` Python for `test_inventory_tab`, `test_inbox`, `test_wsgi`, `test_http_guard`, `test_input_errors`, `test_workflow`, `test_ops_demos`, `test_terms`, `test_reorder`. Not yet browser-checked on Vercel.

## Reorder richer decision loop — October 5, 2026 (America/Los_Angeles)

Requirement: owner must review before authorizing spend; confirmation ≠ receipt; inventory should reflect completion (PRD FR-04/FR-05; DESIGN approval/trust).

Sandbox reorder path is no longer one-click approve→receipt. Prep phases (review → negotiate with fixture hold at $189 → draft PO email → ready) gate money approval. Approve only binds terms; **Submit simulated order** and **Confirm supplier match** are separate. Awaiting receipt links to confirmation/receipt evidence (not inventory). Completed offers **View Quiet linear switch in inventory** (`q=DEMO-ITM-001`). Fixture economics unchanged ($189 / 21→121).

Local verification: **46 passed** (inbox/inventory/WSGI/http-guard/input-errors) + **27 passed** (workflow/ops/terms/sponsor-budget) on `.venv` Python. Not yet browser-checked on Vercel.

## Access model decision — October 5, 2026 (America/Los_Angeles)

Owner-confirmed in [SECURITY_AND_DECISIONS.md](SECURITY_AND_DECISIONS.md): **sandbox** (try without signup / demo tour, no sponsor calls) vs **practice owner app** (login, seeded data, real sponsor calls, connectors only to disposable demo accounts).

## `/try` sandbox carve — October 5, 2026 (America/Los_Angeles)

Requirement: separate try-without-signup from a future practice-owner surface (SECURITY access model; D3/D5).

`/` is a product-home stub (CTA into demo tour; practice-owner sign-in not available; states dense catalog belongs after login). Demo tour lives at `/try` (daily brief, small demo catalog, reorder, four practice loops). Forms, redirects, catalog issue links, and WSGI/local handlers post and redirect under `/try`. Sponsor calls stay off on this surface. Practice-owner login is not shipped.

Local verification: **45 passed** on `.venv` Python for `tests/test_inbox.py`, `test_inventory_tab.py`, `test_wsgi.py`, `test_http_guard.py`, `test_input_errors.py`. Not yet redeployed or browser-checked on Vercel.

## UX loop review pass (Reorder + Daily brief) — October 5, 2026 (America/Los_Angeles)

Requirement: owner must see a clear decision and consequence (DESIGN approval/trust copy; UX loop review priorities 1–2).

1. **Reorder** empty/active states lead with a practice-run banner, hero story, decision line + primary actions, then collapsed “Why this recommendation” and evidence. Approval still $189; stock still 21 until receipt / 121 after.
2. **Daily brief** is a guided launcher: “Demo tour” kicker, Reorder featured first with next-step copy, inventory attention card, plain-language cards for the other four, “Tool activity this session” instead of “What ran”.
3. **Shared demo-tour banner** on Daily brief, Reorder, Workshop, Detective, Rescue, and Staffing (one `PRACTICE_BANNER` string).
4. **Workshop / Detective / Rescue / Staffing** use the same story → decision → consequence → actions pattern, with numbers under “Why this recommendation”. Fixture economics unchanged ($700 workshop; Saturday staffing 14 hours / 2 blocks).

Verified: `tests/test_inbox.py` + ops/inventory regressions. Not yet browser-checked on Vercel.

## Inventory tab — October 5, 2026 (America/Los_Angeles)

Requirement: after decisions, owners should see stock actually update (PRD confirmation ≠ receipt; mvp_scope reconciled inventory). Inventory reader should expose SKU/location quantities (IMPLEMENTATION_CONTRACT).

`/try?scenario=inventory` uses the **small demo-tour catalog** (`SANDBOX_CATALOG`: reorder + workshop BOM + detective + a few browse samples). Same table columns as before (Product → Category → Status → Available → Reserved → Incoming → In transit → Unavailable → Last counted → Issue), sortable/filterable. Quiet linear switch keeps PRD economics ($2.49 list / $1.82 cost, available 21 → 121 after receipt). Workshop BOM and detective lines still update from practice loops.

The dense specialty-shop assortment (**492 SKUs**: Switches 12, Keycaps 31, Keyboards 9, Desk mats 28, Keyboard configs 405, Tools 7; baseline ~available 3521 / reserved 69 / incoming 504 / in transit 22 / unavailable 57) lives in `SEEDED_CATALOG` for the practice-owner surface (`mode="owner"`). Login is not shipped; product home documents the split. Not a live POS ledger (D2 still open).

Local verification: `tests/test_inventory_tab.py` + inbox/WSGI regressions. No paid provider calls. Not yet redeployed or browser-checked on Vercel.

## Production smoke and local ZooWork cost sample — October 5, 2026 (America/Los_Angeles)

### 1) Production smoke (`https://smolstuff.vercel.app`)

Independent HTTP cookie jar: start reorder → approve → receive full. Observed:

- Start and completion pages showed **Sponsor calls are off**, parser fallback / not a verified live model call, and **no** `Tavily · live` / `ZooWork · live` / `Novita · live`
- After approve: awaiting receipt with available stock **21**
- After receive: stock **121**, completed reorder; daily brief showed replenishment completed
- No production env changes; `SMOL_SPONSOR_CALLS` left off

In-app browser also reached awaiting receipt with sponsor-off parser evidence after approving the **$189** order. Receipt was confirmed on the HTTP path above.

### 2) Local ZooWork cost sample (not production)

One local `explain_supplier_delay` against the configured stopped agent returned **live** text (lead time 14→~35 days) without changing order authority. Key-scoped `/usage?range=24h` moved from **13→14** requests and about **89.55→96.53** platform credits (~**+7.0 credits**). At the documented **200 credits/USD**, that is about **$0.035** for this one explanation. Usage attribution lagged the HTTP response by a few seconds. This is one sample on the project key, not Organization-wide billing or a guarantee for every future model/run.

Recommended showcase posture updated in [SECURITY_AND_DECISIONS.md](SECURITY_AND_DECISIONS.md): still keep public calls off; ~50 live ZooWork explanations remains a conservative budget against the $200 grant.

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

### Novita follow-up — October 6, 2026

After the owner confirmed saving the key locally and on Vercel, the remaining approved local extraction was attempted at **20:24:34 UTC**. The configured Novita endpoint returned **HTTP 403**. No usable extraction was returned, and no retry was made. The HTTP status alone does not establish the cause. The key was loaded privately and was not printed. A temporary local one-attempt budget was used; no hosted settings changed or hosted check ran. Across this verification sequence: **two provider attempts total** (one successful Tavily search, one refused Novita extraction). Novita remains live-unverified; existing parser fallback tests pass. Actual billed credits were not inspected.

## Groq → Gemini → parser wiring — October 6, 2026

Owner requested this provider order. The optional `groq_gemini_parser` extraction mode is wired into persisted reorder processing. Each configured provider is attempted once and requires its own existing quota claim; failure, invalid output or disagreement moves to the next provider, then the parser. Disabled calls or exhausted quota use the parser without another network attempt. Sanitized failed attempts and the accepted result appear in tool activity; the extraction note names the accepted provider. Synthetic economics and authority are unchanged. Existing Novita behavior and regression tests are preserved when the selector is unset.

Local `.env` selector is configured; neither new API key is present. No new model calls, quota increases, Vercel changes or deployment were performed. Verification: **127 passed, 3 skipped**, including new mocked provider-order, timeout/error fallback, conflicting output, quota blocking, persisted evidence, replay and request-shape tests. Live Groq/Gemini and hosted behavior remain unverified. The existing 119-test baseline and rendering fix are part of this local change set.

### Gemini configuration and local verification — October 6, 2026

The local `GEMINI_API_KEY` is configured; `GROQ_API_KEY` remains missing. A fictional-email Gemini request returned HTTP 400. Inspection found the adapter sent JSON Schema via the narrower `responseSchema` field. A failing request-shape regression test was added, and the adapter now uses `responseJsonSchema`. All **9 extraction-chain tests pass**. One corrected live request returned **HTTP 403**, so no validated Gemini extraction exists yet. The status alone does not establish the account/access cause. Two requests were attempted in this follow-up; no automatic retries, hosted setting changes, or hosted checks were made. The local parser remains the fallback. Keys and raw error responses were not printed; actual billed usage was not inspected.

## Groq → OpenRouter → parser — October 6, 2026

The owner saved both keys privately and selected OpenRouter instead of Gemini. Local `.env` now selects `groq_openrouter_parser`; keys were checked for presence without printing values. OpenRouter defaults to `openrouter/free`, requests structured output, and rejects paid-model overrides. Separate quota claims, validation, sanitized failure records and the local parser remain in place. Gemini is not called in this mode; previous modes and regression tests remain available.

Verification: **131 passed, 3 skipped**, including provider order, parser recovery, paid-model rejection and schema request tests. A first Groq check and a subsequent diagnostic request both returned HTTP 403; no readable JSON error established the cause. OpenRouter's first request produced a JSONDecodeError, a diagnostic request returned a completion, and a corrected structured-output request returned validated **14 → 35** day facts. Five provider requests total in this pass (two Groq, three OpenRouter), with no automatic retry loop. This is a successful standalone OpenRouter adapter check, not a persisted live workflow or hosted/browser certification. The owner's $100 OpenRouter key limit was not changed or consumed through paid-model routing; actual account billing was not inspected. No Vercel settings, public sponsor switch, or deployment changed.

### Groq SDK connection fix — 2026-10-06

Groq now uses the official Python SDK (groq>=1.0,<2, declared in pyproject.toml), installed locally. Requests retain the strict schema, 2,000-character excerpt, 10-second timeout and zero automatic retries. SDK API errors become generic fallback errors; clients close after use. OpenRouter and the parser remain backups; sponsor gates are unchanged.

Verification: the SDK transport test failed before implementation. The final suite passed with 132 passed, 3 skipped, and git diff --check passed. One live call through the updated app adapter extracted the fictional supplier fixture from 14 to 35 days. This confirms local adapter connectivity, not a persisted live workflow, browser verification or Vercel deployment. No billing or public execution settings changed.
