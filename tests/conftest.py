"""
Pytest configuration and shared test fixtures for Kannada for Everyone.
"""
import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_user():
    return {
        "id": 1,
        "name": "Priya Sharma",
        "email": "priya@example.com",
        "mother_tongue": "hi",
        "level": 1,
        "is_active": True
    }


@pytest.fixture
def sample_lesson():
    return {
        "id": 1,
        "slug": "test-greetings",
        "title": "Test Greetings",
        "level": 1,
        "lesson_order": 1,
        "pass_score": 70,
        "content_json": {
            "exercises": [
                {
                    "id": "m1",
                    "type": "matching",
                    "pairs": [
                        {"kannada": "ನಮಸ್ಕಾರ", "match": "Hello"},
                        {"kannada": "ಧನ್ಯವಾದಗಳು", "match": "Thank you"}
                    ],
                    "explanation": "Standard greetings"
                },
                {
                    "id": "f1",
                    "type": "fill_blank",
                    "correct_answer": "ಚೆನ್ನಾಗಿದ್ದೀನಿ",
                    "explanation": "I am fine"
                },
                {
                    "id": "t1",
                    "type": "translation",
                    "correct_answer": "ಹೇಗಿದ್ದೀರ?",
                    "explanation": "How are you?"
                }
            ]
        }
    }
