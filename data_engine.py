# data_engine.py

LIVE_STORE_DATA = {
    "Walmart": {
        "Oat Milk": {"stock": 0, "price": 4.50},
        "Eggs": {"stock": 10, "price": 3.99}
    },
    "Costco": {
        "Oat Milk": {"stock": 50, "price": 4.10},
        "Eggs": {"stock": 0, "price": 6.50}
    },
    "Target": {
        "Oat Milk": {"stock": 10, "price": 4.99},
        "Eggs": {"stock": 20, "price": 4.25}
    }
}

def get_live_details(item, store_list):
    return {
        store: LIVE_STORE_DATA.get(store, {}).get(item, {"stock": 0, "price": 0})
        for store in store_list
    }

def find_best_alternative(item, preferred_stores):
    for store, inventory in LIVE_STORE_DATA.items():
        if store not in preferred_stores and inventory.get(item, {}).get("stock", 0) > 0:
            return {"store": store, "price": inventory[item]["price"]}
    return None