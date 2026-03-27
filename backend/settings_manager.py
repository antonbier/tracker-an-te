"""
WanderSuite — Settings Manager
Encrypted storage of API keys in SQLite via Fernet (AES-128).
Encryption key is derived from the APP_SECRET environment variable.

If APP_SECRET is not set, a default key is used (development only).
Always set APP_SECRET in production via .env or docker-compose environment.
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from database import save_setting, get_setting, get_all_settings

# Bekannte Setting-Keys
SETTING_KEYS = [
    "serpapi_key",
    "gemini_key",
    "openai_key",
    "dawarich_url",
    "dawarich_token",
    "actual_url",
    "actual_token",
    "llm_provider",
    "timezone",
    "home_lat",
    "home_lon",
    "travel_categories",   # comma-separated ActualBudget category names
]


def _get_fernet() -> Fernet:
    """
    Fernet-Instanz aus APP_SECRET ableiten.
    APP_SECRET kann beliebiger String sein — wird zu 32-Byte Key gehasht.
    Fallback: statischer Default-Key (nur für lokale Entwicklung).
    """
    secret = os.environ.get("APP_SECRET", "wandersuite-default-secret-change-in-production")
    key_bytes = hashlib.sha256(secret.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def save_settings_bulk(settings: dict) -> None:
    """Mehrere Settings auf einmal speichern."""
    fernet = _get_fernet()
    for key, value in settings.items():
        if key in SETTING_KEYS and value is not None:
            save_setting(key, str(value), fernet)


def get_settings_all() -> dict:
    """Alle Settings entschlüsselt zurückgeben (für API-Response, Keys maskiert)."""
    fernet = _get_fernet()
    raw = get_all_settings(fernet)
    # API Keys maskieren für Frontend-Anzeige
    masked = {}
    for key, value in raw.items():
        if key.endswith("_key") or key.endswith("_token"):
            masked[key] = "••••••••" if value else ""
        else:
            masked[key] = value
    return masked


def get_setting_value(key: str) -> str | None:
    """Einzelnen Setting-Wert entschlüsselt abrufen (intern für Scraper)."""
    fernet = _get_fernet()
    return get_setting(key, fernet)
