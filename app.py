import streamlit as st
import datetime
from data_engine import find_cheapest_store, find_best_alternative, find_category_substitute
import ai_logic
import chat_bot

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="PantryFul", page_icon="🧺", layout="centered")

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
[data-testid="stVerticalBlock"] div.stButton > button:not(.get-started-primary) {
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

    # st.markdown("""
    # **Welcome to PantryFull!** You'll never have to say "oh no, we're out" again
    # PantryFull helps you keep your pantry organized, track what you usually buy,  
    # and get AI-powered insights to make shopping easier.  
    # Never run out of your essentials again!
    # """)
    st.markdown('<div class="get-started-btn">', unsafe_allow_html=True)

    if st.button("Get Started →"):
        st.session_state.step = 0
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


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
            st.session_state.ai_results = ai_logic.predict_low_stock(
                usual_items=st.session_state.usuals,
                household_size=st.session_state.h_size,
                grocery_freq=st.session_state.grocery_freq,
                last_trip=st.session_state.last_trip_date
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
    m1.metric("Household", f"{st.session_state.h_size} People")
    m2.metric("Waste Risk", f"{len(aging_items)} Items", delta="Action Required", delta_color="inverse")
    m3.metric("Stock Alerts", f"{len(low_items)} Low")

    st.markdown("---")

    # --- 3. THE INTERACTIVE GRID ---
    col_left, col_right = st.columns(2)

    # CARD 1: SMART CART (AI-Driven)
    with col_left:
        with st.container(border=True):
            st.markdown("### 🛒 Smart Cart")

            if shopping_list:
                total_savings = sum(item.get("savings", 0) for item in shopping_list)

                st.info(f"✨ AI found **${total_savings:.2f}** in potential savings today!")
                st.caption("Optimized using live store pricing and your preferences")

                for item in shopping_list:
                    name = item["item"]
                    best_store = item.get("best_store")
                    best_price = item.get("best_price")
                    second_store = item.get("second_store")
                    savings = item.get("savings", 0)
                    reason = item.get("reason", "AI predicted need")

                    c1, c2 = st.columns([3, 1])

                    with c1:
                        st.checkbox(
                            f"**{name}**",
                            key=f"cart_{name}",
                            value=True
                        )
                        if best_store:
                            store_line = f"📍 {best_store}"
                            if second_store and savings > 0:
                                store_line += f" <span style='color:#059669;'>(Save ${savings:.2f} vs {second_store})</span>"
                        else:
                            store_line = "📍 No preferred store available"

                        st.markdown(
                            f"""
                            <div style="font-size: 0.8rem; color: #111827; margin-left: 30px;">
                                {store_line}<br>
                                🏷️ {reason}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        

                        if item.get("alternative"):
                            alt = item["alternative"]
                            st.markdown(
                                f"""
                                <div style="font-size: 0.75rem; margin-left: 30px; color:#6B7280;">
                                    🔁 Alternative: {alt['item']} (${alt['price']})
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                    with c2:
                        price_display = (
                            f"${best_price:.2f}"
                            if isinstance(best_price, (int, float))
                            else "Price unavailable"
                        )

                        st.markdown(
                            f"<p style='font-weight:600; margin-top:6px;'>{price_display}</p>",
                            unsafe_allow_html=True
                        )

                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    st.button("📱 Share List", key="share_cart", use_container_width=True)

                with col_btn2:
                    st.button("📦 Order Now", key="order_cart", type="primary", use_container_width=True)

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
    # --- ADD THIS TO THE VERY BOTTOM OF app.py ---

# 1. Initialize Conversation State (Only if not already set)
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your Pantry AI. Ask me for a recipe or shopping advice! 🤖"}
    ]

# 2. Add the Chatbot CSS (Pinned to bottom right)
st.markdown("""
<style>
    /* Floating Toggle Button */
    div.stButton > button[data-testid="baseButton-secondary"] {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        z-index: 1001;
        background-color: #FF4B4B !important;
        color: white !important;
        font-size: 24px;
    }

    /* THE CHAT BOX CONTAINER */
    [data-testid="stVerticalBlockBorderWrapper"]:has(#chat-anchor) {
        position: fixed !important;
        bottom: 90px !important;
        right: 20px !important;
        width: 320px !important;
        height: 500px !important;
        background-color: white !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important;
        z-index: 1000 !important;
        padding: 0px !important;
        overflow: hidden !important;
    }

    .orange-header {
        background-color: #000080;
        padding: 15px;
        border-radius: 15px 15px 0 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# 3. Chat Logic
# We wrap this in a container to ensure it stays in its own "layer"
if st.button("💬", key="chat_toggle_btn"):
    st.session_state.chat_open = not st.session_state.chat_open

if st.session_state.chat_open:
    with st.container():
        st.markdown('<div id="chat-anchor"></div>', unsafe_allow_html=True)
        
        st.markdown("""
            <div class="orange-header">
                <h4 style='color: white; margin: 0; font-family: sans-serif;'>🤖 Pantry Assistant</h4>
            </div>
        """, unsafe_allow_html=True)

        with st.container():
            # Messages Area
            msg_area = st.container(height=320, border=False)
            
            with msg_area:
                for msg in st.session_state.messages:
                    role_label = "AI" if msg["role"] == "assistant" else "You"
                    # Using black color for text inside the white box regardless of global CSS
                    st.markdown(f"<p style='color: black !important;'><b>{role_label}:</b> {msg['content']}</p>", unsafe_allow_html=True)

            # Input Function
            def send_to_ai():
                user_text = st.session_state.chat_input
                if user_text:
                    st.session_state.messages.append({"role": "user", "content": user_text})
                    try:
                        # Explicitly call the model from ai_logic
                        response = ai_logic.model.generate_content(user_text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        # Print the actual error to your terminal for debugging
                        print(f"DEBUG CHAT ERROR: {e}")
                        st.session_state.messages.append({"role": "assistant", "content": "I'm having a bit of trouble connecting."})
                    st.session_state.chat_input = "" 

            st.text_input("Ask me anything...", key="chat_input", on_change=send_to_ai)

st.markdown("""
<style>
/* FORCE ALL STREAMLIT BUTTONS TO NAVY BLUE */
div.stButton > button {
    background-color: #000080 !important; /* Navy Blue */
    color: #FFFFFF !important;           /* White Text */
    border-color: #000080 !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Hover state: Darker Navy */
div.stButton > button:hover {
    background-color: #000066 !important; 
    color: #FFFFFF !important;
    border-color: #000066 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

/* Active (pressed) */
div.stButton > button:active {
    background-color: #000044 !important;
    transform: translateY(0px);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ONLY the Get Started button */
.get-started-btn div.stButton > button {
    background-color: #22C55E !important;   /* green */
    color: #FFFFFF !important;
    border-color: #22C55E !important;
    font-size: 1.1rem !important;
    padding: 0.8rem 2rem !important;
}

/* Hover */
.get-started-btn div.stButton > button:hover {
    background-color: #16A34A !important;
    border-color: #16A34A !important;
}
</style>
""", unsafe_allow_html=True)