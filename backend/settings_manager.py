"""
WanderSuite — Settings Manager

Global settings (admin): serpapi_key, gemini_key, openai_key,
                          llm_provider, telegram_*, gotify_*, language,
                          timezone, date_format, currency,
                          home_lat, home_lon, home_name
Per-user settings:        dawarich_url, dawarich_token,
                          actual_url, actual_token, actual_file,
                          home_lat, home_lon, home_name, travel_categories
"""

import os
import re
import base64
import hashlib
from cryptography.fernet import Fernet
from database import (
    save_setting, get_setting, get_all_settings,
    save_user_setting, get_user_setting, get_all_user_settings,
)

GLOBAL_KEYS = [
    "serpapi_key", "gemini_key", "openai_key", "llm_provider",
    "telegram_bot_token", "telegram_chat_id", "gotify_url", "gotify_token",
    "language", "timezone", "date_format", "currency",
    "home_lat", "home_lon", "home_name",
]

USER_KEYS = [
    "dawarich_url", "dawarich_token",
    "actual_url", "actual_token", "actual_file",
    "home_lat", "home_lon", "home_name",
    "travel_categories", "timezone", "date_format", "currency",
    "immich_url", "immich_api_key", "immich_geo_sync",
    "ww_adults", "ww_children", "ww_home_airport",
    "ww_lug_s10", "ww_lug_s20", "ww_lug_s23",
    "ww_lug_l10", "ww_lug_l20", "ww_lug_l23",
    "ww_dep_min", "ww_dep_max", "ww_arr_min", "ww_arr_max",
    "travel_style", "climate_pref", "landscape_pref",
    "companions", "wish_text", "unsplash_key",
    "travel_mode", "max_travel_time", "history_mode",
]

ALL_KEYS = GLOBAL_KEYS + USER_KEYS
_MASKED = {k for k in ALL_KEYS if k.endswith("_key") or k.endswith("_token")}


def _get_fernet() -> Fernet:
    secret = os.environ.get("APP_SECRET", "wandersuite-default-secret-change-in-production")
    key_bytes = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def normalize_coordinate(value: str | None) -> str | None:
    """
    FIX: Konvertiert DMS-Koordinaten (46°47'57.91"N) ins Dezimalformat (46.7994).
    Akzeptiert bereits korrekte Dezimalwerte ohne Änderung.
    Gibt None zurück wenn der Wert nicht parsebar ist.
    """
    if not value:
        return value
    value = str(value).strip()

    # Bereits Dezimalformat (z.B. "46.7994" oder "-34.56")
    try:
        f = float(value)
        if -180.0 <= f <= 180.0:
            return f"{f:.6f}"
    except ValueError:
        pass

    # DMS-Format: 46°47'57.91"N  oder  11°56'3.44"E  oder  34°33'47.52"S
    dms_pattern = re.compile(
        r"""^\s*
        (\d+)\s*°\s*          # Grad
        (\d+)\s*'\s*          # Minuten
        ([\d.]+)\s*"?\s*       # Sekunden (optional ")
        ([NSEWnsew]?)             # Himmelsrichtung
        \s*$""",
        re.VERBOSE,
    )
    m = dms_pattern.match(value)
    if m:
        deg  = float(m.group(1))
        mins = float(m.group(2))
        secs = float(m.group(3))
        hemi = m.group(4).upper()
        decimal = deg + mins / 60.0 + secs / 3600.0
        if hemi in ("S", "W"):
            decimal = -decimal
        if -180.0 <= decimal <= 180.0:
            return f"{decimal:.6f}"

    return None  # nicht parsebar — lieber None als kaputten Wert speichern


# ── Global settings ───────────────────────────────────────────────────────────

def save_settings_bulk(settings: dict) -> None:
    """Save global settings. Normalizes home_lat/home_lon to decimal format."""
    fernet = _get_fernet()
    for key, value in settings.items():
        if key not in GLOBAL_KEYS or value is None:
            continue
        # Normalize coordinate fields
        if key in ("home_lat", "home_lon"):
            value = normalize_coordinate(str(value))
            if value is None:
                continue  # skip invalid coordinate
        save_setting(key, str(value), fernet)


def get_settings_all() -> dict:
    """Return all global settings, secrets masked."""
    fernet = _get_fernet()
    raw = get_all_settings(fernet)
    return {k: ("••••••••" if k in _MASKED and v else v or "") for k, v in raw.items()}


def get_setting_value(key: str) -> str | None:
    fernet = _get_fernet()
    return get_setting(key, fernet)


# ── Per-user settings ─────────────────────────────────────────────────────────

def save_user_settings_bulk(user_id: int, settings: dict) -> None:
    """Save per-user settings. Normalizes home_lat/home_lon to decimal format."""
    fernet = _get_fernet()
    for key, value in settings.items():
        if key not in USER_KEYS or value is None:
            continue
        if key in ("home_lat", "home_lon"):
            value = normalize_coordinate(str(value))
            if value is None:
                continue
        save_user_setting(user_id, key, str(value), fernet)


def get_user_settings_all(user_id: int) -> dict:
    fernet = _get_fernet()
    raw = get_all_user_settings(user_id, fernet)
    return {k: ("••••••••" if k in _MASKED and v else v or "") for k, v in raw.items()}


def get_user_setting_value(user_id: int, key: str) -> str | None:
    fernet = _get_fernet()
    return get_user_setting(user_id, key, fernet)


def resolve_home_location(user_id: int) -> tuple[str | None, str | None, str | None]:
    """
    Resolve home lat/lon/name for a user.
    Priority: per-user setting > global setting > None.
    Returns (lat, lon, name) — always in decimal format.
    """
    fernet = _get_fernet()
    lat  = get_user_setting(user_id, "home_lat",  fernet) or get_setting("home_lat",  fernet)
    lon  = get_user_setting(user_id, "home_lon",  fernet) or get_setting("home_lon",  fernet)
    name = get_user_setting(user_id, "home_name", fernet) or get_setting("home_name", fernet)
    # Normalize on read too (handles legacy data already in DB)
    lat = normalize_coordinate(lat)
    lon = normalize_coordinate(lon)
    return lat, lon, name
