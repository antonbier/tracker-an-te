"""
WanderSuite — /api/discovery
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response

import httpx

from auth_jwt import get_current_user
from discovery import discovery_service
from database import discovery_pool_mark_shown, discovery_pool_clear
from settings_manager import get_user_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


def _serialize(s) -> dict:
    """Suggestion → dict. Proxy-URL kommt bereits aus discovery_service._get_image()."""
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
    suggestions = await discovery_service.get_suggestions(user_id, count=count)
    return [_serialize(s) for s in suggestions]


@router.post("/refresh")
async def refresh_suggestions(
    count: int = Query(default=6, ge=1, le=12),
    user: dict = Depends(get_current_user),
):
    """Pool leeren + neu befüllen."""
    user_id = user["id"]
    discovery_pool_clear(user_id)
    await discovery_service.background_refresh_suggestions(user_id, batch=count)
    suggestions = await discovery_service.get_suggestions(user_id, count=count)
    return [_serialize(s) for s in suggestions]


@router.post("/mark-shown")
async def mark_shown(
    destination: str = Query(...),
    user: dict = Depends(get_current_user),
):
    """Suggestion als gesehen markieren."""
    discovery_pool_mark_shown(user["id"], destination)
    return {"ok": True}


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
    user_id = user["id"]
    detail = await discovery_service.get_destination_detail(user_id, destination, country)
    return detail


@router.get("/image-proxy")
async def image_proxy(
    url: str = Query(..., description="Vollständige Bild-URL die proxied werden soll"),
    user: dict = Depends(get_current_user),
):
    """Proxy für Immich- und Unsplash-Bilder — umgeht CORS und Auth-Probleme."""
    user_id = user["id"] or 1  # guest (id=0) → settings unter user_id=1
    immich_url = (get_user_setting_value(user_id, "immich_url") or "").strip().rstrip("/")

    is_immich = bool(immich_url) and url.startswith(immich_url)

    # Nur Immich durch Proxy — Unsplash-CDN akzeptiert nur Browser-Requests direkt
    # discovery.py gibt Unsplash-URLs bereits ungeproxied zurück
    if not is_immich:
        logger.warning(f"[Proxy] Blockierte URL (nicht Immich): {url}")
        raise HTTPException(403, "URL nicht erlaubt")

    headers = {"User-Agent": "WanderSuite/1.0"}
    if is_immich:
        immich_key = (get_user_setting_value(user_id, "immich_api_key") or "").strip()
        if immich_key:
            headers["x-api-key"] = immich_key

    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True, trust_env=False) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(resp.status_code, "Bildquelle Fehler")
            content_type = resp.headers.get("content-type", "image/jpeg")
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except httpx.TimeoutException:
        raise HTTPException(504, "Proxy Timeout")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Proxy] Fehler: {e}")
        raise HTTPException(502, str(e))


@router.get("/debug-image")
async def debug_image(
    destination: str = Query(default="Meran"),
    user_id: int = Query(default=1),
):
    """Debug: no auth required."""
    from settings_manager import get_user_setting_value as _gv
    unsplash_key = (_gv(user_id, "unsplash_key") or "").strip()
    immich_key   = (_gv(user_id, "immich_api_key") or "").strip()
    immich_url   = (_gv(user_id, "immich_url") or "").strip()
    image_url, image_source = await discovery_service.get_trip_image(user_id, destination)
    return {
        "destination":      destination,
        "user_id":          user_id,
        "has_unsplash_key": bool(unsplash_key),
        "has_immich_key":   bool(immich_key),
        "has_immich_url":   bool(immich_url),
        "image_url":        image_url,
        "image_source":     image_source,
    }
