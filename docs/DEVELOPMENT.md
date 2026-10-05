# smolstuff development and deployment

## Read before coding

Read PRD → MVP_SCOPE → DEMO_SPEC → IMPLEMENTATION_CONTRACT → SECURITY_AND_DECISIONS → INTEGRATIONS. Use project_context for broader product rationale. Read the root AGENTS.md. Current source provides implementation evidence, not permission to lower requirements. Record conflicts and consequential missing choices; proceed with synthetic/configurable boundaries where safe.

## Local setup

Python 3.9+ is declared. Application runtime uses the standard library. Python imports are `smolstuff`. The local server reads `.env` on startup and does not print values. `.env` is gitignored.

```bash
git clone https://github.com/heykatie/smolstuff.git
cd smolstuff
python3 -m venv .venv
.venv/bin/python -m pip install "pytest>=8.0"
PYTHONPATH=src .venv/bin/python -m smolstuff.inbox
```

Open `http://127.0.0.1:8765`. Start demo, inspect evidence, approve, refresh at awaiting receipt (stock 21), simulate full receipt (stock 121), then reset. Decline creates no order. This process reads no private mailbox and sends no external message/purchase.

```bash
.venv/bin/python -m pytest -q
```

`pytest` configuration adds `src` to the import path. Run modules with PYTHONPATH=src; no editable-install/build-backend workflow is verified. There is no lint/typecheck/CI configuration in the baseline. Introduce relevant checks alongside changes, and document their actual commands.

## Actual runtime configuration

| Setting | Current behavior |
| --- | --- |
| PORT | Default 8765; presence also binds 0.0.0.0 instead of 127.0.0.1 |
| DEMO_COOKIE_SECURE | `1` adds Secure to the cookie; use on HTTPS host, not local plain HTTP |
| Storage | Without `DATABASE_URL`: `data/sessions/`, one SQLite file per cookie. With it: session-scoped Postgres workflow/preview rows; local session markers and sponsor counters remain files |
| Cookie | `smol_session`, HttpOnly, SameSite=Lax, one-day Max-Age |
| Provider credentials | `NOVITA_API_KEY`, `TAVILY_API_KEY`, and `ZOOWORK_API_KEY` are read only when sponsor calls are enabled and both limits are set. A key is not proof of a verified workflow. |

Startup loads `.env` without overriding already-set process variables. `.env` and `.env.*` are ignored except `.env.example`. Demo files older than `SMOL_DEMO_TTL_SECONDS` (default one day) are removed when a request arrives. Paid calls stay off unless `SMOL_SPONSOR_CALLS=1` and both sponsor limits are positive integers. Keep private configuration out of commits.

Reset demo on reorder clears its workflow, supplier fact, and integration records. It preserves the session file and the other previews. Cookie expiry alone leaves a file behind. Without `DATABASE_URL`, a missing file means the initial screen on refresh. With Postgres configured, persisted workflow/scenario rows can identify an existing session. File expiry does not establish a database-row retention policy. Do not delete another visitor's state. Stop the process with Ctrl-C. Restarting with the same surviving disk and cookie resumes saved progress.

## Deploy and verify

Vercel is the host. Render is retired. Production `https://smolstuff.vercel.app` serves the dark daily brief without a Vercel login. Temporary host files remain ephemeral; workflow/preview rows use Postgres when `DATABASE_URL` is configured. Commit `0847325` records one approval surviving redeploy; this cleanup did not rerun it. See [ARCHITECTURE.md](ARCHITECTURE.md).

For a complete hosted regression check, verify: new session, approve once, refresh, full receipt once, decline, reset, two separate browsers, and a new deployment that still has the earlier session. Do not claim that passed until those calls succeed. Check narrow mobile layout, keyboard focus, and displayed totals.

## Implementation sequence

1. Preserve deterministic core and add failing behavior tests for the change.
2. Fix safety/state/planning gaps before introducing real business execution.
3. Add one useful AI task behind a scoped replaceable adapter with validated output and disabled-by-default paid execution.
4. Build/test Action Inbox and previews against PRD; keep each scenario isolated.
5. Enable production connectors only after the corresponding decisions and security gates are met.

Document new environment fields, initialization/migrations, storage/recovery and test commands with the implementation. Keep canonical policy, money, inventory and state outside transient agent conversations. Never fabricate a completion or provider evidence record.

## Shared presentation

`ui_theme.py` owns dark CSS tokens, `demo_ui.shell` owns navigation and the page frame, and `inbox.render_inbox` renders reorder into the same shell. Update docs/DESIGN.md with token/interaction changes. The developer preview can call `serve_sessions` with an isolated temporary directory to avoid existing user state and avoid loading local provider credentials. Numeric conversion errors return a styled HTTP 400 page without saving an invalid scenario.
