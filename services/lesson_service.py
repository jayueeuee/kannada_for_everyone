"""
Lesson Orchestration, Quiz Scoring, and Progression Service.
Evaluates quiz exercises deterministically and applies configurable unlocking rules.
"""
from typing import Dict, Any, List, Tuple
from repositories.lessons import (
    get_all_lessons,
    get_lesson_by_slug,
    get_lesson_by_id,
    get_all_user_progress,
    save_lesson_progress
)
from repositories.progress import record_activity
from repositories.assessments import save_assessment


def get_user_learning_path(user_id: int) -> List[Dict[str, Any]]:
    """
    Returns all lessons with user progress, attempt count, best score, and unlocked status.
    Lesson 1 is unlocked by default; subsequent lessons unlock if previous is completed.
    """
    all_lessons = get_all_lessons()
    user_progress = {p["lesson_id"]: p for p in get_all_user_progress(user_id)}

    annotated = []
    prev_completed = True  # First lesson is unlocked

    for les in all_lessons:
        lid = les["id"]
        prog = user_progress.get(lid, {})
        is_completed = prog.get("status") == "completed"

        is_unlocked = prev_completed

        annotated.append({
            "id": lid,
            "slug": les["slug"],
            "title": les["title"],
            "description": les["description"],
            "level": les["level"],
            "lesson_order": les["lesson_order"],
            "estimated_minutes": les["estimated_minutes"],
            "pass_score": les["pass_score"],
            "is_unlocked": is_unlocked,
            "is_completed": is_completed,
            "attempt_count": prog.get("attempt_count", 0),
            "best_score": prog.get("best_score", 0.0),
            "last_score": prog.get("last_score", 0.0),
            "content": les.get("content_json", {})
        })
        prev_completed = is_completed

    return annotated


def grade_lesson_quiz(
    user_id: int,
    lesson_id: int,
    submitted_answers: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Grades submitted quiz answers deterministically against lesson content.
    Persists progress and daily activity.
    """
    lesson = get_lesson_by_id(lesson_id)
    if not lesson:
        raise ValueError("Lesson not found.")

    content = lesson.get("content_json", {})
    exercises = content.get("exercises", [])

    total_exercises = len(exercises)
    if total_exercises == 0:
        return {
            "score": 100.0,
            "passed": True,
            "results": [],
            "feedback": "Lesson reviewed."
        }

    correct_count = 0
    results = []

    for ex in exercises:
        ex_id = ex.get("id")
        ex_type = ex.get("type")
        user_val = submitted_answers.get(ex_id)
        is_correct = False
        explanation = ex.get("explanation", "")

        if ex_type == "matching":
            pairs = ex.get("pairs", [])
            # user_val is expected to be dict of {kannada: match}
            if isinstance(user_val, dict):
                match_correct = True
                for p in pairs:
                    if user_val.get(p["kannada"]) != p["match"]:
                        match_correct = False
                        break
                is_correct = match_correct
        elif ex_type in ("fill_blank", "translation"):
            correct_ans = ex.get("correct_answer", "").strip().lower()
            if isinstance(user_val, str) and user_val.strip().lower() == correct_ans:
                is_correct = True
        elif ex_type == "role_play":
            # For role-play, any thoughtful response is marked valid with feedback
            if user_val and len(str(user_val).strip()) > 1:
                is_correct = True

        if is_correct:
            correct_count += 1

        results.append({
            "id": ex_id,
            "type": ex_type,
            "is_correct": is_correct,
            "user_answer": user_val,
            "explanation": explanation
        })

    score = round((correct_count / total_exercises) * 100.0, 1)
    pass_score = float(lesson.get("pass_score", 70))
    passed = score >= pass_score

    # Save to user_lesson_progress
    status = "completed" if passed else "in_progress"
    save_lesson_progress(
        user_id=user_id,
        lesson_id=lesson_id,
        status=status,
        score=score,
        is_pass=passed
    )

    # Save assessment record
    save_assessment(
        user_id=user_id,
        assessment_type="lesson_quiz",
        score=score,
        max_score=100.0,
        feedback_data={"results": results, "passed": passed},
        lesson_id=lesson_id
    )

    # Record daily activity
    record_activity(
        user_id=user_id,
        minutes_spent=lesson.get("estimated_minutes", 10),
        lessons_completed=1 if passed else 0
    )

    return {
        "score": score,
        "pass_score": pass_score,
        "passed": passed,
        "correct_count": correct_count,
        "total_exercises": total_exercises,
        "results": results
    }
