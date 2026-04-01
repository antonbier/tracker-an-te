"""
WanderSuite — Database Layer (Multi-User)
SQLite via sqlite3. All content tables have user_id.

Global tables (no user_id): settings, webauthn_credentials, webauthn_challenges
Per-user tables:            trackers, gf_trackers, homair_trackers, booking_trackers,
                            detected_trips, user_data

Migration strategy: ADD COLUMN user_id INTEGER DEFAULT 1
  → existing data assigned to user_id=1 (first admin)
  → AUTH_ENABLED=false: use GUEST_USER_ID=0, sees all data
"""

import sqlite3
import json
import os
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "/app/data/tracker.db")

# When AUTH_ENABLED=false, all requests use this virtual user ID
# Routes pass user_id=None for guest → DB functions use 0 = see all
GUEST_USER_ID = 0


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _user_filter(user_id: int | None) -> tuple[str, list]:
    """
    Returns (WHERE clause, params) for user filtering.
    user_id=None or 0 → no filter (admin/guest sees all)
    user_id=N        → WHERE user_id=N
    """
    if not user_id:
        return ("", [])
    return ("WHERE user_id=?", [user_id])


def init_db():
    """Create all tables + run safe migrations."""
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS trackers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL DEFAULT 1,
                origin          TEXT    NOT NULL,
                destination     TEXT    NOT NULL,
                outbound_date   TEXT    NOT NULL,
                return_date     TEXT,
                adults          INTEGER NOT NULL DEFAULT 1,
                children        INTEGER NOT NULL DEFAULT 0,
                baggage_json    TEXT    NOT NULL DEFAULT '[]',
                seat_cost       REAL    NOT NULL DEFAULT 0,
                threshold_price REAL             DEFAULT NULL,
                active          INTEGER NOT NULL DEFAULT 1,
                created_at      TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS price_snapshots (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                tracker_id       INTEGER NOT NULL REFERENCES trackers(id) ON DELETE CASCADE,
                fetched_at       TEXT    NOT NULL,
                flight_price     REAL,
                baggage_price    REAL,
                seat_price       REAL    DEFAULT 0,
                total_price      REAL,
                outbound_flight  TEXT,
                return_flight    TEXT,
                currency         TEXT    DEFAULT 'EUR',
                baggage_fallback INTEGER DEFAULT 0,
                status           TEXT    NOT NULL DEFAULT 'ok',
                error_message    TEXT,
                raw_json         TEXT
            );

            CREATE TABLE IF NOT EXISTS gf_trackers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL DEFAULT 1,
                origin          TEXT    NOT NULL,
                destination     TEXT    NOT NULL,
                outbound_date   TEXT    NOT NULL,
                return_date     TEXT,
                adults          INTEGER NOT NULL DEFAULT 1,
                children        INTEGER NOT NULL DEFAULT 0,
                active          INTEGER NOT NULL DEFAULT 1,
                created_at      TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS gf_snapshots (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                tracker_id       INTEGER NOT NULL REFERENCES gf_trackers(id) ON DELETE CASCADE,
                fetched_at       TEXT    NOT NULL,
                total_price      REAL,
                outbound_flight  TEXT,
                return_flight    TEXT,
                airline          TEXT,
                departure_time   TEXT,
                arrival_time     TEXT,
                duration_min     INTEGER,
                currency         TEXT    DEFAULT 'EUR',
                status           TEXT    NOT NULL DEFAULT 'ok',
                error_message    TEXT
            );

            CREATE TABLE IF NOT EXISTS homair_trackers (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id             INTEGER NOT NULL DEFAULT 1,
                region              TEXT    NOT NULL,
                accommodation_type  TEXT    NOT NULL DEFAULT 'mobilheim-standard',
                checkin_date        TEXT    NOT NULL,
                checkout_date       TEXT    NOT NULL,
                adults              INTEGER NOT NULL DEFAULT 2,
                children            INTEGER NOT NULL DEFAULT 0,
                active              INTEGER NOT NULL DEFAULT 1,
                created_at          TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS homair_snapshots (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                tracker_id     INTEGER NOT NULL REFERENCES homair_trackers(id) ON DELETE CASCADE,
                fetched_at     TEXT    NOT NULL,
                total_price    REAL,
                currency       TEXT    DEFAULT 'EUR',
                status         TEXT    NOT NULL DEFAULT 'ok',
                error_message  TEXT,
                note           TEXT
            );

            CREATE TABLE IF NOT EXISTS booking_trackers (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL DEFAULT 1,
                destination    TEXT    NOT NULL,
                checkin_date   TEXT    NOT NULL,
                checkout_date  TEXT    NOT NULL,
                adults         INTEGER NOT NULL DEFAULT 2,
                rooms          INTEGER NOT NULL DEFAULT 1,
                source         TEXT    NOT NULL DEFAULT 'booking',
                active         INTEGER NOT NULL DEFAULT 1,
                created_at     TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS booking_snapshots (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                tracker_id      INTEGER NOT NULL REFERENCES booking_trackers(id) ON DELETE CASCADE,
                fetched_at      TEXT    NOT NULL,
                total_price     REAL,
                hotel_name      TEXT,
                hotel_rating    REAL,
                currency        TEXT    DEFAULT 'EUR',
                status          TEXT    NOT NULL DEFAULT 'ok',
                error_message   TEXT
            );

            -- Global encrypted settings (admin only, no user_id)
            CREATE TABLE IF NOT EXISTS settings (
                key        TEXT PRIMARY KEY,
                value_enc  BLOB NOT NULL,
                updated_at TEXT NOT NULL
            );

            -- Per-user settings (dawarich, actualbudget, home coords)
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id    INTEGER NOT NULL,
                key        TEXT    NOT NULL,
                value_enc  BLOB    NOT NULL,
                updated_at TEXT    NOT NULL,
                PRIMARY KEY (user_id, key)
            );

            -- Dawarich detected trips (per user)
            CREATE TABLE IF NOT EXISTS detected_trips (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL DEFAULT 1,
                start_date     TEXT    NOT NULL,
                end_date       TEXT    NOT NULL,
                location_name  TEXT,
                country        TEXT,
                lat            REAL,
                lon            REAL,
                nights         INTEGER NOT NULL DEFAULT 1,
                source         TEXT    NOT NULL DEFAULT 'dawarich',
                created_at     TEXT    NOT NULL
            );

            -- Per-user data (trips list, budget, bucketlist)
            CREATE TABLE IF NOT EXISTS user_data (
                user_id    INTEGER NOT NULL DEFAULT 1,
                key        TEXT    NOT NULL,
                value      TEXT    NOT NULL,
                updated_at TEXT    DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, key)
            );
        """)

        # ── Safe migrations (idempotent ALTER TABLE) ──────────────────────────
        migrations = [
            ("trackers",         "user_id INTEGER NOT NULL DEFAULT 1"),
            ("gf_trackers",      "user_id INTEGER NOT NULL DEFAULT 1"),
            ("homair_trackers",  "user_id INTEGER NOT NULL DEFAULT 1"),
            ("booking_trackers", "user_id INTEGER NOT NULL DEFAULT 1"),
            ("detected_trips",   "user_id INTEGER NOT NULL DEFAULT 1"),
            ("trackers",         "threshold_price REAL DEFAULT NULL"),
            ("detected_trips",   "cost REAL DEFAULT NULL"),
            ("detected_trips",   "notes TEXT DEFAULT NULL"),
        ]
        for table, col_def in migrations:
            col_name = col_def.split()[0]
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
                conn.commit()
            except Exception:
                pass  # Column already exists


# ── Settings helpers ──────────────────────────────────────────────────────────

def save_setting(key: str, value: str, fernet) -> None:
    enc = fernet.encrypt(value.encode())
    with db() as conn:
        conn.execute(
            "INSERT INTO settings (key, value_enc, updated_at) VALUES (?,?,datetime('now'))"
            " ON CONFLICT(key) DO UPDATE SET value_enc=excluded.value_enc, updated_at=excluded.updated_at",
            (key, enc)
        )

def get_setting(key: str, fernet) -> str | None:
    with db() as conn:
        row = conn.execute("SELECT value_enc FROM settings WHERE key=?", (key,)).fetchone()
    if not row:
        return None
    try:
        return fernet.decrypt(row[0]).decode()
    except Exception:
        return None

def get_all_settings(fernet) -> dict:
    with db() as conn:
        rows = conn.execute("SELECT key, value_enc FROM settings").fetchall()
    result = {}
    for key, enc in rows:
        try:
            result[key] = fernet.decrypt(enc).decode()
        except Exception:
            result[key] = None
    return result


# ── Per-user settings ─────────────────────────────────────────────────────────

def save_user_setting(user_id: int, key: str, value: str, fernet) -> None:
    enc = fernet.encrypt(value.encode())
    with db() as conn:
        conn.execute(
            "INSERT INTO user_settings (user_id, key, value_enc, updated_at) VALUES (?,?,?,datetime('now'))"
            " ON CONFLICT(user_id, key) DO UPDATE SET value_enc=excluded.value_enc, updated_at=excluded.updated_at",
            (user_id, key, enc)
        )

def get_user_setting(user_id: int, key: str, fernet) -> str | None:
    with db() as conn:
        row = conn.execute(
            "SELECT value_enc FROM user_settings WHERE user_id=? AND key=?",
            (user_id, key)
        ).fetchone()
    if not row:
        return None
    try:
        return fernet.decrypt(row[0]).decode()
    except Exception:
        return None

def get_all_user_settings(user_id: int, fernet) -> dict:
    with db() as conn:
        rows = conn.execute(
            "SELECT key, value_enc FROM user_settings WHERE user_id=?", (user_id,)
        ).fetchall()
    result = {}
    for key, enc in rows:
        try:
            result[key] = fernet.decrypt(enc).decode()
        except Exception:
            result[key] = None
    return result


# ── Ryanair Trackers ──────────────────────────────────────────────────────────

def create_tracker(data: dict, user_id: int = 1) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO trackers
              (user_id, origin, destination, outbound_date, return_date,
               adults, children, baggage_json, seat_cost, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id,
            data["origin"], data["destination"],
            data["outbound_date"], data.get("return_date"),
            data.get("adults", 1), data.get("children", 0),
            json.dumps(data.get("baggage", [])),
            data.get("seat_cost", 0),
            datetime.utcnow().isoformat(),
        ))
        return cur.lastrowid

def list_trackers(active_only: bool = False, user_id: int | None = None) -> list[dict]:
    where_parts = []
    params = []
    if active_only:
        where_parts.append("active=1")
    if user_id:
        where_parts.append("user_id=?")
        params.append(user_id)
    where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
    with db() as conn:
        rows = conn.execute(
            f"SELECT * FROM trackers {where} ORDER BY created_at DESC", params
        ).fetchall()
    result = []
    for r in rows:
        t = dict(r)
        t["baggage"] = json.loads(t.get("baggage_json", "[]"))
        result.append(t)
    return result

def get_tracker(tid: int, user_id: int | None = None) -> dict | None:
    with db() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM trackers WHERE id=? AND user_id=?", (tid, user_id)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM trackers WHERE id=?", (tid,)).fetchone()
    if not row:
        return None
    t = dict(row)
    t["baggage"] = json.loads(t.get("baggage_json", "[]"))
    return t

def delete_tracker(tid: int, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "DELETE FROM trackers WHERE id=? AND user_id=?", (tid, user_id)
            ).rowcount > 0
        return conn.execute("DELETE FROM trackers WHERE id=?", (tid,)).rowcount > 0

def toggle_tracker(tid: int, active: bool, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "UPDATE trackers SET active=? WHERE id=? AND user_id=?",
                (1 if active else 0, tid, user_id)
            ).rowcount > 0
        return conn.execute(
            "UPDATE trackers SET active=? WHERE id=?", (1 if active else 0, tid)
        ).rowcount > 0

def get_latest_snapshot(tracker_id: int) -> dict | None:
    return _get_latest("price_snapshots", tracker_id)

def set_tracker_threshold(tracker_id: int, threshold: float | None, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "UPDATE trackers SET threshold_price=? WHERE id=? AND user_id=?",
                (threshold, tracker_id, user_id)
            ).rowcount > 0
        return conn.execute(
            "UPDATE trackers SET threshold_price=? WHERE id=?", (threshold, tracker_id)
        ).rowcount > 0

def get_tracker_threshold(tracker_id: int) -> float | None:
    with db() as conn:
        row = conn.execute(
            "SELECT threshold_price FROM trackers WHERE id=?", (tracker_id,)
        ).fetchone()
    return row[0] if row else None

def save_price_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO price_snapshots
              (tracker_id, fetched_at, flight_price, baggage_price, seat_price,
               total_price, outbound_flight, return_flight, currency,
               baggage_fallback, status, error_message, raw_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tracker_id,
            snap.get("fetched_at", datetime.utcnow().isoformat()),
            snap.get("flight_price"), snap.get("baggage_price"),
            snap.get("seat_price", 0), snap.get("total_price"),
            snap.get("outbound_flight"), snap.get("return_flight"),
            snap.get("currency", "EUR"),
            1 if snap.get("baggage_fallback") else 0,
            snap.get("status", "ok"), snap.get("error_message"),
            json.dumps(snap.get("raw")) if snap.get("raw") else None,
        ))
        return cur.lastrowid

def get_price_history(tracker_id: int, limit: int = 90) -> list[dict]:
    with db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM price_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT ?",
            (tracker_id, limit)
        ).fetchall()]


# ── Google Flights ────────────────────────────────────────────────────────────

def create_gf_tracker(data: dict, user_id: int = 1) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO gf_trackers
              (user_id, origin, destination, outbound_date, return_date,
               adults, children, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            user_id,
            data["origin"], data["destination"],
            data["outbound_date"], data.get("return_date"),
            data.get("adults", 1), data.get("children", 0),
            datetime.utcnow().isoformat(),
        ))
        return cur.lastrowid

def list_gf_trackers(user_id: int | None = None) -> list[dict]:
    where = "WHERE user_id=?" if user_id else ""
    params = [user_id] if user_id else []
    with db() as conn:
        trackers = [dict(r) for r in conn.execute(
            f"SELECT * FROM gf_trackers {where} ORDER BY created_at DESC", params
        ).fetchall()]
    for t in trackers:
        t["latest_snapshot"] = _get_latest("gf_snapshots", t["id"])
    return trackers

def get_gf_tracker(tid: int, user_id: int | None = None) -> dict | None:
    with db() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM gf_trackers WHERE id=? AND user_id=?", (tid, user_id)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM gf_trackers WHERE id=?", (tid,)).fetchone()
    return dict(row) if row else None

def delete_gf_tracker(tid: int, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "DELETE FROM gf_trackers WHERE id=? AND user_id=?", (tid, user_id)
            ).rowcount > 0
        return conn.execute("DELETE FROM gf_trackers WHERE id=?", (tid,)).rowcount > 0

def save_gf_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO gf_snapshots
              (tracker_id, fetched_at, total_price, outbound_flight, return_flight,
               airline, departure_time, arrival_time, duration_min, currency, status, error_message)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tracker_id, snap.get("fetched_at", datetime.utcnow().isoformat()),
            snap.get("total_price"), snap.get("outbound_flight"), snap.get("return_flight"),
            snap.get("airline"), snap.get("departure_time"), snap.get("arrival_time"),
            snap.get("duration_min"), snap.get("currency", "EUR"),
            snap.get("status", "ok"), snap.get("error_message"),
        ))
        return cur.lastrowid

def get_gf_history(tracker_id: int, limit: int = 30) -> list[dict]:
    with db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM gf_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT ?",
            (tracker_id, limit)
        ).fetchall()]


# ── Homair ────────────────────────────────────────────────────────────────────

def create_homair_tracker(data: dict, user_id: int = 1) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO homair_trackers
              (user_id, region, accommodation_type, checkin_date, checkout_date,
               adults, children, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            user_id,
            data["region"], data.get("accommodation_type", "mobilheim-standard"),
            data["checkin_date"], data["checkout_date"],
            data.get("adults", 2), data.get("children", 0),
            datetime.utcnow().isoformat(),
        ))
        return cur.lastrowid

def list_homair_trackers(user_id: int | None = None) -> list[dict]:
    where = "WHERE user_id=?" if user_id else ""
    params = [user_id] if user_id else []
    with db() as conn:
        trackers = [dict(r) for r in conn.execute(
            f"SELECT * FROM homair_trackers {where} ORDER BY created_at DESC", params
        ).fetchall()]
    for t in trackers:
        t["latest_snapshot"] = _get_latest("homair_snapshots", t["id"])
    return trackers

def get_homair_tracker(tid: int, user_id: int | None = None) -> dict | None:
    with db() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM homair_trackers WHERE id=? AND user_id=?", (tid, user_id)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM homair_trackers WHERE id=?", (tid,)).fetchone()
    return dict(row) if row else None

def delete_homair_tracker(tid: int, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "DELETE FROM homair_trackers WHERE id=? AND user_id=?", (tid, user_id)
            ).rowcount > 0
        return conn.execute("DELETE FROM homair_trackers WHERE id=?", (tid,)).rowcount > 0

def save_homair_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO homair_snapshots
              (tracker_id, fetched_at, total_price, currency, status, error_message, note)
            VALUES (?,?,?,?,?,?,?)
        """, (
            tracker_id, snap.get("fetched_at", datetime.utcnow().isoformat()),
            snap.get("total_price"), snap.get("currency", "EUR"),
            snap.get("status", "ok"), snap.get("error_message"), snap.get("note"),
        ))
        return cur.lastrowid


# ── Booking ───────────────────────────────────────────────────────────────────

def create_booking_tracker(data: dict, user_id: int = 1) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO booking_trackers
              (user_id, destination, checkin_date, checkout_date, adults, rooms, source, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            user_id,
            data["destination"], data["checkin_date"], data["checkout_date"],
            data.get("adults", 2), data.get("rooms", 1),
            data.get("source", "booking"),
            datetime.utcnow().isoformat(),
        ))
        return cur.lastrowid

def list_booking_trackers(user_id: int | None = None) -> list[dict]:
    where = "WHERE user_id=?" if user_id else ""
    params = [user_id] if user_id else []
    with db() as conn:
        trackers = [dict(r) for r in conn.execute(
            f"SELECT * FROM booking_trackers {where} ORDER BY created_at DESC", params
        ).fetchall()]
    for t in trackers:
        t["latest_snapshot"] = _get_latest("booking_snapshots", t["id"])
    return trackers

def get_booking_tracker(tid: int, user_id: int | None = None) -> dict | None:
    with db() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM booking_trackers WHERE id=? AND user_id=?", (tid, user_id)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM booking_trackers WHERE id=?", (tid,)).fetchone()
    return dict(row) if row else None

def delete_booking_tracker(tid: int, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "DELETE FROM booking_trackers WHERE id=? AND user_id=?", (tid, user_id)
            ).rowcount > 0
        return conn.execute("DELETE FROM booking_trackers WHERE id=?", (tid,)).rowcount > 0

def save_booking_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO booking_snapshots
              (tracker_id, fetched_at, total_price, hotel_name, hotel_rating,
               currency, status, error_message)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            tracker_id, snap.get("fetched_at", datetime.utcnow().isoformat()),
            snap.get("total_price"), snap.get("hotel_name"), snap.get("hotel_rating"),
            snap.get("currency", "EUR"), snap.get("status", "ok"), snap.get("error_message"),
        ))
        return cur.lastrowid


# ── Detected Trips (Dawarich) ─────────────────────────────────────────────────

def save_detected_trip(trip: dict, user_id: int = 1) -> int:
    with db() as conn:
        existing = conn.execute(
            "SELECT id FROM detected_trips WHERE user_id=? AND start_date=? AND end_date=? AND source=?",
            (user_id, trip["start_date"], trip["end_date"], trip.get("source", "dawarich"))
        ).fetchone()
        if existing:
            conn.execute("""
                UPDATE detected_trips SET
                  location_name=?, country=?, lat=?, lon=?, nights=?, cost=?, notes=?
                WHERE id=?
            """, (
                trip.get("location_name"), trip.get("country"),
                trip.get("lat"), trip.get("lon"),
                trip.get("nights", 1),
                trip.get("cost"), trip.get("notes"),
                existing["id"]
            ))
            return existing["id"]
        cur = conn.execute("""
            INSERT INTO detected_trips
              (user_id, start_date, end_date, location_name, country,
               lat, lon, nights, source, cost, notes, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id,
            trip["start_date"], trip["end_date"],
            trip.get("location_name"), trip.get("country"),
            trip.get("lat"), trip.get("lon"),
            trip.get("nights", 1),
            trip.get("source", "dawarich"),
            trip.get("cost"), trip.get("notes"),
            datetime.utcnow().isoformat(),
        ))
        return cur.lastrowid

def list_detected_trips(limit: int = 50, user_id: int | None = None) -> list[dict]:
    where = "WHERE user_id=?" if user_id else ""
    params = [user_id] if user_id else []
    with db() as conn:
        return [dict(r) for r in conn.execute(
            f"SELECT * FROM detected_trips {where} ORDER BY start_date DESC LIMIT ?",
            params + [limit]
        ).fetchall()]

def update_detected_trip_cost(trip_id: int, cost: float | None, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "UPDATE detected_trips SET cost=? WHERE id=? AND user_id=?",
                (cost, trip_id, user_id)
            ).rowcount > 0
        return conn.execute(
            "UPDATE detected_trips SET cost=? WHERE id=?", (cost, trip_id)
        ).rowcount > 0


def delete_detected_trip(trip_id: int, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "DELETE FROM detected_trips WHERE id=? AND user_id=?", (trip_id, user_id)
            ).rowcount > 0
        return conn.execute(
            "DELETE FROM detected_trips WHERE id=?", (trip_id,)
        ).rowcount > 0


# ── User Data (trips list, budget, bucketlist) ────────────────────────────────

def save_user_data(key: str, value: str, user_id: int = 1) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO user_data (user_id, key, value, updated_at) VALUES (?,?,?,datetime('now'))"
            " ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (user_id, key, value),
        )

def get_user_data(key: str, user_id: int = 1) -> str | None:
    with db() as conn:
        row = conn.execute(
            "SELECT value FROM user_data WHERE user_id=? AND key=?", (user_id, key)
        ).fetchone()
    return row[0] if row else None

def list_user_data_keys(user_id: int = 1) -> list[str]:
    with db() as conn:
        rows = conn.execute(
            "SELECT key FROM user_data WHERE user_id=? ORDER BY key", (user_id,)
        ).fetchall()
    return [r[0] for r in rows]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_latest(table: str, tracker_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute(
            f"SELECT * FROM {table} WHERE tracker_id=? AND status='ok' ORDER BY fetched_at DESC LIMIT 1",
            (tracker_id,)
        ).fetchone()
    return dict(row) if row else None
