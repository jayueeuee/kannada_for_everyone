"""
Assessments and Evaluation History Repository.
"""
import json
from typing import Optional, List, Dict, Any
from db import get_db_cursor
from utils.date_time import utc_now


def save_assessment(
    user_id: int,
    assessment_type: str,
    score: float,
    max_score: float = 100.0,
    feedback_data: Optional[Dict[str, Any]] = None,
    lesson_id: Optional[int] = None,
    session_id: Optional[int] = None
) -> int:
    """Saves an assessment result."""
    fb_json = json.dumps(feedback_data, ensure_ascii=False) if feedback_data else None
    valid_type = assessment_type if assessment_type in ('lesson_quiz', 'vocab_recall', 'conversation', 'speaking', 'pronunciation') else 'lesson_quiz'

    sql = """
    INSERT INTO `assessments` (
      `user_id`, `lesson_id`, `session_id`, `assessment_type`, `score`, `max_score`, `feedback_json`, `created_at`
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (
            user_id,
            lesson_id,
            session_id,
            valid_type,
            score,
            max_score,
            fb_json,
            utc_now()
        ))
        return cursor.lastrowid


def get_user_assessments(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves recent assessments for a user."""
    sql = """
    SELECT a.*, l.title AS lesson_title
    FROM `assessments` a
    LEFT JOIN `lessons` l ON a.lesson_id = l.id
    WHERE a.user_id = %s
    ORDER BY a.created_at DESC
    LIMIT %s
    """
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id, limit))
        rows = cursor.fetchall()
        for r in rows:
            if isinstance(r.get("feedback_json"), str):
                try:
                    r["feedback_json"] = json.loads(r["feedback_json"])
                except Exception:
                    r["feedback_json"] = {}
        return rows


def save_pronunciation_assessment(
    user_id: int,
    target_text: str,
    recognized_text: str,
    similarity_score: float,
    feedback_data: Optional[Dict[str, Any]] = None,
    vocabulary_id: Optional[int] = None
) -> int:
    """Saves a pronunciation transcript comparison assessment."""
    fb_dict = feedback_data or {}
    fb_dict["similarity_score"] = similarity_score
    fb_json = json.dumps(fb_dict, ensure_ascii=False)

    sql = """
    INSERT INTO `pronunciation_assessments` (
      `user_id`, `vocabulary_id`, `target_text`, `recognized_text`, `assessment_method`, `feedback_json`, `created_at`
    )
    VALUES (%s, %s, %s, %s, 'transcript_comparison', %s, %s)
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (
            user_id,
            vocabulary_id,
            target_text,
            recognized_text,
            fb_json,
            utc_now()
        ))
        return cursor.lastrowid
