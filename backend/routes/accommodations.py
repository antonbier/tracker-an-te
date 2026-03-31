"""
WanderSuite — /api/accommodations (Multi-User)
Homair + Booking/Trivago trackers.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime

from database import (
    create_homair_tracker, list_homair_trackers, get_homair_tracker,
    delete_homair_tracker, save_homair_snapshot,
    create_booking_tracker, list_booking_trackers, get_booking_tracker,
    delete_booking_tracker, save_booking_snapshot,
)
from homair_scraper import scrape_homair
from booking_scraper import scrape_booking
from settings_manager import get_setting_value
from auth_jwt import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def _uid(user: dict) -> int | None:
    uid = user.get("id", 0)
    return uid if uid else None

def _uid_w(user: dict) -> int:
    return user.get("id", 1) or 1


# ── Homair ────────────────────────────────────────────────────────────────────

class HomairCreate(BaseModel):
    region:             str
    accommodation_type: str = "mobilheim-standard"
    checkin_date:       str
    checkout_date:      str
    adults:             int = 2
    children:           int = 0


@router.get("/homair")
def list_homair(user: dict = Depends(get_current_user)):
    return list_homair_trackers(user_id=_uid(user))


@router.post("/homair", status_code=201)
def create_homair(data: HomairCreate, user: dict = Depends(get_current_user)):
    tid = create_homair_tracker(data.model_dump(), user_id=_uid_w(user))
    return {"id": tid, "message": "Homair Tracker angelegt"}


@router.delete("/homair/{tracker_id}")
def delete_homair(tracker_id: int, user: dict = Depends(get_current_user)):
    if not delete_homair_tracker(tracker_id, user_id=_uid(user)):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Gelöscht"}


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
        result["fetched_at"] = datetime.utcnow().isoformat()
        save_homair_snapshot(tracker_id, result)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Booking ───────────────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    destination:  str
    checkin_date: str
    checkout_date: str
    adults:       int = 2
    rooms:        int = 1
    source:       str = "booking"


@router.get("/booking")
def list_booking(user: dict = Depends(get_current_user)):
    return list_booking_trackers(user_id=_uid(user))


@router.post("/booking", status_code=201)
def create_booking(data: BookingCreate, user: dict = Depends(get_current_user)):
    tid = create_booking_tracker(data.model_dump(), user_id=_uid_w(user))
    return {"id": tid, "message": "Booking Tracker angelegt"}


@router.delete("/booking/{tracker_id}")
def delete_booking(tracker_id: int, user: dict = Depends(get_current_user)):
    if not delete_booking_tracker(tracker_id, user_id=_uid(user)):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Gelöscht"}


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
        result["fetched_at"] = datetime.utcnow().isoformat()
        save_booking_snapshot(tracker_id, result)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))
