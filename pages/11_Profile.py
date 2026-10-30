"""
Page 11: Learner Profile, Preferences, and Account Settings.
"""
import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.auth_service import get_current_user_profile, update_profile, delete_account
from utils.prompts import get_language_name

st.set_page_config(page_title="Profile & Settings — Kannada for Everyone", page_icon="⚙️", layout="wide")

css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if not st.session_state.get("authenticated") or not st.session_state.get("user"):
    st.warning("Please log in to manage your profile.")
    if st.button("Log In"):
        st.switch_page("pages/1_Login.py")
    st.stop()

user_id = st.session_state.user["id"]
user = get_current_user_profile(user_id)
if not user:
    st.error("Failed to load user profile.")
    st.stop()

settings = user.get("settings", {})

st.markdown("## ⚙️ Learner Profile & Learning Preferences")
st.caption("Customize your mother tongue, proficiency level, practice goals, and city context.")

with st.form("profile_form"):
    st.markdown("#### 👤 Account Details")
    c1, c2 = st.columns(2)
    with c1:
        new_name = st.text_input("Full Name", value=user.get("name", ""))
    with c2:
        st.text_input("Email Address (Immutable)", value=user.get("email", ""), disabled=True)

    st.markdown("#### 🎯 Language & Practice Goals")
    c3, c4 = st.columns(2)
    with c3:
        lang_map = {"Marathi (मराठी)": "mr", "Hindi (हिन्दी)": "hi", "English": "en"}
        cur_lang = user.get("mother_tongue", "en")
        inv_lang_map = {v: k for k, v in lang_map.items()}
        sel_lang = st.selectbox(
            "Mother Tongue (Explanation & Translation Language)",
            options=list(lang_map.keys()),
            index=list(lang_map.values()).index(cur_lang) if cur_lang in inv_lang_map else 2
        )
        new_mother_tongue = lang_map[sel_lang]

    with c4:
        level_map = {
            "Level 1: First Words": 1,
            "Level 2: Basic Sentences": 2,
            "Level 3: Everyday Conversations": 3,
            "Level 4: Listening & Speaking": 4,
            "Level 5: Confident Communication": 5
        }
        cur_level = user.get("level", 1)
        sel_level_str = st.selectbox(
            "Proficiency Level",
            options=list(level_map.keys()),
            index=max(0, min(cur_level - 1, 4))
        )
        new_level = level_map[sel_level_str]

    c5, c6 = st.columns(2)
    with c5:
        new_daily_goal = st.slider(
            "Daily Practice Goal (minutes)",
            min_value=5,
            max_value=120,
            step=5,
            value=int(settings.get("daily_goal_minutes", 15))
        )
    with c6:
        city_options = ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi", "Belagavi", "Shivamogga", "Other"]
        cur_city = settings.get("preferred_city", "Bengaluru")
        new_city = st.selectbox(
            "Preferred City for Local Weather & Context",
            options=city_options,
            index=city_options.index(cur_city) if cur_city in city_options else 0
        )

    new_voice = st.checkbox("Enable Recorded Voice Tutor Features", value=bool(settings.get("voice_enabled", True)))

    save_btn = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

    if save_btn:
        ok, msg = update_profile(
            user_id=user_id,
            name=new_name,
            mother_tongue=new_mother_tongue,
            level=new_level,
            daily_goal=new_daily_goal,
            preferred_city=new_city,
            voice_enabled=new_voice
        )
        if ok:
            st.session_state.user["name"] = new_name
            st.session_state.user["mother_tongue"] = new_mother_tongue
            st.session_state.user["level"] = new_level
            st.success("Your preferences have been updated successfully!")
            st.rerun()
        else:
            st.error(msg)

st.markdown("<br><hr>", unsafe_allow_html=True)

# Danger Zone & Account Deletion
st.markdown("### ⚠️ Danger Zone")
with st.expander("Delete Account and All Personal Learning Data"):
    st.write(
        "Deleting your account will permanently remove your login credentials, saved vocabulary, "
        "lesson scores, mistake history, and conversation transcripts from our MySQL database. "
        "This action cannot be undone."
    )
    confirm_text = st.text_input("Type 'DELETE' to confirm account deletion:")
    if st.button("Permanently Delete My Account", type="secondary"):
        if confirm_text.strip() == "DELETE":
            ok, msg = delete_account(user_id)
            if ok:
                st.session_state.authenticated = False
                st.session_state.user = None
                st.success("Your account has been permanently deleted.")
                st.switch_page("app.py")
            else:
                st.error(msg)
        else:
            st.error("Please type 'DELETE' exactly to confirm deletion.")
