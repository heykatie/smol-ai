# MVP scope

This file is the build boundary for the solo hackathon demo. The broader product vision stays in [project_context.md](project_context.md). If this file and that vision disagree, this file wins for what gets built now.

## One workflow

One fictional retailer. One product: the workshop supply pack. Two suppliers. Synthetic sales and inventory only.

1. Simulate a permitted supplier email: lead time changed from 14 days to 35 days.
2. Extract that fact into a validated structure. The rest of the message is data and cannot change policy.
3. Calculate a rolling average of recent unit sales, days of supply, and reorder risk in ordinary Python.
4. Check seeded warehouse stock and the open purchase order before choosing an alternative supplier.
5. Prepare an illustrative $61 purchase. Autonomous purchases are allowed only under $40, so this one waits for approval.
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
- confirmed inbound timing
- supplier lead time
- a fixed safety-stock setting
- a target-stock quantity, rounded up to pack size and then to the supplier minimum

Say when a reorder is needed and why the proposed quantity is 100. Do not add seasonality, machine-learning forecasts, or extra precision.

## How it is built

- Reuse the existing Python core and SQLite workflow store.
- Keep permissions and arithmetic out of any model.
- Keep workflow state in SQLite so a browser refresh resumes it.
- One approval click creates one order. A second click returns that order.
- Label every simulated email, order, confirmation, and receipt.
- No sponsor integration is live in this MVP. ZooWork, BAND, Moss, Tavily, browser verification, Novita, and Entire are planned, not connected. The demo uses local adapters.

## Remaining plan

1. Core reorder workflow: implemented.
2. Public self-guided demo: isolated visitor sessions, Start Demo and Reset Demo, synthetic data, no outbound purchases or messages.
3. Execution records: each demo-adapter run stores provider, task, result, effect, timestamp, and simulated/replayed/live status. The decision panel and Built with line read those records.
4. A live sponsor call is added only when a workflow step needs it. Planned tools stay in this README, not in the product UI.
5. Extra workflows and a demo video wait until the deployed demo is reliable.

## Not in this build

Merchant negotiation, staffing, opportunity feasibility, returns and refunds, advanced forecasting, account onboarding, multiple privacy modes, production payments, live email or Shopify, analytics dashboards, and live supplier-page checks.

A labeled short-receipt branch is included. Receiving 97 of 100 keeps the missing 3 units open and does not invent a cause. The rehearsed path is still the full receipt.

## Done when

From a fresh page you can:

1. Start the app.
2. Simulate the supplier email.
3. Read the reorder recommendation.
4. Approve once.
5. Simulate the receipt.
6. See reconciled inventory and a completed workflow.

Also verified: the inventory math, the $40 threshold, decline, refresh/resume, and duplicate-click protection.
