"""
Daily AI Learning Companion Service.
Generates personalized, time-and-weather-aware Kannada practice suggestions.
"""
from datetime import datetime
import json
import logging
from typing import Dict, Any, Optional
from config import Config
from services.ai_tutor import generate_hf_chat_response, _clean_json_text
from services.weather_service import get_current_weather, generate_weather_practice_suggestion
from utils.prompts import build_companion_prompt

logger = logging.getLogger("daily_companion")


def _get_time_of_day() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Morning (ಬೆಳಗ್ಗೆ)"
    elif 12 <= hour < 17:
        return "Afternoon (ಮಧ್ಯಾಹ್ನ)"
    elif 17 <= hour < 21:
        return "Evening (ಸಂಜೆ)"
    else:
        return "Night (ರಾತ್ರಿ)"


def get_daily_suggestion(
    user_id: int,
    mother_tongue: str = "en",
    level: int = 1,
    city: str = "Bengaluru",
    words_due: int = 0
) -> Dict[str, Any]:
    """
    Returns a personalized daily practice suggestion.
    Uses Hugging Face when configured, or a deterministic contextual template otherwise.
    """
    time_of_day = _get_time_of_day()
    weather = get_current_weather(city)
    weather_suggestion = generate_weather_practice_suggestion(weather, mother_tongue)

    if Config.is_hf_enabled() and Config.is_hf_configured():
        try:
            weather_desc = f"{weather.get('temperature_c', '')}°C {weather.get('condition_en', '')}" if weather else "Pleasant"
            prompt = build_companion_prompt(
                mother_tongue=mother_tongue,
                level=level,
                time_of_day=time_of_day,
                weather_info=weather_desc,
                recent_topics=f"{words_due} words due for review" if words_due > 0 else "New daily challenge"
            )
            output = generate_hf_chat_response(
                [{"role": "user", "content": prompt}],
                temperature=0.7,
                max_output_tokens=300,
                json_mode=True,
            )
            ai_data = json.loads(_clean_json_text(output))
            if not isinstance(ai_data, dict):
                raise ValueError("Daily companion response was not a JSON object.")
            ai_data["weather"] = weather
            return ai_data
        except Exception as e:
            logger.warning("AI companion generation failed, using intelligent fallback: %s", str(e))

    # Deterministic high-quality contextual suggestions
    if "Morning" in time_of_day:
        phrase = "ಶುಭೋದಯ! ಕಾಫಿ ಆಯ್ತಾ?"
        trans = "Śubhōdaya! Kāfi āytā?"
        meaning_en = "Good morning! Did you have coffee?"
        meaning_hi = "शुभ प्रभात! कॉफ़ी हुई क्या?"
        meaning_mr = "शुभ सकाळ! कॉफी झाली का?"
        title = "Morning Coffee & Greetings"
        scenario = "restaurant"
    elif "Afternoon" in time_of_day:
        phrase = "ಊಟ ಆಯ್ತಾ? ಇವತ್ತು ಊಟಕ್ಕೆ ಏನು?"
        trans = "Ūṭa āytā? Ivattu ūṭakke ēnu?"
        meaning_en = "Did you have lunch? What is for lunch today?"
        meaning_hi = "खाना हुआ क्या? आज खाने में क्या है?"
        meaning_mr = "जेवण झाले का? आज जेवणात काय आहे?"
        title = "Lunchtime Chat with Friends"
        scenario = "college-workplace"
    else:
        phrase = "ಶುಭ ಸಂಜೆ! ಮನೆಗೆ ಯಾವಾಗ ಹೋಗ್ತೀರ?"
        trans = "Śubha sañje! Manege yāvāga hōgtīra?"
        meaning_en = "Good evening! When are you going home?"
        meaning_hi = "शुभ संध्या! घर कब जा रहे हैं?"
        meaning_mr = "शुभ संध्याकाळ! घरी कधी जाणार?"
        title = "Evening Commute & Farewell"
        scenario = "bus-train-travel"

    meaning = meaning_mr if mother_tongue == "mr" else (meaning_hi if mother_tongue == "hi" else meaning_en)

    return {
        "title": title,
        "suggestion": f"Today's recommended practice for {time_of_day} in {city}.",
        "kannada_phrase": phrase,
        "transliteration": trans,
        "translation": meaning,
        "practice_scenario": scenario,
        "weather": weather,
        "weather_prompt": weather_suggestion
    }
