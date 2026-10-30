"""
Page 7: Structured Guided Learning Path.
Interactive multi-level curriculum with quizzes, deterministic scoring, and progression unlocking.
"""
import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.lesson_service import get_user_learning_path, grade_lesson_quiz
from services.vocabulary_service import save_word_for_user
from repositories.vocabulary import get_vocabulary_list

st.set_page_config(page_title="Guided Lessons — Kannada for Everyone", page_icon="📚", layout="wide")

css_file = PROJECT_ROOT / "static" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if not st.session_state.get("authenticated") or not st.session_state.get("user"):
    st.warning("Please log in to access guided lessons.")
    if st.button("Log In"):
        st.switch_page("pages/1_Login.py")
    st.stop()

user = st.session_state.user
user_id = user["id"]
mother_tongue = user.get("mother_tongue", "en")

st.markdown("## 📚 Structured Kannada Learning Path")
st.caption("Master spoken Kannada step-by-step from foundational words to fluent social conversation.")

lessons = get_user_learning_path(user_id)
if not lessons:
    st.error("No lessons found. Please run `python init_db.py` to initialize curriculum.")
    st.stop()

# Determine active lesson
selected_slug = st.session_state.get("selected_lesson_slug")
active_lesson = next((l for l in lessons if l["slug"] == selected_slug), None)
if not active_lesson:
    active_lesson = lessons[0]

# Lesson Selection Bar
col_sel, col_info = st.columns([3, 1])
with col_sel:
    lesson_titles = {
        l["slug"]: f"{'✅' if l['is_completed'] else ('🔓' if l['is_unlocked'] else '🔒')} Level {l['level']}.{l['lesson_order']} — {l['title']}"
        for l in lessons
    }
    chosen_slug = st.selectbox(
        "Choose a Lesson:",
        options=list(lesson_titles.keys()),
        format_func=lambda x: lesson_titles[x],
        index=list(lesson_titles.keys()).index(active_lesson["slug"])
    )
    if chosen_slug != active_lesson["slug"]:
        active_lesson = next(l for l in lessons if l["slug"] == chosen_slug)
        st.session_state.selected_lesson_slug = chosen_slug

with col_info:
    status_text = "Completed ✅" if active_lesson["is_completed"] else ("Unlocked 🔓" if active_lesson["is_unlocked"] else "Locked 🔒")
    st.markdown(f"""
    <div style="padding: 10px; background: #ffffff; border: 1px solid #ddd; border-radius: 8px; text-align: center;">
      <div style="font-weight: 700; color: #1b5e20;">{status_text}</div>
      <div style="font-size: 0.8rem; color: #666;">Best Score: {active_lesson['best_score']}% ({active_lesson['attempt_count']} attempts)</div>
    </div>
    """, unsafe_allow_html=True)

if not active_lesson["is_unlocked"] and not active_lesson["is_completed"]:
    st.warning("🔒 This lesson is currently locked. Complete the preceding lessons with a passing score to unlock it.")
    st.stop()

content = active_lesson.get("content", {})

# Tabs: 1. Study & Vocabulary, 2. Interactive Quiz & Practice
tab_study, tab_quiz = st.tabs(["📖 Lesson Content & Vocabulary", "✍️ Interactive Quiz & Exercises"])

with tab_study:
    st.markdown(f"### 🎯 Learning Objective")
    st.info(content.get("objective", active_lesson["description"]))

    # Vocabulary section
    st.markdown("### 🔤 Key Vocabulary & Phrases")
    vocab_items = content.get("vocabulary", [])
    if vocab_items:
        v_cols = st.columns(2)
        for idx, item in enumerate(vocab_items):
            with v_cols[idx % 2]:
                meaning_key = mother_tongue if mother_tongue in item else "english"
                meaning_text = item.get(meaning_key, item.get("english", ""))
                st.markdown(f"""
                <div class="kfe-card" style="margin-bottom: 10px;">
                  <div class="kannada-text">{item.get('kannada')}</div>
                  <div class="translit-text">{item.get('transliteration')}</div>
                  <div class="meaning-text"><b>Meaning:</b> {meaning_text}</div>
                  <div style="font-size: 0.85rem; color: #555; margin-top: 4px;"><i>{item.get('example', '')}</i></div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"➕ Save to My Vocabulary", key=f"save_v_{active_lesson['id']}_{idx}"):
                    lib_match = get_vocabulary_list(search=item.get("kannada"))
                    if lib_match:
                        save_word_for_user(user_id, lib_match[0]["id"])
                        st.toast(f"Saved '{item.get('kannada')}'!")

    # Grammar notes
    grammar = content.get("grammar_notes", {})
    if grammar:
        st.markdown("### 💡 Grammar & Usage Tips")
        note = grammar.get(mother_tongue, grammar.get("en", ""))
        st.markdown(f"""
        <div class="kfe-panel-green">
          {note}
        </div>
        """, unsafe_allow_html=True)

with tab_quiz:
    st.markdown(f"### 📝 Practice Quiz (Pass Score: {active_lesson['pass_score']}%)")
    exercises = content.get("exercises", [])

    with st.form(f"quiz_form_{active_lesson['id']}"):
        user_answers = {}

        for ex in exercises:
            ex_id = ex["id"]
            ex_type = ex["type"]

            st.markdown(f"**{ex.get('question', ex.get('prompt', 'Question'))}**")

            if ex_type == "matching":
                pairs = ex.get("pairs", [])
                match_results = {}
                m_cols = st.columns(len(pairs))
                all_targets = [p["match"] for p in pairs]
                for p_idx, p in enumerate(pairs):
                    with m_cols[p_idx]:
                        sel = st.selectbox(
                            f"{p['kannada']}",
                            options=all_targets,
                            key=f"m_{ex_id}_{p_idx}"
                        )
                        match_results[p["kannada"]] = sel
                user_answers[ex_id] = match_results

            elif ex_type in ("fill_blank", "translation"):
                options = ex.get("options", [])
                chosen = st.radio(
                    "Select correct answer:",
                    options=options,
                    key=f"opt_{ex_id}",
                    label_visibility="collapsed"
                )
                user_answers[ex_id] = chosen

            elif ex_type == "role_play":
                ans_text = st.text_input(
                    "Your response in Kannada:",
                    key=f"rp_{ex_id}",
                    placeholder="Type what you would say..."
                )
                user_answers[ex_id] = ans_text

            st.markdown("---")

        submit_quiz = st.form_submit_button("Submit Quiz for Evaluation", type="primary", use_container_width=True)

    if submit_quiz:
        grade_res = grade_lesson_quiz(
            user_id=user_id,
            lesson_id=active_lesson["id"],
            submitted_answers=user_answers
        )

        score = grade_res["score"]
        passed = grade_res["passed"]

        if passed:
            st.success(f"🎉 Congratulations! You passed with a score of {score}% ({grade_res['correct_count']}/{grade_res['total_exercises']} correct).")
            st.balloons()
        else:
            st.error(f"Score: {score}%. Passing score is {grade_res['pass_score']}%. Please review the answers below and try again!")

        st.markdown("#### 📋 Detailed Answer Review")
        for res in grade_res["results"]:
            icon = "✅" if res["is_correct"] else "❌"
            st.markdown(f"- {icon} Exercise `{res['id']}`: {res['explanation']}")
