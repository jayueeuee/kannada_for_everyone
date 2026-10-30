"""
Vocabulary Library and Spaced Repetition Repository.
"""
from datetime import datetime
import json
from typing import Optional, List, Dict, Any
from db import get_db_cursor
from utils.date_time import utc_now


def get_vocabulary_list(
    category: Optional[str] = None,
    level: Optional[int] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves vocabulary items with optional category, level, or text search."""
    conditions = []
    params = []

    if category and category != "All":
        conditions.append("`category` = %s")
        params.append(category)
    if level is not None:
        conditions.append("`level` = %s")
        params.append(level)
    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append("(`kannada_text` LIKE %s OR `transliteration` LIKE %s OR `english_meaning` LIKE %s OR `hindi_meaning` LIKE %s OR `marathi_meaning` LIKE %s)")
        params.extend([term, term, term, term, term])

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"SELECT * FROM `vocabulary` {where_clause} ORDER BY `level` ASC, `category` ASC, `id` ASC"

    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        for r in rows:
            if isinstance(r.get("example_translation_json"), str):
                try:
                    r["example_translation"] = json.loads(r["example_translation_json"])
                except Exception:
                    r["example_translation"] = {}
        return rows


def get_vocabulary_by_id(vocab_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single vocabulary word by ID."""
    sql = "SELECT * FROM `vocabulary` WHERE `id` = %s LIMIT 1"
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (vocab_id,))
        row = cursor.fetchone()
        if row and isinstance(row.get("example_translation_json"), str):
            try:
                row["example_translation"] = json.loads(row["example_translation_json"])
            except Exception:
                row["example_translation"] = {}
        return row


def save_user_vocabulary(user_id: int, vocabulary_id: int) -> int:
    """Adds a word to user's personal saved vocabulary (idempotent)."""
    sql = """
    INSERT INTO `user_vocabulary` (
      `user_id`, `vocabulary_id`, `ease_factor`, `interval_days`, `repetitions`, `next_review_at`, `mastery_status`
    )
    VALUES (%s, %s, 2.5, 0, 0, %s, 'learning')
    ON DUPLICATE KEY UPDATE `updated_at` = %s
    """
    now = utc_now()
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (user_id, vocabulary_id, now, now))
        return cursor.lastrowid


def remove_user_vocabulary(user_id: int, vocabulary_id: int) -> bool:
    """Removes a saved word from the user's personal deck."""
    sql = "DELETE FROM `user_vocabulary` WHERE `user_id` = %s AND `vocabulary_id` = %s"
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (user_id, vocabulary_id))
        return cursor.rowcount > 0


def get_user_saved_vocabulary(user_id: int) -> List[Dict[str, Any]]:
    """Retrieves all words saved by the user with SRS parameters."""
    sql = """
    SELECT uv.*, v.kannada_text, v.transliteration, v.english_meaning, v.hindi_meaning, v.marathi_meaning,
           v.example_kannada, v.example_transliteration, v.example_translation_json, v.category, v.level
    FROM `user_vocabulary` uv
    JOIN `vocabulary` v ON uv.vocabulary_id = v.id
    WHERE uv.user_id = %s
    ORDER BY uv.next_review_at ASC
    """
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        for r in rows:
            if isinstance(r.get("example_translation_json"), str):
                try:
                    r["example_translation"] = json.loads(r["example_translation_json"])
                except Exception:
                    r["example_translation"] = {}
        return rows


def get_due_user_vocabulary(user_id: int, before_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Retrieves saved vocabulary that is currently due for review."""
    ref_time = before_time if before_time is not None else utc_now()
    sql = """
    SELECT uv.*, v.kannada_text, v.transliteration, v.english_meaning, v.hindi_meaning, v.marathi_meaning,
           v.example_kannada, v.example_transliteration, v.example_translation_json, v.category, v.level
    FROM `user_vocabulary` uv
    JOIN `vocabulary` v ON uv.vocabulary_id = v.id
    WHERE uv.user_id = %s AND uv.next_review_at <= %s
    ORDER BY uv.next_review_at ASC
    """
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id, ref_time))
        rows = cursor.fetchall()
        for r in rows:
            if isinstance(r.get("example_translation_json"), str):
                try:
                    r["example_translation"] = json.loads(r["example_translation_json"])
                except Exception:
                    r["example_translation"] = {}
        return rows


def update_user_vocab_srs(
    user_vocab_id: int,
    user_id: int,
    ease_factor: float,
    interval_days: int,
    repetitions: int,
    last_rating: str,
    next_review_at: datetime,
    mastery_status: str
) -> bool:
    """Updates SRS schedule for a user vocabulary record, enforcing ownership."""
    sql = """
    UPDATE `user_vocabulary`
    SET `ease_factor` = %s,
        `interval_days` = %s,
        `repetitions` = %s,
        `last_rating` = %s,
        `last_reviewed_at` = %s,
        `next_review_at` = %s,
        `mastery_status` = %s,
        `updated_at` = %s
    WHERE `id` = %s AND `user_id` = %s
    """
    now = utc_now()
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (
            ease_factor,
            interval_days,
            repetitions,
            last_rating,
            now,
            next_review_at,
            mastery_status,
            now,
            user_vocab_id,
            user_id
        ))
        return cursor.rowcount > 0


def record_review_history(user_vocab_id: int, rating: str, previous_interval_days: int, new_interval_days: int) -> int:
    """Inserts an immutable review attempt record."""
    sql = """
    INSERT INTO `vocabulary_review_history` (`user_vocabulary_id`, `rating`, `previous_interval_days`, `new_interval_days`, `reviewed_at`)
    VALUES (%s, %s, %s, %s, %s)
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (user_vocab_id, rating, previous_interval_days, new_interval_days, utc_now()))
        return cursor.lastrowid
