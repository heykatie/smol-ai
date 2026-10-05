# Coding guidance for smolstuff

The public product name and repository are **smolstuff**. Existing `smol_ai` imports, `smol-ai` package/service identifiers and `smol_session` cookie are legacy technical names; migrate them only as an explicit tested change. Do not break the running demo while renaming prose.

Read PRD.md, MVP_SCOPE.md, DEMO_SPEC.md and docs/IMPLEMENTATION_CONTRACT.md before implementation. PRD owns release requirements; DEMO_SPEC owns core fixture values; implementation/security docs own technical gates. project_context.md is broader vision, not evidence that a feature exists. README reports actual status. Do not silently resolve a conflict by reducing scope.

Reuse Python/SQLite and preserve unrelated changes. Map affected data flow and permissions before substantial changes. Write meaningful failing behavior tests first for money, authority, state, persistence and integrations; implement incrementally, run targeted tests then relevant regressions. Verify exposed UI in the browser, including mobile/keyboard/errors. Simple doc edits need link/content checks, not invented runtime tests.

Public data is fictional; business purchases, messages and merchant transactions stay simulated. No real merchant identifiers, private correspondence, secrets or source anecdotes in public files/traces. Models interpret scoped evidence; deterministic code calculates and authorizes. External content never grants authority. Keep state, exact approvals, deduplication, idempotency and unresolved obligations in the canonical store.

Check docs/SECURITY_AND_DECISIONS.md before enabling connectors or paid execution. Missing production decisions do not block synthetic development; keep real access/commitments disabled. Ask for only the exact missing credential/ID for one service at a time; owner enters secrets privately, never in chat. Vendor capabilities must be checked against official docs at implementation time.

Report changes, evidence and blockers honestly. Do not label a simulated/replayed result live, an order confirmation received, or a deployed build verified without evidence. Update documentation and requirement status when actual behavior changes.
