"""
WanderSuite — /api/dawarich (Multi-User)
Each user has their own Dawarich config + detected trips.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging, math

from dawarich import sync_trips, fetch_points, normalize_point
from database import list_detected_trips, delete_detected_trip, save_detected_trip
from settings_manager import get_user_setting_value, get_setting_value
from countries import get_visited_country_codes
from auth_jwt import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class SyncRequest(BaseModel):
    dawarich_url:   Optional[str] = None
    dawarich_token: Optional[str] = None
    home_lat:       Optional[float] = None
    home_lon:       Optional[float] = None
    start_date:     Optional[str] = None
    end_date:       Optional[str] = None


def _uid(user: dict) -> int | None:
    uid = user.get("id", 0)
    return uid if uid else None


@router.post("/sync")
def sync(data: SyncRequest, user: dict = Depends(get_current_user)):
    uid = user.get("id", 1) or 1

    # Per-user settings take priority, fall back to global
    url   = data.dawarich_url   or get_user_setting_value(uid, "dawarich_url")   or get_setting_value("dawarich_url")   or ""
    token = data.dawarich_token or get_user_setting_value(uid, "dawarich_token") or get_setting_value("dawarich_token") or ""

    if not url or not token:
        raise HTTPException(400, "Dawarich URL und Token fehlen — in Einstellungen → Mein Bereich konfigurieren")

    try:
        lat = data.home_lat
        lon = data.home_lon
        if lat is None or lon is None:
            lat = float(get_user_setting_value(uid, "home_lat") or get_setting_value("home_lat") or 0)
            lon = float(get_user_setting_value(uid, "home_lon") or get_setting_value("home_lon") or 0)
    except (ValueError, TypeError):
        raise HTTPException(400, "Ungültige Home-Koordinaten")

    if math.isnan(lat) or math.isnan(lon) or (lat == 0 and lon == 0):
        raise HTTPException(400, "Home-Koordinaten fehlen — in Einstellungen → Mein Bereich eintragen")

    result = sync_trips(
        base_url=url, token=token, home_lat=lat, home_lon=lon,
        start_date=data.start_date, end_date=data.end_date,
        user_id=uid,
    )

    if "error" in result:
        raise HTTPException(400, result["error"])
    result.setdefault("trips_saved", 0)
    return result


@router.get("/trips")
def get_trips(limit: int = 50, user: dict = Depends(get_current_user)):
    return list_detected_trips(limit=limit, user_id=_uid(user))


@router.get("/countries")
def get_countries(user: dict = Depends(get_current_user)):
    return get_visited_country_codes(user_id=_uid(user))


@router.delete("/trips/{trip_id}")
def delete_trip(trip_id: int, user: dict = Depends(get_current_user)):
    if not delete_detected_trip(trip_id, user_id=_uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    return {"message": "Trip gelöscht"}
