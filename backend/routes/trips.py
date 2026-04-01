"""
WanderSuite — /api/trips
Unified endpoint for detected (Dawarich) + manual trips, per-user budgets.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import json, logging
from datetime import datetime

from database import (
    save_detected_trip, list_detected_trips,
    delete_detected_trip, update_detected_trip_cost,
    save_user_data, get_user_data,
)
from auth_jwt import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def _uid(user: dict) -> int:
    return user.get("id", 1) or 1


# ── Manual trip ───────────────────────────────────────────────────────────────

class ManualTripPayload(BaseModel):
    name: str
    start_date: str
    end_date: Optional[str] = None
    location_name: Optional[str] = None
    country: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None


@router.get("")
def get_trips(limit: int = 200, user=Depends(get_current_user)):
    """Return all trips (dawarich + manual), sorted by start_date desc."""
    trips = list_detected_trips(limit=limit, user_id=_uid(user))
    return trips


@router.post("")
def create_manual_trip(data: ManualTripPayload, user=Depends(get_current_user)):
    """Create a manual trip entry."""
    end = data.end_date or data.start_date
    # nights = delta of dates
    try:
        d0 = datetime.strptime(data.start_date, "%Y-%m-%d")
        d1 = datetime.strptime(end, "%Y-%m-%d")
        nights = max(1, (d1 - d0).days)
    except Exception:
        nights = 1

    trip_id = save_detected_trip({
        "start_date":    data.start_date,
        "end_date":      end,
        "location_name": data.name,
        "country":       data.country or "",
        "lat":           None,
        "lon":           None,
        "nights":        nights,
        "source":        "manual",
        "cost":          data.cost,
        "notes":         data.notes,
    }, user_id=_uid(user))
    return {"id": trip_id, "message": "Reise angelegt ✓"}


class CostPayload(BaseModel):
    cost: Optional[float] = None


@router.patch("/{trip_id}/cost")
def update_cost(trip_id: int, data: CostPayload, user=Depends(get_current_user)):
    """Update the cost of a trip (dawarich or manual)."""
    ok = update_detected_trip_cost(trip_id, data.cost, user_id=_uid(user))
    if not ok:
        raise HTTPException(404, "Trip nicht gefunden.")
    return {"id": trip_id, "cost": data.cost, "message": "Kosten gespeichert ✓"}


@router.delete("/{trip_id}")
def remove_trip(trip_id: int, user=Depends(get_current_user)):
    if not delete_detected_trip(trip_id, user_id=_uid(user)):
        raise HTTPException(404, "Trip nicht gefunden.")
    return {"message": "Gelöscht ✓"}


# ── Budget per year ────────────────────────────────────────────────────────────

@router.get("/budget")
def get_budget(user=Depends(get_current_user)):
    """Return budget dict by year: { "2024": 3000, "2025": 4500 }"""
    raw = get_user_data("ws-budget-years", user_id=_uid(user))
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    # Legacy: single budget value
    legacy = get_user_data("ws-budget", user_id=_uid(user))
    if legacy:
        try:
            year = str(datetime.now().year)
            return {year: float(legacy)}
        except Exception:
            pass
    return {}


class BudgetPayload(BaseModel):
    year: int
    amount: float


@router.put("/budget")
def set_budget(data: BudgetPayload, user=Depends(get_current_user)):
    """Set budget for a specific year."""
    raw = get_user_data("ws-budget-years", user_id=_uid(user))
    budgets = {}
    if raw:
        try:
            budgets = json.loads(raw)
        except Exception:
            pass
    budgets[str(data.year)] = data.amount
    save_user_data("ws-budget-years", json.dumps(budgets), user_id=_uid(user))
    return {"year": data.year, "amount": data.amount, "message": "Budget gespeichert ✓"}
