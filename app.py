import streamlit as st
import pandas as pd
import ai_logic  # Make sure generate_shopping_list is defined here

st.set_page_config(page_title="Replen AI", page_icon="🤖", layout="centered")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if 'step' not in st.session_state:
    st.session_state.step = 0

if 'ai_results' not in st.session_state:
    st.session_state.ai_results = None

if 'ai_triggered' not in st.session_state:
    st.session_state.ai_triggered = False

if 'usuals' not in st.session_state:
    st.session_state.usuals = []

# -----------------------------
# SIMULATED INVENTORY FOR PREDICTIVE SEARCH
# -----------------------------
STORE_INVENTORY = {
    "Walmart": {
        "Whole Milk": ["Great Value", "Horizon Organic"],
        "Oat Milk": ["Oatly", "Kirkland"],
        "Eggs": ["Great Value", "Eggland's Best"],
        "Bread": ["Wonder", "Sara Lee"]
    },
    "Target": {
        "Whole Milk": ["Good & Gather"],
        "Oat Milk": ["Good & Gather"],
        "Eggs": ["Good & Gather"],
        "Bread": ["Dave's Killer Bread"]
    },
    "Costco": {
        "Whole Milk": ["Kirkland"],
        "Oat Milk": ["Kirkland"],
        "Eggs": ["Kirkland"],
        "Bread": ["Kirkland"]
    }
}

# -----------------------------
# STEP 0 — ONBOARDING (Stores)
# -----------------------------
if st.session_state.step == 0:
    st.title("🧺 PantryFull")
    st.caption("Your pantry, but proactive.")

    st.markdown("### Where do you usually shop?")
    stores = st.multiselect("Select all that apply", ["Walmart", "Costco", "Target"], key="stores_select")

    st.markdown("---")
    if st.button("Continue →"):
        if stores:
            st.session_state.stores = stores
            st.session_state.step = 1
        else:
            st.warning("Please select at least one store to continue.")

# -----------------------------
# STEP 1 — ONBOARDING (Household + Frequency)
# -----------------------------
elif st.session_state.step == 1:
    st.title("🧺 PantryFull")
    st.caption("Just a few details to personalize your experience.")

    st.markdown("### How many people are in your household?")
    h_size = st.slider("Household size", min_value=1, max_value=20, value=2)

    st.markdown("### How often do you go grocery shopping per week?")
    grocery_freq = st.slider(
        "Times per week",
        min_value=1,
        max_value=7,
        value=2,
        help="Used to predict when you'll need more items."
    )

    st.markdown("---")
    col1, col2 = st.columns(2)
    if col1.button("← Back"):
        st.session_state.step = 0
    if col2.button("Next →"):
        st.session_state.h_size = h_size
        st.session_state.grocery_freq = grocery_freq
        st.session_state.step = 2

# -----------------------------
# STEP 2 — ONBOARDING (Usuals / Pantry Items)
# -----------------------------
elif st.session_state.step == 2:
    st.title("🧺 PantryFull — Your Usual Items")
    st.caption("Select items and brands from your preferred stores.")

    # Flatten available items from selected stores
    available_items = set()
    for store in st.session_state.stores:
        available_items.update(STORE_INVENTORY.get(store, {}).keys())
    available_items = sorted(available_items)

    # Select canonical item
    selected_item = st.selectbox("Search for an item:", [""] + list(available_items))

    if selected_item:
        # Show all available brands for that item in selected stores
        brands = []
        for store in st.session_state.stores:
            brands += STORE_INVENTORY.get(store, {}).get(selected_item, [])
        brands = sorted(set(brands))

        selected_brand = st.selectbox(f"Select a brand for {selected_item}:", [""] + brands)
        if selected_brand:
            display_name = f"{selected_item} ({selected_brand})"
            if display_name not in st.session_state.usuals:
                st.session_state.usuals.append(display_name)

    # Display current usuals
    if st.session_state.usuals:
        st.subheader("Your usual items:")
        for i, item in enumerate(st.session_state.usuals, start=1):
            st.write(f"{i}. {item}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    if col1.button("← Back"):
        st.session_state.step = 1
    if col2.button("Finish Onboarding →"):
        st.session_state.step = 3

# -----------------------------
# STEP 3 — DASHBOARD / AI-ON-DEMAND
# -----------------------------
elif st.session_state.step == 3:
    st.title("⚡ Smart Dashboard")

    # Household info
    col1, col2 = st.columns(2)
    col1.metric("Household Size", st.session_state.h_size)
    col2.metric("Stores", ', '.join(st.session_state.stores))

    st.markdown("---")

    # -----------------------------
    # AI-ON-DEMAND: Shopping List
    # -----------------------------
    st.subheader("🛒 Your Next Shopping List")
    st.caption("Based on your pantry and consumption, here’s what you might need next.")

    if not st.session_state.ai_triggered:
        if st.button("🤖 Generate Shopping List"):
            st.session_state.ai_results = ai_logic.generate_shopping_list(
                st.session_state.h_size,
                st.session_state.stores,
                st.session_state.usuals,
                st.session_state.grocery_freq
            )
            st.session_state.ai_triggered = True
    elif st.session_state.ai_results is not None:
        # Show shopping list
        shopping_list = st.session_state.ai_results['shopping_list']
        for item in shopping_list:
            st.write(f"• {item['name']} — Qty: {item['quantity']}")

        st.markdown("---")

        # -----------------------------
        # AI-ON-DEMAND: Recipe Suggestions
        # -----------------------------
        st.subheader("🍳 Recipe Suggestions")
        st.caption("You have these items in your pantry, try these recipes!")

        recipes = st.session_state.ai_results['recipes']
        for r in recipes:
            st.markdown(f"**{r['name']}**")
            st.write(r['instructions'])
            st.markdown("---")

    # Reset button
    if st.button("🔄 Start Over"):
        st.session_state.step = 0
        st.session_state.ai_triggered = False
        st.session_state.ai_results = None
        st.session_state.usuals = []