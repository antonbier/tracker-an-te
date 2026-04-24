"""
WanderSuite — crud/trackers.py
All tracker CRUD, snapshot, price-history and booking-state functions
for all 4 provider types: flight (Ryanair), google_flight, camping (Homair), hotel (Booking).
"""

import json
import logging
from core.database import db

logger = logging.getLogger(__name__)

# ── Generic helpers (private) ─────────────────────────────────────────────────

def _tracker_table(tracker_type: str) -> str | None:
    return {
        "flight":        "trackers",
        "google_flight": "gf_trackers",
        "camping":       "homair_trackers",
        "hotel":         "booking_trackers",
    }.get(tracker_type)


def _snapshot_table(tracker_type: str) -> str | None:
    """Maps tracker_type → snapshot table name."""
    return {
        "flight":        "price_snapshots",
        "google_flight": "gf_snapshots",
        "camping":       "homair_snapshots",
        "hotel":         "booking_snapshots",
    }.get(tracker_type)


# ── Generische CRUD-Operationen (gelten für alle 4 Tracker-Typen) ─────────
# Alle type-spezifischen Wrapper-Funktionen delegieren hierher.

def _list_trackers(table: str, active_only: bool = False,
                   user_id: int | None = None) -> list[dict]:
    """Generisches list für jeden Tracker-Tabellennamen."""
    with db() as conn:
        parts, params = [], []
        if user_id:
            parts.append("user_id=?"); params.append(user_id)
        if active_only:
            parts.append("active=1")
        where = ("WHERE " + " AND ".join(parts)) if parts else ""
        rows = conn.execute(
            f"SELECT * FROM {table} {where} ORDER BY created_at DESC", params
        ).fetchall()
    return [dict(r) for r in rows]


def _get_tracker(table: str, tracker_id: int,
                 user_id: int | None = None) -> dict | None:
    """Generisches get für jeden Tracker-Tabellennamen."""
    with db() as conn:
        if user_id:
            row = conn.execute(
                f"SELECT * FROM {table} WHERE id=? AND user_id=?",
                (tracker_id, user_id)
            ).fetchone()
        else:
            row = conn.execute(
                f"SELECT * FROM {table} WHERE id=?", (tracker_id,)
            ).fetchone()
    return dict(row) if row else None


def _delete_tracker(table: str, tracker_id: int,
                    user_id: int | None = None) -> bool:
    """Generisches delete für jeden Tracker-Tabellennamen."""
    with db() as conn:
        if user_id:
            return conn.execute(
                f"DELETE FROM {table} WHERE id=? AND user_id=?",
                (tracker_id, user_id)
            ).rowcount > 0
        return conn.execute(
            f"DELETE FROM {table} WHERE id=?", (tracker_id,)
        ).rowcount > 0


def _toggle_tracker(table: str, tracker_id: int, active: bool,
                    user_id: int | None = None) -> bool:
    """Generisches toggle (active/inactive) für jeden Tracker-Tabellennamen."""
    val = 1 if active else 0
    with db() as conn:
        if user_id:
            return conn.execute(
                f"UPDATE {table} SET active=? WHERE id=? AND user_id=?",
                (val, tracker_id, user_id)
            ).rowcount > 0
        return conn.execute(
            f"UPDATE {table} SET active=? WHERE id=?",
            (val, tracker_id)
        ).rowcount > 0


def _get_latest_snapshot(snap_table: str, tracker_id: int) -> dict | None:
    """Generisch: neuester status='ok' Snapshot, Fallback auf neuesten Eintrag."""
    with db() as conn:
        row = conn.execute(
            f"SELECT * FROM {snap_table} WHERE tracker_id=? AND status='ok'"
            " ORDER BY fetched_at DESC LIMIT 1",
            (tracker_id,)
        ).fetchone()
        if not row:
            row = conn.execute(
                f"SELECT * FROM {snap_table} WHERE tracker_id=?"
                " ORDER BY fetched_at DESC LIMIT 1",
                (tracker_id,)
            ).fetchone()
    return dict(row) if row else None


# ── Ryanair (flight) Tracker ──────────────────────────────────────────────────

def create_tracker(data: dict, user_id: int = 1) -> int:
    with db() as conn:
        baggage_json = json.dumps(data.get("baggage", []))
        cur = conn.execute(
            """INSERT INTO trackers
               (user_id, origin, destination, outbound_date, return_date,
                adults, children, baggage_json, seat_cost, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))""",
            (user_id, data["origin"], data["destination"],
             data["outbound_date"], data.get("return_date"),
             data.get("adults", 1), data.get("children", 0),
             baggage_json, data.get("seat_cost", 0))
        )
    return cur.lastrowid


def list_trackers(active_only: bool = False, user_id: int | None = None) -> list[dict]:
    return _list_trackers("trackers", active_only=active_only, user_id=user_id)


def get_tracker(tracker_id: int, user_id: int | None = None) -> dict | None:
    return _get_tracker("trackers", tracker_id, user_id=user_id)


def delete_tracker(tracker_id: int, user_id: int | None = None) -> bool:
    return _delete_tracker("trackers", tracker_id, user_id=user_id)


def toggle_tracker(tracker_id: int, active: bool, user_id: int | None = None) -> bool:
    return _toggle_tracker("trackers", tracker_id, active, user_id=user_id)


def set_tracker_threshold(tracker_id: int, price: float | None, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "UPDATE trackers SET threshold_price=? WHERE id=? AND user_id=?",
                (price, tracker_id, user_id)
            ).rowcount > 0
        return conn.execute(
            "UPDATE trackers SET threshold_price=? WHERE id=?", (price, tracker_id)
        ).rowcount > 0


def set_tracker_wish_price(tracker_id: int, table: str, wish_price: float | None,
                            user_id: int | None = None) -> bool:
    """Set wish_price on any tracker table. table must be one of the known tracker tables."""
    allowed = {"trackers", "gf_trackers", "homair_trackers", "booking_trackers"}
    if table not in allowed:
        raise ValueError(f"Unknown tracker table: {table}")
    with db() as conn:
        if user_id:
            return conn.execute(
                f"UPDATE {table} SET wish_price=? WHERE id=? AND user_id=?",
                (wish_price, tracker_id, user_id)
            ).rowcount > 0
        return conn.execute(
            f"UPDATE {table} SET wish_price=? WHERE id=?", (wish_price, tracker_id)
        ).rowcount > 0


# ── Price Snapshots ───────────────────────────────────────────────────────────

def save_price_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO price_snapshots
               (tracker_id, fetched_at, flight_price, baggage_price, seat_price,
                total_price, outbound_flight, return_flight, currency,
                baggage_fallback, status, error_message, raw_json,
                departure_time, arrival_time, flight_number)
               VALUES (?,datetime('now'),?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (tracker_id,
             snap.get("flight_price"), snap.get("baggage_price"),
             snap.get("seat_price", 0), snap.get("total_price"),
             snap.get("outbound_flight"), snap.get("return_flight"),
             snap.get("currency", "EUR"), snap.get("baggage_fallback", 0),
             snap.get("status", "ok"), snap.get("error_message"),
             json.dumps(snap.get("raw")) if snap.get("raw") else None,
             snap.get("departure_time"), snap.get("arrival_time"),
             snap.get("flight_number") or snap.get("outbound_flight"))
        )
        snap_id = cur.lastrowid

        # Also record in price_history if successful
        if snap.get("status", "ok") == "ok" and snap.get("total_price") is not None:
            # Get user_id from tracker
            row = conn.execute("SELECT user_id FROM trackers WHERE id=?", (tracker_id,)).fetchone()
            uid = row[0] if row else 1
            conn.execute(
                """INSERT INTO price_history (user_id, tracker_type, tracker_id, price, currency, provider, status, fetched_at)
                   VALUES (?,?,?,?,?,?,?,datetime('now'))""",
                (uid, "flight", tracker_id, snap["total_price"],
                 snap.get("currency", "EUR"), "ryanair", "ok")
            )
    return snap_id


def get_latest_snapshot(tracker_id: int) -> dict | None:
    """Neuester fehlerfreier Snapshot (status='ok'). Fallback auf neuesten Eintrag."""    
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM price_snapshots WHERE tracker_id=? AND status='ok' ORDER BY fetched_at DESC LIMIT 1",
            (tracker_id,)
        ).fetchone()
        if not row:
            row = conn.execute(
                "SELECT * FROM price_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT 1",
                (tracker_id,)
            ).fetchone()
    return dict(row) if row else None

def get_snapshots(tracker_id: int, limit: int = 90) -> list[dict]:
    """Return price_snapshots for a Ryanair tracker, newest-first."""
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM price_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT ?",
            (tracker_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]



def get_price_history(tracker_type: str, tracker_id: int, user_id: int | None = None,
                       limit: int = 90) -> list[dict]:
    """Get price history for a tracker, ordered by date ascending."""
    with db() as conn:
        if user_id:
            rows = conn.execute(
                """SELECT fetched_at, price, currency, provider, status, error_msg
                   FROM price_history
                   WHERE tracker_type=? AND tracker_id=? AND user_id=?
                   ORDER BY fetched_at ASC LIMIT ?""",
                (tracker_type, tracker_id, user_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT fetched_at, price, currency, provider, status, error_msg
                   FROM price_history
                   WHERE tracker_type=? AND tracker_id=?
                   ORDER BY fetched_at ASC LIMIT ?""",
                (tracker_type, tracker_id, limit)
            ).fetchall()
    return [dict(r) for r in rows]


def record_price_history(user_id: int, tracker_type: str, tracker_id: int,
                          price: float, currency: str = "EUR",
                          provider: str | None = None,
                          status: str = "ok", error_msg: str | None = None) -> None:
    """Directly record a price history entry (used by all tracker types)."""
    with db() as conn:
        conn.execute(
            """INSERT INTO price_history
               (user_id, tracker_type, tracker_id, price, currency, provider, status, error_msg, fetched_at)
               VALUES (?,?,?,?,?,?,?,?,datetime('now'))""",
            (user_id, tracker_type, tracker_id, price, currency, provider, status, error_msg)
        )



# ── Price History Cleanup ─────────────────────────────────────────────────────

def cleanup_old_price_history(days: int = 60) -> int:
    """Delete price_history entries older than `days` days. Returns count deleted."""
    with db() as conn:
        result = conn.execute(
            "DELETE FROM price_history WHERE fetched_at < datetime('now', ?)",
            (f"-{days} days",)
        )
    return result.rowcount


def cleanup_old_snapshots(days: int = 60) -> dict:
    """Delete price snapshots older than `days` days across all tables. Returns counts."""
    tables = [
        ("price_snapshots", "fetched_at"),
        ("gf_snapshots", "fetched_at"),
        ("homair_snapshots", "fetched_at"),
        ("booking_snapshots", "fetched_at"),
    ]
    counts = {}
    with db() as conn:
        for table, col in tables:
            try:
                r = conn.execute(
                    f"DELETE FROM {table} WHERE {col} < datetime('now', ?)",
                    (f"-{days} days",)
                )
                counts[table] = r.rowcount
            except Exception:
                counts[table] = 0
    return counts



# ── Google Flights Tracker ────────────────────────────────────────────────────

def create_gf_tracker(data: dict, user_id: int = 1) -> int:
    import json as _json
    baggage_json = _json.dumps({
        "baggage": data.get("baggage", "none"),
        "baggage_10kg": data.get("baggage_10kg", 0),
        "baggage_20kg": data.get("baggage_20kg", 0),
        "baggage_23kg": data.get("baggage_23kg", 0),
    })
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO gf_trackers
               (user_id, origin, destination, outbound_date, return_date,
                adults, children, seat_cost, baggage_json, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))""",
            (user_id, data["origin"], data["destination"],
             data["outbound_date"], data.get("return_date"),
             data.get("adults", 1), data.get("children", 0),
             data.get("seat_cost", 0.0), baggage_json)
        )
    return cur.lastrowid


def list_gf_trackers(active_only: bool = False, user_id: int | None = None) -> list[dict]:
    return _list_trackers("gf_trackers", active_only=active_only, user_id=user_id)


def get_gf_tracker(tracker_id: int, user_id: int | None = None) -> dict | None:
    return _get_tracker("gf_trackers", tracker_id, user_id=user_id)


def delete_gf_tracker(tracker_id: int, user_id: int | None = None) -> bool:
    return _delete_tracker("gf_trackers", tracker_id, user_id=user_id)


def toggle_gf_tracker(tracker_id: int, active: bool, user_id: int | None = None) -> bool:
    return _toggle_tracker("gf_trackers", tracker_id, active, user_id=user_id)


def save_gf_snapshot(tracker_id: int, snap: dict) -> int:
    import json as _json
    _lay_airports = snap.get("layover_airports")
    _lay_durations = snap.get("layover_durations")
    lay_airports_json = _json.dumps(_lay_airports) if _lay_airports is not None else None
    lay_durations_json = _json.dumps(_lay_durations) if _lay_durations is not None else None
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO gf_snapshots
               (tracker_id, fetched_at, total_price, outbound_flight, return_flight,
                airline, departure_time, arrival_time, duration_min, stops,
                layover_airports, layover_durations,
                currency, status, error_message)
               VALUES (?,datetime('now'),?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (tracker_id, snap.get("total_price"), snap.get("outbound_flight"),
             snap.get("return_flight"), snap.get("airline"),
             snap.get("departure_time"), snap.get("arrival_time"),
             snap.get("duration_min"), snap.get("stops", 0),
             lay_airports_json, lay_durations_json,
             snap.get("currency", "EUR"),
             snap.get("status", "ok"), snap.get("error_message"))
        )
        snap_id = cur.lastrowid

        # Also record in price_history
        if snap.get("status", "ok") == "ok" and snap.get("total_price") is not None:
            row = conn.execute("SELECT user_id FROM gf_trackers WHERE id=?", (tracker_id,)).fetchone()
            uid = row[0] if row else 1
            conn.execute(
                """INSERT INTO price_history (user_id, tracker_type, tracker_id, price, currency, provider, status, fetched_at)
                   VALUES (?,?,?,?,?,?,?,datetime('now'))""",
                (uid, "google_flight", tracker_id, snap["total_price"],
                 snap.get("currency", "EUR"), "google_flights", "ok")
            )
    return snap_id


def get_latest_gf_snapshot(tracker_id: int) -> dict | None:
    """Neuester fehlerfreier GF-Snapshot (status='ok'). Fallback auf neuesten Eintrag."""
    return _get_latest_snapshot("gf_snapshots", tracker_id)

def get_gf_history(tracker_id: int, limit: int = 90) -> list[dict]:
    """Compatibility alias: return GF snapshots from gf_snapshots table."""
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM gf_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT ?",
            (tracker_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]




# ── Homair (camping) Tracker ──────────────────────────────────────────────────

def create_homair_tracker(data: dict, user_id: int = 1) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO homair_trackers
               (user_id, region, accommodation_type, checkin_date, checkout_date,
                adults, children, campsite_name, created_at)
               VALUES (?,?,?,?,?,?,?,?,datetime('now'))""",
            (user_id, data["region"], data.get("accommodation_type", "mobilheim-standard"),
             data["checkin_date"], data["checkout_date"],
             data.get("adults", 2), data.get("children", 0),
             data.get("campsite_name"))
        )
    return cur.lastrowid


def list_homair_trackers(active_only: bool = False, user_id: int | None = None) -> list[dict]:
    return _list_trackers("homair_trackers", active_only=active_only, user_id=user_id)


def get_homair_tracker(tracker_id: int, user_id: int | None = None) -> dict | None:
    return _get_tracker("homair_trackers", tracker_id, user_id=user_id)


def delete_homair_tracker(tracker_id: int, user_id: int | None = None) -> bool:
    return _delete_tracker("homair_trackers", tracker_id, user_id=user_id)


def toggle_homair_tracker(tracker_id: int, active: bool, user_id: int | None = None) -> bool:
    return _toggle_tracker("homair_trackers", tracker_id, active, user_id=user_id)


def save_homair_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO homair_snapshots
               (tracker_id, fetched_at, total_price, currency, status, error_message, note)
               VALUES (?,datetime('now'),?,?,?,?,?)""",
            (tracker_id, snap.get("total_price"),
             snap.get("currency", "EUR"), snap.get("status", "ok"),
             snap.get("error_message"), snap.get("note"))
        )
        snap_id = cur.lastrowid

        # Also record in price_history
        if snap.get("status", "ok") == "ok" and snap.get("total_price") is not None:
            row = conn.execute("SELECT user_id FROM homair_trackers WHERE id=?", (tracker_id,)).fetchone()
            uid = row[0] if row else 1
            conn.execute(
                """INSERT INTO price_history (user_id, tracker_type, tracker_id, price, currency, provider, status, fetched_at)
                   VALUES (?,?,?,?,?,?,?,datetime('now'))""",
                (uid, "camping", tracker_id, snap["total_price"],
                 snap.get("currency", "EUR"), "homair", "ok")
            )
    return snap_id


def get_latest_homair_snapshot(tracker_id: int) -> dict | None:
    """Neuester fehlerfreier Homair-Snapshot (status='ok'). Fallback auf neuesten Eintrag."""
    return _get_latest_snapshot("homair_snapshots", tracker_id)


# ── Booking (hotel) Tracker ───────────────────────────────────────────────────

def create_booking_tracker(data: dict, user_id: int = 1) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO booking_trackers
               (user_id, destination, checkin_date, checkout_date,
                adults, rooms, source, hotel_name, created_at)
               VALUES (?,?,?,?,?,?,?,?,datetime('now'))""",
            (user_id, data["destination"],
             data["checkin_date"], data["checkout_date"],
             data.get("adults", 2), data.get("rooms", 1),
             data.get("source", "booking"),
             data.get("hotel_name"))
        )
    return cur.lastrowid


def list_booking_trackers(active_only: bool = False, user_id: int | None = None) -> list[dict]:
    return _list_trackers("booking_trackers", active_only=active_only, user_id=user_id)


def get_booking_tracker(tracker_id: int, user_id: int | None = None) -> dict | None:
    return _get_tracker("booking_trackers", tracker_id, user_id=user_id)


def delete_booking_tracker(tracker_id: int, user_id: int | None = None) -> bool:
    return _delete_tracker("booking_trackers", tracker_id, user_id=user_id)


def toggle_booking_tracker(tracker_id: int, active: bool, user_id: int | None = None) -> bool:
    return _toggle_tracker("booking_trackers", tracker_id, active, user_id=user_id)


def save_booking_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO booking_snapshots
               (tracker_id, fetched_at, total_price, hotel_name, hotel_rating,
                currency, status, error_message)
               VALUES (?,datetime('now'),?,?,?,?,?,?)""",
            (tracker_id, snap.get("total_price"), snap.get("hotel_name"),
             snap.get("hotel_rating"), snap.get("currency", "EUR"),
             snap.get("status", "ok"), snap.get("error_message"))
        )
        snap_id = cur.lastrowid

        # Also record in price_history
        if snap.get("status", "ok") == "ok" and snap.get("total_price") is not None:
            row = conn.execute("SELECT user_id FROM booking_trackers WHERE id=?", (tracker_id,)).fetchone()
            uid = row[0] if row else 1
            conn.execute(
                """INSERT INTO price_history (user_id, tracker_type, tracker_id, price, currency, provider, status, fetched_at)
                   VALUES (?,?,?,?,?,?,?,datetime('now'))""",
                (uid, "hotel", tracker_id, snap["total_price"],
                 snap.get("currency", "EUR"),
                 snap.get("source", "booking"), "ok")
            )
    return snap_id


def get_latest_booking_snapshot(tracker_id: int) -> dict | None:
    """Neuester fehlerfreier Booking-Snapshot (status='ok'). Fallback auf neuesten Eintrag."""
    return _get_latest_snapshot("booking_snapshots", tracker_id)


# ── Tracker Booking State ─────────────────────────────────────────────────────

def mark_tracker_booked(
    tracker_id: int,
    tracker_type: str,
    booked_price: float,
    trip_id: int | None = None,
) -> bool:
    """Mark a tracker as booked with a confirmed price."""
    tbl = _tracker_table(tracker_type)
    if not tbl:
        return False
    with db() as conn:
        r = conn.execute(
            f"UPDATE {tbl} SET is_booked=1, booked_price=? WHERE id=?",
            (round(booked_price, 2), tracker_id)
        )
        if trip_id and r.rowcount:
            conn.execute(
                f"UPDATE {tbl} SET trip_id=? WHERE id=?",
                (trip_id, tracker_id)
            )
    return r.rowcount > 0


def unmark_tracker_booked(tracker_id: int, tracker_type: str) -> bool:
    """Reset booking state on a tracker."""
    tbl = _tracker_table(tracker_type)
    if not tbl:
        return False
    with db() as conn:
        r = conn.execute(
            f"UPDATE {tbl} SET is_booked=0, booked_price=NULL WHERE id=?",
            (tracker_id,)
        )
    return r.rowcount > 0


def link_tracker_to_trip(tracker_id: int, tracker_type: str, trip_id: int | None) -> bool:
    """Associate/disassociate a tracker with a ws_trip."""
    tbl = _tracker_table(tracker_type)
    if not tbl:
        return False
    with db() as conn:
        r = conn.execute(
            f"UPDATE {tbl} SET trip_id=? WHERE id=?",
            (trip_id, tracker_id)
        )
    return r.rowcount > 0

# ── Cross-type trip linking ───────────────────────────────────────────────────

def get_trackers_for_trip(trip_id: int) -> dict:
    """
    Return all trackers linked to a ws_trip, grouped by type,
    including latest_snapshot for each tracker.
    """
    result = {"flight": None, "hotel": None, "camping": None, "car": None}

    with db() as conn:
        # Ryanair
        row = conn.execute(
            "SELECT *, 'flight' as _type FROM trackers WHERE trip_id=? ORDER BY id DESC LIMIT 1",
            (trip_id,)
        ).fetchone()
        if row:
            d = dict(row)
            d["latest_snapshot"] = get_latest_snapshot(d["id"])
            result["flight"] = d

        # Google Flights (fallback if no Ryanair)
        if not result["flight"]:
            row = conn.execute(
                "SELECT *, 'google_flight' as _type FROM gf_trackers WHERE trip_id=? ORDER BY id DESC LIMIT 1",
                (trip_id,)
            ).fetchone()
            if row:
                d = dict(row)
                d["latest_snapshot"] = get_latest_gf_snapshot(d["id"])
                result["flight"] = d

        # Hotel / Camping
        snap_fns = {
            "booking_trackers": ("hotel",   get_latest_booking_snapshot),
            "homair_trackers":  ("camping", get_latest_homair_snapshot),
        }
        for tbl, (key, snap_fn) in snap_fns.items():
            row = conn.execute(
                f"SELECT *, '{key}' as _type FROM {tbl} WHERE trip_id=? ORDER BY id DESC LIMIT 1",
                (trip_id,)
            ).fetchone()
            if row:
                d = dict(row)
                d["latest_snapshot"] = snap_fn(d["id"])
                result[key] = d

    return result



