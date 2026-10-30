"""
Authentication and Learner Account Management Service.
Handles registration, login, profile updates, and account deletion.
"""
from typing import Tuple, Optional, Dict, Any
from utils.security import hash_password, verify_password, sanitize_input
from utils.validators import (
    normalize_email,
    validate_email,
    validate_password,
    validate_mother_tongue,
    validate_level,
    validate_daily_goal
)
from repositories.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_last_login,
    update_user_profile,
    delete_user_account
)
from repositories.settings import upsert_settings, get_settings


def register_user(
    name: str,
    email: str,
    password: str,
    confirm_password: str,
    mother_tongue: str,
    level: int = 1,
    daily_goal: int = 15,
    preferred_city: str = "Bengaluru"
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Registers a new user and sets up their default preferences."""
    clean_name = sanitize_input(name)
    if not clean_name or len(clean_name) < 2:
        return False, "Please provide a valid full name (at least 2 characters).", None

    norm_email = normalize_email(email)
    if not validate_email(norm_email):
        return False, "Please enter a valid email address.", None

    if password != confirm_password:
        return False, "Passwords do not match.", None

    valid_pwd, pwd_err = validate_password(password)
    if not valid_pwd:
        return False, pwd_err, None

    if not validate_mother_tongue(mother_tongue):
        return False, "Supported mother tongues are Marathi (mr), Hindi (hi), and English (en).", None

    if not validate_level(level):
        level = 1

    if not validate_daily_goal(daily_goal):
        daily_goal = 15

    # Check if email is already taken
    existing = get_user_by_email(norm_email)
    if existing:
        return False, "An account with this email address already exists.", None

    try:
        pwd_hash = hash_password(password)
        user_id = create_user(
            name=clean_name,
            email=norm_email,
            password_hash=pwd_hash,
            mother_tongue=mother_tongue,
            level=level
        )
        upsert_settings(
            user_id=user_id,
            daily_goal_minutes=daily_goal,
            preferred_city=preferred_city,
            voice_enabled=True,
            interests=["shopping", "food", "travel"]
        )
        user_profile = get_user_by_id(user_id)
        return True, "Registration successful!", user_profile
    except Exception as e:
        return False, f"Registration failed: {str(e)}", None


def login_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Authenticates a user by email and password."""
    norm_email = normalize_email(email)
    if not norm_email or not password:
        return False, "Please provide both email and password.", None

    try:
        user = get_user_by_email(norm_email)
        if not user:
            return False, "Invalid email or password.", None

        if not verify_password(password, user["password_hash"]):
            return False, "Invalid email or password.", None

        update_last_login(user["id"])
        clean_user = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "mother_tongue": user["mother_tongue"],
            "level": user["level"],
            "last_login_at": user.get("last_login_at")
        }
        return True, "Login successful!", clean_user
    except Exception as e:
        return False, f"Login failed: {str(e)}", None


def get_current_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves full profile and settings for the authenticated user."""
    user = get_user_by_id(user_id)
    if not user:
        return None
    settings = get_settings(user_id)
    user["settings"] = settings or {
        "daily_goal_minutes": 15,
        "preferred_city": "Bengaluru",
        "voice_enabled": True,
        "interests_json": []
    }
    return user


def update_profile(
    user_id: int,
    name: str,
    mother_tongue: str,
    level: int,
    daily_goal: int,
    preferred_city: str,
    voice_enabled: bool
) -> Tuple[bool, str]:
    """Updates user information and settings."""
    clean_name = sanitize_input(name)
    if not clean_name:
        return False, "Name cannot be empty."

    if not validate_mother_tongue(mother_tongue):
        return False, "Invalid mother tongue selection."

    if not validate_level(level):
        return False, "Invalid learning level."

    if not validate_daily_goal(daily_goal):
        return False, "Daily practice goal must be between 5 and 180 minutes."

    try:
        update_user_profile(user_id, clean_name, mother_tongue, level)
        upsert_settings(
            user_id=user_id,
            daily_goal_minutes=daily_goal,
            preferred_city=preferred_city,
            voice_enabled=voice_enabled
        )
        return True, "Profile updated successfully!"
    except Exception as e:
        return False, f"Failed to update profile: {str(e)}"


def delete_account(user_id: int) -> Tuple[bool, str]:
    """Deletes user account and associated personal data."""
    try:
        success = delete_user_account(user_id)
        if success:
            return True, "Account deleted successfully."
        return False, "Account could not be found or was already deleted."
    except Exception as e:
        return False, f"Account deletion failed: {str(e)}"
