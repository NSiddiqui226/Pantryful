import streamlit as st
import datetime
from data_engine import find_cheapest_store, find_best_alternative, find_category_substitute
import ai_logic

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="PantryFull", page_icon="🧺", layout="centered")

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
    st.session_state.ai_results = {"shopping_list": [], "upsell_suggestions": [], "recipes": []}

if "ai_triggered" not in st.session_state:
    st.session_state.ai_triggered = False

if "usuals" not in st.session_state:
    st.session_state.usuals = {}

if "category_index" not in st.session_state:
    st.session_state.category_index = 0

if "last_trip_date" not in st.session_state:
    st.session_state.last_trip_date = None

if "shopping_selection" not in st.session_state:
    st.session_state.shopping_selection = []

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
# STEP 0 — LAST GROCERY TRIP
# -----------------------------
if st.session_state.step == 0:
    st.title("🧺 PantryFull")
    st.caption("Your pantry, but proactive.")
    st.markdown("### When was your last grocery trip?")
    last_trip = st.date_input("Select a date", value=st.session_state.last_trip_date)
    st.session_state.last_trip_date = last_trip

    col1, col2 = st.columns(2)
    if col2.button("Next →"):
        if last_trip:
            st.session_state.step = 1
            st.rerun()
        else:
            st.warning("Please select a date for your last grocery trip.")

# -----------------------------
# STEP 1 — STORES
# -----------------------------
elif st.session_state.step == 1:
    st.title("🧺 PantryFull")
    st.caption("Where do you usually shop?")
    stores = [("Walmart", "Walmart"), ("Costco", "Costco"), ("Target", "Target")]
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
        st.caption("Selected: " + ", ".join(st.session_state.stores_selected))

    st.markdown("---")
    if st.button("Continue →"):
        if st.session_state.stores_selected:
            st.session_state.stores = list(st.session_state.stores_selected)
            st.session_state.step = 2
            st.rerun()
        else:
            st.warning("Please select at least one store.")

# -----------------------------
# STEP 2 — HOUSEHOLD + FREQUENCY
# -----------------------------
elif st.session_state.step == 2:
    st.title("🧺 PantryFull")
    st.caption("Just a few details to personalize things.")
    st.markdown("### How many people are in your household?")
    h_size = st.slider("Household size", 1, 20, st.session_state.get("h_size", 2))
    st.markdown("### How often do you grocery shop per week?")
    grocery_freq = st.slider("Times per week", 1, 7, st.session_state.get("grocery_freq", 2))

    col1, col2 = st.columns(2)
    if col1.button("← Back"):
        st.session_state.step = 1
        st.rerun()
    if col2.button("Next →"):
        st.session_state.h_size = h_size
        st.session_state.grocery_freq = grocery_freq
        st.session_state.step = 3
        st.rerun()

# -----------------------------
# STEP 3 — USUALS
# -----------------------------
elif st.session_state.step == 3:
    category = CATEGORY_ORDER[st.session_state.category_index]
    items = PANTRY_CATEGORIES[category]
    st.title("🧺 PantryFull")
    st.progress((st.session_state.category_index + 1) / TOTAL_CATEGORIES)
    st.caption(f"Category {st.session_state.category_index + 1} of {TOTAL_CATEGORIES}")
    st.markdown(f"### {category}")
    st.caption("Select what you usually keep at home — or skip if it doesn’t apply.")

    if category not in st.session_state.usuals:
        st.session_state.usuals[category] = []
    selected_items = set(st.session_state.usuals[category])

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
            st.session_state.step = 4
        st.rerun()
    if col3.button("Next →"):
        st.session_state.category_index += 1
        if st.session_state.category_index >= TOTAL_CATEGORIES:
            st.session_state.step = 4
        st.rerun()

# -----------------------------
# STEP 4 — REVIEW & AI GENERATE
# -----------------------------
elif st.session_state.step == 4:
    st.title("🧺 Review Your Pantry Setup")
    st.markdown("### 🏪 Stores")
    st.write(", ".join(st.session_state.stores))
    st.markdown("### 👨‍👩‍👧 Household")
    st.write(f"{st.session_state.h_size} people")
    st.markdown("### 🛒 Grocery Frequency")
    st.write(f"{st.session_state.grocery_freq} times per week")
    st.markdown("### 📦 Your Usual Items")
    for cat, items in st.session_state.usuals.items():
        if items:
            st.markdown(f"**{cat}**")
            for i in items:
                st.write(f"• {i}")

    col1, col2 = st.columns(2)
    if col1.button("← Edit Choices"):
        st.session_state.step = 3
        st.rerun()
    if col2.button("Generate AI Insights →"):
        if not st.session_state.ai_triggered:
            st.session_state.ai_results = ai_logic.generate_shopping_list(
                household_size=st.session_state.h_size,
                grocery_freq=st.session_state.grocery_freq,
                stores=st.session_state.stores,
                pantry_usuals=st.session_state.usuals
            )
            st.session_state.ai_triggered = True
        st.session_state.step = 5
        st.rerun()

# -----------------------------
# STEP 5 — DASHBOARD / AI-ON-DEMAND
# -----------------------------
elif st.session_state.step == 5:
    st.title("⚡ Smart Dashboard")
    last_trip = st.session_state.last_trip_date
    days_since = (datetime.date.today() - last_trip).days if last_trip else None

    col1, col2 = st.columns(2)
    col1.metric("Household Size", st.session_state.h_size)
    col2.metric("Stores", ", ".join(st.session_state.stores))

    st.markdown("---")
    tabs = st.tabs(["📦 Your Pantry AI Insights", "🛒 Shopping List", "💡 Upsells", "🍳 Recipes"])

    # AI Insights Tab
    with tabs[0]:
        st.subheader("Your Pantry AI Insights")
        if last_trip:
            st.write(f"📅 Your last grocery trip: {last_trip.strftime('%m/%d/%Y')} ({days_since} day(s) ago)")
            low_items = []
            for cat, items in st.session_state.usuals.items():
                for item in items:
                    threshold_days = max(1, int(7 / st.session_state.grocery_freq))
                    if days_since >= threshold_days:
                        low_items.append(item)
            if low_items:
                st.markdown("⚠️ You are likely running low on:")
                for item in low_items:
                    st.write(f"• {item}")
            else:
                st.write("✅ Your pantry is likely stocked for now.")
            suggested_next = last_trip + datetime.timedelta(days=int(7 / st.session_state.grocery_freq))
            st.write(f"🛒 Suggested next grocery trip: **{suggested_next.strftime('%A, %b %d')}**")
        else:
            st.info("Please select your last grocery trip date in the first step.")

        st.markdown("💰 Deals of the day (mocked):")
        MOCK_DEALS = [
            {"store": "Walmart", "item": "Whole Milk", "price": 2.99},
            {"store": "Costco", "item": "Chicken Breast", "price": 3.79},
            {"store": "Target", "item": "Apples", "price": 0.99},
        ]
        for deal in MOCK_DEALS:
            st.write(f"{deal['item']} at {deal['store']}: ${deal['price']:.2f}")

    # AI-Curated Shopping List
    with tabs[1]:
        st.subheader("Your AI-Curated Shopping List")
        shopping_list = st.session_state.ai_results.get("shopping_list", [])
        if shopping_list:
            st.markdown("**Based on your usual pantry items:**")
            for item in shopping_list:
                selected = st.checkbox(f"{item['item']} — Qty: {item['recommended_quantity']}", value=True,
                                       key=item['item'])
                if selected and item['item'] not in st.session_state.shopping_selection:
                    st.session_state.shopping_selection.append(item['item'])
            if st.button("✅ Add All to List"):
                st.session_state.shopping_selection = [item['item'] for item in shopping_list]
                st.success("All items added to your selection!")
            st.markdown("---")
            st.markdown("**Based on your preferences you might like to add:**")
            upsells = st.session_state.ai_results.get("upsell_suggestions", [])
            for u in upsells:
                selected = st.checkbox(f"{u['item']} — {u.get('why', '')}", value=False, key=f"upsell_{u['item']}")
                if selected and u['item'] not in st.session_state.shopping_selection:
                    st.session_state.shopping_selection.append(u['item'])
        else:
            st.info("No AI-generated shopping list yet.")

    # Upsells Tab
    with tabs[2]:
        st.subheader("All AI Upsells")
        upsells = st.session_state.ai_results.get("upsell_suggestions", [])
        if upsells:
            for u in upsells:
                st.write(f"• {u['item']} — {u.get('why', '')}")
        else:
            st.info("No upsell suggestions at this time.")

    # Recipes Tab
    with tabs[3]:
        st.subheader("Recipes You Can Make")
        recipes = st.session_state.ai_results.get("recipes", [])
        if recipes:
            for r in recipes:
                st.markdown(f"**{r['name']}**")
                st.write(r["instructions"])
                st.markdown("---")
        else:
            st.info("No recipes generated yet.")

    # Reset button
    if st.button("🔄 Start Over"):
        st.session_state.clear()
        st.rerun()