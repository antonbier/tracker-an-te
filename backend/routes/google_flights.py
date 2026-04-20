"""
WanderSuite — /api/google-flights (Multi-User)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime

from database import (
    create_gf_tracker, list_gf_trackers, get_gf_tracker,
    delete_gf_tracker, save_gf_snapshot, get_gf_history,
    get_latest_gf_snapshot,
    link_tracker_to_trip,
)
from google_scraper import fetch_google_flights as scrape_google_flights
from settings_manager import get_setting_value
from auth_jwt import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

class GFTrackerCreate(BaseModel):
    origin:        str
    destination:   str
    outbound_date: str
    return_date:   Optional[str] = None
    adults:        int = 1
    children:      int = 0
    baggage:       str = "none"
    baggage_10kg:  int = 0
    baggage_20kg:  int = 0
    baggage_23kg:  int = 0
    seat:          bool = False
    seat_cost:     float = 0.0
    # From search result — for initial snapshot
    initial_price:           Optional[float] = None
    initial_airline:         Optional[str] = None
    initial_dep_time:        Optional[str] = None
    initial_arr_time:        Optional[str] = None
    trip_id:                 Optional[int] = None
    initial_duration:        Optional[int] = None
    initial_stops:           Optional[int] = None
    initial_layover_airports: Optional[list] = None
    initial_layover_durations: Optional[list] = None


def _uid(user: dict) -> int | None:
    uid = user.get("id", 0)
    return uid if uid else None


@router.get("")
def list_trackers(user: dict = Depends(get_current_user)):
    trackers = list_gf_trackers(user_id=_uid(user))
    for t in trackers:
        snap = get_latest_gf_snapshot(t["id"])
        t["latest_snapshot"] = snap
        t["current_price"] = snap.get("total_price") if snap else None
    return trackers


@router.post("", status_code=201)
def create_tracker(data: GFTrackerCreate, user: dict = Depends(get_current_user)):
    uid = user.get("id", 1) or 1
    tid = create_gf_tracker(data.model_dump(), user_id=uid)
    # Save initial snapshot from search result if price was provided
    if data.initial_price is not None:
        save_gf_snapshot(tid, {
            "total_price":       data.initial_price,
            "airline":           data.initial_airline,
            "departure_time":    data.initial_dep_time,
            "arrival_time":      data.initial_arr_time,
            "duration_min":      data.initial_duration,
            "stops":             data.initial_stops or 0,
            "layover_airports":  data.initial_layover_airports or [],
            "layover_durations": data.initial_layover_durations or [],
            "currency":          "EUR",
            "status":            "ok",
        })
    return {"id": tid, "message": "Google Flights Tracker angelegt"}


@router.delete("/{tracker_id}")
def delete_tracker(tracker_id: int, user: dict = Depends(get_current_user)):
    if not delete_gf_tracker(tracker_id, user_id=_uid(user)):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Tracker geloescht"}


@router.get("/{tracker_id}/history")
def get_history(tracker_id: int, user: dict = Depends(get_current_user)):
    t = get_gf_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, "Tracker nicht gefunden")
    return get_gf_history(tracker_id)


@router.post("/{tracker_id}/scrape")
def scrape(tracker_id: int, user: dict = Depends(get_current_user)):
    t = get_gf_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, "Tracker nicht gefunden")
    api_key = get_setting_value("serpapi_key")
    if not api_key:
        raise HTTPException(400, "SerpAPI Key nicht konfiguriert")
    try:
        result = scrape_google_flights(t, api_key)
        status = result.get("status", "error")
        # google_scraper gibt {"status":..., "snapshot":{...}} zurück
        snap = result.get("snapshot", result)
        snap["fetched_at"] = datetime.utcnow().isoformat()

        if status == "ok" and snap.get("total_price") is not None:
            # Nur bei Erfolg speichern — Fehler überschreiben niemals die Historie
            save_gf_snapshot(tracker_id, snap)
            logger.info(f"[GF] ✅ #{tracker_id} scrape ok | price={snap.get('total_price')}")
        else:
            err = snap.get("error_message", "Unbekannter Fehler")
            logger.warning(
                f"[GF] ⚠️ #{tracker_id} scrape fehlgeschlagen ({status}): {err} — Historie bleibt erhalten"
            )
            raise HTTPException(422, detail={"status": status, "error": err})

        return snap
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GF scrape error: {e}")
        raise HTTPException(500, str(e))


class GfTripLinkPayload(BaseModel):
    trip_id: Optional[int] = None

@router.patch("/{tracker_id}/link-trip")
def link_gf_trip(tracker_id: int, data: GfTripLinkPayload, user: dict = Depends(get_current_user)):
    ok = link_tracker_to_trip(tracker_id, "google_flight", data.trip_id)
    return {"ok": ok, "trip_id": data.trip_id}
