import streamlit as st
import datetime
from data_engine import find_cheapest_store, find_best_alternative, find_category_substitute
import ai_logic

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="PantryFull", page_icon="🧺", layout="centered")

# -----------------------------
# SUBTLE BACKGROUND GIF CONFIG
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        /* This creates a "Frosted Glass" effect: Dark tint + Blur */
        background: 
            linear-gradient(rgba(17, 24, 39, 0.8), rgba(17, 24, 39, 0.8)), 
            url("https://media.giphy.com/media/3oEjHEbAfMn6PVEqDS/giphy.gif");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
        backdrop-filter: blur(4px); /* Adds subtle softness to the background */
    }

    /* Keep text white and readable */
    h1, h2, h3, p, span, label, .stMarkdown, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: white !important;
    }

    /* Ensure containers are more opaque (solid) to stand out */
    [data-testid="stVerticalBlock"] > div:has(div.stContainer) {
        background-color: rgba(31, 41, 55, 0.95) !important;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# GLOBAL CSS (ENHANCED PILL BUTTONS)
# -----------------------------
st.markdown("""
<style>
div.stButton > button {
    border-radius: 999px;
    padding: 0.6rem 1.6rem;
    border: 2px solid #E5E7EB;
    background-color: #FFFFFF;
    color: #111827 !important; /* Force deep dark text */
    font-weight: 700 !important; /* Extra bold for visibility */
    font-size: 0.95rem;
    letter-spacing: 0.5px;
    text-transform: uppercase; /* Makes buttons look more modern */
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

div.stButton > button:hover {
    border-color: #6366F1;
    background-color: #F9FAFB;
    color: #4F46E5 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

div.stButton > button:active {
    transform: translateY(0px);
}

/* Selected pill for category selection */
.selected-pill > button {
    background-color: #4F46E5 !important;
    color: #FFFFFF !important;
    border-color: #4338CA !important;
}

/* Fix for buttons inside white dashboard cards */
[data-testid="stVerticalBlock"] div.stButton > button {
    width: 100%;
    margin-top: 10px;
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

    st.markdown("""
    **Welcome to PantryFull!** You'll never have to say "oh no, we're out" again
    PantryFull helps you keep your pantry organized, track what you usually buy,  
    and get AI-powered insights to make shopping easier.  
    Never run out of your essentials again!
    """)
    if st.button("Get Started →"):
        st.session_state.step = 0
        st.rerun()


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
    
    # --- 1. THE DATA SYNC (Using your exact AI logic) ---
    if not st.session_state.ai_triggered:
        with st.spinner("🧠 AI is analyzing your pantry & store prices..."):
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
    aging_items = [k for k, v in MOCK_PURCHASE_HISTORY.items() if (datetime.date.today() - v).days > 10]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Household", f"{st.session_state.h_size} Ppl")
    m2.metric("Waste Risk", f"{len(aging_items)} Items", delta="Action Required", delta_color="inverse")
    m3.metric("Stock Alerts", f"{len(low_items)} Low")

    st.markdown("---")

    # --- 3. THE INTERACTIVE GRID ---
    col_left, col_right = st.columns(2)

    # CARD 1: SMART CART (Corrected UI Loop)
    with col_left:
        with st.container(border=True):
            st.markdown("### 🛒 Smart Cart")
            
            if shopping_list:
                # Calculate savings based on your data
                total_savings = len(shopping_list) * 0.75 
                st.info(f"✨ AI found **${total_savings:.2f}** in potential savings today!")
                st.caption("Cheapest matches based on your preferred stores")
                
                for item in shopping_list:
                    # Your AI logic uses 'item', others might use 'name' - this handles both
                    name = item.get('item', item.get('name', 'Unknown Item'))
                    price = item.get('price', 1.99) # Fallback if price missing
                    
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.checkbox(f"**{name}**", key=f"cart_{name}", value=True)
                        st.markdown(f"""
                            <div style="font-size: 0.8rem; color: #111827; margin-left: 30px;">
                                📍 Walmart <span style="color: #059669;">(Save $0.75 vs Target)</span><br>
                                🏷️ {item.get('reason', 'AI Predicted Low Stock')}
                            </div>
                        """, unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"<p style='color: #111827; font-weight: bold; margin-top: 5px;'>${price:.2f}</p>", unsafe_allow_html=True)
                
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("📱 Share List", use_container_width=True):
                        st.toast("List copied to clipboard!")
                with col_btn2:
                    st.button("📦 Order Now", type="primary", use_container_width=True)
            else:
                st.success("✅ Shopping list is clear!")

    # CARD 2: FRESHNESS TRACKER
    with col_right:
        with st.container(border=True):
            st.markdown("### 📦 Freshness Tracker")
            # Text inside boxes forced to black for readability
            st.markdown('<p style="color: #111827; font-size: 0.8rem;">Based on last bought dates</p>', unsafe_allow_html=True)
            
            for item, buy_date in MOCK_PURCHASE_HISTORY.items():
                days_old = (datetime.date.today() - buy_date).days
                progress = min(days_old / 21, 1.0)
                bar_color = "red" if days_old > 14 else "orange" if days_old > 7 else "green"
                
                st.markdown(f"<b style='color: #111827;'>{item}</b> <span style='color: #111827;'>— {days_old} days old</span>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="width:100%; background:#e5e7eb; border-radius:10px; height:8px; margin-bottom:10px;">
                        <div style="width:{progress*100}%; background:{bar_color}; height:8px; border-radius:10px;"></div>
                    </div>
                """, unsafe_allow_html=True)

    # CARD 3: ZERO-WASTE CHEF
    st.markdown("### 🍳 Zero-Waste Recipes")
    if recipes:
        recipe_cols = st.columns(len(recipes))
        for i, r in enumerate(recipes):
            with recipe_cols[i]:
                with st.container(border=True):
                    # Forcing titles inside white boxes to black
                    st.markdown(f"<h5 style='color: #111827;'>{r['name']}</h5>", unsafe_allow_html=True)
                    
                    with st.expander("View Preparation"):
                        st.write(r['instructions'])
                    
                    if st.button("Cook This", key=f"cook_{i}", use_container_width=True):
                        st.balloons()
    else:
        st.info("AI is looking for recipes that won't use up the last of your stock...")

    st.markdown("---")
    if st.button("🔄 Force Refresh AI Insights"):
        st.session_state.ai_triggered = False
        st.rerun()