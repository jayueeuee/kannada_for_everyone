"""
Configuration and Environment Settings for Kannada for Everyone.
Loads environment variables using python-dotenv with fallback to Streamlit secrets.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current directory and parent directory
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


def _get_setting(key: str, default: str = "") -> str:
    """Retrieves setting from environment or streamlit secrets safely."""
    val = os.getenv(key)
    if val is not None and val != "":
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


class Config:
    # Application Security
    APP_SECRET_KEY = _get_setting("APP_SECRET_KEY", "kfe_secure_default_secret_key_change_in_production_2026")

    # MySQL Database Settings
    MYSQL_HOST = _get_setting("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(_get_setting("MYSQL_PORT", "3306"))
    MYSQL_USER = _get_setting("MYSQL_USER", "root")
    MYSQL_PASSWORD = _get_setting("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = _get_setting("MYSQL_DATABASE", "kannada_everyone")

    # This application uses Hugging Face Inference Providers for AI features.
    MODEL_PROVIDER = _get_setting("MODEL_PROVIDER", "huggingface").strip().lower()
    USE_HUGGINGFACE = _get_setting("USE_HUGGINGFACE", "true").strip().lower() in {"1", "true", "yes", "on"}

    HF_TOKEN = _get_setting("HF_TOKEN") or _get_setting("HUGGINGFACE_API_TOKEN") or _get_setting("HF_API_TOKEN", "")
    HF_CHAT_COMPLETIONS_URL = _get_setting(
        "HF_CHAT_COMPLETIONS_URL",
        "https://router.huggingface.co/v1/chat/completions",
    ).rstrip("/")
    HF_ASR_BASE_URL = _get_setting(
        "HF_ASR_BASE_URL",
        "https://router.huggingface.co/hf-inference/models",
    ).rstrip("/")
    HF_TEXT_MODEL = _get_setting("HF_TEXT_MODEL", _get_setting("HF_MODEL", "openai/gpt-oss-20b"))
    HF_WHISPER_MODEL = _get_setting("HF_WHISPER_MODEL", "openai/whisper-large-v3")

    INFERENCE_TIMEOUT_SECONDS = int(_get_setting("INFERENCE_TIMEOUT_SECONDS", "180"))
    AI_MAX_REQUESTS_PER_DAY = int(_get_setting("AI_MAX_REQUESTS_PER_DAY", "50"))

    # Localization
    DEFAULT_TIMEZONE = _get_setting("DEFAULT_TIMEZONE", "Asia/Kolkata")

    @classmethod
    def is_hf_enabled(cls) -> bool:
        """Reports whether the sole supported AI provider is enabled."""
        provider = (cls.MODEL_PROVIDER or "").lower()
        if provider in {"huggingface", "hf", "huggingface-inference", "hf-inference"}:
            return True
        return cls.USE_HUGGINGFACE

    @classmethod
    def is_hf_configured(cls) -> bool:
        """Reports whether Hugging Face inference has a token available."""
        return bool(cls.HF_TOKEN and cls.HF_TOKEN.strip())

    @classmethod
    def is_local_ai_enabled(cls) -> bool:
        """Backward-compatible alias for Hugging Face provider availability."""
        return cls.is_hf_enabled()
