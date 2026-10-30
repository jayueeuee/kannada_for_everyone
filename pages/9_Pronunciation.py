"""
Page 9: Spoken Pronunciation Practice and Transcript Analysis.
Compares spoken audio transcripts against target Kannada phrases with constructive feedback.
"""
import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from repositories.vocabulary import get_vocabulary_list
from services.speech_service import evaluate_pronunciation, transcribe_audio_bytes
from services.assessment_service import record_pronunciation_attempt
from repositories.progress import record_activity
from utils.prompts import get_language_name

st.set_page_config(page_title="Pronunciation — Kannada for Everyone", page_icon="🎯", layout="wide")

css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if not st.session_state.get("authenticated") or not st.session_state.get("user"):
    st.warning("Please log in to practice pronunciation.")
    if st.button("Log In"):
        st.switch_page("pages/1_Login.py")
    st.stop()

user = st.session_state.user
user_id = user["id"]
mother_tongue = user.get("mother_tongue", "en")

st.markdown("## 🎯 Kannada Pronunciation Practice")
st.caption(
    "Select a phrase, practice speaking it, and receive instant transcript-based comparison feedback. "
    "Audio is evaluated for word-level accuracy."
)

# Practice Phrases from vocabulary
vocab_items = get_vocabulary_list(level=user.get("level", 1))
if not vocab_items:
    vocab_items = get_vocabulary_list()

phrase_options = {v["id"]: f"{v['kannada_text']} ({v['transliteration']}) — {v['english_meaning']}" for v in vocab_items}
sel_id = st.selectbox(
    "Select Target Kannada Phrase to Practice:",
    options=list(phrase_options.keys()),
    format_func=lambda x: phrase_options[x]
)

target_item = next(v for v in vocab_items if v["id"] == sel_id)

st.markdown(f"""
<div class="kfe-card" style="border: 2px solid #2e7d32; background: #fdfdfb; padding: 1.5rem; text-align: center;">
  <span class="kfe-badge">{target_item.get('category')} • Level {target_item.get('level')}</span>
  <div class="kannada-large" style="margin: 0.8rem 0 0.3rem 0; font-size: 2.4rem;">{target_item['kannada_text']}</div>
  <div class="translit-text" style="font-size: 1.25rem;">{target_item['transliteration']}</div>
  <div class="meaning-text" style="margin-top: 6px;">
    <b>Meaning:</b> EN: {target_item['english_meaning']} | HI: {target_item['hindi_meaning']} | MR: {target_item['marathi_meaning']}
  </div>
  {f'<div style="font-size: 0.85rem; color: #666; margin-top: 6px;"><i>Example: {target_item.get("example_kannada")}</i></div>' if target_item.get("example_kannada") else ''}
</div>
""", unsafe_allow_html=True)

st.markdown("### 🎙️ Submit Your Spoken Attempt")

tab_audio, tab_text = st.tabs(["📁 Upload Spoken Audio File", "⌨️ Manual Transcript Entry"])

recognized_transcript = ""

with tab_audio:
    st.markdown("Record your voice on your phone or computer and upload the audio file (`.wav`, `.mp3`, `.m4a`, `.ogg`):")
    audio_file = st.file_uploader("Upload audio recording", type=["wav", "mp3", "m4a", "ogg"], key="pron_audio")

    if audio_file is not None:
        if st.button("Transcribe & Analyze Audio", type="primary"):
            with st.spinner("Transcribing speech locally with Whisper..."):
                raw_bytes = audio_file.read()
                try:
                    recognized_transcript = transcribe_audio_bytes(raw_bytes, audio_file.name)
                except (RuntimeError, ValueError) as exc:
                    st.error(f"Local transcription failed: {exc}")
                else:
                    if not recognized_transcript:
                        st.warning(
                            "No speech was recognized. You can also test pronunciation comparison "
                            "using the 'Manual Transcript Entry' tab."
                        )

with tab_text:
    st.markdown("Type or paste what speech recognition recognized (or practice typing Kannada script):")
    text_input = st.text_input("Spoken Transcript Text", placeholder="e.g. ನಮಸ್ಕಾರ")
    if st.button("Analyze Transcript Accuracy", type="primary"):
        recognized_transcript = text_input.strip()

# Evaluation & Results Card
if recognized_transcript:
    eval_result = evaluate_pronunciation(
        target_text=target_item["kannada_text"],
        recognized_text=recognized_transcript,
        mother_tongue=mother_tongue
    )

    score = eval_result["similarity_score"]
    is_exact = eval_result["is_exact_match"]

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Pronunciation Assessment Result")

    border_color = "#2e7d32" if score >= 75 else "#f9a825"
    st.markdown(f"""
    <div class="kfe-card" style="border-left: 6px solid {border_color};">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <h4 style="margin: 0; color: #1b5e20;">Similarity Match: {score}%</h4>
        <span class="kfe-badge">{'Exact Match 🌟' if is_exact else ('Good Attempt 👍' if score >= 75 else 'Needs Practice 🔁')}</span>
      </div>
      <p style="margin: 8px 0; font-size: 1.05rem;">{eval_result['feedback']}</p>
      <div style="background: #fafafa; padding: 10px; border-radius: 6px; font-size: 0.95rem;">
        <div><b>Target:</b> <span class="kannada-text" style="font-size: 1rem;">{eval_result['target']}</span></div>
        <div><b>Recognized:</b> <span style="font-size: 1rem; color: #1565c0;">{eval_result['recognized']}</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if eval_result.get("missing_words"):
        st.caption(f"Missing words from target: `{', '.join(eval_result['missing_words'])}`")
    if eval_result.get("extra_words"):
        st.caption(f"Extra recognized words: `{', '.join(eval_result['extra_words'])}`")

    # Save assessment and log activity
    record_pronunciation_attempt(
        user_id=user_id,
        target_text=target_item["kannada_text"],
        recognized_text=recognized_transcript,
        similarity_score=score,
        feedback_data=eval_result,
        vocabulary_id=target_item["id"]
    )
    record_activity(user_id=user_id, minutes_spent=2, speaking_minutes=1)
    st.success("Practice attempt saved to your learning progress!")

st.markdown("---")
st.markdown("""
> [!NOTE]
> **Assessment Disclosure**: This module assesses pronunciation via transcript similarity comparison between speech recognition output and the target Kannada text. It helps reinforce accurate word pronunciation and cadence.
""")
