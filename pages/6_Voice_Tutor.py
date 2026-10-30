"""Page 6: Recorded Kannada voice practice using local open models."""
import base64
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from repositories.progress import record_activity
from repositories.situations import get_all_active_situations
from config import Config
from services.ai_tutor import generate_tutor_response
from services.speech_service import transcribe_audio_bytes
from utils.prompts import get_language_name

st.set_page_config(page_title="Voice Tutor — Kannada for Everyone", page_icon="🎙️", layout="wide")

css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

if not st.session_state.get("authenticated") or not st.session_state.get("user"):
    st.warning("Please log in to use voice practice.")
    if st.button("Log In"):
        st.switch_page("pages/1_Login.py")
    st.stop()

if not Config.is_hf_configured():
    st.error(
        "Hugging Face AI is not configured. Open the project `.env` file, set "
        "`HF_TOKEN=hf_your_token_here` using your Hugging Face token with Inference "
        "Providers permission, save it, and restart Streamlit. Do not paste the token into chat."
    )
    st.stop()

user = st.session_state.user
user_id = user["id"]
mother_tongue = user.get("mother_tongue", "en")
level = user.get("level", 1)
situations = get_all_active_situations()
if not situations:
    st.error("No active role-play scenarios found. Please run `python init_db.py`.")
    st.stop()

st.markdown("## 🎙️ Kannada Voice Practice")
st.caption(
    "Record or upload a spoken turn. Hugging Face Whisper transcribes the audio, "
    "then the Kannada tutor responds in text. Use the listen button to hear the reply."
)
st.info(
    f"Explanations are tailored for **{get_language_name(mother_tongue)}**. "
    "Spoken playback uses your browser's available Kannada voice. Text and audio are sent to Hugging Face for inference."
)
st.caption(
    "If recording shows an error, allow microphone access for localhost in your browser and refresh. "
    "You can use the Upload audio tab instead."
)

scenario_by_slug = {item["slug"]: item for item in situations}
current_slug = st.session_state.get("active_scenario")
slug_options = list(scenario_by_slug)
default_index = slug_options.index(current_slug) if current_slug in scenario_by_slug else 0
chosen_slug = st.selectbox(
    "Practice scenario",
    options=slug_options,
    index=default_index,
    format_func=lambda slug: scenario_by_slug[slug]["title"],
)
situation = scenario_by_slug[chosen_slug]
st.session_state.active_scenario = chosen_slug

history_by_scenario = st.session_state.setdefault("voice_history_by_scenario", {})
conversation_history = history_by_scenario.setdefault(chosen_slug, [])

tab_record, tab_upload = st.tabs(["🎙️ Record a turn", "📁 Upload audio"])
with tab_record:
    recorded_audio = st.audio_input("Record your Kannada reply", key=f"voice_record_{chosen_slug}")
with tab_upload:
    uploaded_audio = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "m4a", "ogg"],
        key=f"voice_upload_{chosen_slug}",
    )

audio_file = recorded_audio or uploaded_audio
if audio_file:
    st.audio(audio_file)

if st.button("Transcribe and get tutor reply", type="primary", disabled=audio_file is None):
    with st.spinner("Transcribing Kannada audio and preparing a tutor reply..."):
        try:
            transcript = transcribe_audio_bytes(audio_file.getvalue(), audio_file.name)
        except (RuntimeError, ValueError) as exc:
            st.error(f"Audio transcription failed: {exc}")
        else:
            if not transcript:
                st.warning("No Kannada speech was recognized. Try recording again with clearer audio.")
                st.stop()
            st.markdown(f"**Recognized speech:** {transcript}")
            try:
                response = generate_tutor_response(
                    mother_tongue=mother_tongue,
                    level=level,
                    scenario_title=situation["title"],
                    ai_role=situation.get("ai_role", "Kannada conversation partner"),
                    system_hint=situation.get("system_hint", ""),
                    conversation_history=conversation_history,
                    user_message=transcript,
                )
            except (RuntimeError, ValueError) as exc:
                st.error(f"Could not generate a tutor reply: {exc}")
            else:
                conversation_history.extend([
                    {"speaker": "user", "message_text": transcript},
                    {"speaker": "assistant", "message_text": response["reply"]},
                ])
                st.session_state.voice_latest_response = {
                    "scenario": chosen_slug,
                    "reply": response["reply"],
                    "transliteration": response.get("transliteration", ""),
                    "translation": response.get("translation", ""),
                }
                record_activity(user_id=user_id, speaking_minutes=1, minutes_spent=2)
                st.rerun()

if conversation_history:
    st.markdown("### Conversation")
    for entry in conversation_history:
        if entry["speaker"] == "user":
            st.markdown(f"**You:** {entry['message_text']}")
        else:
            st.markdown(f"**{situation.get('ai_role', 'Tutor')}:** {entry['message_text']}")

latest = st.session_state.get("voice_latest_response")
if latest and latest.get("scenario") == chosen_slug:
    if latest.get("transliteration"):
        st.caption(latest["transliteration"])
    if latest.get("translation"):
        st.write(f"**Meaning:** {latest['translation']}")

    # Browser speech synthesis reads Kannada aloud without sending audio or keys to a third party.
    encoded_reply = base64.b64encode(latest["reply"].encode("utf-8")).decode("ascii")
    components.html(
        f"""
        <button style="padding:0.55rem 0.9rem; border:0; border-radius:0.5rem;
                       background:#2e7d32; color:white; cursor:pointer;"
                onclick="speakKannada()">🔊 Listen to Kannada reply</button>
        <script>
          const replyBase64 = "{encoded_reply}";
          function speakKannada() {{
            const bytes = Uint8Array.from(atob(replyBase64), c => c.charCodeAt(0));
            const text = new TextDecoder().decode(bytes);
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = "kn-IN";
            utterance.rate = 0.85;
            const voice = speechSynthesis.getVoices().find(v => v.lang.toLowerCase().startsWith("kn"));
            if (voice) utterance.voice = voice;
            speechSynthesis.cancel();
            speechSynthesis.speak(utterance);
          }}
        </script>
        """,
        height=58,
    )

st.caption(
    f"Text model: {Config.HF_TEXT_MODEL}. "
    f"Audio model: {Config.HF_WHISPER_MODEL}."
)
