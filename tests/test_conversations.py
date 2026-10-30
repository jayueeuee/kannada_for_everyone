"""Conversation prompts and Hugging Face integration tests."""

import pytest

from services import ai_tutor, daily_companion
from services.ai_tutor import _clean_json_text
from utils.prompts import build_system_prompt


def test_build_system_prompt_languages():
    prompt_mr = build_system_prompt("mr", 1, "Grocery Shopping", "Shopkeeper")
    assert "Marathi" in prompt_mr
    assert "Level 1" in prompt_mr
    assert "Grocery Shopping" in prompt_mr

    prompt_hi = build_system_prompt("hi", 2, "Restaurant", "Server")
    assert "Hindi" in prompt_hi
    assert "Level 2" in prompt_hi

    prompt_en = build_system_prompt("en", 3, "Bus Travel", "Conductor")
    assert "English" in prompt_en
    assert "Level 3" in prompt_en


def test_clean_json_markdown():
    wrapped = '```json\n{"reply": "ನಮಸ್ಕಾರ"}\n```'
    assert _clean_json_text(wrapped) == '{"reply": "ನಮಸ್ಕಾರ"}'
    assert _clean_json_text('{"reply": "ನಮಸ್ಕಾರ"}') == '{"reply": "ನಮಸ್ಕಾರ"}'


def test_hf_chat_request_uses_chat_completions_api(monkeypatch):
    class FakeResponse:
        ok = True

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": '{"reply":"ನಮಸ್ಕಾರ"}'}}]}

    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(ai_tutor.Config, "is_hf_enabled", lambda: True)
    monkeypatch.setattr(ai_tutor.Config, "HF_TOKEN", "hf_test")
    monkeypatch.setattr(ai_tutor.Config, "HF_TEXT_MODEL", "openai/gpt-oss-20b")
    monkeypatch.setattr(ai_tutor.requests, "post", fake_post)

    result = ai_tutor.generate_hf_chat_response(
        [{"role": "user", "content": "ನಮಸ್ಕಾರ"}],
        json_mode=True,
    )

    assert result == '{"reply":"ನಮಸ್ಕಾರ"}'
    assert captured["url"] == "https://router.huggingface.co/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer hf_test"
    assert captured["json"]["model"] == "openai/gpt-oss-20b"
    assert captured["json"]["messages"] == [{"role": "user", "content": "ನಮಸ್ಕಾರ"}]
    assert captured["json"]["response_format"] == {"type": "json_object"}


def test_hf_chat_requires_token(monkeypatch):
    monkeypatch.setattr(ai_tutor.Config, "is_hf_enabled", lambda: True)
    monkeypatch.setattr(ai_tutor.Config, "HF_TOKEN", "")

    with pytest.raises(RuntimeError, match="Hugging Face token is required"):
        ai_tutor.generate_hf_chat_response([{"role": "user", "content": "hello"}])


def test_hf_audio_transcription_uses_whisper_model(monkeypatch):
    class FakeResponse:
        ok = True

        @staticmethod
        def json():
            return {"text": "ನಮಸ್ಕಾರ"}

    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(ai_tutor.Config, "is_hf_enabled", lambda: True)
    monkeypatch.setattr(ai_tutor.Config, "HF_TOKEN", "hf_test")
    monkeypatch.setattr(ai_tutor.Config, "HF_WHISPER_MODEL", "openai/whisper-large-v3")
    monkeypatch.setattr(ai_tutor.requests, "post", fake_post)

    assert ai_tutor.transcribe_audio_bytes(b"audio-bytes", "recording.wav") == "ನಮಸ್ಕಾರ"
    assert captured["url"] == (
        "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3"
    )
    assert captured["data"] == b"audio-bytes"
    assert captured["headers"]["Content-Type"] == "audio/wav"
    assert "files" not in captured


def test_hf_whisper_rejects_unsupported_format():
    with pytest.raises(ValueError, match="Unsupported recording format"):
        ai_tutor.transcribe_audio_bytes(b"fake-audio", "recording.xyz")


def test_daily_companion_uses_huggingface_model(monkeypatch):
    monkeypatch.setattr(daily_companion.Config, "is_hf_enabled", lambda: True)
    monkeypatch.setattr(daily_companion.Config, "is_hf_configured", lambda: True)
    monkeypatch.setattr(daily_companion, "_get_time_of_day", lambda: "Morning (ಬೆಳಗ್ಗೆ)")
    monkeypatch.setattr(
        daily_companion,
        "get_current_weather",
        lambda city: {"temperature_c": 22, "condition_en": "Clear"},
    )
    monkeypatch.setattr(
        daily_companion,
        "generate_weather_practice_suggestion",
        lambda weather, language: "Practice a weather phrase.",
    )
    monkeypatch.setattr(
        daily_companion,
        "generate_hf_chat_response",
        lambda messages, **kwargs: '{"title":"Morning practice"}',
    )

    suggestion = daily_companion.get_daily_suggestion(user_id=1)

    assert suggestion["title"] == "Morning practice"
    assert suggestion["weather"]["condition_en"] == "Clear"


def test_daily_companion_skips_huggingface_when_token_missing(monkeypatch):
    monkeypatch.setattr(daily_companion.Config, "is_hf_enabled", lambda: True)
    monkeypatch.setattr(daily_companion.Config, "is_hf_configured", lambda: False)
    monkeypatch.setattr(daily_companion, "_get_time_of_day", lambda: "Morning (ಬೆಳಗ್ಗೆ)")
    monkeypatch.setattr(daily_companion, "get_current_weather", lambda city: None)
    monkeypatch.setattr(
        daily_companion,
        "generate_weather_practice_suggestion",
        lambda weather, language: "",
    )

    def unexpected_hf_call(*args, **kwargs):
        raise AssertionError("Hugging Face should not be called without a token.")

    monkeypatch.setattr(daily_companion, "generate_hf_chat_response", unexpected_hf_call)

    suggestion = daily_companion.get_daily_suggestion(user_id=1)

    assert suggestion["title"] == "Morning Coffee & Greetings"
