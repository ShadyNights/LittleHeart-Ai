import streamlit as st
import sys
from pathlib import Path
import base64
import os

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Correctly import from new auth functions
from frontend_streamlit.services.auth import login_user, sign_up_user, reset_password
from frontend_streamlit.services.api_client import init_websocket

st.set_page_config(
    page_title="LittleHeart AI Care",
    page_icon="🩺",
    layout="wide"
)

init_websocket()

assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
img_path = os.path.join(
    assets_dir,
    "WhatsApp_Image_2026-02-18_at_3.14.00_PM-removebg-preview.png"
)

try:
    with open(img_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode()
        icon_src = f"data:image/png;base64,{b64_data}"
except Exception:
    icon_src = "https://img.icons8.com/color/96/breastfeeding.png"

# --- THEME CSS (High Contrast + Glassmorphism) ---
theme_css = """
<style>
/* --- CUSTOM HEADER STYLES --- */
.header-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 25px;
    padding: 30px;
    margin-bottom: 40px;
    backdrop-filter: blur(18px);
    background: rgba(255,255,255,0.12);
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,0.25);
    box-shadow: 0 8px 30px rgba(0,0,0,0.08);
}

.brand-icon {
    width: 85px;
    height: auto;
    animation: heartbeat 1.8s infinite ease-in-out;
    filter: drop-shadow(0 0 10px rgba(37,99,235,0.4));
}

@keyframes heartbeat {
    0% { transform: scale(1); }
    25% { transform: scale(1.08); }
    40% { transform: scale(1); }
    60% { transform: scale(1.08); }
    100% { transform: scale(1); }
}

.brand-text {
    font-size: 52px;
    font-weight: 700;
    background: linear-gradient(90deg, #2563EB, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 12px rgba(37,99,235,0.25);
}

.ecg-line {
    width: 170px;
    height: 60px;
}

.ecg-path {
    fill: none;
    stroke: #2563EB;
    stroke-width: 3;
    stroke-dasharray: 400;
    stroke-dashoffset: 400;
    animation: ecg-animation 2.2s linear infinite;
}

@keyframes ecg-animation {
    to {
        stroke-dashoffset: 0;
    }
}

/* --- USER PROVIDED THEME FIX --- */
/* GLOBAL BACKGROUND */
div[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #E0F2FE 0%, #F8FAFC 100%);
}

/* MAIN CONTAINER */
.block-container {
    padding-top: 2rem;
}

/* GLASS CARD */
.glass-card {
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(12px);
    border-radius: 18px;
    padding: 25px;
    border: 1px solid rgba(0,0,0,0.08);
    box-shadow: 0 8px 30px rgba(15,23,42,0.1);
}

/* HEADINGS */
h1, h2, h3 {
    color: #0F172A !important;
}

/* LABELS */
label {
    color: #1E293B !important;
    font-weight: 500;
}

/* BUTTONS */
.stButton>button {
    background: linear-gradient(90deg, #2563EB, #1D4ED8);
    color: white;
    border-radius: 12px;
    font-weight: 600;
    padding: 0.6rem 1.5rem;
    border: none;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A, #1E293B);
}

/* Force sidebar text/links to be white */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] span,
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] svg,
section[data-testid="stSidebar"] .st-emotion-cache-16idsys p {
    color: white !important;
    fill: white !important;
}

/* Hover effect */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    background-color: rgba(255, 255, 255, 0.05);
}

/* Active page highlight */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: rgba(255, 255, 255, 0.1);
    color: #4ade80 !important; /* Light green for active */
}

/* Active page icon */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] svg {
    fill: #4ade80 !important;
}

/* METRICS */
[data-testid="metric-container"] {
    background: white;
    border-radius: 12px;
    padding: 10px;
}
</style>
"""

# --- HEADER HTML (Dynamic with f-string for icon_src) ---
header_html = f"""
<div class="header-container">
    <img src="{icon_src}" class="brand-icon">
    <svg class="ecg-line" viewBox="0 0 160 60">
      <polyline class="ecg-path"
        points="0,30 20,30 30,10 45,50 60,30 80,30 90,15 110,45 125,30 160,30" />
    </svg>
    <div class="brand-text">
        LittleHeart AI Care
    </div>
</div>
"""

st.markdown(theme_css + header_html, unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    
def attempt_login():
    email = st.session_state.get("login_email", "")
    password = st.session_state.get("login_password", "")
    role, token = login_user(email, password)
    if role:
        st.session_state.authenticated = True
        st.session_state.role = role
        st.session_state.access_token = token
        st.success("Login successful")
        st.rerun()
    else:
        st.error("Invalid credentials")

if not st.session_state.authenticated:
    col1, col2 = st.columns([1,1])

    with col1:
        st.markdown("### 🔐 Secure Access Portal")
        
        tab1, tab2 = st.tabs(["Log In", "Create Account"])
        
        with tab1:
            with st.form("login_form"):
                st.text_input("Email", key="login_email")
                st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Sign In", width="stretch")
                
                if submit:
                    attempt_login()
            
            with st.expander("Forgot Password?", icon="🔑"):
                reset_email = st.text_input("Enter your registered email", key="reset_email_input")
                if st.button("Send Reset Link", width="stretch"):
                    if reset_email:
                        success, msg = reset_password(reset_email)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter an email address.")

        with tab2:
            st.markdown("Join LittleHeart AI Care to monitor your health.")
            new_email = st.text_input("Email", key="signup_email")
            new_pass = st.text_input("Password", type="password", key="signup_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="signup_confirm")
            
            if st.button("Create Account", width="stretch"):
                if new_pass != confirm_pass:
                    st.error("Passwords do not match!")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    success, msg = sign_up_user(new_email, new_pass)
                    if success:
                        st.success(msg)
                        st.info("Please verify your email before logging in.")
                    else:
                        st.error(msg)

    with col2:
        st.info("""
        👩‍🍼 **Designed for Early Detection**  
        🏥 **Real-Time Risk Alerts**  
        🤖 **Hybrid AI Clinical Engine**  
        🔒 **Secure & Auditable System**  
        """)

else:
    st.success(f"Logged in as {st.session_state.role}")
    st.info("👈 Use the sidebar to navigate between dashboards.")