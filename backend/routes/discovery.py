"""
WanderSuite — /api/discovery

GET /api/discovery/suggestions?count=3
    Personalisierte Reiseziel-Vorschläge via DiscoveryService.
    Cached 30 Minuten pro user_id (in-memory dict).

GET /api/discovery/trip-image?destination=X
    Nur Bild-Pipeline (kein LLM) — für HeroSection Nostalgie-Bild.
"""

import time
import logging
from fastapi import APIRouter, Depends, Query
from typing import Optional

from auth_jwt import get_current_user
from discovery import discovery_service, Suggestion

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Simple in-memory cache: {user_id: {"ts": float, "data": list}} ────────────
_cache: dict[int, dict] = {}
_CACHE_TTL = 30 * 60  # 30 Minuten


def _get_cached(user_id: int) -> Optional[list]:
    entry = _cache.get(user_id)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        return entry["data"]
    return None


def _set_cached(user_id: int, data: list) -> None:
    _cache[user_id] = {"ts": time.time(), "data": data}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/suggestions")
async def get_suggestions(
    count: int = Query(default=3, ge=1, le=6),
    user: dict = Depends(get_current_user),
):
    """Return personalized travel suggestions (cached 30 min per user)."""
    user_id = user["id"]

    cached = _get_cached(user_id)
    if cached is not None:
        logger.info(f"[Discovery] Cache hit for user={user_id}")
        return cached

    logger.info(f"[Discovery] Fetching suggestions for user={user_id} count={count}")
    suggestions = await discovery_service.get_suggestions(user_id, count=count)

    result = [
        {
            "destination":  s.destination,
            "reason":       s.reason,
            "image_url":    s.image_url,
            "image_source": s.image_source,
            "prefill":      s.prefill,
        }
        for s in suggestions
    ]

    _set_cached(user_id, result)
    return result


@router.post("/refresh")
async def refresh_suggestions(
    count: int = Query(default=3, ge=1, le=6),
    user: dict = Depends(get_current_user),
):
    """Clear cache + fetch fresh suggestions."""
    user_id = user["id"]
    _cache.pop(user_id, None)
    logger.info(f"[Discovery] Cache cleared for user={user_id}, fetching fresh")
    suggestions = await discovery_service.get_suggestions(user_id, count=count)
    result = [
        {
            "destination":  s.destination,
            "reason":       s.reason,
            "image_url":    s.image_url,
            "image_source": s.image_source,
            "prefill":      s.prefill,
        }
        for s in suggestions
    ]
    _set_cached(user_id, result)
    return result


@router.get("/trip-image")
async def get_trip_image(
    destination: str = Query(..., description="Stadtname oder Region"),
    user: dict = Depends(get_current_user),
):
    """Bild-Pipeline ohne LLM — Immich → Unsplash → css_fallback."""
    user_id = user["id"]
    image_url, image_source = await discovery_service.get_trip_image(user_id, destination)
    return {"image_url": image_url, "image_source": image_source}
