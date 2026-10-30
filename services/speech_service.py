"""
Speech Recognition, Audio Transcription, and Pronunciation Comparison Service.
Uses local Whisper for audio transcription and compares transcript similarity.
"""
from typing import Dict, Any, Optional
from services.ai_tutor import transcribe_audio_bytes as transcribe_with_local_whisper
from utils.transliteration import calculate_transcript_similarity, normalize_kannada_text


def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "audio.wav") -> Optional[str]:
    """
    Transcribes audio bytes using a local Whisper model.
    Returns recognized transcript text or None when the recording contains no speech.
    """
    return transcribe_with_local_whisper(audio_bytes, filename)


def evaluate_pronunciation(target_text: str, recognized_text: str, mother_tongue: str = "en") -> Dict[str, Any]:
    """
    Compares the recognized transcript against the target phrase.
    Returns similarity score, difference analysis, and helpful feedback.
    """
    norm_target = normalize_kannada_text(target_text)
    norm_rec = normalize_kannada_text(recognized_text)
    similarity = calculate_transcript_similarity(norm_target, norm_rec)

    is_exact = norm_target == norm_rec
    is_good = similarity >= 75.0

    target_words = norm_target.split()
    rec_words = norm_rec.split()

    missing_words = [w for w in target_words if w not in rec_words]
    extra_words = [w for w in rec_words if w not in target_words]

    if is_exact:
        feedback = "Excellent! Your spoken transcript matches the target Kannada phrase perfectly."
    elif is_good:
        feedback = "Great attempt! Very close to the target phrase. Try repeating once more for smoother flow."
    else:
        feedback = "Good practice effort. Notice the words that differed and try speaking a bit more slowly."

    return {
        "target": norm_target,
        "recognized": norm_rec,
        "similarity_score": similarity,
        "is_exact_match": is_exact,
        "is_good_match": is_good,
        "missing_words": missing_words,
        "extra_words": extra_words,
        "assessment_method": "transcript_comparison",
        "feedback": feedback
    }
