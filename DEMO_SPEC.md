# Demo specification

This is the dataset and screen copy for the public smolstuff demo. [PRD.md](PRD.md) defines release requirements; [MVP_SCOPE.md](MVP_SCOPE.md) summarizes staged scope. Calculations in the app must match this file.

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
- Unit-price increase must be strictly below 5%; exactly 5% requires approval.
- Quantity range is 1–200 inclusive. Aggregate budget remaining is a seeded $200.
- Evidence flags are seeded true; they are not independent live verification.
- For this fixture, the spending threshold is the only reason the purchase needs approval.
- Current code compares each purchase against a supplied budget; it does not reserve or decrement a shared budget. See the implementation contract before supporting multiple orders.

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
- “Warehouse stock and existing orders cannot cover the gap. Supplier B offers an alternative with an estimated six-day delivery.”
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
9. Reset restores the fixture and clears that session’s activity.
10. Separate visitors do not share approvals or inventory.
11. No real purchase, external message, or private inbox access occurs.

## Short receipt and evidence boundaries

The core/action handler supports 97 received → stock 118, three outstanding → later three received → stock 121 and completion. Repeated receipt keys do not add stock again. The default receipt page does not offer the short-receipt action; expose it only with a tested UI. Do not call this Inventory Detective cause investigation or claim a credit/replacement was obtained.

The demo does not authenticate an owner. Clicking approve records the synthetic actor `owner` within that visitor's isolated demo. No real purchase, message, policy change, or private inbox access is authorized by this mechanism.

The demo fixture has no live supplier expiry, customer PII, taxes beyond the stated zero, or simulated intervening sales. Source freshness and verification flags are fixtures. Keep these assumptions visible rather than treating them as production guarantees.
