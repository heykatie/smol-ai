# smolstuff readiness audit — 2026-10-06

## Decision

The project has a useful, tested synthetic operations core. It is not yet ready for private multi-shop production use, and its business model has not been validated. Proceed with a bounded foundation-hardening stage before the Next.js/FastAPI migration. Retain the existing deterministic Python core and Neon; a framework migration cannot substitute for tenant isolation, reliable storage, or customer evidence.

This is an evidence-backed engineering/product review, not a security certification, comprehensive penetration test, accessibility certification, or guarantee of zero bugs. Recommendations below are proposals, not newly granted authority or owner-approved commercial decisions.

## Inspection and verification

- Local checkout: `heykatie/smolstuff`, HEAD `b3576953ca662be9090746cd1b42e202fb2d5918`, plus existing uncommitted membership code/tests and login/status documentation. Those changes were included in inspection and preserved.
- Inspected requirements, authority map, architecture, target stack, security decisions, roadmap, account plan, entrypoint, stores, permissions, request handling, extraction wiring, UI and relevant tests.
- Offline regression suite: **145 passed, 3 skipped** in 4.75 seconds. The three Postgres test modules were skipped because this virtual environment lacks `psycopg`; this is not three passed database checks. No hosted DB or concurrent Postgres behavior was verified.
- Temporary SQLite/in-memory probes reproduced the healthy-stock planner error, unscoped approval counts, orphan membership acceptance, and weak Origin validation. Probes did not modify real data or call providers.
- Local browser sampled the existing daily brief and inventory at 390 × 844. Neither page overflowed horizontally. Inventory filtering reduced the visible list to the requested SKU; tabbing from its labelled search field reached the Product sort button with a solid focus outline. This is sampled evidence, not coverage of every page, browser, assistive technology, or device.
- Repository Markdown relative file targets: no missing targets found. Fragment anchors and external links were not comprehensively tested.
- No migration, credentials, permissions, deployment, connector, billing, or runtime authority was changed. No live provider checks were performed.

## What is sound

1. Money, policy, approvals, receipt reconciliation and workflow state remain deterministic Python rather than model output or browser code.
2. Workflow approvals bind to exact terms; changed terms invalidate prior authority. Submission, confirmation and receipt are separate steps. Receipt replay has regression coverage.
3. Public fixtures and UI identify simulated actions. The app does not claim continuous live monitoring.
4. Application-owned user IDs and memberships are the right separation from Auth0 identity. Shop type eligibility is separate from permissions; correction and spending delegation are separate; self-approval is denied in the permission helper.
5. One relational database and a modular application are appropriate at this stage. No evidence justifies microservices, another primary database, or a separate orchestration platform.
6. Incremental migration with the current demo retained is preferable to replacing working behavior all at once.

## Findings and acceptance gates

Priority P1 means resolve before the affected private/pilot surface ships; P2 means fix during foundation work or before depending on that behavior. Missing planned features are not automatically defects in the current synthetic tour.

| ID | Priority | Evidence and impact | Required outcome |
| --- | --- | --- | --- |
| A1 | P1 | `app.py:58–142` exposes only home and anonymous `/demo`. `shop_access.py:44` and membership persistence are not connected to protected routes. Auth0 application creation is configuration, not working login. | Verified identity → application user → active shop membership → scoped service call on every private read/mutation. Deny anonymous, unknown identity, wrong shop, expired identity, revoked membership and stale grants. |
| A2 | P1 | `shop_memberships.py:14–28` has no foreign keys or role/type/flag CHECK constraints. A direct SQLite insert accepted an active owner linked to a nonexistent user/shop. Normal provisioning checks do reject dangling records, but another writer can bypass those checks. | Versioned schema migrations with DB-enforced relationships and valid values; enable SQLite FK enforcement; prove migration/rollback and Postgres parity. Preserve existing records and audit data. |
| A3 | P1 | Workflow/preview persistence and cleanup use visitor `session_id`; `database.py:58` and `session_files.py:27` expire anonymous records. This is not durable private-shop storage. | Separate durable shop records from expiring tour sessions. Shop-owned products, variants, locations, stock movements and workflows must carry trusted shop scope. Expiry/reset tests must prove private data survives. |
| A4 | P1 | `http_guard.py:19–23` compares host only when Origin has a nonempty netloc. Probes accepted `Origin: null`, missing Origin and an HTTP origin for the same host. No CSRF token is required. This reproduces validator behavior, not a demonstrated cross-site browser exploit; SameSite cookies reduce some exposure. | Explicit full-origin allowlist, malformed/null-origin rejection, and the chosen cookie/CSRF design for authenticated routes. Test browser request behavior; do not reuse the anonymous validator as production protection. |
| A5 | P1 | `inbox.py:486–560` can claim sponsor attempts using environment gates, without a public/practice surface restriction. `/demo` says no sponsor calls, but setting the global switch and caps can permit those calls through the same anonymous workflow. | Hard-deny external paid/model execution in `/demo` regardless of global config. Require authenticated authorized practice scope and separate approved budgets for permitted calls. Test with mocked adapters, never spend to prove the denial. |
| A6 | P2 | `reorder.py:139` constructs a zero-quantity purchase when stock is healthy. A one-day lead-time probe raises `ValueError: Quantity must be a positive integer` rather than returning no action. Existing contract already discloses this limitation. | First-class healthy/no-action result without constructing a purchase; meaningful tests for no risk and zero demand before generalizing the planner. Keep the fixed risky demo unchanged. |
| A7 | P2 | `workflow.py:1125–1159` scopes workflow, receipt and movement counts, but approval/execution/confirmation counts fall through to global counts. A visitor with zero workflows saw another visitor's approval count of one through `count_approvals()`. No current public route leak was demonstrated. | Scope every aggregate through its owning workflow/shop. Verify all count methods across two tenants before exposing them in an API/dashboard. |
| A8 | P1 before real writes | `pg_connection.py:9–11` translates SQLite `BEGIN IMMEDIATE` to ordinary Postgres `BEGIN`; workflow reads in `_require` do not add row locks. SQLite writer serialization does not carry over automatically. The concurrent-approval test collects errors but does not assert their expected handling; the rollback test starts/rolls back without injecting a write failure. | Disposable Postgres tests for concurrent approval/revoke/execute/receipt/delegation, expected replay/conflict results and real partial-write rollback. Use row locks or conditional state/version updates where justified. This is a risk finding, not a reproduced hosted race. |
| A9 | P2 | Schema creation runs in store constructors; cleanup scans persisted activity on normal requests; `reserve_session` stores its counter in local SQLite even on Vercel. A 100/hour setting is therefore not a reliable deployment-wide limit across instances. | Managed migrations; indexed tenant queries; bounded cleanup outside the request hot path when needed; shared deployment-wide abuse controls. Profile first, then tune. |
| A10 | P2 | No `.github` CI configuration was present. The repo tracks 198 paths under `pytest-of-ktl/`. Dependency ranges are broad and there is no demonstrated reproducible frontend build yet. | Automated offline + disposable Postgres checks, reproducible dependency management and secret scanning; deliberately remove generated artifacts after preservation review. Do not silently delete existing user files. |
| A11 | P1 before pilot | Backup/restore, private retention, export/erasure, support, monitoring, incident response and worker retry/recovery are not established by synthetic tests or a single redeploy-survival check. | Defined retention and recovery objectives, tested restore, redacted diagnostics, bounded retries/idempotency and an operating runbook before private business records or external actions. |

### Product logic needing decisions

- Current `shop_access.py:53` limits schedule viewing to one's own user even for owners. Employees viewing only their own schedule matches the request, but owner coverage planning needs a distinct authorized team-schedule capability if that feature is selected. Do not silently grant it.
- With correction self-approval prohibited for everyone, an owner-only shop cannot approve its own correction. Define a practical review path and distinguish submitting an audited correction from performing an separately authorized owner adjustment. Do not add a bypass implicitly.
- Four practice identities are seed descriptions, not provisioned login accounts. Decide invitation/provisioning and demo access/reset behavior without shared passwords or exposing private-shop access.
- Stock availability must distinguish on-hand, reservations, inbound, expiry, damaged stock and locations. Bakery tracking needs batch/lot quantities, expiration rules and disposal/correction audit; a feature flag is insufficient. Do not add inventory to the general JSON preview store as production design.
- Connector truth, manual corrections and observed POS sales need explicit conflict precedence and reconciliation. External systems remain disabled until the existing decisions are resolved.

## Architecture recommendation before migration

Retain a modular monolith: `web/` for Next.js/TypeScript; `src/smolstuff/api/` for thin FastAPI adapters; existing Python domain modules; dedicated persistence/repository interfaces and versioned migrations against the same Neon database. Paths are proposed until implementation.

Recommended request flow:

`Browser → Next.js server session → FastAPI validated API access token → active membership lookup → shop-scoped domain service → Neon`

Next may own login/session transport, but Python owns business authorization. FastAPI must validate signature, issuer, audience, expiry and permitted algorithms with a maintained library. A verified login or email address alone never makes a user a shop owner. Resolve identities with the issuer plus subject, not email matching. Recheck current trusted grants at mutation time. Design revocation and caching explicitly.

Use the Next server as the browser-facing API boundary initially if it simplifies secure cookies and same-origin mutations. Keep a documented access-token API boundary for later mobile clients. No direct browser/Next business-table writes. Never accept a frontend role or shop ID as authority. Tenant-scoped repositories are mandatory; Postgres row-level security may add defense in depth but must use an appropriate DB role and tested connection context—its mere presence is not proof of isolation.

Separate domain services from HTML controllers before wrapping them: `InboxApp` currently mixes routing, demo state, fixtures, providers and presentation. Do not return its rendered HTML as a supposed JSON domain API or port its template internals wholesale into React. Preserve tests around the existing domain modules.

Use explicit API input/output schemas, consistent errors, request limits, idempotency keys and conditional state/version checks. Avoid background work that relies on a serverless request continuing after its response. Durable ingestion/workers are needed only when actual connectors begin; no new queue service is selected by this audit.

The first migration slice should be **login + active shop access + read-only inventory**, not anonymous reorder mutation endpoints. The existing target-stack document instead starts with the reorder loop; reconcile the plan before implementation. Keep `/demo` operating independently until parity and rollback are verified.

## Frontend and experience

The current visual system is coherent and reusable. The sampled mobile pages fit, inventory search works, and keyboard focus was visible. Inventory instructions consume considerable phone space before the table; reduce explanatory copy or put detail behind accessible disclosure controls when designing the new interface.

Before release, test owner/employee navigation, permission-denied states, loading/empty/error states, expired sessions, destructive confirmation, shop switching, long names, large catalogs, narrow screens, keyboard operation and screen readers. Use WCAG 2.2 AA as a target, not a claimed certification. Measure performance with representative data; no measurements currently justify claims that the app is optimized.

## Documentation consistency

- `PRACTICE_OWNER_LOGIN.md` and the security refinement still say provider selection pending; the owner has now selected Auth0 and created a Regular Web Application, but no login runtime is verified.
- PRD section 4 places multiple businesses in P2 and section 2 excludes industry behavior initially; the Oct 6 refinement explicitly requires multiple shops and bakery eligibility. Rewrite the next-release scope coherently rather than relying on an appended exception.
- ROADMAP excludes account onboarding from the current build, while account work is now the next release. Preserve the historical demo boundary and clarify the new release boundary.
- TARGET_STACK begins with an anonymous reorder migration; the recent conversation proposes authenticated shop access first. Choose one sequenced plan and document it.
- Architecture/integration summaries still center Novita and the Vercel subdomain despite later extraction adapters and the new custom domain. Historical verification remains valuable but must be distinguished from the current inventory of adapters and planned configuration.
- `app.py`'s introductory comment describes sponsor counters as temporary on Vercel; current `SponsorBudget` can use shared Postgres. Correct this factual comment during the relevant cleanup.
- Avoid turning documentation into more competing plans: PRD owns requirements; security register owns consequential decisions; target stack owns migration; STATUS owns evidence. This audit supplies findings and proposed actions, not new requirements by itself.

## Business model, validation and GTM

No reviewed evidence establishes product-market fit, customer interviews, paid demand, repeat usage, acquisition cost, retention, support burden or unit economics. PRD correctly labels user roles as hypotheses. Two prospective shops are useful design partners, not proof of broad market demand. Industry engineering practices cannot validate a business model.

Proposed positioning: **help small-shop owners handle inventory and operational exceptions with evidence and controlled approvals**. Avoid a literal “replace your manager” promise: physical work, judgement, employee relationships and accountability still need people. Lead with a concrete outcome that can be measured rather than AI autonomy or the number of sponsor tools.

Proposed initial offer: one core exception workflow plus shared inventory and correction review. Bakery expiration and keyboard compatibility can be separate type-specific modules. Support the confirmed practice demos, but validate one primary customer segment/workflow first. Scheduling, sale-rescue networks and broad autonomous procurement should not all be launch requirements unless interviews justify that scope.

Proposed validation sequence:

1. Interview 5–10 owner/operators about recent actual incidents, current tools, time spent, losses, data access concerns and purchasing authority. Do not count stated enthusiasm as payment evidence.
2. Observe the same recurring workflow in the initial design-partner shops with consent; record a baseline without exporting private records into demos.
3. Run a limited assisted pilot after technical/privacy gates. Track setup effort, completed resolutions, owner interventions, correction quality, unresolved exceptions and continued use.
4. Test a per-shop subscription proposal with included employee seats and bounded AI use. Do not select prices in code yet. Seek a concrete paid commitment and learn whether the value exceeds cost/support effort.
5. Expand only after repeat usage and credible benefit. Predefine success/failure thresholds with the owner; no results or targets were confirmed by this audit.

Per-shop pricing is a reasonable hypothesis for cost-sensitive teams: charging for every employee can discourage adoption. Model costs should not be unlimited. Calculate contribution as subscription revenue minus hosting/auth/model/search/email usage, payment fees and variable support. Free provider tiers and promotional credits are temporary cost assumptions, not the permanent margin model. OpenRouter's key limit and task-count quotas are not proof of zero spend or a monetary budget.

GTM proposal: founder-led onboarding through the initial design partners; a fictional public demo; opt-in referrals after useful outcomes; consented case studies with measured benefits. Broader outreach, paid acquisition and public claims wait for evidence. No messages were sent, no businesses were named in this report and no pricing commitments were made.

Commercial hosting needs attention: Vercel Hobby is for personal/non-commercial use. Confirm an appropriate paid plan before using smolstuff to operate real businesses or for commercial purposes; commercial use can precede subscription revenue. No plan was changed by this review.

## Ordered execution plan

1. **Reconcile the next-release PRD and architecture** around Auth0, private shops, two practice shops, employee roles and an authenticated read-only inventory slice. Record remaining consequential choices.
2. **Fix reproduced defects with failing regression tests first:** scoped aggregates, healthy/no-action planning, public sponsor denial and hardened request validation. Keep anonymous fixtures intact.
3. **Harden persistence:** migrations, relationships/constraints, durable shop scope and disposable Postgres concurrency/rollback tests. Establish CI before new API work.
4. **Begin one Next/FastAPI slice:** login → trusted membership → shop-scoped inventory read; verify wrong-shop, revoked-user and mobile/error paths.
5. **Add audited correction review/apply**, then own schedule/availability and batch expiration, each as a complete tested feature.
6. **Run the bounded pilot and price validation** once private-data, recovery and operating gates pass. Preserve connector/execution gates throughout.

The immediate next step is item 1 plus targeted fixes—not another auth-provider comparison, a broad UI rewrite, or a claim that all production gates are already satisfied.

## External references checked

- [Auth0 access-token validation](https://auth0.com/docs/secure/tokens/access-tokens/validate-access-tokens)
- [PostgreSQL constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)
- [PostgreSQL row security](https://www.postgresql.org/docs/17/ddl-rowsecurity.html)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Vercel Hobby plan](https://vercel.com/docs/plans/hobby) and [fair-use rules](https://vercel.com/docs/limits/fair-use-guidelines)

No universal “industry standard” business strategy exists. These references support specific technical/hosting criteria; the strategy recommendations remain hypotheses requiring customer validation.

## Remediation log

- **A7 fixed locally, 2026-10-06:** approval/execution/confirmation aggregate queries filter through the owning workflow's session. New two-visitor regression failed before the fix and passed afterward; full offline suite 146 passed, 3 Postgres modules skipped. Not deployed; hosted Postgres remains unverified. The original findings above describe the audited baseline.

- **A6 fixed locally, 2026-10-06:** healthy/zero-demand planning returns no purchase; persisted inbox and brief display “No reorder needed,” with replay and attempted purchase actions tested. Offline suite 149 passed, 3 skipped; isolated fictional browser result/mobile layout verified. Not deployed.
- **Schedule visibility decision recorded:** owners may view team schedules/availability within their authorized shop; employee access remains own-only. Permission implementation remains pending.

- **Team permission helper implemented locally, 2026-10-06:** owners can read active same-shop members' schedules/availability; employees stay own-only and no third-party availability writes are granted. Full offline suite 153 passed, 3 skipped. Routes/UI/authentication remain pending.

- **A2 partially remediated locally, 2026-10-06:** versioned membership/identity/shop/audit/session constraints preserve valid records and refuse invalid legacy data. SQLite and disposable PostgreSQL 14.15 preservation, direct-write rejection, rollback and concurrent migration checks pass. Full suite: 258 passed, none skipped. Neon, production backup/restore, durable shop storage and remaining workflow schema gates remain open.
- **A9 narrowed locally, 2026-10-06:** membership/auth-session constructors no longer perform schema DDL and require an explicit recorded migration. This does not resolve schema initialization in other workflow stores. See [SHOP_MIGRATIONS.md](SHOP_MIGRATIONS.md).

- **A5 fixed locally, 2026-10-06:** public InboxApp hard-denies sponsor budget claims and always parses locally, independent of provider keys, global switches, quotas or extraction-chain selection. Mocked WSGI and direct-app denial tests passed; full suite 228 passed, 35 Postgres tests skipped. Private authorized execution is still unimplemented; no deployment or hosted denial check was performed.

- **CI foundation staged locally, 2026-10-06:** read-only checks and a disposable Postgres runner added. Full local runner: 263 passed, no skips; workflow YAML parsed. First GitHub run and required merge checks remain pending. No deployment or repository-settings change.
