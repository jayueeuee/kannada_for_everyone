"""
User Mistakes and Corrections Repository.
Deduplicates mistakes using normalized keys and tracks frequency and resolution.
"""
import re
from typing import Optional, List, Dict, Any
from db import get_db_cursor
from utils.date_time import utc_now


def _generate_normalized_key(original: str, suggested: str) -> str:
    """Generates a consistent normalized key for deduplication."""
    clean_orig = re.sub(r'\s+', ' ', original.strip().lower())
    clean_sugg = re.sub(r'\s+', ' ', suggested.strip().lower())
    combined = f"{clean_orig}::{clean_sugg}"
    return combined[:250]


def record_or_increment_mistake(
    user_id: int,
    mistake_type: str,
    original_text: str,
    suggested_text: str,
    explanation: Optional[str] = None
) -> int:
    """Inserts a new mistake or increments occurrence_count if seen before."""
    norm_key = _generate_normalized_key(original_text, suggested_text)
    now = utc_now()
    valid_type = mistake_type if mistake_type in ('grammar', 'vocabulary', 'word_order', 'sentence_construction', 'pronunciation') else 'other'

    sql = """
    INSERT INTO `user_mistakes` (
      `user_id`, `mistake_type`, `original_text`, `suggested_text`, `explanation`,
      `normalized_key`, `occurrence_count`, `first_seen_at`, `last_seen_at`, `is_resolved`
    )
    VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s, FALSE)
    ON DUPLICATE KEY UPDATE
      `occurrence_count` = `occurrence_count` + 1,
      `last_seen_at` = VALUES(`last_seen_at`),
      `explanation` = IF(VALUES(`explanation`) IS NOT NULL AND VALUES(`explanation`) != '', VALUES(`explanation`), `explanation`),
      `is_resolved` = FALSE;
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (
            user_id,
            valid_type,
            original_text,
            suggested_text,
            explanation,
            norm_key,
            now,
            now
        ))
        return cursor.lastrowid


def get_user_mistakes(user_id: int, unresolved_only: bool = False) -> List[Dict[str, Any]]:
    """Retrieves mistakes for a user, sorted by last occurrence."""
    if unresolved_only:
        sql = "SELECT * FROM `user_mistakes` WHERE `user_id` = %s AND `is_resolved` = FALSE ORDER BY `last_seen_at` DESC"
    else:
        sql = "SELECT * FROM `user_mistakes` WHERE `user_id` = %s ORDER BY `is_resolved` ASC, `last_seen_at` DESC"

    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id,))
        return cursor.fetchall()


def resolve_mistake(user_id: int, mistake_id: int) -> bool:
    """Marks a mistake as resolved by the learner."""
    sql = "UPDATE `user_mistakes` SET `is_resolved` = TRUE WHERE `id` = %s AND `user_id` = %s"
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (mistake_id, user_id))
        return cursor.rowcount > 0
