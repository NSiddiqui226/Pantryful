# data_engine.py
# Mock "live" store inventory + pricing engine (expanded)

LIVE_STORE_DATA = {
    "Walmart": {
        # DAIRY
        "Whole Milk": {"brand": "Great Value", "category": "Dairy", "stock": 15, "price": 3.48},
        "Oat Milk": {"brand": "Great Value", "category": "Dairy Alternatives", "stock": 0, "price": 4.50},
        "Cheddar Cheese": {"brand": "Great Value", "category": "Dairy", "stock": 20, "price": 2.97},
        "Greek Yogurt": {"brand": "Chobani", "category": "Dairy", "stock": 12, "price": 1.25},

        # PROTEIN
        "Eggs": {"brand": "Eggland's Best", "category": "Protein", "stock": 10, "price": 3.99},
        "Chicken Breast": {"brand": "Tyson", "category": "Protein", "stock": 25, "price": 4.99},
        "Ground Beef": {"brand": "Great Value", "category": "Protein", "stock": 18, "price": 5.49},

        # PRODUCE
        "Apples": {"brand": "Fuji", "category": "Produce", "stock": 50, "price": 0.89},
        "Bananas": {"brand": "Organic", "category": "Produce", "stock": 100, "price": 0.59},
        "Spinach": {"brand": "Marketside", "category": "Produce", "stock": 22, "price": 2.49},

        # PANTRY
        "Rice": {"brand": "Mahatma", "category": "Pantry", "stock": 40, "price": 3.99},
        "Pasta": {"brand": "Barilla", "category": "Pantry", "stock": 35, "price": 1.89},
        "Olive Oil": {"brand": "Bertolli", "category": "Pantry", "stock": 14, "price": 6.99},

        # BAKERY
        "Bread": {"brand": "Sara Lee", "category": "Bakery", "stock": 25, "price": 2.99},

        # FROZEN
        "Frozen Pizza": {"brand": "DiGiorno", "category": "Frozen", "stock": 12, "price": 6.49},

        # BEVERAGES
        "Orange Juice": {"brand": "Tropicana", "category": "Beverages", "stock": 18, "price": 4.29}
    },

    "Costco": {
        "Whole Milk": {"brand": "Kirkland", "category": "Dairy", "stock": 30, "price": 2.99},
        "Oat Milk": {"brand": "Kirkland", "category": "Dairy Alternatives", "stock": 50, "price": 4.10},
        "Eggs": {"brand": "Kirkland", "category": "Protein", "stock": 0, "price": 6.50},
        "Chicken Breast": {"brand": "Kirkland", "category": "Protein", "stock": 40, "price": 3.99},
        "Rice": {"brand": "Kirkland", "category": "Pantry", "stock": 60, "price": 12.99},
        "Bread": {"brand": "Kirkland", "category": "Bakery", "stock": 40, "price": 3.50},
        "Frozen Vegetables": {"brand": "Kirkland", "category": "Frozen", "stock": 30, "price": 9.99}
    },

    "Target": {
        "Whole Milk": {"brand": "Good & Gather", "category": "Dairy", "stock": 8, "price": 3.79},
        "Oat Milk": {"brand": "Good & Gather", "category": "Dairy Alternatives", "stock": 10, "price": 4.99},
        "Eggs": {"brand": "Good & Gather", "category": "Protein", "stock": 20, "price": 4.25},
        "Apples": {"brand": "Honeycrisp", "category": "Produce", "stock": 25, "price": 1.29},
        "Bread": {"brand": "Dave's Killer Bread", "category": "Bakery", "stock": 0, "price": 5.99},
        "Almond Butter": {"brand": "Good & Gather", "category": "Pantry", "stock": 10, "price": 7.49}
    }
}

# -----------------------------
# Store-level lookup
# -----------------------------
def get_live_details(item, store_list):
    return {
        store: LIVE_STORE_DATA.get(store, {}).get(item, {
            "brand": None,
            "category": None,
            "stock": 0,
            "price": None
        })
        for store in store_list
    }

# -----------------------------
# Cheapest available option
# -----------------------------
def find_cheapest_store(item, store_list):
    cheapest = None
    for store in store_list:
        data = LIVE_STORE_DATA.get(store, {}).get(item)
        if data and data["stock"] > 0:
            if not cheapest or data["price"] < cheapest["price"]:
                cheapest = {"store": store, **data}
    return cheapest

# -----------------------------
# Alternative store
# -----------------------------
def find_best_alternative(item, preferred_stores):
    for store, inventory in LIVE_STORE_DATA.items():
        if store not in preferred_stores:
            data = inventory.get(item)
            if data and data["stock"] > 0:
                return {"store": store, **data}
    return None

# -----------------------------
# Category substitute
# -----------------------------
def find_category_substitute(item, preferred_stores):
    category = None

    for store in preferred_stores:
        data = LIVE_STORE_DATA.get(store, {}).get(item)
        if data:
            category = data["category"]
            break

    if not category:
        return None

    for store in preferred_stores:
        for alt_item, data in LIVE_STORE_DATA.get(store, {}).items():
            if data["category"] == category and data["stock"] > 0:
                return {"item": alt_item, "store": store, **data}

    return None