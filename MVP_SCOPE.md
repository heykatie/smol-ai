# smolstuff release scope

This file summarizes [PRD.md](PRD.md). It separates implemented behavior from required and optional work. It does not override the PRD. [DEMO_SPEC.md](DEMO_SPEC.md) owns core fixture values; [docs/IMPLEMENTATION_CONTRACT.md](docs/IMPLEMENTATION_CONTRACT.md) owns technical behavior. The broader vision stays in [project_context.md](project_context.md).

## Inspected baseline

At commit `2dc9093610c874179bc14a870ae3b9ad8f0f72b0`, Python and SQLite run one simulated procurement case for a fictional retailer, one SKU, and two seeded suppliers. No live mailbox, model, search, merchant, or sponsor calls are implemented. A hosting manifest is present; deployment has not been verified by this review.

The public path is Start interactive demo → lead-time extraction → inventory risk and internal checks → seeded $61 recommendation → one approval or decline → simulated purchase and matching confirmation → full receipt → reconciliation and closure. Confirmation leaves available stock at 21; receipt changes it to 121. Refresh resumes while the database remains available. Duplicate signals, approvals, and receipts have regression coverage.

A 97-unit receipt branch is implemented in the core and action handler and tested, but the awaiting-receipt page renders only a full-receipt button. Calling the short action leaves three units owed and stock at 118; receiving the remaining three completes at 121. It is not currently a discoverable public UI branch. This is receipt reconciliation, not the separate usage-investigation preview.

## P0 — next release requirements

1. Preserve and verify the complete core loop above, isolated visitor state, exact fixture math, idempotency, failure states, and honest execution labels.
2. Provide a self-guided public dashboard and meaningful evidence. Verify mobile, keyboard, errors, refresh, and host persistence before claiming release completion.
3. Add at least one useful, validated AI or managed-agent task with visible evidence and bounded costs. A missing integration remains a disclosed unmet requirement; local parsing is not a live AI task.
4. Apply the security and execution boundaries in the implementation contract before adding any outbound capability. All demo business actions remain simulated.

## P1 — functional previews after P0

Implement workshop feasibility, Inventory Detective usage investigation, local merchant sale rescue, and staffing coverage using PRD FR-06 through FR-09. Each exposed control must change persisted scenario state, display deterministic values, and meet its acceptance criteria. Keep scenarios isolated from the procurement fixture. Incomplete previews are labeled planned and have no controls implying working behavior.

Useful additional sponsor integrations and an exposed short-receipt path are P1. Logical agent roles can be ordinary functions; do not create extra agents merely to fill a diagram.

## P2 — real-business product

Automatic connected-mailbox triage with no routine uploads; production inventory/POS and supplier data; configurable privacy/autonomy onboarding; real external messages and purchases; participating merchant agents; advanced forecasting; returns and accounting. This remains essential product direction, with separate permission and operational gates. The public demo does not prove it works.

## Forecasting boundary

The core fixture uses the simple mean of ten complete days, zero safety stock, zero warehouse/open PO units, and Supplier B's 100-unit minimum. It does not optimize target stock or support weighted/seasonal forecasts. General replenishment must define coverage horizon, pack rounding, time-phased inbound and cash limits before implementation. No speculative formula should silently replace the fixture.

## Definition of done

Use PRD release acceptance and the requirement-to-test mapping in the implementation contract. Never mark a release complete from tests alone: verify the exposed browser journey and hosted persistence, record integration evidence, and disclose unmet gates. The 50 baseline tests passed during the October 4, 2026 review; future changes require fresh results.
