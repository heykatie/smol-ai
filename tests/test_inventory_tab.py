"""Inventory tab shows multi-location catalog and session stock changes."""

from smolstuff.demo_ui import (
    _product_card,
    _product_diff_line,
    apply_ops,
    inventory_page,
    shell,
)
from smolstuff.fixtures import DEMO_CATALOG
from smolstuff.inbox import InboxApp


def test_shell_includes_inventory_nav():
    page = shell("Inventory", "<h1>Inventory</h1>")

    assert 'href="/?scenario=inventory"' in page
    assert 'aria-current="page"' in page
    assert "Inventory" in page


def test_inventory_catalog_mirrors_specialty_shop_shape(tmp_path):
    app = InboxApp(str(tmp_path / "inbox.sqlite3"))
    page = app.view("inventory")

    assert 'class="catalog-table"' in page
    assert page.count("<article") == 0
    categories = {item["category"] for item in DEMO_CATALOG}
    assert categories == {
        "Switches",
        "Keycaps",
        "Keyboards",
        "Desk mats",
        "Keyboard configs",
        "Tools",
    }
    by_category = {}
    for item in DEMO_CATALOG:
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
    assert by_category["Switches"] == 12
    assert by_category["Keycaps"] == 31
    assert by_category["Keyboards"] == 9
    assert by_category["Desk mats"] == 28
    assert by_category["Keyboard configs"] == 405
    assert by_category["Tools"] == 7
    assert len(DEMO_CATALOG) == 492
    assert "Quiet linear switch" in page
    assert "Gateron Milky Yellow Pro" in page
    assert "GMK MTNU Jukebox base" in page
    assert "$164.00" in page
    assert "Harbor 65 aluminum kit" in page
    assert "$209.00" in page
    assert "Blush Grid deskmat" in page
    assert "Akko CS Piano 70-pack" in page
    assert "IXPE switch film sheet" in page
    assert "10-switch sample strip" in page
    assert "Keyboard configs" in page
    assert "Build-night workshop kit" not in page
    assert str(len(DEMO_CATALOG)) in page
    assert all(item.get("attrs") for item in DEMO_CATALOG)


def test_inventory_product_column_shows_differentiators_not_sku(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    assert "DEMO-SKU-001 · Switches" not in page
    assert 'class="product-meta"' in page
    assert "Linear, Silent" in page
    assert "<dt>SKU</dt>" in page
    assert "<dt>Category</dt>" in page
    assert "List price" in page
    assert "Unit cost" in page
    assert "Details" in page
    assert "$2.49" in page
    assert "$1.82" in page
    quiet = next(item for item in DEMO_CATALOG if item["sku"] == "DEMO-SKU-001")
    assert "Linear" in _product_diff_line(
        {"name": quiet["name"], "category": quiet["category"], "attrs": quiet["attrs"]}
    )
    config = next(item for item in DEMO_CATALOG if item["category"] == "Keyboard configs")
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


def test_inventory_desktop_category_column_is_concise(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    assert 'data-sort="category"' in page
    assert "col-category" in page
    assert ">Configs</td>" in page
    assert ">Desk mats</td>" in page
    assert ">Mats</td>" not in page
    assert ">Switches</td>" in page
    # Sort key uses the shortened label (Configs), not the full catalog name.
    assert 'data-sort-category="configs"' in page
    assert 'data-sort-category="desk mats"' in page
    assert "Phone view: Product, Status, Available, Issue" in page


def test_inventory_issue_combines_workflow_and_problem(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    assert 'data-sort="issue"' in page
    assert ">Issue</button>" in page
    assert ">Work</button>" not in page
    assert "issue-cell" in page
    assert "Lead-time risk" in page
    assert 'href="/?scenario=reorder"' in page
    assert "Event shortfall" in page
    assert "Count mismatch" in page
    assert "Replenishment →" not in page
    assert page.count(">Idle<") == 0

    app = InboxApp(str(tmp_path / "inbox2.sqlite3"))
    app.apply("simulate_email")
    app.apply("approve")
    waiting = app.view("inventory")
    assert ">Waiting<" in waiting
    assert "Lead-time risk" in waiting


def test_inventory_columns_are_sortable_and_filter_targets_catalog_rows(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    for key in (
        "product",
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
    app.apply("simulate_email")
    app.apply("approve")
    waiting = app.view("inventory")
    assert ">Waiting<" in waiting
    assert ">Incoming<" in waiting


def test_inventory_table_reads_identity_then_availability_then_ops(tmp_path):
    page = InboxApp(str(tmp_path / "inbox.sqlite3")).view("inventory")

    order = (
        'data-sort="product"',
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
    app.apply("simulate_email")
    app.apply("approve")

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
            sku="DEMO-SKU-{0:03d}".format(index),
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
            href="/?scenario=inventory",
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
