"""
REST Routes: /api/trackers
CRUD für Tracker + manuelles Scrapen triggern.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
import re

from database import (
    create_tracker, list_trackers, get_tracker,
    delete_tracker, toggle_tracker, get_latest_snapshot
)
from scheduler import run_single_tracker

router = APIRouter()

# ─── Pydantic Models ─────────────────────────────────────────

class BaggageItem(BaseModel):
    type: str         # "10kg" | "20kg" | "23kg"
    per_person: bool = True

    @field_validator("type")
    @classmethod
    def valid_type(cls, v):
        if v not in ("10kg", "20kg", "23kg"):
            raise ValueError("Gepäcktyp muss '10kg', '20kg' oder '23kg' sein")
        return v


class TrackerCreate(BaseModel):
    origin:        str
    destination:   str
    outbound_date: str
    return_date:   Optional[str] = None
    adults:        int = 1
    children:      int = 0
    baggage:       list[BaggageItem] = []

    @field_validator("origin", "destination")
    @classmethod
    def iata_upper(cls, v):
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", v):
            raise ValueError("IATA-Code muss genau 3 Buchstaben haben (z.B. BZO, DUB)")
        return v

    @field_validator("outbound_date", "return_date")
    @classmethod
    def valid_date(cls, v):
        if v is None:
            return v
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Datum muss im Format YYYY-MM-DD sein")
        return v

    @field_validator("adults")
    @classmethod
    def min_adults(cls, v):
        if v < 1:
            raise ValueError("Mindestens 1 Erwachsener erforderlich")
        return v


# ─── Endpoints ───────────────────────────────────────────────

@router.get("")
def get_all_trackers():
    trackers = list_trackers(active_only=False)
    # Letzten Snapshot anhängen
    for t in trackers:
        t["latest_snapshot"] = get_latest_snapshot(t["id"])
    return trackers


@router.post("", status_code=201)
def add_tracker(data: TrackerCreate):
    payload = data.model_dump()
    payload["baggage"] = [b.model_dump() for b in data.baggage]
    tracker_id = create_tracker(payload)
    return {"id": tracker_id, "message": "Tracker angelegt"}


@router.get("/{tracker_id}")
def get_one_tracker(tracker_id: int):
    t = get_tracker(tracker_id)
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    t["latest_snapshot"] = get_latest_snapshot(tracker_id)
    return t


@router.delete("/{tracker_id}")
def remove_tracker(tracker_id: int):
    if not delete_tracker(tracker_id):
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    return {"message": "Tracker gelöscht"}


@router.patch("/{tracker_id}/toggle")
def toggle(tracker_id: int, active: bool):
    if not toggle_tracker(tracker_id, active):
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    return {"message": f"Tracker {'aktiviert' if active else 'pausiert'}"}


@router.post("/{tracker_id}/scrape")
def manual_scrape(tracker_id: int):
    """Manuell einen Preis-Abruf für einen Tracker triggern."""
    t = get_tracker(tracker_id)
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    try:
        snap = run_single_tracker(tracker_id)
        return {"message": "Scraping abgeschlossen", "snapshot": snap}
    except Exception as e:
        raise HTTPException(500, f"Scraping-Fehler: {str(e)}")
