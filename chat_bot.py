import streamlit as st
import ai_logic  # This imports your model and setup

st.set_page_config(page_title="Pantry AI", layout="wide")

# 1. Initialize Conversation
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your Pantry AI. Ask me for a recipe or shopping advice! 🤖"}
    ]

# 2. CSS: ADAPTIVE FONT COLORS BASED ON DEVICE THEME
st.markdown("""
<style>
    /* Floating Toggle Button */
    .stButton > button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        z-index: 1001;
        background-color: #FF4B4B;
        color: white;
    }

    /* THE WHITE BOX: Locked size for demo */
    [data-testid="stVerticalBlockBorderWrapper"]:has(#chat-anchor) {
        position: fixed !important;
        bottom: 80px !important;
        right: 20px !important;
        width: 320px !important;
        height: 480px !important;
        background-color: white !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3) !important;
        z-index: 1000 !important;
        padding: 0px !important;
        overflow: hidden !important;
    }

    .navy-blue-header {
        background-color: #000080;
        padding: 15px;
        border-radius: 15px 15px 0 0;
        text-align: center;
    }

    /* --- ADAPTIVE TEXT LOGIC --- */
    
    /* Default for Light Mode: Black Text */
    [data-testid="stVerticalBlockBorderWrapper"]:has(#chat-anchor) p, 
    [data-testid="stVerticalBlockBorderWrapper"]:has(#chat-anchor) b,
    [data-testid="stVerticalBlockBorderWrapper"]:has(#chat-anchor) span {
        color: black !important;
        font-size: 14px !important;
    }

    /* Automatic Switch for Dark Mode: White Text */
    @media (prefers-color-scheme: dark) {
        [data-testid="stVerticalBlockBorderWrapper"]:has(#chat-anchor) p, 
        [data-testid="stVerticalBlockBorderWrapper"]:has(#chat-anchor) b,
        [data-testid="stVerticalBlockBorderWrapper"]:has(#chat-anchor) span {
            color: white !important;
        }
    }
    
    .inner-chat-padding {
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Toggle Button
if st.button("💬"):
    st.session_state.chat_open = not st.session_state.chat_open

# 4. The Chat Logic
if st.session_state.chat_open:
    with st.container():
        st.markdown('<div id="chat-anchor"></div>', unsafe_allow_html=True)
        
        st.markdown("""
            <div class="navy-blue-header">
                <h4 style='color: white; margin: 0;'>🤖 Pantry Assistant</h4>
            </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="inner-chat-padding">', unsafe_allow_html=True)
            
            msg_area = st.container(height=300, border=False)
            
            with msg_area:
                for msg in st.session_state.messages:
                    role_label = "AI" if msg["role"] == "assistant" else "You"
                    # Note: The CSS above will handle the text color automatically
                    st.markdown(f"<p><b>{role_label}:</b> {msg['content']}</p>", unsafe_allow_html=True)

            # 5. Input Function
            def send_to_ai():
                user_text = st.session_state.chat_input
                if user_text:
                    st.session_state.messages.append({"role": "user", "content": user_text})
                    try:
                        # This calls the fixed model in ai_logic.py
                        response = ai_logic.model.generate_content(user_text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        # This will now show the new error if one occurs
                        print(f"DEBUG ERROR: {e}")
                        st.session_state.messages.append({"role": "assistant", "content": "Connection issue fixed! Try again."})
                    st.session_state.chat_input = ""

            st.text_input("Ask me anything...", key="chat_input", on_change=send_to_ai)
            st.markdown('</div>', unsafe_allow_html=True)