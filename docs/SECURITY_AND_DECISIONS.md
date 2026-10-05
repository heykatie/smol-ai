# smolstuff security boundaries and decisions

Requirements and proposals as of October 4, 2026. No audited-security claim is made. The public demo uses synthetic records and simulated business actions; real accounts and business execution remain disabled until their gates are met.

## Data and authority boundaries

| Boundary | Required enforcement | Current limit |
| --- | --- | --- |
| Mail provider → gate | Exact consent/scopes; approved metadata first; prohibited bodies never fetched | No live mailbox connector |
| Gate → models/agents | Minimum structured operational facts with evidence references | Optional constrained Novita call or parser fallback using synthetic supplier message |
| Canonical store → retrieval | Business/source access filters; expiry/deletion propagation | No retrieval index |
| Planner → policy | Schema validation; canonical trust/freshness from application records | Seeded proposal flags |
| Policy → executor | Versioned exact authority; fail closed on missing critical evidence | Simulated execution only |
| Owner → approval | Authenticated role, session/business binding, exact terms, CSRF protection | Synthetic `owner`; anonymous demo session |
| Browser/research → network | Allowlisted schemes/hosts, private-network denial, safe redirect handling, no unrestricted downloads | Tavily research exists; no browser verifier; destination enforcement still required before general network tools |
| Store → audit/export | Minimal facts, actor/scope, disclosure fields, redaction and defined retention | Workflow history and short integration records; not a tamper-evident ledger |

External email, attachments, webpages and agent text are evidence. They cannot change instructions, trust themselves, grant permission, raise limits, obtain credentials or invoke unrestricted tools. No model receives purchase credentials or direct execution tools. Validate recipients and destinations in application code. Raw evidence must be separated from general model context and user-facing logs.

Least privilege applies to reads and disclosures as well as writes. Model extraction may receive only the permitted relevant excerpt, never an entire inbox/thread by default. Search receives generic product requirements, not customer names or private supplier prices. Merchant requests disclose item/variant, quantity, deadline and necessary fulfillment terms; internal acquisition ceiling, margin targets, employee records and unrelated customers stay local. Log the exact field manifest disclosed to each provider without retaining unnecessary content.

Sender allowlisting is permission to process, not proof of identity or factual correctness. Use provider authenticated metadata and appropriate sender verification before critical claims; display-name matching is insufficient. Reject or quarantine ambiguous product mapping and conflicting facts.

## Public demo launch gates

The cookie is a server-issued 32-hex identifier with HttpOnly, SameSite=Lax, and a one-day Max-Age. A client-invented value is ignored unless that session file already exists. Secure is set when `DEMO_COOKIE_SECURE=1` or `VERCEL=1`. This is not login. A request removes demo files older than `SMOL_DEMO_TTL_SECONDS`. Posts are size-limited before the body is read, content-type checked, and refused when the Origin host does not match Host. New sessions are counted in a window, 100 per hour by default. Sponsor calls stay off unless `SMOL_SPONSOR_CALLS=1` and both limits are positive integers. The counters share one file per server instance. `.gitignore` excludes `data/` and private `.env` files; `.env.example` is the public placeholder. Styled 400 pages handle invalid numeric input.

Before public paid calls or broader exposure, require:

1. HTTPS and Secure cookies on the host; CSRF/origin validation on mutations, bounded body length, validated content type/action, controlled invalid-input/error responses.
2. Server-side session scoping for every read/mutation; tests that one visitor cannot approve, reset or view another visitor's case. Do not adopt a client-selected arbitrary existing session as authentication.
3. New anonymous sessions are limited to 100 per hour by default. That counter is not a disk quota, and it does not survive as a business-record retention policy.
4. Paid connectors disabled unless a server-side owner-approved budget exists; overall and per-session quotas, cache/replay fallback, timeouts and no unlimited public provider calls.
5. Secrets excluded from source, `.env` files, prompts, evidence, screenshots, browser output and development provenance. Maintain private-config ignores and public placeholders before entering credentials locally.
6. Persistence contract stating whether restart/redeploy retains files. No current hosting certification; if ephemeral, show a session-reset limitation and do not promise durable approval resume across deployments.

## Production pilot gates

Authenticate owner/operators; enforce roles at the API and database/retrieval layer. Restrict each connector/worker to the authorized business and action set. Protect tokens and evidence at rest and in transit, rotate/revoke credentials, document third-party data handling and backups, and implement access/erasure audit. A successful demo isolation test proves neither production multi-tenancy nor provider privacy.

Revocation stops new reads, model disclosures and unauthorized pending actions immediately. Remove pending access jobs and cached/retrieved private content according to retention policy. Already-submitted orders must enter a tracked cancellation/recovery process; disconnecting does not undo a transaction. Deletion handles raw evidence, extracted facts, vector copies, logs and backups with disclosed exceptions for required records. Do not promise immediate deletion from a provider whose contract does not support it.

Production audit records link source/evidence, disclosed fields, action snapshot, policy version, authenticated actor, execution attempt/external ID, verification, receipt/movement and resolution. Protect writes and exports; decide retention and tamper protection explicitly. Concise evidence/rationale suffices; hidden model reasoning is not an audit requirement.

## Decision register

These are missing consequential choices, not permissions the coding assistant may infer. Implement a disabled/configurable boundary while progressing with synthetic tests.

| ID | Decision needed before | Required choice | Safe interim behavior |
| --- | --- | --- | --- |
| D1 | Real mailbox onboarding | First provider, operations mailbox/routing vs mixed inbox, exact scopes, permitted categories and consent wording | Synthetic event source only; no routine uploads as intended production UX |
| D2 | Real inventory/POS integration | Authoritative system, SKU/location mapping, conflict priority, observation cadence, read/write scopes | Fixture ledger; never overwrite remote quantities |
| D3 | Public sponsor/model execution | Runtime/provider, specific model, approved total and session cost budget, quota window | Paid calls disabled; deterministic fallback labeled simulated |
| D4 | Hosted durability | Vercel is the host. The remaining choice is the database: Neon Postgres is recommended and is not provisioned. Backups and cleanup are still unset | Local SQLite while the disk survives; no hosted durability claim |
| D5 | Real approvals or purchases | Auth/roles, allowed action classes, approval TTL, hard cash limits vs overrideable rules, budget window and reservation semantics | Synthetic approval only; block real executor |
| D6 | Real data ingestion | Raw-content/fact/audit/vector retention, storage location, third-party handling, erasure and backup exceptions | No private records; public fixtures only |
| D7 | Live merchant outreach | Participating counterparties, discovery/geo scope, nonbinding message authority, offer expiry/reservation protocol, transfer/dispute responsibility | Two fictional participants; simulated negotiation only |
| D8 | General forecasting | Complete-history minimum, target coverage horizon, safety-stock rule, seasonality and stockout bias | Ten-day demo average; no optimized quantity claim |
| D9 | Real staffing advice | Minimum coverage, opening-hour availability, workload data and scheduling constraints | Coverage-hour recommendation only; no named-worker scheduling |

Preview input ranges, retry caps and synthetic negotiation rounds in the implementation contract are proposed engineering defaults. Record accepted changes here; do not call them owner-confirmed decisions. None of these proposals expands access, spending or disclosure authority.

## Inspection scope

The dark UI changes presentation only; they do not make these production gates complete. The current app can call Novita/Tavily when configured and has no public-call quota; do not host it with paid credentials until D3 and rate limits are implemented. This UI inspection ran without loading private credentials or making provider calls. See STATUS.md for current versus historical evidence.
