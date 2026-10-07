"""Fictional connector-shaped normalized seeds; not vendor API recordings."""
import json
from pathlib import Path

def load_practice_seed():
    return json.loads((Path(__file__).with_name("connector_fixtures") / "connector_practice.json").read_text())

def replay_seed(store, seed=None):
    seed = load_practice_seed() if seed is None else seed
    for connection in seed["connections"]:
        store.register_connection(connection["shop_id"], connection["connection_id"],
                                  connection["provider"], connection["kinds"], practice=True)
    result = []
    for page in seed["pages"]:
        result.extend(store.apply_page(page["shop_id"], page["connection_id"],
                                        page["records"], cursor=page["cursor"]))
    return result

if __name__ == "__main__":
    # A disposable in-memory SQLite store; never loads .env or touches hosted DBs.
    from smolstuff.connector_sync import SyncStore
    with SyncStore(":memory:") as store:
        outcomes = replay_seed(store)
        print(json.dumps({"origin": "simulated", "applied": outcomes.count("applied"),
                          "shops": {s["shop_id"]: len(store.records(s["shop_id"]))
                                    for s in load_practice_seed()["shops"]}}, indent=2))
