# smolstuff design specification

Confirmed direction: **modern, clean, sleek, dark mode, stylish and gently cute**. The product is an approachable operations team for AI-skeptical small-business owners. Make it feel calm, useful and trustworthy. A small smile-mark and restrained sparkle supply personality; business decisions and evidence take priority.

## Shared system

`src/smolstuff/ui_theme.py` owns CSS tokens. `demo_ui.shell` owns page title, navigation, skip link, workspace frame and demo/privacy notice. Dashboard, inventory, reorder (including empty/approval/receipt/completion), workshop, detective, sale rescue, staffing and recoverable errors use this shell. Do not introduce another page-specific light theme or duplicate token definitions.

| Token | Value / purpose |
| --- | --- |
| Background | #101115, charcoal canvas |
| Surface / raised | #1b1d24 / #22252e, layered cards and controls |
| Primary text / secondary | #f5f3fb / #b1b3c3 |
| Accent | #c4b5fd, lavender navigation and primary actions; dark button text |
| Success / focus | #a8e8ce, mint; always accompanied by status text |
| Input boundary | #747988 against dark input fill; visible without relying on placeholder text |
| Typography | System sans-serif stack; no remote font or tracking dependency |
| Shape | 20px cards, 24px hero, 11px controls, restrained pill statuses |
| Spacing | 16px card gap, 20–24px card padding, generous content margins |

Desktop uses a left navigation rail and two-column dashboard cards. Below 760px navigation wraps across the top, cards become one column and counts use two columns. Content and buttons wrap; evidence uses pre-wrap and overflow wrapping. Keep empty groups out of the main card list while retaining accurate zero counts. A fresh visitor sees five discoverable demos plus an Inventory tab rather than long empty status sections.

## Interaction and accessibility

Use labeled native forms/buttons/details, meaningful link names, active navigation via aria-current, a skip-to-content link, visible mint keyboard focus and text status labels. Buttons target at least 44px height. Show a specific main decision and clear consequence; simulation labels must remain visible. Honor prefers-reduced-motion; decorative mark/icons are aria-hidden. Avoid fake notifications, invented savings/revenue, online indicators or a suggestion that real inbox monitoring runs.

Reference: [W3C WCAG 2.2 quick reference](https://www.w3.org/WAI/WCAG22/quickref/) for keyboard access, contrast, reflow, labels and focus. WCAG 2.2 AA is a target, not an audited certification. Check color contrast, navigation/focus, mobile reflow, forms, errors and displayed values on actual screens. Automated checks do not establish full compliance.

Recoverable action/number errors render the shared dark shell with an alert, a safe explanation and a route back to the Daily brief. Invalid conversion cannot save a scenario. General server/request hardening remains a separate launch gate.

## Approval and trust copy

The owner must know what is being authorized. Reorder shows quantity, counterparty, landed total, spending policy and evidence. Workshop preview currently bundles a synthetic commitment/preparation authorization; production must separate those action permissions. Merchant simulators must never be described as live nearby agents. Staffing saves coverage hours, not a named worker schedule. Verified receipt is distinct from order confirmation.

## Acceptance for this UI change

- All seven routes (daily brief, inventory, reorder, four previews) and empty/error screens share the dark frame, typography and controls.
- Reorder remains $189, one money approval (after review/negotiate/draft), separate submit/confirm, stock 21 until receipt and 121 after full receipt; completed links to the catalog line.
- Inventory uses one scannable catalog table (same columns on both surfaces) with sticky product column + sticky header, ordered identity → availability → quantities → ops: **Product** (name + merchandising differentiators) / **Category** (desktop short labels: Desk mats / Configs) / **Status** / **Available** / **Reserved** / **Incoming** / **In transit** / **Unavailable** / **Last counted** / **Issue**. Column headers are sortable: Category by short label; Status by severity (Out of stock → Available); qty columns numeric; Last counted by date; Issue by sidebar demo order (Reorder → Workshop → Detective) then workflow. **Issue** combines workflow pills (Decide / Waiting / Active / Done; Idle browse rows show —) with the open problem link (Lead-time risk / Event shortfall / Count mismatch). SKU, full category, list/cost live in **Details**. Filter matches `data-search` on catalog rows only. **Status** pills: Available (promiseable &gt; 0) / Incoming / Unavailable (holds only, Available = 0) / In transit / Out of stock. Item ID is internal (`DEMO-ITM-…`); merchant SKU is optional and distinct (`MS-…`) when present. Hover Available for Front store · Warehouse split. Zero holds render as —. Below 760px, phone keeps Product / Status / Available / Issue. **Surface split:** `/try` demo tour shows a **small demo catalog** (`SANDBOX_CATALOG` — reorder + workshop/detective + a few samples). The dense ~492-SKU specialty-shop assortment (`SEEDED_CATALOG`) is for the practice-owner / logged-in surface (login not shipped; owner mode is structured in code). Quiet linear: available 21 / Available / Lead-time risk; after approve Incoming / Waiting; after receipt available 121, Available / Done.
- Workshop shows $700 contribution / eight complete seats left after BOM consume; detective preserves the original count and resolves on recount; merchant defaults show $21/$27; staffing Saturday with workshop shows 14 workload hours/two blocks.
- All routes reflow without horizontal page overflow at 390px and 320px; input/button content remains legible.
- Keyboard can reach navigation, forms and evidence; focus is visible and skip link reaches main content.
- Session counts derive from persisted state and simulation/provider labels remain accurate.
- docs/STATUS.md records the checks actually performed and any remaining limitations.
