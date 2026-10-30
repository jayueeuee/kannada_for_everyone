"""
User Settings Repository.
Manages user preferences such as daily goals, city, voice preference, and learning interests.
"""
import json
from typing import Optional, Dict, Any, List
from db import get_db_cursor
from utils.date_time import utc_now


def get_settings(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves settings for a user."""
    sql = "SELECT * FROM `user_settings` WHERE `user_id` = %s LIMIT 1"
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()
        if row and isinstance(row.get("interests_json"), str):
            try:
                row["interests_json"] = json.loads(row["interests_json"])
            except Exception:
                row["interests_json"] = []
        return row


def upsert_settings(
    user_id: int,
    daily_goal_minutes: int = 15,
    preferred_city: str = "Bengaluru",
    voice_enabled: bool = True,
    interests: Optional[List[str]] = None,
    timezone_str: str = "Asia/Kolkata"
) -> bool:
    """Inserts or updates settings for a user."""
    interests_json = json.dumps(interests if interests is not None else ["daily_life", "shopping"])
    sql = """
    INSERT INTO `user_settings` (
      `user_id`, `daily_goal_minutes`, `preferred_city`, `voice_enabled`, `interests_json`, `timezone`, `created_at`
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      `daily_goal_minutes` = VALUES(`daily_goal_minutes`),
      `preferred_city` = VALUES(`preferred_city`),
      `voice_enabled` = VALUES(`voice_enabled`),
      `interests_json` = VALUES(`interests_json`),
      `timezone` = VALUES(`timezone`),
      `updated_at` = VALUES(`created_at`)
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (
            user_id,
            daily_goal_minutes,
            preferred_city,
            voice_enabled,
            interests_json,
            timezone_str,
            utc_now()
        ))
        return True
