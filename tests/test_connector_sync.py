import copy

import pytest
from smolstuff.connector_sync import SyncStore, SyncConflict
from smolstuff.connector_seeds import load_practice_seed, replay_seed

def record(**changes):
    value = dict(kind="inventory", external_id="stock-1",
                 source_updated_at="2026-10-06T12:00:00Z",
                 observed_at="2026-10-06T13:00:00Z", origin="simulated",
                 deleted=False, data=dict(product_id="p1", location_id="main",
                                          quantity="21", unit="each", state="sellable"))
    value.update(changes)
    return value

@pytest.fixture
def store(tmp_path):
    with SyncStore(tmp_path / "sync.sqlite") as value:
        value.register_connection("practice-keyboard", "pos", "shopify", {"inventory"}, practice=True)
        yield value

def test_duplicate_snapshots_never_add_stock_and_survive_restart(store):
    assert store.apply_page("practice-keyboard", "pos", [record()], cursor="page-1") == ["applied"]
    assert store.apply_page("practice-keyboard", "pos", [record()], cursor="page-2") == ["duplicate"]
    assert store.records("practice-keyboard")[0]["data"]["quantity"] == "21"
    with SyncStore(store.path) as reopened:
        assert reopened.cursor("practice-keyboard", "pos") == "page-2"
        assert len(reopened.records("practice-keyboard")) == 1

def test_out_of_order_conflict_and_tombstone(store):
    store.apply_page("practice-keyboard", "pos", [record()], cursor="1")
    assert store.apply_page("practice-keyboard", "pos", [
        record(source_updated_at="2026-10-05T12:00:00Z", data=dict(record()["data"], quantity="200"))
    ], cursor="2") == ["stale"]
    with pytest.raises(SyncConflict):
        store.apply_page("practice-keyboard", "pos", [
            record(data=dict(record()["data"], quantity="200"))
        ], cursor="bad")
    assert store.cursor("practice-keyboard", "pos") == "2"
    tombstone = record(source_updated_at="2026-10-06T14:00:00Z",
                       observed_at="2026-10-06T15:00:00Z", deleted=True, data={})
    store.apply_page("practice-keyboard", "pos", [tombstone], cursor="3")
    assert store.records("practice-keyboard") == []
    assert store.records("practice-keyboard", include_deleted=True)[0]["deleted"] is True
    assert store.apply_page("practice-keyboard", "pos", [record()], cursor="4") == ["stale"]
    assert store.records("practice-keyboard") == []

def test_pages_are_atomic_and_only_completed_scan_advances_cursor(store):
    store.apply_page("practice-keyboard", "pos", [record()], cursor="checkpoint")
    store.apply_page("practice-keyboard", "pos", [record(external_id="p2")],
                     cursor="intermediate", complete=False)
    assert store.cursor("practice-keyboard", "pos") == "checkpoint"
    with pytest.raises(ValueError):
        store.apply_page("practice-keyboard", "pos", [
            record(external_id="p3"), record(external_id="bad", data=dict(record()["data"], quantity="NaN"))
        ], cursor="bad")
    assert len(store.records("practice-keyboard")) == 2
    assert store.cursor("practice-keyboard", "pos") == "checkpoint"

def test_conflict_rolls_back_earlier_records_on_same_page(store):
    store.apply_page("practice-keyboard", "pos", [record()], cursor="before")
    with pytest.raises(SyncConflict):
        store.apply_page("practice-keyboard", "pos", [
            record(external_id="new"), record(data=dict(record()["data"], quantity="5"))
        ], cursor="after")
    assert len(store.records("practice-keyboard")) == 1
    assert store.cursor("practice-keyboard", "pos") == "before"

def test_shop_connection_and_provider_identity_are_separate(store):
    store.register_connection("practice-bakery", "pos", "square", {"inventory"}, practice=True)
    store.apply_page("practice-keyboard", "pos", [record()], cursor="k")
    store.apply_page("practice-bakery", "pos", [
        record(data=dict(record()["data"], quantity="3"))
    ], cursor="b")
    assert store.records("practice-bakery")[0]["data"]["quantity"] == "3"
    assert store.records("practice-keyboard")[0]["provider"] == "shopify"
    with pytest.raises(ValueError):
        store.register_connection("practice-keyboard", "pos", "square", {"inventory"}, practice=True)
    with pytest.raises(ValueError):
        store.apply_page("another-shop", "pos", [record()], cursor="x")
    with pytest.raises(ValueError):
        store.apply_page("practice-keyboard", "pos", [record(shop_id="practice-bakery")], cursor="x")

def test_revoked_disallowed_and_live_records_rejected(store):
    with pytest.raises(ValueError):
        store.register_connection("real-shop", "pos", "square", {"inventory"}, practice=False)
    with pytest.raises(ValueError):
        store.apply_page("practice-keyboard", "pos", [record(origin="live")], cursor="x")
    with pytest.raises(ValueError):
        store.apply_page("practice-keyboard", "pos", [record(kind="payment")], cursor="x")
    store.set_active("practice-keyboard", "pos", False)
    with pytest.raises(ValueError):
        store.apply_page("practice-keyboard", "pos", [record()], cursor="x")
    assert store.cursor("practice-keyboard", "pos") is None

@pytest.mark.parametrize("bad", [
    {"quantity": "Infinity"}, {"quantity": True}, {"quantity": 1.2},
    {"api_key": "not-a-secret"}, {"role": "owner"}, {"unit": ""},
])
def test_invalid_facts_or_authority_fields_do_not_enter_store(store, bad):
    with pytest.raises(ValueError):
        store.apply_page("practice-keyboard", "pos", [
            record(data=dict(record()["data"], **bad))
        ], cursor="x")
    assert store.records("practice-keyboard") == []

def test_timestamp_offsets_compare_as_instants_and_naive_time_is_rejected(store):
    store.apply_page("practice-keyboard", "pos", [record()], cursor="1")
    assert store.apply_page("practice-keyboard", "pos", [
        record(source_updated_at="2026-10-06T05:00:00-07:00")
    ], cursor="2") == ["duplicate"]
    with pytest.raises(ValueError):
        store.apply_page("practice-keyboard", "pos", [
            record(source_updated_at="2026-10-06T12:00:00")
        ], cursor="bad")

def test_both_seed_shops_replay_without_double_counting_or_cross_shop_merge(tmp_path):
    seed = load_practice_seed()
    assert {shop["shop_id"] for shop in seed["shops"]} == {"practice-keyboard", "practice-bakery"}
    with SyncStore(tmp_path / "seed.sqlite") as store:
        first = replay_seed(store, seed)
        before = {s["shop_id"]: store.records(s["shop_id"]) for s in seed["shops"]}
        second = replay_seed(store, seed)
        assert all(result == "applied" for result in first)
        assert all(result == "duplicate" for result in second)
        assert before == {s["shop_id"]: store.records(s["shop_id"]) for s in seed["shops"]}
        bakery = before["practice-bakery"]
        assert {"order", "invoice", "calendar_event", "inventory", "lot", "recipe",
                "shift", "availability", "inquiry", "payment"} <= {r["kind"] for r in bakery}
        orders = [r for r in bakery if r["kind"] == "order"]
        assert any(r["data"]["payment_status"] == "unknown" for r in orders)
        assert any(r["data"]["fulfillment_status"] == "unfulfilled" for r in orders)
        assert all(r["origin"] == "simulated" for records in before.values() for r in records)
        assert all("customer_email" not in r["data"] for records in before.values() for r in records)

def test_calendar_and_money_validation_do_not_infer_business_state(tmp_path):
    seed = load_practice_seed()
    page = next(p for p in seed["pages"] if p["records"][0]["kind"] == "calendar_event")
    with SyncStore(tmp_path / "seed.sqlite") as store:
        replay_seed(store, seed)
        event = store.records(page["shop_id"], kind="calendar_event")[0]
        assert "payment_status" not in event["data"]
        invalid = copy.deepcopy(page["records"][0])
        invalid["external_id"] = "bad"
        invalid["data"]["end"] = invalid["data"]["start"]
        with pytest.raises(ValueError):
            store.apply_page(page["shop_id"], page["connection_id"], [invalid], cursor="bad")

def test_seed_loader_returns_independent_values():
    first = load_practice_seed()
    first["shops"][0]["shop_id"] = "changed"
    assert load_practice_seed()["shops"][0]["shop_id"] == "practice-keyboard"

@pytest.mark.parametrize("field,value", [
    ("total_minor", 12.50), ("total_minor", True), ("total_minor", -1),
    ("currency", "usd"), ("payment_status", "definitely_paid"),
])
def test_invalid_order_money_and_state_never_persist(tmp_path, field, value):
    seed = load_practice_seed()
    page = next(p for p in seed["pages"] if p["connection_id"] == "pos")
    order = copy.deepcopy(next(r for r in page["records"] if r["kind"] == "order"))
    order["data"][field] = value
    with SyncStore(tmp_path / "money.sqlite") as store:
        store.register_connection(page["shop_id"], "pos", "shopify", {"order"}, practice=True)
        with pytest.raises(ValueError):
            store.apply_page(page["shop_id"], "pos", [order], cursor="bad")
        assert store.records(page["shop_id"]) == []
        assert store.cursor(page["shop_id"], "pos") is None

def test_later_fractional_timestamp_is_newer(store):
    store.apply_page("practice-keyboard", "pos", [record()], cursor="1")
    value = record(source_updated_at="2026-10-06T12:00:00.1Z",
                   data=dict(record()["data"], quantity="20"))
    assert store.apply_page("practice-keyboard", "pos", [value], cursor="2") == ["applied"]
    assert store.records("practice-keyboard")[0]["data"]["quantity"] == "20"

def test_registration_replay_does_not_restore_revoked_access(store):
    store.set_active("practice-keyboard", "pos", False)
    store.register_connection("practice-keyboard", "pos", "shopify", {"inventory"}, practice=True)
    with pytest.raises(ValueError):
        store.apply_page("practice-keyboard", "pos", [record()], cursor="x")

def test_source_snapshots_do_not_merge_across_connections_or_add_stock(store):
    store.register_connection("practice-keyboard", "sheet", "google_sheets", {"inventory"}, practice=True)
    store.apply_page("practice-keyboard", "pos", [record()], cursor="1")
    store.apply_page("practice-keyboard", "sheet", [
        record(data=dict(record()["data"], quantity="19"))
    ], cursor="2")
    values = store.records("practice-keyboard", kind="inventory")
    assert {(r["provider"], r["data"]["quantity"]) for r in values} == {
        ("shopify", "21"), ("google_sheets", "19")}
