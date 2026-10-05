# Historical hackathon context

Preserved on 2026-10-05 from the files named below. smolstuff is an ongoing product. This archive does not set a deadline, prove a sponsorship, or override [prd.md](../../prd.md), [SECURITY_AND_DECISIONS.md](../SECURITY_AND_DECISIONS.md), or the README.

Sponsor roles here are the intended roles written for the original presentation. A current integration claim has to come from the README, [STATUS.md](../STATUS.md), and a recorded workflow call.

## From `prd.md` header, before 2026-10-05

| Document field | Historical value |
| --- | --- |
| Scope | Hackathon live demo, functional capability previews, and a separate future roadmap |
| Data boundary | Fictional businesses and synthetic operational records throughout the submission |
| Delivery | A public, self-guided live site; an optional demo video shorter than three minutes |

## From `prd.md` section 1

The primary hackathon demonstration is a supplier delay that creates inventory risk, followed by an approved alternative purchase and a reconciled receipt.

## From `prd.md` section 2, secondary users

- A hackathon judge or visitor evaluating the public demo without connecting a real account.

## From `prd.md` section 11, stage 4

### Stage 4 — Submission and optional recording

Prepare clear project documentation and sponsor-role evidence. Rehearse a self-guided live journey and, if time permits, record a video shorter than three minutes. Suggested story: signal and risk → evidence and one approval → confirmation and receipt → completed result → brief functional previews → sponsor roles and trust boundaries.

## From `prd.md` section 12, confirmed decision 1 as originally worded

Cover the hackathon MVP plus a clearly separated future roadmap.

## From `project_context.md` section 2

The original build was shaped as a solo hackathon demo. That history explains the one-loop-first sequence. It does not limit later releases. Do not imply unverified sponsorship, endorsement, or adoption.

## From `project_context.md` section 6

The hackathon simulates an arriving message with Start interactive demo. After that demonstration trigger, the workflow runs without upload or classification. The production product must begin from a permitted connector event or background poll without the owner starting each case.

## From `project_context.md` section 19 — sponsor-tool roles

These are the intended roles selected in the conversation, not claims that integration or current vendor capability has been verified. Confirm official APIs, account access, and limitations when implementing. Keep adapters replaceable.

| Tool | Intended role | Boundary / evidence of meaningful use |
| --- | --- | --- |
| **ZooWork** | Main orchestration/runtime for planning, execution, and approval pauses where supported. | Application state and deterministic policy remain authoritative; demonstrate pause/resume. |
| **BAND** | Coordination and handoffs among specialized agents, optionally local merchant agents. | One agent's result must materially change another's next step. Removing BAND should break meaningful coordination. |
| **Moss** | Retrieval over permitted catalog information, supplier terms, policies, compatibility, and business context. | Retrieval augments the canonical structured store; apply source and business access filters. |
| **Tavily** | Discover external suppliers, products, and relevant current pages after internal options fail. | Search results are candidates, not verified stock or delivery promises. |
| **Browser verification sponsor** | Inspect candidate pages and verify current product details, price, stock, and fulfillment evidence. | Timestamp observations and preserve limitations; page availability is not a reservation. |
| **Novita** | Model inference for structured extraction, interpretation, explanation, or candidate ranking. | Models neither perform authoritative arithmetic nor grant permissions. |
| **Entire** | Development provenance for the Claude/Cursor build process. | Keep its role in development; do not force it into merchant operations or record secrets. |

Prefer a few real, coherent integrations over seven decorative logos. Clearly identify live, seeded, and simulated components and fallback behavior.

The current integration contract, including the proof required before calling a tool live, remains in [prd.md](../../prd.md) section 7 and [INTEGRATIONS.md](../INTEGRATIONS.md).

## From `project_context.md` section 20 — judging script

The steps below are the intended judging story. They are not a claim that every step is live. Current execution status is in [README.md](../../README.md).

### Approximately 90-second demo

1. **Opening:** “Big companies have operations teams. Small businesses have an inbox.” Show the one-time boundaries already configured.
2. A supplier message arrives automatically: lead time changes from 14 to 35 days. Show the minimized fact and its source.
3. The system calculates ~19 days of supply and investigates warehouse stock, POs, and alternatives.
4. Show meaningful agent coordination and current evidence for a candidate supplier; optionally use the local-merchant branch.
5. Explain the illustrative $189 resolution and show the deterministic $40 authorization limit.
6. The owner approves once. The workflow resumes and verifies the order confirmation.
7. Advance through clearly labeled simulated shipment/receipt events. Reconcile the full 100-unit receipt for the shortest successful path.
8. Show the completed outcome, inventory update, audit evidence, and one human decision. Briefly show the shortage/recovery branch if time permits.

Do not silently compress a real shipping delay or call an order “received” because a PO was submitted. Label the full demo run when simulated. A 97-unit receipt must retain the remaining obligation until its resolution is demonstrated.

Fallbacks must be deterministic and visibly labeled. Never present replayed evidence as a fresh live verification. Rehearse the complete story, including decline, failed verification, and unavailable-tool behavior.

## From `project_context.md` section 14

For the hackathon, two seeded merchant agents are sufficient to demonstrate the coordination. Label them as simulated participants; do not imply a live merchant network already exists.

## From `project_context.md` section 22, item 5

Integrate meaningful sponsor roles. Prioritize the tools needed by the loop; verify each dependency before relying on it in judging.
