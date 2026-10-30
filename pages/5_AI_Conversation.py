"""
Page 5: Situation-Based Text AI Tutor.
Interactive conversational role-play with Kannada script, transliteration, mother-tongue translation, and mistake tracking.
"""
import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from repositories.situations import get_situation_by_slug, get_all_active_situations
from repositories.conversations import (
    create_session,
    get_session,
    add_message,
    get_session_messages,
    update_session_status
)
from repositories.progress import record_activity
from config import Config
from services.ai_tutor import generate_tutor_response, generate_conversation_assessment
from services.mistake_service import log_mistake_from_ai
from services.vocabulary_service import save_word_for_user
from repositories.vocabulary import get_vocabulary_list

st.set_page_config(page_title="AI Conversation — Kannada for Everyone", page_icon="💬", layout="wide")

css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Auth check
if not st.session_state.get("authenticated") or not st.session_state.get("user"):
    st.warning("Please log in to converse with the AI tutor.")
    if st.button("Log In"):
        st.switch_page("pages/1_Login.py")
    st.stop()

user = st.session_state.user
user_id = user["id"]
mother_tongue = user.get("mother_tongue", "en")
level = user.get("level", 1)

if not Config.is_hf_configured():
    st.error(
        "Hugging Face AI is not configured. Open the project `.env` file, set "
        "`HF_TOKEN=hf_your_token_here` using your Hugging Face token with Inference "
        "Providers permission, save it, and restart Streamlit. Do not paste the token into chat."
    )
    st.stop()

# Scenario selection
active_slug = st.session_state.get("active_scenario") or "grocery-shopping"
situation = get_situation_by_slug(active_slug)
if not situation:
    all_sits = get_all_active_situations()
    situation = all_sits[0] if all_sits else None

if not situation:
    st.error("No active role-play scenario found. Please run `python init_db.py`.")
    st.stop()

# Ensure Active Database Conversation Session
if not st.session_state.get("active_session_id"):
    new_sess_id = create_session(user_id=user_id, situation_id=situation["id"], mode="text")
    st.session_state.active_session_id = new_sess_id
    # Add initial greeting from tutor
    greeting_kannada = "ನಮಸ್ಕಾರ! ಬನ್ನಿ, ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?"
    greeting_trans = "Namaskāra! Banni, nānu nimage hēge sahāya māḍali?"
    greeting_transla = "Hello! Welcome, how may I help you?"
    add_message(
        session_id=new_sess_id,
        speaker="assistant",
        message_text=greeting_kannada,
        transliteration=greeting_trans,
        translation=greeting_transla
    )

session_id = st.session_state.active_session_id

# Header and scenario bar
st.markdown(f"""
<div style="background: #e8f5e9; padding: 1rem 1.25rem; border-radius: 10px; margin-bottom: 1.25rem; border: 1px solid #c8e6c9;">
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <div>
      <span class="kfe-badge">{situation['category']} • Level {situation['difficulty_level']}</span>
      <h3 style="margin: 4px 0; color: #1b5e20;">{situation['title']}</h3>
      <span style="color: #424242; font-size: 0.9rem;"><b>AI Persona:</b> {situation['ai_role']}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Action controls
c_top1, c_top2 = st.columns([4, 1])
with c_top2:
    if st.button("🏁 Finish & Score", type="secondary", use_container_width=True):
        messages = get_session_messages(session_id)
        with st.spinner("Generating conversation feedback..."):
            assessment = generate_conversation_assessment(
                mother_tongue=mother_tongue,
                level=level,
                scenario_title=situation["title"],
                messages=messages
            )
            update_session_status(
                session_id=session_id,
                user_id=user_id,
                status="completed",
                summary=assessment.get("summary_feedback", "Completed scenario roleplay."),
                assessment_data=assessment
            )
            record_activity(user_id=user_id, conversations_completed=1, minutes_spent=5)
            st.session_state.last_assessment = assessment
            st.session_state.active_session_id = None
            st.rerun()

# Display last assessment if just finished
if st.session_state.get("last_assessment"):
    la = st.session_state.last_assessment
    st.markdown(f"""
    <div class="kfe-card" style="border: 2px solid #2e7d32; background-color: #f1f8f3;">
      <h4 style="color: #1b5e20; margin-top: 0;">🎉 Role-Play Completed!</h4>
      <p><b>Overall Score:</b> {la.get('overall_score', 80)}/100</p>
      <p><b>Summary:</b> {la.get('summary_feedback', '')}</p>
      <p><b>Strengths:</b> {', '.join(la.get('strengths', []))}</p>
      <p><b>Areas to Improve:</b> {', '.join(la.get('areas_to_improve', []))}</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start New Conversation"):
        st.session_state.last_assessment = None
        st.rerun()
    st.stop()

# Retrieve Messages
messages = get_session_messages(session_id)

# Render Chat History
chat_container = st.container()
with chat_container:
    for m in messages:
        speaker = m.get("speaker")
        text = m.get("message_text", "")
        trans = m.get("transliteration", "")
        transl = m.get("translation", "")
        fb = m.get("feedback_json") or {}

        if speaker == "user":
            st.markdown(f"""
            <div class="chat-bubble-user">
              <span style="font-size: 0.8rem; font-weight: 700; color: #1565c0;">YOU</span>
              <div style="font-size: 1.05rem; margin-top: 3px;">{text}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-bubble-ai">
              <span style="font-size: 0.8rem; font-weight: 700; color: #2e7d32;">{situation['ai_role'].upper()}</span>
              <div class="kannada-text" style="margin-top: 3px;">{text}</div>
              {f'<div class="translit-text">{trans}</div>' if trans else ''}
              {f'<div class="meaning-text" style="font-size: 0.95rem; margin-top: 4px;"><b>Meaning:</b> {transl}</div>' if transl else ''}
            </div>
            """, unsafe_allow_html=True)

            # Display corrections if any
            if fb.get("correction"):
                st.markdown(f"""
                <div style="background: #fff8e1; border-left: 4px solid #fbc02d; padding: 8px 12px; border-radius: 6px; margin: -4px 0 12px 14px; font-size: 0.9rem;">
                  <b>💡 Gentle Correction:</b> {fb.get('correction')}<br>
                  <span style="color: #666;">{fb.get('feedback', '')}</span>
                </div>
                """, unsafe_allow_html=True)

            # Display vocabulary buttons
            vocab_items = fb.get("vocabulary", [])
            if vocab_items:
                v_cols = st.columns(min(len(vocab_items), 3))
                for v_idx, v_item in enumerate(vocab_items[:3]):
                    with v_cols[v_idx]:
                        if st.button(f"➕ Save '{v_item.get('kannada')}'", key=f"v_{m['id']}_{v_idx}"):
                            # Match in library or save
                            lib_matches = get_vocabulary_list(search=v_item.get('kannada'))
                            if lib_matches:
                                save_word_for_user(user_id, lib_matches[0]["id"])
                                st.toast(f"Saved '{v_item.get('kannada')}' to your vocabulary!")

st.markdown("<br>", unsafe_allow_html=True)

# Input form
with st.form("chat_input_form", clear_on_submit=True):
    col_in, col_send = st.columns([5, 1])
    with col_in:
        user_input = st.text_input(
            "Your reply in Kannada (script or Roman text)",
            placeholder="Type your response... (e.g. Namaskara, idara bele eshtu? / ಒಂದು ಕೆಜಿ ಟೊಮ್ಯಾಟೊ ಕೊಡಿ)",
            label_visibility="collapsed"
        )
    with col_send:
        sent = st.form_submit_button("Send 🚀", type="primary", use_container_width=True)

if sent and user_input.strip():
    # Generate before persisting so a provider error does not leave an unanswered turn.
    try:
        with st.spinner("Tutor is thinking..."):
            ai_resp = generate_tutor_response(
                mother_tongue=mother_tongue,
                level=level,
                scenario_title=situation["title"],
                ai_role=situation["ai_role"],
                system_hint=situation.get("system_hint", ""),
                conversation_history=messages,
                user_message=user_input.strip()
            )

        add_message(
            session_id=session_id,
            speaker="user",
            message_text=user_input.strip()
        )

        if ai_resp.get("correction"):
            log_mistake_from_ai(
                user_id=user_id,
                original_text=user_input.strip(),
                suggested_text=ai_resp.get("correction", ""),
                explanation=ai_resp.get("feedback", ""),
                mistake_type=ai_resp.get("mistake_type")
            )

        add_message(
            session_id=session_id,
            speaker="assistant",
            message_text=ai_resp.get("reply", ""),
            transliteration=ai_resp.get("transliteration", ""),
            translation=ai_resp.get("translation", ""),
            feedback_data={
                "correction": ai_resp.get("correction"),
                "vocabulary": ai_resp.get("vocabulary", []),
                "feedback": ai_resp.get("feedback"),
                "next_question": ai_resp.get("next_question")
            }
        )

        record_activity(user_id=user_id, minutes_spent=2)
        st.rerun()

    except Exception as e:
        st.error(f"Error communicating with AI: {str(e)}")
