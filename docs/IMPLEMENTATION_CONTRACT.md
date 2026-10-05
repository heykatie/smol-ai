# smolstuff implementation contract

Updated October 4, 2026. **Current** means inspected source at `d48c344a485924b2eea9120e7e96ee3260b8e722`; **required** means target behavior, not a claim that a control exists. PRD defines product scope. Build in small increments against behavior tests; keep business actions synthetic in the public demo.

## Existing components and data flow

```text
Browser GET/POST /
  -> inbox.make_session_handler: smol_session cookie -> session SQLite file
  -> InboxApp.route: reorder or one of four persisted synthetic previews
  -> extract.resolve_lead_time: optional Novita -> validated LeadTimeFact or parser fallback
  -> research.research_supplier: optional Tavily sources or labeled fallback
  -> reorder.plan_reorder: seeded inputs -> inventory/money math -> policy result
  -> WorkflowStore: persisted action, approval and transitions
  -> simulated execution -> confirmation -> receipt + inventory movement
  -> shared demo_ui.shell + ui_theme: persisted progress, preview state and evidence -> dark HTML
```

`fixtures.py` supplies stock, supplier offer, sales history and policy. `inventory.py` calculates supply; `money.py` rounds Decimal amounts to cents; `policy.py` separates not-ready evidence from missing authority; `terms.py` hashes purchase terms; `lifecycle.py` defines legal states. `workflow.py` uses SQLite transactions and unique constraints. `inbox.py` combines rendering and HTTP handling. An optional Novita client and Tavily research client are wired. `ops_demos.py` owns the four deterministic preview scenarios and ScenarioStore; `demo_ui.py` renders/routes previews, and `ui_theme.py` owns the shared dark style. There is no connector worker, generic email task extractor, vector retrieval inside the inbox, independent agent runtime, or live inventory/POS adapter.

Current tables: workflows, actions, approvals, executions, confirmations, receipts, inventory_movements, integration_events, workflow_transitions, scenario_state (phase and JSON payload by scenario key). Stock is a caller-supplied fixture baseline plus stored movements, not a synchronized inventory ledger. Policy is supplied by Python; actions store policy result/reasons but not a complete versioned policy snapshot. Each visitor file provides demo separation; it is not production authorization or tenant isolation.

## Required adapter boundaries

Add typed interfaces beside the existing core rather than replacing it. Suggested contracts:

| Interface | Input | Output / failure behavior |
| --- | --- | --- |
| Signal source | Connection ID, granted scope, cursor | Source events; retryable errors, auth revoked, cursor expired; never policy updates |
| Gate | Metadata, source/category rule version | Allowed fields or reject/quarantine; no blocked body retrieval |
| Extractor | Minimized permitted content, mapped supplier/SKU | Schema-valid facts with evidence IDs; unknown/conflict instead of guesses |
| Inventory reader | Business, SKU, location, observation cutoff | On-hand, reserved, inbound ETA and freshness; unavailable is not zero |
| Research/retrieval | Sanitized query, allowed corpus/hosts | Candidate claims with source/time; never execution authority |
| Planner/agent | Scoped facts, task, approved tool set | Proposed plan and evidence references; cannot set trusted verification flags |
| Policy evaluator | Canonical proposed action, current policy and budget | Not ready, approval required, authorized, or prohibited with reasons |
| Executor | Validated action ID/version, authority, idempotency key | Submitted/confirmed/failed/unknown outcome and external ID |
| Verifier/receiver | Confirmation or receipt event, expected action | Matched/mismatched evidence; authorized movement and outstanding obligations |

Store external event envelope before processing: `event_id`, `business_id` (or isolated demo session), `connection_id`, provider event ID/dedup key, received/observed timestamps in UTC, source class, allowed metadata, restricted content reference, rule version, evidence IDs, status and origin. Deduplication is scoped by provider and business. Source facts include units/currency, observed/effective/expiry times, evidence reference and verification status; preserve supersession/conflicts. These records are required additions, not current schema.

Models may propose facts and plans. Application code derives allowlist status, canonical SKU mappings, fresh evidence and verification from trusted records; never accept a model's `verified=true` as proof. Add `business_id` scoping and authenticated identity before sharing a production database across businesses.

## Action and approval contract

Current hash covers supplier ID, SKU, quantity, unit price, fees, computed total and currency. It excludes ETA, delivery destination, substitutions, cancellation terms and evidence snapshot. Current actor `owner` is synthetic. Approval TTL/revocation exist in the store API; the UI does not expose these controls and sets no TTL.

Required action snapshot: business/session, action type, canonical recipient ID and destination, item/variant/unit, quantity, currency and landed total components, promised timing, material fulfillment/cancellation terms, evidence IDs and snapshot version, policy ID/version, idempotency key, origin. Approval binds a versioned canonical payload hash and authenticated actor, scope, decision, timestamp, expiry and revocation. Monetary serialization uses normalized fixed-scale decimals/minor units so equivalent values hash identically. Changed material terms supersede the action and require reevaluation; old approval cannot cover a replacement action.

Recheck current connection permissions, actor authority, approval validity, action hash, counterparty trust, evidence freshness, and spending reservations immediately before execution. Any missing critical term blocks execution. Human approval cannot fix unknown price, wrong SKU, stale evidence or revoked access. New suppliers, stock write-offs, customer commitments and policy expansion require explicit relevant authority. Separate communication approval from purchase approval and inventory adjustment approval.

Current policy fixture: total `< $40`, price increase `< 5%`, quantity `1..200`, supplied remaining budget `$200`, allowlisted supplier, known SKU and three true evidence flags. Exactly $40 or exactly 5% needs approval. Readiness failures win over authority failures. The 100-unit $61 fixture has only the spending-threshold failure.

**Budget gap:** the store does not reserve/decrement a shared budget. Required multiple-order implementation reserves funds atomically before submission, converts reservation to spent on verified commitment, releases only after confirmed non-execution/cancellation, and counts pending plus committed spend in one owner-defined period. Parallel or split purchases cannot bypass the limit. The budget period, hard cash limit and override scope must be chosen before real purchases. An approval of one order is not blanket approval to exceed a hard account limit.

## Lifecycle, idempotency and recovery

Current legal states are in `lifecycle.py`: detected → investigating → plan_ready → policy_check → authorized or waiting_for_approval → approved → executing → verifying → awaiting_receipt → reconciling → completed. Blocked, recovery, declined, cancelled and failed branches are explicit. No `monitoring` enum or background shipping monitor exists. Short receipts remain reconciling.

Required completion: matched confirmation, verified received/fulfilled quantities, authorized stock movements, reconciled monetary obligations where applicable, zero unresolved required obligations. If a follow-up is transferred, show its owner, remaining quantity/value and due date; do not label the whole business problem resolved. Current completion covers the synthetic quantity obligation only, not payment/invoice reconciliation.

Use stable idempotency keys per action and distinct provider receipt/event IDs. Apply receipt, movement and workflow transition atomically. Duplicate event returns original result without another movement or purchase. Same receipt key with different payload must be rejected as conflict, not accepted as a new fact. Current receipt replay compares action identity, not all receipt payload fields; broaden before real ingestion.

For external execution, persist intent before the network call. On timeout, enter unknown-outcome recovery and query the provider by idempotency key/external ID before any resubmit. Never claim exactly-once remote execution from a local unique constraint alone. Proposed engineering default: 10-second timeout, at most two retries with backoff for safe reads; writes retry only after status reconciliation or documented provider idempotency. Persist next attempt/deadline so restart does not reset retry count. These values are proposed defaults, not current vendor capabilities.

Matching confirmation leaves stock 21. Full receipt adds 100 once, stock 121, completed. Receipt 97 adds 97 once, stock 118, outstanding three; later three adds once and completes. Over-receipt is blocked; premature receipt is blocked. Confirmation mismatch enters recovery with no stock movement. Decline submits nothing. Production discrepancies preserve original counts and evidence; correction never silently overwrites history.

## Planning edge cases

Current `plan_reorder` is fixture-specific: open-PO coverage is always false, offer/evidence flags are seeded, warehouse/MOQ are constants. A no-risk message produces quantity zero and reaches positive-quantity validation; it is not a working zero-intervention healthy path. `assess_supply` itself handles zero demand with undefined days/gap, but the planner assumes nonzero demand. Do not generalize the planner without tests.

Required behavior before generalization:

- No reorder risk: persist checked/no-action outcome, create no zero-quantity purchase, close analysis without owner approval.
- Zero demand: show insufficient/no observed demand and avoid division; empty/sparse history or censored stockout sales produce explicit uncertainty.
- Stale count, unknown fees, unmapped variant or conflicting supplier facts: block commitment and ask only for the missing fact.
- Inbound/warehouse coverage: compare arrival/transfer dates with demand dates; count reservations and event demand once; incoming stock is not available stock.
- Returns, cancelled reservations, negative/NaN/infinite values, mixed currency, units versus packs and partially observed days: validate explicitly.
- Reorder quantity: the core remains MOQ 100. Generalized target horizon, safety-stock method and cash/storage limits require a documented rule; round integer units to packs/MOQ after netting time-phased supply.

## Preview contracts

Use PRD FR-06–FR-09 as executable scenario contracts. The four previews now persist in independent ScenarioStore keys in the same visitor file, with a synthetic authorization/fulfillment path. Production exact action approval/roles remain future requirements. Proposed further defaults, which must not be mistaken for existing input validation:

- Workshop: validate integer attendees 1–100 and deadline 1–90 days; negative cost invalid. Reserve materials/capacity only after customer commitment authority; purchasing is a separate action. Purchase cash and consumed material cost are not counted twice.
- Detective: confirm 12 actual uses before proposing the three-unit correction from 20 to 17; original physical count 16 stays recorded; a recount 17 resolves, otherwise the remaining discrepancy stays open. No automatic write-off.
- Merchant: two synthetic counterparties; maximum two counteroffer rounds each, no binding send/purchase/customer promise without authority. Each counteroffer must improve feasible contribution without crossing the seeded merchant floor. Display unavailable/expired/declined offers and fallback options. Real expiry, routing radius, reservation protocol and transfer responsibility need owner/provider decisions.
- Staffing: mean transaction history by weekday; workload = transactions × .25 hours + pickups × .25 + 1 baseline hour + 4 workshop hours. Extra blocks = ceiling(max(0, workload − owner hours)/4). Tuesday mean 5.2 → 2.3 hours with no event/pickups → zero extra blocks at six owner hours. Saturday 36 + workshop → 14 hours → two extra blocks. Recommend coverage; saving does not schedule or reduce employee shifts. Missing history means needs data, not zero workload.

These are review proposals and may be adjusted in a documented decision before implementing those previews. They grant no real-world authority.

## Requirement-to-verification map

| Requirement | Existing evidence | Required additional coverage |
| --- | --- | --- |
| FR-01 signal/extraction | test_reorder parser/override and validated model-output/fallback tests | Live-provider duplicates, blocked metadata/body, revocation, cursor recovery and general task extraction |
| FR-02/03 planning/economics | test_inventory, test_reorder | No-risk planner, stale facts, timed inbound, fees unknown, variant/pack mapping |
| FR-04 authority | test_policy, test_terms, test_workflow | Full material hash, authenticated actor, budget reservation across concurrent orders, hard-limit overrides |
| FR-05 receipt/persistence | test_fulfillment, test_lifecycle, test_workflow | Remote unknown outcome, conflicting replay payload, hosted durability, financial obligations |
| FR-06–09 previews | test_ops_demos verifies default fixture math, blocked workshop, correction/recount, negotiation floors and coverage; browser review exercises persisted paths | Broader range/finite-number validation, per-action authorization binding, decline/expiry, hostile state/replay, concurrency and financial reconciliation |
| FR-10 status/audit | test_inbox execution records and test_research provider-result/fallback tests | Real successful/failed provider calls, fallback origin, field disclosure manifest and secret redaction |
| Security/public experience | test_inbox session/HTTP flow | CSRF/request validation, disk/session quotas, expiry cleanup, keyboard/mobile and recoverable errors |

Test meaningful business behavior first and demonstrate intended failures before implementation. Run targeted tests then relevant regressions. Do not add tests that merely assert documentation wording. Browser/host validation is separate from passing Python tests.

## UI source of truth

All pages use demo_ui.shell and ui_theme.STYLE; no separate light procurement page remains. docs/DESIGN.md defines the confirmed dark/playful direction and measurable experience checks. docs/STATUS.md records the fresh inspection and distinguishes tests/source wiring from previous provider reports. This contract does not certify those provider reports or a hosted release.
