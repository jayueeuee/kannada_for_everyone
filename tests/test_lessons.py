"""
Lessons and Quiz Scoring Deterministic Logic Tests.
"""
import pytest


def grade_test_quiz(exercises, submitted):
    correct = 0
    total = len(exercises)
    for ex in exercises:
        ex_id = ex["id"]
        ex_type = ex["type"]
        val = submitted.get(ex_id)
        if ex_type == "matching":
            pairs = ex.get("pairs", [])
            if isinstance(val, dict) and all(val.get(p["kannada"]) == p["match"] for p in pairs):
                correct += 1
        elif ex_type in ("fill_blank", "translation"):
            if isinstance(val, str) and val.strip().lower() == ex.get("correct_answer", "").strip().lower():
                correct += 1
        elif ex_type == "role_play":
            if val and len(str(val).strip()) > 1:
                correct += 1
    return round((correct / total) * 100.0, 1)


def test_quiz_scoring_all_correct(sample_lesson):
    exercises = sample_lesson["content_json"]["exercises"]
    answers = {
        "m1": {"ನಮಸ್ಕಾರ": "Hello", "ಧನ್ಯವಾದಗಳು": "Thank you"},
        "f1": "ಚೆನ್ನಾಗಿದ್ದೀನಿ",
        "t1": "ಹೇಗಿದ್ದೀರ?"
    }
    score = grade_test_quiz(exercises, answers)
    assert score == 100.0


def test_quiz_scoring_partial(sample_lesson):
    exercises = sample_lesson["content_json"]["exercises"]
    answers = {
        "m1": {"ನಮಸ್ಕಾರ": "Hello", "ಧನ್ಯವಾದಗಳು": "Wrong Match"},
        "f1": "ಚೆನ್ನಾಗಿದ್ದೀನಿ",
        "t1": "ಹೇಗಿದ್ದೀರ?"
    }
    score = grade_test_quiz(exercises, answers)
    assert score == 66.7


def test_quiz_scoring_all_incorrect(sample_lesson):
    exercises = sample_lesson["content_json"]["exercises"]
    answers = {
        "m1": {},
        "f1": "wrong",
        "t1": "wrong"
    }
    score = grade_test_quiz(exercises, answers)
    assert score == 0.0
