"""
Vocabulary Management and Review Tracking Service.
"""
from typing import List, Dict, Any, Optional
from repositories.vocabulary import (
    get_vocabulary_list,
    get_vocabulary_by_id,
    save_user_vocabulary,
    remove_user_vocabulary,
    get_user_saved_vocabulary,
    get_due_user_vocabulary,
    update_user_vocab_srs,
    record_review_history
)
from repositories.progress import record_activity
from services.spaced_repetition import calculate_next_review


def list_vocabulary(
    category: Optional[str] = None,
    level: Optional[int] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetches library vocabulary with optional search and filters."""
    return get_vocabulary_list(category=category, level=level, search=search)


def save_word_for_user(user_id: int, vocabulary_id: int) -> bool:
    """Adds a word to learner's personal collection."""
    try:
        save_user_vocabulary(user_id=user_id, vocabulary_id=vocabulary_id)
        return True
    except Exception:
        return False


def remove_word_for_user(user_id: int, vocabulary_id: int) -> bool:
    """Removes a word from learner's personal collection."""
    return remove_user_vocabulary(user_id=user_id, vocabulary_id=vocabulary_id)


def get_user_vocabulary_stats(user_id: int) -> Dict[str, Any]:
    """Retrieves learner's vocabulary stats (total saved, due for review, mastered)."""
    saved = get_user_saved_vocabulary(user_id)
    due = get_due_user_vocabulary(user_id)
    mastered = [w for w in saved if w.get("mastery_status") == "mastered"]
    learning = [w for w in saved if w.get("mastery_status") == "learning"]
    reviewing = [w for w in saved if w.get("mastery_status") == "reviewing"]

    return {
        "total_saved": len(saved),
        "due_count": len(due),
        "mastered_count": len(mastered),
        "learning_count": len(learning),
        "reviewing_count": len(reviewing),
        "saved_words": saved,
        "due_words": due
    }


def process_word_review(
    user_id: int,
    user_vocab_id: int,
    current_reps: int,
    current_interval: int,
    current_ease: float,
    rating: str
) -> Dict[str, Any]:
    """
    Applies spaced repetition update for a reviewed word and records history.
    """
    srs_result = calculate_next_review(
        rating=rating,
        repetitions=current_reps,
        interval_days=current_interval,
        ease_factor=current_ease
    )

    update_user_vocab_srs(
        user_vocab_id=user_vocab_id,
        user_id=user_id,
        ease_factor=srs_result["ease_factor"],
        interval_days=srs_result["new_interval_days"],
        repetitions=srs_result["repetitions"],
        last_rating=rating,
        next_review_at=srs_result["next_review_at"],
        mastery_status=srs_result["mastery_status"]
    )

    record_review_history(
        user_vocab_id=user_vocab_id,
        rating=rating,
        previous_interval_days=srs_result["previous_interval_days"],
        new_interval_days=srs_result["new_interval_days"]
    )

    # Record daily activity
    record_activity(user_id=user_id, words_reviewed=1, minutes_spent=1)

    return srs_result
