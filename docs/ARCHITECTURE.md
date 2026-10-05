# smolstuff architecture

Inspected at commit `d48c344`. This describes the running code and the hosting direction. It is not a claim that a hosted site or a durable database exists.

## What stays

| Piece | Current code | Keep |
| --- | --- | --- |
| Product name and package | `smolstuff` | Yes |
| Business rules | `money`, `policy`, `terms`, `inventory`, `lifecycle`, `reorder`, `ops_demos` | Yes. These stay deterministic Python. |
| Screens | Server-rendered HTML in `demo_ui.py` and `inbox.py` | Yes for the current product. A separate frontend is not required to host this. |
| Reorder and four previews | Inbox routes and scenario store | Yes. Public purchases, messages, and merchant actions stay simulated. |
| Sponsor calls | Tavily when configured; Novita optional; others not a verified workflow | Yes. Paid public calls stay off until a budget exists. |

## What cannot stay on Vercel as it is

The app is a long-running `http.server` process. Each visitor's state is a SQLite file under `data/sessions/`. Vercel Functions are stateless and do not keep that disk. A redeploy or a different instance would lose or split those files.

| Piece | Today | Hosted direction |
| --- | --- | --- |
| HTTP entry | `python -m smolstuff.inbox` on port 8765, and a stdlib WSGI `app` in `app.py` | One Vercel Python Function. The WSGI callable is the adapter. Flask stays a fallback only if a preview deploy rejects the stdlib app. The domain modules do not move to JavaScript. |
| Workflow execution | `WorkflowStore` state machine in process | Same Python transitions. The approval pause is a saved state, not a second orchestrator. Vercel Workflow is not needed for this loop. |
| Database | One SQLite file per cookie | One hosted relational database. Every row carries the visitor session id. Tests keep using SQLite so they do not require a network database. |
| Authentication | `smol_session` cookie, not a login | Unchanged for the public demo. Owner accounts are a later release. |
| Business isolation | Separate files, not a tenant id | Session scoping in one database. That is not production multi-business security. A `business_id` comes with real onboarding. |

## Hosting decision

Vercel Hobby is the selected plan. Render is retired, and `render.yaml` is removed. Production returned the dark daily brief at `https://smolstuff.vercel.app`. Neon is not provisioned. Session files on Vercel are temporary, so a hosted session is not durable across a redeploy.

## Database choice, not yet provisioned

**Proposed, pending confirmation:** Neon Postgres through the Vercel Marketplace.

- Workflows, approvals, inventory movements, orders, and audit rows need transactions and foreign keys. The current schema is already relational.
- Postgres is the store for hosted use. Local tests stay on SQLite behind the same store calls where the SQL allows it.
- Turso would keep more of the current SQLite dialect. It is a second database vendor and a weaker fit once more than one business shares a database.

Do not create the Neon database until that choice is confirmed. The local demo keeps working on SQLite until the store can talk to both.

## Cost, before any service is created

- The owner selected the Vercel Hobby plan for now. It is $0 and includes 1 million function invocations and 4 active CPU-hours per month. Hobby is personal, non-commercial use only ([Hobby plan](https://vercel.com/docs/plans/hobby), [fair use guidelines](https://vercel.com/docs/limits/fair-use-guidelines#commercial-usage)). If smolstuff is used for financial gain, the project has to move to Pro at $20 per month before that use. No project has been created, because the CLI is not logged in.
- Neon Free, checked on the plans page the same day, is $0: 100 CU-hours and 0.5 GB of storage per project each month. Compute suspends after 5 minutes idle. Launch, only if those limits are exceeded, is $0.106 per CU-hour and $0.35 per GB-month with no monthly minimum. No Neon project has been created.
- Tavily, Novita, ZooWork, Moss, and BAND are separate bills. Anonymous calls stay off unless `SMOL_SPONSOR_CALLS=1` and both a global limit and a per-session limit are set. A key alone does not place a call.

## Not in this migration

Production mailbox, commerce, payments, owner login, and a real merchant network stay later releases. Each needs its own permission decision. The public demo does not gain those by being hosted.
