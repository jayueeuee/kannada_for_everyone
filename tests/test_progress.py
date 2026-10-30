"""
Learning Streak and Progress Calculation Tests.
"""
from datetime import date, timedelta
import pytest
from utils.date_time import calculate_streak


def test_streak_empty():
    assert calculate_streak([]) == 0


def test_streak_active_today_only():
    today = date(2026, 10, 22)
    assert calculate_streak([today], reference_date=today) == 1


def test_streak_active_yesterday_only():
    today = date(2026, 10, 22)
    yesterday = today - timedelta(days=1)
    assert calculate_streak([yesterday], reference_date=today) == 1


def test_streak_consecutive_days():
    today = date(2026, 10, 22)
    d1 = today
    d2 = today - timedelta(days=1)
    d3 = today - timedelta(days=2)
    d4 = today - timedelta(days=3)
    assert calculate_streak([d1, d2, d3, d4], reference_date=today) == 4


def test_streak_with_duplicates_same_day():
    today = date(2026, 10, 22)
    yesterday = today - timedelta(days=1)
    # User practiced multiple times on both days
    assert calculate_streak([today, today, yesterday, yesterday], reference_date=today) == 2


def test_streak_broken():
    today = date(2026, 10, 22)
    two_days_ago = today - timedelta(days=2)
    # No practice yesterday or today
    assert calculate_streak([two_days_ago], reference_date=today) == 0
