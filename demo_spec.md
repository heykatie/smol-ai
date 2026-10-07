# Demo specification

This is the reorder dataset and screen copy. Calculations in the app must match this file. Requirements are in [prd.md](prd.md). The MVP boundary is in [mvp_scope.md](mvp_scope.md). Historical hackathon material is in [docs/archive/HACKATHON_CONTEXT.md](docs/archive/HACKATHON_CONTEXT.md). The four other previews use their own fixtures in code and tests; they do not change these reorder numbers.

Fictional data only. Purchases and deliveries are simulated. No private inbox is read, and no real order is sent.

## Shared data

- Product: Quiet linear switch
- Catalog line: 5-pin, factory lubricated, sold by the switch. Fictional. Not copied from a real shop.
- Item ID: `DEMO-ITM-001`
- Currency: USD
- Units sold over the last 10 complete days: `[1, 2, 0, 1, 1, 2, 1, 0, 2, 1]`
- Total sold: 11
- Average daily sales: 1.1 units
- Available inventory: 21
- Reservations: 0
- Warehouse stock: 0
- Open purchase orders: 0
- Original supplier lead time: 14 days
- Updated supplier lead time: 35 days

Supplier B:

- Approved supplier
- Known, previously purchased SKU
- Available quantity: 100
- Minimum order quantity: 100
- Unit price: $1.82
- Previous unit price: $1.82
- Merchandise subtotal: $182
- Shipping: $7
- Total: $189
- Estimated delivery: 6 days
- No other taxes or fees

Purchase policy:

- An autonomous purchase must total strictly less than $40.
- Supplier, SKU, quantity, price, evidence, and aggregate-budget checks must also pass.
- For this fixture, the spending threshold is the only reason the purchase needs approval.

## Calculations

Code, not a model, calculates:

- Sales velocity: `11 / 10 = 1.1` units/day
- Days of supply: `21 / 1.1 ≈ 19.1` days
- Projected gap: `35 - 19.1 ≈ 15.9` days

The card says about 19 days of supply and about a 16-day gap.

The 100-unit quantity is Supplier B’s minimum order. It is more than the immediate shortage. It is not an optimized forecast.

Receipt does not advance sales or subtract extra consumption:

- Before receipt: 21 available
- Receive: 100
- After receipt: 121 available

The six-day delivery is a supplier term. The receipt control is an accelerated simulation. It does not mean six days of sales were simulated.

## Supplier message

Subject: Updated lead time for Quiet linear switch

```text
Hello,

The lead time for Quiet linear switch has increased from 14 days to approximately 35 days. Please use the updated estimate when planning your next order.

Supplier A
```

Start interactive demo simulates this message arriving through an already configured monitoring rule. The visitor does not upload or label it.

## Interface copy

Landing:

- “Your operations, followed through.”
- “smolstuff connects business signals, investigates what needs attention, and completes routine workflows within rules you control.”
- Button: “Start interactive demo”
- Notice: “Fictional business data. Purchases and deliveries are simulated.”

Surfaces: `/demo` is the **demo tour** (no login) — demo workflows, demo wording, and a **small demo catalog** so inventory can show `DEMO-ITM-001` updating after receipt without presenting a full specialty-shop assortment. The dense seeded catalog (~492 fictional SKUs) is for the practice-owner / logged-in surface (login not shipped). Product home `/` states both.

Happy path (demo tour `/demo`) after start:

1. **Review packet** — gap, Supplier B terms, MOQ, policy. Button: “Continue to terms”. Decline/Reset available. Approve is not shown yet.
2. **Negotiate** — Accept $189 terms, or send one counter. Counter replies that Supplier B **holds at $189** (no invented discount). Then Accept to continue.
3. **Draft message** — editable practice PO email. Button: “Send simulated draft”.
4. **Approve** — “Approve simulated $189 order” / Decline. Approval authorizes spend only; it does not submit or confirm.
5. **Submit** — “Submit simulated order”.
6. **Confirm** — “Confirm supplier match”.
7. **Awaiting receipt** — “Simulate receiving 100 units”; links to **View confirmation** and **Purchase receipt** in evidence (not inventory). Stock still 21.
8. **Completed** — “View Quiet linear switch in inventory” (`/demo?scenario=inventory&q=DEMO-ITM-001`) plus Reset.

Risk / decision copy (ready to approve):

- “Supplier delay puts inventory at risk”
- “You have about 19 days of stock. Your usual supplier now needs 35 days.”
- “There is about a 16-day gap… Supplier B… Minimum order: 100 units… below-$40…”
- “Order 100 units from Supplier B for $189”
- “$182 merchandise + $7 shipping = $189 total”

Completion:

- “Replenishment workflow completed”
- “100 units received. Available inventory updated from 21 to 121.”
- “1 owner approval. Simulated receipt recorded. Inventory reconciled.”

Reset: “Reset demo”

Show a state only after the action that creates it has succeeded.

## Evidence

The expandable evidence panel shows the synthetic message, sales history and calculations, inventory and open-order checks, Supplier B’s seeded offer, the policy result, and approval, confirmation, and receipt records.

A seeded offer is labeled seeded. It is not live web verification. Sponsor or adapter lines come from execution records. The main screen stays on the business decision.

## Acceptance

1. A new visitor can start without credentials or private business data.
2. Displayed calculations match this specification.
3. Approve is unavailable until review → negotiate (accept) → draft are done. Approve alone does not submit or confirm.
4. The $189 order cannot execute before approval; submit and confirm are separate steps after approval.
5. A counteroffer on this fixture holds at $189; happy-path money approval still binds to $189.
6. Declining leaves inventory unchanged.
7. Confirmation alone leaves available inventory at 21.
8. Simulated receipt changes inventory to 121 and completes the workflow.
9. Completed offers an inventory deep-link to `DEMO-ITM-001`; awaiting receipt links to confirmation/receipt evidence instead.
10. Repeated approval, submit, confirm, or receipt clicks do not duplicate actions.
11. Refreshing preserves the workflow and prep phase.
12. **Reset demo** on the reorder screen clears that reorder workflow, prep state, and its tool records. It does not delete the visitor’s session file, so the other previews in the same session remain.
13. Separate visitors do not share approvals or inventory.
14. No real purchase, external message, or private inbox access occurs.

## Presentation contract

Render the fixed calculations and lifecycle inside the same dark shell as the Daily brief and four previews. Reorder empty/approval/receipt/completion states must not switch to a legacy light page. docs/DESIGN.md owns visual tokens; numeric fixtures above remain unchanged. docs/STATUS.md distinguishes implementation, test and provider evidence.
