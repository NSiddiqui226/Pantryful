import streamlit as st
import pandas as pd
import ai_logic
import time
import random
from data_engine import find_cheapest_store, find_best_alternative

st.set_page_config(page_title="PantryFull", page_icon="🧺", layout="centered")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 0

if "ai_results" not in st.session_state or st.session_state.ai_results is None:
    st.session_state.ai_results = {
        "shopping_list": [],
        "upsell_suggestions": [],
        "recipes": []
    }

if "usuals" not in st.session_state:
    st.session_state.usuals = {}

if "category_index" not in st.session_state:
    st.session_state.category_index = 0

if "loading_step" not in st.session_state:
    st.session_state.loading_step = 0

# -----------------------------
# CATEGORY DATA (MOCK, EXPANDABLE)
# -----------------------------
PANTRY_CATEGORIES = {
    "Dairy": ["Whole Milk", "Oat Milk", "Almond Milk", "Greek Yogurt", "Butter", "Cheddar Cheese"],
    "Protein": ["Eggs", "Chicken Breast", "Ground Beef", "Salmon", "Tofu"],
    "Produce": ["Apples", "Bananas", "Spinach", "Tomatoes", "Onions"],
    "Pantry": ["Rice", "Pasta", "Olive Oil", "Cereal", "Peanut Butter"],
    "Frozen": ["Frozen Vegetables", "Frozen Pizza", "Ice Cream"]
}

CATEGORY_ORDER = list(PANTRY_CATEGORIES.keys())
TOTAL_CATEGORIES = len(CATEGORY_ORDER)

# -----------------------------
# STEP 0 — STORES
# -----------------------------
if st.session_state.step == 0:
    st.title("🧺 PantryFull")
    st.caption("Your pantry, but proactive.")

    st.markdown("### Where do you usually shop?")
    stores = st.multiselect("Select all that apply", ["Walmart", "Costco", "Target"])

    if st.button("Continue →"):
        if stores:
            st.session_state.stores = stores
            st.session_state.step = 1
            st.rerun()
        else:
            st.warning("Please select at least one store.")

# -----------------------------
# STEP 1 — HOUSEHOLD + FREQUENCY
# -----------------------------
elif st.session_state.step == 1:
    st.title("🧺 PantryFull")
    st.caption("Just a few details to personalize things.")

    st.markdown("### How many people are in your household?")
    h_size = st.slider("Household size", 1, 20, 2)

    st.markdown("### How often do you grocery shop per week?")
    grocery_freq = st.slider("Times per week", 1, 7, 2)

    col1, col2 = st.columns(2)
    if col1.button("← Back"):
        st.session_state.step = 0
        st.rerun()
    if col2.button("Next →"):
        st.session_state.h_size = h_size
        st.session_state.grocery_freq = grocery_freq
        st.session_state.step = 2
        st.rerun()

# -----------------------------
# STEP 2 — USUALS
# -----------------------------
elif st.session_state.step == 2:
    category = CATEGORY_ORDER[st.session_state.category_index]
    items = PANTRY_CATEGORIES[category]

    st.title("🧺 PantryFull")
    progress = (st.session_state.category_index + 1) / TOTAL_CATEGORIES
    st.progress(progress)
    st.caption(f"Category {st.session_state.category_index + 1} of {TOTAL_CATEGORIES}")

    st.markdown(f"### {category}")
    st.caption("Select what you usually keep at home — or skip if it doesn’t apply.")

    default_selection = st.session_state.usuals.get(category, [])
    selections = st.multiselect(f"Your usual {category.lower()} items", items, default=default_selection)

    if selections:
        st.session_state.usuals[category] = selections

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    # BACK
    if col1.button("← Back") and st.session_state.category_index > 0:
        st.session_state.category_index -= 1
        st.rerun()

    # SKIP
    if col2.button("Skip →"):
        if st.session_state.category_index < TOTAL_CATEGORIES - 1:
            st.session_state.category_index += 1
        else:
            st.session_state.step = 3
        st.rerun()

    # NEXT
    if col3.button("Next →"):
        st.session_state.usuals[category] = selections
        if st.session_state.category_index < TOTAL_CATEGORIES - 1:
            st.session_state.category_index += 1
        else:
            st.session_state.step = 3
        st.rerun()

# -----------------------------
# STEP 3 — REVIEW CHOICES
# -----------------------------
elif st.session_state.step == 3:
    st.title("🧺 Review Your Pantry Setup")
    st.caption("Take a moment to review before we generate insights.")

    st.markdown("### 🏪 Stores")
    st.write(", ".join(st.session_state.stores))

    st.markdown("### 👨‍👩‍👧 Household")
    st.write(f"{st.session_state.h_size} people")

    st.markdown("### 🛒 Grocery Frequency")
    st.write(f"{st.session_state.grocery_freq} times per week")

    st.markdown("### 📦 Your Usual Items")
    has_items = False
    for category, items in st.session_state.usuals.items():
        if items:
            has_items = True
            st.markdown(f"**{category}**")
            for item in items:
                st.write(f"• {item}")

    if not has_items:
        st.caption("No usual items selected — we’ll still make smart predictions.")

    st.markdown("---")
    col1, col2 = st.columns(2)
    if col1.button("← Edit Choices"):
        st.session_state.step = 2
        st.rerun()
    if col2.button("Looks Good →"):
        st.session_state.step = 4
        st.rerun()

# -----------------------------
# STEP 4 — DASHBOARD / AI
# -----------------------------
elif st.session_state.step == 4:
    st.title("⚡ Smart Dashboard")

    # Household info
    col1, col2 = st.columns(2)
    col1.metric("Household Size", st.session_state.h_size)
    col2.metric("Stores", ', '.join(st.session_state.stores))

    st.markdown("---")

    # Safe AI results access
    ai_results = st.session_state.ai_results or {}
    shopping_list = ai_results.get("shopping_list", [])
    upsells = ai_results.get("upsell_suggestions", [])
    recipes = ai_results.get("recipes", [])

    # Enrich shopping list with live pricing info
    for item in shopping_list:
        item_name = item.get("item")
        cheapest = find_cheapest_store(item_name, st.session_state.stores)
        if cheapest:
            item["cheapest_store"] = cheapest["store"]
            item["price"] = cheapest["price"]
            item["brand"] = cheapest["brand"]
            item["discount_note"] = f"Available at {cheapest['store']} for ${cheapest['price']:.2f}"
        else:
            item["cheapest_store"] = None
            item["price"] = None
            item["brand"] = None
            item["discount_note"] = "Out of stock at your preferred stores"
            alternative = find_best_alternative(item_name, st.session_state.stores)
            if alternative:
                item["alternative_store"] = alternative["store"]
                item["alternative_price"] = alternative["price"]
                item["alternative_brand"] = alternative["brand"]
                item["discount_note"] += f"; Available at {alternative['store']} for ${alternative['price']:.2f}"

    # Tabs
    tabs = st.tabs(["📦 Your Pantry", "🛒 Shopping List", "💡 Upsells", "🍳 Recipes"])

    # Pantry Tab
    with tabs[0]:
        st.subheader("Your Pantry")
        st.caption("Update items you ran out of; they'll automatically be added to your shopping list.")
        for category, items in st.session_state.usuals.items():
            st.markdown(f"**{category}**")
            for i, item in enumerate(items):
                out_key = f"out_{category}_{i}"
                if st.checkbox(f"Ran out of {item}?", key=out_key):
                    if not any(x["item"] == item for x in shopping_list):
                        shopping_list.append({
                            "item": item,
                            "recommended_quantity": "1 unit",
                            "reason": "You marked this as out of stock",
                            "price": None,
                            "cheapest_store": None,
                            "discount_note": "You marked this as out of stock"
                        })

    # Shopping List Tab
    with tabs[1]:
        st.subheader("Your Shopping List")
        if not shopping_list:
            st.info("No items in your shopping list yet.")
        for item in shopping_list:
            st.markdown(f"**{item['item']}** — Qty: {item['recommended_quantity']}")
            st.caption(f"Reason: {item.get('reason', 'No reason provided')}")
            if item.get("price"):
                st.write(f"💰 {item['brand']} at {item['cheapest_store']}: ${item['price']:.2f}")
            if item.get("alternative_store"):
                st.write(f"🔄 Alternative: {item['alternative_brand']} at {item['alternative_store']} for ${item['alternative_price']:.2f}")
            if item.get("discount_note"):
                st.info(item["discount_note"])
            st.markdown("---")

    # Upsells Tab
    with tabs[2]:
        st.subheader("Smart Suggestions / Upsells")
        if not upsells:
            st.info("No upsell suggestions at this time.")
        for u in upsells:
            st.write(f"• {u['item']} — {u.get('why', '')}")

    # Recipes Tab
    with tabs[3]:
        st.subheader("Recipes You Can Make")
        if not recipes:
            st.info("No recipes generated yet.")
        for r in recipes:
            st.markdown(f"**{r['name']}**")
            st.write(r["instructions"])
            st.markdown("---")

    # Reset button
    if st.button("🔄 Start Over"):
        st.session_state.step = 0
        st.session_state.ai_results = {
            "shopping_list": [],
            "upsell_suggestions": [],
            "recipes": []
        }
        st.session_state.usuals = {}
        st.session_state.category_index = 0
        st.rerun()