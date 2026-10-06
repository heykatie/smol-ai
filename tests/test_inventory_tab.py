"""Inventory tab shows multi-location catalog and session stock changes."""

from reorder_path import advance_reorder
from smolstuff.demo_ui import (
    INVENTORY_MODE_OWNER,
    _product_card,
    _product_diff_line,
    apply_ops,
    empty_inventory_snapshot,
    inventory_page,
    product_home_page,
    shell,
)
from smolstuff.fixtures import DEMO_CATALOG, SANDBOX_CATALOG, SEEDED_CATALOG
from smolstuff.inbox import InboxApp


def test_shell_includes_inventory_nav():
    page = shell("Inventory", "<h1>Inventory</h1>")

    assert 'href="/try?scenario=inventory"' in page
    assert 'aria-current="page"' in page
    assert "Inventory" in page
    assert "Demo tour" in page


def test_product_home_distinguishes_demo_tour_from_practice_owner():
    page = product_home_page()

    assert "Start demo tour" in page
    assert "Demo tour" in page
    assert "Practice owner" in page
    assert "492" in page
    assert "Sign in is not available" in page
    assert 'href="/try"' in page


def test_seeded_catalog_mirrors_specialty_shop_shape():
    """Full specialty-shop assortment is reserved for practice-owner / logged-in."""
    assert SEEDED_CATALOG is DEMO_CATALOG
    categories = {item["category"] for item in SEEDED_CATALOG}
    assert categories == {
        "Switches",
        "Keycaps",
        "Keyboards",
        "Desk mats",
        "Keyboard configs",
        "Tools",
    }
    by_category = {}
    for item in SEEDED_CATALOG:
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
    assert by_category["Switches"] == 12
    assert by_category["Keycaps"] == 31
    assert by_category["Keyboards"] == 9
    assert by_category["Desk mats"] == 28
    assert by_category["Keyboard configs"] == 405
    assert by_category["Tools"] == 7
    assert len(SEEDED_CATALOG) == 492
    assert all(item.get("attrs") for item in SEEDED_CATALOG)


def test_sandbox_inventory_uses_small_demo_catalog(tmp_path):
    """Anonymous `/try` inventory is a tour subset, not the dense shop catalog."""
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    assert 'class="catalog-table"' in page
    assert page.count("<article") == 0
    assert len(SANDBOX_CATALOG) < 20
    assert str(len(SANDBOX_CATALOG)) in page
    assert "492" not in page
    assert "specialty-shop assortment (~492" not in page
    assert "Small demo catalog" in page or "Demo-tour catalog" in page
    assert "Quiet linear switch" in page
    assert "DEMO-ITM-001" in page
    assert "Akko CS Piano 70-pack" in page
    assert "IXPE switch film sheet" in page
    assert "10-switch sample strip" in page
    assert "Gateron Milky Yellow Pro" in page
    assert "Harbor 65 aluminum kit" in page
    assert "Blush Grid deskmat" in page
    assert "Keyboard configs" not in page
    assert "Build-night workshop kit" not in page
    # Dense fill rows stay on the seeded catalog only.
    assert "GMK MTNU Jukebox base" in page  # one sample keycap is in the tour
    assert page.count("data-search=") == len(SANDBOX_CATALOG)


def test_owner_inventory_snapshot_exposes_dense_seeded_catalog():
    """Practice-owner mode keeps the full seeded assortment ready for login."""
    snapshot = empty_inventory_snapshot(mode=INVENTORY_MODE_OWNER)
    page = inventory_page(snapshot)

    assert snapshot["mode"] == INVENTORY_MODE_OWNER
    assert len(snapshot["products"]) == 492
    assert "492" in page
    assert "specialty-shop assortment (~492" in page
    assert "Keyboard configs" in page
    assert "Quiet linear switch" in page


def test_inventory_product_column_shows_differentiators_not_sku(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    assert "DEMO-ITM-001 · Switches" not in page
    assert 'class="product-meta"' in page
    assert "Linear, Silent" in page
    assert "<dt>Item ID</dt>" in page
    assert "<dt>SKU</dt>" in page
    assert "<dt>Barcode</dt>" in page
    assert "<dt>Category</dt>" in page
    assert "List price" in page
    assert "Unit cost" in page
    assert "Details" in page
    assert "$2.49" in page
    assert "$1.82" in page
    quiet = next(item for item in SANDBOX_CATALOG if item["sku"] == "DEMO-ITM-001")
    assert quiet.get("barcode")
    assert quiet.get("merchant_sku")
    assert "Linear" in _product_diff_line(
        {"name": quiet["name"], "category": quiet["category"], "attrs": quiet["attrs"]}
    )
    config = next(item for item in SEEDED_CATALOG if item["category"] == "Keyboard configs")
    assert not config.get("barcode")
    assert not config.get("merchant_sku")
    assert (
        _product_diff_line(
            {
                "name": config["name"],
                "category": config["category"],
                "attrs": config["attrs"],
            }
        )
        == ""
    )
    # Optional identity on the seeded shop catalog.
    assert any(not item.get("barcode") for item in SEEDED_CATALOG)
    assert any(item.get("barcode") for item in SEEDED_CATALOG)
    assert any(not item.get("merchant_sku") for item in SEEDED_CATALOG)


def test_catalog_positions_are_realistic_and_consistent(tmp_path):
    from smolstuff.fixtures import (
        BOM_PACK_SKU,
        DETECTIVE_SKU,
        STORE_ON_HAND,
        WORKSHOP_SKU,
    )
    from smolstuff.ops_demos import DETECTIVE_FIXTURE, WORKSHOP_BOM

    by_sku = {item["sku"]: item for item in SEEDED_CATALOG}
    assert by_sku[WORKSHOP_SKU]["store"] == int(STORE_ON_HAND)
    for line in WORKSHOP_BOM:
        row = by_sku[line["sku"]]
        # Catalog store/warehouse are available; reserved is set aside for the workshop.
        physical_store = row["store"] + row.get("reserved_store", 0)
        physical_wh = row["warehouse"] + row.get("reserved_warehouse", 0)
        assert physical_store == line["store"]
        assert physical_wh == line["warehouse"]
        assert row.get("reserved_reason") == "Upcoming workshop (20 seats)"
        assert row.get("reserved_store", 0) + row.get("reserved_warehouse", 0) > 0
    assert by_sku[DETECTIVE_SKU]["store"] == DETECTIVE_FIXTURE["system_inventory"]
    pack = by_sku[BOM_PACK_SKU]
    assert pack["store"] + pack["warehouse"] == 0  # all 18 reserved for 20-seat workshop
    assert pack["reserved_store"] + pack["reserved_warehouse"] == 18

    for mode in (None, INVENTORY_MODE_OWNER):
        snapshot = (
            empty_inventory_snapshot()
            if mode is None
            else empty_inventory_snapshot(mode=mode)
        )
        for product in snapshot["products"]:
            totals = product["totals"]
            for key in (
                "available",
                "reserved",
                "inbound",
                "in_transfer",
                "damaged",
                "returns_pending",
                "display_demo",
            ):
                if key == "available":
                    location_sum = sum(
                        int(loc.get("available", loc.get("sellable", 0)))
                        for loc in product["locations"]
                    )
                else:
                    location_sum = sum(int(loc.get(key, 0)) for loc in product["locations"])
                assert totals.get(key, 0) == location_sum, (product["sku"], key)

    with_reserved = sum(
        1
        for item in SEEDED_CATALOG
        if item.get("reserved_store", 0) + item.get("reserved_warehouse", 0) > 0
    )
    with_inbound = sum(1 for item in SEEDED_CATALOG if item.get("inbound_warehouse", 0) > 0)
    with_transfer = sum(1 for item in SEEDED_CATALOG if item.get("in_transfer", 0) > 0)
    with_holds = sum(
        1
        for item in SEEDED_CATALOG
        if item.get("damaged", 0)
        + item.get("damaged_warehouse", 0)
        + item.get("returns_pending", 0)
        + item.get("display_demo", 0)
        > 0
    )
    with_store_damaged = sum(1 for item in SEEDED_CATALOG if item.get("damaged", 0) > 0)
    with_wh_damaged = sum(
        1 for item in SEEDED_CATALOG if item.get("damaged_warehouse", 0) > 0
    )
    assert 10 <= with_reserved <= 80
    assert 15 <= with_inbound <= 80
    assert 2 <= with_transfer <= 40
    assert 15 <= with_holds <= 120
    assert with_store_damaged >= 5
    assert with_wh_damaged >= 2
    assert any(
        item.get("inbound_warehouse", 0) > 0
        for item in SEEDED_CATALOG
        if item["category"] == "Switches"
    )
    # Details expands unavailable into Damaged / Returns / Display per location.
    page = InboxApp(str(tmp_path / "positions.sqlite3")).view("inventory")
    assert ">Damaged<" in page
    assert ">Returns<" in page
    assert ">Display<" in page
    # Fill SKUs are not a simple index staircase (1,2,3… repeating).
    keycap_stores = [
        item["store"]
        for item in SEEDED_CATALOG
        if item["sku"].startswith("DEMO-ITM-KC-") and item["sku"][-2:].isdigit()
    ]
    assert len(set(keycap_stores)) >= 4
    assert max(keycap_stores) >= 5


def test_inventory_desktop_category_column_is_concise(tmp_path):
    sandbox = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")
    assert 'data-sort="category"' in sandbox
    assert "col-category" in sandbox
    assert ">Desk mats</td>" in sandbox
    assert ">Mats</td>" not in sandbox
    assert ">Switches</td>" in sandbox
    assert 'data-sort-category="desk mats"' in sandbox
    assert "Phone view: Product, Status, Available, Issue" in sandbox

    # Short Configs label belongs to the dense seeded / practice-owner catalog.
    owner = inventory_page(empty_inventory_snapshot(mode=INVENTORY_MODE_OWNER))
    assert ">Configs</td>" in owner
    assert 'data-sort-category="configs"' in owner


def test_inventory_item_id_column_and_filter_include_identity(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    assert 'data-sort="itemid"' in page
    assert "col-itemid" in page
    assert ">DEMO-ITM-001</td>" in page
    assert "Item ID, SKU, barcode" in page
    quiet = next(item for item in SANDBOX_CATALOG if item["sku"] == "DEMO-ITM-001")
    assert quiet["barcode"]
    # Item ID (internal) ≠ merchant SKU when both are present.
    assert quiet["merchant_sku"]
    assert quiet["merchant_sku"] != quiet["sku"]
    assert quiet["merchant_sku"].startswith("MS-")
    assert all(
        (not item.get("merchant_sku")) or item["merchant_sku"] != item["sku"]
        for item in SEEDED_CATALOG
    )
    # Filter haystack + Available hover include Item ID / barcode / location split.
    idx = page.lower().index("quiet linear switch")
    chunk = page[idx : idx + 8000].lower()
    assert "demo-itm-001" in chunk
    assert quiet["barcode"].lower() in chunk
    assert quiet["merchant_sku"].lower() in chunk
    assert 'title="front store 21 · warehouse 0"' in chunk


def test_stock_condition_unavailable_only_when_nothing_promiseable():
    from smolstuff.demo_ui import _stock_condition

    assert _stock_condition(
        {"available": 8, "damaged": 2, "returns_pending": 0, "display_demo": 0, "inbound": 0}
    )[0] == "Available"
    assert _stock_condition(
        {"available": 0, "damaged": 2, "returns_pending": 1, "display_demo": 0, "inbound": 0}
    )[0] == "Unavailable"
    assert _stock_condition(
        {"available": 0, "damaged": 0, "returns_pending": 0, "display_demo": 0, "inbound": 50}
    )[0] == "Incoming"
    assert _stock_condition(
        {"available": 5, "damaged": 1, "returns_pending": 0, "display_demo": 0, "inbound": 20}
    )[0] == "Incoming"


def test_reserved_hover_shows_reason_and_blank_zero(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")
    reserved = [item for item in SANDBOX_CATALOG if item.get("reserved_store", 0) > 0]
    assert reserved
    assert all(item.get("reserved_reason") for item in reserved)
    assert "Reserved for:" in page
    assert reserved[0]["reserved_reason"] in page
    # Zero reserved renders as em dash, same as other sparse qty columns.
    assert 'title="No reserved units">' in page or "No reserved units" in page


def test_inventory_issue_combines_workflow_and_problem(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    assert 'data-sort="issue"' in page
    assert ">Issue</button>" in page
    assert ">Work</button>" not in page
    assert "issue-cell" in page
    assert "Lead-time risk" in page
    assert 'href="/try?scenario=reorder"' in page
    assert "Event shortfall" in page
    assert "Count mismatch" in page
    assert "Replenishment →" not in page
    assert page.count(">Idle<") == 0

    app = InboxApp(str(tmp_path / "inbox2.sqlite3"))
    advance_reorder(app, through="confirm")
    waiting = app.view("inventory")
    assert ">Waiting<" in waiting
    assert "Lead-time risk" in waiting


def test_inventory_columns_are_sortable_and_filter_targets_catalog_rows(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    for key in (
        "product",
        "itemid",
        "category",
        "status",
        "available",
        "reserved",
        "incoming",
        "transfer",
        "unavailable",
        "counted",
        "issue",
    ):
        assert 'data-sort="{0}"'.format(key) in page
        assert "data-sort-{0}=".format(key) in page
    assert 'data-type="number"' in page
    assert 'data-type="date"' in page
    # Status severity ranks (Out of stock=0 … Available=4), not label text.
    assert 'data-sort-status="4"' in page or 'data-sort-status="0"' in page
    # Issue follows sidebar demo order: Reorder=0, Workshop=1, Detective=2.
    assert 'data-sort-issue="0"' in page  # Lead-time risk
    assert 'data-sort-issue="1"' in page  # Event shortfall
    assert 'data-sort-issue="2"' in page  # Count mismatch
    assert "sort-btn" in page
    assert "table.tBodies[0]" in page
    assert 'querySelectorAll("tbody tr")' not in page
    assert "Date.parse" in page
    assert "data-search=" in page
    assert "inventory-filter" in page


def test_inventory_status_separate_from_issue(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    assert 'data-sort="status"' in page and ">Status</button>" in page
    assert 'data-sort="issue"' in page and ">Issue</button>" in page
    assert "Reorder demo baseline" in page
    assert "Browse row only" in page
    assert ">Available<" in page or ">Unavailable<" in page or ">Out of stock<" in page

    app = InboxApp(str(tmp_path / "inbox2.sqlite3"))
    advance_reorder(app, through="confirm")
    waiting = app.view("inventory")
    assert ">Waiting<" in waiting
    assert ">Incoming<" in waiting


def test_inventory_table_reads_identity_then_availability_then_ops(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    order = (
        'data-sort="product"',
        'data-sort="itemid"',
        'data-sort="category"',
        'data-sort="status"',
        'data-sort="available"',
        'data-sort="reserved"',
        'data-sort="incoming"',
        'data-sort="transfer"',
        'data-sort="unavailable"',
        'data-sort="counted"',
        'data-sort="issue"',
    )
    positions = [page.index(token) for token in order]
    assert positions == sorted(positions)
    for legacy in ("Work", "Action", "Workflow", "Stock"):
        assert 'data-sort="{0}"'.format(legacy.lower()) not in page
        assert ">{0}</button>".format(legacy) not in page
    assert "unavail-split" in page
    assert "Vendor return" not in page
    assert "Phone view: Product, Status, Available, Issue" in page


def test_inventory_inbound_then_store_receipt(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    advance_reorder(app, through="confirm")

    waiting = app.view("inventory")
    assert ">Waiting<" in waiting
    assert ">Incoming<" in waiting
    assert ">21<" in waiting or "still 21" in waiting or "stays 21" in waiting
    assert ">100<" in waiting or ">100</td>" in waiting
    assert ">121<" not in waiting

    app.apply("receive_full")
    done = app.view("inventory")

    assert ">121<" in done
    assert ">Done<" in done
    assert ">Available<" in done
    assert "Simulated receipt" in done
    assert "+100" in done


def test_inventory_reflects_workshop_bom_and_detective(tmp_path):
    path = str(tmp_path / "inbox.sqlite3")
    apply_ops(
        path,
        "workshop_check",
        {"scenario": ["workshop"], "attendees": ["20"], "days_until": ["7"]},
        "local",
    )
    apply_ops(path, "workshop_approve", {"scenario": ["workshop"]}, "local")
    apply_ops(path, "workshop_receive", {"scenario": ["workshop"]}, "local")
    apply_ops(path, "workshop_complete", {"scenario": ["workshop"]}, "local")
    apply_ops(
        path,
        "detective_check",
        {"scenario": ["detective"], "physical_count": ["16"]},
        "local",
    )
    apply_ops(path, "detective_confirm", {"scenario": ["detective"]}, "local")
    apply_ops(path, "detective_correct", {"scenario": ["detective"]}, "local")

    page = InboxApp(path).view("inventory")

    assert ">Done<" in page
    assert "Workshop consumption written back" in page or "remain after the event" in page
    assert ">8<" in page or "remain after the event" in page
    assert "17" in page
    assert "sample strip" in page.lower() or "not the quiet linear" in page.lower()


def test_inventory_layout_stays_one_table_with_many_skus():
    products = [
        _product_card(
            name="Item {0:03d}".format(index),
            sku="DEMO-ITM-{0:03d}".format(index),
            unit="units",
            icon="·",
            locations=[
                {
                    "name": "Front store",
                    "sellable": index % 7,
                    "available": index % 7,
                    "reserved": 0,
                    "inbound": 0,
                    "damaged": 0,
                    "returns_pending": 0,
                    "in_transfer": 0,
                    "display_demo": 0,
                },
                {
                    "name": "Warehouse",
                    "sellable": index % 3,
                    "available": index % 3,
                    "reserved": 0,
                    "inbound": 0,
                    "damaged": 0,
                    "returns_pending": 0,
                    "in_transfer": 0,
                    "display_demo": 0,
                },
            ],
            status_label="Seeded",
            status_class="idle",
            note="Synthetic bulk row.",
            href="/try?scenario=inventory",
            link_label="Open →",
            category="Switches",
            list_price="0.40",
            cost="0.20",
            description="Bulk test row.",
            role="browse",
            last_counted="2026-09-01",
            attrs={
                "Switch type": "Linear",
                "Sold as": "each",
                "Shelf status": "In stock",
            },
        )
        for index in range(100)
    ]
    page = inventory_page({"products": products, "movements": []})

    assert page.count('class="catalog-table"') == 1
    assert page.count('data-search="') == 100
    assert page.count("<article") == 0
    assert "product-meta" in page
    assert "Linear" in page
    assert 'data-sort-category="switches"' in page
