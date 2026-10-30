"""
Situations and Role-Play Scenarios Repository.
"""
from typing import Optional, List, Dict, Any
from db import get_db_cursor


def get_all_active_situations() -> List[Dict[str, Any]]:
    """Retrieves all active role-play situations ordered by difficulty level."""
    sql = """
    SELECT `id`, `slug`, `title`, `description`, `category`, `difficulty_level`, `ai_role`, `system_hint`
    FROM `situations`
    WHERE `is_active` = TRUE
    ORDER BY `difficulty_level` ASC, `id` ASC
    """
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql)
        return cursor.fetchall()


def get_situation_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Retrieves a situation by slug."""
    sql = "SELECT * FROM `situations` WHERE `slug` = %s AND `is_active` = TRUE LIMIT 1"
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (slug,))
        return cursor.fetchone()


def get_situation_by_id(situation_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a situation by ID."""
    sql = "SELECT * FROM `situations` WHERE `id` = %s AND `is_active` = TRUE LIMIT 1"
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (situation_id,))
        return cursor.fetchone()
