import streamlit as st
import pandas as pd
import ai_logic

st.set_page_config(page_title="PantryFull", page_icon="🧺", layout="centered")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 0

if "ai_results" not in st.session_state:
    st.session_state.ai_results = None

if "ai_triggered" not in st.session_state:
    st.session_state.ai_triggered = False

if "usuals" not in st.session_state:
    st.session_state.usuals = {}

if "category_index" not in st.session_state:
    st.session_state.category_index = 0

# -----------------------------
# CATEGORY DATA (MOCK, EXPANDABLE)
# -----------------------------
PANTRY_CATEGORIES = {
    "Dairy": [
        "Whole Milk",
        "Oat Milk",
        "Almond Milk",
        "Greek Yogurt",
        "Butter",
        "Cheddar Cheese"
    ],
    "Protein": [
        "Eggs",
        "Chicken Breast",
        "Ground Beef",
        "Salmon",
        "Tofu"
    ],
    "Produce": [
        "Apples",
        "Bananas",
        "Spinach",
        "Tomatoes",
        "Onions"
    ],
    "Pantry": [
        "Rice",
        "Pasta",
        "Olive Oil",
        "Cereal",
        "Peanut Butter"
    ],
    "Frozen": [
        "Frozen Vegetables",
        "Frozen Pizza",
        "Ice Cream"
    ]
}

CATEGORY_ORDER = list(PANTRY_CATEGORIES.keys())

# -----------------------------
# STEP 0 — STORES
# -----------------------------
if st.session_state.step == 0:
    st.title("🧺 PantryFull")
    st.caption("Your pantry, but proactive.")

    st.markdown("### Where do you usually shop?")
    stores = st.multiselect(
        "Select all that apply",
        ["Walmart", "Costco", "Target"]
    )

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
# STEP 2 — USUALS (CATEGORY BY CATEGORY)
# -----------------------------
elif st.session_state.step == 2:
    category = CATEGORY_ORDER[st.session_state.category_index]
    items = PANTRY_CATEGORIES[category]

    st.title("🧺 PantryFull")
    st.caption("Select what you usually keep at home.")

    st.markdown(f"### {category}")
    st.caption("Select all that apply")

    selections = st.multiselect(
        f"Your usual {category.lower()} items",
        items,
        default=st.session_state.usuals.get(category, [])
    )

    st.session_state.usuals[category] = selections

    st.markdown("---")
    col1, col2 = st.columns(2)

    if col1.button("← Back") and st.session_state.category_index > 0:
        st.session_state.category_index -= 1
        st.rerun()

    if col2.button("Next →"):
        if st.session_state.category_index < len(CATEGORY_ORDER) - 1:
            st.session_state.category_index += 1
            st.rerun()
        else:
            st.session_state.step = 3
            st.rerun()

# -----------------------------
# STEP 3 — DASHBOARD / AI ON DEMAND
# -----------------------------
elif st.session_state.step == 3:
    st.title("⚡ Smart Dashboard")

    col1, col2 = st.columns(2)
    col1.metric("Household Size", st.session_state.h_size)
    col2.metric("Shopping Frequency", f"{st.session_state.grocery_freq}x / week")

    st.markdown("---")

    st.subheader("🛒 Your Next Shopping List")
    st.caption("Generated only when you ask.")

    if not st.session_state.ai_triggered:
        if st.button("🤖 Generate Shopping List"):
            st.session_state.ai_results = ai_logic.generate_shopping_list(
                st.session_state.h_size,
                st.session_state.stores,
                st.session_state.usuals,
                st.session_state.grocery_freq
            )
            st.session_state.ai_triggered = True
            st.rerun()

    elif st.session_state.ai_results:
        for item in st.session_state.ai_results["shopping_list"]:
            st.write(f"• {item['name']} — Qty: {item['quantity']}")

        st.markdown("---")
        st.subheader("🍳 Recipe Suggestions")

        for r in st.session_state.ai_results["recipes"]:
            st.markdown(f"**{r['name']}**")
            st.write(r["instructions"])
            st.markdown("---")

    if st.button("🔄 Start Over"):
        st.session_state.clear()
        st.rerun()