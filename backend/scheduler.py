"""
WanderSuite — APScheduler Background Jobs

Per-user interval support: each user can configure their own update interval.
Cleanup job: runs daily at 03:00 to delete history older than 180 days.
Deep logging: per-provider status, scraping status, errors.
"""

import logging
import random
import time

from database import (
    list_trackers, save_price_snapshot as save_snapshot,
    list_gf_trackers, save_gf_snapshot,
    list_homair_trackers, save_homair_snapshot,
    list_booking_trackers, save_booking_snapshot,
    get_user_scheduler_settings, update_scheduler_last_run,
    cleanup_old_price_history, cleanup_old_snapshots,
)
from scraper import fetch_flights
from settings_manager import get_setting_value

logger = logging.getLogger(__name__)


# ── Deep Logging Helper ───────────────────────────────────────────────────────

def _log_provider(provider: str, status: str, tracker_id: int,
                  detail: str = "", price: float | None = None):
    price_str = f" | price={price:.2f}" if price is not None else ""
    detail_str = f" | {detail}" if detail else ""
    icon = "✅" if status == "ok" else ("⚠️" if status == "blocked" else "❌")
    logger.info(f"  [{provider.upper()}] {icon} #{tracker_id} status={status}{price_str}{detail_str}")


# ── Ryanair Trackers ──────────────────────────────────────────────────────────

def run_ryanair_trackers(user_id: int | None = None):
    trackers = list_trackers(active_only=True, user_id=user_id)
    logger.info(f"🛫 Ryanair: {len(trackers)} aktive Tracker (user_id={user_id or 'all'})")

    for i, tracker in enumerate(trackers):
        tid = tracker["id"]
        logger.info(f"  [{i+1}/{len(trackers)}] Ryanair #{tid}: "
                    f"{tracker['origin']}→{tracker['destination']} {tracker['outbound_date']}")
        try:
            result = fetch_flights(tracker)
            snap = result["snapshot"]
            status = result.get("status", "error")
            price = snap.get("total_price")

            if status == "ok":
                # Nur bei Erfolg speichern — Fehler ueberschreiben niemals die Historie
                save_snapshot(tid, snap)
                _log_provider("ryanair", "ok", tid, "scrape=success", price)
                _check_and_notify(tracker, snap, result.get("previous_price"))
            else:
                _log_provider("ryanair", status, tid, snap.get("error_message", "unknown"))

        except Exception as e:
            logger.error(f"  ❌ Ryanair #{tid}: {e}", exc_info=True)
            # Kein Error-Snapshot — alte Preisdaten bleiben erhalten

        if i < len(trackers) - 1:
            time.sleep(random.uniform(8, 20))


# ── Google Flights Trackers ───────────────────────────────────────────────────

def run_gf_trackers(user_id: int | None = None):
    try:
        from google_scraper import fetch_google_flights
    except ImportError:
        logger.warning("⚠️  google_scraper nicht verfügbar — GF-Tracker übersprungen")
        return

    trackers = list_gf_trackers(active_only=True, user_id=user_id)
    logger.info(f"✈️  Google Flights: {len(trackers)} aktive Tracker")
    api_key = get_setting_value("serpapi_key") or ""

    for i, tracker in enumerate(trackers):
        tid = tracker["id"]
        logger.info(f"  [{i+1}/{len(trackers)}] GF #{tid}: "
                    f"{tracker['origin']}→{tracker['destination']} {tracker['outbound_date']}")
        try:
            snap = fetch_google_flights(tracker, api_key=api_key)
            status = snap.get("status", "error")
            if status == "ok":
                # Nur bei Erfolg speichern
                save_gf_snapshot(tid, snap)
                _log_provider("google_flights", "ok", tid, "source=serpapi", snap.get("total_price"))
                _check_and_notify_generic(tracker, snap)
            else:
                _log_provider("google_flights", status, tid, snap.get("error_message", ""))
        except Exception as e:
            logger.error(f"  ❌ GF #{tid}: {e}", exc_info=True)
            # Kein Error-Snapshot — alte Preisdaten bleiben erhalten

        if i < len(trackers) - 1:
            time.sleep(random.uniform(5, 15))


# ── Homair / Camping Trackers ─────────────────────────────────────────────────

def run_homair_trackers(user_id: int | None = None):
    try:
        from homair_scraper import fetch_homair
    except ImportError:
        logger.warning("⚠️  homair_scraper nicht verfügbar — Homair-Tracker übersprungen")
        return

    trackers = list_homair_trackers(active_only=True, user_id=user_id)
    logger.info(f"⛺ Homair: {len(trackers)} aktive Tracker")
    api_key = get_setting_value("serpapi_key") or ""

    for i, tracker in enumerate(trackers):
        tid = tracker["id"]
        logger.info(f"  [{i+1}/{len(trackers)}] Homair #{tid}: {tracker.get('region')}")
        try:
            snap = fetch_homair(tracker, api_key=api_key)
            status = snap.get("status", "error")
            if status == "ok":
                # Nur bei Erfolg speichern
                save_homair_snapshot(tid, snap)
                _log_provider("homair", "ok", tid, "source=serpapi", snap.get("total_price"))
                _check_and_notify_generic(tracker, snap)
            else:
                _log_provider("homair", status, tid, snap.get("error_message", ""))
        except Exception as e:
            logger.error(f"  ❌ Homair #{tid}: {e}", exc_info=True)
            # Kein Error-Snapshot — alte Preisdaten bleiben erhalten

        if i < len(trackers) - 1:
            time.sleep(random.uniform(5, 15))


# ── Booking / Hotel Trackers ──────────────────────────────────────────────────

def run_booking_trackers(user_id: int | None = None):
    try:
        from booking_scraper import fetch_booking
    except ImportError:
        logger.warning("⚠️  booking_scraper nicht verfügbar — Booking-Tracker übersprungen")
        return

    trackers = list_booking_trackers(active_only=True, user_id=user_id)
    logger.info(f"🏨 Booking: {len(trackers)} aktive Tracker")
    api_key = get_setting_value("serpapi_key") or ""

    for i, tracker in enumerate(trackers):
        tid = tracker["id"]
        logger.info(f"  [{i+1}/{len(trackers)}] Booking #{tid}: {tracker.get('destination')}")
        try:
            snap = fetch_booking(tracker, api_key=api_key)
            status = snap.get("status", "error")
            if status == "ok":
                # Nur bei Erfolg speichern
                save_booking_snapshot(tid, snap)
                _log_provider("booking", "ok", tid, "source=serpapi", snap.get("total_price"))
                _check_and_notify_generic(tracker, snap)
            else:
                _log_provider("booking", status, tid, snap.get("error_message", ""))
        except Exception as e:
            logger.error(f"  ❌ Booking #{tid}: {e}", exc_info=True)
            # Kein Error-Snapshot — alte Preisdaten bleiben erhalten

        if i < len(trackers) - 1:
            time.sleep(random.uniform(5, 12))


# ── Notification Helpers ──────────────────────────────────────────────────────

def _check_and_notify(tracker: dict, snap: dict, prev_price: float | None):
    new_price = snap.get("total_price")
    if not new_price:
        return
    if prev_price and new_price < prev_price:
        try:
            from notifications import notify_price_drop
            notify_price_drop(tracker, old_price=prev_price, new_price=new_price)
        except Exception as ne:
            logger.warning(f"  ⚠️ Benachrichtigung fehlgeschlagen: {ne}")
    threshold = tracker.get("threshold_price") or tracker.get("wish_price")
    if threshold and new_price <= threshold:
        already_below = prev_price and prev_price <= threshold
        if not already_below:
            try:
                from notifications import notify_threshold_reached
                notify_threshold_reached(tracker, price=new_price, threshold=threshold)
            except Exception as ne:
                logger.warning(f"  ⚠️ Threshold-Alert fehlgeschlagen: {ne}")


def _check_and_notify_generic(tracker: dict, snap: dict):
    new_price = snap.get("total_price")
    wish_price = tracker.get("wish_price")
    if not new_price or not wish_price:
        return
    if new_price <= wish_price:
        try:
            from notifications import notify_threshold_reached
            notify_threshold_reached(tracker, price=new_price, threshold=wish_price)
        except Exception as ne:
            logger.warning(f"  ⚠️ Wish-price alert fehlgeschlagen: {ne}")


# ── Master Run ────────────────────────────────────────────────────────────────

def run_all_trackers(user_id: int | None = None):
    """
    Run all tracker types. Each provider is independent — errors don't cascade.
    Called by APScheduler daily or via POST /api/scheduler/run.
    """
    logger.info(f"🕐 Scheduler startet (user_id={user_id or 'all'})")

    for runner, name in [
        (run_ryanair_trackers,  "Ryanair"),
        (run_gf_trackers,       "Google Flights"),
        (run_homair_trackers,   "Homair/Camping"),
        (run_booking_trackers,  "Booking/Hotels"),
    ]:
        try:
            runner(user_id=user_id)
        except Exception as e:
            logger.error(f"❌ {name} runner crashed: {e}", exc_info=True)

    # FIX B3: update last_run_at for the target user(s)
    # When called by APScheduler (user_id=None), update all users who have tracker data
    if user_id:
        try:
            update_scheduler_last_run(user_id)
        except Exception:
            pass
    else:
        # Scheduled run: update last_run_at for ALL users with active trackers
        try:
            from database import db as _db
            with _db() as conn:
                user_ids = conn.execute(
                    "SELECT DISTINCT user_id FROM trackers WHERE active=1 "
                    "UNION SELECT DISTINCT user_id FROM gf_trackers WHERE active=1 "
                    "UNION SELECT DISTINCT user_id FROM homair_trackers WHERE active=1 "
                    "UNION SELECT DISTINCT user_id FROM booking_trackers WHERE active=1"
                ).fetchall()
            for row in user_ids:
                try:
                    update_scheduler_last_run(row[0])
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"[Scheduler] last_run_at update fehlgeschlagen: {e}")

    logger.info("✅ Scheduler-Lauf abgeschlossen")


def run_single_tracker(tracker_id: int):
    """Einzelnen Ryanair-Tracker manuell abrufen.
    Nur bei status=ok wird ein Snapshot gespeichert —
    Fehler überschreiben niemals die bestehende Preishistorie.
    """
    from database import get_tracker
    tracker = get_tracker(tracker_id)
    if not tracker:
        raise ValueError(f"Tracker #{tracker_id} nicht gefunden")
    result = fetch_flights(tracker)
    snap = result["snapshot"]
    status = result.get("status", "error")
    if status == "ok" and snap.get("total_price") is not None:
        snap_id = save_snapshot(tracker_id, snap)
        snap["id"] = snap_id
        logger.info(f"  ✅ run_single #{tracker_id}: ok | price={snap.get('total_price')}")
    else:
        err = snap.get("error_message", "Unbekannt")
        logger.warning(f"  ⚠️ run_single #{tracker_id}: {status} — {err} | Historie bleibt erhalten")
        raise ValueError(f"Scraping fehlgeschlagen ({status}): {err}")
    return snap


# ── Cleanup Job ───────────────────────────────────────────────────────────────

def run_cleanup_job():
    """Delete price history and snapshots older than 60 days. Runs daily at 03:00."""
    logger.info("Cleanup-Job startet (>60 Tage)")
    try:
        ph = cleanup_old_price_history(days=60)
        snaps = cleanup_old_snapshots(days=60)
        logger.info(f"  Cleanup: price_history={ph} geloescht | snapshots={sum(snaps.values())} geloescht (>60d)")
    except Exception as e:
        logger.error(f"  ❌ Cleanup fehlgeschlagen: {e}", exc_info=True)

