"""
Conversation Sessions and Messages Repository.
Persists text and voice conversation history, ensuring user ownership.
"""
import json
from typing import Optional, List, Dict, Any
from db import get_db_cursor
from utils.date_time import utc_now


def create_session(user_id: int, situation_id: Optional[int] = None, mode: str = "text") -> int:
    """Creates a new tutoring session."""
    sql = """
    INSERT INTO `conversation_sessions` (`user_id`, `situation_id`, `mode`, `started_at`, `status`)
    VALUES (%s, %s, %s, %s, 'active')
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (user_id, situation_id, mode, utc_now()))
        return cursor.lastrowid


def get_session(session_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a conversation session enforcing user ownership."""
    sql = """
    SELECT cs.*, s.title AS situation_title, s.slug AS situation_slug, s.ai_role, s.system_hint
    FROM `conversation_sessions` cs
    LEFT JOIN `situations` s ON cs.situation_id = s.id
    WHERE cs.id = %s AND cs.user_id = %s
    LIMIT 1
    """
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (session_id, user_id))
        return cursor.fetchone()


def update_session_status(
    session_id: int,
    user_id: int,
    status: str = "completed",
    summary: Optional[str] = None,
    assessment_data: Optional[Dict[str, Any]] = None
) -> bool:
    """Updates session status, summary, and assessment."""
    assess_json = json.dumps(assessment_data, ensure_ascii=False) if assessment_data else None
    sql = """
    UPDATE `conversation_sessions`
    SET `status` = %s, `ended_at` = %s, `summary` = %s, `assessment_json` = %s
    WHERE `id` = %s AND `user_id` = %s
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (status, utc_now(), summary, assess_json, session_id, user_id))
        return cursor.rowcount > 0


def add_message(
    session_id: int,
    speaker: str,
    message_text: str,
    transliteration: Optional[str] = None,
    translation: Optional[str] = None,
    feedback_data: Optional[Dict[str, Any]] = None
) -> int:
    """Appends a new message to a conversation session."""
    fb_json = json.dumps(feedback_data, ensure_ascii=False) if feedback_data else None
    sql = """
    INSERT INTO `conversation_messages` (
      `session_id`, `speaker`, `message_text`, `transliteration`, `translation`, `feedback_json`, `created_at`
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (session_id, speaker, message_text, transliteration, translation, fb_json, utc_now()))
        return cursor.lastrowid


def get_session_messages(session_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves messages in chronological order for a session."""
    sql = """
    SELECT `id`, `session_id`, `speaker`, `message_text`, `transliteration`, `translation`, `feedback_json`, `created_at`
    FROM `conversation_messages`
    WHERE `session_id` = %s
    ORDER BY `created_at` ASC, `id` ASC
    LIMIT %s
    """
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (session_id, limit))
        rows = cursor.fetchall()
        for r in rows:
            if isinstance(r.get("feedback_json"), str):
                try:
                    r["feedback_json"] = json.loads(r["feedback_json"])
                except Exception:
                    r["feedback_json"] = {}
        return rows


def get_user_recent_sessions(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves recent conversation sessions for a user."""
    sql = """
    SELECT cs.*, s.title AS situation_title, s.slug AS situation_slug
    FROM `conversation_sessions` cs
    LEFT JOIN `situations` s ON cs.situation_id = s.id
    WHERE cs.user_id = %s
    ORDER BY cs.started_at DESC
    LIMIT %s
    """
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id, limit))
        return cursor.fetchall()
