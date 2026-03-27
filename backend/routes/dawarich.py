"""
WanderSuite — REST Routes: /api/dawarich
Trip Sync + Reisetagebuch.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from dawarich import sync_trips
from database import list_detected_trips, delete_detected_trip
from settings_manager import get_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


class SyncRequest(BaseModel):
    dawarich_url:   Optional[str] = None
    dawarich_token: Optional[str] = None
    home_lat:       Optional[float] = None
    home_lon:       Optional[float] = None
    start_date:     Optional[str] = None  # YYYY-MM-DD
    end_date:       Optional[str] = None


@router.post("/sync")
def sync(data: SyncRequest):
    """
    Dawarich Sync ausführen.
    Verwendet Server-Settings falls keine Parameter angegeben.
    """
    url   = data.dawarich_url   or get_setting_value("dawarich_url")   or ""
    token = data.dawarich_token or get_setting_value("dawarich_token") or ""

    if not url or not token:
        raise HTTPException(400, "Dawarich URL und Token fehlen — in den Einstellungen eintragen")

    # Home-Koordinaten
    try:
        lat = data.home_lat or float(get_setting_value("home_lat") or 0)
        lon = data.home_lon or float(get_setting_value("home_lon") or 0)
    except (ValueError, TypeError):
        raise HTTPException(400, "Ungültige Home-Koordinaten — Format: 46.7987,11.7188")

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


@router.get("/trips")
def get_trips(limit: int = 50):
    """Alle erkannten Trips aus der DB abrufen."""
    return list_detected_trips(limit=limit)


@router.delete("/trips/{trip_id}")
def delete_trip(trip_id: int):
    if not delete_detected_trip(trip_id):
        raise HTTPException(404, "Trip nicht gefunden")
    return {"message": "Trip gelöscht"}
