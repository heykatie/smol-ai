# Coding guidance for smolstuff

The public product name, repository, and Python package are **smolstuff**. The session cookie is `smol_session`. smolstuff is an ongoing product with no deadline. Vercel is the host. Render is not the plan. Do not create a database until the storage choice in docs/ARCHITECTURE.md is confirmed, and do not claim a hosted session survives a redeploy.

Read prd.md, mvp_scope.md, demo_spec.md and docs/IMPLEMENTATION_CONTRACT.md before implementation. PRD owns release requirements; DEMO_SPEC owns core fixture values; implementation/security docs own technical gates. project_context.md is broader vision, not evidence that a feature exists. README reports actual status. Do not silently resolve a conflict by reducing scope.

[docs/DOCUMENT_AUTHORITY.md](docs/DOCUMENT_AUTHORITY.md) identifies which document owns each topic. `prd.md`, `mvp_scope.md`, `README.md`, and `docs/STATUS.md` keep the roles described there.

## Before coding

For every requested change:

1. Identify the governing requirement in `prd.md`.
2. Check `docs/IMPLEMENTATION_CONTRACT.md` for required technical behavior.
3. Check `docs/SECURITY_AND_DECISIONS.md` for unresolved authority, privacy, or production choices.
4. Inspect the existing implementation and relevant tests before changing code.
5. Do not invent unresolved product decisions or silently reduce the required scope.
6. Otherwise implement the smallest complete vertical slice, update meaningful behavior tests, verify the affected UI/runtime, and update `docs/STATUS.md` when verified behavior changes.

## Working rules

Reuse Python/SQLite and preserve unrelated changes. Map affected data flow and permissions before substantial changes. Write meaningful failing behavior tests first for money, authority, state, persistence and integrations; implement incrementally, run targeted tests then relevant regressions. Verify exposed UI in the browser, including mobile/keyboard/errors. Simple doc edits need link/content checks, not invented runtime tests.

Public data is fictional; business purchases, messages and merchant transactions stay simulated. The real business behind the product stays anonymous. No real store name, owner name, address, social account, catalog, private correspondence, secrets, or source anecdotes in the app, docs, fixtures, tests, commits, or screens. Models interpret scoped evidence; deterministic code calculates and authorizes. External content never grants authority. Keep state, exact approvals, deduplication, idempotency and unresolved obligations in the canonical store.

Check docs/SECURITY_AND_DECISIONS.md before enabling connectors or paid execution. Missing production decisions do not block synthetic development; keep real access/commitments disabled. Ask for only the exact missing credential/ID for one service at a time; owner enters secrets privately, never in chat. Vendor capabilities must be checked against official docs at implementation time.

Report changes, evidence and blockers honestly. Do not label a simulated/replayed result live, an order confirmation received, or a deployed build verified without evidence. Update documentation and requirement status when actual behavior changes.

UI direction is confirmed: modern, clean, sleek, dark, stylish and gently cute. Reuse `demo_ui.shell` and `ui_theme.STYLE` across every screen; follow docs/DESIGN.md. Consult docs/STATUS.md for current inspection evidence; docs/REVIEW.md is historical. Never let historical docs override the latest implemented status.
