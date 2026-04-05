"""
WanderSuite — Database Layer (Multi-User)
SQLite via sqlite3. All content tables have user_id.

Global tables (no user_id): settings, webauthn_credentials, webauthn_challenges
Per-user tables:            trackers, gf_trackers, homair_trackers, booking_trackers,
                            detected_trips, user_data, price_history

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
                wish_price      REAL             DEFAULT NULL,
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
                wish_price      REAL             DEFAULT NULL,
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
                wish_price          REAL             DEFAULT NULL,
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
                wish_price     REAL             DEFAULT NULL,
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

            -- Unified price history: one row per price observation, per tracker type
            -- tracker_type: 'flight' | 'google_flight' | 'hotel' | 'camping' | 'car'
            CREATE TABLE IF NOT EXISTS price_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL DEFAULT 1,
                tracker_type TEXT    NOT NULL,
                tracker_id   INTEGER NOT NULL,
                price        REAL    NOT NULL,
                currency     TEXT    NOT NULL DEFAULT 'EUR',
                provider     TEXT,
                status       TEXT    NOT NULL DEFAULT 'ok',
                error_msg    TEXT,
                fetched_at   TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            -- Per-user scheduler settings (update intervals)
            CREATE TABLE IF NOT EXISTS user_scheduler_settings (
                user_id               INTEGER PRIMARY KEY,
                update_interval_hours INTEGER NOT NULL DEFAULT 24,
                notify_price_drop     INTEGER NOT NULL DEFAULT 1,
                notify_daily_summary  INTEGER NOT NULL DEFAULT 0,
                last_run_at           TEXT,
                updated_at            TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            -- Per-user notification credentials (Fernet-encrypted)
            CREATE TABLE IF NOT EXISTS user_notification_settings (
                user_id             INTEGER PRIMARY KEY,
                telegram_bot_token  TEXT DEFAULT NULL,
                telegram_chat_id    TEXT DEFAULT NULL,
                gotify_url          TEXT DEFAULT NULL,
                gotify_app_token    TEXT DEFAULT NULL,
                updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
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
            ("trackers",         "wish_price REAL DEFAULT NULL"),
            ("gf_trackers",      "wish_price REAL DEFAULT NULL"),
            ("homair_trackers",  "wish_price REAL DEFAULT NULL"),
            ("booking_trackers", "wish_price REAL DEFAULT NULL"),
            ("detected_trips",   "cost REAL DEFAULT NULL"),
            ("detected_trips",   "notes TEXT DEFAULT NULL"),
            ("detected_trips",   "ignored INTEGER NOT NULL DEFAULT 0"),
            ("detected_trips",   "auto_cost REAL DEFAULT NULL"),
            ("detected_trips",   "auto_cost_txs TEXT DEFAULT NULL"),
            ("homair_trackers",  "campsite_name TEXT DEFAULT NULL"),
            ("booking_trackers", "hotel_name TEXT DEFAULT NULL"),
            ("gf_trackers",      "seat_cost REAL NOT NULL DEFAULT 0"),
            ("gf_trackers",      "baggage_json TEXT NOT NULL DEFAULT '[]'"),
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
            "SELECT value_enc FROM user_settings WHERE user_id=? AND key=?", (user_id, key)
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


# ── Tracker CRUD ──────────────────────────────────────────────────────────────

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
    with db() as conn:
        where_parts = []
        params = []
        if user_id:
            where_parts.append("user_id=?")
            params.append(user_id)
        if active_only:
            where_parts.append("active=1")
        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        rows = conn.execute(f"SELECT * FROM trackers {where} ORDER BY created_at DESC", params).fetchall()
    return [dict(r) for r in rows]


def get_tracker(tracker_id: int, user_id: int | None = None) -> dict | None:
    with db() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM trackers WHERE id=? AND user_id=?", (tracker_id, user_id)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM trackers WHERE id=?", (tracker_id,)).fetchone()
    return dict(row) if row else None


def delete_tracker(tracker_id: int, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "DELETE FROM trackers WHERE id=? AND user_id=?", (tracker_id, user_id)
            ).rowcount > 0
        return conn.execute("DELETE FROM trackers WHERE id=?", (tracker_id,)).rowcount > 0


def toggle_tracker(tracker_id: int, active: bool, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "UPDATE trackers SET active=? WHERE id=? AND user_id=?",
                (1 if active else 0, tracker_id, user_id)
            ).rowcount > 0
        return conn.execute(
            "UPDATE trackers SET active=? WHERE id=?",
            (1 if active else 0, tracker_id)
        ).rowcount > 0


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
                baggage_fallback, status, error_message, raw_json)
               VALUES (?,datetime('now'),?,?,?,?,?,?,?,?,?,?,?)""",
            (tracker_id,
             snap.get("flight_price"), snap.get("baggage_price"),
             snap.get("seat_price", 0), snap.get("total_price"),
             snap.get("outbound_flight"), snap.get("return_flight"),
             snap.get("currency", "EUR"), snap.get("baggage_fallback", 0),
             snap.get("status", "ok"), snap.get("error_message"),
             json.dumps(snap.get("raw")) if snap.get("raw") else None)
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
    with db() as conn:
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


# ── Google Flights Tracker CRUD ───────────────────────────────────────────────

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
    with db() as conn:
        where_parts = []
        params = []
        if user_id:
            where_parts.append("user_id=?")
            params.append(user_id)
        if active_only:
            where_parts.append("active=1")
        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        rows = conn.execute(f"SELECT * FROM gf_trackers {where} ORDER BY created_at DESC", params).fetchall()
    return [dict(r) for r in rows]


def get_gf_tracker(tracker_id: int, user_id: int | None = None) -> dict | None:
    with db() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM gf_trackers WHERE id=? AND user_id=?", (tracker_id, user_id)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM gf_trackers WHERE id=?", (tracker_id,)).fetchone()
    return dict(row) if row else None


def delete_gf_tracker(tracker_id: int, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "DELETE FROM gf_trackers WHERE id=? AND user_id=?", (tracker_id, user_id)
            ).rowcount > 0
        return conn.execute("DELETE FROM gf_trackers WHERE id=?", (tracker_id,)).rowcount > 0


def toggle_gf_tracker(tracker_id: int, active: bool, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "UPDATE gf_trackers SET active=? WHERE id=? AND user_id=?",
                (1 if active else 0, tracker_id, user_id)
            ).rowcount > 0
        return conn.execute(
            "UPDATE gf_trackers SET active=? WHERE id=?",
            (1 if active else 0, tracker_id)
        ).rowcount > 0


def save_gf_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO gf_snapshots
               (tracker_id, fetched_at, total_price, outbound_flight, return_flight,
                airline, departure_time, arrival_time, duration_min, currency, status, error_message)
               VALUES (?,datetime('now'),?,?,?,?,?,?,?,?,?,?)""",
            (tracker_id, snap.get("total_price"), snap.get("outbound_flight"),
             snap.get("return_flight"), snap.get("airline"),
             snap.get("departure_time"), snap.get("arrival_time"),
             snap.get("duration_min"), snap.get("currency", "EUR"),
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
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM gf_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT 1",
            (tracker_id,)
        ).fetchone()
    return dict(row) if row else None

def get_gf_history(tracker_id: int, limit: int = 90) -> list[dict]:
    """Compatibility alias: return GF snapshots from gf_snapshots table."""
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM gf_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT ?",
            (tracker_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]



# ── Homair Tracker CRUD ───────────────────────────────────────────────────────

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
    with db() as conn:
        where_parts = []
        params = []
        if user_id:
            where_parts.append("user_id=?")
            params.append(user_id)
        if active_only:
            where_parts.append("active=1")
        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        rows = conn.execute(f"SELECT * FROM homair_trackers {where} ORDER BY created_at DESC", params).fetchall()
    return [dict(r) for r in rows]


def get_homair_tracker(tracker_id: int, user_id: int | None = None) -> dict | None:
    with db() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM homair_trackers WHERE id=? AND user_id=?", (tracker_id, user_id)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM homair_trackers WHERE id=?", (tracker_id,)).fetchone()
    return dict(row) if row else None


def delete_homair_tracker(tracker_id: int, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "DELETE FROM homair_trackers WHERE id=? AND user_id=?", (tracker_id, user_id)
            ).rowcount > 0
        return conn.execute("DELETE FROM homair_trackers WHERE id=?", (tracker_id,)).rowcount > 0


def toggle_homair_tracker(tracker_id: int, active: bool, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "UPDATE homair_trackers SET active=? WHERE id=? AND user_id=?",
                (1 if active else 0, tracker_id, user_id)
            ).rowcount > 0
        return conn.execute(
            "UPDATE homair_trackers SET active=? WHERE id=?",
            (1 if active else 0, tracker_id)
        ).rowcount > 0


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
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM homair_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT 1",
            (tracker_id,)
        ).fetchone()
    return dict(row) if row else None


# ── Booking / Hotel Tracker CRUD ──────────────────────────────────────────────

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
    with db() as conn:
        where_parts = []
        params = []
        if user_id:
            where_parts.append("user_id=?")
            params.append(user_id)
        if active_only:
            where_parts.append("active=1")
        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        rows = conn.execute(f"SELECT * FROM booking_trackers {where} ORDER BY created_at DESC", params).fetchall()
    return [dict(r) for r in rows]


def get_booking_tracker(tracker_id: int, user_id: int | None = None) -> dict | None:
    with db() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM booking_trackers WHERE id=? AND user_id=?", (tracker_id, user_id)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM booking_trackers WHERE id=?", (tracker_id,)).fetchone()
    return dict(row) if row else None


def delete_booking_tracker(tracker_id: int, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "DELETE FROM booking_trackers WHERE id=? AND user_id=?", (tracker_id, user_id)
            ).rowcount > 0
        return conn.execute("DELETE FROM booking_trackers WHERE id=?", (tracker_id,)).rowcount > 0


def toggle_booking_tracker(tracker_id: int, active: bool, user_id: int | None = None) -> bool:
    with db() as conn:
        if user_id:
            return conn.execute(
                "UPDATE booking_trackers SET active=? WHERE id=? AND user_id=?",
                (1 if active else 0, tracker_id, user_id)
            ).rowcount > 0
        return conn.execute(
            "UPDATE booking_trackers SET active=? WHERE id=?",
            (1 if active else 0, tracker_id)
        ).rowcount > 0


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
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM booking_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT 1",
            (tracker_id,)
        ).fetchone()
    return dict(row) if row else None


# ── User Scheduler Settings ───────────────────────────────────────────────────

def get_user_scheduler_settings(user_id: int) -> dict:
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM user_scheduler_settings WHERE user_id=?", (user_id,)
        ).fetchone()
    if row:
        return dict(row)
    return {
        "user_id": user_id,
        "update_interval_hours": 24,
        "notify_price_drop": True,
        "notify_daily_summary": False,
        "last_run_at": None,
    }


def save_user_scheduler_settings(user_id: int, interval_hours: int,
                                   notify_price_drop: bool,
                                   notify_daily_summary: bool) -> None:
    with db() as conn:
        conn.execute(
            """INSERT INTO user_scheduler_settings
               (user_id, update_interval_hours, notify_price_drop, notify_daily_summary, updated_at)
               VALUES (?,?,?,?,datetime('now'))
               ON CONFLICT(user_id) DO UPDATE SET
                 update_interval_hours=excluded.update_interval_hours,
                 notify_price_drop=excluded.notify_price_drop,
                 notify_daily_summary=excluded.notify_daily_summary,
                 updated_at=excluded.updated_at""",
            (user_id, interval_hours,
             1 if notify_price_drop else 0,
             1 if notify_daily_summary else 0)
        )


def update_scheduler_last_run(user_id: int) -> None:
    with db() as conn:
        conn.execute(
            """INSERT INTO user_scheduler_settings (user_id, update_interval_hours, notify_price_drop,
               notify_daily_summary, last_run_at, updated_at)
               VALUES (?,24,1,0,datetime('now'),datetime('now'))
               ON CONFLICT(user_id) DO UPDATE SET last_run_at=datetime('now')""",
            (user_id,)
        )


# ── detected_trips helpers ────────────────────────────────────────────────────

def list_detected_trips(user_id: int | None = None,
                         include_ignored: bool = False,
                         limit: int = 500) -> list[dict]:
    with db() as conn:
        where_parts = []
        params = []
        if user_id:
            where_parts.append("user_id=?")
            params.append(user_id)
        if not include_ignored:
            where_parts.append("(ignored IS NULL OR ignored=0)")
        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        rows = conn.execute(
            f"SELECT * FROM detected_trips {where} ORDER BY start_date DESC LIMIT ?",
            params + [limit]
        ).fetchall()
    return [dict(r) for r in rows]


def create_detected_trip(data: dict, user_id: int = 1) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO detected_trips
               (user_id, start_date, end_date, location_name, country,
                lat, lon, nights, source, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))""",
            (user_id, data["start_date"], data["end_date"],
             data.get("location_name"), data.get("country"),
             data.get("lat"), data.get("lon"),
             data.get("nights", 1), data.get("source", "manual"))
        )
    return cur.lastrowid


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


def delete_detected_trip(trip_id: int, user_id: int | None = None,
                             hard: bool = False) -> bool:
    """Soft-delete: setzt ignored=1. hard=True löscht wirklich (für manuelle Einträge)."""
    with db() as conn:
        # Manuelle Einträge wirklich löschen, Dawarich-Trips nur ignorieren
        row = conn.execute("SELECT source FROM detected_trips WHERE id=?", (trip_id,)).fetchone()
        is_manual = row and row[0] == "manual"
        if hard or is_manual:
            if user_id:
                return conn.execute(
                    "DELETE FROM detected_trips WHERE id=? AND user_id=?", (trip_id, user_id)
                ).rowcount > 0
            return conn.execute("DELETE FROM detected_trips WHERE id=?", (trip_id,)).rowcount > 0
        else:
            # Soft-delete: ignored=1
            if user_id:
                return conn.execute(
                    "UPDATE detected_trips SET ignored=1 WHERE id=? AND user_id=?", (trip_id, user_id)
                ).rowcount > 0
            return conn.execute(
                "UPDATE detected_trips SET ignored=1 WHERE id=?", (trip_id,)
            ).rowcount > 0


def unignore_detected_trips(user_id: int | None = None) -> int:
    """Full Sync: alle ignorierten Trips wieder aktivieren."""
    with db() as conn:
        if user_id:
            return conn.execute(
                "UPDATE detected_trips SET ignored=0 WHERE user_id=? AND source='dawarich'",
                (user_id,)
            ).rowcount
        return conn.execute(
            "UPDATE detected_trips SET ignored=0 WHERE source='dawarich'"
        ).rowcount


def update_trip_auto_cost(trip_id: int, auto_cost: float | None,
                          txs_json: str | None = None,
                          user_id: int | None = None) -> bool:
    """Automatisch zugeordnete Kosten aus ActualBudget speichern."""
    with db() as conn:
        if user_id:
            return conn.execute(
                "UPDATE detected_trips SET auto_cost=?, auto_cost_txs=? WHERE id=? AND user_id=?",
                (auto_cost, txs_json, trip_id, user_id)
            ).rowcount > 0
        return conn.execute(
            "UPDATE detected_trips SET auto_cost=?, auto_cost_txs=? WHERE id=?",
            (auto_cost, txs_json, trip_id)
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


def save_detected_trip(data: dict, user_id: int = 1) -> int:
    """Alias for create_detected_trip — backward compatibility."""
    return create_detected_trip(data, user_id=user_id)

# ── User Notification Settings CRUD ──────────────────────────────────────────

def get_user_notification_settings(user_id: int, fernet) -> dict:
    """Return decrypted notification settings for a user. Missing fields -> empty string."""
    with db() as conn:
        row = conn.execute(
            "SELECT telegram_bot_token, telegram_chat_id, gotify_url, gotify_app_token "
            "FROM user_notification_settings WHERE user_id=?",
            (user_id,)
        ).fetchone()
    if not row:
        return {"telegram_bot_token": "", "telegram_chat_id": "", "gotify_url": "", "gotify_app_token": ""}
    def _dec(v):
        if not v:
            return ""
        try:
            return fernet.decrypt(v.encode()).decode()
        except Exception:
            return ""
    return {
        "telegram_bot_token": _dec(row["telegram_bot_token"]),
        "telegram_chat_id":   _dec(row["telegram_chat_id"]),
        "gotify_url":         _dec(row["gotify_url"]),
        "gotify_app_token":   _dec(row["gotify_app_token"]),
    }


def save_user_notification_settings(user_id: int, settings: dict, fernet) -> None:
    """Encrypt and upsert notification credentials for a user. Empty string -> NULL."""
    def _enc(v):
        if not v:
            return None
        return fernet.encrypt(v.encode()).decode()
    with db() as conn:
        conn.execute("""
            INSERT INTO user_notification_settings
                (user_id, telegram_bot_token, telegram_chat_id, gotify_url, gotify_app_token, updated_at)
            VALUES (?,?,?,?,?,datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                telegram_bot_token = excluded.telegram_bot_token,
                telegram_chat_id   = excluded.telegram_chat_id,
                gotify_url         = excluded.gotify_url,
                gotify_app_token   = excluded.gotify_app_token,
                updated_at         = excluded.updated_at
        """, (
            user_id,
            _enc(settings.get("telegram_bot_token", "")),
            _enc(settings.get("telegram_chat_id",   "")),
            _enc(settings.get("gotify_url",          "")),
            _enc(settings.get("gotify_app_token",    "")),
        ))



