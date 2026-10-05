@AGENTS.md

## Deployment target: Vercel

- Vercel is the host. Render is not the plan. Do not create a database until the storage choice in docs/ARCHITECTURE.md is confirmed, and do not claim a hosted session survives a redeploy.
- The working Python business logic in `src/` is the asset to preserve. Before proposing a framework or language rewrite, evaluate Vercel's Python support against the existing code (runtime version vs. `requires-python`, entrypoint/ASGI-WSGI shape, SQLite on an ephemeral filesystem, bundle size, request/response limits, cron/background needs) using current official Vercel docs, and report concrete incompatibilities with evidence.
- Prefer thin adapters around the existing deterministic core over rewriting it. Propose a rewrite only for a demonstrated blocker, with the smaller alternative considered first.
- Target UI/API stack (Next.js + TypeScript, FastAPI, existing Python core, Neon) is documented in docs/TARGET_STACK.md. It is planned, not current. Do not start Phase 1+ unless the user explicitly asks. Do not move authority or money rules into Next.
