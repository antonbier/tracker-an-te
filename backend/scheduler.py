"""
WanderSuite — APScheduler Background Jobs

Per-user interval support: each user can configure their own update interval.
Cleanup job: runs daily at 03:00 to delete history older than 180 days.
Deep logging: per-provider status, scraping status, errors.
"""

import logging
import random
import time

from core.database import db
from crud.settings import (
    get_user_scheduler_settings,
    update_scheduler_last_run,
)
from crud.trackers import (
    list_trackers,
    save_price_snapshot as save_snapshot,
    list_gf_trackers,
    save_gf_snapshot,
    list_homair_trackers,
    save_homair_snapshot,
    list_booking_trackers,
    save_booking_snapshot,
    cleanup_old_price_history,
    cleanup_old_snapshots,
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
            # BUG 2 FIX: Letzten bekannten Preis VOR dem Scrape aus DB holen.
            # fetch_flights() liefert KEIN previous_price-Feld — daher müssen
            # wir den Vergleichswert selbst aus der Snapshot-History ziehen.
            prev_snap = get_latest_snapshot(tid)
            prev_price = float(prev_snap["total_price"]) if prev_snap and prev_snap.get("total_price") else None
            logger.info(f"  [Ryanair] #{tid} prev_price={prev_price}")

            result = fetch_flights(tracker)
            snap = result["snapshot"]
            status = result.get("status", "error")
            price = snap.get("total_price")

            if status == "ok":
                # Nur bei Erfolg speichern — Fehler ueberschreiben niemals die Historie
                save_snapshot(tid, snap)
                _log_provider("ryanair", "ok", tid, "scrape=success", price)
                # BUG 2 FIX: prev_price aus DB statt aus result.get("previous_price")
                logger.info(f"  [Notify-Check] #{tid} new={price} prev={prev_price} "
                            f"wish={tracker.get('wish_price')} threshold={tracker.get('threshold_price')}")
                _check_and_notify(tracker, snap, prev_price)
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
            # BUG 2 FIX: prev_price vor Scrape aus DB
            prev_gf = _gf_snap(tid)
            prev_gf_price = float(prev_gf["total_price"]) if prev_gf and prev_gf.get("total_price") else None

            snap = fetch_google_flights(tracker, api_key=api_key)
            status = snap.get("status", "error")
            if status == "ok":
                # Nur bei Erfolg speichern
                save_gf_snapshot(tid, snap)
                _log_provider("google_flights", "ok", tid, "source=serpapi", snap.get("total_price"))
                _check_and_notify_generic(tracker, snap, prev_price=prev_gf_price)
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
            prev_snap = get_latest_homair_snapshot(tid)
            prev_price = float(prev_snap["total_price"]) if prev_snap and prev_snap.get("total_price") else None
            snap = fetch_homair(tracker, api_key=api_key)
            status = snap.get("status", "error")
            if status == "ok":
                # Nur bei Erfolg speichern
                save_homair_snapshot(tid, snap)
                _log_provider("homair", "ok", tid, "source=serpapi", snap.get("total_price"))
                _check_and_notify_generic(tracker, snap, prev_price=prev_price)
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
            prev_snap = get_latest_booking_snapshot(tid)
            prev_price = float(prev_snap["total_price"]) if prev_snap and prev_snap.get("total_price") else None
            snap = fetch_booking(tracker, api_key=api_key)
            status = snap.get("status", "error")
            if status == "ok":
                # Nur bei Erfolg speichern
                save_booking_snapshot(tid, snap)
                _log_provider("booking", "ok", tid, "source=serpapi", snap.get("total_price"))
                _check_and_notify_generic(tracker, snap, prev_price=prev_price)
            else:
                _log_provider("booking", status, tid, snap.get("error_message", ""))
        except Exception as e:
            logger.error(f"  ❌ Booking #{tid}: {e}", exc_info=True)
            # Kein Error-Snapshot — alte Preisdaten bleiben erhalten

        if i < len(trackers) - 1:
            time.sleep(random.uniform(5, 12))


# ── Notification Helpers ──────────────────────────────────────────────────────

def _evaluate_price_drop(
    tracker_id: int,
    new_price: float,
    prev_price: float | None,
) -> tuple[bool, float, float]:
    """
    Prüft ob ein Preissturz vorliegt.
    Gibt (should_notify, diff, pct) zurück.
    Reiner Evaluations-Helper ohne Side-Effects.
    """
    if prev_price is None:
        logger.info(f"  [Notify] #{tracker_id} kein Vergleichspreis — Preissturz-Check übersprungen")
        return False, 0.0, 0.0
    if new_price < prev_price:
        diff = round(prev_price - new_price, 2)
        pct  = round((diff / prev_price) * 100, 1)
        logger.info(f"  📉 PREISSTURZ #{tracker_id}: {prev_price:.2f}→{new_price:.2f} (-{diff:.2f}€ / -{pct}%)")
        return True, diff, pct
    logger.debug(f"  [Notify] #{tracker_id} kein Preissturz ({prev_price:.2f}→{new_price:.2f})")
    return False, 0.0, 0.0


def _evaluate_threshold(
    tracker_id: int,
    new_price: float,
    prev_price: float | None,
    threshold: float,
) -> bool:
    """
    Prüft ob Wunschpreis/Threshold erstmalig unterschritten wurde.
    Gibt True zurück wenn Notification gesendet werden soll.
    Verhindert Spam: kein Alert wenn Preis schon vorher unter Threshold war.
    """
    if new_price <= threshold:
        already_below = prev_price is not None and prev_price <= threshold
        if not already_below:
            logger.info(f"  🎯 ZIEL ERREICHT #{tracker_id}: {new_price:.2f}€ ≤ {threshold:.2f}€")
            return True
        logger.debug(f"  [Notify] #{tracker_id} Ziel bereits unterschritten — kein erneuter Alert")
    else:
        logger.debug(f"  [Notify] #{tracker_id} {new_price:.2f}€ über Ziel {threshold:.2f}€")
    return False


def _check_and_notify(tracker: dict, snap: dict, prev_price: float | None):
    """
    Orchestriert Preissturz- und Threshold-Checks für einen Tracker.
    Delegiert Evaluation an _evaluate_price_drop() + _evaluate_threshold(),
    kümmert sich selbst nur um das Senden der Notifications.
    """

    new_price = snap.get("total_price")
    if not new_price:
        logger.debug(f"  [Notify] Kein neuer Preis — übersprungen")
        return

    # ── Preissturz ────────────────────────────────────────────────────────────
    should_drop, diff, pct = _evaluate_price_drop(tracker["id"], new_price, prev_price)
    if should_drop:
        try:
            notify_price_drop(tracker, old_price=prev_price, new_price=new_price)
        except Exception as ne:
            logger.warning(f"  ⚠️ Preissturz-Notification fehlgeschlagen: {ne}")

    # ── Threshold / Wunschpreis ───────────────────────────────────────────────
    threshold = tracker.get("threshold_price") or tracker.get("wish_price")
    if threshold and _evaluate_threshold(tracker["id"], new_price, prev_price, threshold):
        try:
            notify_threshold_reached(tracker, price=new_price, threshold=threshold)
        except Exception as ne:
            logger.warning(f"  ⚠️ Threshold-Alert fehlgeschlagen: {ne}")


def _check_and_notify_generic(tracker: dict, snap: dict, prev_price: float | None = None):
    """BUG 2 FIX: prev_price-Parameter ergänzt für Preissturz-Checks."""
    new_price = snap.get("total_price")
    if not new_price:
        return

    # Preissturz-Check (falls prev_price verfügbar)
    if prev_price is not None and new_price < prev_price:
        diff = round(prev_price - new_price, 2)
        logger.info(f"  📉 PREISSTURZ #{tracker.get('id')}: {prev_price:.2f}→{new_price:.2f} (-{diff:.2f}€)")
        try:
            notify_price_drop(tracker, old_price=prev_price, new_price=new_price)
        except Exception as ne:
            logger.warning(f"  ⚠️ Preissturz-Notification fehlgeschlagen: {ne}")

    # Wunschpreis-Check
    wish_price = tracker.get("wish_price")
    if not wish_price:
        return
    if new_price <= wish_price:
        already_below = prev_price is not None and prev_price <= wish_price
        if not already_below:
            logger.info(f"  🎯 ZIEL ERREICHT #{tracker.get('id')}: {new_price:.2f}€ ≤ {wish_price:.2f}€")
            try:
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
            with db() as conn:
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


