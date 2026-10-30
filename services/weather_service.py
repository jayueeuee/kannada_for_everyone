"""
Weather Retrieval and Context-Aware Kannada Practice Suggestions using Open-Meteo.
Uses free geocoding and weather endpoints without requiring a paid API key.
"""
import logging
from typing import Dict, Any, Optional, Tuple
import requests

logger = logging.getLogger("weather_service")

# Simple in-memory cache to avoid redundant requests during reruns
_WEATHER_CACHE: Dict[str, Dict[str, Any]] = {}

WMO_WEATHER_CODES = {
    0: {"desc_en": "Clear sky", "desc_hi": "साफ़ आसमान", "desc_mr": "निरभ्र आकाश", "icon": "☀️", "type": "sunny"},
    1: {"desc_en": "Mainly clear", "desc_hi": "मुख्यतः साफ़", "desc_mr": "मुख्यतः स्वच्छ", "icon": "🌤️", "type": "clear"},
    2: {"desc_en": "Partly cloudy", "desc_hi": "आंशिक बादल", "desc_mr": "अंशतः ढगाळ", "icon": "⛅", "type": "cloudy"},
    3: {"desc_en": "Overcast", "desc_hi": "बादल छाए हुए", "desc_mr": "ढगाळ वातावरण", "icon": "☁️", "type": "cloudy"},
    45: {"desc_en": "Foggy", "desc_hi": "कोहरा", "desc_mr": "धुके", "icon": "🌫️", "type": "fog"},
    51: {"desc_en": "Light drizzle", "desc_hi": "हल्की बूंदाबांदी", "desc_mr": "हलकी रिमझिम", "icon": "🌦️", "type": "rain"},
    61: {"desc_en": "Slight rain", "desc_hi": "हल्की बारिश", "desc_mr": "हलका पाऊस", "icon": "🌧️", "type": "rain"},
    63: {"desc_en": "Moderate rain", "desc_hi": "मध्यम बारिश", "desc_mr": "मध्यम पाऊस", "icon": "🌧️", "type": "rain"},
    65: {"desc_en": "Heavy rain", "desc_hi": "भारी बारिश", "desc_mr": "मुसळधार पाऊस", "icon": "⛈️", "type": "rain"},
    80: {"desc_en": "Rain showers", "desc_hi": "बारिश की फुहारें", "desc_mr": "पावसाची सर", "icon": "🌦️", "type": "rain"},
    95: {"desc_en": "Thunderstorm", "desc_hi": "तूफान", "desc_mr": "वादळ", "icon": "⚡", "type": "storm"}
}


def get_city_coordinates(city_name: str) -> Optional[Tuple[float, float, str]]:
    """Geocodes a city name to latitude and longitude using Open-Meteo geocoding."""
    if not city_name or not city_name.strip():
        return None

    clean_city = city_name.strip()
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={clean_city}&count=1&language=en&format=json"

    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results")
            if results and len(results) > 0:
                first = results[0]
                return float(first["latitude"]), float(first["longitude"]), first.get("name", clean_city)
        return None
    except Exception as e:
        logger.warning("Geocoding lookup failed for '%s': %s", clean_city, str(e))
        return None


def get_current_weather(city_name: str = "Bengaluru") -> Optional[Dict[str, Any]]:
    """
    Fetches real-time weather from Open-Meteo for the specified city.
    Returns weather data dict or None on failure.
    """
    clean_city = city_name.strip() if city_name else "Bengaluru"
    if clean_city in _WEATHER_CACHE:
        return _WEATHER_CACHE[clean_city]

    coords = get_city_coordinates(clean_city)
    if not coords:
        return None

    lat, lon, resolved_name = coords
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"

    try:
        res = requests.get(weather_url, timeout=10)
        if res.status_code != 200:
            return None

        data = res.json()
        current = data.get("current", {})
        temp = current.get("temperature_2m")
        w_code = current.get("weather_code", 0)
        humidity = current.get("relative_humidity_2m")

        info = WMO_WEATHER_CODES.get(w_code, WMO_WEATHER_CODES[0])

        result = {
            "city": resolved_name,
            "temperature_c": temp,
            "humidity": humidity,
            "weather_code": w_code,
            "condition_en": info["desc_en"],
            "condition_hi": info["desc_hi"],
            "condition_mr": info["desc_mr"],
            "icon": info["icon"],
            "type": info["type"]
        }
        _WEATHER_CACHE[clean_city] = result
        return result
    except Exception as e:
        logger.warning("Open-Meteo request failed: %s", str(e))
        return None


def generate_weather_practice_suggestion(weather_data: Optional[Dict[str, Any]], mother_tongue: str = "en") -> Dict[str, str]:
    """
    Generates a localized Kannada conversation prompt based on actual retrieved weather.
    """
    if not weather_data:
        return {
            "kannada": "ಇವತ್ತು ಹವಾಮಾನ ಹೇಗಿದೆ? (Ivattu havāmāna hēgide?)",
            "meaning": "How is the weather today?",
            "prompt": "Ask someone about today's weather in Kannada.",
            "scenario": "daily-greetings"
        }

    w_type = weather_data.get("type", "clear")
    temp = weather_data.get("temperature_c", 25)
    city = weather_data.get("city", "Bengaluru")

    if w_type == "rain" or w_type == "storm":
        return {
            "kannada": f"ಇವತ್ತು {city}ನಲ್ಲಿ ಮಳೆ ಬರ್ತಿದೆ! ಒಂದು ಬಿಸಿ ಫಿಲ್ಟರ್ ಕಾಫಿ ಕುಡಿಯೋಣ್ವಾ?",
            "transliteration": f"Ivattu {city}nalli maḷe bartide! Ondu bisi philṭar kāfi kuḍiyōṇvā?",
            "meaning": f"It is raining in {city} today! Shall we drink a hot filter coffee?",
            "prompt": f"Practise ordering a hot drink or discussing the rain in {city}.",
            "scenario": "restaurant"
        }
    elif temp and temp > 30:
        return {
            "kannada": f"ಇವತ್ತು ತುಂಬಾ ಬಿಸಿಲಿದೆ ({temp}°C). ನನಗೆ ತಣ್ಣನೆ ಎಳನೀರು ಬೇಕು.",
            "transliteration": f"Ivattu tumbā bisilide ({temp}°C). Nanage taṇṇane eḷanīru bēku.",
            "meaning": f"It is very sunny today ({temp}°C). I want tender coconut water.",
            "prompt": "Practise asking for tender coconut or cold water at a street vendor.",
            "scenario": "local-market"
        }
    else:
        return {
            "kannada": f"ಇವತ್ತು {city}ನಲ್ಲಿ ಹವಾಮಾನ ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ! ಹೊರಗೆ ವಾಕಿಂಗ್ ಹೋಗೋಣ್ವಾ?",
            "transliteration": f"Ivattu {city}nalli havāmāna tumbā cennāgide! Horage wāking hōgōṇvā?",
            "meaning": f"The weather in {city} is very pleasant today! Shall we go for a walk outside?",
            "prompt": "Practise greeting a neighbour and discussing the pleasant weather.",
            "scenario": "talking-to-neighbours"
        }
