"""
REST Routes: /api/prices
Preisverlauf für Charts abrufen.
"""

from fastapi import APIRouter, HTTPException
from database import get_tracker, get_snapshots

router = APIRouter()


@router.get("/{tracker_id}")
def get_price_history(tracker_id: int, limit: int = 90):
    """Preisverlauf für einen Tracker (für Chart.js)."""
    t = get_tracker(tracker_id)
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")

    snaps = get_snapshots(tracker_id, limit=limit)

    # Chronologisch sortieren (älteste zuerst) für Charts
    snaps_sorted = sorted(snaps, key=lambda s: s["fetched_at"])

    # Chart.js-kompatibles Format
    chart_data = {
        "tracker": {
            "id":          t["id"],
            "origin":      t["origin"],
            "destination": t["destination"],
            "outbound_date": t["outbound_date"],
            "return_date": t.get("return_date"),
            "adults":      t["adults"],
        },
        "labels":         [s["fetched_at"][:10] for s in snaps_sorted],
        "total_prices":   [s["total_price"] for s in snaps_sorted],
        "flight_prices":  [s["flight_price"] for s in snaps_sorted],
        "baggage_prices": [s["baggage_price"] for s in snaps_sorted],
        "statuses":       [s["status"] for s in snaps_sorted],
        "snapshots":      snaps_sorted,
    }

    return chart_data
