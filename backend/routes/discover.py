"""
WanderSuite v1.0 — REST Routes: /api/discover
AI-Reiseempfehlungen via Gemini oder OpenAI.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging

from gemini import generate_travel_recommendations as gemini_recs
from openai_client import generate_travel_recommendations as openai_recs
from settings_manager import get_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


class DiscoverRequest(BaseModel):
    query:          str
    lang:           str = "de"
    provider:       str = "gemini"   # gemini | openai
    exclude_places: Optional[list[str]] = None
    # Optional: Frontend kann Keys mitschicken (Fallback zu Server-Settings)
    api_key:        Optional[str] = None


@router.post("")
def get_recommendations(data: DiscoverRequest):
    if not data.query.strip():
        return {"error": "Bitte beschreibe was du suchst"}

    # API Key: Frontend-Angabe oder Server-Setting
    if data.provider == "openai":
        key = data.api_key or get_setting_value("openai_key") or ""
        if not key:
            return {"error": "OpenAI API Key fehlt — in den Einstellungen eintragen"}
        return openai_recs(query=data.query, api_key=key, exclude_places=data.exclude_places or [], lang=data.lang)
    else:
        key = data.api_key or get_setting_value("gemini_key") or ""
        if not key:
            return {"error": "Gemini API Key fehlt — in den Einstellungen eintragen"}
        return gemini_recs(query=data.query, api_key=key, exclude_places=data.exclude_places or [], lang=data.lang)
