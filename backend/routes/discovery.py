"""
WanderSuite — /api/discovery
"""

import time
import logging
from fastapi import APIRouter, Depends, Query
from typing import Optional

from auth_jwt import get_current_user
from discovery import discovery_service

router = APIRouter()
logger = logging.getLogger(__name__)

_cache: dict[int, dict] = {}
_CACHE_TTL = 30 * 60


def _get_cached(user_id: int) -> Optional[list]:
    entry = _cache.get(user_id)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        return entry["data"]
    return None


def _set_cached(user_id: int, data: list) -> None:
    _cache[user_id] = {"ts": time.time(), "data": data}


def _serialize(s) -> dict:
    return {
        "destination":  s.destination,
        "reason":       s.reason,
        "image_url":    s.image_url,
        "image_source": s.image_source,
        "prefill":      s.prefill,
    }


@router.get("/suggestions")
async def get_suggestions(
    count: int = Query(default=3, ge=1, le=6),
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    cached = _get_cached(user_id)
    if cached is not None:
        return cached
    suggestions = await discovery_service.get_suggestions(user_id, count=count)
    result = [_serialize(s) for s in suggestions]
    _set_cached(user_id, result)
    return result


@router.post("/refresh")
async def refresh_suggestions(
    count: int = Query(default=3, ge=1, le=6),
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    _cache.pop(user_id, None)
    suggestions = await discovery_service.get_suggestions(user_id, count=count)
    result = [_serialize(s) for s in suggestions]
    _set_cached(user_id, result)
    return result


@router.get("/trip-image")
async def get_trip_image(
    destination: str = Query(...),
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]
    image_url, image_source = await discovery_service.get_trip_image(user_id, destination)
    return {"image_url": image_url, "image_source": image_source}


@router.get("/detail")
async def get_destination_detail(
    destination: str = Query(...),
    country: str = Query(default=""),
    user: dict = Depends(get_current_user),
):
    """Full detail for a destination: LLM description + things-to-do + multiple images."""
    user_id = user["id"]
    detail = await discovery_service.get_destination_detail(user_id, destination, country)
    return detail


@router.get("/image-proxy")
async def image_proxy(
    url: str = Query(..., description="Vollständige Bild-URL die proxied werden soll"),
    user: dict = Depends(get_current_user),
):
    """Proxy für Immich-Bilder — umgeht CORS und Auth-Probleme im Browser."""
    import httpx as _httpx
    from fastapi.responses import Response as _Response
    from settings_manager import get_user_setting_value as _get_val

    user_id = user["id"]
    # Only proxy URLs from the user's own Immich instance for security
    immich_url = (get_user_setting_value(user_id, "immich_url") or "").strip().rstrip("/")
    immich_key = (get_user_setting_value(user_id, "immich_api_key") or "").strip()

    if not immich_url or not url.startswith(immich_url):
        raise HTTPException(403, "URL nicht erlaubt")

    try:
        async with _httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"x-api-key": immich_key})
            if resp.status_code != 200:
                raise HTTPException(resp.status_code, "Immich Fehler")
            content_type = resp.headers.get("content-type", "image/jpeg")
            return _Response(content=resp.content, media_type=content_type,
                             headers={"Cache-Control": "public, max-age=3600"})
    except _httpx.TimeoutException:
        raise HTTPException(504, "Immich Timeout")
    except Exception as e:
        raise HTTPException(502, str(e))


@router.get("/debug-image")
async def debug_image(
    destination: str = Query(default="Meran"),
    user_id: int = Query(default=1),
):
    """Debug: no auth required. Check which image provider works."""
    from settings_manager import get_user_setting_value
    unsplash_key = (get_user_setting_value(user_id, "unsplash_key") or "").strip()
    immich_key   = (get_user_setting_value(user_id, "immich_api_key") or "").strip()
    immich_url   = (get_user_setting_value(user_id, "immich_url") or "").strip()
    image_url, image_source = await discovery_service.get_trip_image(user_id, destination)
    return {
        "destination":      destination,
        "user_id":          user_id,
        "has_unsplash_key": bool(unsplash_key),
        "unsplash_key_len": len(unsplash_key),
        "has_immich_key":   bool(immich_key),
        "has_immich_url":   bool(immich_url),
        "immich_url_val":   immich_url or "(leer)",
        "image_url":        image_url,
        "image_source":     image_source,
    }
