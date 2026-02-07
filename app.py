import streamlit as st
import time
import pandas as pd

# Basic Page Setup
st.set_page_config(page_title="Replen AI", page_icon="🤖")

# State management to keep track of steps
if 'step' not in st.session_state:
    st.session_state.step = 0

# STEP 0: ONBOARDING
if st.session_state.step == 0:
    st.title("🤖 Welcome to Replen")
    st.write("Let's set up your smart pantry.")
    
    stores = st.multiselect("Which stores do you use?", ["Walmart", "Costco", "Target", "Amazon"])
    h_size = st.number_input("Household Size", min_value=1, max_value=10, value=2)
    diet = st.multiselect("Dietary Needs", ["Vegan", "Halal", "Kosher", "None"])
    
    if st.button("Start Anticipating My Needs"):
        st.session_state.h_size = h_size
        st.session_state.step = 1
        st.rerun()

# STEP 1: AI ANALYSIS (The WOW Factor)
elif st.session_state.step == 1:
    st.header("Analyzing your data...")
    progress_bar = st.progress(0)
    
    # Fake AI "thinking" time
    for i in range(100):
        time.sleep(0.02)
        progress_bar.progress(i + 1)
        
    st.session_state.step = 2
    st.rerun()

# STEP 2: THE DASHBOARD
elif st.session_state.step == 2:
    st.title("⚡ Your Smart Dashboard")
    
    # Simple logic: More people = faster consumption
    # Formula: 14 days divided by household size
    days_left = round(14 / st.session_state.h_size)
    
    st.metric(label="Oat Milk Supply", value=f"{days_left} Days Left", delta="-2 Days since yesterday")
    
    st.write("### Consumption Trends")
    # Generating a simple data chart
    data = pd.DataFrame([20, 35, 30, 45, 70, 85, 90], columns=["Usage %"])
    st.line_chart(data)
    
    if st.button("Approve Restock Order"):
        st.balloons()
        st.success("Order placed successfully!")