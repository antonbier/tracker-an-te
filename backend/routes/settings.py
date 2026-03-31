"""
WanderSuite — /api/settings (Multi-User)

Global (admin): GET/POST /api/settings
Per-user:       GET/POST /api/settings/user
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import requests, logging

from settings_manager import (
    save_settings_bulk, get_settings_all, get_setting_value,
    save_user_settings_bulk, get_user_settings_all, get_user_setting_value,
    GLOBAL_KEYS, USER_KEYS,
)
from auth_jwt import get_current_user, require_admin

router = APIRouter()
logger = logging.getLogger(__name__)


class GlobalSettingsPayload(BaseModel):
    serpapi_key:        Optional[str] = None
    gemini_key:         Optional[str] = None
    openai_key:         Optional[str] = None
    llm_provider:       Optional[str] = None
    timezone:           Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id:   Optional[str] = None
    gotify_url:         Optional[str] = None
    gotify_token:       Optional[str] = None
    language:           Optional[str] = None


class UserSettingsPayload(BaseModel):
    dawarich_url:      Optional[str] = None
    dawarich_token:    Optional[str] = None
    actual_url:        Optional[str] = None
    actual_token:      Optional[str] = None
    actual_file:       Optional[str] = None
    home_lat:          Optional[str] = None
    home_lon:          Optional[str] = None
    travel_categories: Optional[str] = None


# ── Global settings (admin configures once for all) ───────────────────────────

@router.get("")
def get_global_settings(user: dict = Depends(get_current_user)):
    return get_settings_all()


@router.post("")
def update_global_settings(data: GlobalSettingsPayload, admin: dict = Depends(require_admin)):
    payload = {k: v for k, v in data.model_dump().items() if v is not None and v != ""}
    save_settings_bulk(payload)
    return {"message": "Gespeichert", "updated": list(payload.keys())}


# ── Per-user settings (each user configures their own integrations) ───────────

@router.get("/user")
def get_my_settings(user: dict = Depends(get_current_user)):
    return get_user_settings_all(user["id"])


@router.post("/user")
def update_my_settings(data: UserSettingsPayload, user: dict = Depends(get_current_user)):
    payload = {k: v for k, v in data.model_dump().items() if v is not None and v != ""}
    save_user_settings_bulk(user["id"], payload)
    return {"message": "Gespeichert", "updated": list(payload.keys())}


# ── SerpAPI quota ─────────────────────────────────────────────────────────────

@router.get("/serpapi-quota")
def get_serpapi_quota():
    api_key = get_setting_value("serpapi_key")
    if not api_key:
        return {"error": "SerpAPI Key nicht konfiguriert"}
    try:
        resp = requests.get(
            "https://serpapi.com/account",
            params={"api_key": api_key}, timeout=10,
        )
        if resp.status_code == 401:
            return {"error": "Ungültiger SerpAPI Key"}
        resp.raise_for_status()
        data = resp.json()
        left  = data.get("plan_searches_left")
        total = data.get("plan_monthly_searches")
        used  = (total - left) if (total and left is not None) else None
        return {"used": used, "limit": total, "remaining": left,
                "plan": data.get("plan_name", "unknown"), "account": data.get("email", "")}
    except requests.RequestException as e:
        return {"error": f"SerpAPI nicht erreichbar: {e}"}
