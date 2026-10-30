"""
Kannada for Everyone — Main Application Entry Point.
Streamlit Multipage Application Architecture.
"""
import os
import sys
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from db import check_database_connection
from utils.prompts import get_language_name

# 1. Page Configuration
st.set_page_config(
    page_title="Kannada for Everyone",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom CSS
css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# 3. Initialize Shared Safe Session State
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "active_session_id" not in st.session_state:
        st.session_state.active_session_id = None
    if "active_scenario" not in st.session_state:
        st.session_state.active_scenario = None
    if "selected_lesson_slug" not in st.session_state:
        st.session_state.selected_lesson_slug = None


init_session_state()

# 4. Render Sidebar Navigation & Auth State
with st.sidebar:
    st.markdown("### 🌿 Kannada for Everyone")
    st.markdown("*Learn Kannada. Speak confidently. Connect locally.*")
    st.markdown("---")

    if st.session_state.authenticated and st.session_state.user:
        u = st.session_state.user
        st.success(f"👤 Logged in: **{u.get('name', 'Learner')}**")
        st.caption(f"Mother Tongue: **{get_language_name(u.get('mother_tongue', 'en'))}**")
        st.caption(f"Current Level: **Level {u.get('level', 1)}**")

        st.markdown("#### 🧭 Quick Navigation")
        st.page_link("pages/3_Dashboard.py", label="📊 Dashboard", icon="📈")
        st.page_link("pages/4_Situations.py", label="🎭 Situations Role-Play", icon="💬")
        st.page_link("pages/5_AI_Conversation.py", label="🤖 Text AI Tutor", icon="🗨️")
        st.page_link("pages/6_Voice_Tutor.py", label="🎙️ Recorded Voice Tutor", icon="🗣️")
        st.page_link("pages/7_Guided_Lessons.py", label="📚 Guided Lessons", icon="📖")
        st.page_link("pages/8_Vocabulary.py", label="📝 Vocabulary & SRS", icon="🗂️")
        st.page_link("pages/9_Pronunciation.py", label="🎤 Pronunciation Practice", icon="🎯")
        st.page_link("pages/10_Progress.py", label="📉 Progress & Mistakes", icon="⭐")
        st.page_link("pages/11_Profile.py", label="⚙️ Profile & Settings", icon="🔧")

        st.markdown("---")
        if st.button("🚪 Log Out", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.active_session_id = None
            st.session_state.active_scenario = None
            st.rerun()
    else:
        st.info("👋 Welcome! Please log in or register to track your learning progress.")
        st.page_link("pages/1_Login.py", label="🔑 Log In", icon="🔓")
        st.page_link("pages/2_Register.py", label="📝 Register New Account", icon="✨")

    st.markdown("---")
    # Database status indicator in sidebar
    db_ok, db_msg = check_database_connection()
    if db_ok:
        st.caption("🟢 Database Connected")
    else:
        st.caption("🔴 Database Offline")
        with st.expander("DB Help"):
            st.caption(f"Details: {db_msg}")
            st.caption("Run `python init_db.py` to create schema & seed data.")

# 5. Public Homepage Main Body
st.markdown("""
<div style="text-align: center; padding: 2rem 1rem 1.5rem 1rem;">
  <h1 style="color: #1b5e20; font-size: 2.8rem; margin-bottom: 0.5rem; font-weight: 800;">
    Speak Kannada with Confidence
  </h1>
  <p style="font-size: 1.25rem; color: #424242; max-width: 750px; margin: 0 auto 1.5rem auto;">
    Learn practical spoken Kannada through everyday conversations, interactive lessons,
    and your personal AI tutor tailored for <b>Marathi</b>, <b>Hindi</b>, and <b>English</b> speakers.
  </p>
</div>
""", unsafe_allow_html=True)

# CTA Buttons Row
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
with col_btn2:
    if st.session_state.authenticated:
        if st.button("🚀 Open My Dashboard", use_container_width=True, type="primary"):
            st.switch_page("pages/3_Dashboard.py")
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✨ Get Started", use_container_width=True, type="primary"):
                st.switch_page("pages/2_Register.py")
        with c2:
            if st.button("🔑 Log In", use_container_width=True):
                st.switch_page("pages/1_Login.py")

st.markdown("<br>", unsafe_allow_html=True)

# Sample Learning Example Card
st.markdown("""
<div class="kfe-panel-green">
  <div style="font-size: 0.85rem; font-weight: 700; color: #2e7d32; text-transform: uppercase; margin-bottom: 4px;">
    📖 Sample Educational Expression
  </div>
  <div class="kannada-large">ನಮಸ್ಕಾರ! ಏನು ಬೇಕು?</div>
  <div class="translit-text">Namaskāra! Ēnu bēku?</div>
  <div class="meaning-text" style="margin-top: 4px;">
    <b>Meaning:</b> Hello! What would you like? (A warm, courteous everyday greeting used across Karnataka)
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🌟 What You Can Do")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.markdown("""
    <div class="kfe-card">
      <div style="font-size: 1.8rem; margin-bottom: 8px;">🎭</div>
      <h4 style="margin: 0 0 6px 0; color: #1b5e20;">Everyday Conversations</h4>
      <p style="color: #616161; font-size: 0.95rem;">
        Role-play realistic scenarios: grocery stores, local markets, darshinis, auto rides, and neighborly chats.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="kfe-card">
      <div style="font-size: 1.8rem; margin-bottom: 8px;">🎙️</div>
      <h4 style="margin: 0 0 6px 0; color: #1b5e20;">Recorded Voice Tutor</h4>
      <p style="color: #616161; font-size: 0.95rem;">
        Practice spoken Kannada with local audio transcription and spoken tutor replies.
      </p>
    </div>
    """, unsafe_allow_html=True)

with col_f2:
    st.markdown("""
    <div class="kfe-card">
      <div style="font-size: 1.8rem; margin-bottom: 8px;">📚</div>
      <h4 style="margin: 0 0 6px 0; color: #1b5e20;">Guided Learning Path</h4>
      <p style="color: #616161; font-size: 0.95rem;">
        5 structured levels from First Words to Confident Fluency with matching, fill-in-the-blank, and translation quizzes.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="kfe-card">
      <div style="font-size: 1.8rem; margin-bottom: 8px;">🗂️</div>
      <h4 style="margin: 0 0 6px 0; color: #1b5e20;">Vocabulary & Spaced Repetition</h4>
      <p style="color: #616161; font-size: 0.95rem;">
        Curated words with Marathi, Hindi, and English meanings. Review words due today with SM-2 memory intervals.
      </p>
    </div>
    """, unsafe_allow_html=True)

with col_f3:
    st.markdown("""
    <div class="kfe-card">
      <div style="font-size: 1.8rem; margin-bottom: 8px;">🎯</div>
      <h4 style="margin: 0 0 6px 0; color: #1b5e20;">Pronunciation Practice</h4>
      <p style="color: #616161; font-size: 0.95rem;">
        Speak target phrases, compare recognized transcripts against native Kannada text, and receive immediate guidance.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="kfe-card">
      <div style="font-size: 1.8rem; margin-bottom: 8px;">☀️</div>
      <h4 style="margin: 0 0 6px 0; color: #1b5e20;">Weather-Aware Companion</h4>
      <p style="color: #616161; font-size: 0.95rem;">
        Daily 5-minute practice missions tuned to your local time and live weather conditions in Bengaluru, Mysuru, or your city.
      </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# How it works section
st.markdown("### 🧭 How It Works")
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown("##### 1. Choose Mother Tongue")
    st.caption("Learn in Marathi, Hindi, or English with Kannada as the target language.")
with s2:
    st.markdown("##### 2. Choose Your Level")
    st.caption("Start with basic words or jump into practical everyday sentence patterns.")
with s3:
    st.markdown("##### 3. Practise & Speak")
    st.caption("Engage in text and recorded-voice role-plays with gentle feedback and corrections.")
with s4:
    st.markdown("##### 4. Retain & Master")
    st.caption("Review saved vocabulary with spaced repetition and track your daily learning streak.")

st.markdown("<br>", unsafe_allow_html=True)
if not st.session_state.authenticated:
    _, center_col, _ = st.columns([1, 1, 1])
    with center_col:
        if st.button("🚀 Start Learning Now — Free", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Register.py")
