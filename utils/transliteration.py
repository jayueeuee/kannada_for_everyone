"""
Kannada Transliteration, Unicode Normalization, and Transcript Similarity Helpers.
"""
import unicodedata
import re


def normalize_kannada_text(text: str) -> str:
    """Normalizes Unicode text to NFC format and strips excess spaces."""
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    return re.sub(r'\s+', ' ', text).strip()


def calculate_transcript_similarity(target: str, recognized: str) -> float:
    """
    Computes a normalized word-level overlap and character similarity score
    between the target Kannada phrase and the recognized speech transcript.
    Returns a score between 0.0 and 100.0.
    """
    if not target or not recognized:
        return 0.0

    target_norm = normalize_kannada_text(target).lower()
    rec_norm = normalize_kannada_text(recognized).lower()

    if target_norm == rec_norm:
        return 100.0

    target_words = target_norm.split()
    rec_words = rec_norm.split()

    if not target_words:
        return 0.0

    # Word match count
    matched = sum(1 for w in target_words if w in rec_words)
    word_score = (matched / max(len(target_words), len(rec_words))) * 70.0

    # Character set overlap
    set_target = set(target_norm.replace(' ', ''))
    set_rec = set(rec_norm.replace(' ', ''))
    char_overlap = len(set_target.intersection(set_rec)) / max(len(set_target.union(set_rec)), 1)
    char_score = char_overlap * 30.0

    total_score = round(word_score + char_score, 1)
    return min(100.0, max(0.0, total_score))
