"""
WanderSuite — REST Routes: /api/dawarich
Trip Sync + Reisetagebuch + Debug.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from dawarich import sync_trips, fetch_points, normalize_point
from database import list_detected_trips, delete_detected_trip
from settings_manager import get_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


class SyncRequest(BaseModel):
    dawarich_url:   Optional[str] = None
    dawarich_token: Optional[str] = None
    home_lat:       Optional[float] = None
    home_lon:       Optional[float] = None
    start_date:     Optional[str] = None
    end_date:       Optional[str] = None


@router.post("/sync")
def sync(data: SyncRequest):
    url   = data.dawarich_url   or get_setting_value("dawarich_url")   or ""
    token = data.dawarich_token or get_setting_value("dawarich_token") or ""

    if not url or not token:
        raise HTTPException(400, "Dawarich URL und Token fehlen")

    try:
        lat = data.home_lat or float(get_setting_value("home_lat") or 0)
        lon = data.home_lon or float(get_setting_value("home_lon") or 0)
    except (ValueError, TypeError):
        raise HTTPException(400, "Ungültige Home-Koordinaten")

    if lat == 0 and lon == 0:
        raise HTTPException(400, "Home-Koordinaten fehlen — in den Einstellungen eintragen")

    result = sync_trips(
        base_url=url, token=token,
        home_lat=lat, home_lon=lon,
        start_date=data.start_date,
        end_date=data.end_date,
    )

    if "error" in result:
        raise HTTPException(400, result["error"])

    return result


@router.post("/debug")
def debug_points(data: SyncRequest):
    """
    Debug-Endpoint: Zeigt die ersten 5 Roh-Punkte von Dawarich
    und wie sie normalisiert werden — hilft bei Format-Problemen.
    """
    url   = data.dawarich_url   or get_setting_value("dawarich_url")   or ""
    token = data.dawarich_token or get_setting_value("dawarich_token") or ""

    if not url or not token:
        raise HTTPException(400, "Dawarich URL und Token fehlen")

    try:
        # Nur erste Seite laden (schnell)
        raw = fetch_points(url, token, page_size=10)
    except Exception as e:
        raise HTTPException(400, str(e))

    # Zeige Rohformat + Normalisierung
    samples = raw[:5]
    normalized = []
    for p in samples:
        n = normalize_point(p)
        normalized.append({
            "raw_keys":   list(p.keys()),
            "raw_sample": {k: p[k] for k in list(p.keys())[:8]},
            "normalized": n,
        })

    return {
        "total_points": len(raw),
        "samples": normalized,
    }


@router.get("/trips")
def get_trips(limit: int = 50):
    return list_detected_trips(limit=limit)


@router.delete("/trips/{trip_id}")
def delete_trip(trip_id: int):
    if not delete_detected_trip(trip_id):
        raise HTTPException(404, "Trip nicht gefunden")
    return {"message": "Trip gelöscht"}
