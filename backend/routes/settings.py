"""
WanderSuite — /api/settings (Multi-User)

Global (admin): GET/POST /api/settings
Per-user:       GET/POST /api/settings/user
Geocode:        GET /api/settings/geocode?q=... (backend proxy for Nominatim)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
import requests, logging

from database import get_provider_configs, save_provider_config
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
    date_format:        Optional[str] = None  # NEW
    telegram_bot_token: Optional[str] = None
    telegram_chat_id:   Optional[str] = None
    gotify_url:         Optional[str] = None
    gotify_token:       Optional[str] = None
    language:           Optional[str] = None


class UserSettingsPayload(BaseModel):
    # ── Bestehende Felder ────────────────────────────────────────────────
    dawarich_url:      Optional[str] = None
    dawarich_token:    Optional[str] = None
    actual_url:        Optional[str] = None
    actual_token:      Optional[str] = None
    actual_file:       Optional[str] = None
    home_lat:          Optional[str] = None
    home_lon:          Optional[str] = None
    travel_categories: Optional[str] = None
    timezone:          Optional[str] = None
    date_format:       Optional[str] = None
    # ── Immich ───────────────────────────────────────────────────────────
    immich_url:      Optional[str]  = None
    immich_api_key:  Optional[str]  = None
    immich_geo_sync: Optional[bool] = None
    # ── WanderWizzard Defaults ────────────────────────────────────────
    ww_adults:       Optional[int]  = None
    ww_children:     Optional[int]  = None
    ww_home_airport: Optional[str]  = None
    ww_lug_s10:      Optional[int]  = None
    ww_lug_s20:      Optional[int]  = None
    ww_lug_s23:      Optional[int]  = None
    ww_lug_l10:      Optional[int]  = None
    ww_lug_l20:      Optional[int]  = None
    ww_lug_l23:      Optional[int]  = None
    ww_dep_min:      Optional[str]  = None
    ww_dep_max:      Optional[str]  = None
    ww_arr_min:      Optional[str]  = None
    ww_arr_max:      Optional[str]  = None


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
    """Save per-user settings including Immich + WanderWizzard defaults."""
    raw = data.model_dump()
    payload = {}
    for k, v in raw.items():
        if v is None:
            continue
        # Bool → "true"/"false" for consistent TEXT storage
        payload[k] = "true" if v is True else "false" if v is False else str(v)
    save_user_settings_bulk(user["id"], payload)
    logger.info(f"[SETTINGS/USER] updated user={user.get('id')} fields={list(payload.keys())}")
    return {"message": "Gespeichert", "updated": list(payload.keys())}


# ── Geocoding proxy (Nominatim via backend — avoids CORS/HTTPS issues) ────────

@router.get("/geocode")
def geocode_place(
    q: str = Query(..., description="Ortsname für Geocoding"),
    user: dict = Depends(get_current_user),
):
    """Backend proxy for Nominatim geocoding — avoids browser CORS restrictions."""
    if not q or len(q.strip()) < 2:
        raise HTTPException(400, "Query zu kurz")
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q.strip(), "format": "json", "limit": 3},
            headers={
                "User-Agent": "WanderSuite/1.0 (self-hosted travel tracker; contact=admin)",
                "Accept-Language": "de",
            },
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return {"results": []}
        return {
            "results": [
                {
                    "lat": r["lat"],
                    "lon": r["lon"],
                    "display_name": r.get("display_name", ""),
                }
                for r in results[:3]
            ]
        }
    except requests.RequestException as e:
        logger.warning(f"Geocoding error: {e}")
        raise HTTPException(503, f"Geocoding nicht erreichbar: {e}")



# ── Provider configs (flight search provider management) ──────────────────

class ProviderConfigItem(BaseModel):
    name:      str
    enabled:   bool
    api_key:   Optional[str] = None
    test_mode: bool = False


class ProviderConfigsPayload(BaseModel):
    providers: list[ProviderConfigItem]


_PROVIDER_LABELS = {
    "ryanair_native": {"label": "Ryanair (Native)",  "icon": "🟠", "key_required": False},
    "google_flights":  {"label": "Google Flights",    "icon": "🔵", "key_required": True},
    "kiwi":            {"label": "Kiwi Tequila",      "icon": "🟢", "key_required": True},
    "duffel":          {"label": "Duffel",            "icon": "🟣", "key_required": True},
}


@router.get("/providers")
def get_providers(user: dict = Depends(get_current_user)):
    """Return all provider configs with labels for UI rendering."""
    configs = get_provider_configs()
    result = []
    for cfg in configs:
        meta = _PROVIDER_LABELS.get(cfg["name"], {"label": cfg["name"], "icon": "⚙️", "key_required": True})
        result.append({
            "name":         cfg["name"],
            "label":        meta["label"],
            "icon":         meta["icon"],
            "key_required": meta["key_required"],
            "enabled":      bool(cfg["enabled"]),
            "has_key":      bool(cfg.get("api_key")),
            "test_mode":    bool(cfg["test_mode"]),
        })
    return result


@router.put("/providers")
def update_providers(data: ProviderConfigsPayload, user: dict = Depends(get_current_user)):
    """Update enabled state, api_key and test_mode per provider."""
    for item in data.providers:
        save_provider_config(
            name=item.name,
            enabled=item.enabled,
            api_key=item.api_key,
            test_mode=item.test_mode,
        )
    logger.info(f"[SETTINGS] providers updated by user={user.get('id')} | {[p.name for p in data.providers]}")
    return {"message": "Provider-Einstellungen gespeichert", "updated": len(data.providers)}


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

