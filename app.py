import streamlit as st
import time
import pandas as pd
import ai_logic 

st.set_page_config(page_title="Replen AI", page_icon="🤖")

if 'step' not in st.session_state:
    st.session_state.step = 0

# STEP 0: ONBOARDING
if st.session_state.step == 0:
    st.title("🤖 Welcome to Replen")
    stores = st.multiselect("Which stores do you use?", ["Walmart", "Costco", "Target"])
    h_size = st.number_input("Household Size", min_value=1, max_value=10, value=2)
    
    if st.button("Start Anticipating My Needs"):
        if stores:
            st.session_state.stores = stores
            st.session_state.h_size = h_size
            st.session_state.step = 1
            st.rerun()
        else:
            st.warning("Select a store first!")

# STEP 1: LOADING
elif st.session_state.step == 1:
    st.header("AI is analyzing your consumption...")
    # Trigger the logic
    st.session_state.ai_results = ai_logic.analyze_pantry(st.session_state.h_size, st.session_state.stores)
    
    bar = st.progress(0)
    for i in range(100):
        time.sleep(0.01)
        bar.progress(i + 1)
    st.session_state.step = 2
    st.rerun()

# STEP 2: DASHBOARD
elif st.session_state.step == 2:
    st.title("⚡ Smart Dashboard")
    res = st.session_state.ai_results

    col1, col2 = st.columns(2)
    col1.metric("Oat Milk Supply", f"{res['days_left']} Days")
    col2.metric("Store Status", res['status'])

    st.error(res['recommendation']) if "ALERT" in res['recommendation'] else st.success(res['recommendation'])
    
    with st.expander("🤖 AI Chef's Tip"):
        st.write(res['ai_tip'])

    st.line_chart(pd.DataFrame([10, 25, 40, 55, 70, 90], columns=["Usage %"]))
    
    if st.button("Reset Demo"):
        st.session_state.step = 0
        st.rerun()