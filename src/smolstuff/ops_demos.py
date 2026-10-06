"""Synthetic operations scenarios that do not share the reorder product's stock.

Money and authorization stay in ordinary code. External actions are simulated.
"""

from __future__ import annotations

import json
import sqlite3
from decimal import Decimal, ROUND_CEILING
from typing import Optional


# Per-seat bill of materials. Costs still sum to $20 so contribution stays $700.
# Complete seats available = min(on_hand / per_seat) = 18 with seeded stock.
WORKSHOP_BOM = (
    {
        "sku": "DEMO-SKU-WS-PACK",
        "name": "Akko CS Piano 70-pack",
        "per_seat": 1,
        "store": 14,
        "warehouse": 4,
        "unit_cost": Decimal("14.00"),
        "bottleneck": True,
    },
    {
        "sku": "DEMO-SKU-WS-FILM",
        "name": "IXPE switch film sheet",
        "per_seat": 1,
        "store": 22,
        "warehouse": 18,
        "unit_cost": Decimal("2.50"),
        "bottleneck": False,
    },
    {
        "sku": "DEMO-SKU-WS-TOOL",
        "name": "Keycap + switch puller duo",
        "per_seat": 1,
        "store": 20,
        "warehouse": 15,
        "unit_cost": Decimal("3.50"),
        "bottleneck": False,
    },
)

WORKSHOP_FIXTURE = {
    "attendees": 20,
    "days_until": 7,
    "price": Decimal("1500"),
    "available_kits": min(
        (item["store"] + item["warehouse"]) // item["per_seat"] for item in WORKSHOP_BOM
    ),
    "kit_cost": sum((item["unit_cost"] for item in WORKSHOP_BOM), Decimal("0")),
    "moq": 10,
    "pack_size": 10,
    "delivery_days": 3,
    "labor": Decimal("300"),
    "other_costs": Decimal("100"),
    "calendar_available": True,
    "staffing_available": True,
}

DETECTIVE_FIXTURE = {
    "system_inventory": 20,
    "physical_count": 16,
    "attendance": 12,
    "recorded_usage": 9,
    "daily_demand": Decimal("1"),
}

RESCUE_FIXTURE = {
    "selling_price": Decimal("119"),
    "payment_fee": Decimal("4"),
    "other_variable": Decimal("5"),
    "minimum_contribution": Decimal("15"),
    "max_rounds": 3,
    "merchants": (
        {"id": "merchant-a", "name": "Merchant A simulator", "acquisition": Decimal("79"), "transfer": Decimal("10"), "floor": Decimal("79")},
        {"id": "merchant-b", "name": "Merchant B simulator", "acquisition": Decimal("76"), "transfer": Decimal("7"), "floor": Decimal("76")},
    ),
}

STAFFING_HISTORY = {
    "tuesday": (4, 5, 7, 4, 6),
    "saturday": (30, 34, 36, 38, 42),
}
MINUTES_PER_TRANSACTION = 15
MINUTES_PER_PICKUP = 15
BASELINE_HOURS = Decimal("1")
WORKSHOP_STAFF_HOURS = Decimal("4")
COVERAGE_BLOCK_HOURS = 4


def assess_workshop(attendees: int, days_until: int) -> dict:
    if attendees < 1 or days_until < 0:
        raise ValueError("Attendees must be positive and the event cannot be in the past.")
    fixture = WORKSHOP_FIXTURE
    required = attendees
    bom_lines = []
    seat_capacity = None
    for item in WORKSHOP_BOM:
        on_hand = item["store"] + item["warehouse"]
        seats = on_hand // item["per_seat"]
        if seat_capacity is None or seats < seat_capacity:
            seat_capacity = seats
        bom_lines.append(
            {
                "sku": item["sku"],
                "name": item["name"],
                "per_seat": item["per_seat"],
                "on_hand": on_hand,
                "store": item["store"],
                "warehouse": item["warehouse"],
                "unit_cost": _money(item["unit_cost"]),
                "required_units": required * item["per_seat"],
                "bottleneck": bool(item["bottleneck"]),
            }
        )
    available = int(seat_capacity if seat_capacity is not None else 0)
    shortage = max(0, required - available)
    if shortage == 0:
        purchase = 0
    else:
        packs = (shortage + fixture["pack_size"] - 1) // fixture["pack_size"]
        purchase = max(packs * fixture["pack_size"], fixture["moq"])
    # Procurement buys only the bottleneck BOM line (switch seat packs).
    bottleneck_cost = next(item["unit_cost"] for item in WORKSHOP_BOM if item["bottleneck"])
    procurement_cash = bottleneck_cost * purchase
    materials = fixture["kit_cost"] * required
    contribution = fixture["price"] - materials - fixture["labor"] - fixture["other_costs"]
    inventory_after = available + purchase - required
    for line in bom_lines:
        buy = purchase if line["bottleneck"] else 0
        line["purchase"] = buy
        line["after_units"] = line["on_hand"] + buy - line["required_units"]
    delivery_ok = shortage == 0 or days_until >= fixture["delivery_days"]
    if (
        not fixture["calendar_available"]
        or not fixture["staffing_available"]
        or not delivery_ok
        or contribution < 0
    ):
        verdict = "blocked"
    elif purchase > 0:
        verdict = "feasible_with_conditions"
    else:
        verdict = "feasible"
    return {
        "attendees": attendees,
        "days_until": days_until,
        "required": required,
        "shortage": shortage,
        "purchase": purchase,
        "procurement_cash": _money(procurement_cash),
        "materials_consumed": _money(materials),
        "contribution": _money(contribution),
        "inventory_after": inventory_after,
        "delivery_ok": delivery_ok,
        "verdict": verdict,
        "phase": "assessed",
        "consumed": False,
        "bom": bom_lines,
    }


def investigate_stock(physical_count: int) -> dict:
    if physical_count < 0:
        raise ValueError("A physical count cannot be negative.")
    fixture = DETECTIVE_FIXTURE
    system = fixture["system_inventory"]
    discrepancy = system - physical_count
    possible_unrecorded = fixture["attendance"] - fixture["recorded_usage"]
    return {
        "system_inventory": system,
        "physical_count": physical_count,
        "original_physical_count": physical_count,
        "attendance": fixture["attendance"],
        "recorded_usage": fixture["recorded_usage"],
        "discrepancy": discrepancy,
        "hypothesis_units": possible_unrecorded,
        "evidence_confirmed": False,
        "corrected": False,
        "unresolved": discrepancy,
        "closed": discrepancy == 0,
        "phase": "investigated",
        "history": ["Physical count recorded: {0}.".format(physical_count)],
    }


def confirm_workshop_evidence(case: dict) -> dict:
    if case.get("evidence_confirmed"):
        case = dict(case)
        case["replayed"] = True
        return case
    updated = dict(case)
    updated["evidence_confirmed"] = True
    updated["history"] = list(case.get("history", [])) + [
        "Simulated evidence confirms {0} practice switch strips were consumed. Attendance alone did not prove that.".format(
            DETECTIVE_FIXTURE["attendance"]
        )
    ]
    updated["replayed"] = False
    return updated


def apply_usage_correction(case: dict) -> dict:
    if not case.get("evidence_confirmed"):
        raise ValueError("Workshop consumption is not confirmed.")
    if case.get("discrepancy", 0) <= 0:
        raise ValueError("There is no missing stock to correct.")
    hypothesis = case.get("hypothesis_units", 0)
    if not (0 < hypothesis <= case["discrepancy"]):
        raise ValueError("The hypothesis does not fit the discrepancy.")
    if case.get("corrected"):
        case = dict(case)
        case["replayed"] = True
        return case
    updated = dict(case)
    updated["system_inventory"] = case["system_inventory"] - case["hypothesis_units"]
    updated["corrected"] = True
    updated["unresolved"] = updated["system_inventory"] - case["original_physical_count"]
    updated["closed"] = False
    updated["replayed"] = False
    updated["history"] = list(case.get("history", [])) + [
        "Approved correction removed {0} unrecorded workshop units. System inventory is now {1}. The count of {2} is unchanged.".format(
            case["hypothesis_units"], updated["system_inventory"], case["original_physical_count"]
        )
    ]
    return updated


def apply_recount(case: dict, recount: int) -> dict:
    if not case.get("corrected"):
        raise ValueError("Recount is available after the usage correction.")
    updated = dict(case)
    updated["history"] = list(case.get("history", [])) + [
        "Simulated recount: {0}. Earlier count {1} is preserved.".format(recount, case["original_physical_count"])
    ]
    updated["latest_recount"] = recount
    if recount == updated["system_inventory"]:
        updated["closed"] = True
        updated["unresolved"] = 0
        updated["history"].append("Recount matches system inventory. Discrepancy closed.")
    else:
        updated["closed"] = False
        updated["unresolved"] = updated["system_inventory"] - recount
        updated["history"].append("Recount still differs. The case stays open.")
    return updated


def detective_days_of_supply(system_inventory: int) -> Decimal:
    return Decimal(system_inventory) / DETECTIVE_FIXTURE["daily_demand"]


def merchant_contribution(selling_price: Decimal, acquisition: Decimal, transfer: Decimal) -> Decimal:
    fixture = RESCUE_FIXTURE
    return selling_price - acquisition - transfer - fixture["payment_fee"] - fixture["other_variable"]


def default_offers(selling_price: Decimal) -> list:
    offers = []
    for merchant in RESCUE_FIXTURE["merchants"]:
        contribution = merchant_contribution(selling_price, merchant["acquisition"], merchant["transfer"])
        offers.append({
            "id": merchant["id"],
            "name": merchant["name"],
            "acquisition": _money(merchant["acquisition"]),
            "transfer": _money(merchant["transfer"]),
            "floor": _money(merchant["floor"]),
            "contribution": _money(contribution),
            "acceptable": contribution >= RESCUE_FIXTURE["minimum_contribution"],
            "status": "quoted",
            "rounds": 0,
        })
    return offers


def negotiate(offer: dict, counter_price: Decimal, selling_price: Decimal) -> dict:
    updated = dict(offer)
    floor = Decimal(offer["floor"])
    transfer = Decimal(offer["transfer"])
    rounds = int(offer.get("rounds", 0)) + 1
    updated["rounds"] = rounds
    asked = Decimal(offer["acquisition"])
    if counter_price > asked:
        raise ValueError("A counteroffer cannot cost more than the current offer.")
    if counter_price < floor:
        raise ValueError("That counter is below the simulator floor. The current offer stays.")
    if rounds > RESCUE_FIXTURE["max_rounds"]:
        updated["status"] = "closed"
        updated["note"] = "Negotiation round limit reached. No binding transaction."
        return updated
    acquisition = counter_price
    updated["status"] = "accepted"
    updated["note"] = "Simulator can accept ${0}. This is not a binding purchase.".format(_money(counter_price))
    updated["acquisition"] = _money(acquisition)
    contribution = merchant_contribution(selling_price, acquisition, transfer)
    updated["contribution"] = _money(contribution)
    updated["acceptable"] = contribution >= RESCUE_FIXTURE["minimum_contribution"] and updated["status"] == "accepted"
    return updated


def workshop_approve(assessment: dict) -> dict:
    if assessment.get("verdict") == "blocked":
        raise ValueError("Approval cannot bypass a blocked feasibility check.")
    if assessment.get("phase") in ("approved", "materials_in", "completed"):
        updated = dict(assessment)
        updated["replayed"] = True
        return updated
    updated = dict(assessment)
    updated["phase"] = "approved"
    updated["replayed"] = False
    return updated


def workshop_receive(assessment: dict) -> dict:
    if assessment.get("purchase", 0) <= 0:
        raise ValueError("No procurement is required.")
    if assessment.get("phase") in ("materials_in", "completed"):
        updated = dict(assessment)
        updated["replayed"] = True
        return updated
    if assessment.get("phase") != "approved":
        raise ValueError("Receive materials after approval.")
    updated = dict(assessment)
    updated["phase"] = "materials_in"
    updated["replayed"] = False
    return updated


def workshop_complete(assessment: dict) -> dict:
    if assessment.get("consumed"):
        updated = dict(assessment)
        updated["replayed"] = True
        return updated
    purchase = assessment.get("purchase", 0)
    phase = assessment.get("phase")
    ready = (purchase == 0 and phase == "approved") or phase == "materials_in"
    if not ready:
        raise ValueError("Materials are not available yet.")
    updated = dict(assessment)
    updated["phase"] = "completed"
    updated["consumed"] = True
    updated["replayed"] = False
    return updated


def staffing_plan(day: str, workshop: bool, owner_hours: Decimal) -> dict:
    counts = STAFFING_HISTORY.get(day)
    if counts is None:
        raise ValueError("Choose Tuesday or Saturday.")
    if owner_hours < 0:
        raise ValueError("Owner capacity cannot be negative.")
    expected = Decimal(sum(counts)) / Decimal(len(counts))
    pickups = 1 if day == "tuesday" else 0
    transaction_hours = expected * Decimal(MINUTES_PER_TRANSACTION) / Decimal(60)
    pickup_hours = Decimal(pickups) * Decimal(MINUTES_PER_PICKUP) / Decimal(60)
    workshop_hours = WORKSHOP_STAFF_HOURS if workshop else Decimal("0")
    workload = transaction_hours + pickup_hours + BASELINE_HOURS + workshop_hours
    extra = workload - owner_hours
    if extra < 0:
        extra = Decimal("0")
    if extra == 0:
        blocks = 0
    else:
        blocks = int((extra / Decimal(COVERAGE_BLOCK_HOURS)).to_integral_value(rounding=ROUND_CEILING))
    return {
        "day": day,
        "workshop": workshop,
        "owner_hours": _money(owner_hours),
        "history": list(counts),
        "expected_transactions": _money(expected),
        "pickups": pickups,
        "workload_hours": _money(workload),
        "extra_hours": _money(extra),
        "coverage_blocks": blocks,
        "saved": False,
    }


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


class ScenarioStore:
    """Session-scoped preview state in SQLite or configured Postgres."""

    def __init__(self, path: str, session_id: str = "local", connection=None) -> None:
        self.path = path
        self.session_id = session_id or "local"
        if connection is None:
            from smolstuff.database import postgres_connection

            connection = postgres_connection()
        if connection is None:
            self._conn = sqlite3.connect(path)
            self._conn.row_factory = sqlite3.Row
            self._conn.isolation_level = None
            existing = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='scenario_state'"
            ).fetchone()
            if existing is None:
                self._conn.execute(
                    """
                    CREATE TABLE scenario_state (
                        session_id TEXT NOT NULL,
                        scenario TEXT NOT NULL,
                        phase TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        updated_at TEXT,
                        PRIMARY KEY (session_id, scenario)
                    )
                    """
                )
                self._scoped = True
            else:
                columns = {row[1] for row in self._conn.execute("PRAGMA table_info(scenario_state)")}
                self._scoped = "session_id" in columns
                if "updated_at" not in columns:
                    self._conn.execute("ALTER TABLE scenario_state ADD COLUMN updated_at TEXT")
            return
        self._conn = connection
        self._scoped = True
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scenario_state (
                session_id TEXT NOT NULL,
                scenario TEXT NOT NULL,
                phase TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT,
                PRIMARY KEY (session_id, scenario)
            )
            """
        )
        self._conn.execute(
            "ALTER TABLE scenario_state ADD COLUMN IF NOT EXISTS updated_at TEXT"
        )

    def close(self) -> None:
        self._conn.close()

    def get(self, scenario: str) -> Optional[dict]:
        if self._scoped:
            row = self._conn.execute(
                "SELECT phase, payload FROM scenario_state WHERE session_id = ? AND scenario = ?",
                (self.session_id, scenario),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT phase, payload FROM scenario_state WHERE scenario = ?", (scenario,)
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload"])
        payload["phase"] = row["phase"]
        return payload

    def save(self, scenario: str, payload: dict) -> None:
        from datetime import datetime, timezone

        phase = payload.get("phase", "saved")
        touched = datetime.now(timezone.utc).isoformat()
        if self._scoped:
            self._conn.execute(
                """
                INSERT INTO scenario_state (session_id, scenario, phase, payload, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id, scenario) DO UPDATE SET
                    phase = excluded.phase,
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (self.session_id, scenario, phase, json.dumps(payload), touched),
            )
        else:
            self._conn.execute(
                """
                INSERT INTO scenario_state (scenario, phase, payload, updated_at) VALUES (?, ?, ?, ?)
                ON CONFLICT(scenario) DO UPDATE SET
                    phase = excluded.phase,
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (scenario, phase, json.dumps(payload), touched),
            )

    def reset(self, scenario: str) -> None:
        if self._scoped:
            self._conn.execute(
                "DELETE FROM scenario_state WHERE session_id = ? AND scenario = ?",
                (self.session_id, scenario),
            )
        else:
            self._conn.execute("DELETE FROM scenario_state WHERE scenario = ?", (scenario,))
