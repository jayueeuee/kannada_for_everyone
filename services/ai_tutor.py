"""Hugging Face-based tutoring and whisper transcription for Kannada learning."""
import json
import logging
import mimetypes
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from config import Config
from utils.prompts import build_system_prompt

logger = logging.getLogger("ai_tutor")


def _build_hf_headers() -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if Config.HF_TOKEN:
        headers["Authorization"] = f"Bearer {Config.HF_TOKEN}"
    return headers


def _call_huggingface_inference(url: str, payload: Dict[str, Any], *, is_json: bool = True) -> Any:
    if not Config.HF_TOKEN:
        raise RuntimeError("Hugging Face token is required. Set HF_TOKEN or HF_API_TOKEN before enabling the Hugging Face model provider.")

    try:
        response = requests.post(
            url,
            headers=_build_hf_headers(),
            json=payload if is_json else None,
            data=payload if not is_json else None,
            timeout=Config.INFERENCE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.error("Hugging Face request failed: %s", type(exc).__name__)
        raise RuntimeError("Hugging Face inference is unavailable. Check the network and Hugging Face token.") from exc

    if not response.ok:
        try:
            detail = response.json().get("error") or response.text
        except (ValueError, AttributeError):
            detail = response.text
        logger.error("Hugging Face inference HTTP %s: %s", response.status_code, detail)
        raise RuntimeError(f"Hugging Face inference failed (HTTP {response.status_code}): {detail}")

    try:
        return response.json()
    except ValueError as exc:
        logger.error("Hugging Face response was not JSON: %s", response.text[:300])
        raise RuntimeError("Hugging Face returned a non-JSON response.") from exc


def generate_hf_chat_response(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_output_tokens: int = 800,
    json_mode: bool = False,
) -> str:
    """Generates chat text using Hugging Face Inference Providers."""
    if not Config.is_hf_enabled():
        raise RuntimeError("Hugging Face is the only supported AI provider. Set MODEL_PROVIDER=huggingface.")
    payload: Dict[str, Any] = {
        "model": Config.HF_TEXT_MODEL,
        "messages": messages,
        "max_tokens": max_output_tokens,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    result = _call_huggingface_inference(Config.HF_CHAT_COMPLETIONS_URL, payload)
    try:
        text = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Hugging Face returned no usable chat completion.") from exc
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("Hugging Face returned an empty response.")
    return text.strip()


def _clean_json_text(text: str) -> str:
    """Extracts JSON from optional markdown fences or surrounding text."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    return match.group(1).strip() if match else text.strip()


def generate_tutor_response(
    mother_tongue: str,
    level: int,
    scenario_title: str,
    ai_role: str,
    system_hint: str,
    conversation_history: List[Dict[str, Any]],
    user_message: str,
) -> Dict[str, Any]:
    """Submits a role-play and recent history to the Hugging Face text model."""
    system_instruction = build_system_prompt(
        mother_tongue=mother_tongue,
        level=level,
        scenario_title=scenario_title,
        ai_role=ai_role,
        system_hint=system_hint,
    )
    messages = [{
        "role": "system",
        "content": (
            system_instruction
            + "\nReturn exactly one valid JSON object, with no markdown or surrounding text."
        ),
    }]
    for message in conversation_history[-10:]:
        content = message.get("message_text", "")
        if content:
            role = "assistant" if message.get("speaker") == "assistant" else "user"
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    raw_output = generate_hf_chat_response(messages, json_mode=True)
    try:
        data = json.loads(_clean_json_text(raw_output))
    except json.JSONDecodeError as exc:
        logger.error("Hugging Face tutor returned invalid JSON: %s", str(exc))
        raise RuntimeError("The Hugging Face tutor returned an invalid response format.") from exc

    return {
        "reply": data.get("reply", "ನಮಸ್ಕಾರ! (Namaskara!)"),
        "transliteration": data.get("transliteration", ""),
        "translation": data.get("translation", ""),
        "correction": data.get("correction"),
        "mistake_type": data.get("mistake_type"),
        "vocabulary": data.get("vocabulary", []),
        "next_question": data.get("next_question", ""),
        "feedback": data.get("feedback", ""),
    }


def generate_conversation_assessment(
    mother_tongue: str,
    level: int,
    scenario_title: str,
    messages: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generates an assessment with Hugging Face and uses a deterministic fallback on provider errors."""
    if not messages:
        return {
            "overall_score": 80,
            "strengths": ["Completed the role-play interaction"],
            "areas_to_improve": ["Practice vocabulary from this scenario regularly"],
            "summary_feedback": "Great effort! Consistent daily practice will build fluency.",
        }

    lang_desc = {"mr": "Marathi", "hi": "Hindi"}.get(mother_tongue, "English")
    transcript = "\n".join(
        f"{message.get('speaker', 'unknown')}: {message.get('message_text', '')}"
        for message in messages
    )
    prompt = f"""Evaluate this Kannada learning conversation in '{scenario_title}'.
Learner native language: {lang_desc}. Proficiency level: {level}.
Conversation:
{transcript}
Return only valid JSON with keys overall_score (0-100), strengths (array),
areas_to_improve (array), and summary_feedback (string). Use {lang_desc}."""

    try:
        output = generate_hf_chat_response(
            [{"role": "user", "content": prompt}],
            temperature=0.5,
            max_output_tokens=400,
            json_mode=True,
        )
        assessment = json.loads(_clean_json_text(output))
        if not isinstance(assessment, dict):
            raise ValueError("Assessment is not a JSON object.")
        return assessment
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("Hugging Face assessment unavailable; using deterministic summary: %s", exc)
        return {
            "overall_score": 75,
            "strengths": ["Completed conversation practice"],
            "areas_to_improve": ["Continue practicing key vocabulary"],
            "summary_feedback": "Well done on completing this practice session!",
        }


def _transcribe_with_hf(audio_bytes: bytes, filename: str) -> Optional[str]:
    """Transcribes audio via Hugging Face Whisper inference."""
    if not Config.is_hf_enabled():
        raise RuntimeError("Hugging Face audio transcription is not configured.")
    if not Config.HF_TOKEN:
        raise RuntimeError("Hugging Face token is required. Set HF_TOKEN or HF_API_TOKEN.")
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    try:
        response = requests.post(
            f"{Config.HF_ASR_BASE_URL}/{Config.HF_WHISPER_MODEL}",
            headers={**_build_hf_headers(), "Content-Type": content_type},
            data=audio_bytes,
            timeout=Config.INFERENCE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.error("Hugging Face audio request failed: %s", type(exc).__name__)
        raise RuntimeError("Hugging Face speech transcription is unavailable.") from exc

    if not response.ok:
        error_detail = response.text[:500]
        logger.error("HF audio transcription HTTP %s: %s", response.status_code, error_detail)
        raise RuntimeError(f"Hugging Face audio transcription failed (HTTP {response.status_code}): {error_detail}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Hugging Face returned a non-JSON transcription response.") from exc
    if isinstance(payload, list):
        texts = [item.get("text") if isinstance(item, dict) else str(item) for item in payload]
        transcript = " ".join(part for part in texts if part).strip()
        return transcript or None
    if isinstance(payload, dict):
        transcript = payload.get("text") or payload.get("transcript") or payload.get("output_text")
        return transcript.strip() if isinstance(transcript, str) and transcript.strip() else None
    if isinstance(payload, str):
        return payload.strip() or None
    return None


def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "audio.wav") -> Optional[str]:
    """Transcribes Kannada speech with the configured provider."""
    if not audio_bytes:
        logger.warning("Cannot transcribe an empty audio recording.")
        return None

    suffix = Path(filename).suffix.lower()
    if suffix not in {".wav", ".mp3", ".m4a", ".ogg", ".webm"}:
        raise ValueError("Unsupported recording format. Use WAV, MP3, M4A, OGG, or WebM.")

    if not Config.is_hf_enabled():
        raise RuntimeError("Hugging Face is the only supported AI provider. Set MODEL_PROVIDER=huggingface.")
    return _transcribe_with_hf(audio_bytes, filename)
