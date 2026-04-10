"""
WanderSuite — /api/discovery
"""

import time
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException

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


def _proxy_url(image_url: str | None, image_source: str) -> tuple:
    """Wrap Immich URLs through our proxy endpoint to avoid CORS issues."""
    if image_source == "immich_proxy" and image_url:
        from urllib.parse import quote
        proxied = f"/api/discovery/image-proxy?url={quote(image_url, safe='')}"
        return proxied, "immich"
    return image_url, image_source


def _serialize(s) -> dict:
    url, src = _proxy_url(s.image_url, s.image_source)
    return {
        "destination":  s.destination,
        "reason":       s.reason,
        "image_url":    url,
        "image_source": src,
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
    url, src = _proxy_url(image_url, image_source)
    return {"image_url": url, "image_source": src}


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
):
    """Proxy für Immich- und Unsplash-Bilder — umgeht CORS und Auth-Probleme."""
    import httpx as _httpx
    from fastapi.responses import Response as _Response
    from settings_manager import get_user_setting_value as _get_val

    user_id = 1
    
    # 1. Validierung: Was darf durch den Proxy?
    immich_url = (_get_val(user_id, "immich_url") or "").strip().rstrip("/")
    
    is_immich = immich_url and url.startswith(immich_url)
    is_unsplash = "unsplash.com" in url
    
    if not is_immich and not is_unsplash:
        logger.warning(f"[Proxy] Blockierte URL: {url}")
        raise HTTPException(403, "URL nicht erlaubt")

    # 2. Header vorbereiten
    headers = {
        "User-Agent": "WanderSuite/1.0"
    }
    
    # Nur wenn es Immich ist, schicken wir den Key mit
    if is_immich:
        immich_key = (_get_val(user_id, "immich_api_key") or "").strip()
        if immich_key:
            headers["x-api-key"] = immich_key

    # 3. Bild abrufen und ausliefern
    try:
        async with _httpx.AsyncClient(timeout=10.0, follow_redirects=True, trust_env=False) as client:
            resp = await client.get(url, headers=headers)
            
            if resp.status_code != 200:
                logger.error(f"[Proxy] Fehler beim Abruf ({resp.status_code}) für: {url}")
                raise HTTPException(resp.status_code, "Bildquelle Fehler")
                
            content_type = resp.headers.get("content-type", "image/jpeg")
            return _Response(
                content=resp.content, 
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=86400"} # 24h Cache für Bilder
            )
            
    except _httpx.TimeoutException:
        raise HTTPException(504, "Proxy Timeout")
    except Exception as e:
        logger.error(f"[Proxy] Systemfehler: {e}")
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
