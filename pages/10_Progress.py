"""
Page 10: Progress Analytics and Mistake Correction History.
Detailed visualizations, daily practice trends, assessment logs, and mistake management.
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.progress_service import get_learner_dashboard_metrics
from services.mistake_service import get_learner_mistakes, mark_mistake_resolved, summarize_mistake_patterns
from services.assessment_service import get_learner_assessments

st.set_page_config(page_title="Progress & Analytics — Kannada for Everyone", page_icon="📈", layout="wide")

css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if not st.session_state.get("authenticated") or not st.session_state.get("user"):
    st.warning("Please log in to view your progress analytics.")
    if st.button("Log In"):
        st.switch_page("pages/1_Login.py")
    st.stop()

user = st.session_state.user
user_id = user["id"]

st.markdown("## 📈 Learning Analytics & Progress")
st.caption("Track your daily commitment, lesson mastery, conversation performance, and mistake corrections.")

metrics = get_learner_dashboard_metrics(user_id)
mistakes = get_learner_mistakes(user_id)
mistake_summary = summarize_mistake_patterns(user_id)
assessments = get_learner_assessments(user_id)

tab_overview, tab_activity, tab_mistakes, tab_assessments = st.tabs([
    "📊 Overview & Streaks",
    "📅 Daily Practice Trends",
    f"💡 Mistake Corrections ({len(mistakes)})",
    f"📋 Assessment Records ({len(assessments)})"
])

# ----------------- TAB 1: OVERVIEW -----------------
with tab_overview:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Consecutive Day Streak", f"🔥 {metrics['streak_days']} days")
    with m2:
        st.metric("Lesson Completion", f"{metrics['lessons_completed']} / {metrics['total_lessons']}")
    with m3:
        st.metric("Saved Vocabulary Words", metrics['words_saved'])
    with m4:
        st.metric("Role-Play Conversations", metrics['conversations_count'])

    st.markdown("#### 🎯 Curriculum Progress")
    st.progress(metrics["completion_percentage"] / 100.0)
    st.caption(f"{metrics['completion_percentage']}% of the Kannada guided curriculum completed.")

# ----------------- TAB 2: DAILY PRACTICE TRENDS -----------------
with tab_activity:
    daily_history = metrics.get("daily_history", [])
    if daily_history:
        st.markdown("#### 🕒 Practice Minutes (Last 30 Days)")
        df = pd.DataFrame(daily_history)
        df["date_str"] = df["activity_date"].astype(str)
        df = df.sort_values("activity_date")

        chart_df = df.set_index("date_str")[["minutes_spent", "speaking_minutes"]]
        chart_df.columns = ["Total Minutes", "Speaking Minutes"]
        st.bar_chart(chart_df)

        st.markdown("#### 📋 Detailed Daily Records")
        display_df = df[["activity_date", "minutes_spent", "lessons_completed", "words_reviewed", "conversations_completed", "speaking_minutes"]]
        display_df.columns = ["Date", "Minutes Spent", "Lessons Done", "Words Reviewed", "Conversations", "Speaking (mins)"]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No daily learning activity recorded yet. Start a lesson or conversation to see your practice trends!")

# ----------------- TAB 3: MISTAKE CORRECTIONS -----------------
with tab_mistakes:
    st.markdown("### 💡 Personal Mistake & Correction Log")
    st.caption("Mistakes are automatically identified during conversations and deduplicated so you can focus on recurring patterns.")

    if not mistakes:
        st.success("🌟 No mistakes recorded yet! Practice conversations in Text AI Tutor or Voice Tutor to receive guidance.")
    else:
        c_filter, _ = st.columns([2, 3])
        with c_filter:
            show_unresolved = st.checkbox("Show unresolved only", value=False)

        filtered_mistakes = [m for m in mistakes if not m.get("is_resolved")] if show_unresolved else mistakes

        for m in filtered_mistakes:
            status_badge = "✅ Resolved" if m.get("is_resolved") else "⚠️ Need Practice"
            st.markdown(f"""
            <div class="kfe-card" style="margin-bottom: 12px; border-left: 4px solid {'#2e7d32' if m.get('is_resolved') else '#f9a825'};">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="kfe-badge">{m.get('mistake_type', 'other').upper()}</span>
                <span style="font-size: 0.8rem; color: #757575;">Seen {m.get('occurrence_count')} time(s) • {status_badge}</span>
              </div>
              <div style="margin: 8px 0;">
                <div style="color: #c62828;"><b>Original Attempt:</b> {m.get('original_text')}</div>
                <div style="color: #1b5e20;"><b>Suggested Phrasing:</b> {m.get('suggested_text')}</div>
              </div>
              {f'<div style="font-size: 0.9rem; color: #555;"><i>Why: {m.get("explanation")}</i></div>' if m.get("explanation") else ''}
            </div>
            """, unsafe_allow_html=True)

            if not m.get("is_resolved"):
                if st.button("Mark as Understood & Resolved", key=f"res_{m['id']}"):
                    mark_mistake_resolved(user_id, m["id"])
                    st.rerun()

# ----------------- TAB 4: ASSESSMENTS HISTORY -----------------
with tab_assessments:
    st.markdown("### 📋 Completed Assessments & Feedback")
    if not assessments:
        st.info("No assessments completed yet. Take lesson quizzes or finish role-play conversations to build your history.")
    else:
        for a in assessments:
            title = a.get("lesson_title") or a.get("assessment_type").replace("_", " ").title()
            st.markdown(f"""
            <div class="kfe-card" style="margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #1b5e20;">{title}</h4>
                <span class="kfe-badge kfe-badge-gold">Score: {a.get('score')}/{a.get('max_score')}</span>
              </div>
              <div style="font-size: 0.8rem; color: #757575; margin-top: 4px;">Completed on: {str(a.get('created_at'))[:16]}</div>
            </div>
            """, unsafe_allow_html=True)
