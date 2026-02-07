import streamlit as st
import pandas as pd
import ai_logic
import time
import random

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

if "loading_step" not in st.session_state:
    st.session_state.loading_step = 0

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
TOTAL_CATEGORIES = len(CATEGORY_ORDER)

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

    # Progress bar
    progress = (st.session_state.category_index + 1) / TOTAL_CATEGORIES
    st.progress(progress)
    st.caption(f"Category {st.session_state.category_index + 1} of {TOTAL_CATEGORIES}")

    st.markdown(f"### {category}")
    st.caption("Select what you usually keep at home — or skip if it doesn’t apply.")

    # Load previous selections if any
    default_selection = st.session_state.usuals.get(category, [])

    selections = st.multiselect(
        f"Your usual {category.lower()} items",
        items,
        default=default_selection
    )

    # Update session state only if the user selected something
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
        # Do NOT overwrite previous selection — just move to next
        if st.session_state.category_index < TOTAL_CATEGORIES - 1:
            st.session_state.category_index += 1
        else:
            st.session_state.step = 3
        st.rerun()

    # NEXT
    if col3.button("Next →"):
        # Save selection even if empty
        st.session_state.usuals[category] = selections
        if st.session_state.category_index < TOTAL_CATEGORIES - 1:
            st.session_state.category_index += 1
        else:
            st.session_state.step = 3
        st.rerun()

# -----------------------------
# STEP 3 — REVIEW YOUR CHOICES
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
        st.session_state.step = 99
        st.rerun()

# -----------------------------
# STEP 99 — LOADING SCREEN / AI CURATION
# -----------------------------
elif st.session_state.step == 99:
    st.markdown(
        """
        <style>
        .centered {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 90vh;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="centered">', unsafe_allow_html=True)

    # FULL SCREEN GIF
    st.image(
        "https://media.giphy.com/media/3oEjHEbAfMn6PVEqDS/giphy.gif",
        use_column_width=True
    )

    st.markdown("### 🧠 PantryFull is curating your personalized recommendations…")
    st.caption("Analyzing your pantry, habits, and shopping patterns")

    st.markdown('</div>', unsafe_allow_html=True)

    # Simulate AI processing time
    import time
    time.sleep(3.5)  # make it slightly longer for effect

    # -----------------------------
    # TRIGGER AI LOGIC (shopping list & recipes)
    # -----------------------------
    import ai_logic

    st.session_state.ai_results = ai_logic.generate_shopping_list(
        household_size=st.session_state.h_size,
        grocery_freq=st.session_state.grocery_freq,
        stores=st.session_state.stores,
        pantry_usuals=st.session_state.usuals
    )
    # Move to dashboard/chat
    st.session_state.step = 4
    st.rerun()


# -----------------------------
# STEP 4 — DASHBOARD / AI-ON-DEMAND
# -----------------------------
elif st.session_state.step == 4:
    st.title("⚡ Smart Dashboard")

    # Household info
    col1, col2 = st.columns(2)
    col1.metric("Household Size", st.session_state.h_size)
    col2.metric("Stores", ', '.join(st.session_state.stores))

    st.markdown("---")

    # -----------------------------
# AI-ON-DEMAND: Shopping List + Recipes
# -----------------------------
st.subheader("🛒 Your Next Shopping List")
st.caption("Based on your pantry and consumption, here’s what we recommend:")

if st.session_state.ai_results is not None:
    shopping_list = st.session_state.ai_results.get('shopping_list', [])
    for item in shopping_list:
        st.write(f"• {item['item']} — Qty: {item['recommended_quantity']}")
        st.caption(f"Reason: {item.get('reason', 'No reason provided')}")

    st.markdown("---")

    # Upsell suggestions
    upsells = st.session_state.ai_results.get('upsell_suggestions', [])
    if upsells:
        st.subheader("💡 Complementary Suggestions")
        for u in upsells:
            st.write(f"• {u['item']}")
            st.caption(f"Why: {u.get('why', 'No reason provided')}")

    st.markdown("---")

    # AI-generated recipes
    recipes = st.session_state.ai_results.get('recipes', [])
    if recipes:
        st.subheader("🍳 New Recipes to Try")
        for r in recipes:
            st.markdown(f"**{r['name']}**")
            st.write(r['instructions'])
            st.markdown("---")

        # -----------------------------
        # AI-ON-DEMAND: Recipe Suggestions
        # -----------------------------
        st.subheader("🍳 Recipe Suggestions")
        st.caption("You can make these with your current pantry:")

        recipes = st.session_state.ai_results['recipes']
        for r in recipes:
            st.markdown(f"**{r['name']}**")
            st.write(r['instructions'])
            st.markdown("---")

    # RESET BUTTON
    if st.button("🔄 Start Over"):
        st.session_state.step = 0
        st.session_state.ai_triggered = False
        st.session_state.ai_results = None
        st.session_state.usuals = {}
        st.session_state.category_index = 0
        st.rerun()