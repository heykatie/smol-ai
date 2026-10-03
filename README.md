# smol.ai

**An operations team for small businesses. From incoming signal to verified resolution.**

smol.ai is a privacy-first autonomous operations agent designed to connect supplier email, inventory, and business policies, investigate what needs attention, and carry work through to completion. Owners set the boundaries once; the system handles routine work and asks for help when authority or judgment is needed.

> **Automate the work, not the authority.**

**Status:** Planning stage for a solo AI commerce hackathon project. This repository currently contains the product specification and documentation. The application, integrations, and runnable demo have not been added; the workflows below describe the intended implementation.

[Project specification](project_context.md) · [Getting started](#getting-started) · [Roadmap](#roadmap) · [License](LICENSE)

## Why smol.ai

Big companies have operations teams. Small businesses have an inbox.

A supplier changes a lead time. Sales keep moving. Inventory is split between a storefront and a warehouse. A customer asks for something that requires materials, staffing, and a deadline. The owner has to connect those facts, decide what to do, and follow through.

smol.ai is designed to turn those scattered signals into completed operational workflows, with evidence for each decision and clear limits on what the agent can access or do.

The North Star is simple: **Can an owner configure it once, then largely forget about it until a meaningful decision needs their attention?**

## How it works

1. **Detect:** Monitor permitted business signals automatically through configured sources and categories.
2. **Understand:** Extract the minimum operational facts needed, retaining their source and timestamp.
3. **Investigate:** Check inventory, reservations, open orders, supplier terms, and alternatives.
4. **Decide:** Calculate feasibility, cost, cash impact, and expected contribution using deterministic code.
5. **Authorize:** Apply owner-defined rules; request approval only when the proposed action exceeds existing authority or evidence needs review.
6. **Execute and verify:** Carry out the authorized action and compare confirmation with the approved terms.
7. **Reconcile and close:** Track delivery, record actual receipt, resolve discrepancies, and update business state.

The main interface is an **Action Inbox**: what needs attention, what has already been checked, the proposed resolution, and why a decision is required. Supporting evidence and background activity remain available without becoming another inbox to manage.

## Planned hackathon demo

**One supplier delay. One meaningful approval. One complete procurement cycle.**

The demo uses a fictional retailer and synthetic records:

| Signal or decision | Demo value |
| --- | --- |
| Supplier lead time changes | 14 → 35 days |
| Available inventory | 21 units |
| Average daily demand | 1.1 units |
| Estimated supply | About 19 days |
| Projected gap without another solution | About 16 days |
| Proposed alternative purchase | 100 units for an illustrative $61 total |
| Standing purchase authority | Transactions below $40, subject to all other policy checks |

A permitted supplier message arrives automatically. smol.ai extracts the lead-time change, calculates the risk, checks internal options, and investigates an alternative. The owner sees the evidence and one question: **“Approve this $61 purchase?”**

After approval, the workflow resumes, verifies the order confirmation, monitors fulfillment, and reconciles receipt. The demo will advance through clearly labeled simulated shipping events.

**An order confirmation does not complete the workflow.** If 97 of 100 units arrive, Inventory Detective investigates the evidence and keeps the remaining three units tracked until a replacement, credit, or other authorized resolution is verified.

The primary build target is this single reliable loop. All simulated events, seeded records, and replayed verification results must be distinguishable from live integrations.

## Planned architecture

```text
Permitted email / inventory / calendar / receipt events
                         |
              Smart Gate + fact extraction
                         |
          Sourced facts + restricted evidence store
                         |
        Stateful workflow + specialized agent handoffs
                         |
            Deterministic calculations and policy
                         |
           Authorized action / approval pause
                         |
             Execute → verify → reconcile → close
```

The Smart Gate applies source and category boundaries before passing minimized data downstream. Specialized agents investigate and propose actions; ordinary application code controls arithmetic, permissions, and execution.

Workflow state, approvals, orders, inventory movements, and audit events belong in a persistent canonical store. Retrieval supports investigation without replacing authoritative stock or policy records. Persisted state and idempotent actions allow approval pauses, restarts, and retries without duplicate purchases.

Use two or three meaningful agents for the MVP. Select the application framework and database during implementation; no runtime stack is committed in this repository yet.

### Planned sponsor-tool roles

These are proposed integration responsibilities, pending implementation and verification against current vendor APIs.

| Tool | Intended responsibility |
| --- | --- |
| ZooWork | Workflow orchestration and approval pause/resume where supported. |
| BAND | Agent coordination, with one agent's findings changing another agent's next action. |
| Moss | Retrieval over permitted catalog information, supplier terms, and business policies. |
| Tavily | Discovery of alternative suppliers and relevant product pages. |
| Browser verification tool | Inspect candidate pages for current product, price, availability, and fulfillment evidence. |
| Novita | Model inference for extraction, interpretation, and explanation. |
| Entire | Development provenance for the Claude/Cursor build process. |

External search produces candidates. Verification establishes what the available evidence supports. A product page showing stock does not reserve the item or guarantee delivery.

## Privacy and bounded autonomy

**Set the rules once. Handle exceptions when they matter.**

The planned privacy model combines automatic ingestion with persistent boundaries:

- **Scoped access:** Configure permitted senders, categories, systems, and retention. Offer an operations mailbox or automatic provider routing for mixed personal/business inboxes.
- **Data minimization:** Give downstream agents structured operational facts instead of unrestricted email bodies. Limit outbound disclosure to models, search tools, and merchant agents.
- **Deterministic authorization:** Keep spending limits, approved counterparties, quantity limits, and approval requirements outside model control.
- **Untrusted input:** Treat email, webpages, and agent messages as evidence. Their contents cannot grant permissions, change policy, or authorize a transaction.
- **Traceable decisions:** Record accessed sources, policy results, exact approvals, execution, verification, and reconciliation. Show facts, inferences, and unknowns separately.

| Autonomy mode | Intended behavior |
| --- | --- |
| Observe | Read permitted data, investigate, calculate, and explain. |
| Prepare | Also draft resolutions, messages, orders, and internal tasks; execution requires approval. |
| Guarded Auto | Execute explicitly authorized action classes when every applicable policy check passes. |

Approvals bind to specific actions and material terms. Changes to price, quantity, recipient, or other approved terms require reevaluation. Learning may suggest new rules; it cannot silently expand authority.

These are implementation requirements, not claims of audited security or regulatory certification. All public examples use fictional businesses and synthetic data.

## Roadmap

- [x] Document product requirements, trust boundaries, workflows, and MVP acceptance criteria.
- [ ] Build the deterministic inventory, economics, and policy core.
- [ ] Implement persisted workflow state, approval/resume, and duplicate-action prevention.
- [ ] Add scoped ingestion, extraction, retrieval, and meaningful agent coordination.
- [ ] Complete procurement through confirmation, receipt, reconciliation, and recovery.
- [ ] Build the Action Inbox, evidence panel, and resettable demo.
- [ ] Add the partial-receipt Inventory Detective branch.

The broader product extends the same engine to:

| Capability | Intended outcome |
| --- | --- |
| Local sale rescue | Query participating merchant agents, negotiate a bounded transaction, verify fulfillment, and reconcile contribution. |
| Opportunity feasibility | Check materials, calendar, staffing, costs, and deadlines before an owner commits to a workshop or custom order. |
| Staffing forecasting | Recommend required coverage from expected workload; leave individual scheduling to the owner. |
| Returns and supplier learning | Reconcile returns/refunds and compare promised supplier performance with actual outcomes. |

Economics applies across workflows: a saved sale or replenishment order must make sense after acquisition cost, delivery, fees, labor where applicable, and cash constraints.

## Getting started

To explore the current documentation, install Git and clone the repository:

```bash
git clone https://github.com/heykatie/smol-ai.git
cd smol-ai
```

Open the folder in your editor, then read [project_context.md](project_context.md) for the full scope, data model, policy rules, and implementation priorities.

```text
smol-ai/
├── README.md           # Project overview and entry point
├── project_context.md  # Master product and implementation specification
└── LICENSE             # MIT license
```

There are no application dependencies, environment variables, build commands, or test commands to run yet. Setup instructions will be added alongside the executable implementation. Claude/Cursor contributors should use the project specification as the source of truth.

## Validation plan

Before the MVP is marked complete, verify that:

- Permitted signals trigger automatically, and unrelated private content stays outside downstream agent context.
- Inventory and money calculations are deterministic; policy denies actions outside granted authority.
- Approval survives a restart, while changed terms, denial, or revocation prevent unauthorized execution.
- Duplicate events and retries do not create duplicate orders or inventory movements.
- Untrusted content cannot change policy or obtain secrets.
- Confirmation mismatches, missing receipts, and shortages remain visible until resolved.
- Completion is supported by actual verification and reconciliation evidence.

The full acceptance criteria are in [the project specification](project_context.md#23-acceptance-criteria).

## Contributing and feedback

Questions, suggestions, and implementation proposals are welcome through [GitHub Issues](https://github.com/heykatie/smol-ai/issues). Keep contributions focused on the primary workflow, explain how behavior was verified, and update documentation when implementation status changes.

Use synthetic business records in examples and fixtures. Keep credentials, private correspondence, and identifying merchant or customer information out of commits, screenshots, and public reports.

## License

Licensed under the [MIT License](LICENSE).
