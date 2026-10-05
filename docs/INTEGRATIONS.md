# smolstuff integration contract and status

At inspected commit `2dc9093610c874179bc14a870ae3b9ad8f0f72b0`, **no sponsor/runtime network integration is implemented**. The source has no provider client or credential loading. Accounts, installed plugins and API keys are not proof of an application integration. This review makes no assertion about current vendor API capabilities; consult official provider documentation when choosing adapters.

| Integration | Current | Intended responsibility | Proof before calling it live |
| --- | --- | --- | --- |
| Email | Simulated arrival + local regex | Automatic permitted-provider events/polling, triage and task extraction | Allowed arrival opens case without uploads; blocked body never reaches downstream; duplicate/revocation recovery |
| Inventory/POS | Seeded fixture + receipt movements | Read authoritative stock/sales/inbound; scoped authorized corrections | Real scoped read with time/source; write/reconciliation tests before writes |
| ZooWork | Not wired | Scoped managed-agent interpretation/planning where supported | Validated task output affects case; durable state/policy stays in app |
| BAND | Not wired | Meaningful handoff between distinct logical specialists or merchants | Receiving agent consumes findings and changes its next action |
| Moss | Not wired | Permission-filtered evidence retrieval | Relevant cited retrieval; business filtering and deletion verified |
| Tavily | Not wired | Public supplier discovery | Real search result used by investigation; stock/ETA still tentative |
| Novita/selected model | Not wired | Constrained fact extraction or explanation | Schema-valid result from permitted excerpt; output cannot set authority |
| Browser verification | Not wired | Timestamped product-page observation | Product/cost/timing evidence and limitations; no reservation claim |
| Purchase/confirmation/receipt | Local simulated adapters | Authorized submission, independent confirmation and receiving | External ID, matching approved terms, idempotency/recovery and actual receipt |
| Merchant network | Not wired | Bounded nonbinding requests/offers and verified fulfillment | Onboarded counterparties, explicit disclosure scope, expiry/reservation and dispute flow |
| Entire | Development role only | Reviewed build provenance | Actual captured build evidence; no private records/secrets shared |

The state machine belongs to the application. A managed agent may help plan; do not assume a sponsor supports durable orchestration or approval pause/resume without API evidence. A successful public search does not verify the seeded Supplier B offer. Real research and simulated purchases can coexist if each result carries its own origin.

## Adapter result schema

Require: run ID, linked workflow/step, provider/task, start/end time, input field manifest, source/evidence references, validated result summary, effect on workflow, origin (`live`, `simulated`, `replayed`), outcome (`succeeded`, `failed`, `unknown`), retry count, error category and fallback link. Do not record secrets or unrestricted prompt bodies. Current integration_events records only provider/task/result/effect/time/status; outcome/disclosure/linkage are required additions.

Transport status and business validity are separate: HTTP success with malformed output is a failed task; a models-list call is not an operations task; replayed prior evidence is not fresh research. Any fallback must retain failed-call evidence and label its replacement result. Invalid output cannot produce live-success UI. Exceeding quota produces a clear fallback/blocked state, never another unapproved paid call.

## Configuration and verification sequence

1. Select one adapter needed by a workflow step. Verify its official endpoint, runtime compatibility, available account permissions, expected input/output and cost.
2. Create server-side placeholder settings and ignored private configuration before entering secrets. Document required vs optional fields, local/hosted configuration, and a default disabled switch.
3. Tell the owner the exact missing credential or identifier and its dashboard field. Ask one service at a time; the owner enters it locally or in hosted secrets. Never request secret values in chat.
4. Run one permitted synthetic workflow task; validate response and demonstrate effect on the persisted case. Record sanitized evidence. Test unavailable credentials, timeout, invalid output and quota exhaustion.
5. Enable public calls only after approved budget, rate limits, privacy controls and fallback are verified. Keep real purchases/messages disabled for this demo.

Exact IDs/key names are intentionally not invented in this doc. Retrieve them from selected providers' official documentation during implementation. Do not add redundant providers solely to increase sponsor logos.
