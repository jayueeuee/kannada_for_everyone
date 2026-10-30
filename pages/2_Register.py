"""
Page 2: Learner Registration and Onboarding.
"""
import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.auth_service import register_user

st.set_page_config(page_title="Register — Kannada for Everyone", page_icon="✨", layout="centered")

css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if st.session_state.get("authenticated"):
    st.info("You are already logged in.")
    if st.button("Go to Dashboard", type="primary"):
        st.switch_page("pages/3_Dashboard.py")
    st.stop()

st.markdown("## ✨ Create Your Free Account")
st.caption("Personalized Kannada learning tailored to your native language and everyday goals.")

with st.form("register_form"):
    name = st.text_input("Full Name", placeholder="e.g. Rahul Patil / Priya Sharma")
    email = st.text_input("Email Address", placeholder="name@example.com")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        password = st.text_input("Password (min 6 characters)", type="password")
    with col_p2:
        confirm_password = st.text_input("Confirm Password", type="password")

    st.markdown("#### 🎯 Learner Preferences")

    mother_tongue_options = {
        "Marathi (मराठी)": "mr",
        "Hindi (हिन्दी)": "hi",
        "English": "en"
    }
    sel_lang_label = st.selectbox(
        "Mother Tongue (Explanations & Translations)",
        list(mother_tongue_options.keys())
    )
    mother_tongue = mother_tongue_options[sel_lang_label]

    level_options = {
        "Level 1: First Words (Greetings, Yes/No, Numbers)": 1,
        "Level 2: Basic Sentences (Needs & Wants, Simple questions)": 2,
        "Level 3: Everyday Conversations (Shopping, Eating, Travel)": 3,
        "Level 4: Listening & Speaking (Directions, Fluency)": 4,
        "Level 5: Confident Communication (Workplace & Nuances)": 5
    }
    sel_level_label = st.selectbox("Current Kannada Level", list(level_options.keys()))
    level = level_options[sel_level_label]

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        daily_goal = st.select_slider(
            "Daily Learning Goal (minutes)",
            options=[5, 10, 15, 20, 30, 45, 60],
            value=15
        )
    with col_g2:
        city = st.selectbox(
            "Preferred City for Context & Weather",
            ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi", "Belagavi", "Other"]
        )

    submitted = st.form_submit_button("Create My Account", type="primary", use_container_width=True)

    if submitted:
        with st.spinner("Setting up your learner account..."):
            ok, msg, user_obj = register_user(
                name=name,
                email=email,
                password=password,
                confirm_password=confirm_password,
                mother_tongue=mother_tongue,
                level=level,
                daily_goal=daily_goal,
                preferred_city=city
            )
            if ok and user_obj:
                st.session_state.authenticated = True
                st.session_state.user = user_obj
                st.success("Account created successfully! Welcome to Kannada for Everyone.")
                st.switch_page("pages/3_Dashboard.py")
            else:
                st.error(msg)

st.markdown("---")
c1, c2 = st.columns([2, 1])
with c1:
    st.write("Already have an account?")
with c2:
    if st.button("Log In Instead", use_container_width=True):
        st.switch_page("pages/1_Login.py")
