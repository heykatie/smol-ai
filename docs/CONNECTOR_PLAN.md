# Future connectors and offline data foundation

Researched October 6, 2026 against the official documentation linked below. This is a broad connector inventory for retail and bakery operations, not an exhaustive list of every vendor or proof that a merchant account grants access. APIs, commercial terms, app review, plans and regional availability must be rechecked when an adapter is selected.

The current implementation is an **offline synthetic snapshot harness** with two fictional datasets. There are no live commerce/calendar/mail adapters, OAuth grants, background workers, hosted migrations or connector UI. Existing demo inventory and workflow rules are untouched. [STATUS.md](STATUS.md) owns verification evidence; [SECURITY_AND_DECISIONS.md](SECURITY_AND_DECISIONS.md) still gates real ingestion and execution.

## Recommended order

1. Start with Square, Shopify, Google Calendar and explicitly mapped Google Sheets. Together these can supply commerce facts, timing and records the POS does not track.
2. After authenticated shop isolation and read-only ingestion are verified, add one email provider for permitted inquiries and supplier signals.
3. Add accounting, staffing or shipping only when an actual pilot workflow needs them. Preserve the software a shop already uses.
4. Treat delivery marketplaces and payroll as separate access projects; never promise them based on merchant login alone.

This order is an engineering recommendation, not a confirmed choice of inventory authority, a new business commitment, or permission to enable a connector. Keep costs down through bounded polling, selected resources, webhook-triggered refetch where available, and reconciliation rather than repeatedly downloading everything.

## Commerce and inventory

“Possible writes” describes vendor capabilities to evaluate later. **No outbound writes are implemented or authorized by this plan.**

| Connector and official source | Candidate read data → smolstuff use | Synchronization/access considerations | Possible writes to evaluate later |
| --- | --- | --- | --- |
| [Square Orders](https://developer.squareup.com/docs/orders-api/what-it-does), [Inventory](https://developer.squareup.com/docs/inventory-api/what-it-does), [Invoices](https://developer.squareup.com/docs/invoices-api/overview) | Order IDs, locations, items/modifiers, totals, fulfillment; catalog-linked counts/states; invoice status and amounts → order queue, inventory observations, payment follow-up | Merchant OAuth with exact resource read scopes; selected locations; webhook/refetch plus reconciliation. Invoice read requires INVOICES_READ. Join invoice to its order for itemization. A completed provider order must not automatically mean physical pickup completed. | Order/inventory mutations and invoice creation/publication need separate scopes and action approval. Publishing can trigger communications or collection. Invoice features have API/plan limitations. |
| [Shopify inventory](https://shopify.dev/docs/apps/build/orders-fulfillment/inventory-management-apps), [webhooks](https://shopify.dev/docs/apps/build/webhooks), [protected data](https://shopify.dev/docs/apps/launch/protected-customer-data) | Products/variants, location inventory states, order lines, financial/fulfillment facts → retail demand and replenishment | Use supported versioned Admin GraphQL API and granted scopes. Protected order/customer data access depends on app distribution/review; avoid unnecessary PII. Some inventory states do not emit quantity-change webhooks; reconcile snapshots. | Inventory changes, product updates, fulfillment and draft orders require resource-specific permissions and deterministic checks. |
| [WooCommerce](https://woocommerce.com/document/woocommerce-rest-api/) | Orders, products/variations and stock via its REST API → another commerce source | Merchant-issued read keys; WordPress installation/plugin/version behavior varies. Read-only keys are available. Endpoint mappings and webhooks need adapter-level verification. | Product/order updates with write access; never request write keys for read-only onboarding. |
| [Clover](https://docs.clover.com/dev/docs/making-rest-api-calls), [orders](https://docs.clover.com/dev/docs/working-with-orders) | Merchant inventory, orders and payment details → stock/sales observations | Merchant OAuth; region-specific environment and resource permissions; reconcile provider totals. | Inventory/order changes, with payment execution separately gated. |
| [Toast](https://dev.toasttab.com/doc/devguide/apiOverview.html), [standard access](https://support.toasttab.com/en/article/Standard-API-Access), [stock](https://doc.toasttab.com/doc/devguide/apiStock.html) | Menu, orders, restaurant stock availability → prepared-item demand and availability | Standard API access is read-only; other integration access differs. Menu stock is not proof of ingredient quantities, recipes or lot expiry. Unknown availability remains unknown in smolstuff. | Evaluate only through an eligible integration program; do not infer write permission from standard access. |
| [Lightspeed Retail X-Series](https://x-series-api.lightspeedhq.com/reference/search-1), [inventory records](https://x-series-api.lightspeedhq.com/reference/listinventoryrecords) | Products/sales and outlet inventory records → retail stock/demand | Dedicated X-Series adapter; account authorization, API version and deletion handling need selection-time checks. | Evaluate supported product/inventory endpoints separately. |
| [Lightspeed Retail R-Series](https://retail-support.lightspeedhq.com/hc/en-us/articles/229129268-Integrating-with-the-Lightspeed-Retail-POS-R-Series-API) | Retail API integration candidate | Different API from X-Series; field mapping, scopes and sync behavior not yet verified here. | Deferred until endpoint research. |
| [Etsy](https://developers.etsy.com/documentation/) | Inventory, sales orders and shop records → marketplace demand | Seller-app access is own-shop only; broader smolstuff use requires an appropriate reviewed app/access model. Private data requires OAuth; buyer email is separate access. No scraping fallback. | Listing/inventory/shop updates only with appropriate grants and review. |
| [Amazon SP-API](https://developer-docs.amazon/sp-api/docs/what-is-the-selling-partner-api) | Orders, inventory, shipments, payment/financial reports → marketplace observations | Registered application and selling-partner authorization; roles, restricted data and report availability must be checked per endpoint. | Listing, stock and shipment updates under separately granted authority. |

Catalog counts are not universal ingredient ledgers. None of the sources above establish that a bakery uses a particular recipe, tracks batches, or records expiry. Those facts require owner-maintained records or a separately verified inventory system.

## Calendar, records and inquiries

| Connector and official source | Candidate read data → use | Access/sync limits and possible later writes |
| --- | --- | --- |
| [Google Calendar](https://developers.google.com/workspace/calendar/api/guides/sync) | Events, start/end/timezone, status, recurring instances → holds, commitments and capacity context | Selected calendars and narrow scopes; incremental sync tokens, pagination and full resync on invalid token. Recurrence, all-day dates, cancellations and daylight saving need native-adapter tests. Event status never proves payment or production readiness. Event creation/update requires separate write access. |
| [Google Sheets](https://developers.google.com/workspace/sheets/api/guides/concepts) | Selected cell ranges → recipes, batch expiry, manual counts, cost inputs, order details or staffing templates | Explicit spreadsheet/tab/column mapping and durable row IDs; row number is not identity. Formula output and edited/reordered/deleted rows need reconciliation. Cell read/write capability does not create a universal business schema. Initial ingestion should read selected ranges only. |
| [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes) | Permitted message headers/body excerpts and thread references → inquiries, supplier updates and reply preparation | Metadata/read access are restricted scopes; server handling can require verification/security assessment. App filtering is not provider-enforced mailbox isolation. Prefer dedicated/routed operations mail. Gmail compose permits send as well as drafts; keep drafts inside smolstuff initially. |
| [Microsoft Graph mail delta](https://learn.microsoft.com/en-us/graph/api/message-delta?view=graph-rest-1.0) | Folder message changes → permitted inquiries and supplier signals | Folder-scoped delta paging and permissions; body access/send is separate. Outlook calendar is another candidate needing its own event adapter research. No mail adapter is implemented. |
| [Calendly events/webhooks](https://developer.calendly.com/docs/api-guides/receive-data-from-scheduled-events-in-real-time-with-webhook-subscriptions), [plan limits](https://developer.calendly.com/docs/getting-started/frequently-asked-questions) | Scheduled events, invitees and cancellation/reschedule notifications → appointment context | Token/OAuth permissions and user/organization scope; webhooks require an eligible paid plan. Collect minimized event references rather than unrestricted invitee details. |
| [Typeform](https://www.typeform.com/developers/) | Submitted answers and submission IDs → structured inquiry intake | Responses API or submission webhooks; grant access only to selected forms; schema changes require mapping updates. A response is a request, not an accepted order. |
| [Notion](https://developers.notion.com/reference/intro) | Accessible pages/databases → policies, reference material, structured operations records | Explicit content access and versioned property mapping; not automatically authoritative inventory. Supported page/property writes can be evaluated later. |

## Accounting, staffing, delivery and communications

| Connector and official source | Candidate read data → use | Access/sync limits and possible later writes |
| --- | --- | --- |
| [QuickBooks Online PurchaseOrder reference](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/purchaseorder), [webhooks](https://static.developer.intuit.com/output_html/qbo/docs/develop/webhooks.html) | Accounting entities, purchase orders and change notifications → procurement/accounting reconciliation | OAuth company scope, entity permissions and current partner terms; webhook entity references need refetch. Extend invoice/bill mappings only after endpoint verification. Book entries do not prove physical receiving. |
| [Xero invoices](https://developer.xero.com/documentation/api/accounting/invoices), [payments](https://developer.xero.com/documentation/api/accounting/payments) | Sales invoices, purchase bills and linked payment records → receivables/payables follow-up | Authorized tenant and accounting scopes; provider IDs, currency and status preserved. Invoice/bill/payment writes need separate approvals; never duplicate a Square invoice in accounting without an explicit mapping. |
| [Stripe invoices](https://docs.stripe.com/api/invoices) | Invoice amounts/status and invoice events → payment follow-up | Account-scoped API access and verified webhooks; a paid event can include an out-of-band paid marking. Finalization/payment/sending can cause collection or communications. No card data is needed in smolstuff. |
| [7shifts](https://developers.7shifts.com/docs/getting-started) | Scheduling, labor, sales and employee data → coverage context | Company developer access and exact endpoint permissions. Availability/time-off support must be checked before promising a field mapping. Employee PII/payroll excluded from these fixtures. Scheduling writes deferred. |
| [Gusto Embedded Payroll](https://docs.gusto.com/embedded-payroll/v2026-02-01/docs/introduction) | Payroll-domain candidate, separate from ordinary shop scheduling | Partner onboarding; an Embedded Payroll integration is not the same as connecting an existing Gusto account. Use its separate App Integration docs for that evaluation. Not an initial connector; no payroll/tax/bank records seeded. |
| [DoorDash Marketplace](https://developer.doordash.com/en-US/docs/marketplace/faq/getting_started/) | Eligible merchant order/menu integration → delivery order queue | Limited partner access; merchant credentials alone are insufficient. DoorDash Drive courier integration is different and does not grant marketplace order access. Acceptance/cancellation/menu writes are consequential. |
| [Uber Eats](https://developer.uber.com/docs/eats/introduction) | Store, menu and order integration → delivery order queue | Integration/partner access and endpoint scopes need approval. No promise of accessible account data until granted. Menu/order operations deferred. |
| [Grubhub orders](https://grubhub-developers.zendesk.com/hc/en-us/articles/115002713846-Orders), [authentication](https://grubhub-developers.zendesk.com/hc/en-us/articles/360000061003-Authentication) | Partner order records → delivery order context | Partner authentication and signed requests; use provider UUID, not short display order number. No direct adapter without partner access. |
| [Shippo tracking](https://docs.goshippo.com/shippoapi/public-api/tracking-status/gettrack) | Carrier/tracking status and shipment references → shipping exceptions | Provider access; carrier coverage and source identity verified per adapter. Label creation/purchase is separate from tracking. Delivered status does not automatically reconcile purchase receiving. |
| [Twilio Messaging](https://www.twilio.com/docs/messaging/api) | Account message history and delivery status → approved communication follow-up | Account access, consent and sender/channel requirements; SMS/WhatsApp are not unrestricted inbox imports. Sending costs and messaging authority require separate decisions. No phone numbers or messages seeded. |

The table covers 26 vendor/product entries, treating Google Calendar, Sheets and Gmail as separate connectors and Lightspeed versions separately. It does not claim every individual endpoint was inspected or access was tested.

Further candidates, **not capability-verified in this pass**: Airtable (documentation fetch failed), eBay (documentation fetch failed), Homebase, Deputy, When I Work, Wix, Squarespace Commerce, Ecwid, BigCommerce, ShipStation, EasyPost, Slack, Teams messaging, SendGrid, direct WhatsApp/Instagram, Jotform and industry recipe/inventory tools. CSV/JSON imports remain an access-independent fallback. Zapier, Make and n8n can transport authorized events later; they do not expand provider access or replace identity, validation and deduplication checks. No scraper-based connector fallback is planned.

## Data flow and ownership

```text
Future authorized provider read / selected file
  -> provider adapter: minimize, map units/state, retain source identity
  -> normalized source snapshots + provenance
  -> explicit product/order mappings and conflict review
  -> shop read models -> workflow preparation
  -> separate deterministic approval/execution gates for outbound actions
```

Proposed ownership defaults, to confirm per shop before live onboarding:

- POS supplies commerce observations for the fields it actually tracks.
- Calendar supplies event timing/status; it does not own payment or order acceptance.
- Sheets supplies specifically mapped operational fields, not an automatic override of POS stock.
- smolstuff owns workflow/approval records, role grants and approved operational decisions.
- Accounting supplies accounting/payment observations; reconciliation establishes which records refer to the same transaction.
- A delivery order may already appear in the POS. Link source IDs explicitly before counting demand/revenue; do not merge on customer name, amount or nearby timestamp.
- Recipe yield/ingredient quantities, shelf-life policy, capacity and missing custom-order details stay explicit inputs. Do not infer them from an item name or invent a universal bakery rule.

## Implemented normalized contract

[connector_sync.py](../src/smolstuff/connector_sync.py) supports 13 record kinds: product, inventory, order, payment, invoice, calendar_event, lot, recipe, shift, availability, inquiry, purchase_order and shipment.

Each source record requires kind, external_id, source_updated_at, observed_at, origin, deleted and minimized data. Trusted caller context selects shop and connection. The stored identity is (shop, connection, kind, external ID); the connection binds provider and allowed kinds. Payloads cannot supply shop/connection/role/approval/secrets. Only the two synthetic practice shop IDs and origin=simulated are accepted.

| Kind | Minimal normalized facts |
| --- | --- |
| Product | Source product ID; SKU, name, unit; optional location/active |
| Inventory | Product/location, decimal-string quantity, explicit unit and stock state |
| Order | Item product/quantity/unit/unit-price minor units; total/currency; source state; independent payment and fulfillment states |
| Payment / invoice | Referenced order, explicit currency and integer minor units; payment amount/status or invoice total/balance/status |
| Calendar / shift / availability | Aware start/end, IANA timezone and status; calendar title or pseudonymous employee reference |
| Lot | Product/location, quantity/unit, explicit expiry date and optional batch |
| Recipe | Product, yield quantity/unit and ingredient quantities/units |
| Inquiry | Channel, status and bounded requirements; no raw mail body or contact details |
| Purchase order / shipment | Expected items/totals/status or order/tracking/status; does not constitute a received inventory movement |

Unknown payment/fulfillment is retained. Quantities never use binary floats; money never uses floating dollars. Currency codes are syntactically validated, not converted; minor-unit interpretation needs the future adapter's currency metadata. Item sums are not forced equal to order totals because tax, discounts and fees may intervene. Unit conversion and SKU mapping are not inferred.

Inventory snapshots replace the same source observation; they are never added as movements. A sheet count and a POS count remain separate observations. Source references such as product_id and order_ref are **not verified joins**: mappings must specify provider/connection/shop before a production read model combines them.

## Replay and failure behavior

The dedicated SQLite store persists source snapshots, connection state and completed-scan cursors. It is separate from existing demo and membership stores; no live database migrations are run.

- Duplicate source revision and identical facts produce duplicate, without increasing inventory.
- Older source timestamps produce stale, preserving the newer snapshot.
- Equal source revision with different facts raises SyncConflict and rolls back that page, including its cursor.
- Newer tombstones remove records from active reads while preserving source identity/version to block older resurrection.
- Invalid pages roll back entirely. Intermediate pages may persist records, but do not advance the completed-scan checkpoint; restart safely replays them.
- Revoked connections reject new pages; replay registration does not reactivate them.
- Timestamps with up to six fractional digits normalize to UTC for ordering; higher precision is rejected rather than silently truncated and needs a native adapter revision strategy; original calendar start/end offsets/timezone are retained inside facts.
- Duplicate replay does not refresh evidence age. This harness compares source timestamps; a provider without reliable monotonic revisions needs adapter-specific version/refetch rules. Never use fetch time as fabricated source update time.

This is not production concurrency/authentication evidence. Missing production work includes native payload adapters and webhook verification, token vault/refresh/revocation, access-scoped queries, durable jobs/retries/dead-letter handling, source mapping tables, conflict/audit history, freshness rules, pagination/token recovery, migrations, Postgres locking tests, retention/deletion/backups, and downstream read models. Existing production gates remain unresolved.

## Fictional datasets and local use

[connector_fixtures/connector_practice.json](../src/smolstuff/connector_fixtures/connector_practice.json) contains 46 normalized synthetic records:

- Keyboard: 21 records across Shopify-shaped commerce, Google Calendar-shaped events, an explicit Sheets template and local staffing/inquiry records.
- Bakery: 25 records across Square-shaped commerce/invoices, Google Calendar-shaped events, an explicit Sheets template with fractional ingredient stock, two expiry lots and a recipe, plus local staffing/inquiry records.
- Both include paid/completed and unknown-payment/unfulfilled orders, tentative holds, full-day calendar windows (native all-day markers are deferred), owner/employee shift references, availability shorter than a shift, and a POS-versus-sheet discrepancy.
- Incoming purchase orders are separate from actual receiving. Calendar holds are separate from accepted/paid orders. Lot quantities describe subsets of existing stock; do not sum them into POS stock.
- These are invented normalized adapter outputs, **not native API recordings**. Recipe/expiry/manual-count columns assume a defined Sheets template; providers do not generate these facts automatically. Local inquiry fields are practice inputs, not evidence of a mailbox connection.

Run from the repository:

```sh
PYTHONPATH=src .venv/bin/python -m smolstuff.connector_seeds
```

It uses an in-memory SQLite database, loads no environment keys and prints synthetic record counts. It does not seed production, create login accounts or expose records in /demo. The datasets are a tested reusable foundation for the later authenticated practice UI, not a claim that scheduling/expiry workflows are already implemented.

Next implementation slice: bind authenticated shop access, then connect these practice source observations to a shop-scoped read model with visible source/freshness/conflicts. After that, validate one native read-only provider adapter against a disposable account and confirm the shop's source ownership/mapping decisions. Do not implement all vendors at once.

## Owner-approved outbound workflow — 2026-10-06

The owner selected automatic reply/invoice preparation followed by explicit approval before sending, with an optional separately approved owner-email preview. This is a later outbound slice after authenticated shop isolation and verified adapters, not read-only connector behavior. [PRD acceptance criteria](../prd.md#approved-replies-and-invoices--owner-decision-2026-10-06) specify exact-version/recipient approval, preview separation, provider-triggered invoice communications, idempotency and uncertain-send recovery. No live sender is implemented or enabled.
