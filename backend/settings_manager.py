"""
WanderSuite — Settings Manager

Global settings (admin): serpapi_key, gemini_key, openai_key,
                          llm_provider, telegram_*, gotify_*, language,
                          timezone, date_format
Per-user settings:        dawarich_url, dawarich_token,
                          actual_url, actual_token, actual_file,
                          home_lat, home_lon, travel_categories
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from database import (
    save_setting, get_setting, get_all_settings,
    save_user_setting, get_user_setting, get_all_user_settings,
)

# Global keys — stored in settings table (admin configures once for all)
GLOBAL_KEYS = [
    "serpapi_key",
    "gemini_key",
    "openai_key",
    "llm_provider",
    "telegram_bot_token",
    "telegram_chat_id",
    "gotify_url",
    "gotify_token",
    "language",
    "timezone",
    "date_format",   # NEW: DD.MM.YYYY | MM/DD/YYYY | YYYY-MM-DD
]

# Per-user keys — stored in user_settings table (each user configures their own)
# Note: notification credentials are stored separately in user_notification_settings table
# and managed via database.get/save_user_notification_settings with Fernet encryption.
USER_KEYS = [
    "dawarich_url",
    "dawarich_token",
    "actual_url",
    "actual_token",      # ActualBudget server password
    "actual_file",       # Budget display name
    "home_lat",
    "home_lon",
    "travel_categories",
    "timezone",          # Per-user timezone override
    "date_format",       # Per-user date format override
    # Immich
    "immich_url",
    "immich_api_key",    # Fernet-verschlüsselt
    "immich_geo_sync",
    # WanderWizzard Defaults
    "ww_adults",
    "ww_children",
    "ww_home_airport",
    "ww_lug_s10",
    "ww_lug_s20",
    "ww_lug_s23",
    "ww_lug_l10",
    "ww_lug_l20",
    "ww_lug_l23",
    "ww_dep_min",
    "ww_dep_max",
    "ww_arr_min",
    "ww_arr_max",
    # WanderWizzard: Reisepersönlichkeit
    "travel_style",
    "climate_pref",
    "landscape_pref",
    "companions",
    "wish_text",
    "unsplash_key",   # Fernet-verschlüsselt
    # Discovery: Mobilitäts-Präferenzen
    "travel_mode",       # flight | car
    "max_travel_time",   # 2h | 4h | 8h | 12h | 12h+
    "history_mode",      # blacklist | context
]

ALL_KEYS = GLOBAL_KEYS + USER_KEYS
_MASKED = {k for k in ALL_KEYS if k.endswith("_key") or k.endswith("_token")}


def _get_fernet() -> Fernet:
    secret = os.environ.get("APP_SECRET", "wandersuite-default-secret-change-in-production")
    key_bytes = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


# ── Global settings ───────────────────────────────────────────────────────────

def save_settings_bulk(settings: dict) -> None:
    """Save global settings (admin only)."""
    fernet = _get_fernet()
    for key, value in settings.items():
        if key in GLOBAL_KEYS and value is not None:
            save_setting(key, str(value), fernet)

def get_settings_all() -> dict:
    """Return all global settings, secrets masked."""
    fernet = _get_fernet()
    raw = get_all_settings(fernet)
    return {k: ("••••••••" if k in _MASKED and v else v or "") for k, v in raw.items()}

def get_setting_value(key: str) -> str | None:
    """Get a single global setting (decrypted)."""
    fernet = _get_fernet()
    return get_setting(key, fernet)


# ── Per-user settings ─────────────────────────────────────────────────────────

def save_user_settings_bulk(user_id: int, settings: dict) -> None:
    """Save per-user settings."""
    fernet = _get_fernet()
    for key, value in settings.items():
        if key in USER_KEYS and value is not None:
            save_user_setting(user_id, key, str(value), fernet)

def get_user_settings_all(user_id: int) -> dict:
    """Return all per-user settings, secrets masked."""
    fernet = _get_fernet()
    raw = get_all_user_settings(user_id, fernet)
    return {k: ("••••••••" if k in _MASKED and v else v or "") for k, v in raw.items()}

def get_user_setting_value(user_id: int, key: str) -> str | None:
    """Get a single per-user setting (decrypted)."""
    fernet = _get_fernet()
    return get_user_setting(user_id, key, fernet)
