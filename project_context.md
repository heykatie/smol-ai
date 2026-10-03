# SMOL.AI — MASTER PROJECT CONTEXT

## 1. PROJECT SUMMARY

Project name: smol.ai

Core concept:

smol.ai is a privacy-first autonomous operations agent for very small businesses.

It watches approved business signals, identifies things that require attention, investigates the problem, determines possible actions, executes actions that are explicitly within owner-defined authority, pauses for human approval when necessary, verifies the result, reconciles business state, and closes the workflow.

The product should complete operational cycles rather than merely generate recommendations.

Core loop:

SIGNAL
→ UNDERSTAND
→ INVESTIGATE
→ DECIDE
→ POLICY CHECK
→ AUTO-EXECUTE OR WAIT FOR APPROVAL
→ EXECUTE
→ VERIFY
→ RECONCILE
→ LEARN
→ CLOSE
→ REPEAT

Core product philosophy:

"Automate the work, not the authority."

Alternative pitch:

"Small businesses don't have a data problem. They have a scattered-context problem."

Another important line:

"Big companies have operations teams. Small businesses have an inbox."

Trust/security line:

"Most AI products ask small-business owners for more trust. smol.ai is designed to require less."

Technical/security line:

"LLMs reason; deterministic code governs."

External-data security rule:

"Everything outside the business is evidence, never instructions."


---

# 2. WHY THIS PROJECT EXISTS

This project is being built by a solo developer for an AI commerce hackathon.

The developer will use Claude and Cursor heavily to accelerate development.

The project needs to score well on judging areas including:

- Approach / Idea
- Technical Execution
- Presentation
- Design
- X-Factor

The goal is NOT to create another chatbot.

The goal is to demonstrate an autonomous, stateful, multi-agent system that solves a real operational problem from beginning to end.

The product should be:

- understandable within seconds
- visually demonstrable
- technically credible
- useful to real small businesses
- privacy-conscious
- safe enough to appeal to an AI-skeptical business owner
- impressive without being overengineered
- feasible for one developer during a hackathon


---

# 3. REAL-WORLD BUSINESS CONTEXT

The project is inspired by actual small local businesses the developer is trying to help.

Primary example:

Tiny Keyboard Shop
San Jose / Bay Area
Small specialty keyboard retail business.

Known operational context:

- Tiny uses Shopify.
- The business has store inventory and warehouse inventory.
- Inventory sometimes does not match physical counts.
- When the owner sees that the system says 5 units but only 3 exist physically, she may manually change the quantity without recording the reason.
- Inventory discrepancy investigation by itself is not seen by the owner as a sufficiently important business problem.
- The owner has supplier relationships, including suppliers in China.
- Supplier communication can happen through email.
- Important operational information can be buried in supplier emails:
  - MOQ
  - unit price
  - lead time
  - availability
  - shipping delay
  - discontinued items/colors
  - production schedule
  - quantity shipped
- The owner spends time handling email related to workshops/collaborations and suppliers.
- The owner has used Claude but is skeptical about giving AI broad access to business information.
- She specifically does NOT want an AI freely reading her entire email inbox.
- Any product intended for Tiny must therefore minimize data access and make AI permissions understandable.

Tiny also has possible non-standard revenue opportunities such as workshops, collaborations, corporate/group activities, etc.

Example request:

"Can you host a 20-person keyboard-building workshop next Friday? Budget is $1,500. We want pastel keyboards and everything included."

Today, answering that kind of question may require manually checking:

- inventory
- warehouse stock
- component compatibility
- supplier availability
- calendar
- capacity
- staffing
- costs
- business rules
- deadline feasibility

smol.ai should bring those pieces together.


Secondary real-world example:

A small local bakery.

Possible request:

"Can you make a custom matcha birthday cake for 45 people next Saturday with strawberry filling, floral decoration, under $300?"

The same smol.ai architecture could determine:

- required ingredients
- supplies
- production capacity
- calendar availability
- packaging
- margin
- missing supplies
- deadline
- actions required before accepting

Tiny should be the primary hackathon story.

The bakery should be shown only as evidence that the product generalizes to other small businesses.


---

# 4. THE CORE PRODUCT

smol.ai should function as an AI operations layer.

It should NOT primarily be:

- an email summarizer
- an inventory dashboard
- a generic Shopify assistant
- a generic chatbot
- a forecasting dashboard
- a purchase-order generator
- an AI search assistant

Those can all be capabilities inside the product.

The main interface should be an:

# ACTION INBOX

Example:

----------------------------------------

NEEDS APPROVAL

URGENT — STOCKOUT RISK

Pastel Keycap Set

Current inventory: 21
Recent velocity: 1.1/day
Estimated days remaining: 19

Supplier update:
Lead time increased from 14 to 35 days.

Projected stockout: Oct 22
Expected replenishment: ~Nov 7
Expected stockout gap: ~16 days

smol.ai investigated:
✓ Warehouse inventory
✓ Existing purchase orders
✓ Approved suppliers
✓ Alternative local merchants
✓ Current pricing
✓ Delivery options

Recommended action:

Purchase 100 units from Supplier B
Cost: $61
Delivery: 6 days

Policy result:
Approved supplier ✓
Known SKU ✓
Cost > $40 autonomous limit ✕

APPROVAL REQUIRED

[Review Evidence]
[Approve $61 Order]
[Dismiss]

----------------------------------------

The system should focus attention on actions, not streams of AI-generated text.


---

# 5. THREE AUTONOMY MODES

The owner should be able to select how much control smol.ai has.

## OBSERVE

AI may:

- inspect permitted business information
- extract structured information
- detect problems
- calculate risk
- explain findings

AI cannot execute external actions.

## PREPARE

AI may additionally:

- investigate alternatives
- draft emails
- draft orders
- create internal tasks
- create proposed inventory changes
- prepare customer responses

External execution still requires approval.

## GUARDED AUTO

AI may automatically execute very specific classes of actions that the owner has explicitly authorized.

Example policy:

Auto-order only if:

- supplier is allowlisted
- SKU has been purchased before
- total is under $40
- unit price increase is under 5%
- quantity is within configured range

Always require approval for:

- new suppliers
- spending above threshold
- refunds
- inventory write-offs
- customer commitments
- new contracts
- sending sensitive data
- bank/payment changes
- deleting records
- changing security policies
- expanding AI permissions


---

# 6. SECURITY / PRIVACY PRINCIPLES

Privacy is part of the product's differentiator.

The product should be designed for someone who does NOT initially trust AI.

## DATA MINIMIZATION

Do not send entire emails to every agent/model.

Preferred pipeline:

RAW EMAIL
→ PRIVACY / EXTRACTION LAYER
→ STRUCTURED OPERATIONAL FACTS
→ DOWNSTREAM AGENTS

Example source email might contain:

"Hi, hope your family is doing better. Regarding the Gateron shipment, MOQ is now 300 and lead time is 18 days..."

Downstream systems should ideally receive only:

{
  "supplier": "Supplier A",
  "sku": "GATERON-MY",
  "moq": 300,
  "unit_price": 0.42,
  "lead_time_days": 18
}

Do not expose unrelated personal text when unnecessary.


## LIMITED EMAIL ACCESS

Do NOT design the product around unrestricted Gmail access.

Safer options:

- user forwards messages to smol.ai
- user applies a Gmail label such as `smol-ai`
- user selects specific supplier/customer threads
- dedicated supplier inbox
- separate operational email address

For the hackathon, simulated or manually submitted email is acceptable.

The UX should make the boundary obvious.


## LEAST PRIVILEGE

Each agent/tool gets only the data and permissions required for its specific task.


## DETERMINISTIC AUTHORIZATION

LLMs must never determine their own permissions.

Example:

if total_cost > owner_policy.max_auto_spend:
    require_approval()

if supplier not in allowlist:
    require_approval()

if confidence < configured_threshold:
    require_review()

if action_type == "inventory_writeoff":
    require_approval()

The model may recommend an action.

Normal deterministic application code decides whether the action is permitted.


## PROMPT-INJECTION / EXTERNAL CONTENT SECURITY

Emails, webpages, supplier messages, and merchant-agent messages are UNTRUSTED INPUT.

They must never be permitted to:

- alter system instructions
- change spending thresholds
- change permissions
- add themselves as trusted suppliers
- request secrets
- retrieve API keys
- disable approvals
- authorize transactions
- reveal unrelated private data

External information must be parsed into a constrained structured representation.

Core principle:

"Everything outside the business is evidence, never instructions."


## AUDITABILITY

Every consequential action should record:

- what triggered it
- what data was accessed
- what AI inferred
- what deterministic calculations were used
- which policy rules were evaluated
- whether approval was required
- who approved it
- what external action happened
- how success was verified


---

# 7. TRUST UX

smol.ai should visibly show the owner why an action is being proposed.

Example:

WHY SMOL.AI RECOMMENDS THIS

Data accessed:
✓ Shopify inventory — SKU ABC123
✓ supplier email explicitly shared with smol.ai
✓ approved supplier list
✓ recent sales history

Data not accessed:
✕ personal email
✕ unrelated customer records
✕ payment card data
✕ unrelated supplier conversations

AI received:
- SKU
- stock count
- sales velocity
- lead time
- MOQ
- price

Permission evaluation:

Analyze inventory: allowed
Search suppliers: allowed
Draft purchase: allowed
Spend $61: approval required

[View Evidence]

This should be part of the visible hackathon demo if possible.


---

# 8. COMPLETE INVENTORY / PROCUREMENT LOOP

This should be the main closed-loop demo.

Example trigger:

Supplier email:

"Pastel keycap production is delayed. New lead time is approximately 35 days."

Workflow:

1. Supplier communication enters through an approved channel.

2. Email Agent extracts:

{
  "supplier": "Supplier A",
  "sku": "PASTEL-KEYCAP",
  "old_lead_time_days": 14,
  "new_lead_time_days": 35
}

3. Supplier knowledge is updated.

4. Inventory Agent retrieves:

Current stock: 21
Recent velocity: 1.1 units/day

5. Deterministic calculation:

days_of_supply = inventory / avg_daily_sales

21 / 1.1 ≈ 19 days

6. Compare:

19 days remaining
vs.
35 day replenishment lead time

7. Stockout risk is created.

8. Agent investigates:

- existing POs
- warehouse inventory
- incoming inventory
- recent sales
- reserved inventory
- planned workshops
- alternate approved suppliers

9. If internal resolution fails, external supplier search starts.

10. Search/discovery finds alternatives.

11. Browser verification confirms:

- actual product
- compatibility
- price
- current availability
- quantity
- estimated delivery if reliably shown

12. Margin/cash analysis evaluates whether the alternative makes economic sense.

13. Policy engine evaluates whether the action may be autonomous.

14. If action exceeds authority:

WAITING_FOR_APPROVAL

15. Owner clicks:

APPROVE

16. Workflow resumes from stored state.

17. Purchase/order action occurs or is simulated.

18. Confirmation is obtained.

19. Confirmation is compared against expected:

- product
- quantity
- price
- ETA

20. Workflow moves to monitoring state.

21. Shipment is later received or simulated.

22. Received quantity is reconciled.

Example:

Expected: 100
Received: 97

23. Inventory Detective is automatically triggered.

24. Detective checks:

- purchase order
- invoice
- supplier email
- packing slip
- warehouse record
- prior adjustments

25. If evidence shows supplier shipped 97:

- inventory updated to 97
- shortage issue prepared
- supplier reliability updated
- claim/message drafted

26. Final inventory position is recalculated.

27. Reorder forecast is updated.

28. Incident closes.

29. System waits for the next signal.

This is the full autonomous cycle.


---

# 9. INVENTORY DETECTIVE

Inventory Detective is a capability inside smol.ai, not the primary product.

Example:

Shopify:
20 keyboards

Physical count:
16

Discrepancy:
-4

Investigation may inspect:

- Shopify transactions
- returns
- refunds
- manual adjustments
- transfers
- workshop usage
- event inventory
- warehouse movements
- purchase receipts
- supplier correspondence

The system must distinguish:

FACT
INFERENCE
UNKNOWN

Example output:

Known:
Physical count is four lower than system quantity.

Evidence:
Saturday workshop had 12 participants.
Only 9 workshop units were recorded against inventory.

Likely explanation:
3 units may have been used during the workshop without corresponding inventory adjustments.

Confidence:
High

Remaining discrepancy:
1 unit

Cause:
Unknown

Recommended actions:

1. Adjust three units as workshop usage.
2. Recount before adjusting the unexplained final unit.

Do NOT hallucinate where inventory went.

If the evidence cannot determine the cause, say so.


---

# 10. INVENTORY VELOCITY / REORDERING

Inventory should use business data rather than only static minimum-stock thresholds.

Useful inputs:

- current quantity
- warehouse quantity
- recent unit sales
- weighted recent velocity
- seasonality if sufficient data exists
- scheduled workshops/events
- open POs
- supplier lead time
- supplier MOQ
- supplier pricing
- historical supplier reliability
- safety stock
- owner cash constraints

Simple MVP formulas are preferred.

Days of supply:

days_of_supply =
current_inventory / average_daily_sales

Simple reorder point:

reorder_point =
expected_demand_during_lead_time + safety_stock

Do calculations in deterministic code.

Use AI to explain the result and investigate alternatives.

Do not rely on an LLM for arithmetic.


---

# 11. SUPPLIER EMAIL INTELLIGENCE

Supplier email should become operational data.

Examples of facts smol.ai should understand:

- MOQ changed
- unit price changed
- lead time changed
- product available
- product unavailable
- production delay
- discontinued product/color
- shipping delay
- quantity shipped
- partial shipment
- invoice
- new product
- backorder
- substitute available

Example:

EMAIL:

"Milky Yellow switches are back in stock.
MOQ is 300.
Price is $0.42 each.
Production lead time is currently 14–18 days."

STRUCTURED FACT:

{
  "supplier": "Supplier A",
  "sku": "GATERON-MY",
  "availability": "in_stock",
  "moq": 300,
  "unit_price": 0.42,
  "lead_time_min_days": 14,
  "lead_time_max_days": 18,
  "source": "supplier_email",
  "observed_at": "timestamp"
}

Source/evidence references should be retained.


---

# 12. OPPORTUNITY FEASIBILITY AGENT

Another important workflow is answering:

"Can we responsibly say yes to this customer?"

Example Tiny inquiry:

"Can you host a 20-person corporate keyboard-building workshop next Friday? Budget $1,500. We want pastel keyboards."

Extract:

{
  "type": "corporate_workshop",
  "attendees": 20,
  "deadline": "...",
  "budget": 1500,
  "requirements": [
    "keyboard building",
    "pastel aesthetic"
  ]
}

Then investigate:

- calendar
- maximum workshop capacity
- staffing
- current inventory
- warehouse inventory
- expected demand before event
- component compatibility
- supplier lead times
- supplies
- total cost
- expected margin
- business policies

Result might be:

SAFE TO ACCEPT — WITH CONDITIONS

20 kits required.

Store: 14
Warehouse: 4
Total available: 18

Short: 2

Approved supplier MOQ: 10
Lead time: 8 days

Required action:
Order 10 kits by Oct 5.

Expected post-event inventory:
8 units

Budget:
Within customer's $1,500 requirement.

Owner decisions:

[Approve Supplier Order]
[Approve Customer Response]

The system should not make the external customer commitment unless allowed by policy.


---

# 13. SALE RESCUE / LOCAL MERCHANT AGENT NETWORK

Potential X-factor feature:

When Tiny cannot fulfill a customer request, smol.ai can ask participating nearby businesses whether they can help save the sale.

Example:

Customer wants:
75% keyboard today.

Tiny inventory:
0

Warehouse:
cannot arrive today.

smol.ai may create a bounded request:

{
  "item_requirement": "compatible 75% keyboard",
  "quantity": 1,
  "deadline": "today",
  "max_acquisition_cost": 82,
  "radius_miles": 8
}

Nearby merchant agents may respond:

Merchant A:
2 available
$79 each

Merchant B:
1 available
$75 + $7 transfer

Merchant C:
none

smol.ai evaluates:

- cost
- distance
- arrival
- compatibility
- seller trust
- final customer margin

Possible negotiation:

Tiny agent:
"Can purchase two at $72 each."

Merchant agent:
"Minimum $76."

Tiny agent:
"$74 if pickup occurs today."

Merchant agent:
"Accepted."

Important restrictions:

Agent negotiation must be limited to a SPECIFIC TRANSACTION.

Do not permit merchants to exchange:

- general future pricing strategy
- competitor margins
- future retail price plans
- coordinated pricing
- broad market strategy

Do not create price-fixing behavior.

The negotiating agents should receive only the minimum necessary transaction information.

Do not share customer identity unless required for fulfillment.

A merchant-to-merchant transaction may require owner approval depending on configured limits.


---

# 14. SALE RESCUE ECONOMIC CHECK

Saving the sale must still make economic sense.

Example:

Customer price:            $119
Merchant acquisition:       -$76
Transfer cost:               -$7
Payment fee:                 -$4
Other cost:                  -$5
--------------------------------
Expected contribution:        $27

Owner minimum contribution:
$15

RESULT:
Proceed.

If margin falls below threshold, smol.ai should recommend declining or asking the customer about alternatives.

Do not optimize purely for revenue.

Consider contribution/margin and risk.


---

# 15. STAFFING FORECASTING

smol.ai may also help determine which days require extra staffing.

Important framing:

The system predicts STAFFING REQUIREMENTS.

It should NOT autonomously determine which individual employee deserves fewer hours.

Possible inputs:

- historical transactions
- revenue
- hourly traffic if available
- online orders
- pickups
- scheduled workshops
- event calendar
- delivery schedules
- day of week
- seasonality
- holidays
- planned promotions

Example:

NEXT WEEK

Monday
Demand: Very Low
Recommendation:
Owner-only likely sufficient

Tuesday
Demand: Low
Recommendation:
Owner-only likely sufficient

Wednesday
Demand: Moderate
Recommendation:
+1 employee from 1–5 PM

Saturday
Demand: Very High
Recommendation:
+2 employees

After the day completes:

Predicted transactions: 4–7
Actual transactions: 6

Forecast result:
accurate

Use results to improve future forecasts.

For hackathon MVP, deterministic or simple statistical forecasting is enough.

Do not build complex ML unless time remains.


---

# 16. RETURN / REFUND LOOP

Long-term product capability:

RETURN
→ inspect
→ determine condition
→ determine whether product can return to sellable inventory
→ calculate refund
→ policy check
→ approval if necessary
→ process refund
→ update inventory
→ update financial state
→ close

This does not need to be built for the initial hackathon.


---

# 17. SUPPLIER RELIABILITY

The system should eventually compare supplier promises with reality.

Example:

Supplier claims:
14-day lead time

Historical last 8 deliveries:
average actual = 21 days

smol.ai may say:

"Supplier currently quotes 14 days, but recent historical fulfillment has averaged 21 days."

This becomes useful in reorder calculations.

Maintain distinction between:

supplier-stated lead time
vs.
observed historical lead time


---

# 18. LEARNING FROM OWNER DECISIONS

The system may learn patterns from owner approvals.

However, it must NEVER silently expand its own authority.

Example:

"You approved this exact purchasing pattern 9 out of 9 times.

Would you like to allow automatic purchases from Supplier X under $75 when:

- SKU was previously purchased
- price increase < 5%
- inventory is below reorder point?"

[Change Policy]
[Keep Approval Required]

Changing authority must itself require explicit owner action.


---

# 19. ACTION STATE MACHINE

Actions should be durable/stateful.

Suggested states:

DETECTED

UNDERSTANDING

INVESTIGATING

PLAN_READY

POLICY_CHECK

WAITING_FOR_APPROVAL

APPROVED

EXECUTING

VERIFYING

RECONCILING

COMPLETED

FAILED

RECOVERING

DISMISSED

Example:

DETECTED
→ INVESTIGATING
→ PLAN_READY
→ WAITING_FOR_APPROVAL

Time passes.

User returns later.

Action must still be:

WAITING_FOR_APPROVAL

User approves.

→ APPROVED
→ EXECUTING
→ VERIFYING
→ RECONCILING
→ COMPLETED

The workflow should not depend on an uninterrupted chat session.


---

# 20. AGENT ARCHITECTURE

Conceptual architecture:

INPUT SOURCES

Email
Shopify/demo commerce data
Calendar
Physical inventory counts
Supplier data
Merchant network
Owner policies

             ↓

PRIVACY / DATA-MINIMIZATION LAYER

             ↓

ORCHESTRATOR

             ↓

SPECIALIZED AGENTS

Email Agent
Inventory Agent
Inventory Detective
Procurement Agent
Opportunity Agent
Staffing Agent
Sale Rescue Agent
Supplier Agent
Verification Agent
Decision/Explanation Agent

             ↓

POLICY ENGINE

             ↓

AUTO-EXECUTE
OR
HUMAN APPROVAL

             ↓

EXECUTION TOOLS

             ↓

VERIFICATION

             ↓

RECONCILIATION

             ↓

AUDIT LOG + BUSINESS MEMORY

             ↺


Do not create many fake agents that independently summarize the same data.

Agents should exist only when they have meaningfully different:

- information
- tools
- responsibilities
- permissions
- outputs

Agent A's result should sometimes trigger Agent B.


---

# 21. SPONSOR TOOL STRATEGY

Sponsor APIs/products should have real jobs.

Do not bolt logos onto the architecture merely to claim usage.

Exact APIs and current docs MUST be checked before implementing because sponsor SDKs may have changed.

## BAND

Use for actual multi-agent communication / delegation.

Example:

InventoryAgent:

"We will stock out before the supplier can replenish."

→ @SupplierAgent

"Check approved sources."

SupplierAgent:

"No approved supplier can meet deadline."

→ @LocalRescueAgent

"Check merchant network."

The agent handoff should change system behavior.

Removing BAND should meaningfully break or simplify the coordination.


## MOSS

Use as local/fast business knowledge retrieval where appropriate.

Possible knowledge:

- supplier rules
- workshop policy
- product compatibility
- internal notes
- business policies
- customer FAQ
- return rules
- inventory notes

Privacy/local retrieval is particularly aligned with smol.ai's trust story.


## TAVILY

Use for external discovery/search only when internal data cannot solve the problem.

Examples:

- discover candidate alternate supplier
- locate current product page
- find external source for replacement item

Do not use Tavily when internal inventory already provides the answer.


## TINYFISH

Use for live web verification after discovery.

Example:

Tavily finds supplier/product candidate.

TinyFish verifies:

- page renders
- correct product
- current price
- current stock
- variant
- relevant current details

Discovery and verification should be separate concepts.


## ZOOWORK

Potential role:

Main workflow/orchestration environment and tool-execution layer.

Particularly useful for:

- execution plans
- tool use
- runtime
- approval gates
- guardrails

Verify current sponsor API/docs before choosing exact implementation.


## NOVITA

Possible model provider for specific LLM operations.

Potential use:

- convert natural-language email into structured event/data
- rank recovery plans
- classify message intent
- explain recommendations

Keep deterministic math/policy outside the model.


## ENTIRE

Use in the development process with Claude/Cursor if appropriate.

Possible value:

- coding-agent session history
- checkpoints
- provenance
- development trace

Do not force Entire into the customer runtime workflow if that is not what it is built for.


---

# 22. RECOMMENDED MVP

DO NOT BUILD THE ENTIRE VISION DURING THE HACKATHON.

The primary demo should implement ONE closed-loop operational story.

Recommended scenario:

## SUPPLIER DELAY → STOCKOUT → RESOLUTION

Starting conditions:

Product:
Pastel Keycap Set

Current inventory:
21

Recent velocity:
1.1 units/day

Original supplier lead time:
14 days

New supplier email:
"Production delay. Lead time is now approximately 35 days."

Step 1:
User imports/pastes/simulates the supplier email.

Step 2:
Email Agent extracts:

lead_time = 35

Step 3:
Inventory Agent calculates:

days_of_supply ≈ 19

Step 4:
System determines:

19 days stock
< 35 day replenishment lead time

STOCKOUT RISK

Step 5:
Investigate:

warehouse inventory
open purchase orders
approved suppliers

No internal resolution.

Step 6:
External discovery searches candidate alternate supplier.

Step 7:
Browser verification verifies candidate.

Example:

100 units
$61
arrives in 6 days

Step 8:
Economics confirms acceptable.

Step 9:
Policy engine evaluates:

approved category ✓
spend $61 > $40 auto threshold ✕

Step 10:
Action Inbox displays:

APPROVAL REQUIRED

Step 11:
User clicks:

APPROVE

Step 12:
Order is executed OR clearly simulated in the hackathon environment.

Step 13:
Confirmation is returned.

Step 14:
smol.ai verifies quantity / cost / ETA.

Step 15:
Inventory/procurement state updates.

Step 16:
Incident closes.

Final result screen:

STOCKOUT PREVENTED

Detected automatically:
30-day supplier delay

Resolved:
100 replacement units secured

Human decisions required:
1

Unrelated emails exposed:
0

STATUS:
CLOSED ✓


---

# 23. SECONDARY DEMO / TEASER FEATURES

Only implement these if the primary loop works.

Possible dashboard cards:

INVENTORY DISCREPANCY
Lavender Keycaps
Expected: 12
Physical: 8
Status: Investigation ready

STAFFING
Tuesday predicted lowest-demand day
Owner-only coverage likely sufficient

OPPORTUNITY
20-person corporate workshop inquiry
Status: Waiting for review

SALE RESCUE
Customer requested unavailable product
Nearby merchants available: 2

These can be partially mocked if clearly labeled.

The primary closed loop must be real.


---

# 24. POSSIBLE X-FACTOR DEMO

If time allows:

Use the merchant-agent rescue flow.

Customer wants a product Tiny does not have.

Tiny agent queries nearby participating merchant agents.

Agents negotiate within explicit boundaries.

System finds a viable transaction.

Policy allows/blocks it.

Sale is rescued.

This could be visually impressive but MUST NOT jeopardize the main workflow.


---

# 25. UI DESIGN

Product should NOT look like a hacker terminal.

It should feel like a polished operations dashboard for a nontechnical small-business owner.

Primary navigation could be:

Overview
Actions
Inventory
Suppliers
Workflows
Policies
Activity

Main landing page:

GOOD MORNING

3 things need your attention.

URGENT
Stockout risk

APPROVAL
Supplier purchase — $61

OPPORTUNITY
Corporate workshop request


Each action card should answer:

1. What happened?
2. Why does it matter?
3. What did smol.ai investigate?
4. What does smol.ai recommend?
5. What evidence supports it?
6. What permission does smol.ai currently have?
7. What does the owner need to do?


Avoid giant model-response paragraphs.


---

# 26. POSSIBLE ACTION CARD

URGENT
STOCKOUT RISK

Pastel Keycap Set

Stock:
21

Current sales rate:
1.1/day

Days remaining:
~19

Supplier lead time:
35 days

Expected gap:
~16 days

smol.ai checked:

✓ warehouse inventory
✓ open POs
✓ approved suppliers
✓ alternate source

Recommended:

Buy 100 units from Supplier B

Cost:
$61

ETA:
6 days

Expected stockout avoided:
Yes

Policy:

Known item ✓
Supplier approved ✓
Cost under $40 ✕


APPROVAL REQUIRED

[Review Evidence]

[Approve $61]

[Dismiss]


---

# 27. TRUST PANEL

An expandable section could show:

WHY THIS ACTION EXISTS

Trigger:
Supplier lead-time change

Sources:
Supplier Email #102
Shopify SKU PASTEL-01
Sales history last 30 days
Supplier B product page

Data sent to AI:
SKU
stock quantity
sales velocity
MOQ
lead time
price

Data NOT accessed:
personal inbox
unrelated customers
payment information

Policy:
Purchases over $40 require approval

Current action:
Waiting for owner


---

# 28. PROPOSED DATA MODEL

Keep schema simple.

## Business

id
name
timezone

## User

id
business_id
role

## Product

id
business_id
sku
name
current_stock
warehouse_stock
cost
sale_price
safety_stock

## InventoryEvent

id
product_id
type
quantity_delta
source
timestamp
metadata

Types:

sale
return
workshop
adjustment
transfer
purchase_receipt
physical_count

## Supplier

id
business_id
name
approved
reliability_score

## SupplierProduct

supplier_id
product_id
supplier_sku
unit_price
moq
lead_time_min
lead_time_max
last_verified_at

## SupplierFact

id
supplier_id
product_id
fact_type
value
source
confidence
observed_at

## EmailSource

id
sender
subject
received_at
approved_for_ai
raw_content optional
sanitized_content optional

## Opportunity

id
type
customer_request
requirements_json
deadline
budget
status

## Action

id
business_id
type
status
risk_level
title
summary
recommended_action
created_at
updated_at

## ActionEvidence

id
action_id
source_type
source_id
summary
confidence

## Policy

id
business_id
action_type
max_auto_amount
require_approval
conditions_json

## Approval

id
action_id
user_id
decision
timestamp

## Execution

id
action_id
type
request_payload
response_payload
status
executed_at

## AuditEvent

id
action_id
actor
event_type
data
timestamp

## Merchant

id
name
location
approved_network_member

## MerchantOffer

id
merchant_id
action_id
sku
quantity
price
transfer_cost
expires_at


---

# 29. DERIVED METRICS

Do not store everything if it can be computed.

Examples:

average_daily_velocity

days_of_supply

reorder_point

estimated_stockout_date

expected_margin

supplier_delay_variance

staffing_demand

These should be deterministic where possible.


---

# 30. ARCHITECTURE PRINCIPLE

Separate:

REASONING

from

AUTHORIZATION

from

EXECUTION.

Example:

LLM:

"Inventory will likely stock out before replenishment."

Deterministic service:

days_supply = 19
lead_time = 35
stockout_risk = true

LLM:

"Supplier B appears to be the best alternative."

Policy engine:

cost = $61
max_auto_spend = $40

result:

APPROVAL REQUIRED

Execution layer:

Only runs after authorization.

This separation is critical.


---

# 31. AGENT OUTPUTS SHOULD BE STRUCTURED

Avoid passing large freeform messages between agents.

Example:

{
  "finding": "stockout_risk",
  "product_id": "pastel-keycaps",
  "days_of_supply": 19.1,
  "current_supplier_lead_time": 35,
  "severity": "high",
  "confidence": 0.97,
  "recommended_next_agent": "supplier_agent"
}

Structured contracts make the application safer and easier to debug.


---

# 32. CONFIDENCE HANDLING

Never pretend the system knows more than it does.

Use:

verified
high confidence
moderate confidence
low confidence
unknown

Example Inventory Detective:

NOT:

"Four keyboards were used during the workshop."

Unless evidence proves it.

Instead:

"Three missing units are consistent with unlogged workshop usage.

Confidence: High.

One additional unit remains unexplained."


---

# 33. OWNER APPROVAL UX

Approval should be attached to an exact action.

Bad:

"Allow smol.ai to manage inventory?"

Good:

"Approve purchase:
100 Pastel Keycap Sets
Supplier B
$61 total
expected delivery Oct 9"

Approval must not silently authorize unrelated future actions.


---

# 34. WORKFLOW RESUMPTION

Important implementation requirement:

Actions waiting for approval must persist.

Approval should resume the existing workflow.

Example:

actionId = abc123

state:

{
  "status": "WAITING_FOR_APPROVAL",
  "next_step": "execute_purchase",
  "candidate_supplier": "...",
  "quantity": 100,
  "total": 61
}

After approval:

resume(abc123)

Do NOT restart the entire LLM conversation.


---

# 35. FAILURE RECOVERY

A real operational workflow must handle failure.

Example:

Agent chooses Supplier B.

Execution fails:
out of stock

Workflow:

EXECUTING
→ FAILED
→ RECOVERING

Then:

try next valid alternative

If new cost exceeds policy threshold:

WAITING_FOR_APPROVAL

Again.

This makes the system feel autonomous rather than scripted.


---

# 36. DEVELOPMENT PRIORITIES

Highest priority:

A. working closed-loop workflow
B. persistent action state
C. deterministic policy gate
D. clear Action Inbox
E. at least one real sponsor-tool integration
F. evidence / trust visualization
G. good presentation flow

Lower priority:

full Shopify OAuth
full Gmail OAuth
production payments
advanced machine learning
complex staffing forecasts
merchant network backend
multiple businesses
complex analytics

Hackathon success depends more on a polished, coherent demo than breadth.


---

# 37. MOCK DATA IS ACCEPTABLE

For data sources that are difficult to integrate during the hackathon, use realistic seeded data.

But clearly distinguish:

REAL:

- sponsor API call
- agent orchestration
- search
- reasoning
- policy logic
- calculations
- workflow state

MOCKED:

- Shopify inventory fixture
- supplier mailbox
- transaction execution
- merchant network

Do not falsely imply mocked operations are real external transactions.


---

# 38. RECOMMENDED DEMO DATA

Business:

Tiny Keyboard Shop Demo

Product:

Pastel Keycap Set

SKU:
PASTEL-01

Retail price:
$49

Cost:
$22

Current store inventory:
21

Warehouse:
0

Recent sales:

last 30 days = 33

approx velocity:
1.1/day

Supplier A:

approved:
true

normal lead time:
14 days

new lead time:
35 days

MOQ:
100

price:
$20/unit

Supplier B:

approved:
true

availability:
100+

unit price:
$21

delivery:
6 days

Example procurement demo order can use smaller dollar values if easier.

Owner auto-spend threshold:

$40

Therefore an order above $40 forces approval.


---

# 39. HACKATHON STORY

Recommended opening:

"Small businesses don't have a data problem. They have a scattered-context problem.

Inventory is in Shopify.
Supplier information is buried in email.
Customer opportunities arrive in the inbox.
Schedules live somewhere else.

And the connection between all of those systems lives in the owner's head."


Then:

"smol.ai gives a small business the operations team it can't afford to hire."


Then demonstrate:

Supplier email arrives.

"Lead time increased to 35 days."

smol.ai extracts the operational fact.

Inventory analysis shows:

19 days of inventory remain.

Stockout predicted.

smol.ai investigates.

Finds an alternate supplier.

Verifies availability.

Creates a purchase plan.

But:

$61 > $40 owner spending limit.

System stops.

"Approval required."

Owner approves.

Agent completes the action.

Confirmation is verified.

Incident closes.


Then show:

STOCKOUT PREVENTED

1 human decision

0 unrelated emails exposed

STATUS: CLOSED


---

# 40. TRUST STORY

Explain:

"We're not asking the owner to hand an AI the keys to the business."

Instead:

"The owner defines exactly:

what the AI may see,
what it may prepare,
what it may execute,
and when it must stop."


Then:

"The model can recommend spending $61.

It cannot decide that it is allowed to spend $61."


This distinction should be very clear.


---

# 41. POSSIBLE FINAL SLIDE

smol.ai

AI operations for very small businesses.

DETECT
INVESTIGATE
ACT
VERIFY
RECONCILE
REPEAT

with:

least access
bounded authority
human control


Long-term capabilities:

Inventory
Procurement
Supplier intelligence
Sale rescue
Opportunity feasibility
Staffing
Returns
Local merchant coordination


---

# 42. WHAT NOT TO DO

Do not build a generic chat UI.

Do not make every action an LLM call.

Do not give the LLM direct unrestricted purchasing authority.

Do not claim the AI discovered the cause of inventory loss unless evidence proves it.

Do not expose all emails unnecessarily.

Do not make approval fake.

Do not build 10 half-working workflows.

Do not spend most hackathon time on login/auth.

Do not build complex forecasting before the core loop works.

Do not overuse sponsors merely for logos.

Do not allow web/email content to alter system policy.

Do not auto-expand permissions.

Do not obscure whether data is mocked vs real.


---

# 43. IMPLEMENTATION STRATEGY FOR CURSOR

Before modifying the project:

1. Inspect the entire repository.
2. Identify existing stack, dependencies, routes, state management, data structures, and styles.
3. Do not rewrite working architecture unless necessary.
4. Propose a minimal implementation plan.
5. Identify which sponsor integrations are actually realistic within hackathon time.
6. Implement the primary closed loop first.
7. Keep changes incremental and test after each meaningful step.
8. Prefer typed structured data.
9. Keep AI outputs schema-constrained.
10. Keep authorization deterministic.
11. Preserve clear separation between mocked and real integrations.
12. Prioritize demo reliability.


---

# 44. HOW CLAUDE SHOULD HELP

Claude should act as:

- product architect
- security reviewer
- workflow designer
- hackathon strategist
- code reviewer
- technical debugger
- pitch reviewer

When analyzing a feature, always ask:

Does this improve the main demo?

Does it make the workflow more complete?

Does it demonstrate sponsor technology meaningfully?

Does it improve owner trust?

Can one developer realistically finish it?

Does it increase demo failure risk?

Is deterministic code better than AI here?


---

# 45. QUESTIONS TO RESOLVE BEFORE BUILDING

Determine from the current hackathon docs and sponsor documentation:

- Which sponsor tools are mandatory, optional, or prize-specific?
- Exact BAND integration/API.
- Exact ZooWork workflow model.
- Exact Moss SDK/API.
- Exact Tavily endpoints needed.
- Exact TinyFish integration.
- Exact Novita model/API.
- Whether Entire should be used only for dev provenance.
- Submission deadline.
- demo time limit.
- required hosting/submission format.
- whether source code must be public.
- whether judging gives explicit bonus for sponsor count.
- whether mocked commerce execution is acceptable.

Do not assume sponsor APIs from memory.

Verify current docs before coding.


---

# 46. NORTH STAR

At any point during implementation, use this test:

Can we show one business problem entering smol.ai and watch smol.ai carry it all the way to a verified resolution while proving that the owner remained in control?

If yes, the project is succeeding.

If not, prioritize completing that loop before adding features.


---

# 47. PRODUCT VISION IN ONE SENTENCE

smol.ai is a privacy-first autonomous operations agent that gives very small businesses the operational intelligence of a larger company without requiring them to surrender control to AI.


# END MASTER PROJECT CONTEXT
