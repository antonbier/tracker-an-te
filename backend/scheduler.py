"""
WanderSuite — APScheduler Background Jobs

Per-user interval support: each user can configure their own update interval.
Cleanup job: runs daily at 03:00 to delete history older than 180 days.
Deep logging: per-provider status, scraping status, errors.
"""

import logging
import random
import time
from datetime import datetime, timezone

from database import (
    list_trackers, save_price_snapshot as save_snapshot,
    list_gf_trackers, save_gf_snapshot,
    list_homair_trackers, save_homair_snapshot,
    list_booking_trackers, save_booking_snapshot,
    get_user_scheduler_settings, update_scheduler_last_run,
    cleanup_old_price_history, cleanup_old_snapshots,
)

logger = logging.getLogger(__name__)

# ── Deep Logging Helpers ──────────────────────────────────────────────────────

def _log_provider(provider: str, status: str, tracker_id: int,
                  detail: str = "", price: float | None = None):
    """Structured per-provider log entry."""
    price_str = f" | price={price:.2f}" if price is not None else ""
    detail_str = f" | {detail}" if detail else ""
    icon = "✅" if status == "ok" else ("⚠️" if status == "blocked" else "❌")
    logger.info(f"  [{provider.upper()}] {icon} #{tracker_id} status={status}{price_str}{detail_str}")


# ── Ryanair Trackers ──────────────────────────────────────────────────────────

def run_ryanair_trackers(user_id: int | None = None):
    """Run all active Ryanair trackers, optionally filtered by user_id."""
    from scraper import fetch_flights
    trackers = list_trackers(active_only=True, user_id=user_id)
    logger.info(f"🛫 Ryanair: {len(trackers)} aktive Tracker (user_id={user_id or 'all'})")

    for i, tracker in enumerate(trackers):
        tid = tracker["id"]
        logger.info(f"  [{i+1}/{len(trackers)}] Ryanair #{tid}: "
                    f"{tracker['origin']}→{tracker['destination']} {tracker['outbound_date']}")
        try:
            result = fetch_flights(tracker)
            snap = result["snapshot"]
            snap_id = save_snapshot(tid, snap)

            status = result.get("status", "error")
            price = snap.get("total_price")

            if status == "ok":
                _log_provider("ryanair", "ok", tid, "scrape=success", price)
                _check_and_notify(tracker, snap, result.get("previous_price"))
            elif status in ("blocked", "rate_limited"):
                _log_provider("ryanair", "blocked", tid, "scrape=blocked_by_cf")
            else:
                _log_provider("ryanair", "error", tid, snap.get("error_message", "unknown"))

        except Exception as e:
            logger.error(f"  ❌ Ryanair #{tid}: {e}", exc_info=True)
            save_snapshot(tid, {"status": "error", "error_message": str(e)})

        if i < len(trackers) - 1:
            time.sleep(random.uniform(8, 20))


# ── Google Flights Trackers ───────────────────────────────────────────────────

def run_gf_trackers(user_id: int | None = None):
    from routes.google_flights import fetch_gf_price
    trackers = list_gf_trackers(active_only=True, user_id=user_id)
    logger.info(f"✈️  Google Flights: {len(trackers)} aktive Tracker")

    for i, tracker in enumerate(trackers):
        tid = tracker["id"]
        logger.info(f"  [{i+1}/{len(trackers)}] GF #{tid}: "
                    f"{tracker['origin']}→{tracker['destination']} {tracker['outbound_date']}")
        try:
            snap = fetch_gf_price(tracker)
            save_gf_snapshot(tid, snap)
            status = snap.get("status", "error")
            if status == "ok":
                _log_provider("google_flights", "ok", tid, "source=serpapi", snap.get("total_price"))
                _check_and_notify_generic(tracker, snap, tracker_type="google_flight")
            else:
                _log_provider("google_flights", status, tid, snap.get("error_message", ""))
        except Exception as e:
            logger.error(f"  ❌ GF #{tid}: {e}", exc_info=True)
            save_gf_snapshot(tid, {"status": "error", "error_message": str(e)})

        if i < len(trackers) - 1:
            time.sleep(random.uniform(5, 15))


# ── Homair / Camping Trackers ─────────────────────────────────────────────────

def run_homair_trackers(user_id: int | None = None):
    from routes.accommodations import fetch_homair_price
    trackers = list_homair_trackers(active_only=True, user_id=user_id)
    logger.info(f"⛺ Homair: {len(trackers)} aktive Tracker")

    for i, tracker in enumerate(trackers):
        tid = tracker["id"]
        logger.info(f"  [{i+1}/{len(trackers)}] Homair #{tid}: {tracker.get('region')}")
        try:
            snap = fetch_homair_price(tracker)
            save_homair_snapshot(tid, snap)
            status = snap.get("status", "error")
            if status == "ok":
                _log_provider("homair", "ok", tid, "source=serpapi_hotels", snap.get("total_price"))
                _check_and_notify_generic(tracker, snap, tracker_type="camping")
            else:
                _log_provider("homair", status, tid, snap.get("error_message", ""))
        except Exception as e:
            logger.error(f"  ❌ Homair #{tid}: {e}", exc_info=True)
            save_homair_snapshot(tid, {"status": "error", "error_message": str(e)})

        if i < len(trackers) - 1:
            time.sleep(random.uniform(5, 15))


# ── Booking / Hotel Trackers ──────────────────────────────────────────────────

def run_booking_trackers(user_id: int | None = None):
    from routes.accommodations import fetch_booking_price
    trackers = list_booking_trackers(active_only=True, user_id=user_id)
    logger.info(f"🏨 Booking: {len(trackers)} aktive Tracker")

    for i, tracker in enumerate(trackers):
        tid = tracker["id"]
        logger.info(f"  [{i+1}/{len(trackers)}] Booking #{tid}: {tracker.get('destination')}")
        try:
            snap = fetch_booking_price(tracker)
            save_booking_snapshot(tid, snap)
            status = snap.get("status", "error")
            if status == "ok":
                _log_provider("booking", "ok", tid, "source=serpapi", snap.get("total_price"))
                _check_and_notify_generic(tracker, snap, tracker_type="hotel")
            else:
                _log_provider("booking", status, tid, snap.get("error_message", ""))
        except Exception as e:
            logger.error(f"  ❌ Booking #{tid}: {e}", exc_info=True)
            save_booking_snapshot(tid, {"status": "error", "error_message": str(e)})

        if i < len(trackers) - 1:
            time.sleep(random.uniform(5, 12))


# ── Notification Helpers ──────────────────────────────────────────────────────

def _check_and_notify(tracker: dict, snap: dict, prev_price: float | None):
    """Ryanair-specific notification (has threshold_price field)."""
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


def _check_and_notify_generic(tracker: dict, snap: dict, tracker_type: str):
    """Generic notification for non-Ryanair trackers (wish_price only)."""
    new_price = snap.get("total_price")
    wish_price = tracker.get("wish_price")
    if not new_price or not wish_price:
        return
    if new_price <= wish_price:
        try:
            from notifications import notify_threshold_reached
            notify_threshold_reached(tracker, price=new_price, threshold=wish_price)
        except Exception as ne:
            logger.warning(f"  ⚠️ Wish-price alert fehlgeschlagen ({tracker_type}): {ne}")


# ── Master Run Function ───────────────────────────────────────────────────────

def run_all_trackers(user_id: int | None = None):
    """
    Run all tracker types for a user (or all users).
    Called by APScheduler or manually via API.
    Each provider runs independently — errors in one don't affect others.
    """
    logger.info(f"🕐 Scheduler startet (user_id={user_id or 'all'})")

    for runner, name in [
        (run_ryanair_trackers, "Ryanair"),
        (run_gf_trackers, "Google Flights"),
        (run_homair_trackers, "Homair/Camping"),
        (run_booking_trackers, "Booking/Hotels"),
    ]:
        try:
            runner(user_id=user_id)
        except Exception as e:
            logger.error(f"❌ {name} runner crashed: {e}", exc_info=True)
            # Continue with next provider

    if user_id:
        update_scheduler_last_run(user_id)

    logger.info("✅ Scheduler-Lauf abgeschlossen")


def run_single_tracker(tracker_id: int):
    """Einzelnen Ryanair-Tracker manuell abrufen."""
    from database import get_tracker
    from scraper import fetch_flights
    tracker = get_tracker(tracker_id)
    if not tracker:
        raise ValueError(f"Tracker #{tracker_id} nicht gefunden")
    result = fetch_flights(tracker)
    snap = result["snapshot"]
    snap_id = save_snapshot(tracker_id, snap)
    snap["id"] = snap_id
    return snap


# ── Cleanup Job ───────────────────────────────────────────────────────────────

def run_cleanup_job():
    """
    Delete price history and snapshots older than 180 days.
    Runs daily at 03:00 via APScheduler.
    """
    logger.info("🧹 Cleanup-Job startet (>180 Tage)")
    try:
        ph_count = cleanup_old_price_history(days=180)
        snap_counts = cleanup_old_snapshots(days=180)
        total_snaps = sum(snap_counts.values())
        logger.info(f"  ✅ price_history: {ph_count} Einträge gelöscht")
        logger.info(f"  ✅ snapshots: {total_snaps} Einträge gelöscht {snap_counts}")
    except Exception as e:
        logger.error(f"  ❌ Cleanup fehlgeschlagen: {e}", exc_info=True)
