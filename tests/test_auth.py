"""
Authentication and Password Security Tests.
"""
import pytest
from utils.security import hash_password, verify_password, sanitize_input
from utils.validators import validate_mother_tongue


def test_password_hashing():
    pwd = "secretPassword123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongPassword", hashed) is False


def test_password_empty_or_short():
    with pytest.raises(ValueError):
        hash_password("123")
    with pytest.raises(ValueError):
        hash_password("")


def test_sanitize_input():
    dirty = "  <script>alert('xss');</script> Hello  "
    clean = sanitize_input(dirty)
    assert "<script>" not in clean
    assert "&lt;script&gt;" in clean
    assert clean.startswith("&lt;script&gt;")
    assert clean.endswith("Hello")


def test_unsupported_mother_tongue():
    assert validate_mother_tongue("de") is False
    assert validate_mother_tongue("mr") is True
    assert validate_mother_tongue("hi") is True
    assert validate_mother_tongue("en") is True
