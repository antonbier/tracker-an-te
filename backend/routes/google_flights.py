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
)
from google_scraper import scrape_google_flights
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


def _uid(user: dict) -> int | None:
    uid = user.get("id", 0)
    return uid if uid else None


@router.get("")
def list_trackers(user: dict = Depends(get_current_user)):
    return list_gf_trackers(user_id=_uid(user))


@router.post("", status_code=201)
def create_tracker(data: GFTrackerCreate, user: dict = Depends(get_current_user)):
    uid = user.get("id", 1) or 1
    tid = create_gf_tracker(data.model_dump(), user_id=uid)
    return {"id": tid, "message": "Google Flights Tracker angelegt"}


@router.delete("/{tracker_id}")
def delete_tracker(tracker_id: int, user: dict = Depends(get_current_user)):
    if not delete_gf_tracker(tracker_id, user_id=_uid(user)):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Tracker gelöscht"}


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
        result["fetched_at"] = datetime.utcnow().isoformat()
        save_gf_snapshot(tracker_id, result)
        return result
    except Exception as e:
        logger.error(f"GF scrape error: {e}")
        raise HTTPException(500, str(e))
