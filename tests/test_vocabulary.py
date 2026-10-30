"""
Vocabulary Filtering, Search, and Unicode Normalization Tests.
"""
import pytest
from utils.transliteration import normalize_kannada_text, calculate_transcript_similarity


def test_normalize_kannada_text():
    raw = "  ನಮಸ್ಕಾರ    ಹೇಗಿದ್ದೀರ?  "
    norm = normalize_kannada_text(raw)
    assert norm == "ನಮಸ್ಕಾರ ಹೇಗಿದ್ದೀರ?"


def test_transcript_similarity_exact():
    target = "ನಮಸ್ಕಾರ! ಏನು ಬೇಕು?"
    rec = "ನಮಸ್ಕಾರ! ಏನು ಬೇಕು?"
    score = calculate_transcript_similarity(target, rec)
    assert score == 100.0


def test_transcript_similarity_partial():
    target = "ಒಂದು ಕಾಫಿ ಕೊಡಿ"
    rec = "ಎರಡು ಕಾಫಿ ಕೊಡಿ"
    score = calculate_transcript_similarity(target, rec)
    assert 40.0 <= score <= 90.0


def test_transcript_similarity_empty():
    assert calculate_transcript_similarity("", "ನಮಸ್ಕಾರ") == 0.0
    assert calculate_transcript_similarity("ನಮಸ್ಕಾರ", "") == 0.0
