"""
WanderSuite — Settings Manager

Fixes applied:
  - normalize_coordinate(): DMS → decimal conversion + validation
  - validate_timezone(): rejects unknown timezone strings
"""

import os
import re
import base64
import hashlib
from cryptography.fernet import Fernet
from crud.settings import (
    save_setting,
    get_setting,
    get_all_settings,
    save_user_setting,
    get_user_setting,
    get_all_user_settings,
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


_APP_SECRET_DEFAULT = "wandersuite-default-secret-change-in-production"
_APP_SECRET = os.environ.get("APP_SECRET", _APP_SECRET_DEFAULT)

# Warnung beim Import — kein sys.exit() auf Modul-Level (würde FastAPI killen)
if _APP_SECRET == _APP_SECRET_DEFAULT:
    import logging as _log
    _log.getLogger(__name__).warning(
        "⚠️  APP_SECRET ist der Default-Dev-Wert — Credentials sind nur schwach geschützt. "
        "Setze APP_SECRET=$(openssl rand -hex 32) in .env für Produktion."
    )


def verify_app_secret() -> None:
    """
    Prüft ob APP_SECRET sicher gesetzt ist.
    Soll von main.py beim Startup aufgerufen werden — NICHT auf Modul-Level.
    Nur ein kritisches Log — kein sys.exit(), damit der Admin die Logs lesen kann.
    """
    auth_enabled = os.environ.get("AUTH_ENABLED", "false").lower() == "true"
    if auth_enabled and _APP_SECRET == _APP_SECRET_DEFAULT:
        import logging as _log
        _log.getLogger(__name__).critical(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║  SICHERHEITSWARNUNG: APP_SECRET ist der Default-Dev-Wert!  ║\n"
            "║  Alle verschlüsselten Credentials sind unzureichend         ║\n"
            "║  geschützt. Setze in .env:                                   ║\n"
            "║    APP_SECRET=$(openssl rand -hex 32)                        ║\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )
        # Kein sys.exit() — App läuft weiter damit Admin Logs lesen kann


def _get_fernet() -> Fernet:
    key_bytes = hashlib.sha256(_APP_SECRET.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def normalize_coordinate(value: str | None) -> str | None:
    """
    Normalize a coordinate value to decimal format.
    Accepts decimal strings ("46.7994") and DMS strings ("46°47'57.91\"N").
    Returns None if unparseable — never stores corrupt data.
    """
    if not value:
        return value
    value = str(value).strip()

    # Already decimal
    try:
        f = float(value)
        if -180.0 <= f <= 180.0:
            return f"{f:.6f}"
    except ValueError:
        pass

    # DMS pattern: 46°47'57.91"N  or  11°56'3.44"E  or  34°33'47.52"S
    dms = re.compile(
        r"""^\s*(\d+)\s*°\s*(\d+)\s*'\s*([\d.]+)\s*"?\s*([NSEWnsew]?)\s*$""",
        re.VERBOSE,
    )
    m = dms.match(value)
    if m:
        decimal = float(m.group(1)) + float(m.group(2)) / 60.0 + float(m.group(3)) / 3600.0
        if m.group(4).upper() in ("S", "W"):
            decimal = -decimal
        if -180.0 <= decimal <= 180.0:
            return f"{decimal:.6f}"

    return None  # reject unparseable value


def validate_timezone(tz: str | None) -> str | None:
    """
    FIX W2: Validate a timezone string against zoneinfo.available_timezones().
    Returns the timezone if valid, None if unknown (caller decides whether to skip or error).
    Falls back gracefully if zoneinfo is unavailable.
    """
    if not tz:
        return None
    try:
        import zoneinfo
        if tz in zoneinfo.available_timezones():
            return tz
        # Some common aliases not in available_timezones (e.g. "UTC") — try to instantiate
        zoneinfo.ZoneInfo(tz)
        return tz
    except Exception:
        return None


# ── Global settings ───────────────────────────────────────────────────────────

def save_settings_bulk(settings: dict) -> None:
    """Save global settings. Normalizes coordinates and validates timezone."""
    fernet = _get_fernet()
    for key, value in settings.items():
        if key not in GLOBAL_KEYS or value is None:
            continue
        if key in ("home_lat", "home_lon"):
            value = normalize_coordinate(str(value))
            if value is None:
                continue
        if key == "timezone":
            value = validate_timezone(str(value))
            if value is None:
                continue
        save_setting(key, str(value), fernet)


def get_settings_all() -> dict:
    fernet = _get_fernet()
    raw = get_all_settings(fernet)
    return {k: ("••••••••" if k in _MASKED and v else v or "") for k, v in raw.items()}


def get_setting_value(key: str) -> str | None:
    fernet = _get_fernet()
    return get_setting(key, fernet)


# ── Per-user settings ─────────────────────────────────────────────────────────

def save_user_settings_bulk(user_id: int, settings: dict) -> None:
    """Save per-user settings. Normalizes coordinates and validates timezone."""
    fernet = _get_fernet()
    for key, value in settings.items():
        if key not in USER_KEYS or value is None:
            continue
        if key in ("home_lat", "home_lon"):
            value = normalize_coordinate(str(value))
            if value is None:
                continue
        if key == "timezone":
            value = validate_timezone(str(value))
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
    Priority: per-user > global > None.
    Always returns decimal-format coordinates.
    """
    fernet = _get_fernet()
    lat  = get_user_setting(user_id, "home_lat",  fernet) or get_setting("home_lat",  fernet)
    lon  = get_user_setting(user_id, "home_lon",  fernet) or get_setting("home_lon",  fernet)
    name = get_user_setting(user_id, "home_name", fernet) or get_setting("home_name", fernet)
    # Normalize on read — handles legacy DMS data already in DB
    lat = normalize_coordinate(lat)
    lon = normalize_coordinate(lon)
    return lat, lon, name
