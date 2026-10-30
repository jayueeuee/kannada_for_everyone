"""
Learner Progress Analytics and Streak Calculation Service.
Calculates authentic metrics directly from MySQL records without fabricated numbers.
"""
from datetime import date
from typing import Dict, Any, List
from repositories.progress import get_active_dates, get_user_daily_activities
from repositories.lessons import get_all_lessons, get_all_user_progress
from repositories.vocabulary import get_user_saved_vocabulary, get_due_user_vocabulary
from repositories.conversations import get_user_recent_sessions
from repositories.assessments import get_user_assessments
from utils.date_time import calculate_streak, get_local_date


def get_learner_dashboard_metrics(user_id: int) -> Dict[str, Any]:
    """
    Computes all personalized dashboard statistics from MySQL database records.
    """
    today = get_local_date()

    # 1. Active dates & Streak calculation
    active_dates = get_active_dates(user_id)
    current_streak = calculate_streak(active_dates, reference_date=today)

    # 2. Daily activity for today
    recent_activities = get_user_daily_activities(user_id, limit_days=30)
    today_activity = next((a for a in recent_activities if a.get("activity_date") == today), None)

    minutes_today = today_activity["minutes_spent"] if today_activity else 0
    speaking_today = today_activity["speaking_minutes"] if today_activity else 0

    # 3. Lesson completion & progress
    all_lessons = get_all_lessons()
    total_lessons_count = len(all_lessons)
    user_progress = get_all_user_progress(user_id)
    completed_progress = [p for p in user_progress if p.get("status") == "completed"]
    completed_lessons_count = len(completed_progress)

    completion_pct = round((completed_lessons_count / total_lessons_count) * 100, 1) if total_lessons_count > 0 else 0.0

    # Determine recommended next lesson
    completed_ids = {p["lesson_id"] for p in completed_progress}
    next_lesson = None
    for les in all_lessons:
        if les["id"] not in completed_ids:
            next_lesson = les
            break
    if not next_lesson and all_lessons:
        next_lesson = all_lessons[0]  # If all completed, recommend lesson 1 for review

    # 4. Vocabulary statistics
    saved_vocab = get_user_saved_vocabulary(user_id)
    due_vocab = get_due_user_vocabulary(user_id)

    # 5. Conversation sessions
    recent_sessions = get_user_recent_sessions(user_id, limit=5)
    total_convs_completed = sum(1 for s in recent_sessions if s.get("status") == "completed")

    # 6. Recent assessments
    recent_assessments = get_user_assessments(user_id, limit=5)

    return {
        "streak_days": current_streak,
        "minutes_today": minutes_today,
        "speaking_minutes_today": speaking_today,
        "lessons_completed": completed_lessons_count,
        "total_lessons": total_lessons_count,
        "completion_percentage": completion_pct,
        "next_lesson": next_lesson,
        "words_saved": len(saved_vocab),
        "words_due": len(due_vocab),
        "conversations_count": len(recent_sessions),
        "recent_sessions": recent_sessions,
        "recent_assessments": recent_assessments,
        "daily_history": recent_activities
    }
