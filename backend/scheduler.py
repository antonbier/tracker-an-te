"""
APScheduler Job — läuft täglich 07:00 Uhr Europe/Rome.
Holt Preise für alle aktiven Tracker und speichert Snapshots.
"""

import logging
import random
import time

from database import list_trackers, save_snapshot
from scraper import fetch_flights

logger = logging.getLogger(__name__)


def run_all_trackers():
    """Alle aktiven Tracker einmal abrufen. Wird täglich vom Scheduler aufgerufen."""
    trackers = list_trackers(active_only=True)
    logger.info(f"🕐 Scheduler startet: {len(trackers)} aktive Tracker")

    for i, tracker in enumerate(trackers):
        logger.info(f"[{i+1}/{len(trackers)}] Tracker #{tracker['id']}: "
                    f"{tracker['origin']}→{tracker['destination']} {tracker['outbound_date']}")
        try:
            result = fetch_flights(tracker)
            snap = result["snapshot"]
            snap_id = save_snapshot(tracker["id"], snap)

            if result["status"] == "ok":
                logger.info(f"  ✅ Gespeichert (id={snap_id}): {snap['total_price']} {snap['currency']}")
            else:
                logger.warning(f"  ⚠️  Status={result['status']}: {snap.get('error_message')}")

        except Exception as e:
            logger.error(f"  ❌ Unerwarteter Fehler bei Tracker #{tracker['id']}: {e}", exc_info=True)
            save_snapshot(tracker["id"], {
                "status": "error",
                "error_message": str(e),
            })

        # Zufälliger Delay zwischen Tracker-Abrufen (Anti-Bot)
        if i < len(trackers) - 1:
            delay = random.uniform(8, 20)
            logger.debug(f"Warte {delay:.1f}s vor nächstem Tracker...")
            time.sleep(delay)

    logger.info("✅ Scheduler-Lauf abgeschlossen")


def run_single_tracker(tracker_id: int):
    """Einzelnen Tracker manuell abrufen (für API-Endpoint /scrape/{id})."""
    from database import get_tracker
    tracker = get_tracker(tracker_id)
    if not tracker:
        raise ValueError(f"Tracker #{tracker_id} nicht gefunden")

    result = fetch_flights(tracker)
    snap = result["snapshot"]
    snap_id = save_snapshot(tracker_id, snap)
    snap["id"] = snap_id
    return snap
