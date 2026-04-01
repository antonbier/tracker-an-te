"""
WanderSuite — /api/trips
Unified endpoint for detected (Dawarich) + manual trips, per-user budgets.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import json, logging
from datetime import datetime, date

from database import (
    save_detected_trip, list_detected_trips,
    delete_detected_trip, update_detected_trip_cost,
    update_trip_auto_cost,
    save_user_data, get_user_data,
)
from auth_jwt import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def _uid(user: dict) -> int:
    return user.get("id", 1) or 1


# ── Trips abrufen ─────────────────────────────────────────────────────────────

@router.get("")
def get_trips(limit: int = 200, user=Depends(get_current_user)):
    """Return all non-ignored trips (dawarich + manual), sorted by start_date desc."""
    trips = list_detected_trips(limit=limit, user_id=_uid(user), include_ignored=False)
    return trips


# ── Manuellen Trip anlegen ────────────────────────────────────────────────────

class ManualTripPayload(BaseModel):
    name: str
    start_date: str
    end_date: Optional[str] = None
    location_name: Optional[str] = None
    country: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None


@router.post("")
def create_manual_trip(data: ManualTripPayload, user=Depends(get_current_user)):
    end = data.end_date or data.start_date
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


# ── Kosten ────────────────────────────────────────────────────────────────────

class CostPayload(BaseModel):
    cost: Optional[float] = None


@router.patch("/{trip_id}/cost")
def update_cost(trip_id: int, data: CostPayload, user=Depends(get_current_user)):
    ok = update_detected_trip_cost(trip_id, data.cost, user_id=_uid(user))
    if not ok:
        raise HTTPException(404, "Trip nicht gefunden.")
    return {"id": trip_id, "cost": data.cost, "message": "Kosten gespeichert ✓"}


# ── Löschen (Soft-Delete für Dawarich, Hard-Delete für Manual) ────────────────

@router.delete("/{trip_id}")
def remove_trip(trip_id: int, user=Depends(get_current_user)):
    """Dawarich-Trips → ignored=1 (werden beim nächsten Sync übersprungen).
       Manuelle Trips → echter Delete."""
    if not delete_detected_trip(trip_id, user_id=_uid(user)):
        raise HTTPException(404, "Trip nicht gefunden.")
    return {"message": "Gelöscht ✓"}


# ── Budget per Jahr ───────────────────────────────────────────────────────────

@router.get("/budget")
def get_budget(user=Depends(get_current_user)):
    raw = get_user_data("ws-budget-years", user_id=_uid(user))
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
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


# ── Auto-Cost: ActualBudget Transaktionen → Reise zuordnen ───────────────────

class AutoCostRequest(BaseModel):
    actual_url:   str
    actual_token: str
    actual_file:  Optional[str] = None
    categories:   Optional[str] = None   # komma-getrennt


@router.post("/auto-cost")
def assign_actual_costs(data: AutoCostRequest, user=Depends(get_current_user)):
    """
    Ordnet ActualBudget-Transaktionen automatisch den Dawarich-Trips zu.
    Logik: Transaktion.datum liegt im [trip.start_date, trip.end_date] Intervall
           → wird dem Trip als auto_cost zugeordnet.
    Gibt zurück: { trips_updated, total_assigned, details: [...] }
    """
    from actual_budget import get_travel_expenses, list_budget_files

    uid = _uid(user)
    base_url    = data.actual_url.rstrip("/")
    password    = data.actual_token
    budget_file = data.actual_file or ""
    cats        = [c.strip() for c in (data.categories or "").split(",") if c.strip()]

    # Budget-Datei auto-detect
    if not budget_file:
        files_resp = list_budget_files(base_url, password)
        files = files_resp.get("files", [])
        if not files:
            raise HTTPException(400, "Keine Budget-Dateien gefunden")
        budget_file = files[0].get("name", "")
        logger.info(f"[AutoCost] Nutze erste Budget-Datei: {budget_file}")

    # Alle Transaktionen laden (kein Jahresfilter — wir filtern per Trip-Datum)
    result = get_travel_expenses(base_url, password, budget_file, cats, year=None)
    if "error" in result:
        raise HTTPException(400, result["error"])

    txs = result.get("transactions", [])
    if not txs:
        return {"trips_updated": 0, "total_assigned": 0.0, "details": []}

    # Alle Trips laden
    trips = list_detected_trips(limit=5000, user_id=uid, include_ignored=False)

    details = []
    trips_updated = 0

    for trip in trips:
        start = trip.get("start_date", "")
        end   = trip.get("end_date",   "") or start
        if not start:
            continue

        # Transaktionen im Zeitraum der Reise (beide Datumsgrenzen inklusive)
        matched = [
            tx for tx in txs
            if start <= tx.get("date", "") <= end
        ]
        if not matched:
            continue

        total = round(sum(abs(tx.get("amount", 0)) for tx in matched if tx.get("amount", 0) < 0), 2)
        if total == 0:
            # Ausgaben-Transaktionen haben negativen Betrag in ActualBudget
            # Fallback: absoluter Betrag aller gematchten
            total = round(sum(abs(tx.get("amount", 0)) for tx in matched), 2)

        txs_json = json.dumps([
            {"date": tx["date"], "payee": tx.get("payee",""), "amount": tx.get("amount",0)}
            for tx in matched
        ])

        update_trip_auto_cost(trip["id"], total, txs_json, user_id=uid)
        trips_updated += 1
        details.append({
            "trip_id":        trip["id"],
            "trip_name":      trip.get("location_name") or trip.get("name", ""),
            "period":         f"{start} → {end}",
            "transactions":   len(matched),
            "auto_cost":      total,
        })
        logger.info(f"[AutoCost] Trip {trip['id']} ({start}→{end}): {total:.2f}€ ({len(matched)} Tx)")

    total_assigned = round(sum(d["auto_cost"] for d in details), 2)
    return {
        "trips_updated":  trips_updated,
        "total_assigned": total_assigned,
        "budget_file":    budget_file,
        "details":        details,
    }
