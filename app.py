import streamlit as st
import pandas as pd
import time
import random

from data_engine import find_cheapest_store, find_best_alternative

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="PantryFull",
    page_icon="🧺",
    layout="centered"
)

# -----------------------------
# GLOBAL CSS (PILL BUTTONS)
# -----------------------------
st.markdown("""
<style>
div.stButton > button {
    border-radius: 999px;
    padding: 0.6rem 1.4rem;
    border: 2px solid #E5E7EB;
    background-color: white;
    color: #111827;
    font-weight: 500;
    transition: all 0.2s ease;
}

div.stButton > button:hover {
    border-color: #6366F1;
    background-color: #EEF2FF;
    color: #4338CA;
}

div.stButton > button:focus {
    box-shadow: none;
}

.selected-pill > button {
    background-color: #4F46E5 !important;
    color: white !important;
    border-color: #4F46E5 !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 0

if "stores_selected" not in st.session_state:
    st.session_state.stores_selected = set()

if "ai_results" not in st.session_state:
    st.session_state.ai_results = {
        "shopping_list": [],
        "upsell_suggestions": [],
        "recipes": []
    }

if "usuals" not in st.session_state:
    st.session_state.usuals = {}

if "category_index" not in st.session_state:
    st.session_state.category_index = 0

# -----------------------------
# CATEGORY DATA
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
# STEP 0 — STORES (BUTTONS)
# -----------------------------
if st.session_state.step == 0:
    st.title("🧺 PantryFull")
    st.caption("Your pantry, but proactive.")

    st.markdown("### Where do you usually shop?")

    stores = [
        (" Walmart", "Walmart"),
        (" Costco", "Costco"),
        (" Target", "Target")
    ]

    cols = st.columns(len(stores))

    for i, (label, store) in enumerate(stores):
        is_selected = store in st.session_state.stores_selected
        container_class = "selected-pill" if is_selected else ""

        with cols[i]:
            st.markdown(f"<div class='{container_class}'>", unsafe_allow_html=True)
            if st.button(label, key=f"store_{store}"):
                if is_selected:
                    st.session_state.stores_selected.remove(store)
                else:
                    st.session_state.stores_selected.add(store)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.stores_selected:
        st.caption(
            "Selected: " + ", ".join(st.session_state.stores_selected)
        )

    st.markdown("---")

    if st.button("Continue →"):
        if st.session_state.stores_selected:
            st.session_state.stores = list(st.session_state.stores_selected)
            st.session_state.step = 1
            st.rerun()
        else:
            st.warning("Please select at least one store.")

# -----------------------------
# STEP 1 — HOUSEHOLD
# -----------------------------
elif st.session_state.step == 1:
    st.title("🧺 PantryFull")
    st.caption("Just a few details to personalize things.")

    h_size = st.slider("Household size", 1, 20, 2)
    grocery_freq = st.slider("Times you shop per week", 1, 7, 2)

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
# STEP 2 — USUAL ITEMS (PILL BUTTONS)
# -----------------------------
elif st.session_state.step == 2:
    category = CATEGORY_ORDER[st.session_state.category_index]
    items = PANTRY_CATEGORIES[category]

    st.title("🧺 PantryFull")
    st.progress((st.session_state.category_index + 1) / TOTAL_CATEGORIES)
    st.caption(f"Category {st.session_state.category_index + 1} of {TOTAL_CATEGORIES}")

    st.markdown(f"### {category}")
    st.caption("Select what you usually keep at home — or skip if it doesn’t apply.")

    # Ensure category exists in session state
    if category not in st.session_state.usuals:
        st.session_state.usuals[category] = []

    selected_items = set(st.session_state.usuals[category])

    # Display items as pill buttons
    cols = st.columns(3)
    for i, item in enumerate(items):
        col = cols[i % 3]
        is_selected = item in selected_items
        container_class = "selected-pill" if is_selected else ""

        with col:
            st.markdown(f"<div class='{container_class}'>", unsafe_allow_html=True)
            if st.button(item, key=f"{category}_{item}"):
                if is_selected:
                    selected_items.remove(item)
                else:
                    selected_items.add(item)
                st.session_state.usuals[category] = list(selected_items)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    if col1.button("← Back") and st.session_state.category_index > 0:
        st.session_state.category_index -= 1
        st.rerun()

    if col2.button("Skip →"):
        st.session_state.category_index += 1
        if st.session_state.category_index >= TOTAL_CATEGORIES:
            st.session_state.step = 3
        st.rerun()

    if col3.button("Next →"):
        st.session_state.category_index += 1
        if st.session_state.category_index >= TOTAL_CATEGORIES:
            st.session_state.step = 3
        st.rerun()

# -----------------------------
# STEP 3 — REVIEW
# -----------------------------
elif st.session_state.step == 3:
    st.title("🧺 Review Your Pantry Setup")

    st.markdown("### 🏪 Stores")
    st.write(", ".join(st.session_state.stores))

    st.markdown("### 👨‍👩‍👧 Household")
    st.write(f"{st.session_state.h_size} people")

    st.markdown("### 📦 Your Usual Items")
    for cat, items in st.session_state.usuals.items():
        if items:
            st.markdown(f"**{cat}**")
            for i in items:
                st.write(f"• {i}")

    col1, col2 = st.columns(2)
    if col1.button("← Edit"):
        st.session_state.step = 2
        st.rerun()

    if col2.button("Looks Good →"):
        st.session_state.step = 4
        st.rerun()

# -----------------------------
# STEP 4 — DASHBOARD
# -----------------------------
elif st.session_state.step == 4:
    st.title("⚡ Smart Dashboard")

    col1, col2 = st.columns(2)
    col1.metric("Household Size", st.session_state.h_size)
    col2.metric("Stores", ", ".join(st.session_state.stores))

    st.info("Your AI-powered insights will appear here.")
