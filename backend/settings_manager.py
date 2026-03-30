"""
WanderSuite — Settings Manager
Encrypted storage of API keys in SQLite via Fernet (AES-128).
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from database import save_setting, get_setting, get_all_settings

SETTING_KEYS = [
    "serpapi_key",
    "gemini_key",
    "openai_key",
    "dawarich_url",
    "dawarich_token",
    "actual_url",
    "actual_token",
    "actual_file",
    "llm_provider",
    "timezone",
    "home_lat",
    "home_lon",
    "travel_categories",
    "telegram_bot_token",
    "telegram_chat_id",
    "gotify_url",
    "gotify_token",
    "language",          # UI language: de | en | it
]

# Keys that are masked in GET /api/settings response
_MASKED_KEYS = {k for k in SETTING_KEYS if k.endswith("_key") or k.endswith("_token")}


def _get_fernet() -> Fernet:
    secret = os.environ.get("APP_SECRET", "wandersuite-default-secret-change-in-production")
    key_bytes = hashlib.sha256(secret.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def save_settings_bulk(settings: dict) -> None:
    fernet = _get_fernet()
    for key, value in settings.items():
        if key in SETTING_KEYS and value is not None:
            save_setting(key, str(value), fernet)


def get_settings_all() -> dict:
    fernet = _get_fernet()
    raw = get_all_settings(fernet)
    masked = {}
    for key, value in raw.items():
        if key in _MASKED_KEYS:
            masked[key] = "••••••••" if value else ""
        else:
            masked[key] = value
    return masked


def get_setting_value(key: str) -> str | None:
    fernet = _get_fernet()
    return get_setting(key, fernet)
