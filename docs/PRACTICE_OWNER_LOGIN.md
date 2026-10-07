# Shop accounts and practice login

Status: staged implementation. Auth0 is the selected login direction; configuration and integration remain pending. No login, private shop routes, provider accounts or production tenancy are shipped by this document.

## Confirmed scope — 2026-10-06

Keep /demo as an anonymous fictional guided tour. Provide two separate seeded practice shops (keyboard and bakery), each with an individual owner and employee account. Real shops have their own owners and invited employees, separate from practice data. Owner onboarding selects a shop type. Shared features include inventory, correction requests, recommendations, schedules and availability. Bakery eligibility includes batch/product expiration tracking; keyboard eligibility includes compatibility information. Eligibility does not mean these features are built.

Start with owner and employee roles. Owners may delegate correction approval and spending approval separately to trusted employees; no separate manager role initially. Employees view inventory, submit corrections for approval, prepare recommendations, view their own schedules and submit their own availability. Correction requesters cannot approve their own requests, including owners. Preserve original records, proposed values, reasons, requester, reviewer and decision history. External POS writes remain disabled pending a separately authorized connector.

Practice accounts have working features as they ship, with fictional seeded data and simulated consequential actions. Authentication does not enable sponsor spending, real purchases or connectors. Real business identities stay out of public fixtures and documentation.

## Acceptance criteria

- Verify managed identity server-side; load active membership from trusted records. Client-supplied roles, shop IDs or demo cookies cannot grant authority.
- Scope every read and mutation to the authorized shop. Test cross-shop, cross-practice and anonymous access denial.
- Maintain stable shop storage independent of visitor-demo expiry/reset. Auth provider IDs map to application-owned user records.
- Fail closed on missing authentication configuration, invalid/expired sessions, removed membership or unknown permissions.
- Keep shop type eligibility separate from user authority; preserve deterministic money and purchase rules.
- Enforce origin/CSRF protections, logout and private-response caching rules on protected routes.

## Step-by-step delivery

1. Establish this scope and test provider-independent shop permissions and four synthetic practice identities.
2. Confirm provider and configure credentials privately; implement verified login, trusted persisted memberships, protected routes and isolation tests.
3. Wire shop-scoped catalog and navigation; seed separate keyboard/bakery practice records and verify owner/employee interactions.
4. Implement audited correction request/review/apply with concurrency and no self-approval.
5. Implement own schedule/availability flows and bakery expiration tracking, one tested slice at a time.
6. Enable integrations only under their separate authority and budget decisions.

Current inspected stack: Python/WSGI app.py routes / and /demo; inbox/store records use demo session scope; demo_ui forms/navigation are tour-specific; session_files applies anonymous expiry. This foundation does not yet enforce permissions in those routes. The Next/FastAPI migration remains a separate decision.

## Current foundation

shop_access.py defines shop features and owner/employee permissions. shop_memberships.py persists application identities, shop memberships and audited delegation through SQLite or the existing Postgres adapter. Local SQLite behavior is tested; hosted persistence and concurrency have not been verified. Provisioning is an internal trusted operation, not a signup endpoint. No authentication provider or protected app routes are connected yet. auth_sessions.py supplies tested internal server-session and request-guard helpers; see [AUTHENTICATION.md](AUTHENTICATION.md).

## Confirmed refinements — 2026-10-06

Owners may view their own shop's team schedules and availability. Employees remain limited to their own. Team access still requires trusted active membership and server-side shop isolation; this refinement does not claim that schedule routes are implemented.

Healthy-stock checks show a brief “No reorder needed” result instead of only activity history. They create no purchase proposal, approval request or stock change.

## Membership integrity and explicit initialization — 2026-10-06

[SHOP_MIGRATIONS.md](SHOP_MIGRATIONS.md) describes version 1, data-preserving preflight, database constraints and rollback. MembershipStore requires the migrated schema; AuthSessions no longer creates tables. This is locally verified on SQLite and disposable Postgres, not a Neon rollout or shipped login.
