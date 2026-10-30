"""
Page 8: Vocabulary Library & Spaced Repetition (SRS).
Browse words, save to personal decks, and review due words with SM-2 intervals.
"""
import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.vocabulary_service import (
    list_vocabulary,
    save_word_for_user,
    remove_word_for_user,
    get_user_vocabulary_stats,
    process_word_review
)

st.set_page_config(page_title="Vocabulary & SRS — Kannada for Everyone", page_icon="📝", layout="wide")

css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if not st.session_state.get("authenticated") or not st.session_state.get("user"):
    st.warning("Please log in to manage your saved vocabulary and spaced repetition reviews.")
    if st.button("Log In"):
        st.switch_page("pages/1_Login.py")
    st.stop()

user = st.session_state.user
user_id = user["id"]
mother_tongue = user.get("mother_tongue", "en")

st.markdown("## 📝 Vocabulary Library & Spaced Repetition")
st.caption("Expand your word bank, save everyday phrases, and build permanent recall with SM-2 memory intervals.")

stats = get_user_vocabulary_stats(user_id)

# Stats header row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Saved Words", stats["total_saved"])
with m2:
    st.metric("Due for Review Today", stats["due_count"], delta=f"{stats['due_count']} due" if stats["due_count"] > 0 else "Up to date")
with m3:
    st.metric("In Learning Phase", stats["learning_count"])
with m4:
    st.metric("Mastered Words", stats["mastered_count"])

st.markdown("---")

tab_review, tab_saved, tab_library = st.tabs([
    f"⏰ Review Due Words ({stats['due_count']})",
    f"⭐ My Saved Words ({stats['total_saved']})",
    "📚 Explore Full Library"
])

# ----------------- TAB 1: SPACED REPETITION REVIEW -----------------
with tab_review:
    due_words = stats["due_words"]
    if not due_words:
        st.success("🎉 You're completely caught up! No words are due for review right now.")
        st.info("Explore the vocabulary library or complete lessons to add more words to your review queue.")
    else:
        st.markdown(f"### Flashcard Review ({len(due_words)} remaining)")

        # Current flashcard index in session state
        if "flashcard_idx" not in st.session_state or st.session_state.flashcard_idx >= len(due_words):
            st.session_state.flashcard_idx = 0
        if "reveal_card" not in st.session_state:
            st.session_state.reveal_card = False

        card = due_words[st.session_state.flashcard_idx]

        # Flashcard Container
        st.markdown(f"""
        <div class="kfe-card" style="text-align: center; padding: 2.5rem 1.5rem; border: 2px solid #2e7d32; background: #ffffff;">
          <span class="kfe-badge">{card.get('category')} • Level {card.get('level')}</span>
          <div class="kannada-large" style="margin: 1.25rem 0 0.5rem 0; font-size: 2.8rem;">{card.get('kannada_text')}</div>
          <div class="translit-text" style="font-size: 1.3rem;">{card.get('transliteration')}</div>
          <div style="color: #666; margin-top: 1rem; font-style: italic;">{card.get('example_kannada', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            if not st.session_state.reveal_card:
                if st.button("👁️ Reveal Meaning", use_container_width=True, type="primary"):
                    st.session_state.reveal_card = True
                    st.rerun()
            else:
                meaning_display = (
                    card.get("marathi_meaning") if mother_tongue == "mr"
                    else (card.get("hindi_meaning") if mother_tongue == "hi" else card.get("english_meaning"))
                )
                st.markdown(f"""
                <div class="kfe-panel-green" style="text-align: center; margin: 10px 0;">
                  <h4 style="margin: 0; color: #1b5e20;">Meaning: {meaning_display}</h4>
                  <div style="font-size: 0.85rem; color: #555; margin-top: 4px;">
                    EN: {card.get('english_meaning')} | HI: {card.get('hindi_meaning')} | MR: {card.get('marathi_meaning')}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("##### How well did you remember this word?")
                r1, r2, r3, r4 = st.columns(4)
                ratings = [
                    (r1, "Again", "Forgot completely\n(Interval: 1d)", "secondary"),
                    (r2, "Hard", "Recalled with difficulty\n(Small interval)", "secondary"),
                    (r3, "Good", "Recalled correctly\n(Normal interval)", "primary"),
                    (r4, "Easy", "Recalled instantly\n(Bonus interval)", "secondary")
                ]

                for col, r_label, help_txt, b_type in ratings:
                    with col:
                        if st.button(f"{r_label}", key=f"rate_{r_label}", help=help_txt, use_container_width=True):
                            process_word_review(
                                user_id=user_id,
                                user_vocab_id=card["id"],
                                current_reps=card.get("repetitions", 0),
                                current_interval=card.get("interval_days", 0),
                                current_ease=card.get("ease_factor", 2.5),
                                rating=r_label
                            )
                            st.session_state.reveal_card = False
                            st.session_state.flashcard_idx += 1
                            st.rerun()

# ----------------- TAB 2: MY SAVED WORDS -----------------
with tab_saved:
    saved_list = stats["saved_words"]
    if not saved_list:
        st.info("You haven't saved any words yet. Explore the library tab to add words!")
    else:
        for w in saved_list:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"""
                <div style="padding: 8px 12px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 8px;">
                  <span class="kfe-badge">{w.get('category')}</span>
                  <span class="kfe-badge kfe-badge-gold">{w.get('mastery_status', 'learning').upper()}</span>
                  <span style="font-size: 0.8rem; color: #757575;">Next Review: {str(w.get('next_review_at'))[:10]}</span>
                  <div class="kannada-text" style="margin-top: 4px;">{w.get('kannada_text')} ({w.get('transliteration')})</div>
                  <div style="font-size: 0.95rem; color: #333;">EN: {w.get('english_meaning')} | HI: {w.get('hindi_meaning')} | MR: {w.get('marathi_meaning')}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button("🗑️ Remove", key=f"del_saved_{w['vocabulary_id']}"):
                    remove_word_for_user(user_id, w["vocabulary_id"])
                    st.rerun()

# ----------------- TAB 3: FULL VOCABULARY LIBRARY -----------------
with tab_library:
    c_srch, c_cat, c_lvl = st.columns([3, 2, 1])
    with c_srch:
        search_query = st.text_input("Search vocabulary (Kannada, English, transliteration)", "")
    with c_cat:
        all_cats = ["All", "Greetings", "Basics", "Food & Dining", "Shopping", "Travel", "Social"]
        cat_choice = st.selectbox("Category", all_cats)
    with c_lvl:
        lvl_choice = st.selectbox("Level", ["All", 1, 2, 3, 4, 5])

    lvl_arg = int(lvl_choice) if lvl_choice != "All" else None
    vocab_results = list_vocabulary(category=cat_choice, level=lvl_arg, search=search_query)

    saved_v_ids = {w["vocabulary_id"] for w in stats["saved_words"]}

    st.caption(f"Showing {len(vocab_results)} vocabulary words:")
    for v in vocab_results:
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"""
            <div style="padding: 10px 14px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 8px;">
              <span class="kfe-badge">{v.get('category')}</span> <span style="font-size: 0.8rem; color: #757575;">Level {v.get('level')}</span>
              <div class="kannada-text">{v.get('kannada_text')} <span class="translit-text">({v.get('transliteration')})</span></div>
              <div style="font-size: 0.95rem; color: #333; margin-top: 2px;">
                <b>Meaning:</b> EN: {v.get('english_meaning')} | HI: {v.get('hindi_meaning')} | MR: {v.get('marathi_meaning')}
              </div>
              <div style="font-size: 0.85rem; color: #666; margin-top: 4px;"><i>{v.get('example_kannada', '')} — {v.get('example_transliteration', '')}</i></div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            is_saved = v["id"] in saved_v_ids
            if is_saved:
                st.button("✓ Saved", key=f"lib_saved_{v['id']}", disabled=True)
            else:
                if st.button("➕ Save", key=f"lib_add_{v['id']}", type="primary"):
                    save_word_for_user(user_id, v["id"])
                    st.rerun()
