"""
WanderSuite — REST Routes: /api/prices
Preisverlauf für Charts, CSV-Export, Wish-Price und History-Endpunkt.
"""

import csv
import io
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.database import (
    get_tracker,
    get_price_history as get_snapshots,
    get_price_history as _get_ph,
    set_tracker_wish_price as _set_wish,
)
from auth_jwt import get_current_user

router = APIRouter()


@router.get("/{tracker_id}")
def get_price_history(tracker_id: int, limit: int = 90):
    """Preisverlauf für einen Ryanair-Tracker (Chart.js-kompatibel)."""
    t = get_tracker(tracker_id)
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")

    snaps = get_snapshots(tracker_id, limit=limit)
    snaps_sorted = sorted(snaps, key=lambda s: s["fetched_at"])

    return {
        "tracker": {
            "id":              t["id"],
            "origin":          t["origin"],
            "destination":     t["destination"],
            "outbound_date":   t["outbound_date"],
            "return_date":     t.get("return_date"),
            "adults":          t["adults"],
            "seat_cost":       t.get("seat_cost", 0.0),
            "threshold_price": t.get("threshold_price"),
        },
        "labels":         [s["fetched_at"][:10] for s in snaps_sorted],
        "total_prices":   [s["total_price"]    for s in snaps_sorted],
        "flight_prices":  [s["flight_price"]   for s in snaps_sorted],
        "baggage_prices": [s["baggage_price"]  for s in snaps_sorted],
        "seat_prices":    [s.get("seat_price", 0) for s in snaps_sorted],
        "statuses":       [s["status"]         for s in snaps_sorted],
        "snapshots":      snaps_sorted,
    }


@router.get("/{tracker_id}/export.csv")
def export_price_history_csv(tracker_id: int, limit: int = 365):
    """Export full price history as CSV download."""
    t = get_tracker(tracker_id)
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")

    snaps = get_snapshots(tracker_id, limit=limit)
    snaps_sorted = sorted(snaps, key=lambda s: s["fetched_at"])

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow([
        f"# WanderSuite Preishistorie — "
        f"{t['origin']} → {t['destination']} "
        f"({t['outbound_date']}"
        f"{' ⇄ ' + t['return_date'] if t.get('return_date') else ''})"
    ])
    writer.writerow([f"# Erwachsene: {t['adults']} | Abruf: {len(snaps_sorted)} Datenpunkte"])
    writer.writerow([])
    writer.writerow(["Datum", "Gesamtpreis (€)", "Flugpreis (€)",
                     "Gepäck (€)", "Sitzplatz (€)", "Status", "Währung"])
    for s in snaps_sorted:
        writer.writerow([
            s["fetched_at"][:10],
            s.get("total_price")   or "",
            s.get("flight_price")  or "",
            s.get("baggage_price") or "",
            s.get("seat_price")    or "",
            s.get("status", ""),
            s.get("currency", "EUR"),
        ])

    output.seek(0)
    filename = f"wandersuite_{t['origin']}-{t['destination']}_{t['outbound_date']}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Unified Price History (all tracker types) ─────────────────────────────────

@router.get("/history/{tracker_type}/{tracker_id}")
def get_unified_price_history(
    tracker_type: str,
    tracker_id: int,
    limit: int = 90,
    user: dict = Depends(get_current_user),
):
    """
    Return price history from price_history table for any tracker type.
    tracker_type: flight | google_flight | hotel | camping
    """
    allowed = {"flight", "google_flight", "hotel", "camping", "car"}
    if tracker_type not in allowed:
        raise HTTPException(400, f"tracker_type muss eines von {allowed} sein")
    uid = user.get("id", 0) or None
    history = _get_ph(tracker_type, tracker_id, user_id=uid, limit=min(limit, 365))
    return {"tracker_type": tracker_type, "tracker_id": tracker_id, "history": history}


# ── Wish Price ────────────────────────────────────────────────────────────────

class WishPriceUpdate(BaseModel):
    wish_price: Optional[float] = None


@router.put("/wish/{table}/{tracker_id}")
def update_wish_price(
    table: str,
    tracker_id: int,
    data: WishPriceUpdate,
    user: dict = Depends(get_current_user),
):
    """
    Set or clear wish_price on any tracker table.
    table: trackers | gf_trackers | homair_trackers | booking_trackers
    """
    uid = user.get("id", 0) or None
    ok = _set_wish(tracker_id, table, data.wish_price, user_id=uid)
    if not ok:
        raise HTTPException(404, "Tracker nicht gefunden oder kein Zugriff")
    return {"message": "Wunschpreis gespeichert", "wish_price": data.wish_price}
