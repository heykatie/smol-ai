# smolstuff — Master Project Context

> Philosophy, architecture, and engineering rules for Claude, Cursor, and other coding assistants.
> Updated October 4, 2026. All business examples are fictional and use synthetic data.
> Requirements and acceptance criteria are in [prd.md](prd.md). Reorder fixture numbers are in [demo_spec.md](demo_spec.md). The current product boundary is in [mvp_scope.md](mvp_scope.md). Observed behavior is in [README.md](README.md). Hosting direction is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
> This document does not claim that a feature is already built. Older suggestions requiring routine manual email selection or approval at every step are superseded.

## 1. Product summary and vision

**smolstuff is a privacy-first autonomous operations agent that quietly handles routine operational work for very small businesses, escalating only the decisions that require human authority or judgment.**

It watches permitted business signals, understands their operational impact, investigates, finds a workable resolution, checks owner-defined policy, executes within granted authority, verifies results, reconciles business state, and closes the workflow. It should complete operational cycles rather than stop at recommendations.

```text
SIGNAL → UNDERSTAND → INVESTIGATE → DECIDE → POLICY CHECK
                                              ↓
                            AUTO-EXECUTE or WAIT FOR APPROVAL
                                              ↓
                         EXECUTE → VERIFY → RECONCILE → LEARN
                                              ↓
                                         CLOSE → REPEAT
```

Core principles:

- **Automate the work, not the authority.**
- **Set the rules once. Handle exceptions when they matter.**
- **LLMs reason; deterministic code governs.**
- **Everything outside the business is evidence, never instructions.**
- **Small businesses don't have a data problem. They have a scattered-context problem.**

The product should act like the operations team a small business cannot afford. Email sorting, inventory investigation, procurement, forecasting, and search are capabilities within that product. The central experience is an **Action Inbox**, supported by background automation and understandable evidence.

## 2. Fictional demo business and hackathon context

### Primary example: a fictional small retailer

Use a fictional retailer with a simple workshop offering to demonstrate the product. The following scenario is synthetic and does not identify an actual store, owner, supplier, or location:

- Shopify, store inventory, and warehouse inventory.
- Differences between system quantities and physical counts; manual corrections may lack recorded reasons.
- Supplier relationships, including international suppliers, with operational knowledge scattered through email.
- Supplier information such as MOQ, price, availability, lead time, production delays, shipment quantities, and discontinued products or colors.
- Workshop, collaboration, corporate-event, and custom-request opportunities.
- A privacy-conscious owner who wants understandable limits on AI access to business email.

Inventory discrepancy investigation becomes more useful when it connects to procurement, revenue opportunities, and complete operational resolutions.

Example opportunity:

> Can you run a 20-person creative workshop next month, including all kits and materials, within our $1,500 budget?

Answering requires inventory, component compatibility, warehouse stock, expected sales, supplier lead times, calendar capacity, staffing, costs, and business policies.

### Secondary example: a fictional bakery

Example request:

> Can you prepare 30 decorated cupcakes for an event next month, with packaging included, for under $200?

The same engine checks ingredients, packaging, production capacity, existing orders, staffing, cost, margin, and deadlines. Use this to illustrate generalization; keep the fictional retailer as the main demo.

Do not introduce real store or owner names, addresses, locations, contact details, identifiable correspondence, source-conversation links, or distinctive real-business anecdotes into code fixtures, screenshots, documentation, or presentations. Use generic products, invented counterparties, and synthetic records throughout the demo.

### Product direction

smolstuff is an ongoing product. There is no submission deadline. Vercel is the hosting target. The earlier Render plan is retired. The public demo still uses fictional business actions.

The original build was shaped as a solo hackathon demo. That history explains the one-loop-first sequence. It does not limit later releases. Do not imply unverified sponsorship, endorsement, or adoption. The presentation script and sponsor-role table from that period are in [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md).

## 3. Zero-chores product principle

smolstuff must reduce operational work rather than create another layer of AI management.

During one-time setup, the owner defines:

- Connected systems and permitted data categories.
- Trusted senders, suppliers, and participating merchants.
- Blocked sources and prohibited data.
- Privacy mode and retention preferences.
- Autonomous action classes, spending limits, quantity limits, and price tolerances.
- Actions that always require approval and uncertainty thresholds requiring review.

After setup, ingestion, classification, extraction, calculations, investigation, verification, monitoring, permitted execution, and reconciliation happen automatically.

Do not require the owner to routinely upload, forward, label, or classify each email; initiate every workflow; approve harmless analysis; copy information between systems; monitor a dashboard; or answer questions available from permitted sources.

Interrupt only when:

1. Human authority is required by the action or configured policy.
2. Necessary information cannot safely be determined.
3. Evidence conflicts or uncertainty is too high.
4. A consequential action falls outside existing authorization.

A physical count or a genuinely new trust decision may still need human input. Ask once for the specific missing information, then resume automatically.

## 4. Action Inbox and trust UX

Confirmed visual direction: modern, clean, sleek, dark, stylish and gently playful. All screens share the design in [docs/DESIGN.md](docs/DESIGN.md); current feature/provider evidence is in [docs/STATUS.md](docs/STATUS.md). Keep decisions legible, calm and owner-friendly.

The Action Inbox surfaces meaningful exceptions, opportunities, decisions, and completed outcomes. Background work belongs in an expandable activity history.

Each action card should answer:

- What happened, why does it matter, and when is a decision needed?
- What did smolstuff already investigate?
- What resolution is recommended, with cost, timing, and business impact?
- What is verified, inferred, or unknown?
- Which policy allows the action or requires approval?
- What will happen after approval?

Illustrative card:

```text
STOCKOUT RISK — Quiet linear switch

Available: 21 units | Velocity: 1.1/day | Supply: ~19 days
Supplier lead time changed: 14 → 35 days
Projected gap without another solution: ~16 days

Already checked: warehouse, open POs, reservations, approved alternatives
Proposed resolution: order 100 units from Supplier B
Illustrative total: $189 | Estimated arrival: 6 days

Approved supplier ✓ | Known SKU ✓ | Below $40 auto limit ✕
Decision needed: Approve $189 purchase

[Review evidence] [Approve $189] [Decline / choose another option]
```

Provide an expandable **Why smolstuff can do this** panel showing accessed sources, fields passed to models/tools, permitted actions, blocked access, policy results, and approval history. Distinguish provider access granted to the connector from data actually retrieved or disclosed. Make privacy claims from recorded behavior, not decorative badges.

All quantities, prices, suppliers, and forecasts in examples are synthetic demo fixtures, not verified quotes or any real business's operating data.

## 5. Autonomy and minimized approval fatigue

| Mode | Allowed behavior |
| --- | --- |
| **Observe** | Inspect permitted data, classify, extract, calculate, detect, investigate, and explain; no business commitments or external mutations. |
| **Prepare** | Also draft messages, purchase orders, inventory adjustments, and resolutions; create internal tasks. Execution requires approval. |
| **Guarded Auto** | Execute explicitly authorized action classes when all deterministic policy conditions pass. |

Reads, searches, and model calls still obey access and data-disclosure boundaries in every mode.

Example guarded-auto purchase policy:

```text
supplier is allowlisted
AND SKU was previously purchased
AND full transaction total < $40
AND unit-price increase < 5%
AND quantity is within the configured range
AND evidence is sufficiently current and complete
AND configured confidence/verification requirements pass
AND remaining aggregate spending budget permits the purchase
```

The example uses strict inequalities: a $40 purchase requires approval. All limits are configurable, not universal business rules. Prevent multiple small transactions from bypassing aggregate limits.

Always route new suppliers, inventory write-offs, customer commitments, contracts, bank/payment changes, record deletion, permission expansion, and changes to security or autonomous-spending policy through explicit owner approval. Purchases and refunds above configured limits also require approval. Sensitive-data disclosure requires an applicable explicit authorization.

Internal analysis and reversible preparation within granted permissions should run without repeated prompts:

```text
Detect supplier email → extract lead time → update sourced facts
→ recalculate risk → check inventory/POs → investigate alternatives
→ calculate economics → verify evidence
→ ONE meaningful decision: “Approve this $189 purchase?”
```

An approval must bind to a specific action, recipient, item, quantity, total, and material terms. Recheck policy, evidence, and authority immediately before execution. Material changes invalidate the approval. Declining, expiry, or revocation must prevent execution and leave a clear next state.

Learning can suggest a policy change; it must never silently expand authority.

## 6. Automatic email ingestion with privacy boundaries

Manual uploading, forwarding, and message selection are fallback options. The normal workflow starts automatically after one-time setup.

```text
EMAIL PROVIDER / OPERATIONS MAILBOX
→ SMART GATE
→ sender/domain/routing/category policy
→ minimum necessary content retrieval
→ privacy filtering and structured extraction
→ sourced operational facts
→ automatic workflow trigger
```

### Progressive filtering

1. Inspect only permitted sender/domain and routing metadata first.
2. Evaluate configured source and category rules.
3. Retrieve permitted content only as needed for classification/extraction.
4. Remove unrelated conversation, personal details, signatures, and unnecessary identifiers.
5. Validate extracted facts against schemas and associate evidence.
6. Pass minimized facts to downstream agents; keep raw content in a restricted evidence boundary.

Approved categories may include supplier communication, shipping/fulfillment, inventory, workshop or collaboration inquiries, and customer order problems. Exclude personal conversations, newsletters, unrelated marketing, unrelated customer correspondence, and financial/private messages outside configured workflows.

### Trust decisions and privacy modes

Approve an exact sender or domain once, subject to category restrictions. Trusted-source status permits processing; it does not authorize instructions embedded in messages or guarantee their accuracy.

| Mode | Boundary |
| --- | --- |
| **Strict** | Process only explicitly approved sources and categories. Default starting point for a cautious owner. |
| **Smart** | Use permitted metadata/content to identify likely operational mail; respect blocked categories and ask before permanently trusting unknown business sources. |
| **Broad** | Owner explicitly permits wider business-inbox analysis; downstream minimization and action authorization still apply. |

For a newly identified business sender, offer **Allow future messages**, **Allow this message only**, or **Never allow**. Deduplicate these requests. Never inspect prohibited content merely to determine whether it is prohibited; configure the gate's permitted inputs explicitly.

For mixed personal/business inboxes, support a dedicated operations mailbox, business alias, or provider-side automatic routing. Sender/category filtering inside smolstuff must not be presented as provider-enforced mailbox isolation if the actual connector scope is broader.

The public demo simulates an arriving message with Start interactive demo. After that demonstration trigger, the workflow runs without upload or classification. Production ingestion must begin from a permitted connector event or background poll; that work is listed in [docs/ROADMAP.md](docs/ROADMAP.md). The earlier hackathon wording of this paragraph is in [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md).

## 7. Supplier intelligence and business memory

Extract operational changes including MOQ, unit price, currency, availability, lead-time ranges, delays, discontinued variants, substitutes, quantities shipped, partial shipments, invoices, and backorders.

Example minimized fact:

```json
{
  "supplier_id": "supplier-a",
  "sku": "DEMO-SKU-001",
  "fact_type": "lead_time_change",
  "previous_lead_time_days": 14,
  "new_lead_time_days": 35,
  "source_type": "supplier_email",
  "source_id": "demo-email-001",
  "evidence_id": "demo-evidence-001",
  "observed_at": "2026-10-03T16:00:00Z",
  "is_simulated": true
}
```

Retain source, observation time, effective date when known, units, currency, and extraction/verification status. Match supplier products to internal SKUs carefully. Preserve conflicting or superseded facts rather than silently overwriting history. Current verified records should outrank stale retrieval snippets.

Business memory contains structured facts plus permission-filtered retrieval over relevant policies, catalog details, compatibility rules, and supplier terms. A retrieval index is not the authoritative ledger for stock, permissions, orders, or money.

## 8. Shared architecture and agent responsibilities

```text
Email / Shopify / calendar / counts / shipment events
                         ↓
               Connectors + Smart Gate
                         ↓
             Restricted evidence + fact store
                         ↓
               Stateful orchestrator
                         ↓
        Specialized agents + deterministic calculations
                         ↓
                  Proposed action
                         ↓
                Deterministic policy engine
                         ↓
             Authorized execution / approval pause
                         ↓
             Constrained action executor
                         ↓
           Verify → monitor → receive → reconcile
                         ↓
              Audit + learning + closure
```

Logical responsibilities:

| Role | Responsibility |
| --- | --- |
| Email / Supplier Agent | Classify permitted messages and extract sourced supplier facts. |
| Inventory Agent | Evaluate availability, velocity, reservations, incoming stock, and stockout risk. |
| Inventory Detective | Investigate discrepancies and distinguish fact, inference, and unknowns. |
| Procurement / Recovery Agent | Find feasible replenishment or recovery options. |
| Opportunity Agent | Check whether a workshop, custom order, or collaboration can be fulfilled. |
| Sale Rescue Agent | Coordinate bounded requests and offers with participating local merchant agents. |
| Staffing Agent | Forecast workload and required coverage. |
| Margin / Cash Agent | Explain economic tradeoffs using deterministic financial calculations. |
| Verifier | Check transaction-critical claims and actual outcomes against evidence. |

These are logical roles, not a requirement to deploy nine independent agents. Use ordinary functions for the deterministic baseline. Add logical agent handoffs only where useful and verified; the current code does not deploy independent agents. Persist coordination, decisions, and pending work outside transient model context.

## 9. Stateful workflows and genuine completion

Recommended shared lifecycle:

```text
DETECTED → INVESTIGATING → PLAN_READY → POLICY_CHECK
                                        ├─ AUTHORIZED
                                        ├─ WAITING_FOR_APPROVAL → APPROVED
                                        └─ BLOCKED / DECLINED

AUTHORIZED / APPROVED → EXECUTING → VERIFYING
→ MONITORING / AWAITING_RECEIPT → RECONCILING → COMPLETED

Failure or discrepancy → RECOVERY → new plan / necessary approval
Other terminal outcomes: CANCELLED, DECLINED, FAILED
```

Persist enough state to resume after approvals, incoming events, restarts, or tool failures. An external action must have an idempotency key. Deduplicate signals, callbacks, and approvals. If a submission times out, check whether it already succeeded before retrying.

**A purchase confirmation is not receipt of inventory.** It starts monitoring. Receiving, reconciliation, and unresolved obligations determine completion. A parent workflow may close only when required obligations are resolved or explicitly transferred to a tracked follow-up with a defined owner and completion condition; never hide unresolved work behind a green status.

Use bounded retries, deadlines, stale-evidence checks, and recovery states. Replanning does not grant new authority.

Some workflows require zero intervention: a supplier fact changes, forecasts update, no risk is found, and the task closes; or an inventory scan finds no anomaly and records a healthy result.

## 10. Inventory velocity and deterministic planning

Use current stock, location, recent demand, reservations, workshops, open orders, inbound timing, supplier terms, safety stock, reliability, and cash constraints. Keep arithmetic in normal application code.

MVP formulas:

```text
available_now = sellable_on_hand - existing_reservations
days_of_supply = available_now / average_daily_demand
reorder_point = expected_demand_during_lead_time + safety_stock
inventory_position = sellable_on_hand + confirmed_inbound - committed_demand
```

Define each quantity consistently. Do not subtract the same reservation twice or include the same event demand in both baseline demand and event demand. For deadline feasibility, use time-phased availability: an incoming order helps only after its expected receipt date.

Illustrative fixture:

```text
21 available units / 1.1 units per day = 19.09 days of supply
Supplier lead time = 35 days
Projected availability gap = 35 - 19.09 = 15.91 days
Demand over lead time = 1.1 × 35 = 38.5 units, before safety stock
```

Choose order quantity using a defined target coverage horizon, expected demand, inventory position, pack size/MOQ, and cash/storage limits. Round physical quantities appropriately. Explain if MOQ creates excess stock.

Handle zero demand, sparse history, stale counts, lead-time ranges, returns, reserved inventory, and stockout periods that suppress observed sales. Use simple rolling or weighted averages first; add seasonality or advanced forecasting only when data supports it. Display uncertainty rather than false precision.

## 11. Main closed loop: inventory and procurement

1. A permitted supplier message arrives automatically: lead time changed from 14 to 35 days.
2. The gate extracts the operational change and evidence; supplier facts update.
3. Inventory calculations find approximately 19 days of supply and create a risk.
4. Investigate warehouse stock, transfers, reservations, planned workshops, open POs, inbound receipts, and approved alternatives.
5. If internal options cannot solve the problem, discover external candidates within access/disclosure policy.
6. Verify product/variant, compatibility, quantity, price, shipping, and delivery claims. Preserve timestamps and unknowns.
7. Compare landed cost, cash impact, stockout exposure, expected contribution, and excess-stock risk.
8. Prepare the best feasible action and evaluate deterministic authorization.
9. Pause for one specific approval if needed; otherwise proceed under standing authority.
10. Execute the purchase/PO through an authorized integration or clearly labeled demo adapter.
11. Compare supplier confirmation with approved product, quantity, total, and ETA. Route mismatches to recovery.
12. Monitor fulfillment. Ingest receipt evidence or request a physical count if necessary.
13. Reconcile the actual received quantity against the PO and shipment records.
14. Update inventory, open obligations, supplier reliability, and forecasts.
15. Close only after the required verification and reconciliation are complete.

Shortage branch:

```text
Ordered: 100 | Received: 97
→ Inventory Detective checks PO, invoice, packing slip, receiving record, email
→ Evidence confirms 97 shipped
→ Record 97 received under applicable inventory-write policy
→ Track the remaining 3 as a shortage/backorder/claim, not received stock
→ Draft or send an authorized supplier claim
→ Verify replacement, credit, cancellation, or another approved resolution
→ Reconcile remaining obligation and close
```

Recording an evidenced receipt differs from writing off unexplained stock. Both obey their configured action policies. Creating a claim draft alone does not resolve the shortage.

## 12. Inventory Detective

Trigger on physical-count mismatches, partial receipts, unexplained adjustments, or conflicting inventory records. Investigate sales, returns/refunds, workshop consumption, transfers, warehouse movements, purchase receipts, supplier correspondence, and prior adjustments.

Always separate **fact**, **inference**, and **unknown**.

Example:

```text
Fact: system quantity 20; physical count 16; difference -4.
Evidence: workshop had 12 participants; only 9 units of usage were recorded.
Inference: 3 units may have been consumed without an inventory entry.
Unknown: remaining 1 unit has no supported explanation.
Next action: verify workshop usage; propose a sourced correction;
recount/investigate the unexplained unit before any write-off.
```

Do not invent theft, loss, or workshop usage as established causes. Model confidence is not proof. Preserve the original record, reason, evidence, actor, and approval for corrections. Recalculate availability and reorder risk after an authorized adjustment; trigger procurement when needed.

## 13. Opportunity feasibility: “Can I take this?”

Automatically detect a workshop, collaboration, or custom-order inquiry. Extract quantity/attendees, deadline, budget, hard requirements, preferences, and unanswered questions.

Check calendar, capacity, staffing, materials, component compatibility, existing reservations, expected intervening demand, supplier terms, missing supplies, lead time, costs, contribution, and policies.

Return **Safe to accept**, **Safe with conditions**, **Cannot meet requirements**, or **Needs clarification**, with evidence and required preparations.

For a 20-kit workshop, 14 store kits plus 4 warehouse kits means a shortage of 2 before other demand. An MOQ-10 purchase would leave 8 after the event only if no other units are consumed or reserved; include intervening demand explicitly.

Closed loop:

```text
Inquiry → feasibility → prepare response and required actions
→ owner approves customer commitment and any non-authorized purchase
→ reserve capacity/materials → execute preparations → monitor readiness
→ deliver event/order → reconcile consumed inventory, costs, and revenue
→ compare forecast with actual outcome → close
```

Bundle related decisions into one understandable review when useful, while keeping each authorization explicit. Do not promise availability merely because an unconfirmed supplier could provide it.

## 14. Sale rescue with local merchant agents

When internal stock, warehouse transfers, and incoming inventory cannot meet a customer's needs, query participating nearby merchants about a specific transaction.

Example request:

```json
{
  "item_requirement": "compatible quiet linear switch",
  "quantity": 1,
  "deadline": "customer-required same-day deadline",
  "radius_miles": 8
}
```

The outgoing request above excludes the internal acquisition ceiling. Store that ceiling in local policy only and validate the outbound payload before disclosure. Share only fields required to obtain a useful quote. Offers should include item/variant, quantity, price, fees, fulfillment location, timing, expiry, and counterparty identity.

Evaluate compatibility, availability, travel/transfer time, total cost, seller trust, evidence freshness, and contribution. Allow bounded counteroffers for this specific transaction. Limit rounds, quantities, price range, time, and data disclosure.

A candidate offer is tentative until policy authorization and reservation/transaction confirmation. Negotiation must not create a binding commitment outside granted authority.

Closed loop:

```text
Customer need → internal options fail → local merchant requests
→ compare/verify offers → bounded negotiation → economic/policy check
→ approval when required → reserve/purchase → verify transfer or pickup
→ fulfill customer under approved commitment
→ reconcile inventory, payment, fees, and contribution → close
```

Restrict communications to transaction facts. Do not exchange broad pricing strategies, future retail-price plans, competitor margins, coordinated prices, or unrelated forecasts. Do not disclose customer identity unless fulfillment requires it and sharing is authorized.

For the public demo, two seeded merchant agents are sufficient to demonstrate the coordination. Label them as simulated participants; do not imply a live merchant network already exists. The earlier “for the hackathon” wording is in [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md).

## 15. Staffing demand forecasting

Forecast **how much coverage is needed**, leaving individual scheduling decisions to the owner.

Inputs may include transactions, hourly traffic where available, online orders, pickups, workshop/event calendars, deliveries, day of week, seasonality, holidays, and promotions. Include non-sales workload such as receiving, setup, and cleanup.

| Day | Illustrative demand | Coverage recommendation |
| --- | --- | --- |
| Monday | Very low | Owner-only may be sufficient. |
| Tuesday | Low; 4–7 projected transactions | No additional coverage if capacity and minimum-coverage rules permit. |
| Wednesday | Moderate | One additional employee, 1–5 PM. |
| Saturday | High plus events | Two additional employees. |

Show assumptions, uncertainty, workload hours, and minimum-coverage constraints. Do not infer that a named employee deserves fewer hours or autonomously cut shifts. Respect owner-defined availability and applicable scheduling constraints; do not invent legal rules.

Loop: forecast workload → recommend coverage → owner schedules → observe actual workload → compare forecast with actuals → improve the next forecast. Start with simple deterministic/statistical methods. This is a later capability unless the primary demo is complete.

## 16. Economics: “Should we?” as well as “Can we?”

Evaluate procurement, sale rescue, and opportunities against contribution, cash availability, risk, and capacity. Revenue alone is insufficient.

Illustrative sale-rescue calculation:

```text
Customer price                 $119
Merchant acquisition           -$76
Transfer                        -$7
Payment fee                     -$4
Other variable cost              -$5
Expected contribution            $27
Owner minimum contribution       $15
```

This is expected contribution, not net profit. Define included costs consistently; handle shipping, taxes, duties, fees, and labor where applicable without double-counting.

For procurement, consider MOQ, cash already committed, landed cost, storage, expected demand, stockout cost, dead-stock risk, supplier reliability, and owner limits. For workshops/custom orders, include preparation and delivery labor, materials, capacity displaced, and required purchases.

Use integer minor currency units or an appropriate decimal type. Do not let an LLM calculate transaction totals or invent unavailable cash balances. Missing material cost information should produce a range or a targeted question.

## 17. Other loops and learning

- **Returns/refunds:** receive return → inspect condition → decide sellable/quarantine disposition → calculate refund → policy/approval → execute → verify → reconcile inventory and financial records → close.
- **Supplier reliability:** compare promised and actual price, quantity, and delivery dates. Use observed performance to inform future plans while retaining sample size and uncertainty.
- **Owner preferences:** record reasons for approvals/rejections and improve recommendations. Suggest recurring-rule changes for owner approval; never infer permission expansion from repeated approvals.
- **Forecast feedback:** compare predicted and actual demand, labor needs, costs, and outcomes; update models and assumptions with provenance.

These share the same policy, evidence, workflow, and reconciliation infrastructure. Avoid separate disconnected feature silos.

## 18. Security and privacy architecture

Security should be understandable and demonstrable to an AI-skeptical owner.

### Trust boundaries

- Treat emails, webpages, attachments, retrieved text, and merchant-agent messages as untrusted evidence.
- Extract into constrained schemas; validate types, units, identifiers, and allowable fields.
- External content cannot alter instructions, allowlist itself, change spending limits, request secrets, grant permissions, disable approvals, or authorize transactions.
- Internal retrieved business text is also data unless an authenticated authorized actor changed the actual policy store.
- Keep policy decisions and external execution in deterministic application code outside model control.

### Least privilege and controlled disclosure

- Give each agent only the necessary fields and tools. Inventory analysis does not need personal email or payment credentials; supplier sourcing does not need employee records or the full customer database.
- Keep credentials in a server-side secret boundary. Never include keys in prompts, browser-visible code, evidence excerpts, or logs.
- Use restricted connector scopes where supported and document actual scopes. Enforce tenant/business isolation in database queries and retrieval.
- Apply outbound data rules to model calls, search queries, browser tools, and merchant messages; minimization must happen before disclosure.
- Separate access permission, source trust, factual reliability, and action authority. None substitutes for the others.

### Storage, revocation, and execution

- Minimize raw-content retention; keep restricted originals or minimal evidence references only as required by the configured retention policy.
- Protect stored sensitive data and transport, redact logs, and support disconnection/revocation and defined deletion behavior.
- Stop future reads and pending unauthorized actions when access is revoked. Revalidate authority at execution time.
- Validate sender/counterparty identity where practical; a matching display name or model classification is insufficient.
- Restrict browser/executor capabilities; use explicit action parameters, destination validation, idempotency, and bounded retries.

### Audit record

For each consequential action, record the trigger, accessed sources, disclosed fields, relevant inferences, deterministic calculations, policy version/results, approval actor/time/scope, attempted execution, external confirmation, verification result, reconciliation, and terminal outcome.

Record decision evidence and concise rationale; do not depend on storing hidden model reasoning. An audit log supports accountability but does not itself prevent unauthorized actions.

Include a demo attack fixture that attempts to override a spending limit or request a secret. The expected result is no permission change, no secret disclosure, and no unauthorized action.

## 19. Sponsor-tool roles

The presentation table of intended sponsor roles was moved on 2026-10-05 to [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md). It is history, not proof of an integration. The current contract is [prd.md](prd.md) section 7 and [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md). Observed calls belong in the README. Prefer a few real, coherent integrations over decorative logos, and label live, seeded, and simulated results.

## 20. MVP scope and demo plan

### Required vertical slice

Target **permitted supplier signal → stockout investigation → alternative with evidence → policy/approval → execution → confirmation → receipt → reconciliation → closure**. In the current demo the signal, offer, and business actions are synthetic; supplier terms remain seeded even when optional public research is called. PRD and MVP_SCOPE define release priority; this section does not impose extra independent gates.

Required pieces:

- One fictional demo business, one generic focal SKU, store/warehouse locations, synthetic sales history, and supplier fixtures.
- A configured email boundary and automatic arrival trigger, with simulation labeled when used.
- Structured extraction, source evidence, deterministic inventory/economic calculations, and a policy engine.
- At least one useful validated AI/managed-agent task for the next release; further coordination/research is added where needed. The existing seeded offer remains synthetic.
- Action Inbox, evidence/privacy panel, one approval checkpoint, and durable resume.
- Purchase, confirmation, receipt, and reconciliation adapters; simulated physical events clearly labeled.
- Audit trail, failure/recovery states, and a resettable deterministic fallback.

### P1 functional previews

After P0 is reliable, implement workshop feasibility, Inventory Detective usage investigation, local merchant sale rescue, and staffing coverage against PRD FR-06–FR-09. The implemented short-receipt handler is separate from the cause-investigation preview. Any exposed preview must be functional and persisted; incomplete features remain visibly planned.

Keep full mailbox production integration, broad Shopify write coverage, live payments, a real merchant network, advanced forecasting, and complete returns/accounting integrations outside the initial MVP unless the core loop is already reliable. Unimplemented roadmap cards must be visibly identified as planned; working previews must meet their acceptance criteria.

The local demo now includes the four functional previews named in [prd.md](prd.md): workshop feasibility, Inventory Detective, sale rescue, and staffing coverage. They are simulated workflows, not production integrations. Current sponsor-call status belongs in the README, not in this vision.

The approximately 90-second judging script was moved on 2026-10-05 to [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md). It is not a claim that every step is live. Do not call an order received because a purchase was submitted. A short receipt must retain the remaining obligation. Fallbacks stay labeled. Current execution status is in [README.md](README.md).

## 21. Recommended data model

Use a small canonical relational/document store with explicit relationships. This schema organizes the conversation's requirements into an implementation starting point; adapt names to the actual stack.

All relevant records should carry `business_id`, stable IDs, timestamps, provenance/version fields, and simulation status. Do not mix demo fixtures with live records.

| Entity | Minimum useful fields / purpose |
| --- | --- |
| `businesses` | Name, timezone, currency, autonomy mode, settings. |
| `connections` / `ingestion_rules` | Provider, credential reference, actual access scopes, source/category rules, privacy mode, retention, revocation state. |
| `policies` | Version, allowed actions, supplier/merchant allowlists, transaction and aggregate limits, price/quantity tolerances, required approvals. |
| `source_events` | Source/provider ID, deduplication key, event type, received time, permitted metadata, restricted raw-content reference, processing status. |
| `evidence` / `supplier_facts` | Source link/reference, relevant excerpt or structured claim, SKU/supplier, units/currency, observed/effective/expiry times, verification state, supersession/conflict links. |
| `products` / `locations` | Internal SKU, variants, compatibility, unit of measure, pack size, location identity. |
| `inventory_balances` / `inventory_movements` | SKU/location, sellable/reserved quantities, movement delta/type, reason, source/action, approved actor where required. |
| `sales` / `reservations` | SKU, quantity, time, demand source, commitment/event reference, status; enough to calculate demand without unnecessary customer identity. |
| `suppliers` / `offers` | Supplier identity, allowlist state, product mapping, MOQ, unit price, shipping/fees, lead-time range, quantity, validity and evidence. |
| `workflows` / `workflow_steps` | Type, trigger, state, parent/child relationships, plan version, deadlines, retry/recovery state, linked obligations, completion criteria. |
| `actions` | Exact proposed operation, recipient, items, quantity, currency/total, material terms, input/evidence snapshot, policy result, idempotency key, execution status. |
| `approvals` | Action/version or payload hash, decision, actor/time, authorized scope, expiry/revocation, reason. |
| `purchase_orders` / `receipts` | Lines, expected/confirmed/received quantities, costs, ETA, confirmations, external IDs, invoice/packing-slip evidence, remaining obligation. |
| `discrepancies` | Expected/observed values, investigation evidence, supported/inferred causes, unresolved quantity, proposed correction, resolution state. |
| `audit_events` | Actor/agent/tool, accessed/disclosed data references, policy/approval/action links, outcomes, verification and reconciliation events. |

Later entities: `opportunities` for customer requirements/capacity commitments; `merchant_requests` and `merchant_offers` for bounded negotiation and reservation expiry; `staffing_forecasts` and `actual_workload` for coverage predictions; `returns`, `refunds`, and `supplier_performance` for additional loops.

Store monetary values with currency and safe numeric types; distinguish units from packs. Link claims to evidence and actions to exact approvals. Stock mutations should produce auditable movements. An order awaiting receipt must remain distinct from available stock.

## 22. Implementation priorities and working guidance

1. **Establish the executable contract.** Define demo fixtures, schemas, lifecycle, policy semantics, economics, and completion criteria. Record live versus simulated integrations.
2. **Build the deterministic core.** Inventory math, money math, authorization, approval binding, deduplication, idempotency, and persisted state come before elaborate agent prompts.
3. **Complete the narrow loop with adapters.** Make trigger, approval, execution, confirmation, receipt, and reconciliation work end to end with labeled fixtures.
4. **Add scoped extraction and retrieval.** Preserve provenance, minimize data before model/tool disclosure, and validate outputs.
5. **Integrate meaningful sponsor roles.** Prioritize the tools needed by the loop and verify each dependency before relying on it. The earlier “in judging” wording is in [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md).
6. **Polish the Action Inbox and trust panel.** Clear outcomes, concise evidence, one meaningful decision, understandable uncertainty, and recovery paths.
7. **Rehearse and verify.** Exercise success, denial, duplicate events, restart/resume, altered terms, tool failure, stale evidence, and shortage resolution.
8. **Expand only after the loop is reliable.** Add Inventory Detective depth, merchant negotiation, then opportunity/staffing previews.

The inspected baseline uses Python, the standard-library HTTP server, and SQLite. Reuse that stack for incremental work; production persistence and hosting require separate decisions. Prefer the simplest stack compatible with the existing repository and sponsor integrations. Do not replace working project conventions without a concrete need.

Coding assistants should preserve the current product decisions, distinguish requirements from assumptions, inspect existing implementation before redesigning it, and work in small verifiable increments. Use typed schemas and replaceable integration boundaries. Keep model prompts, deterministic authorization, and executors separate. Do not invent business facts, live integrations, quotes, or completion evidence.

## 23. Acceptance criteria

These describe target behavior, not verified implementation status. PRD defines release gates. The product should demonstrate:

- A permitted supplier signal automatically starts the workflow without manual selection or prompting.
- Blocked/unrelated email content is not passed to downstream agents; extracted claims retain source evidence.
- Deterministic math identifies the illustrative ~16-day gap from 21 units, 1.1/day demand, and 35-day lead time.
- Internal stock, reservations, POs, and alternatives affect the decision.
- Critical product, cost, and fulfillment claims are verified or explicitly marked unknown.
- The $189 action cannot execute automatically under the example strict $40 policy; an eligible lower-cost action can proceed only when every applicable rule passes.
- Approval survives pause/resume but cannot authorize changed terms; denial/revocation prevents execution.
- Duplicate signals, callbacks, or approval clicks do not create duplicate orders or inventory movements.
- Untrusted text cannot change policy, disclose secrets, or authorize execution.
- Confirmation mismatches and failures enter recovery rather than false success.
- Receipt updates actual received inventory; a shortage remains tracked until resolved.
- Completion is supported by verification, reconciliation, and an understandable audit history.
- The owner sees decisions and outcomes without babysitting the system; live and simulated results are distinguishable.

## 24. North Star and longer-term vision

At every implementation decision, ask:

1. Can a normal small-business owner configure smolstuff once and then largely forget about it?
2. Can one business problem enter automatically and reach a verified resolution?
3. Does the system interrupt only when human authority or judgment is needed?
4. Can the owner understand what happened, what smolstuff did, what data it used, what it was not permitted to access, and why a decision is required?
5. Did the resolution improve the business outcome without creating hidden work, unauthorized commitments, or unresolved obligations?

If not, simplify the workflow before adding features.

Track verified workflows resolved, owner time and interruptions per resolution, policy compliance, discrepancy resolution, forecast accuracy, and realized business value. Measure saved sales or avoided stockouts only with appropriate evidence; separate estimates from observed outcomes.

The longer-term product connects inventory, procurement, opportunities, local sale rescue, staffing, and returns into a shared operating layer. Before a promise, it determines whether the business can fulfill it. After a problem, it works to preserve the outcome. Both use the same bounded authority and evidence model.

**Product vision:** smolstuff gives very small businesses the operational support of a larger team, while keeping data access limited, authority explicit, and everyday effort low.

**Pitch:** “Small businesses don't need another AI assistant. They need the operations team they can't afford to hire.”

**Trust promise:** “Most AI products ask small-business owners for more trust. smolstuff is designed to require less.”

## 25. Engineering rules

These rules apply to new work. Do not rewrite a working feature only to claim that it was built test-first. Skip a new test when the change is only copy or styling.

1. Before implementing a feature, identify its PRD requirement and acceptance criteria. Map the affected UI, application functions, storage, integrations, state transitions, and permission boundaries. Reuse the existing architecture. Create or update a compact diagram when it helps.

2. For business logic, workflow transitions, permissions, inventory or money calculations, persistence, and integrations, write or extend a meaningful behavior test before changing the implementation. Run it and confirm that any new failing test fails for the intended reason.

3. Implement the smallest change that satisfies the requirement. Run the targeted tests, inspect the actual result, fix failures, and repeat until the applicable checks pass. Keep existing regression tests intact. Do not weaken an expectation merely to get a pass.

4. Inspect UI changes in the browser, including mobile layout, keyboard use, errors, and displayed calculations. Passing unit tests alone does not establish that the demo works.

5. Before marking work complete, run the relevant regression checks and report what passed, what was inspected, and any remaining blocker. Missing credentials or unavailable services must be reported honestly.
