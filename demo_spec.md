# Demo specification

This is the reorder dataset and screen copy. Calculations in the app must match this file. Requirements are in [prd.md](prd.md). The hackathon boundary is in [mvp_scope.md](mvp_scope.md). The four other previews use their own fixtures in code and tests; they do not change these reorder numbers.

Fictional data only. Purchases and deliveries are simulated. No private inbox is read, and no real order is sent.

## Shared data

- Product: Workshop Supply Pack
- SKU: `DEMO-SKU-001`
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
- Unit price: $0.54
- Previous unit price: $0.54
- Merchandise subtotal: $54
- Shipping: $7
- Total: $61
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

Subject: Updated lead time for Workshop Supply Pack

```text
Hello,

The lead time for Workshop Supply Pack has increased from 14 days to approximately 35 days. Please use the updated estimate when planning your next order.

Supplier A
```

Start interactive demo simulates this message arriving through an already configured monitoring rule. The visitor does not upload or label it.

## Interface copy

Landing:

- “Your operations, followed through.”
- “smolstuff connects business signals, investigates what needs attention, and completes routine workflows within rules you control.”
- Button: “Start interactive demo”
- Notice: “Fictional business data. Purchases and deliveries are simulated.”

Risk card:

- “Supplier delay puts inventory at risk”
- “You have about 19 days of stock. Your supplier now needs 35 days to replenish it.”
- “There is about a 16-day gap. Warehouse stock and existing orders cannot cover the gap. Supplier B offers an alternative with an estimated 6-day delivery.”
- “Order 100 units from Supplier B”
- “$54 merchandise + $7 shipping = $61 total”
- “Minimum order: 100 units. This buys more than the immediate shortage.”
- “This purchase exceeds your below-$40 automatic spending limit. The other configured checks pass.”
- Buttons: “Review evidence”, “Approve simulated $61 order”, “Decline”

After approval:

- “Order confirmed — awaiting receipt”
- “Confirmation matches the approved product, quantity, and total.”
- “Simulate receiving 100 units”

Completion:

- “Replenishment workflow completed”
- “100 units received. Available inventory updated from 21 to 121.”
- “1 owner approval. Receipt verified. Inventory reconciled.”

Reset: “Reset demo”

Show a state only after the action that creates it has succeeded.

## Evidence

The expandable evidence panel shows the synthetic message, sales history and calculations, inventory and open-order checks, Supplier B’s seeded offer, the policy result, and approval, confirmation, and receipt records.

A seeded offer is labeled seeded. It is not live web verification. Sponsor or adapter lines come from execution records. The main screen stays on the business decision.

## Acceptance

1. A new visitor can start without credentials or private business data.
2. Displayed calculations match this specification.
3. The $61 order cannot execute before approval.
4. Declining leaves inventory unchanged.
5. Confirmation alone leaves available inventory at 21.
6. Simulated receipt changes inventory to 121 and completes the workflow.
7. Repeated approval or receipt clicks do not duplicate actions.
8. Refreshing preserves the workflow.
9. **Reset demo** on the reorder screen clears that reorder workflow and its tool records. It does not delete the visitor’s session file, so the other previews in the same session remain.
10. Separate visitors do not share approvals or inventory.
11. No real purchase, external message, or private inbox access occurs.
