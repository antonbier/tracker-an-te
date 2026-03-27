"""
WanderSuite v1.0 — REST Routes: /api/settings
Verschlüsselte API Key Verwaltung.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from settings_manager import save_settings_bulk, get_settings_all, get_setting_value

router = APIRouter()


class SettingsPayload(BaseModel):
    serpapi_key:        Optional[str] = None
    gemini_key:         Optional[str] = None
    openai_key:         Optional[str] = None
    dawarich_url:       Optional[str] = None
    dawarich_token:     Optional[str] = None
    actual_url:         Optional[str] = None
    actual_token:       Optional[str] = None
    llm_provider:       Optional[str] = None
    timezone:           Optional[str] = None
    home_lat:           Optional[str] = None
    home_lon:           Optional[str] = None
    travel_categories:  Optional[str] = None


@router.get("")
def get_settings():
    """Alle Settings abrufen (Keys maskiert)."""
    return get_settings_all()


@router.post("")
def update_settings(data: SettingsPayload):
    """Settings speichern — leere Strings werden ignoriert."""
    payload = {k: v for k, v in data.model_dump().items() if v}
    save_settings_bulk(payload)
    return {"message": "Gespeichert", "updated": list(payload.keys())}
