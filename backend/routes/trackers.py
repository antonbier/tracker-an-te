"""
WanderSuite — /api/trackers (Multi-User)
Each user sees and manages only their own trackers.
Guest (AUTH_ENABLED=false) sees all.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import Optional
import re, traceback, logging

from database import (
    create_tracker, list_trackers, get_tracker,
    delete_tracker, toggle_tracker, get_latest_snapshot,
    set_tracker_threshold,
)
from scheduler import run_single_tracker
from auth_jwt import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class BaggageItem(BaseModel):
    type: str
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
    seat_cost:     float = 0.0
    trip_id:       Optional[int] = None

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
            raise ValueError("Datum muss im Format YYYY-MM-DD sein")
        return v

    @field_validator("adults")
    @classmethod
    def min_adults(cls, v):
        if v < 1: raise ValueError("Mindestens 1 Erwachsener erforderlich")
        return v


def _uid(user: dict) -> int | None:
    """Return user_id for DB filtering. 0 (guest) → None = no filter."""
    uid = user.get("id", 0)
    return uid if uid else None


@router.get("")
def get_all_trackers(user: dict = Depends(get_current_user)):
    trackers = list_trackers(active_only=False, user_id=_uid(user))
    for t in trackers:
        t["latest_snapshot"] = get_latest_snapshot(t["id"])
    return trackers


@router.post("", status_code=201)
def add_tracker(data: TrackerCreate, user: dict = Depends(get_current_user)):
    payload = data.model_dump()
    payload["baggage"] = [b.model_dump() for b in data.baggage]
    uid = user.get("id", 1) or 1
    tracker_id = create_tracker(payload, user_id=uid)
    # Link to trip if provided
    if data.trip_id:
        from database import link_tracker_to_trip
        link_tracker_to_trip(tracker_id, "flight", data.trip_id)
    return {"id": tracker_id, "message": "Tracker angelegt"}


@router.get("/{tracker_id}")
def get_one_tracker(tracker_id: int, user: dict = Depends(get_current_user)):
    t = get_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    t["latest_snapshot"] = get_latest_snapshot(tracker_id)
    return t


@router.delete("/{tracker_id}")
def remove_tracker(tracker_id: int, user: dict = Depends(get_current_user)):
    if not delete_tracker(tracker_id, user_id=_uid(user)):
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    return {"message": "Tracker gelöscht"}


@router.patch("/{tracker_id}/toggle")
def toggle(tracker_id: int, active: bool, user: dict = Depends(get_current_user)):
    if not toggle_tracker(tracker_id, active, user_id=_uid(user)):
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    return {"message": f"Tracker {'aktiviert' if active else 'pausiert'}"}


class ThresholdPayload(BaseModel):
    threshold: Optional[float] = None


@router.patch("/{tracker_id}/threshold")
def set_threshold(tracker_id: int, data: ThresholdPayload, user: dict = Depends(get_current_user)):
    t = get_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    value = round(data.threshold, 2) if data.threshold is not None else None
    set_tracker_threshold(tracker_id, value, user_id=_uid(user))
    return {"message": f"Preisalarm {'gesetzt: unter ' + str(value) + ' €' if value else 'deaktiviert'}",
            "threshold_price": value}


@router.post("/{tracker_id}/scrape")
def manual_scrape(tracker_id: int, user: dict = Depends(get_current_user)):
    t = get_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    try:
        snap = run_single_tracker(tracker_id)
        return {"message": "Scraping abgeschlossen", "snapshot": snap}
    except Exception as e:
        logger.error(f"Scraping Fehler Tracker #{tracker_id}:\n{traceback.format_exc()}")
        raise HTTPException(500, detail=f"{type(e).__name__}: {str(e)}")
