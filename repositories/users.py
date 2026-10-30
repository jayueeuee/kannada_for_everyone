"""
User Account Repository.
Handles user creation, lookup, profile updates, and account deletion.
"""
from typing import Optional, Dict, Any
from db import get_db_cursor
from utils.date_time import utc_now


def create_user(name: str, email: str, password_hash: str, mother_tongue: str = "en", level: int = 1) -> int:
    """Inserts a new user and returns their generated ID."""
    sql = """
    INSERT INTO `users` (`name`, `email`, `password_hash`, `mother_tongue`, `level`, `is_active`, `created_at`)
    VALUES (%s, %s, %s, %s, %s, TRUE, %s)
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (name, email, password_hash, mother_tongue, level, utc_now()))
        return cursor.lastrowid


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves an active user record by email."""
    sql = "SELECT * FROM `users` WHERE `email` = %s AND `is_active` = TRUE LIMIT 1"
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (email,))
        return cursor.fetchone()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves an active user record by ID."""
    sql = "SELECT `id`, `name`, `email`, `mother_tongue`, `level`, `is_active`, `created_at`, `last_login_at` FROM `users` WHERE `id` = %s AND `is_active` = TRUE LIMIT 1"
    with get_db_cursor(commit=False) as (_, cursor):
        cursor.execute(sql, (user_id,))
        return cursor.fetchone()


def update_last_login(user_id: int) -> None:
    """Updates the last_login_at timestamp for the user."""
    sql = "UPDATE `users` SET `last_login_at` = %s WHERE `id` = %s"
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (utc_now(), user_id))


def update_user_profile(user_id: int, name: str, mother_tongue: str, level: int) -> bool:
    """Updates user name, mother tongue, and learning level."""
    sql = """
    UPDATE `users`
    SET `name` = %s, `mother_tongue` = %s, `level` = %s, `updated_at` = %s
    WHERE `id` = %s
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (name, mother_tongue, level, utc_now(), user_id))
        return cursor.rowcount > 0


def delete_user_account(user_id: int) -> bool:
    """Permanently deletes a user account (cascades to child records)."""
    sql = "DELETE FROM `users` WHERE `id` = %s"
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, (user_id,))
        return cursor.rowcount > 0
