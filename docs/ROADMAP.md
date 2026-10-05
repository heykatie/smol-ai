# Roadmap

Future and post-MVP work. Nothing in this file is a claim that the work is built, a deadline, or permission to connect a real system or spend money. Current acceptance stays in [prd.md](../prd.md). The current boundary stays in [mvp_scope.md](../mvp_scope.md). Observed behavior stays in the [README](../README.md) and [STATUS.md](STATUS.md). Connector and spending gates stay in [SECURITY_AND_DECISIONS.md](SECURITY_AND_DECISIONS.md).

Moved here on 2026-10-05 from the future-roadmap paragraph in `prd.md` section 13. The vision essays remain in [project_context.md](../project_context.md).

## Later product work

- Automatic permitted email ingestion, starting from a connector event or background poll rather than a demo button. The privacy gate is described in project context section 6.
- Configurable autonomy and privacy modes.
- Production inventory and commerce connections.
- Trend-aware replenishment. The current fixture uses a rolling average only.
- Collaboration inquiries and custom orders as variants of the feasibility engine, not separate workflows.
- Live merchant coordination. The demo uses two simulated merchants.
- Deeper staffing forecasts. Saving a plan still must not schedule a person until that product exists and is authorized.
- Returns and refunds.
- Supplier reliability learned from promised versus actual price, quantity, and dates.
- Learning from actual outcomes, without treating repeated approvals as new permission.

## Explicitly not in the current build

These exclusions are also listed in [mvp_scope.md](../mvp_scope.md). They stay out until the core loop is reliable and the matching security decision is made:

- Account onboarding
- Production payments
- Live email or Shopify
- Analytics dashboards
- Live supplier-page checks
- A public paid-call budget

A hosted session that survives a redeploy is an open storage decision in [ARCHITECTURE.md](ARCHITECTURE.md), not a completed roadmap item.
