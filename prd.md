# smolstuff — Product Requirements Document

> An operations team for small businesses. Small but mighty.

| Document field | Value |
| --- | --- |
| Version | 1.0 — scope confirmed; release requirements |
| Updated | October 4, 2026 |
| Product owner | Project owner |
| Audience | Product, design, engineering, and AI coding assistants |
| Scope | Ongoing product: the MVP reorder loop, functional capability previews, and a separate future roadmap |
| Data boundary | Fictional businesses and synthetic operational records in the public demo |
| Delivery | A public, self-guided site. The earlier submission packaging is archived in [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md) |

## How to read this file in the repository

This PRD states intended behavior and acceptance criteria. It does not certify that a feature is implemented.

| Question | Read |
| --- | --- |
| What should the product do? | This file |
| Why is the product shaped this way? | [project_context.md](project_context.md), a supporting reference for product philosophy, architecture intent, and examples |
| Which reorder numbers and screen copy are fixed? | [demo_spec.md](demo_spec.md) |
| What is in the product now, and what is later? | [mvp_scope.md](mvp_scope.md) |
| What does the running code do today? | [README.md](README.md) and [docs/STATUS.md](docs/STATUS.md), then the code and tests |
| What is later, and not a current gate? | [docs/ROADMAP.md](docs/ROADMAP.md) |
| Which file owns a topic? | [docs/DOCUMENT_AUTHORITY.md](docs/DOCUMENT_AUTHORITY.md) |
| Where did the hackathon script go? | [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md) |

If a displayed reorder number disagrees, `demo_spec.md` wins. If a document disagrees about whether something is built, the code, tests, and README win. If they disagree about whether something is required, this PRD wins.

## 1. Executive summary

smolstuff is a privacy-first operations manager for very small businesses. It connects permitted business signals, investigates problems and opportunities, recommends feasible actions, executes within owner-defined authority, and follows work through verification and reconciliation.

The product addresses scattered operational context: supplier terms live in email, inventory lives in multiple records, and capacity, cash, and customer commitments are considered separately. The owner becomes the integration layer and must remember every follow-up.

smolstuff brings those facts into a shared operating loop. The primary public demonstration is a supplier delay that creates inventory risk, followed by an approved alternative purchase and a reconciled receipt. Four compact, functional previews show the same operations-team vision: workshop feasibility, Inventory Detective, local merchant sale rescue, and staffing coverage. The earlier “hackathon demonstration” wording is kept in [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md).

This PRD defines intended behavior and acceptance criteria. It does not certify that a feature, integration, deployment, or security control is implemented. Existing code must be inspected before changes, and completion must be supported by observable evidence.

## 2. Problem, users, and value

### Primary user

An owner-operator of a small retail or product business who also manages purchasing, inventory, supplier communication, customer requests, and coverage. The owner has limited time and may be cautious about AI access to business information.

### Secondary users

- A designated operations worker who supplies receiving evidence or physical counts within granted permissions.
- A visitor evaluating the public demo without connecting a real account. The earlier “hackathon judge” wording is in [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md).
- Participating merchant agents in the future sale-rescue network, operating within their own business boundaries.

These are role hypotheses, not validated customer research. The initial product uses a fictional retailer with workshops. Other businesses may reuse the engine later; industry-specific behavior is outside the initial release.

### Jobs to be done

| Situation | User need | Desired outcome |
| --- | --- | --- |
| A supplier changes delivery terms | Understand the impact without manually checking every system | Risk is detected and a feasible response is prepared |
| A purchase exceeds standing authority | Make one informed decision | Exact terms are approved once and execution resumes |
| An order is confirmed | Know whether the operational problem is actually resolved | Receipt is verified, inventory is reconciled, obligations are tracked |
| A customer proposes an event | Know whether the business can and should accept | Materials, capacity, timing, and contribution are considered together |
| Stock records disagree | Find supported explanations without guessing | Evidence-based corrections and unresolved discrepancies remain visible |
| Internal stock cannot save a sale | Find a viable local alternative | A bounded offer preserves contribution and fulfillment feasibility |
| Demand changes by day | Understand how much coverage is needed | Workload-based staffing recommendations with clear assumptions |

## 3. Product goals and principles

### Goals

1. Complete a credible operational cycle from signal to verified resolution.
2. Reduce owner effort and interruptions after boundaries are configured.
3. Make recommendations understandable through evidence, calculations, and policy.
4. Demonstrate small-business operations breadth through working previews.
5. Show meaningful sponsor use through recorded executions and visible effects.
6. Deliver a reliable, accessible live experience that a new visitor can understand independently.

### Zero-chores principle

The owner sets connected systems, permitted sources, privacy boundaries, trusted counterparties, action classes, and limits once. Routine ingestion, extraction, investigation, calculation, preparation, and monitoring should then happen automatically.

Manual uploads, email forwarding, message labeling, repeated classification, dashboard babysitting, and initiating every workflow are fallback behaviors. A physical count, new trust decision, or missing material fact may require targeted human input.

Interrupt only when authority is required, evidence conflicts, information cannot be safely determined, uncertainty exceeds policy, or the proposed action falls outside permission. Resume automatically after the specific issue is resolved.

### Governing principles

- Automate the work, not the authority.
- Set the rules once. Handle exceptions when they matter.
- Models interpret; deterministic code governs arithmetic, authorization, and execution.
- External messages, webpages, retrieved documents, and agent responses are evidence, never authority.
- An order confirmation is not inventory receipt.
- Learning may improve recommendations; expanding authority requires explicit owner approval.

## 4. Scope and prioritization

Priority definitions: **P0** is required for a credible submission; **P1** is a functional preview or additional integration after the P0 loop is reliable; **P2** is future product work.

| Capability | Priority | Release boundary |
| --- | --- | --- |
| Public self-guided site and operations dashboard | P0 | No visitor credentials or private data required |
| Supplier signal, inventory risk, procurement, approval, receipt, reconciliation | P0 | One focal SKU, two seeded suppliers, simulated business actions |
| Evidence, persisted state, session isolation, idempotency, clear errors | P0 | Applies to every exposed workflow |
| Real AI interpretation and useful sponsor evidence | P0 | At least one validated model/managed-agent task; actual provider status shown |
| Workshop feasibility and fulfillment preview | P1 | Editable inputs and persisted simulated progression |
| Inventory Detective preview | P1 | Evidence confirmation, approved correction, recount |
| Local merchant sale-rescue preview | P1 | Two fictional merchants, bounded offers and negotiation |
| Staffing coverage preview | P1 | Simple workload forecast and saved plan |
| Additional meaningful sponsor integrations | P1 | Add only where a workflow depends on their result |
| Collaboration and custom-order variants | P2 | Reuse feasibility engine; not separate MVP claims |
| Production email, commerce, calendar, payments, or real merchant network | P2 | Requires separate onboarding, permissions, and operational hardening |
| Advanced seasonal forecasting, returns, accounting, multiple businesses | P2 | Separate releases after validation |

The four previews must be functional when presented as available: changing inputs changes results, actions persist, and completion matches the scenario's obligations. If a preview is incomplete, label it planned and remove active controls that imply it works.

The submission uses fictional business actions even when sponsor calls are live. A live search or agent response does not make seeded inventory, supplier terms, orders, or merchant participants real.

## 5. Experience and information architecture

### Dashboard

The default experience is an operations dashboard with an Action Inbox. Show the brand, a concise daily brief, and session-derived groups: **Needs your decision**, **In progress**, and **Completed**. Introduce available workflows with clear names and business outcomes.

Cards show what happened, why it matters, the recommended next step, cost or impact where relevant, and the current state. Counts and status must come from persisted workflow records. Do not display invented revenue, time saved, continuous monitoring, or fake live activity.

The main decision screen has one clear primary action, a secondary decline/back action, and one expandable evidence control. Detailed tools and calculations belong in the evidence panel. Sponsor branding must reflect execution records.

### Language and design

Confirmed UI direction: modern, clean, sleek, dark mode, stylish and gently cute. Use the shared charcoal/lavender/mint design system in [docs/DESIGN.md](docs/DESIGN.md) on the dashboard, all workflows, evidence, empty states and errors. The playful accent is subordinate to readable business decisions. No visual element may imply unverified live monitoring or realized business impact.

Use plain owner-friendly language, readable typography, restrained color, strong hierarchy, adequate spacing, and responsive layouts. Distinguish approved, blocked, pending, and completed states with text as well as color. Maintain visible keyboard focus, labeled inputs, understandable validation, and loading/error feedback.

The core journey must be usable on mobile without horizontal page scrolling. Target WCAG 2.2 AA for implemented screens; assess keyboard navigation, contrast, form labels, and status announcements. Do not claim certification from an automated check alone.

### Demo entry

Show a concise notice that data and business transactions are fictional. **Start interactive demo** simulates a permitted signal arriving through a configured monitoring rule. Visitors do not upload or classify the message. This demonstrates automatic ingestion behavior while transparently using a manual demonstration trigger.

Each visitor gets an isolated session. Refresh resumes it; reset clears only that visitor's scenario state and restores fixtures.

## 6. Functional requirements and acceptance criteria

### FR-01 — Automatic ingestion and privacy boundaries

**P0 demo:** ingest a synthetic supplier event through a preconfigured source rule. Preserve its origin, timestamp, processing status, and simulation label. Extract only allowed operational fields into a validated schema.

**P2 production:** support provider events or polling, metadata-first filtering, approved senders/categories, blocked sources, minimized content retrieval, revocation, and configurable retention. Dedicated operations mailboxes or provider-side routing are privacy options. Do not describe application filtering as provider-enforced isolation when connector scopes are broader.

Acceptance:

- A permitted event starts investigation without another owner instruction.
- Duplicate events do not create duplicate workflows.
- Unrelated or blocked content is not passed downstream.
- Extraction preserves source evidence and distinguishes unknown values.
- A message requesting secret disclosure or a higher spending limit causes neither.

### FR-02 — Inventory velocity and reorder planning

Calculate demand, availability, days of supply, and replenishment risk in application code. Recent sales velocity supports a transparent replenishment estimate; it is not a sophisticated seasonal forecast.

```text
average_daily_demand = units_sold / complete_days_observed
available_now = sellable_on_hand - existing_reservations
days_of_supply = available_now / average_daily_demand
reorder_point = expected_demand_during_lead_time + safety_stock
inventory_position = sellable_on_hand + confirmed_inbound - committed_demand
```

Use consistent quantity definitions; never subtract commitments twice. Inbound stock contributes to deadline feasibility only after expected receipt. Handle zero demand, sparse history, stale counts, unavailable units, and lead-time uncertainty explicitly.

Acceptance for the primary fixture:

| Input or output | Value |
| --- | --- |
| SKU | `DEMO-SKU-001`, quiet linear switch |
| Sales over ten complete days | `[1, 2, 0, 1, 1, 2, 1, 0, 2, 1]` |
| Total / daily velocity | 11 units / 1.1 units per day |
| Available / reserved / warehouse / open PO | 21 / 0 / 0 / 0 |
| Supplier A lead time | 14 → 35 days |
| Days of supply | 21 / 1.1 ≈ 19.09 days |
| Projected gap | 35 − 19.09 ≈ 15.91 days |
| Immediate demand shortage | 1.1 × 35 − 21 = 17.5 units before safety stock |

The UI rounds to about 19 days of supply and a 16-day gap. Explain that Supplier B's 100-unit minimum exceeds the immediate shortage. Do not call that quantity an optimized forecast. Trend, seasonality, and more advanced replenishment quantities are future enhancements with data requirements.

### FR-03 — Investigation, alternatives, and procurement economics

Check warehouse stock, reservations, open orders, and arrival timing before recommending an external source. Candidate suppliers require product/variant compatibility, quantity, MOQ, total landed cost, timing, source freshness, and trust status.

The primary seeded offer is 100 units at $1.82, merchandise $182, shipping $7, total $189, estimated delivery six days. No additional taxes or fees exist in this fixture. Unknown fees in future inputs must remain unknown rather than silently becoming zero.

Acceptance:

- Internal checks are visible in evidence and influence feasibility.
- The subtotal and total are calculated with decimal or minor-unit arithmetic.
- Public search results are labeled discovery evidence, not confirmed stock or reserved inventory.
- The seeded $189 offer remains explicitly seeded even when research is live.
- A critical mismatch or missing term blocks execution or produces a specific clarification.

### FR-04 — Authority, approvals, and execution

Support the product concepts **Observe**, **Prepare**, and **Guarded Auto**. The demo can expose one preconfigured policy without building full onboarding or a settings console.

The example purchase auto-executes only if the full total is strictly below $40 and supplier, known SKU, price tolerance, quantity, evidence, and aggregate-budget checks all pass. At exactly $40, approval is required. Splitting purchases must not bypass aggregate limits.

New suppliers, unsupported inventory write-offs, customer commitments, policy expansion, and sensitive actions require the applicable explicit authority. Routine analysis and preparation do not require repeated approvals.

Acceptance:

- The $189 proposal waits for one approval; the other fixture checks pass.
- Approval binds to exact recipient, item, quantity, currency, total, and material terms or a versioned payload hash.
- Changed terms invalidate approval; authority is rechecked before execution.
- Decline submits no order and preserves inventory.
- Duplicate approval creates one simulated order.
- Any below-limit test still requires all other policy checks to pass.

### FR-05 — Verification, receiving, reconciliation, and recovery

Persist the lifecycle from detection through investigation, decision, authorization, execution, confirmation, awaiting receipt, reconciliation, and completion. Include blocked, declined, failed, and recovery outcomes. Replanning does not create authority.

Acceptance:

- Matching confirmation leaves available stock at 21 and the workflow awaiting receipt.
- Full simulated receipt adds 100 once, changes available stock to 121, and closes the obligation.
- The accelerated receipt does not subtract six days of sales; show this simulation assumption.
- A 97-unit receipt updates stock to 118 and leaves three outstanding. A later three-unit receipt changes it to 121 and permits closure.
- Repeated receipt events never double-count inventory.
- Timeout or uncertain submission triggers status checking before retrying.
- Unresolved obligations remain visible; a claim draft is not a resolved shortage.
- Core pause/resume survives browser refresh and server restart within configured durable storage.

The short-receipt branch may remain an additional path if the public core demonstrates full receipt; document whether it is exposed or only verified internally.

### FR-06 — Workshop feasibility functional preview

Visitors adjust attendees and days until an event. Evaluate materials, MOQ, arrival deadline, labor/capacity assumptions, costs, and contribution. Return feasible, conditional, blocked, or needs clarification with reasons.

Default fixture: 20 attendees; event in seven days; revenue $1,500; 18 available kits; $20 consumed cost per kit; buy in packs of ten; supplier ETA three days; labor $300; other variable cost $100; calendar and staff available; no competing consumption.

Acceptance:

- Two missing kits require purchase of ten; cash outlay is $200.
- Materials consumed cost $400; contribution is $1,500 − $400 − $300 − $100 = $700.
- Eight kits remain after event completion. Purchase cash outlay is not added again to consumed cost.
- A two-day deadline with missing kits blocks acceptance under the three-day ETA.
- Customer commitment and purchase permissions are distinct, even when reviewed together.
- Simulated approval, receipt, event completion, and reconciliation persist and are idempotent.

Collaboration inquiries and custom orders are future variants of this engine. Do not claim separate implemented workflows.

### FR-07 — Inventory Detective functional preview

Investigate a separate scenario: system quantity 20, physical count 16, workshop attendance 12, recorded workshop usage nine. Preserve facts, inferences, and unknowns.

Acceptance:

- The four-unit discrepancy is factual; three potentially unrecorded workshop units are an inference until confirmed.
- Confirmation of actual usage supports a proposed three-unit correction requiring authority.
- Approved correction changes system quantity to 17; one remains unresolved against the original count of 16.
- A subsequent recount of 17 resolves the case; preserve the original count and investigation history.
- No theft, loss, or consumption is invented as a proven cause.
- The scenario does not alter the primary reorder fixture.

### FR-08 — Local merchant sale-rescue functional preview

Compare two fictional merchant offers and demonstrate bounded counteroffers. Offers are tentative until the authorized transaction is confirmed. Keep internal ceilings private unless specifically allowed to disclose them.

Default sale price $119; payment fee $4; other variable cost $5; minimum contribution $15. Merchant A acquisition $79 plus transfer $10; Merchant B acquisition $76 plus transfer $7. Default contributions are $21 and $27. Counteroffer floors are $79 and $76 respectively.

Acceptance:

- Changing price or valid offer terms recalculates contribution deterministically.
- A $90 sale qualifies neither offer under the minimum contribution.
- Negotiation respects stated floors and bounded rounds; it does not fabricate live merchants.
- Simulated approval, transfer, customer fulfillment, and reconciliation are required before completion.
- External disclosure is limited to necessary item, quantity, timing, and fulfillment facts.

A future real network requires counterparty onboarding, permissions, offer expiry, reservation confirmation, dispute handling, and verified fulfillment.

### FR-09 — Staffing coverage functional preview

Forecast required workload and coverage, leaving individual employee scheduling to the owner. Use simple history and documented work assumptions.

Default histories: Tuesday `[4, 5, 7, 4, 6]`; Saturday `[30, 34, 36, 38, 42]`. Each transaction requires 15 minutes, each pickup 15 minutes, baseline work one hour, and a workshop four staff-hours. Owner capacity defaults to six hours; additional coverage is expressed in four-hour blocks.

Acceptance:

- Saturday averages 36 transactions. With a workshop and no pickups, workload is 36 × 0.25 + 1 + 4 = 14 hours.
- Six owner hours leave eight additional hours, or two four-hour blocks.
- Changing day, event selection, or owner capacity recalculates recommendations.
- A saved coverage plan persists; saving does not schedule a person or cut anyone's shifts.
- Describe this as workload forecasting, not a validated demand-prediction model.

### FR-10 — Evidence and honest execution status

Each tool execution records provider, task, result summary, effect on the workflow, timestamp, outcome, and **live**, **simulated**, or **replayed** status. Record errors and fallback use. Minimize excerpts and redact secrets.

Acceptance:

- The evidence panel explains sources, calculations, assumptions, policy outcome, approvals, confirmation, receipt, and remaining obligations.
- Failed calls cannot generate a live-success badge.
- A configured account, API key, models-list call, or empty agent creation does not prove an operations integration.
- Sponsor output affects a real workflow step; decorative logos and canned transcripts do not count as functional integration.

## 7. Sponsor responsibilities and integration contract

| Tool | Intended product role | Proof required |
| --- | --- | --- |
| ZooWork | Managed operations agent interpreting a case and producing a constrained plan or explanation | A real task returns validated output that affects the case; application policy remains authoritative |
| BAND | Handoff between distinct specialist or merchant agents | The receiving agent acts on the sender's result, with observable coordination |
| Moss | Retrieval over permitted fictional policies, catalog, compatibility, and supplier context | Relevant records are retrieved and cited; authoritative inventory and policy remain in the application store |
| Tavily | Public supplier discovery/research | Real search results and source links are recorded; candidates remain unverified until further checks |
| Novita | Structured extraction or interpretation when chosen as the model provider | Validated extraction from the synthetic supplier message; labeled fallback on failure |
| Browser verification sponsor | Optional product-page observations | Timestamped evidence with limitations; observations are not reservations |
| Entire | Development-session provenance | Relevant build sessions are captured; reviewed before sharing for secrets or identifying context |

The owner has reported accounts for ZooWork, Entire, Tavily, Moss, and BAND. Account creation alone is not integration. The choice of an additional model provider depends on available access and the managed runtime; do not require a redundant service solely to add a logo.

Engineering must prepare placeholder configuration, ignore private credential files, load local environment settings, and document separate hosted settings. Ask for only missing credentials or identifiers one service at a time, with exact dashboard and field names. The owner enters secrets directly into private configuration; do not request them in chat.

Use timeouts, bounded retries, validated schemas, provider quotas, and controlled fallbacks. Public visitors must not trigger unlimited paid calls. Set a configurable per-session call budget and overall quota before launch; the exact values require owner approval if they enable spending. Never silently purchase credits.

## 8. Architecture and data requirements

Preserve the working Python/SQLite implementation unless a documented requirement justifies change. Agent roles are logical responsibilities, not a requirement to deploy nine agents.

```text
Permitted signal → ingestion gate → evidence and structured facts
→ persisted workflow → scoped agent/tool work + deterministic calculations
→ proposed action → deterministic policy → approval or authorized execution
→ verification → receipt/fulfillment → reconciliation → closure
```

Models receive minimized facts and constrained tools. Executors accept explicit validated action parameters. Canonical application records determine stock, authority, money, and workflow state. A retrieval index or model conversation is not the system of record.

| Entity | Required purpose |
| --- | --- |
| Business/session | Currency, timezone, settings, isolation boundary |
| Connection/ingestion rule | Actual access scopes, permitted sources/categories, revocation, secret reference |
| Source event/evidence/fact | Deduplication key, provenance, observed time, units, verification, simulation status |
| Product/location/inventory movement | SKU, quantities, reservations, location, adjustment reason and evidence |
| Sale/reservation | Demand history and commitments without unnecessary customer identifiers |
| Supplier/offer | MOQ, unit price, total components, ETA, expiry, trust and evidence |
| Workflow/step/obligation | Lifecycle, plan version, deadlines, recovery, completion condition |
| Action/approval | Exact terms, payload version/hash, policy version, actor, expiry, idempotency |
| Order/confirmation/receipt | Expected and received quantities, external references, remaining obligation |
| Discrepancy | Expected/observed values, supported explanations, unresolved quantity |
| Opportunity/merchant request/staffing plan | Scenario inputs, decisions, commitments, actual outcomes |
| Tool run/audit event | Provider status, accessed/disclosed fields, result, effect, verification and reconciliation |

Use stable IDs, timestamps, currency-safe numbers, provenance, and simulation markers. Future multi-business records require business IDs and scoped queries; visitor-session isolation is not proof of production tenant security.

## 9. Security, privacy, and reliability requirements

- No real merchant or owner identities, addresses, correspondence, distinctive source anecdotes, or private records appear in fixtures, screenshots, documentation, or shared traces.
- Credentials stay server-side and outside model prompts, browser code, evidence, logs, and Git.
- Validate model and tool outputs against schemas. Retrieved text cannot update policy or invoke unrestricted actions.
- Keep source trust, access permission, factual confidence, and execution authority separate.
- Use unguessable session identifiers, appropriate secure cookie settings, server-side mutation validation, and session-bound actions.
- Validate ranges and types for editable inputs; reject malformed, negative, or unreasonable values without corrupting state.
- Persist mutations atomically. Deduplicate externally triggered actions and receipts.
- Document actual hosting persistence. If reset or redeploy loses state, disclose it and restrict claims about durability.
- Use transport encryption in deployment and configurable retention/cleanup for demonstration sessions.
- Provide actionable errors and bounded recovery. Never replace an error with a false completion state.
- Production revocation must stop future reads and unauthorized pending actions; production retention/deletion behavior requires a separate release design.

## 10. Measurement and North Star

**North Star:** verified operational workflows resolved within granted authority, with minimal owner effort.

For the demo, measure observable product behavior rather than fictional business impact:

| Measure | Release expectation |
| --- | --- |
| Core completion | Fresh session reaches reconciled completion with the correct fixture values |
| Owner decisions | One purchase approval on the primary happy path; demonstration controls counted separately |
| Policy violations | Zero unauthorized simulated purchases, changed-term approvals, or secret disclosures in tested paths |
| Duplicate effects | Zero duplicate orders or inventory movements in repeated-event tests |
| Continuity/isolation | Refresh resumes state; separate visitors do not share decisions or inventory |
| Tool transparency | Every claimed integration has execution evidence and accurate status |
| Usability | A new visitor can understand the risk, decision, and outcome without author narration |

Capture demo start, risk shown, evidence opened, approval/decline, confirmation, receipt, completion, errors, and tool calls using session-safe identifiers. No third-party analytics or personal tracking is required for the MVP.

Later measure resolution rate, elapsed time, owner interruptions, forecast error, unresolved obligations, and realized contribution. Saved sales, avoided stockouts, or time savings require observed evidence and a defined baseline. Do not publish unsupported metrics.

## 11. Release plan and definition of done

### Stage 1 — Reliable core and public deployment

Verify the reorder lifecycle, policy semantics, idempotency, isolated sessions, refresh/resume, and visible evidence. Deploy the site and verify the complete path at its public URL, including configuration and persistence. Deployment is a release gate, not an assumed result.

### Stage 2 — Real sponsor/AI task

Complete the smallest useful model or managed-agent task and relevant research integration. Demonstrate returned output affecting the case and safe handling of malformed output, failure, and quota limits.

### Stage 3 — Functional operations previews

Polish the dashboard and workshop, detective, rescue, and staffing scenarios already present or in progress. Each exposed control must have a tested effect. Protect the core workflow from scenario cross-contamination.

### Historical submission packaging

The stage that described a hackathon submission and an optional video shorter than three minutes was moved on 2026-10-05 to [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md). It is not a current deadline. Stages 1–3 above remain the release plan.

### Release acceptance checklist

Leave an item unchecked until the README or the tests record evidence for it. An unchecked item is an open requirement, not a hidden failure.

- [ ] Public URL is reachable and the primary journey passes on the hosted build.
- [ ] All displayed numbers match the fixture contract.
- [ ] Approval, decline, altered terms, duplicate clicks, refresh, and isolation are verified.
- [ ] Confirmation cannot inflate inventory or prematurely complete the case.
- [ ] Full receipt reconciles once; any exposed shortage path retains the obligation.
- [ ] At least one real AI/managed-agent task is evidenced, or the submission explicitly discloses the gap.
- [ ] Sponsor calls, fallbacks, seeded offers, and business simulations are labeled accurately.
- [ ] Every exposed preview meets its scenario acceptance criteria.
- [ ] Keyboard/mobile/error states are checked.
- [ ] Secrets and identifying context are absent from public artifacts and shared traces.
- [ ] Public call budgets and timeout/recovery behavior are configured.
- [ ] README, scope, demo specification, and this PRD agree about intended and implemented behavior.

## 12. Risks, dependencies, and open decisions

| Risk or dependency | Mitigation / decision |
| --- | --- |
| Time spent wiring every sponsor | Prioritize useful dependencies and a reliable core; defer extras explicitly |
| Account or API access differs by product | Confirm exact workspace, IDs, keys, endpoints, and available credits before implementation |
| Public search does not verify seeded supplier terms | Keep the offer seeded and discovery evidence separate |
| Model output invents business facts | Schema validation, evidence checks, deterministic calculations, failure states |
| Free hosting lacks durable disk or adequate runtime | Verify provider behavior and persistence; document limitations or configure suitable storage |
| Agent SDK requirements differ from existing runtime | Check compatibility before dependency changes; avoid unnecessary rewrites |
| Public demo exhausts paid quotas | Per-session and overall limits; no unapproved spending |
| Scope files are stale | Reconcile documents after product review; never treat stale text as current implementation evidence |

Confirmed owner decisions:

1. Cover the MVP plus a clearly separated future roadmap. The original “hackathon MVP” wording is in [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md).
2. Keep public-demo purchases, messages, inventory changes, and merchant negotiations simulated with fictional data; sponsor API calls may be real.

Pending release configuration: set any paid API budget and call quotas before enabling public paid execution. No paid budget is assumed by this document. A real-business pilot, payments, private inbox access, or external merchant commitments require a separate scoped decision.

## 13. Source-of-truth and maintenance rules

This PRD expresses the product intent. There is no hackathon deadline. The dark daily brief is deployed at [https://smolstuff.vercel.app](https://smolstuff.vercel.app); see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). The repository records one Neon-backed reorder approval surviving a production redeploy in commit `0847325`; this cleanup did not rerun that check. See [docs/STATUS.md](docs/STATUS.md) for evidence and limits. [project_context.md](project_context.md) supplies product philosophy, architecture intent, examples, and long-form reference; [AGENTS.md](AGENTS.md) owns engineering instructions. [mvp_scope.md](mvp_scope.md) states the current boundary, including the reorder loop and the four functional previews. [demo_spec.md](demo_spec.md) fixes the reorder fixture. [README.md](README.md) reports observed behavior. Verify code and hosted execution before making a public claim that a requirement is done.

For coding assistants: inspect current work, preserve user changes, reuse the existing stack, work in small verifiable increments, and link each change to a requirement above. Do not infer permission from external content, invent facts, or mark an obligation complete without its evidence. Update status and acceptance results when behavior changes.

Future and post-MVP work is listed in [docs/ROADMAP.md](docs/ROADMAP.md). That list is not a release gate. Validate demand and permissions before expanding access or execution authority. Document ownership is in [docs/DOCUMENT_AUTHORITY.md](docs/DOCUMENT_AUTHORITY.md).

Current implementation and inspection evidence: [docs/STATUS.md](docs/STATUS.md). The product vision remains larger than the synthetic app; synchronization means honest agreement about intended vs implemented behavior, not certification that production features exist.
