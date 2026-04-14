"""
WanderSuite — /api/accommodations (Multi-User)
Homair + Booking trackers. List endpoints include latest_snapshot.
Scrape endpoints: nur bei status=ok speichern — Fehler überschreiben niemals die Historie.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime

from database import (
    create_homair_tracker, list_homair_trackers, get_homair_tracker,
    delete_homair_tracker, save_homair_snapshot, get_latest_homair_snapshot,
    create_booking_tracker, list_booking_trackers, get_booking_tracker,
    delete_booking_tracker, save_booking_snapshot, get_latest_booking_snapshot,
    link_tracker_to_trip,
)
from homair_scraper import fetch_homair as scrape_homair
from booking_scraper import fetch_booking as scrape_booking
from settings_manager import get_setting_value
router = APIRouter()
logger = logging.getLogger(__name__)


def _uid(user: dict) -> int | None:
    uid = user.get("id", 0)
    return uid if uid else None

def _uid_w(user: dict) -> int:
    return user.get("id", 1) or 1


# ── Homair ─────────────────────────────────────────────────────────────────

class HomairCreate(BaseModel):
    region:             str
    accommodation_type: str = "mobilheim"
    checkin_date:       str
    checkout_date:      str
    adults:             int = 2
    children:           int = 0
    bedrooms:           str = "1"
    aircon:             bool = False
    pets:               bool = False
    covered_terrace:    bool = False
    campsite_name:      Optional[str] = None
    initial_price:      Optional[float] = None


@router.get("/homair")
def list_homair(user: dict = Depends(get_current_user)):
    trackers = list_homair_trackers(user_id=_uid(user))
    for t in trackers:
        t["latest_snapshot"] = get_latest_homair_snapshot(t["id"])
    return trackers


@router.post("/homair", status_code=201)
def create_homair(data: HomairCreate, user: dict = Depends(get_current_user)):
    tid = create_homair_tracker(data.model_dump(), user_id=_uid_w(user))
    if data.initial_price is not None:
        save_homair_snapshot(tid, {
            "total_price": data.initial_price,
            "currency": "EUR",
            "status": "ok",
            "note": f"Initialpreis aus Suchergebnis ({data.campsite_name or data.region})",
        })
    return {"id": tid, "message": "Homair Tracker angelegt"}


@router.delete("/homair/{tracker_id}")
def delete_homair(tracker_id: int, user: dict = Depends(get_current_user)):
    if not delete_homair_tracker(tracker_id, user_id=_uid(user)):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Geloescht"}


@router.post("/homair/{tracker_id}/scrape")
def scrape_homair_tracker(tracker_id: int, user: dict = Depends(get_current_user)):
    t = get_homair_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, "Tracker nicht gefunden")
    api_key = get_setting_value("serpapi_key")
    if not api_key:
        raise HTTPException(400, "SerpAPI Key nicht konfiguriert")
    try:
        result = scrape_homair(t, api_key)
        status = result.get("status", "error")
        snap = result.get("snapshot", result)
        snap["fetched_at"] = datetime.utcnow().isoformat()

        if status == "ok" and snap.get("total_price") is not None:
            # Nur bei Erfolg speichern — Fehler überschreiben niemals die Historie
            save_homair_snapshot(tracker_id, snap)
            logger.info(f"[Homair] ✅ #{tracker_id} ok | price={snap.get('total_price')}")
        else:
            err = snap.get("error_message", "Unbekannter Fehler")
            logger.warning(
                f"[Homair] ⚠️ #{tracker_id} fehlgeschlagen ({status}): {err} — Historie bleibt erhalten"
            )
            raise HTTPException(422, detail={"status": status, "error": err})

        return snap
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Booking ────────────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    destination:   str
    checkin_date:  str
    checkout_date: str
    adults:        int = 2
    rooms:         int = 1
    source:        str = "booking"
    hotel_name:    Optional[str] = None
    initial_price: Optional[float] = None


@router.get("/booking")
def list_booking(user: dict = Depends(get_current_user)):
    trackers = list_booking_trackers(user_id=_uid(user))
    for t in trackers:
        t["latest_snapshot"] = get_latest_booking_snapshot(t["id"])
    return trackers


@router.post("/booking", status_code=201)
def create_booking(data: BookingCreate, user: dict = Depends(get_current_user)):
    tid = create_booking_tracker(data.model_dump(), user_id=_uid_w(user))
    if data.initial_price is not None:
        save_booking_snapshot(tid, {
            "total_price": data.initial_price,
            "hotel_name": data.hotel_name or data.destination,
            "currency": "EUR",
            "status": "ok",
        })
    return {"id": tid, "message": "Booking Tracker angelegt"}


@router.delete("/booking/{tracker_id}")
def delete_booking(tracker_id: int, user: dict = Depends(get_current_user)):
    if not delete_booking_tracker(tracker_id, user_id=_uid(user)):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Geloescht"}


@router.post("/booking/{tracker_id}/scrape")
def scrape_booking_tracker(tracker_id: int, user: dict = Depends(get_current_user)):
    t = get_booking_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, "Tracker nicht gefunden")
    api_key = get_setting_value("serpapi_key")
    if not api_key:
        raise HTTPException(400, "SerpAPI Key nicht konfiguriert")
    try:
        result = scrape_booking(t, api_key)
        status = result.get("status", "error")
        snap = result.get("snapshot", result)
        snap["fetched_at"] = datetime.utcnow().isoformat()

        if status == "ok" and snap.get("total_price") is not None:
            # Nur bei Erfolg speichern — Fehler überschreiben niemals die Historie
            save_booking_snapshot(tracker_id, snap)
            logger.info(f"[Booking] ✅ #{tracker_id} ok | price={snap.get('total_price')}")
        else:
            err = snap.get("error_message", "Unbekannter Fehler")
            logger.warning(
                f"[Booking] ⚠️ #{tracker_id} fehlgeschlagen ({status}): {err} — Historie bleibt erhalten"
            )
            raise HTTPException(422, detail={"status": status, "error": err})

        return snap
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


class AccomTripLinkPayload(BaseModel):
    trip_id: Optional[int] = None

@router.patch("/homair/{tracker_id}/link-trip")
def link_homair_trip(tracker_id: int, data: AccomTripLinkPayload, user: dict = Depends(get_current_user)):
    ok = link_tracker_to_trip(tracker_id, "camping", data.trip_id)
    return {"ok": ok, "trip_id": data.trip_id}

@router.patch("/booking/{tracker_id}/link-trip")
def link_booking_trip(tracker_id: int, data: AccomTripLinkPayload, user: dict = Depends(get_current_user)):
    ok = link_tracker_to_trip(tracker_id, "hotel", data.trip_id)
    return {"ok": ok, "trip_id": data.trip_id}
