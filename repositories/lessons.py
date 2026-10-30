"""
Lessons and User Progress Repository.
"""
import json
from typing import Optional, List, Dict, Any
from db import get_db_cursor
from utils.date_time import utc_now


def get_all_lessons(level: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves active lessons, optionally filtered by level."""
    if level is not None:
        sql = """
        SELECT `id`, `slug`, `title`, `description`, `level`, `lesson_order`, `estimated_minutes`, `content_json`, `pass_score`
        FROM `lessons`
        WHERE `is_active` = TRUE AND `level` = %s
        ORDER BY `lesson_order` ASC
        """
        params = (level,)
    else:
        sql = """
        SELECT `id`, `slug`, `title`, `description`, `level`, `lesson_order`, `estimated_minutes`, `content_json`, `pass_score`
        FROM `lessons`
        WHERE `is_active` = TRUE
        ORDER BY `level` ASC, `lesson_order` ASC
        """
        params = ()

    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        for r in rows:
            if isinstance(r.get("content_json"), str):
                try:
                    r["content_json"] = json.loads(r["content_json"])
                except Exception:
                    r["content_json"] = {}
        return rows


def get_lesson_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Retrieves a lesson by slug."""
    sql = "SELECT * FROM `lessons` WHERE `slug` = %s AND `is_active` = TRUE LIMIT 1"
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (slug,))
        row = cursor.fetchone()
        if row and isinstance(row.get("content_json"), str):
            try:
                row["content_json"] = json.loads(row["content_json"])
            except Exception:
                row["content_json"] = {}
        return row


def get_lesson_by_id(lesson_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a lesson by ID."""
    sql = "SELECT * FROM `lessons` WHERE `id` = %s AND `is_active` = TRUE LIMIT 1"
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (lesson_id,))
        row = cursor.fetchone()
        if row and isinstance(row.get("content_json"), str):
            try:
                row["content_json"] = json.loads(row["content_json"])
            except Exception:
                row["content_json"] = {}
        return row


def get_user_lesson_progress(user_id: int, lesson_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves user's progress record for a lesson."""
    sql = "SELECT * FROM `user_lesson_progress` WHERE `user_id` = %s AND `lesson_id` = %s LIMIT 1"
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id, lesson_id))
        return cursor.fetchone()


def get_all_user_progress(user_id: int) -> List[Dict[str, Any]]:
    """Retrieves all lesson progress records for a user."""
    sql = """
    SELECT ulp.*, l.slug, l.title, l.level, l.lesson_order, l.pass_score
    FROM `user_lesson_progress` ulp
    JOIN `lessons` l ON ulp.lesson_id = l.id
    WHERE ulp.user_id = %s
    ORDER BY l.level ASC, l.lesson_order ASC
    """
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id,))
        return cursor.fetchall()


def save_lesson_progress(user_id: int, lesson_id: int, status: str, score: float, is_pass: bool) -> bool:
    """Updates or inserts a lesson completion/attempt record."""
    now = utc_now()
    completed_at = now if is_pass else None

    sql = """
    INSERT INTO `user_lesson_progress` (
      `user_id`, `lesson_id`, `status`, `attempt_count`, `best_score`, `last_score`, `started_at`, `completed_at`, `updated_at`
    )
    VALUES (%s, %s, %s, 1, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      `attempt_count` = `attempt_count` + 1,
      `last_score` = VALUES(`last_score`),
      `best_score` = GREATEST(`best_score`, VALUES(`best_score`)),
      `status` = IF(VALUES(`status`) = 'completed' OR `status` = 'completed', 'completed', VALUES(`status`)),
      `completed_at` = IF(`completed_at` IS NOT NULL, `completed_at`, VALUES(`completed_at`)),
      `updated_at` = VALUES(`updated_at`);
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (
            user_id,
            lesson_id,
            status,
            score,
            score,
            now,
            completed_at,
            now
        ))
        return True
