"""
WanderSuite v1.0 — REST Routes: /api/google-flights
SQLite-persistente Google Flights Tracker.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
import re, logging

from database import (
    create_gf_tracker, list_gf_trackers, get_gf_tracker,
    delete_gf_tracker, save_gf_snapshot, get_gf_snapshots, get_gf_latest_snapshot
)
from google_scraper import fetch_google_flights
from settings_manager import get_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


class GFTrackerCreate(BaseModel):
    origin:        str
    destination:   str
    outbound_date: str
    return_date:   Optional[str] = None
    adults:        int = 1
    children:      int = 0

    @field_validator("origin", "destination")
    @classmethod
    def iata_upper(cls, v):
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", v):
            raise ValueError("IATA-Code muss genau 3 Buchstaben haben")
        return v

    @field_validator("outbound_date", "return_date")
    @classmethod
    def valid_date(cls, v):
        if v is None: return v
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Format: YYYY-MM-DD")
        return v


@router.get("")
def list_trackers():
    return list_gf_trackers()


@router.post("", status_code=201)
def add_tracker(data: GFTrackerCreate):
    tid = create_gf_tracker(data.model_dump())
    return {"id": tid, "message": "Google Flights Tracker angelegt"}


@router.delete("/{tracker_id}")
def del_tracker(tracker_id: int):
    if not delete_gf_tracker(tracker_id):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Tracker gelöscht"}


@router.post("/{tracker_id}/scrape")
def scrape_tracker(tracker_id: int, api_key: str = ""):
    tracker = get_gf_tracker(tracker_id)
    if not tracker:
        raise HTTPException(404, "Tracker nicht gefunden")
    key = api_key or get_setting_value("serpapi_key") or ""
    if not key:
        raise HTTPException(400, "SerpAPI Key fehlt")
    result = fetch_google_flights(tracker, key)
    snap = result["snapshot"]
    snap_id = save_gf_snapshot(tracker_id, snap)
    snap["id"] = snap_id
    return {"message": "Scraping abgeschlossen", "snapshot": snap}


@router.get("/{tracker_id}/history")
def get_history(tracker_id: int, limit: int = 90):
    return get_gf_snapshots(tracker_id, limit)
