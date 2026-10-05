# smolstuff development and deployment

## Read before coding

Read PRD → MVP_SCOPE → DEMO_SPEC → IMPLEMENTATION_CONTRACT → SECURITY_AND_DECISIONS → INTEGRATIONS. Use project_context for broader product rationale. Read the root AGENTS.md. Current source provides implementation evidence, not permission to lower requirements. Record conflicts and consequential missing choices; proceed with synthetic/configurable boundaries where safe.

## Local setup

Python 3.9+ is declared. The October 4 review ran the 50-test baseline on Python 3.14; the Render manifest pins Python 3.11.11, which was not exercised by this review. Application runtime uses only the standard library. Python imports are `smolstuff`.

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
| Storage | `data/sessions/` beneath repository root, one SQLite file per cookie |
| Cookie | `smol_session`, HttpOnly, SameSite=Lax, one-day Max-Age |
| Provider credentials | None currently read; setting a key alone does nothing |

No `.env` loader, configurable storage-directory setting, automated expiry cleanup or paid-call budget currently exists. These are engineering work, not working settings. Keep private configuration out of commits; the proposed security rules require ignoring it before any credential is entered.

Public-handler reset removes that session's file; single-store test handler resets its signal records. Cookie expiry alone leaves a file behind. Deleted/unavailable file means the initial screen on refresh. Do not delete another visitor's state. Stop the process with Ctrl-C; restarting with the same surviving disk and cookie resumes saved progress.

## Deploy and verify

`render.yaml` defines a free Python web service, compile-only build and the same inbox entry point; service identifier is still `smol-ai`. There is no configured persistent disk/database URL. A manifest is not evidence of a deployed site, and compileall is not a regression suite.

Before release, select/verify hosting persistence and quotas (decision D4), configure HTTPS/secure cookies, run tests, deploy the reviewed revision, and record URL/commit/time. On the host verify: new session, approve once, refresh, full receipt once, decline, reset, two separate browsers, restart and redeploy behavior. Record data-loss limitations if storage is ephemeral. Check narrow mobile layout, keyboard focus/forms/evidence, malformed input and recoverable errors. Do not claim the hosted build passed from a local test run.

## Implementation sequence

1. Preserve deterministic core and add failing behavior tests for the change.
2. Fix safety/state/planning gaps before introducing real business execution.
3. Add one useful AI task behind a scoped replaceable adapter with validated output and disabled-by-default paid execution.
4. Build/test Action Inbox and previews against PRD; keep each scenario isolated.
5. Enable production connectors only after the corresponding decisions and security gates are met.

Document new environment fields, initialization/migrations, storage/recovery and test commands with the implementation. Keep canonical policy, money, inventory and state outside transient agent conversations. Never fabricate a completion or provider evidence record.
