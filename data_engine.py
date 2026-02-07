# data_engine.py

# Simulated Live Store Data
LIVE_STORE_DATA = {
    "Walmart": {
        "Oat Milk": {"stock": 0, "price": 4.50, "brand": "Oatly"},
        "Eggs": {"stock": 10, "price": 3.99, "brand": "Great Value"}
    },
    "Costco": {
        "Oat Milk": {"stock": 50, "price": 4.10, "brand": "Kirkland"},
        "Eggs": {"stock": 0, "price": 6.50, "brand": "Kirkland"}
    },
    "Target": {
        "Oat Milk": {"stock": 10, "price": 4.99, "brand": "Good & Gather"},
        "Eggs": {"stock": 20, "price": 4.25, "brand": "Good & Gather"}
    }
}

def get_live_details(item, store_list):
    """Fetches stock/price for the AI to analyze."""
    return {store: LIVE_STORE_DATA.get(store, {}).get(item, {"stock": 0, "price": 0}) for store in store_list}

def find_best_alternative(item, preferred_stores):
    """Finds a store NOT in the user's list that has stock."""
    for store, inventory in LIVE_STORE_DATA.items():
        if store not in preferred_stores and inventory.get(item, {}).get("stock", 0) > 0:
            return {"store": store, "price": inventory[item]["price"]}
    return None