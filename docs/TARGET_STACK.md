# Target application stack

Owner-confirmed direction for Cursor and Claude. This is the intended end state, **not** a claim that Next or FastAPI are implemented today.

**Current production** remains Python stdlib HTTP locally and WSGI `app.py` on Vercel, with server-rendered HTML. See [ARCHITECTURE.md](ARCHITECTURE.md) and [STATUS.md](STATUS.md).

## Target shape

```text
Next.js (TypeScript UI)
        │  JSON over HTTP (cookies/session as designed)
        ▼
FastAPI (Python JSON API — thin adapters only)
        │
        ▼
Deterministic Python core (smolstuff package)
  workflow, policy, money, terms, inventory, lifecycle,
  reorder, ops_demos, sponsor_budget, zoowork/novita/tavily adapters
        │
        ▼
SQLite (local) / Neon Postgres (hosted DATABASE_URL)
```

| Layer | Choice | Role |
| --- | --- | --- |
| UI | **Next.js + TypeScript** | Pages, layout, client interaction. Follow [DESIGN.md](DESIGN.md). |
| JSON API | **FastAPI** | HTTP/JSON adapters that call existing Python domain code. |
| Domain | **Existing `src/smolstuff/`** | Authority, money, policy, workflow state. Stays Python. |
| DB | **SQLite / Neon** | Canonical store. Do not create a second database. |
| Host | **Vercel** | UI and API deployment as designed at implementation time. |

Flask is **not** the target API framework. Stdlib/WSGI HTML may remain as a fallback or be retired after Next parity — decide at cutover, do not delete early.

## Non-negotiable rules (agents must follow)

1. **Do not rewrite** `workflow`, `policy`, `money`, `terms`, `lifecycle`, `reorder`, or sponsor/ZooWork authority into TypeScript or Next server code.
2. **Do not put** approve/decline, spend limits, or policy decisions only in the frontend.
3. **Do not enable** public paid calls or real connectors unless [SECURITY_AND_DECISIONS.md](SECURITY_AND_DECISIONS.md) gates are met.
4. **Do not start Phase 1+** unless the user explicitly asks to begin the Next/FastAPI work (or a task clearly scopes that phase).
5. Prefer the **smallest vertical slice** (one reorder API + one Next page) over a big-bang migration.
6. Preserve and extend **behavior tests** for money, authority, persistence, and integrations.
7. Neon remains the hosted DB; no second database product.

## Phased plan

### Phase 0 — Current (default until user starts migration)

- Keep stdlib inbox server + WSGI `app.py` + HTML UI.
- Continue product work (TTL, sponsor gates, synthetic demo, docs).
- Owner login and paid-call enablement stay decision-gated.

**Agent default:** implement features on the current stack unless the user names Phase 1+.

### Phase 1 — FastAPI JSON API

**Trigger:** user asks to start the API/UI migration, or asks for JSON endpoints for a Next client.

**Do:**

1. Add a FastAPI app as a **thin** layer (suggested location: `src/smolstuff/api/` or repo-root `api/` — choose one and document in [DEVELOPMENT.md](DEVELOPMENT.md)).
2. First endpoints should cover one reorder loop, for example:
   - session bootstrap / current user session
   - get reorder / daily-brief state
   - `simulate_email` / start
   - `approve` / `decline`
   - `receive_full`
   - reset (scoped as today)
3. Handlers call existing `InboxApp` / `WorkflowStore` / stores — no duplicated policy math.
4. Keep `smol_session` (or successor) server-issued; document cookie/`SameSite` behavior for local Next → API.
5. Tests: API behavior tests for the same authority/persistence properties as today’s inbox tests.
6. Do **not** remove HTML SSR in this phase.

### Phase 2 — Next.js + TypeScript UI

**Trigger:** Phase 1 can complete one reorder loop via JSON; user asks for the Next UI.

**Do:**

1. Scaffold Next (App Router) + TypeScript in-repo (suggested `web/` or `frontend/` — document the path).
2. Implement **daily brief + reorder** first; match [DESIGN.md](DESIGN.md) (dark, clean, sleek, gently cute).
3. UI calls FastAPI only; no direct DB access from Next.
4. Local DX: Next `npm run dev` + FastAPI/uvicorn (document exact commands in [DEVELOPMENT.md](DEVELOPMENT.md)).
5. Do not require rewriting NomNow/ProFolio; this is smolstuff’s UI layer.

### Phase 3 — Cutover

**Trigger:** Next covers the flows we ship publicly (at least reorder + daily brief); user approves cutover.

**Do:**

1. Make Next the primary UI on Vercel.
2. Serve FastAPI as the JSON backend (same project or linked service — pick at implementation time using current Vercel Python docs).
3. Retire or demote HTML SSR deliberately; update README/STATUS with evidence.
4. Keep synthetic purchases/messages and sponsor-off defaults unless security decisions change.

## Out of scope for this migration

- Rewriting the domain core in Node/TypeScript
- Replacing Neon with another primary DB
- Enabling real mailbox, payments, or merchant send without security decisions
- Using Next API routes as the system of record for approvals or money

## Related owners

| Topic | Doc |
| --- | --- |
| Hosting / Neon / current adapters | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Local commands (update when phases land) | [DEVELOPMENT.md](DEVELOPMENT.md) |
| Visual UI | [DESIGN.md](DESIGN.md) |
| Auth / paid calls / connectors | [SECURITY_AND_DECISIONS.md](SECURITY_AND_DECISIONS.md) |
| What is verified today | [STATUS.md](STATUS.md) |
| Later product ideas | [ROADMAP.md](ROADMAP.md) |
