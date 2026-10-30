"""
Page 4: Role-Play Situations Library.
Browse and launch real-life conversational scenarios.
"""
import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from repositories.situations import get_all_active_situations

st.set_page_config(page_title="Situations — Kannada for Everyone", page_icon="🎭", layout="wide")

css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if not st.session_state.get("authenticated") or not st.session_state.get("user"):
    st.warning("Please log in to participate in role-play situations.")
    if st.button("Log In"):
        st.switch_page("pages/1_Login.py")
    st.stop()

st.markdown("## 🎭 Real-Life Situation Role-Plays")
st.markdown("Select a real-world scenario to practice speaking with your personal AI Kannada tutor.")

situations = get_all_active_situations()
if not situations:
    st.error("No active situations found in database. Please run `python init_db.py` to seed scenarios.")
    st.stop()

# Categories filter
categories = ["All"] + sorted(list({s["category"] for s in situations}))
sel_category = st.selectbox("Filter by Category", categories)

filtered = situations if sel_category == "All" else [s for s in situations if s["category"] == sel_category]

# Render situations in grid
cols = st.columns(2)
for idx, sit in enumerate(filtered):
    col = cols[idx % 2]
    with col:
        st.markdown(f"""
        <div class="kfe-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span class="kfe-badge">{sit['category']}</span>
            <span style="font-size: 0.8rem; color: #757575;">Level {sit['difficulty_level']}</span>
          </div>
          <h4 style="margin: 4px 0 6px 0; color: #1b5e20;">{sit['title']}</h4>
          <p style="font-size: 0.95rem; color: #424242; margin-bottom: 8px;">{sit['description']}</p>
          <div style="font-size: 0.85rem; color: #2e7d32; margin-bottom: 12px;">
            <b>AI Role:</b> {sit['ai_role']}
          </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💬 Text Chat", key=f"text_{sit['slug']}", use_container_width=True, type="primary"):
                st.session_state.active_scenario = sit["slug"]
                st.session_state.active_session_id = None  # New session
                st.switch_page("pages/5_AI_Conversation.py")
        with c2:
            if st.button("🎙️ Voice Session", key=f"voice_{sit['slug']}", use_container_width=True):
                st.session_state.active_scenario = sit["slug"]
                st.switch_page("pages/6_Voice_Tutor.py")
