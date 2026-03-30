"""
WanderSuite — REST Routes: /api/settings
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import requests
import logging

from settings_manager import save_settings_bulk, get_settings_all, get_setting_value, SETTING_KEYS

router = APIRouter()
logger = logging.getLogger(__name__)


class SettingsPayload(BaseModel):
    serpapi_key:        Optional[str] = None
    gemini_key:         Optional[str] = None
    openai_key:         Optional[str] = None
    dawarich_url:       Optional[str] = None
    dawarich_token:     Optional[str] = None
    actual_url:         Optional[str] = None
    actual_token:       Optional[str] = None
    actual_file:        Optional[str] = None
    llm_provider:       Optional[str] = None
    timezone:           Optional[str] = None
    home_lat:           Optional[str] = None
    home_lon:           Optional[str] = None
    travel_categories:  Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id:   Optional[str] = None
    gotify_url:         Optional[str] = None
    gotify_token:       Optional[str] = None
    language:           Optional[str] = None   # NEW: UI language preference


@router.get("")
def get_settings():
    """Alle Settings abrufen (Keys maskiert, language im Klartext)."""
    return get_settings_all()


@router.post("")
def update_settings(data: SettingsPayload):
    """Settings speichern — None-Werte werden ignoriert."""
    payload = {k: v for k, v in data.model_dump().items() if v is not None and v != ""}
    save_settings_bulk(payload)
    return {"message": "Gespeichert", "updated": list(payload.keys())}


@router.get("/serpapi-quota")
def get_serpapi_quota():
    api_key = get_setting_value("serpapi_key")
    if not api_key:
        return {"error": "SerpAPI Key nicht konfiguriert"}
    try:
        resp = requests.get(
            "https://serpapi.com/account",
            params={"api_key": api_key},
            timeout=10,
        )
        if resp.status_code == 401:
            return {"error": "Ungültiger SerpAPI Key"}
        resp.raise_for_status()
        data = resp.json()
        searches_left  = data.get("plan_searches_left", None)
        total_searches = data.get("plan_monthly_searches", None)
        used = (total_searches - searches_left) if (total_searches and searches_left is not None) else None
        return {
            "used":      used,
            "limit":     total_searches,
            "remaining": searches_left,
            "plan":      data.get("plan_name", "unknown"),
            "account":   data.get("email", ""),
        }
    except requests.RequestException as e:
        logger.warning(f"[SerpAPI] Quota-Abfrage fehlgeschlagen: {e}")
        return {"error": f"SerpAPI nicht erreichbar: {str(e)}"}
