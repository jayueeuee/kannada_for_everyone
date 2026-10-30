"""
Learner Daily Activity and Progress Metrics Repository.
"""
from datetime import date
from typing import List, Dict, Any
from db import get_db_cursor
from utils.date_time import get_local_date, utc_now


def record_activity(
    user_id: int,
    activity_date: date | None = None,
    minutes_spent: int = 0,
    lessons_completed: int = 0,
    words_reviewed: int = 0,
    conversations_completed: int = 0,
    speaking_minutes: int = 0
) -> bool:
    """Updates or inserts daily learning activity for the user."""
    act_date = activity_date if activity_date is not None else get_local_date()
    now = utc_now()

    sql = """
    INSERT INTO `daily_activity` (
      `user_id`, `activity_date`, `minutes_spent`, `lessons_completed`, `words_reviewed`,
      `conversations_completed`, `speaking_minutes`, `created_at`, `updated_at`
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      `minutes_spent` = `minutes_spent` + VALUES(`minutes_spent`),
      `lessons_completed` = `lessons_completed` + VALUES(`lessons_completed`),
      `words_reviewed` = `words_reviewed` + VALUES(`words_reviewed`),
      `conversations_completed` = `conversations_completed` + VALUES(`conversations_completed`),
      `speaking_minutes` = `speaking_minutes` + VALUES(`speaking_minutes`),
      `updated_at` = VALUES(`updated_at`);
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (
            user_id,
            act_date,
            minutes_spent,
            lessons_completed,
            words_reviewed,
            conversations_completed,
            speaking_minutes,
            now,
            now
        ))
        return True


def get_user_daily_activities(user_id: int, limit_days: int = 30) -> List[Dict[str, Any]]:
    """Retrieves recent daily activity logs for a user."""
    sql = """
    SELECT * FROM `daily_activity`
    WHERE `user_id` = %s
    ORDER BY `activity_date` DESC
    LIMIT %s
    """
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id, limit_days))
        return cursor.fetchall()


def get_active_dates(user_id: int) -> List[date]:
    """Retrieves all distinct dates where the user had qualifying learning activity."""
    sql = """
    SELECT `activity_date` FROM `daily_activity`
    WHERE `user_id` = %s AND (
      `minutes_spent` > 0 OR `lessons_completed` > 0 OR `words_reviewed` > 0 OR `conversations_completed` > 0
    )
    ORDER BY `activity_date` DESC
    """
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        return [r["activity_date"] for r in rows]
