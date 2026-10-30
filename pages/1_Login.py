"""
Page 1: User Login.
"""
import sys
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.auth_service import login_user

st.set_page_config(page_title="Login — Kannada for Everyone", page_icon="🔑", layout="centered")

# Load CSS
css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if st.session_state.get("authenticated"):
    st.success(f"You are already logged in as **{st.session_state.user.get('name')}**.")
    if st.button("Go to Dashboard", type="primary"):
        st.switch_page("pages/3_Dashboard.py")
    st.stop()

st.markdown("## 🔑 Log In to Your Account")
st.caption("Access your personalized Kannada learning path, saved vocabulary, and practice history.")

with st.form("login_form"):
    email = st.text_input("Email Address", placeholder="e.g. learner@example.com")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please fill in both email and password.")
        else:
            with st.spinner("Authenticating..."):
                ok, msg, user_obj = login_user(email, password)
                if ok and user_obj:
                    st.session_state.authenticated = True
                    st.session_state.user = user_obj
                    st.success("Login successful! Redirecting to dashboard...")
                    st.switch_page("pages/3_Dashboard.py")
                else:
                    st.error(msg or "Invalid email or password.")

st.markdown("---")
col1, col2 = st.columns([2, 1])
with col1:
    st.write("Don't have an account yet?")
with col2:
    if st.button("Register Here", use_container_width=True):
        st.switch_page("pages/2_Register.py")
