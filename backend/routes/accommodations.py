"""
WanderSuite v1.0 — REST Routes: /api/accommodations
SQLite-persistente Homair + Booking Tracker.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from database import (
    create_homair_tracker, list_homair_trackers, get_homair_tracker,
    delete_homair_tracker, save_homair_snapshot,
    create_booking_tracker, list_booking_trackers, get_booking_tracker,
    delete_booking_tracker, save_booking_snapshot,
)
from homair_scraper import fetch_homair
from booking_scraper import fetch_booking
from settings_manager import get_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


class HomairCreate(BaseModel):
    region:             str = "cote-d-azur"
    accommodation_type: str = "mobilheim-standard"
    checkin_date:       str
    checkout_date:      str
    adults:             int = 2
    children:           int = 0


class BookingCreate(BaseModel):
    destination:   str
    checkin_date:  str
    checkout_date: str
    adults:        int = 2
    rooms:         int = 1
    source:        str = "booking"


# ── Homair ────────────────────────────────────────────

@router.get("/homair")
def list_homair():
    return list_homair_trackers()


@router.post("/homair", status_code=201)
def add_homair(data: HomairCreate):
    tid = create_homair_tracker(data.model_dump())
    return {"id": tid, "message": "Homair Tracker angelegt"}


@router.delete("/homair/{tid}")
def del_homair(tid: int):
    if not delete_homair_tracker(tid):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Gelöscht"}


@router.post("/homair/{tid}/scrape")
def scrape_homair(tid: int):
    tracker = get_homair_tracker(tid)
    if not tracker:
        raise HTTPException(404, "Tracker nicht gefunden")
    result = fetch_homair(tracker)
    snap = result["snapshot"]
    save_homair_snapshot(tid, snap)
    return {"message": "Scraping abgeschlossen", "snapshot": snap}


# ── Booking ───────────────────────────────────────────

@router.get("/booking")
def list_booking():
    return list_booking_trackers()


@router.post("/booking", status_code=201)
def add_booking(data: BookingCreate):
    tid = create_booking_tracker(data.model_dump())
    return {"id": tid, "message": "Booking Tracker angelegt"}


@router.delete("/booking/{tid}")
def del_booking(tid: int):
    if not delete_booking_tracker(tid):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Gelöscht"}


@router.post("/booking/{tid}/scrape")
def scrape_booking(tid: int, api_key: str = ""):
    tracker = get_booking_tracker(tid)
    if not tracker:
        raise HTTPException(404, "Tracker nicht gefunden")
    key = api_key or get_setting_value("serpapi_key") or ""
    if not key:
        raise HTTPException(400, "SerpAPI Key fehlt")
    result = fetch_booking(tracker, key)
    snap = result["snapshot"]
    save_booking_snapshot(tid, snap)
    return {"message": "Scraping abgeschlossen", "snapshot": snap}
