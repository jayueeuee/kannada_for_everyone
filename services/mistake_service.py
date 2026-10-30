"""
Learner Mistake Tracking and Correction History Service.
"""
from typing import List, Dict, Any, Optional
from repositories.mistakes import (
    record_or_increment_mistake,
    get_user_mistakes,
    resolve_mistake
)


def log_mistake_from_ai(
    user_id: int,
    original_text: str,
    suggested_text: str,
    explanation: Optional[str] = None,
    mistake_type: Optional[str] = None
) -> Optional[int]:
    """Records an AI-identified mistake with deduplication."""
    if not original_text or not suggested_text:
        return None
    if original_text.strip().lower() == suggested_text.strip().lower():
        return None

    clean_type = mistake_type or "grammar"
    return record_or_increment_mistake(
        user_id=user_id,
        mistake_type=clean_type,
        original_text=original_text.strip(),
        suggested_text=suggested_text.strip(),
        explanation=explanation
    )


def get_learner_mistakes(user_id: int, unresolved_only: bool = False) -> List[Dict[str, Any]]:
    """Fetches mistake records for a learner."""
    return get_user_mistakes(user_id=user_id, unresolved_only=unresolved_only)


def mark_mistake_resolved(user_id: int, mistake_id: int) -> bool:
    """Marks a mistake as understood/resolved by learner."""
    return resolve_mistake(user_id=user_id, mistake_id=mistake_id)


def summarize_mistake_patterns(user_id: int) -> Dict[str, Any]:
    """Summarizes common mistake categories and frequency for dashboard insights."""
    all_mistakes = get_user_mistakes(user_id=user_id, unresolved_only=False)
    total_count = len(all_mistakes)
    unresolved_count = sum(1 for m in all_mistakes if not m.get("is_resolved"))

    category_counts: Dict[str, int] = {}
    for m in all_mistakes:
        cat = m.get("mistake_type", "other")
        category_counts[cat] = category_counts.get(cat, 0) + m.get("occurrence_count", 1)

    top_repeated = sorted(all_mistakes, key=lambda x: x.get("occurrence_count", 1), reverse=True)[:3]

    return {
        "total_recorded": total_count,
        "unresolved_count": unresolved_count,
        "category_breakdown": category_counts,
        "top_recurring": top_repeated
    }
