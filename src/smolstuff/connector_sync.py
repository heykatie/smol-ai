"""Offline normalized connector snapshots. No network, secrets, or production ingestion.

Trusted callers select shop/connection; payloads cannot set either. This store is a
practice harness, not authenticated tenant storage or a production sync worker.
"""
import json
import re
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

# (required fields, optional fields). Adapter outputs contain minimized facts only.
SCHEMAS = {
    "product": ({"sku", "name", "unit"}, {"location_id", "active"}),
    "inventory": ({"product_id", "location_id", "quantity", "unit", "state"}, set()),
    "order": ({"line_items", "currency", "total_minor", "source_state",
               "payment_status", "fulfillment_status"}, {"location_id", "due_at"}),
    "payment": ({"order_id", "currency", "amount_minor", "status"}, set()),
    "invoice": ({"order_id", "currency", "total_minor", "balance_minor", "status"}, {"due_at"}),
    "calendar_event": ({"title", "start", "end", "time_zone", "status"}, {"order_ref"}),
    "lot": ({"product_id", "location_id", "quantity", "unit", "expires_on"}, {"batch_id"}),
    "recipe": ({"product_id", "yield_quantity", "yield_unit", "ingredients"}, set()),
    "shift": ({"employee_ref", "start", "end", "time_zone", "status"}, {"location_id"}),
    "availability": ({"employee_ref", "start", "end", "time_zone", "status"}, set()),
    "inquiry": ({"channel", "status", "requirements"}, {"order_ref"}),
    "purchase_order": ({"line_items", "currency", "total_minor", "status"}, {"due_at"}),
    "shipment": ({"order_id", "status"}, {"carrier", "tracking_ref", "due_at"}),
}
ENVELOPE = {"kind", "external_id", "source_updated_at", "observed_at", "origin", "deleted", "data"}
ENUMS = {
    "payment_status": {"unknown", "unpaid", "partial", "paid", "refunded"},
    "fulfillment_status": {"unknown", "unfulfilled", "partial", "fulfilled", "cancelled"},
}
STATES = {
    "inventory": {"sellable", "committed", "reserved", "damaged", "unknown"},
    "payment": {"unknown", "pending", "completed", "failed", "refunded"},
    "invoice": {"unknown", "draft", "open", "paid", "void"},
    "calendar_event": {"confirmed", "tentative", "cancelled"},
    "shift": {"draft", "published", "cancelled"},
    "availability": {"available", "unavailable"},
    "inquiry": {"new", "details_pending", "ready_for_review", "closed"},
    "purchase_order": {"draft", "submitted", "confirmed", "received", "cancelled"},
    "shipment": {"unknown", "label_created", "in_transit", "delivered", "exception"},
}

class SyncConflict(ValueError):
    """Same source revision has different facts: resolve rather than overwrite."""

def text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 1000:
        raise ValueError("Expected bounded non-empty text.")
    return value

def timestamp(value):
    text(value)
    try:
        normalized = value.replace("Z", "+00:00")
        fraction = re.search(r"\.(\d+)(?=[+-]\d{2}:\d{2}$)", normalized)
        if fraction:
            if len(fraction.group(1)) > 6:
                raise ValueError()
            normalized = normalized[:fraction.start(1)] + fraction.group(1).ljust(6, "0") + normalized[fraction.end(1):]
        result = datetime.fromisoformat(normalized)
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError()
        return result.astimezone(timezone.utc).isoformat(timespec="microseconds")
    except ValueError:
        raise ValueError("Expected a timestamp with timezone.") from None

def quantity(value, positive=False):
    # Decimal strings retain fractional quantities; no floats, booleans or NaN.
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Quantity must be a decimal string.")
    try:
        number = Decimal(value)
        if not number.is_finite() or abs(number) > Decimal("1000000000"):
            raise ValueError()
        if positive and number <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid quantity.") from None

def line_items(items, ingredients=False):
    if not isinstance(items, list) or not 1 <= len(items) <= 500:
        raise ValueError("Expected bounded non-empty items.")
    expected = {"product_id", "quantity", "unit"} if ingredients else {
        "product_id", "quantity", "unit", "unit_price_minor"}
    for item in items:
        if not isinstance(item, dict) or set(item) != expected:
            raise ValueError("Unexpected item fields.")
        text(item["product_id"])
        text(item["unit"])
        quantity(item["quantity"], positive=True)
        if not ingredients:
            minor(item["unit_price_minor"])

def minor(value):
    if type(value) is not int or not 0 <= value <= 1000000000000:
        raise ValueError("Money must be bounded integer minor units.")

def validate(record):
    if not isinstance(record, dict) or set(record) != ENVELOPE:
        raise ValueError("Unexpected record fields.")
    kind = record["kind"]
    if not isinstance(kind, str) or kind not in SCHEMAS:
        raise ValueError("Unsupported record kind.")
    text(record["external_id"])
    if record["origin"] != "simulated" or type(record["deleted"]) is not bool:
        raise ValueError("Only explicit synthetic practice records are accepted.")
    updated = timestamp(record["source_updated_at"])
    observed = timestamp(record["observed_at"])
    if observed < updated:
        raise ValueError("Observation precedes source revision.")
    data = record["data"]
    if not isinstance(data, dict):
        raise ValueError("Expected structured facts.")
    if record["deleted"]:
        if data:
            raise ValueError("Tombstones must not retain fact bodies.")
    else:
        required, optional = SCHEMAS[kind]
        if not required <= set(data) or not set(data) <= required | optional:
            raise ValueError("Missing or unexpected fact fields.")
        for key, value in data.items():
            if key in {"quantity", "yield_quantity"}:
                quantity(value, positive=(key == "yield_quantity"))
                if kind == "lot" and Decimal(value) < 0:
                    raise ValueError("Lot quantity cannot be negative.")
            elif key.endswith("_minor"):
                minor(value)
            elif key == "currency":
                if not isinstance(value, str) or not re.fullmatch("[A-Z]{3}", value):
                    raise ValueError("Expected explicit three-letter currency.")
            elif key in {"start", "end", "due_at"}:
                timestamp(value)
            elif key == "expires_on":
                from datetime import date
                if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    raise ValueError("Expected expiry date.")
                date.fromisoformat(value)
            elif key == "active":
                if type(value) is not bool:
                    raise ValueError("Expected boolean active flag.")
            elif key == "line_items":
                line_items(value)
            elif key == "ingredients":
                line_items(value, ingredients=True)
            elif key == "requirements":
                if not isinstance(value, list) or len(value) > 30:
                    raise ValueError("Expected bounded requirements.")
                for requirement in value:
                    text(requirement)
            elif key in ENUMS:
                if not isinstance(value, str) or value not in ENUMS[key]:
                    raise ValueError("Unsupported state.")
            elif key in {"status", "state"}:
                if not isinstance(value, str) or value not in STATES[kind]:
                    raise ValueError("Unsupported state.")
            else:
                text(value)
        if "start" in data and timestamp(data["end"]) <= timestamp(data["start"]):
            raise ValueError("End must follow start.")
        if "time_zone" in data:
            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
            try:
                ZoneInfo(data["time_zone"])
            except ZoneInfoNotFoundError:
                raise ValueError("Unknown timezone.") from None
    # Store a copy. Callers cannot mutate accepted facts after ingestion.
    return dict(record, source_updated_at=updated, observed_at=observed,
                data=json.loads(json.dumps(data, allow_nan=False)))

class SyncStore:
    """Dedicated SQLite practice snapshots. Methods require trusted caller context."""
    def __init__(self, path):
        self.path = Path(path)
        self.db = sqlite3.connect(str(self.path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS connector_connections (
                shop_id TEXT NOT NULL, connection_id TEXT NOT NULL,
                provider TEXT NOT NULL, kinds TEXT NOT NULL, active INTEGER NOT NULL,
                cursor TEXT, PRIMARY KEY(shop_id, connection_id));
            CREATE TABLE IF NOT EXISTS connector_snapshots (
                shop_id TEXT NOT NULL, connection_id TEXT NOT NULL, kind TEXT NOT NULL,
                external_id TEXT NOT NULL, source_updated_at TEXT NOT NULL,
                observed_at TEXT NOT NULL, origin TEXT NOT NULL,
                deleted INTEGER NOT NULL, data TEXT NOT NULL,
                PRIMARY KEY(shop_id, connection_id, kind, external_id),
                FOREIGN KEY(shop_id, connection_id)
                REFERENCES connector_connections(shop_id, connection_id));
        """)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    def register_connection(self, shop_id, connection_id, provider, kinds, *, practice):
        if practice is not True or shop_id not in {"practice-keyboard", "practice-bakery"}:
            raise ValueError("This store accepts the two synthetic practice shops only.")
        for value in (connection_id, provider):
            text(value)
        kinds = set(kinds)
        if not kinds or not kinds <= set(SCHEMAS):
            raise ValueError("Unsupported connection record kinds.")
        encoded = json.dumps(sorted(kinds))
        with self.db:
            existing = self.db.execute(
                "SELECT provider, kinds FROM connector_connections WHERE shop_id=? AND connection_id=?",
                (shop_id, connection_id)).fetchone()
            if existing and (existing["provider"] != provider or existing["kinds"] != encoded):
                raise ValueError("Connection identity/scopes cannot be silently replaced.")
            self.db.execute("INSERT OR IGNORE INTO connector_connections VALUES (?, ?, ?, ?, 1, NULL)",
                            (shop_id, connection_id, provider, encoded))

    def _connection(self, shop_id, connection_id):
        row = self.db.execute("SELECT * FROM connector_connections WHERE shop_id=? AND connection_id=?",
                              (shop_id, connection_id)).fetchone()
        if row is None:
            raise ValueError("Unknown shop connection.")
        return row

    def set_active(self, shop_id, connection_id, active):
        self._connection(shop_id, connection_id)
        if type(active) is not bool:
            raise ValueError("Expected explicit active flag.")
        with self.db:
            self.db.execute("UPDATE connector_connections SET active=? WHERE shop_id=? AND connection_id=?",
                            (int(active), shop_id, connection_id))

    def cursor(self, shop_id, connection_id):
        return self._connection(shop_id, connection_id)["cursor"]

    def apply_page(self, shop_id, connection_id, records, *, cursor, complete=True):
        text(cursor)
        if type(complete) is not bool or not isinstance(records, list) or len(records) > 1000:
            raise ValueError("Invalid page.")
        records = [validate(record) for record in records]
        outcomes = []
        try:
            self.db.execute("BEGIN IMMEDIATE")
            connection = self._connection(shop_id, connection_id)
            if not connection["active"]:
                raise ValueError("Connection is revoked.")
            for record in records:
                if record["kind"] not in json.loads(connection["kinds"]):
                    raise ValueError("Record kind is outside connection scope.")
                key = (shop_id, connection_id, record["kind"], record["external_id"])
                old = self.db.execute(
                    "SELECT * FROM connector_snapshots WHERE shop_id=? AND connection_id=? AND kind=? AND external_id=?",
                    key).fetchone()
                facts = json.dumps(record["data"], sort_keys=True, separators=(",", ":"), allow_nan=False)
                if old and record["source_updated_at"] < old["source_updated_at"]:
                    outcomes.append("stale")
                    continue
                if old and record["source_updated_at"] == old["source_updated_at"]:
                    if facts != old["data"] or int(record["deleted"]) != old["deleted"]:
                        raise SyncConflict("Conflicting facts for the same source revision.")
                    outcomes.append("duplicate")
                    continue
                self.db.execute(
                    """INSERT INTO connector_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(shop_id, connection_id, kind, external_id) DO UPDATE SET
                       source_updated_at=excluded.source_updated_at, observed_at=excluded.observed_at,
                       origin=excluded.origin, deleted=excluded.deleted, data=excluded.data""",
                    key + (record["source_updated_at"], record["observed_at"], record["origin"],
                           int(record["deleted"]), facts))
                outcomes.append("applied")
            if complete:
                self.db.execute("UPDATE connector_connections SET cursor=? WHERE shop_id=? AND connection_id=?",
                                (cursor, shop_id, connection_id))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return outcomes

    def records(self, shop_id, *, kind=None, include_deleted=False):
        query = """SELECT s.*, c.provider FROM connector_snapshots s
                   JOIN connector_connections c USING(shop_id, connection_id)
                   WHERE s.shop_id=?"""
        args = [shop_id]
        if kind is not None:
            if kind not in SCHEMAS:
                raise ValueError("Unsupported record kind.")
            query += " AND s.kind=?"
            args.append(kind)
        if not include_deleted:
            query += " AND s.deleted=0"
        query += " ORDER BY s.connection_id, s.kind, s.external_id"
        result = []
        for row in self.db.execute(query, args):
            item = dict(row)
            item["data"] = json.loads(item["data"])
            item["deleted"] = bool(item["deleted"])
            result.append(item)
        return result
