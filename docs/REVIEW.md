> **Historical review.** This document describes the first inspection at the commit below. It is retained as history and is superseded for current status by [STATUS.md](STATUS.md). File names, package paths, feature status and test counts here are historical observations, not current implementation claims.

# smolstuff documentation review

Historical review of commit `2dc9093`. Current behavior is in [README.md](../README.md). Hosting direction is in [ARCHITECTURE.md](ARCHITECTURE.md). Render is no longer the plan, and the package is `smolstuff`.

Reviewed October 4, 2026 against GitHub `heykatie/smolstuff` at that older commit. The notes below describe that checkout, not the current tree.

## Verdict

The vision is strong and broadly matches the requested small-business operations system. The live implementation is a much narrower simulated procurement demo. Before this review, the docs were **not internally consistent or implementation-ready for the complete product**: Cursor would have to choose scope, invent integration and security contracts, and infer important approval/recovery rules.

The documentation changes provide one staged source of truth for the next demo release and detailed boundaries for future connectors. They do not implement the missing features or settle consequential owner/provider decisions. The narrow baseline is runnable and covered by 50 passing tests; no live provider call, public deployment, production privacy control or broader preview is certified here.

## Product coverage

| Intended capability | Existing documentation | Actual live baseline / gap |
| --- | --- | --- |
| Easy setup and low owner effort | Zero-chores principle and Action Inbox are explicit | Anonymous synthetic demo; no onboarding or connected business source |
| Automatic email triage without uploads | Progressive gate/privacy modes described | Button supplies one hardcoded message; regex extracts one lead-time pattern; no background intake, categories or general actionable tasks |
| Sensitive actions queued for approval | Modes, strict limits, exact terms, rechecks described | One purchase approval/decline; no authenticated roles or broad action queue |
| Inventory discrepancy investigation | Good fact/inference/unknown example | Receipt shortage ledger only; no physical-count/usage investigation |
| Velocity and supplier-aware reorder | Clear stock/lead-time math | Fixed ten-day mean, seeded MOQ/offer and constant warehouse/PO inputs; no timed live supply or optimized quantities |
| Staffing-light days | Coverage vision described | No staffing code; release PRD now provides deterministic low/high-day fixtures |
| Save a sale through nearby agents | Network/negotiation and contribution vision | No merchant adapters, offers, reservation or fulfillment workflow; disclosure example originally included private acquisition ceiling |
| Privacy/security/least privilege | Strong principles | No real connector enforcement; simulated verification flags, anonymous synthetic actor, incomplete HTTP/retention/secret setup rules |
| Auditability and trust | Evidence/closure principles | SQLite transitions, approvals, movements and short tool records; not a production disclosure audit, financial reconciliation or tamper-evident log |

## Prioritized gaps and resolutions

Priority here is review urgency, separate from PRD feature priority. **P0** resolves ambiguity before further coding or prevents unsafe claims/execution; **P1** specifies the next functional work; **P2** improves subsequent operations/maintenance.

| Priority | Gap at inspected commit | Why it matters / concrete response |
| --- | --- | --- |
| P0 | Multiple sources of truth: MVP_SCOPE says it wins, project_context calls itself master; project PRD wasn't in repo | Added repository PRD and precedence across all entry docs. Preserve synthetic P0 core, P1 functional previews, P2 production direction; never confuse current absence with permanent exclusion |
| P0 | Scope contradicts requested breadth: merchant/staffing/opportunity excluded while project PRD expects previews | Rewrote staged MVP scope; imported FR-06–09 fixtures; all displayed previews must work, otherwise marked planned |
| P0 | Automatic-ingestion language could imply connected inbox; gate not implemented | Clarified demo trigger vs automatic production events/polling; required event envelope, filtering, task extraction, dedup/cursor/revocation contracts; provider/access choice remains D1 |
| P0 | Approval binding is incomplete | terms.py hashes supplier/SKU/price/quantity/fees/currency but not ETA/destination/other material terms; added complete action snapshot and authenticated actor requirements before real execution |
| P0 | Aggregate anti-splitting promise exceeds implementation | policy compares static supplied remaining budget; workflow does not reserve/decrement it. Required atomic pending/committed budget accounting and a decision on hard limits/overrides/window (D5) |
| P0 | Privacy promises lack provider/storage boundaries | Added per-boundary enforcement, data disclosure fields, revocation/deletion across raw/facts/vector/logs/backups, secret setup, fail-closed production gates; retention/provider settings remain D1/D6 |
| P0 | Merchant example leaks internal ceiling | Removed max_acquisition_cost from outbound JSON. Required private policy ceiling and sanitized transaction-only payloads |
| P0 | Sponsor/runtime responsibility ambiguous | Main orchestration language conflicts with an application-owned state machine; no provider clients exist. Added status/contracts and required real task evidence; vendor capabilities remain unverified |
| P0 | Public durability/security claims exceed manifest | render.yaml has no configured durable store; session cookie isn't owner authentication. Added launch tests, request/session/quota/CSRF/retention requirements and explicit disk-lifetime limits |
| P1 | Short-receipt documentation contradicts rendered UI | MVP says included; README says not a button. Documented exact distinction: handler/test supports 97+3, normal page only full receipt. Separate from Inventory Detective cause analysis |
| P1 | General forecasting requirements exceed fixture planner | No-risk path reaches zero-quantity rejection; PO coverage hardcoded false; stock/evidence constant. Added required tests/outcomes for no action, zero/sparse demand, timed inbound, stale stock, mapping and fees |
| P1 | Recovery/remote exactly-once behavior unspecified | Local simulated unique keys do not solve network unknown outcomes. Defined durable intent, status query, bounded retry and conflicting replay behavior before external writes |
| P1 | Scenario completion, ranges and negotiation unspecified | PRD gives exact workshop/detective/merchant/staffing numbers; technical contract proposes input ranges/two-round simulated negotiation and independent scenario persistence. Real reservation/expiry/fulfillment still D7 |
| P1 | Security flags can be mistaken for established verification | Model plans must not set allowlist/evidence truth. Derive canonical status from trusted records; current flags remain labeled seeded |
| P1 | Acceptance lacks requirement-to-test/host evidence | Added FR-to-test map, missing behavior tests, and separate browser/host gates. Existing tests pass but do not prove remaining requirements |
| P2 | Brand is stale across docs, UI, metadata, cookie/service | Renamed documentation and clone/issue URLs to smolstuff. Technical identifiers/UI strings remain explicitly inventoried for a separately tested migration |
| P2 | Dev/CI/configuration instructions incomplete | Added actual env settings, storage/reset behavior, startup/tests, hosting caveats and configuration sequence. No .env loader, lint/typecheck/CI or cleanup exists; do not document imaginary commands |

## Concrete file-by-file changes

Historical `src/smol_ai/` paths in this table are the package paths recorded at commit `2dc9093`. Later commits use `src/smolstuff/`. Those old paths stay because they are what that inspection saw.

| File | Applied documentation edit / remaining work |
| --- | --- |
| README.md | Correct brand/URL and status; new reading path; demo-vs-production intake and disk persistence limits; developer/security/integration links |
| MVP_SCOPE.md | Replaced contradictory exclusion/precedence text with current baseline and P0/P1/P2 release boundaries; accurate short-receipt exposure and quantity method |
| DEMO_SPEC.md | Correct brand; exact 5%/quantity/$200 fixture rules; seeded verification/budget limits; 97+3 branch and synthetic owner boundaries |
| project_context.md | Preserve detailed vision; correct name, doc precedence and stack; clarify trigger, scope, agent roles and technical status; remove private ceiling from outbound request |
| PRD.md | Added reconciled project PRD with functional acceptance; removed unsupported claims of live Tavily/model fallback or previews already present; defined doc ownership and inspected status |
| AGENTS.md | Added short Cursor instructions: read requirements/contracts, preserve core, test meaningful behavior first, synthetic boundaries and truthful status |
| docs/IMPLEMENTATION_CONTRACT.md | Added code/data-flow map, current vs required schemas, action hash/policy/budget semantics, lifecycle/retries, edge cases, preview defaults and test traceability |
| docs/SECURITY_AND_DECISIONS.md | Added trust-boundary matrix, public/pilot gates, disclosure/retention/revocation rules and nine explicit missing decisions with safe interim behavior |
| docs/INTEGRATIONS.md | Added per-adapter actual status/intended role/proof; result schema, one-service credential sequence and cost/fallback rules without invented API claims |
| docs/DEVELOPMENT.md | Added runnable setup, exact current env/storage, local-vs-host verification and staged implementation sequence |
| pyproject.toml | No runtime edit: distribution name/description still legacy. Rename in a dedicated compatibility change; verify Python support and packaging workflow |
| render.yaml | No deployment edit: legacy service name and persistence gap recorded. Decide storage/provider, then verify deployed revision and restart/redeploy |
| .gitignore | No edit in doc-only change: data already ignored; add `.env`/private credential exclusions before credential entry and verify no tracked secrets |
| LICENSE | Inspected; MIT license unchanged |
| src/smol_ai/inbox.py | No code edit: stale title/landing copy, missing empty-page viewport, public request defenses and short branch exposure identified for follow-up |
| src/smol_ai/policy.py, terms.py, workflow.py | No code edit: authoritative trust, complete material hash, authenticated approvals, budget reservations, remote recovery and richer audit required before real execution |
| src/smol_ai/reorder.py, inventory.py, extract.py, fixtures.py | No code edit: make general no-risk/timed-stock/triage contracts real only after meaningful tests; preserve demo math |
| tests/ | No new doc-wording tests. Baseline 50 pass; map records missing tests for upcoming behavior changes |

## Verification and remaining decisions

Cloned the renamed live default branch separately; preserved the older local checkout and its uncommitted README. Reviewed all tracked docs/config and mapped the Python/test structure. Ran `.venv/bin/python -m pytest -q`: **50 passed**. Checked final documentation links, fenced JSON, brand references and diff whitespace. Documentation changes do not change runtime code, dependencies, hosting settings or business integrations.

No hosted URL or actual runtime provider call was verified. Browser visual/keyboard/mobile checks were not run for this documentation-only change; required experience checks remain release gates. No claim is made that local newer work, account setup or previously reported integration status is on the live branch.

Owner/provider decisions D1–D9 are in SECURITY_AND_DECISIONS. Coding can proceed against the synthetic next-release contract. Private ingestion, paid public calls, real purchases/messages and live merchant commitments remain disabled until their respective choices and verification gates are completed. Merge of this documentation does not authorize any of those operations.
