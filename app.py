# app.py
import streamlit as st
import time
import pandas as pd
import ai_logic  # Bridge to the brain

st.set_page_config(page_title="Replen AI", page_icon="🤖")

# State management
if 'step' not in st.session_state:
    st.session_state.step = 0

# STEP 0: ONBOARDING
if st.session_state.step == 0:
    st.title("🤖 Welcome to Replen")
    st.write("Let's set up your smart pantry.")
    
    stores = st.multiselect("Which stores do you use?", ["Walmart", "Costco", "Target"])
    h_size = st.number_input("Household Size", min_value=1, max_value=10, value=2)
    
    if st.button("Start Anticipating My Needs"):
        if not stores:
            st.warning("Please select at least one store!")
        else:
            st.session_state.stores = stores
            st.session_state.h_size = h_size
            st.session_state.step = 1
            st.rerun()

# STEP 1: AI ANALYSIS
elif st.session_state.step == 1:
    st.header("Analyzing your consumption patterns...")
    
    # Process data through our Logic File
    results = ai_logic.analyze_pantry(st.session_state.h_size, st.session_state.stores)
    st.session_state.ai_results = results
    
    progress_bar = st.progress(0)
    for i in range(100):
        time.sleep(0.01)
        progress_bar.progress(i + 1)
        
    st.session_state.step = 2
    st.rerun()

# STEP 2: THE DASHBOARD
elif st.session_state.step == 2:
    st.title("⚡ Your Smart Dashboard")
    res = st.session_state.ai_results
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Oat Milk Supply", value=f"{res['days_left']} Days Left")
    with col2:
        st.metric(label="Local Status", value=res['status'])

    # The AI Suggestion Card
    st.info(f"**AI Insight:** {res['recommendation']}")
    
    st.write("### Weekly Usage Trend")
    chart_data = pd.DataFrame([10, 25, 45, 60, 75, 80, 95], columns=["Usage %"])
    st.line_chart(chart_data)
    
    if st.button("Reset Demo"):
        st.session_state.step = 0
        st.rerun()