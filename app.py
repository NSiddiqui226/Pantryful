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
/* Global text color */
html, body, [class*="css"] {
    color: #1E3A8A !important;  /* dark blue */
}

/* Titles & headers */
h1, h2, h3, h4, h5, h6 {
    color: #1E3A8A !important;
}

/* Captions, labels, markdown, metrics */
p, span, label, div {
    color: #1E3A8A !important;
}
</style>
""", unsafe_allow_html=True)

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
st.markdown("""
<style>
/* Import Aleo font from Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Aleo&display=swap');

/* Apply Alteo font to all titles (st.title) */
h1 {
    font-family: 'Aleo', sans-serif !important;
    font-weight: normal !important; /* Aleo is naturally bold, adjust if needed */
}

/* Optional: make all headers (h2, h3) use Aleo too */
h2, h3 {
    font-family: 'Aleo', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = -1

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
# WELCOME PAGE
# -----------------------------
if st.session_state.step == -1:
    st.title("🧺 PantryFull")

    col_img, col_text = st.columns([1, 2])

    with col_img:
        st.image("grocerybag.png", use_container_width=True)

    with col_text:
        st.markdown("""
        **Welcome to PantryFull!**  
        You'll never have to say "oh no, we're out" again  

        PantryFull helps you keep your pantry organized, track what you usually buy,  
        and get AI-powered insights to make shopping easier.  

        Never run out of your essentials again!
        """)

        st.button("Get Started →", on_click=lambda: st.session_state.update({"step": 0}))


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
# -----------------------------
# STEP 1 — STORES (Logo Pill Buttons)
# -----------------------------
# -----------------------------
# STEP 1 — STORES (Logo Above Button)
# -----------------------------
elif st.session_state.step == 1:
    st.title("🧺 PantryFull")
    st.caption("Where do you usually shop?")

    stores = [
        ("Walmart", "walmart.png"),
        ("Costco", "costco.png"),
        ("Target", "target.png")
    ]

    cols = st.columns(len(stores))
    for i, (store_name, logo_file) in enumerate(stores):
        is_selected = store_name in st.session_state.stores_selected
        selected_class = "selected-pill" if is_selected else ""

        with cols[i]:
            # Display logo above button
            st.image(logo_file, width=50)

            # Pill-style button
            if st.button(store_name, key=f"store_{store_name}"):
                if is_selected:
                    st.session_state.stores_selected.remove(store_name)
                else:
                    st.session_state.stores_selected.add(store_name)
                st.rerun()

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

elif st.session_state.step == 5:
    st.title("⚡ Smart Pantry Dashboard")
    
    # --- 1. THE DATA SYNC ---
    # Force the AI to analyze the data if it hasn't yet
    if not st.session_state.ai_triggered:
        with st.spinner("🧠 AI is analyzing your pantry & store prices..."):
            # This calls your predict_low_stock which handles the Scarcity vs Surplus logic
            st.session_state.ai_results = ai_logic.predict_low_stock(
                usual_items=st.session_state.usuals,
                household_size=st.session_state.h_size,
                grocery_freq=st.session_state.grocery_freq,
                last_trip=st.session_state.last_trip_date
            )
            st.session_state.ai_triggered = True

    results = st.session_state.ai_results
    shopping_list = results.get("shopping_list", [])
    recipes = results.get("recipes", [])
    low_items = results.get("low_items", [])

    # --- 2. TOP KPI BAR ---
    from data_engine import MOCK_PURCHASE_HISTORY
    # Calculate how many items are over 10 days old
    aging_items = [k for k, v in MOCK_PURCHASE_HISTORY.items() if (datetime.date.today() - v).days > 10]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Household", f"{st.session_state.h_size} Ppl")
    m2.metric("Waste Risk", f"{len(aging_items)} Items", delta="Action Required", delta_color="inverse")
    m3.metric("Stock Alerts", f"{len(low_items)} Low", delta="-5% vs Last Week")

    st.markdown("---")

    # --- 3. THE INTERACTIVE GRID ---
    col_left, col_right = st.columns(2)

    # CARD 1: SMART SHOPPING (Scarcity Logic)
    with col_left:
        with st.container(border=True):
            st.markdown("### 🛒 Smart Cart")
            st.caption("Cheapest matches for items you're running out of")
            
            if shopping_list:
                for item in shopping_list:
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        # Displaying the item and the reason it was added
                        st.checkbox(f"**{item['item']}**", key=f"list_{item['item']}", value=True)
                        st.caption(f"📍 {item.get('store', 'Walmart')} • {item.get('reason', 'Refill')}")
                    with c2:
                        # Pulling real mock price from data_engine
                        price = item.get('price', 0.00)
                        st.markdown(f"**${price:.2f}**")
            else:
                st.success("✅ Shopping list is clear!")

    # CARD 2: FRESHNESS TRACKER (Historical Logic)
    with col_right:
        with st.container(border=True):
            st.markdown("### 📦 Freshness Tracker")
            st.caption("Based on last bought dates in Data Engine")
            
            for item, buy_date in MOCK_PURCHASE_HISTORY.items():
                days_old = (datetime.date.today() - buy_date).days
                # Visual bar: Red for old, Green for fresh
                progress = min(days_old / 21, 1.0)
                bar_color = "red" if days_old > 14 else "orange" if days_old > 7 else "green"
                
                st.markdown(f"**{item}** — {days_old} days old")
                st.markdown(f"""
                    <div style="width:100%; background:#f0f2f6; border-radius:10px; height:8px;">
                        <div style="width:{progress*100}%; background:{bar_color}; height:8px; border-radius:10px;"></div>
                    </div>
                """, unsafe_allow_html=True)
                st.write("") # Spacer

    # CARD 3: ZERO-WASTE CHEF (Surplus Logic)
    st.markdown("### 🍳 Zero-Waste Recipes")
    st.caption("Using aging items while protecting your low-stock staples")
    
    if recipes:
        # Display recipes in a horizontal scrolling-style grid
        recipe_cols = st.columns(len(recipes))
        for i, r in enumerate(recipes):
            with recipe_cols[i]:
                with st.container(border=True):
                    st.markdown(f"##### {r['name']}")
                    # Extract the "clears out" info if available
                    if "clears out" in r['name'].lower():
                        st.toast(f"Found recipe for {r['name']}")
                    
                    with st.expander("View Preparation"):
                        st.write(r['instructions'])
                    
                    if st.button("Cook This", key=f"cook_{i}", use_container_width=True):
                        st.balloons()
    else:
        st.info("AI is looking for recipes that won't use up the last of your stock...")

    # --- 4. ACTION FOOTER ---
    st.markdown("---")
    if st.button("🔄 Force Refresh AI Insights"):
        st.session_state.ai_triggered = False
        st.rerun()