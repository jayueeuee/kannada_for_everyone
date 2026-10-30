"""
Unit Tests for Input Validators.
"""
import pytest
from utils.validators import (
    normalize_email,
    validate_email,
    validate_password,
    validate_mother_tongue,
    validate_level,
    validate_daily_goal
)


def test_normalize_email():
    assert normalize_email("  TEST@Example.COM  ") == "test@example.com"
    assert normalize_email("") == ""
    assert normalize_email(None) == ""


def test_validate_email_valid():
    assert validate_email("user@example.com") is True
    assert validate_email("rahul.patil+kannada@gmail.co.in") is True


def test_validate_email_invalid():
    assert validate_email("not-an-email") is False
    assert validate_email("@missinguser.com") is False
    assert validate_email("user@.com") is False
    assert validate_email("") is False
    assert validate_email(None) is False


def test_validate_password():
    valid, _ = validate_password("strongpass123")
    assert valid is True

    invalid, msg = validate_password("123")
    assert invalid is False
    assert "at least 6 characters" in msg

    invalid_empty, msg_empty = validate_password("")
    assert invalid_empty is False


def test_validate_mother_tongue():
    assert validate_mother_tongue("mr") is True
    assert validate_mother_tongue("hi") is True
    assert validate_mother_tongue("en") is True
    assert validate_mother_tongue("fr") is False
    assert validate_mother_tongue("es") is False
    assert validate_mother_tongue("") is False


def test_validate_level():
    assert validate_level(1) is True
    assert validate_level(3) is True
    assert validate_level(5) is True
    assert validate_level(0) is False
    assert validate_level(6) is False
    assert validate_level("1") is False


def test_validate_daily_goal():
    assert validate_daily_goal(15) is True
    assert validate_daily_goal(60) is True
    assert validate_daily_goal(4) is False
    assert validate_daily_goal(200) is False
