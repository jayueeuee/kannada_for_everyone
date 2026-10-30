"""
Input Validators for User Profiles, Authentication, and Settings.
"""
import re

SUPPORTED_LANGUAGES = {"mr": "Marathi", "hi": "Hindi", "en": "English"}
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def normalize_email(email: str) -> str:
    """Normalizes email to lowercase and strips extraneous spaces."""
    if not email:
        return ""
    return email.strip().lower()


def validate_email(email: str) -> bool:
    """Validates email format using regex."""
    if not email:
        return False
    norm = normalize_email(email)
    return bool(EMAIL_REGEX.match(norm)) and len(norm) <= 255


def validate_password(password: str) -> tuple[bool, str]:
    """
    Checks password strength. Minimum 6 characters.
    Returns (is_valid, error_message).
    """
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""


def validate_mother_tongue(lang_code: str) -> bool:
    """Checks if the language is one of the supported mother tongues."""
    return lang_code in SUPPORTED_LANGUAGES


def validate_level(level: int) -> bool:
    """Checks if the learning level is within valid bounds (1 to 5)."""
    return isinstance(level, int) and 1 <= level <= 5


def validate_daily_goal(minutes: int) -> bool:
    """Checks if the daily goal is reasonable (5 to 180 minutes)."""
    return isinstance(minutes, int) and 5 <= minutes <= 180
