"""
WanderSuite — /api/discovery
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response

import httpx

from auth_jwt import get_current_user, get_optional_user
from discovery import discovery_service
from database import discovery_pool_mark_shown, discovery_pool_clear
from settings_manager import get_user_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


def _serialize(s) -> dict:
    return {
        "destination":        s.destination,
        "reason":             s.reason,
        "image_url":          s.image_url,
        "image_source":       s.image_source,
        "prefill":            s.prefill,
        "unsplash_author_name": getattr(s, "unsplash_author_name", None),
        "unsplash_author_url":  getattr(s, "unsplash_author_url",  None),
    }


@router.get("/suggestions")
async def get_suggestions(
    count: int = Query(default=3, ge=1, le=6),
    user: dict = Depends(get_current_user),
):
    try:
        suggestions = await discovery_service.get_suggestions(user["id"], count=count)
        return [_serialize(s) for s in suggestions]
    except RuntimeError as e:
        if "api_rate_limit" in str(e):
            raise HTTPException(429, "API-Limit erreicht. Bitte versuche es später erneut.")
        raise


@router.post("/refresh")
async def refresh_suggestions(
    count: int = Query(default=6, ge=1, le=12),
    user: dict = Depends(get_current_user),
):
    """Pool leeren + neu befüllen."""
    try:
        discovery_pool_clear(user["id"])
        await discovery_service.background_refresh_suggestions(user["id"], batch=count)
        suggestions = await discovery_service.get_suggestions(user["id"], count=count)
        return [_serialize(s) for s in suggestions]
    except RuntimeError as e:
        if "api_rate_limit" in str(e):
            raise HTTPException(429, "API-Limit erreicht. Bitte versuche es später erneut.")
        raise


@router.post("/mark-shown")
async def mark_shown(
    destination: str = Query(...),
    user: dict = Depends(get_current_user),
):
    discovery_pool_mark_shown(user["id"], destination)
    return {"ok": True}


@router.get("/trip-image")
async def get_trip_image(
    destination: str = Query(...),
    user: dict = Depends(get_current_user),
):
    result = await discovery_service.get_trip_image(user["id"], destination)
    image_url    = result[0]
    image_source = result[1]
    author_name  = result[2] if len(result) > 2 else None
    author_url   = result[3] if len(result) > 3 else None
    return {
        "image_url":    image_url,
        "image_source": image_source,
        "author_name":  author_name,
        "author_url":   author_url,
    }


@router.get("/detail")
async def get_destination_detail(
    destination: str = Query(...),
    country: str = Query(default=""),
    user: dict = Depends(get_current_user),
):
    detail = await discovery_service.get_destination_detail(user["id"], destination, country)
    return detail


@router.get("/image-proxy")
async def image_proxy(
    url: str = Query(..., description="Vollständige Bild-URL die proxied werden soll"),
    user: dict = Depends(get_optional_user),
):
    """Proxy für Immich- und Unsplash-Bilder — umgeht CORS und Auth-Probleme."""
    user_id = user["id"] or 1
    immich_url = (get_user_setting_value(user_id, "immich_url") or "").strip().rstrip("/")

    is_immich   = bool(immich_url) and url.startswith(immich_url)
    is_unsplash = "images.unsplash.com" in url or "source.unsplash.com" in url

    if not is_immich and not is_unsplash:
        logger.warning(f"[Proxy] Blockierte URL: {url}")
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

# NOTE: /debug-image endpoint removed — was unauthenticated and exposed key metadata
