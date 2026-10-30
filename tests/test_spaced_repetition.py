"""
Spaced Repetition (SM-2) Scheduling Algorithm Tests.
"""
from datetime import datetime, timezone
import pytest
from services.spaced_repetition import calculate_next_review


def test_rating_again_resets_repetitions():
    now = datetime(2026, 10, 20, 10, 0, 0, tzinfo=timezone.utc)
    res = calculate_next_review(
        rating="Again",
        repetitions=4,
        interval_days=10,
        ease_factor=2.5,
        reference_time=now
    )
    assert res["repetitions"] == 0
    assert res["new_interval_days"] == 1
    assert res["ease_factor"] == 2.3  # Reduced by 0.2
    assert res["mastery_status"] == "learning"


def test_rating_good_progression():
    now = datetime(2026, 10, 20, 10, 0, 0, tzinfo=timezone.utc)
    # First good review
    r1 = calculate_next_review("Good", repetitions=0, interval_days=0, ease_factor=2.5, reference_time=now)
    assert r1["repetitions"] == 1
    assert r1["new_interval_days"] == 1

    # Second good review
    r2 = calculate_next_review("Good", repetitions=1, interval_days=1, ease_factor=2.5, reference_time=now)
    assert r2["repetitions"] == 2
    assert r2["new_interval_days"] == 3

    # Third good review (3 * 2.5 = 7)
    r3 = calculate_next_review("Good", repetitions=2, interval_days=3, ease_factor=2.5, reference_time=now)
    assert r3["repetitions"] == 3
    assert r3["new_interval_days"] == 7


def test_rating_easy_bonus():
    now = datetime(2026, 10, 20, 10, 0, 0, tzinfo=timezone.utc)
    res = calculate_next_review("Easy", repetitions=0, interval_days=0, ease_factor=2.5, reference_time=now)
    assert res["repetitions"] == 1
    assert res["new_interval_days"] == 3
    assert res["ease_factor"] == 2.65


def test_invalid_rating():
    with pytest.raises(ValueError):
        calculate_next_review("InvalidRating")
