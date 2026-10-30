"""
Assessment Service.
Handles quiz assessments, conversational speaking evaluations, and pronunciation tracking.
"""
from typing import Dict, Any, List, Optional
from repositories.assessments import (
    save_assessment,
    get_user_assessments,
    save_pronunciation_assessment
)


def record_quiz_assessment(user_id: int, lesson_id: int, score: float, feedback_data: Dict[str, Any]) -> int:
    """Saves a lesson quiz result."""
    return save_assessment(
        user_id=user_id,
        lesson_id=lesson_id,
        assessment_type="lesson_quiz",
        score=score,
        max_score=100.0,
        feedback_data=feedback_data
    )


def record_conversation_assessment(user_id: int, session_id: int, score: float, feedback_data: Dict[str, Any]) -> int:
    """Saves a conversation role-play assessment."""
    return save_assessment(
        user_id=user_id,
        session_id=session_id,
        assessment_type="conversation",
        score=score,
        max_score=100.0,
        feedback_data=feedback_data
    )


def record_pronunciation_attempt(
    user_id: int,
    target_text: str,
    recognized_text: str,
    similarity_score: float,
    feedback_data: Dict[str, Any],
    vocabulary_id: Optional[int] = None
) -> int:
    """Saves a pronunciation transcript comparison record."""
    return save_pronunciation_assessment(
        user_id=user_id,
        target_text=target_text,
        recognized_text=recognized_text,
        similarity_score=similarity_score,
        feedback_data=feedback_data,
        vocabulary_id=vocabulary_id
    )


def get_learner_assessments(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves learner assessment history."""
    return get_user_assessments(user_id=user_id, limit=limit)
