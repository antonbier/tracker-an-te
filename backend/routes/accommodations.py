"""
WanderSuite v0.6 — REST Routes: /api/accommodations
Homair + Booking/Trivago Tracker.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import os

from homair_scraper import fetch_homair
from booking_scraper import fetch_booking

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory stores (v0.7 → SQLite)
_homair_trackers: list[dict] = []
_booking_trackers: list[dict] = []
_homair_id = 1
_booking_id = 1


# ── Homair ────────────────────────────────────────────

class HomairTrackerCreate(BaseModel):
    region:             str = "cote-d-azur"
    accommodation_type: str = "mobilheim-standard"
    checkin_date:       str
    checkout_date:      str
    adults:             int = 2
    children:           int = 0


@router.get("/homair")
def list_homair():
    return _homair_trackers


@router.post("/homair", status_code=201)
def add_homair(data: HomairTrackerCreate):
    global _homair_id
    tracker = {
        "id": _homair_id, **data.model_dump(),
        "latest_snapshot": None, "history": []
    }
    _homair_trackers.append(tracker)
    _homair_id += 1
    return {"id": tracker["id"], "message": "Homair Tracker angelegt"}


@router.delete("/homair/{tracker_id}")
def delete_homair(tracker_id: int):
    global _homair_trackers
    before = len(_homair_trackers)
    _homair_trackers = [t for t in _homair_trackers if t["id"] != tracker_id]
    if len(_homair_trackers) == before:
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Tracker gelöscht"}


@router.post("/homair/{tracker_id}/scrape")
def scrape_homair(tracker_id: int):
    tracker = next((t for t in _homair_trackers if t["id"] == tracker_id), None)
    if not tracker:
        raise HTTPException(404, "Tracker nicht gefunden")
    result = fetch_homair(tracker)
    snap = result["snapshot"]
    tracker["latest_snapshot"] = snap
    tracker["history"].append(snap)
    return {"message": "Scraping abgeschlossen", "snapshot": snap}


# ── Booking ───────────────────────────────────────────

class BookingTrackerCreate(BaseModel):
    destination:  str
    checkin_date:  str
    checkout_date: str
    adults:        int = 2
    rooms:         int = 1
    source:        str = "booking"  # booking | trivago


@router.get("/booking")
def list_booking():
    return _booking_trackers


@router.post("/booking", status_code=201)
def add_booking(data: BookingTrackerCreate):
    global _booking_id
    tracker = {
        "id": _booking_id, **data.model_dump(),
        "latest_snapshot": None, "history": []
    }
    _booking_trackers.append(tracker)
    _booking_id += 1
    return {"id": tracker["id"], "message": "Booking Tracker angelegt"}


@router.delete("/booking/{tracker_id}")
def delete_booking(tracker_id: int):
    global _booking_trackers
    before = len(_booking_trackers)
    _booking_trackers = [t for t in _booking_trackers if t["id"] != tracker_id]
    if len(_booking_trackers) == before:
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Tracker gelöscht"}


@router.post("/booking/{tracker_id}/scrape")
def scrape_booking(tracker_id: int, api_key: str = ""):
    tracker = next((t for t in _booking_trackers if t["id"] == tracker_id), None)
    if not tracker:
        raise HTTPException(404, "Tracker nicht gefunden")
    key = api_key or os.environ.get("SERPAPI_KEY", "")
    if not key:
        raise HTTPException(400, "SerpAPI Key fehlt")
    result = fetch_booking(tracker, key)
    snap = result["snapshot"]
    tracker["latest_snapshot"] = snap
    tracker["history"].append(snap)
    return {"message": "Scraping abgeschlossen", "snapshot": snap}
