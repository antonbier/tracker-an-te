"""
WanderSuite v0.5 — REST Routes: /api/google-flights
Google Flights Tracker via SerpAPI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
import re
import logging
import os

from google_scraper import fetch_google_flights

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory store für Google Flights Tracker (einfach, kein extra DB-Schema)
# In v0.6 wird das in die SQLite DB überführt
_gf_trackers: list[dict] = []
_gf_id_counter = 1


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
        if v is None:
            return v
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Datum muss im Format YYYY-MM-DD sein")
        return v


@router.get("")
def list_gf_trackers():
    return _gf_trackers


@router.post("", status_code=201)
def add_gf_tracker(data: GFTrackerCreate):
    global _gf_id_counter
    tracker = {
        "id":            _gf_id_counter,
        "origin":        data.origin,
        "destination":   data.destination,
        "outbound_date": data.outbound_date,
        "return_date":   data.return_date,
        "adults":        data.adults,
        "children":      data.children,
        "latest_snapshot": None,
    }
    _gf_trackers.append(tracker)
    _gf_id_counter += 1
    return {"id": tracker["id"], "message": "Google Flights Tracker angelegt"}


@router.delete("/{tracker_id}")
def delete_gf_tracker(tracker_id: int):
    global _gf_trackers
    before = len(_gf_trackers)
    _gf_trackers = [t for t in _gf_trackers if t["id"] != tracker_id]
    if len(_gf_trackers) == before:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    return {"message": "Tracker gelöscht"}


@router.post("/{tracker_id}/scrape")
def scrape_gf_tracker(tracker_id: int, api_key: str = ""):
    tracker = next((t for t in _gf_trackers if t["id"] == tracker_id), None)
    if not tracker:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")

    # API Key aus Env oder Query-Param
    key = api_key or os.environ.get("SERPAPI_KEY", "")
    if not key:
        raise HTTPException(400, "SerpAPI Key fehlt — in den Einstellungen eintragen")

    result = fetch_google_flights(tracker, key)
    snap = result["snapshot"]

    # Snapshot im Tracker speichern
    tracker["latest_snapshot"] = snap
    if not tracker.get("history"):
        tracker["history"] = []
    tracker["history"].append(snap)

    return {"message": "Scraping abgeschlossen", "snapshot": snap}
