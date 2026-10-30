"""
Date and Time Helper Functions.
Handles UTC storage, timezone adjustments, and learning streak calculations.
"""
from datetime import datetime, date, timedelta, timezone
import zoneinfo


def utc_now() -> datetime:
    """Returns the current UTC datetime."""
    return datetime.now(timezone.utc)


def get_local_date(tz_name: str = "Asia/Kolkata") -> date:
    """Returns today's date in the specified local timezone."""
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    return datetime.now(tz).date()


def calculate_streak(active_dates: list[date], reference_date: date | None = None) -> int:
    """
    Calculates consecutive active days streak up to today or yesterday.
    If the user has not practiced today or yesterday, streak is 0.
    """
    if not active_dates:
        return 0

    if reference_date is None:
        reference_date = get_local_date()

    unique_dates = sorted(set(active_dates), reverse=True)

    # Check if reference_date or reference_date - 1 is present
    yesterday = reference_date - timedelta(days=1)
    if unique_dates[0] not in (reference_date, yesterday):
        return 0

    streak = 1
    current = unique_dates[0]

    for next_date in unique_dates[1:]:
        if next_date == current - timedelta(days=1):
            streak += 1
            current = next_date
        elif next_date == current:
            continue
        else:
            break

    return streak
