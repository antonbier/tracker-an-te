"""
WanderSuite v0.1 — REST Routes: /api/prices
Preisverlauf für Charts — inkl. Sitzplatzkosten.
"""

from fastapi import APIRouter, HTTPException
from database import get_tracker, get_snapshots

router = APIRouter()


@router.get("/{tracker_id}")
def get_price_history(tracker_id: int, limit: int = 90):
    """Preisverlauf für einen Tracker (Chart.js-kompatibel)."""
    t = get_tracker(tracker_id)
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")

    snaps = get_snapshots(tracker_id, limit=limit)
    snaps_sorted = sorted(snaps, key=lambda s: s["fetched_at"])

    return {
        "tracker": {
            "id":            t["id"],
            "origin":        t["origin"],
            "destination":   t["destination"],
            "outbound_date": t["outbound_date"],
            "return_date":   t.get("return_date"),
            "adults":        t["adults"],
            "seat_cost":     t.get("seat_cost", 0.0),
        },
        "labels":         [s["fetched_at"][:10] for s in snaps_sorted],
        "total_prices":   [s["total_price"]   for s in snaps_sorted],
        "flight_prices":  [s["flight_price"]  for s in snaps_sorted],
        "baggage_prices": [s["baggage_price"] for s in snaps_sorted],
        "seat_prices":    [s.get("seat_price", 0) for s in snaps_sorted],
        "statuses":       [s["status"]        for s in snaps_sorted],
        "snapshots":      snaps_sorted,
    }
