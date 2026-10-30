"""
Security and Password Hashing Utilities.
Uses bcrypt with proper salting. Never stores or logs plaintext passwords.
"""
import bcrypt
import re
import html


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    salt = bcrypt.gensalt(rounds=12)
    pwd_bytes = password.encode('utf-8')
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    if not password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def sanitize_input(text: str) -> str:
    """Strips leading/trailing whitespace and escapes potential HTML tags."""
    if not text:
        return ""
    return html.escape(text.strip())
