# MVP scope

This file is the current product boundary, not a deadline. Requirements are in [prd.md](prd.md). The reorder fixture is in [demo_spec.md](demo_spec.md). [project_context.md](project_context.md) supplies product philosophy, architecture intent, examples, and long-form reference; [AGENTS.md](AGENTS.md) owns engineering instructions. What the code does today is in [README.md](README.md). Hosting direction is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Later work is in [docs/ROADMAP.md](docs/ROADMAP.md). Historical hackathon material is in [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md). Document ownership is in [docs/DOCUMENT_AUTHORITY.md](docs/DOCUMENT_AUTHORITY.md).

The reorder loop below is the core. The four previews are in the local demo and must stay functional. Production email, commerce, payments, and a real merchant network stay later releases. Vercel is the host. The dark daily brief was verified there. The repository records one Neon-backed reorder approval surviving a production redeploy in commit `0847325`; this cleanup did not rerun that check. See [docs/STATUS.md](docs/STATUS.md) for evidence and limits.

## One workflow

One fictional retailer. One product: the quiet linear switch. Two suppliers. Synthetic sales and inventory only.

1. Simulate a permitted supplier email: lead time changed from 14 days to 35 days.
2. Extract that fact into a validated structure. The rest of the message is data and cannot change policy.
3. Calculate a rolling average of recent unit sales, days of supply, and reorder risk in ordinary Python.
4. Check seeded warehouse stock and the open purchase order before choosing an alternative supplier.
5. Prepare an illustrative $189 purchase. Autonomous purchases are allowed only under $40, so this one waits for approval.
6. Show one action card: recommendation, calculation, evidence, and why approval is required.
7. On approval, resume the saved workflow, submit a simulated order, and record a matching simulated confirmation.
8. Offer one labeled demo control to simulate receipt of the full order.
9. Reconcile that receipt, update on-hand inventory, and show the completed workflow with a short activity history.

An order confirmation does not complete the workflow. Completion requires the receipt and the reconciliation.

## Forecasting

Use only:

- a rolling average of recent unit sales
- available store inventory
- reservations
- warehouse stock and open purchase orders
- supplier lead time
- safety stock of zero for this fixture

Say when a reorder is needed. The proposed quantity is 100 because that is Supplier B's minimum, not because a target-stock formula optimized it. Do not add seasonality or a machine-learning forecast.

## How it is built

- Reuse the existing Python core and SQLite workflow store.
- Keep permissions and arithmetic out of any model.
- Keep workflow state in SQLite so a browser refresh resumes it.
- One approval click creates one order. A second click returns that order.
- Label every simulated email, order, confirmation, and receipt.
- A sponsor call is live only after a real workflow call is recorded. A key, a models list, or an empty agent is not that proof. Current status is in the README.

## Also in the local demo

These are the PRD's P1 previews. They use separate synthetic fixtures and must not change the reorder product's 21 units.

1. Workshop feasibility.
2. Inventory Detective.
3. Local merchant sale rescue, including bounded negotiation between two fictional merchants.
4. Staffing coverage. Saving a plan does not schedule a person.

Collaboration inquiries and custom orders remain future variants of the feasibility engine. They are not separate workflows.

## Remaining plan

1. Core reorder workflow: implemented locally.
2. Public URL: [https://smolstuff.vercel.app](https://smolstuff.vercel.app) serves the dark daily brief without a Vercel login. A hosted session can disappear on redeploy.
3. Execution records: each recorded run stores provider, task, result, effect, timestamp, and simulated, replayed, or live status.
4. Sponsor calls stay limited to a step the workflow actually uses. Do not add a logo without that step.
5. A demo video waits until the public demo is reliable.

## Not in this build

Returns and refunds, advanced forecasting, account onboarding, multiple privacy modes, production payments, live email or Shopify, analytics dashboards, and live supplier-page checks. A public call budget is not configured. No paid public execution is approved.

## Short receipt

A labeled short-receipt branch is included in the store. Receiving 97 of 100 keeps the missing 3 units open and does not invent a cause. The rehearsed demo button is still the full receipt.

## Acceptance

The local reorder path is the behavior covered by `tests/`:

1. Start the app.
2. Simulate the supplier email.
3. Read the reorder recommendation.
4. Approve once.
5. Simulate the receipt.
6. See reconciled inventory and a completed workflow.

The same suite covers the inventory math, the $40 threshold, decline, refresh/resume, and duplicate-click protection.

Still open, and not claimed as done: a hosted session that survives redeploy, a provider-wide call budget, and a fresh sponsor call inside this checkout. An earlier Tavily search was reported and was not rerun. Status for those belongs in the README.

## Shared experience

All local screens use the same modern dark UI, responsive navigation, lavender accents, mint status treatments and gently playful smolstuff mark. Design criteria are in docs/DESIGN.md; current synchronization evidence and remaining gates are in docs/STATUS.md. The visuals do not imply that real email monitoring, merchants or purchases are connected.
