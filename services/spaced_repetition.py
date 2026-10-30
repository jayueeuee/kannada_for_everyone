"""
Spaced Repetition System (SRS) Scheduling Service.
Implements a modified SM-2 algorithm with four ratings: Again, Hard, Good, Easy.
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from utils.date_time import utc_now

VALID_RATINGS = ("Again", "Hard", "Good", "Easy")


def calculate_next_review(
    rating: str,
    repetitions: int = 0,
    interval_days: int = 0,
    ease_factor: float = 2.5,
    reference_time: datetime | None = None
) -> Dict[str, Any]:
    """
    Calculates updated SRS scheduling parameters based on user's recall rating.
    """
    if rating not in VALID_RATINGS:
        raise ValueError(f"Rating must be one of {VALID_RATINGS}, got '{rating}'.")

    now = reference_time if reference_time is not None else utc_now()
    ease = max(1.3, float(ease_factor))
    reps = max(0, int(repetitions))
    prev_interval = max(0, int(interval_days))

    if rating == "Again":
        reps = 0
        new_interval = 1
        ease = max(1.3, ease - 0.2)
    elif rating == "Hard":
        reps += 1
        new_interval = max(1, int(prev_interval * 1.2)) if prev_interval > 0 else 1
        ease = max(1.3, ease - 0.15)
    elif rating == "Good":
        reps += 1
        if reps == 1:
            new_interval = 1
        elif reps == 2:
            new_interval = 3
        else:
            new_interval = max(1, int(prev_interval * ease))
    elif rating == "Easy":
        reps += 1
        if reps == 1:
            new_interval = 3
        elif reps == 2:
            new_interval = 6
        else:
            new_interval = max(1, int(prev_interval * ease * 1.3))
        ease = min(3.0, ease + 0.15)

    next_review_time = now + timedelta(days=new_interval)

    # Determine mastery status
    if reps >= 5 and new_interval >= 21:
        mastery = "mastered"
    elif reps >= 2:
        mastery = "reviewing"
    else:
        mastery = "learning"

    return {
        "rating": rating,
        "repetitions": reps,
        "previous_interval_days": prev_interval,
        "new_interval_days": new_interval,
        "ease_factor": round(ease, 2),
        "next_review_at": next_review_time,
        "mastery_status": mastery
    }
