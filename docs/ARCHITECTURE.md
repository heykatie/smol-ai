# smolstuff architecture

Source re-inspected at `7cd4647` for storage and sponsor-call wiring. Hosting/database setup and the single redeploy result below are repository-recorded evidence, not fresh dashboard or runtime verification. See [STATUS.md](STATUS.md) for inspection scope.

## What stays

| Piece | Current code | Keep |
| --- | --- | --- |
| Product name and package | `smolstuff` | Yes |
| Business rules | `money`, `policy`, `terms`, `inventory`, `lifecycle`, `reorder`, `ops_demos` | Yes. These stay deterministic Python. |
| Screens | Server-rendered HTML in `demo_ui.py` and `inbox.py` | Yes for the current product. A separate frontend is not required to host this. |
| Reorder and four previews | Inbox routes and scenario store | Yes. Public purchases, messages, and merchant actions stay simulated. |
| Sponsor calls | Tavily research, Novita extraction, and ZooWork explanation behind the local sponsor gate; prior provider results were not rerun | Yes. Paid public calls stay off until a budget exists. |

## Local and hosted adapters

Locally, the app is a long-running `http.server` process and each visitor's state is a SQLite file under `data/sessions/`. The recorded Vercel configuration points `DATABASE_URL` at Neon, so the workflow and preview rows are in Postgres instead of that temporary disk.

| Piece | Today | Hosted direction |
| --- | --- | --- |
| HTTP entry | `python -m smolstuff.inbox` on port 8765, and a stdlib WSGI `app` in `app.py` | One Vercel Python Function. The WSGI callable is the adapter. Flask stays a fallback only if a preview deploy rejects the stdlib app. The domain modules do not move to JavaScript. |
| Workflow execution | `WorkflowStore` state machine in process | Same Python transitions. The approval pause is a saved state, not a second orchestrator. Vercel Workflow is not needed for this loop. |
| Database | SQLite without `DATABASE_URL`, session-scoped Postgres with it | One hosted relational database. Every row carries the visitor session id. Tests keep using SQLite so they do not require a network database. |
| Authentication | `smol_session` cookie, not a login | Unchanged for the public demo. Owner accounts are a later release. |
| Business isolation | Local files or Postgres visitor session ids, not authenticated business identity | Session scoping in one database. That is not production multi-business security. A `business_id` comes with real onboarding. |

## Hosting decision

Vercel Hobby is the selected plan. Render is retired, and `render.yaml` is removed. Production serves the dark daily brief at `https://smolstuff.vercel.app`. Neon Free is connected to the Vercel project in the Washington, D.C. region. The app uses it when `DATABASE_URL` is set. Local development stays on SQLite when that variable is empty. Commit `0847325` records one production check: a reorder was approved, the app redeployed, and the same session was still awaiting receipt with stock at 21. The commit was authored October 4, 2026 in America/Los_Angeles (October 5 UTC). This cleanup did not rerun the check or inspect the dashboard.

## Database

Neon Free is repository-recorded as provisioned and connected. It is $0, with 100 compute-hours and 0.5 GB per project each month, and it sleeps after 5 minutes idle. Do not create a second database. The local demo keeps using SQLite until `DATABASE_URL` is present.

## Recorded plan and cost decisions

- The owner selected the Vercel Hobby plan. It is $0 and includes 1 million function invocations and 4 active CPU-hours per month. Hobby is personal, non-commercial use only ([Hobby plan](https://vercel.com/docs/plans/hobby), [fair use guidelines](https://vercel.com/docs/limits/fair-use-guidelines#commercial-usage)). If smolstuff is used for financial gain, the project has to move to Pro at $20 per month before that use. The project exists. Neon Free is connected. Launch pricing applies only after an upgrade: $0.106 per compute-hour and $0.35 per GB-month.
- Tavily, Novita, ZooWork, Moss, and BAND are separate bills. Anonymous calls stay off unless `SMOL_SPONSOR_CALLS=1` and both a global limit and a per-session limit are set. A key alone does not place a call. Sponsor counters use the same Postgres database when `DATABASE_URL` is set, so instances sharing that database share the call-count caps. Without `DATABASE_URL`, counters stay in a local SQLite file. It is a call-count limit, not a monetary cap.

## Not in this migration

Production mailbox, commerce, payments, owner login, and a real merchant network stay later releases. Each needs its own permission decision. The public demo does not gain those by being hosted.
