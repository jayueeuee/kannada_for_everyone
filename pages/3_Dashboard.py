"""
Page 3: Learner Dashboard.
Displays personalized real metrics from MySQL, recommendations, and companion missions.
"""
import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.auth_service import get_current_user_profile
from services.progress_service import get_learner_dashboard_metrics
from services.daily_companion import get_daily_suggestion
from services.mistake_service import summarize_mistake_patterns
from utils.prompts import get_language_name
from config import Config

st.set_page_config(page_title="Dashboard — Kannada for Everyone", page_icon="📊", layout="wide")

css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Authentication Guard
if not st.session_state.get("authenticated") or not st.session_state.get("user"):
    st.warning("⚠️ You must be logged in to view your dashboard.")
    if st.button("Go to Login"):
        st.switch_page("pages/1_Login.py")
    st.stop()

user_id = st.session_state.user["id"]
user = get_current_user_profile(user_id)
if not user:
    st.error("User record could not be loaded. Please re-login.")
    st.stop()

settings = user.get("settings", {})
preferred_city = settings.get("preferred_city", "Bengaluru")
daily_goal = settings.get("daily_goal_minutes", 15)
mother_tongue = user.get("mother_tongue", "en")
level = user.get("level", 1)

if Config.is_hf_enabled() and not Config.is_hf_configured():
    st.warning(
        "Hugging Face AI is not configured. Add your Hugging Face token to `HF_TOKEN` "
        "in the project `.env` file and restart Streamlit. The daily mission below is "
        "a built-in practice suggestion until then."
    )

metrics = get_learner_dashboard_metrics(user_id)
companion = get_daily_suggestion(
    user_id=user_id,
    mother_tongue=mother_tongue,
    level=level,
    city=preferred_city,
    words_due=metrics["words_due"]
)
mistake_summary = summarize_mistake_patterns(user_id)

# Header Section
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1.5rem;">
  <div>
    <h2 style="color: #1b5e20; margin-bottom: 0.2rem;">ನಮಸ್ಕಾರ, {user['name']}! 👋</h2>
    <span style="color: #616161;">Mother tongue: <b>{get_language_name(mother_tongue)}</b> | Level: <b>Level {level}</b> | City: <b>{preferred_city}</b></span>
  </div>
</div>
""", unsafe_allow_html=True)

# Metric Badges Row
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.markdown(f"""
    <div class="metric-container">
      <div class="metric-val">🔥 {metrics['streak_days']}</div>
      <div class="metric-lbl">Day Streak</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-container">
      <div class="metric-val">{metrics['minutes_today']}/{daily_goal}</div>
      <div class="metric-lbl">Minutes Today</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-container">
      <div class="metric-val">{metrics['lessons_completed']}/{metrics['total_lessons']}</div>
      <div class="metric-lbl">Lessons ({metrics['completion_percentage']}%)</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-container">
      <div class="metric-val">{metrics['words_saved']}</div>
      <div class="metric-lbl">Saved Words</div>
    </div>
    """, unsafe_allow_html=True)

with m5:
    badge_color = "#c62828" if metrics['words_due'] > 0 else "#2e7d32"
    st.markdown(f"""
    <div class="metric-container">
      <div class="metric-val" style="color: {badge_color};">⏰ {metrics['words_due']}</div>
      <div class="metric-lbl">Due for Review</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Grid: Left = Daily Companion & Quick Actions, Right = Next Lesson & Reviews
col_left, col_right = st.columns([3, 2])

with col_left:
    # Daily Learning Companion Card
    st.markdown("### ☀️ Today's Practice Mission")
    weather = companion.get("weather")
    weather_badge = f"{weather.get('icon', '☀️')} {weather.get('city')}: {weather.get('temperature_c')}°C ({weather.get('condition_en')})" if weather else f"📍 {preferred_city}"

    st.markdown(f"""
    <div class="kfe-card" style="border-left: 5px solid #f9a825;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span class="kfe-badge kfe-badge-gold">⚡ AI Practice Companion</span>
        <span style="font-size: 0.85rem; color: #555;">{weather_badge}</span>
      </div>
      <h4 style="margin: 4px 0; color: #1b5e20;">{companion.get('title', 'Daily Kannada Challenge')}</h4>
      <p style="color: #424242; margin-bottom: 10px;">{companion.get('suggestion', '')}</p>
      <div class="kfe-panel-green" style="margin-bottom: 8px;">
        <div class="kannada-text">{companion.get('kannada_phrase', '')}</div>
        <div class="translit-text">{companion.get('transliteration', '')}</div>
        <div class="meaning-text" style="font-size: 0.95rem; margin-top: 4px;"><b>Meaning:</b> {companion.get('translation', '')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Action Buttons
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    with c_btn1:
        if st.button("💬 Start AI Text Chat", use_container_width=True, type="primary"):
            st.session_state.active_scenario = companion.get("practice_scenario", "daily-greetings")
            st.switch_page("pages/5_AI_Conversation.py")
    with c_btn2:
        if st.button("🎙️ Open Voice Tutor", use_container_width=True):
            st.session_state.active_scenario = companion.get("practice_scenario", "daily-greetings")
            st.switch_page("pages/6_Voice_Tutor.py")
    with c_btn3:
        if st.button("🎯 Pronunciation", use_container_width=True):
            st.switch_page("pages/9_Pronunciation.py")

    # Mistakes & Corrections Card
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 💡 Learning Insights & Corrections")
    if mistake_summary["total_recorded"] > 0:
        st.markdown(f"""
        <div class="kfe-card">
          <p style="margin: 0 0 8px 0;">You have recorded <b>{mistake_summary['total_recorded']}</b> personalized learning corrections (<b>{mistake_summary['unresolved_count']}</b> to review).</p>
          <div style="font-size: 0.85rem; color: #555;">
            Top categories: {', '.join([f'{k}: {v}' for k, v in mistake_summary['category_breakdown'].items()])}
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Review My Mistakes"):
            st.switch_page("pages/10_Progress.py")
    else:
        st.info("No recorded mistakes yet! As you practice in text and voice role-plays, personalized corrections will appear here.")

with col_right:
    # Recommended Next Lesson Card
    st.markdown("### 📖 Recommended Next Lesson")
    next_les = metrics.get("next_lesson")
    if next_les:
        st.markdown(f"""
        <div class="kfe-card" style="border-top: 4px solid #1b5e20;">
          <span class="kfe-badge">Level {next_les.get('level')} • Lesson {next_les.get('lesson_order')}</span>
          <h4 style="margin: 8px 0 4px 0; color: #1b5e20;">{next_les.get('title')}</h4>
          <p style="font-size: 0.9rem; color: #616161;">{next_les.get('description')}</p>
          <div style="font-size: 0.85rem; color: #757575; margin-bottom: 12px;">
            ⏱ Estimated: {next_les.get('estimated_minutes', 10)} min | Pass score: {next_les.get('pass_score', 70)}%
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("▶ Continue Learning", use_container_width=True, type="primary"):
            st.session_state.selected_lesson_slug = next_les.get("slug")
            st.switch_page("pages/7_Guided_Lessons.py")
    else:
        st.success("🎉 You have completed all available lessons!")

    # Spaced Repetition Due Card
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🗂️ Spaced Repetition Review")
    if metrics["words_due"] > 0:
        st.warning(f"You have **{metrics['words_due']}** words scheduled for memory review today!")
        if st.button("📝 Review Due Words Now", use_container_width=True):
            st.switch_page("pages/8_Vocabulary.py")
    elif metrics["words_saved"] > 0:
        st.success(f"All caught up! You have saved {metrics['words_saved']} words, none due right now.")
        if st.button("Explore Vocabulary Library", use_container_width=True):
            st.switch_page("pages/8_Vocabulary.py")
    else:
        st.info("Save words from lessons and conversations to activate smart spaced repetition memory cards.")
        if st.button("Browse Vocabulary Library", use_container_width=True):
            st.switch_page("pages/8_Vocabulary.py")
