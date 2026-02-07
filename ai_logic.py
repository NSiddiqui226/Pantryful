import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Check if key is loaded in your terminal
if not API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file")
else:
    print(f"✅ API Key loaded: {API_KEY[:5]}...")

genai.configure(api_key=API_KEY)
# Using flash for faster chat response
model = genai.GenerativeModel("gemini-1.5-flash")
from data_engine import (
    get_live_details,
    find_cheapest_store,
    find_best_alternative,
    find_category_substitute
)
import datetime
import pandas as pd

# -----------------------------
# AI SETUP (SAFE ON IMPORT)
# -----------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# -----------------------------
# HELPER: REAL RECIPES FROM full_format_recipes.json
# -----------------------------
def get_real_recipes(pantry_usuals, low_items, dataset_path="full_format_recipes.json", max_recipes=3):
    """
    Uses the full_format_recipes.json dataset to find realistic recipes.
    Prioritizes items you have plenty of (Surplus) and AVOIDS Low-stock items.
    """
    try:
        with open(dataset_path, 'r') as f:
            all_recipes = json.load(f)
        
        pantry_flat = [item.lower().strip() for items in pantry_usuals.values() for item in items]
        low_flat = [item.lower().strip() for item in low_items]
        
        # Surplus = Items we have in the pantry that are NOT currently low stock
        surplus_items = [item for item in pantry_flat if item not in low_flat]

        valid_matches = []
        for recipe in all_recipes:
            ingredients_text = " ".join(recipe.get("ingredients", [])).lower()
            title_text = recipe.get("title", "").lower()

            # RULE 1: If the recipe requires a low-stock item, skip it.
            if any(low in ingredients_text for low in low_flat if len(low) > 2):
                continue

            # RULE 2: Does it use our surplus/aging items?
            matches = [item for item in surplus_items if item in ingredients_text or item in title_text]
            
            if matches:
                # Score based on how many surplus items it clears out
                score = len(matches)
                valid_matches.append({
                    "name": recipe.get("title", "Untitled Recipe"),
                    "ingredients": recipe.get("ingredients", []),
                    "instructions": "\n".join(recipe.get("directions", [])),
                    "score": score,
                    "clears_out": matches
                })

        valid_matches.sort(key=lambda x: x["score"], reverse=True)
        
        formatted = []
        for r in valid_matches[:max_recipes]:
            teaser = f" (Clears out: {', '.join(r['clears_out'][:2])})"
            formatted.append({
                "name": f"{r['name']}{teaser}",
                "ingredients": r["ingredients"],
                "instructions": r["instructions"]
            })
        return formatted
    except Exception as e:
        print(f"Error loading recipe JSON: {e}")
        return []

# -----------------------------
# CORE AI CURATION ENGINE
# -----------------------------
def generate_shopping_list(
    household_size,
    grocery_freq,
    stores,
    pantry_usuals,
    last_trip=None,
    low_items=None
):
    if low_items is None:
        low_items = []
        
    flat_items = []
    for category, items in pantry_usuals.items():
        for item in items:
            flat_items.append(f"{item} ({category})")

    store_context = {}
    for item in flat_items:
        store_context[item] = get_live_details(item.split(" (")[0], stores)

    prompt = f"""
You are a professional AI chef. The user is running LOW on certain items—do NOT suggest recipes that use them. 
Instead, suggest recipes using the OTHER items in the pantry to reduce food waste.

User Profile:
- Household size: {household_size}
- Last grocery trip: {last_trip}

Pantry Inventory (Available):
{json.dumps(pantry_usuals, indent=2)}

Low-stock items (DO NOT USE IN RECIPES - ADD TO SHOPPING LIST):
{json.dumps(low_items, indent=2)}

Instructions:
1. Generate 3 REAL, diverse recipes. 
2. Use ONLY items from the 'Pantry Inventory' that are NOT in the 'Low-stock' list.
3. If an item is in 'Produce' and the last trip was a while ago, prioritize using it.
4. Output valid JSON only:
{{
  "shopping_list": [{{ "item": "string", "recommended_quantity": "string", "reason": "string" }}],
  "recipes": [{{ "name": "string", "ingredients": ["string"], "instructions": "string" }}]
}}
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        parsed = json.loads(text[json_start:json_end])
        return parsed
    except Exception as e:
        fallback_recipes = get_real_recipes(pantry_usuals, low_items)
        fallback_list = [{"item": i, "recommended_quantity": "1 unit", "reason": "Low stock"} for i in low_items]
        return {"shopping_list": fallback_list, "recipes": fallback_recipes, "upsell_suggestions": [], "error": str(e)}

# -----------------------------
# AI STORE OPTIMIZATION LAYER
# -----------------------------
# -----------------------------
# AI STORE OPTIMIZATION LAYER
# -----------------------------
def ai_optimize_cart(shopping_list, stores):
    """
    Applies AI + data-engine reasoning to enrich the shopping list
    with store choice, savings explanation, and alternatives.
    """

    enriched = []

    for entry in shopping_list:
        item = entry["item"]

        # Get live store data (price + stock)
        store_details = get_live_details(item, stores)

        # Best store (your existing logic)
        cheapest = find_cheapest_store(item, stores)

        # Second-best store for comparison
        sorted_prices = sorted(
            [
                (store, data["price"])
                for store, data in store_details.items()
                if data.get("price") is not None
            ],
            key=lambda x: x[1]
        )
        if cheapest is None or cheapest.get("price") is None:
            continue

        second_best = sorted_prices[1] if len(sorted_prices) > 1 else None

        # AI-driven alternative (your logic)
        alternative = find_best_alternative(item, store_details)

        enriched.append({
            "item": item,
            "recommended_quantity": entry.get("recommended_quantity", "1 unit"),
            "best_store": cheapest["store"] if cheapest else None,
            "best_price": cheapest["price"] if cheapest else None,
            "second_store": second_best[0] if second_best else None,
            "second_price": second_best[1] if second_best else None,
            "savings": round(
                (second_best[1] - cheapest["price"])
                if cheapest and second_best else 0,
                2
            ),
            "alternative": alternative,
            "reason": entry.get("reason", "Predicted need or low stock")
        })

    return enriched
# -----------------------------
# PREDICT LOW-STOCK AI
# -----------------------------
def predict_low_stock(usual_items, household_size, grocery_freq, last_trip):
    today = datetime.date.today()
    days_since = (today - last_trip).days if last_trip else 0
    flat_items = [item for items in usual_items.values() for item in items]

    prompt = f"""
You are an AI that predicts pantry consumption.
Estimate low items for {household_size} people, {days_since} days since shopping.
Inventory: {usual_items}
Output JSON: {{"low_items": ["item1"]}}
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        parsed = json.loads(text[json_start:json_end])
        low_items = parsed.get("low_items", [])
    except Exception:
        low_items = random.sample(flat_items, min(len(flat_items), 2))

    raw_next = last_trip + datetime.timedelta(days=max(1, round(7 / grocery_freq))) if last_trip else None
    suggested_next_str = raw_next.strftime("%A, %b %d") if raw_next else None

    ai_results = generate_shopping_list(
        household_size,
        grocery_freq,
        [],
        usual_items,
        last_trip,
        low_items
    )

    optimized_cart = ai_optimize_cart(
        ai_results.get("shopping_list", []),
        ["Walmart", "Costco", "Target"]
    )

    return {
        "low_items": low_items,
        "suggested_next_trip": suggested_next_str,
        "shopping_list": optimized_cart,
        "recipes": ai_results.get("recipes", [])
    }

# ---------------------------------------------------------
# STREAMLIT UI - FULL RESTORE
# ---------------------------------------------------------
import streamlit as st

if __name__ == "__main__":
    st.set_page_config(page_title="PantryFull", page_icon="🧺", layout="centered")

    st.markdown("""
    <style>
    div.stButton > button { border-radius: 999px; padding: 0.6rem 1.4rem; border: 2px solid #E5E7EB; background-color: white; color: #111827; font-weight: 500; }
    div.stButton > button:hover { border-color: #6366F1; background-color: #EEF2FF; color: #4338CA; }
    .selected-pill > button { background-color: #4F46E5 !important; color: white !important; border-color: #4F46E5 !important; }
    </style>
    """, unsafe_allow_html=True)

    if "step" not in st.session_state: st.session_state.step = 0
    if "stores_selected" not in st.session_state: st.session_state.stores_selected = set()
    if "ai_results" not in st.session_state: st.session_state.ai_results = {"shopping_list": [], "recipes": []}
    if "usuals" not in st.session_state: st.session_state.usuals = {}
    if "category_index" not in st.session_state: st.session_state.category_index = 0
    if "last_trip_date" not in st.session_state: st.session_state.last_trip_date = None

    PANTRY_CATEGORIES = {
        "Dairy": ["Whole Milk", "Oat Milk", "Butter"],
        "Protein": ["Eggs", "Chicken Breast", "Ground Beef"],
        "Produce": ["Apples", "Bananas", "Spinach", "Tomatoes", "Onions"],
        "Pantry": ["Rice", "Pasta", "Olive Oil", "Cereal"]
    }
    CATEGORY_ORDER = list(PANTRY_CATEGORIES.keys())

    if st.session_state.step == 0:
        st.title("🧺 PantryFull")
        last_trip = st.date_input("When was your last grocery trip?", value=st.session_state.last_trip_date)
        if st.button("Next →"):
            st.session_state.last_trip_date = last_trip
            st.session_state.step = 1
            st.rerun()

    elif st.session_state.step == 1:
        st.title("🧺 Where do you shop?")
        stores = ["Walmart", "Costco", "Target"]
        for s in stores:
            if st.button(s, key=s, help="Select Store"):
                st.session_state.stores_selected.add(s)
        if st.button("Continue →"):
            st.session_state.step = 2
            st.rerun()

    elif st.session_state.step == 2:
        st.title("🧺 Household Details")
        h_size = st.slider("Household size", 1, 10, 2)
        freq = st.slider("Shopping frequency (times/week)", 1, 7, 2)
        if st.button("Next →"):
            st.session_state.h_size = h_size
            st.session_state.grocery_freq = freq
            st.session_state.step = 3
            st.rerun()

    elif st.session_state.step == 3:
        cat = CATEGORY_ORDER[st.session_state.category_index]
        st.title(f"🧺 {cat}")
        for item in PANTRY_CATEGORIES[cat]:
            if st.button(item, key=item):
                if cat not in st.session_state.usuals: st.session_state.usuals[cat] = []
                st.session_state.usuals[cat].append(item)
        if st.button("Finish →"):
            st.session_state.step = 4
            st.rerun()

    elif st.session_state.step == 4:
        st.title("🧺 Review")
        if st.button("Generate AI Insights →"):
            st.session_state.ai_results = predict_low_stock(
                st.session_state.usuals, 
                st.session_state.h_size, 
                st.session_state.grocery_freq, 
                st.session_state.last_trip_date
            )
            st.session_state.step = 5
            st.rerun()

    elif st.session_state.step == 5:
        st.title("⚡ Smart Dashboard")
        tabs = st.tabs(["📦 Insights", "🛒 Shopping List", "🍳 Recipes"])
        
        with tabs[0]:
            st.write(f"Low on: {', '.join(st.session_state.ai_results['low_items'])}")
            
        with tabs[1]:
            for item in st.session_state.ai_results['shopping_list']:
                st.checkbox(f"{item['item']} ({item['reason']})", value=True)

        with tabs[2]:
            for r in st.session_state.ai_results['recipes']:
                with st.expander(r['name']):
                    st.write(r['instructions'])