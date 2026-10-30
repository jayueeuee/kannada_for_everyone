"""
Weather Service and Contextual Practice Suggestion Tests.
"""
import pytest
from services.weather_service import generate_weather_practice_suggestion


def test_weather_suggestion_rain():
    rain_data = {
        "city": "Bengaluru",
        "temperature_c": 22.5,
        "type": "rain",
        "condition_en": "Moderate rain"
    }
    sugg = generate_weather_practice_suggestion(rain_data, "en")
    assert "ಮಳೆ" in sugg["kannada"]  # Kannada word for rain
    assert "restaurant" in sugg["scenario"]


def test_weather_suggestion_hot():
    hot_data = {
        "city": "Ballari",
        "temperature_c": 36.0,
        "type": "sunny",
        "condition_en": "Clear sky"
    }
    sugg = generate_weather_practice_suggestion(hot_data, "en")
    assert "ಬಿಸಿಲಿದೆ" in sugg["kannada"]  # Sunny/hot
    assert "local-market" in sugg["scenario"]


def test_weather_suggestion_fallback_when_none():
    sugg = generate_weather_practice_suggestion(None, "en")
    assert "ಹವಾಮಾನ" in sugg["kannada"]
    assert sugg["scenario"] == "daily-greetings"
