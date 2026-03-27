"""
WanderSuite v1.0 — Datenbank-Layer
SQLite — alle Tracker-Typen persistent, verschlüsselte Settings.
"""

import sqlite3
import json
import os
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "tracker.db")


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


def init_db():
    """Alle Tabellen anlegen + Migrationen."""
    with db() as conn:
        conn.executescript("""
            -- Ryanair Tracker
            CREATE TABLE IF NOT EXISTS trackers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                origin          TEXT    NOT NULL,
                destination     TEXT    NOT NULL,
                outbound_date   TEXT    NOT NULL,
                return_date     TEXT,
                adults          INTEGER NOT NULL DEFAULT 1,
                children        INTEGER NOT NULL DEFAULT 0,
                baggage_json    TEXT    NOT NULL DEFAULT '[]',
                seat_cost       REAL    NOT NULL DEFAULT 0,
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

            -- Google Flights Tracker
            CREATE TABLE IF NOT EXISTS gf_trackers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
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

            -- Homair Tracker
            CREATE TABLE IF NOT EXISTS homair_trackers (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
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

            -- Booking Tracker
            CREATE TABLE IF NOT EXISTS booking_trackers (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
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

            -- Encrypted Settings
            CREATE TABLE IF NOT EXISTS settings (
                key        TEXT PRIMARY KEY,
                value_enc  BLOB NOT NULL,
                updated_at TEXT NOT NULL
            );

            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_price_snaps   ON price_snapshots(tracker_id, fetched_at DESC);
            CREATE INDEX IF NOT EXISTS idx_gf_snaps      ON gf_snapshots(tracker_id, fetched_at DESC);
            CREATE INDEX IF NOT EXISTS idx_homair_snaps  ON homair_snapshots(tracker_id, fetched_at DESC);
            CREATE INDEX IF NOT EXISTS idx_booking_snaps ON booking_snapshots(tracker_id, fetched_at DESC);
        """)

        # Migrations for existing Ryanair tables
        for col, definition in [
            ("seat_cost", "REAL NOT NULL DEFAULT 0"),
            ("seat_price", "REAL DEFAULT 0"),
        ]:
            try:
                if col == "seat_cost":
                    conn.execute(f"ALTER TABLE trackers ADD COLUMN {col} {definition}")
                else:
                    conn.execute(f"ALTER TABLE price_snapshots ADD COLUMN {col} {definition}")
            except Exception:
                pass


# ─── Settings (encrypted) ────────────────────────────

def save_setting(key: str, value: str, fernet) -> None:
    encrypted = fernet.encrypt(value.encode())
    with db() as conn:
        conn.execute("""
            INSERT INTO settings (key, value_enc, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value_enc=excluded.value_enc, updated_at=excluded.updated_at
        """, (key, encrypted, datetime.utcnow().isoformat()))


def get_setting(key: str, fernet) -> str | None:
    with db() as conn:
        row = conn.execute("SELECT value_enc FROM settings WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        try:
            return fernet.decrypt(row["value_enc"]).decode()
        except Exception:
            return None


def get_all_settings(fernet) -> dict:
    with db() as conn:
        rows = conn.execute("SELECT key, value_enc FROM settings").fetchall()
    result = {}
    for row in rows:
        try:
            result[row["key"]] = fernet.decrypt(row["value_enc"]).decode()
        except Exception:
            result[row["key"]] = ""
    return result


# ─── Ryanair Tracker ─────────────────────────────────

def create_tracker(data: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO trackers
              (origin, destination, outbound_date, return_date,
               adults, children, baggage_json, seat_cost, active, created_at)
            VALUES (?,?,?,?,?,?,?,?,1,?)
        """, (
            data["origin"].upper(), data["destination"].upper(),
            data["outbound_date"], data.get("return_date"),
            data.get("adults", 1), data.get("children", 0),
            json.dumps(data.get("baggage", [])),
            data.get("seat_cost", 0.0),
            datetime.utcnow().isoformat(),
        ))
        return cur.lastrowid


def list_trackers(active_only=True) -> list[dict]:
    with db() as conn:
        sql = "SELECT * FROM trackers" + (" WHERE active=1" if active_only else "") + " ORDER BY created_at DESC"
        rows = conn.execute(sql).fetchall()
        result = []
        for row in rows:
            t = dict(row)
            t["baggage"] = json.loads(t.pop("baggage_json", "[]"))
            result.append(t)
        return result


def get_tracker(tracker_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM trackers WHERE id=?", (tracker_id,)).fetchone()
        if not row:
            return None
        t = dict(row)
        t["baggage"] = json.loads(t.pop("baggage_json", "[]"))
        return t


def delete_tracker(tracker_id: int) -> bool:
    with db() as conn:
        return conn.execute("DELETE FROM trackers WHERE id=?", (tracker_id,)).rowcount > 0


def toggle_tracker(tracker_id: int, active: bool) -> bool:
    with db() as conn:
        return conn.execute("UPDATE trackers SET active=? WHERE id=?", (1 if active else 0, tracker_id)).rowcount > 0


def save_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO price_snapshots
              (tracker_id, fetched_at, flight_price, baggage_price, seat_price,
               total_price, outbound_flight, return_flight, currency,
               baggage_fallback, status, error_message, raw_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tracker_id, snap.get("fetched_at", datetime.utcnow().isoformat()),
            snap.get("flight_price"), snap.get("baggage_price"), snap.get("seat_price", 0),
            snap.get("total_price"), snap.get("outbound_flight"), snap.get("return_flight"),
            snap.get("currency", "EUR"), 1 if snap.get("baggage_fallback") else 0,
            snap.get("status", "ok"), snap.get("error_message"),
            json.dumps(snap.get("raw")) if snap.get("raw") else None,
        ))
        return cur.lastrowid


def get_snapshots(tracker_id: int, limit=90) -> list[dict]:
    with db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM price_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT ?",
            (tracker_id, limit)
        ).fetchall()]


def get_latest_snapshot(tracker_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM price_snapshots WHERE tracker_id=? AND status='ok' ORDER BY fetched_at DESC LIMIT 1",
            (tracker_id,)
        ).fetchone()
        return dict(row) if row else None


# ─── Google Flights Tracker ──────────────────────────

def create_gf_tracker(data: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO gf_trackers (origin, destination, outbound_date, return_date, adults, children, created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (
            data["origin"].upper(), data["destination"].upper(),
            data["outbound_date"], data.get("return_date"),
            data.get("adults", 1), data.get("children", 0),
            datetime.utcnow().isoformat(),
        ))
        return cur.lastrowid


def list_gf_trackers() -> list[dict]:
    with db() as conn:
        trackers = [dict(r) for r in conn.execute("SELECT * FROM gf_trackers ORDER BY created_at DESC").fetchall()]
        for t in trackers:
            t["latest_snapshot"] = get_gf_latest_snapshot(t["id"])
        return trackers


def get_gf_tracker(tid: int) -> dict | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM gf_trackers WHERE id=?", (tid,)).fetchone()
        return dict(row) if row else None


def delete_gf_tracker(tid: int) -> bool:
    with db() as conn:
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


def get_gf_snapshots(tracker_id: int, limit=90) -> list[dict]:
    with db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM gf_snapshots WHERE tracker_id=? ORDER BY fetched_at DESC LIMIT ?",
            (tracker_id, limit)
        ).fetchall()]


def get_gf_latest_snapshot(tracker_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM gf_snapshots WHERE tracker_id=? AND status='ok' ORDER BY fetched_at DESC LIMIT 1",
            (tracker_id,)
        ).fetchone()
        return dict(row) if row else None


# ─── Homair Tracker ──────────────────────────────────

def create_homair_tracker(data: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO homair_trackers
              (region, accommodation_type, checkin_date, checkout_date, adults, children, created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (
            data["region"], data.get("accommodation_type", "mobilheim-standard"),
            data["checkin_date"], data["checkout_date"],
            data.get("adults", 2), data.get("children", 0),
            datetime.utcnow().isoformat(),
        ))
        return cur.lastrowid


def list_homair_trackers() -> list[dict]:
    with db() as conn:
        trackers = [dict(r) for r in conn.execute("SELECT * FROM homair_trackers ORDER BY created_at DESC").fetchall()]
        for t in trackers:
            t["latest_snapshot"] = _get_latest("homair_snapshots", t["id"])
        return trackers


def get_homair_tracker(tid: int) -> dict | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM homair_trackers WHERE id=?", (tid,)).fetchone()
        return dict(row) if row else None


def delete_homair_tracker(tid: int) -> bool:
    with db() as conn:
        return conn.execute("DELETE FROM homair_trackers WHERE id=?", (tid,)).rowcount > 0


def save_homair_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO homair_snapshots (tracker_id, fetched_at, total_price, currency, status, error_message, note)
            VALUES (?,?,?,?,?,?,?)
        """, (
            tracker_id, snap.get("fetched_at", datetime.utcnow().isoformat()),
            snap.get("total_price"), snap.get("currency", "EUR"),
            snap.get("status", "ok"), snap.get("error_message"), snap.get("note"),
        ))
        return cur.lastrowid


# ─── Booking Tracker ─────────────────────────────────

def create_booking_tracker(data: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO booking_trackers
              (destination, checkin_date, checkout_date, adults, rooms, source, created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (
            data["destination"], data["checkin_date"], data["checkout_date"],
            data.get("adults", 2), data.get("rooms", 1),
            data.get("source", "booking"),
            datetime.utcnow().isoformat(),
        ))
        return cur.lastrowid


def list_booking_trackers() -> list[dict]:
    with db() as conn:
        trackers = [dict(r) for r in conn.execute("SELECT * FROM booking_trackers ORDER BY created_at DESC").fetchall()]
        for t in trackers:
            t["latest_snapshot"] = _get_latest("booking_snapshots", t["id"])
        return trackers


def get_booking_tracker(tid: int) -> dict | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM booking_trackers WHERE id=?", (tid,)).fetchone()
        return dict(row) if row else None


def delete_booking_tracker(tid: int) -> bool:
    with db() as conn:
        return conn.execute("DELETE FROM booking_trackers WHERE id=?", (tid,)).rowcount > 0


def save_booking_snapshot(tracker_id: int, snap: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO booking_snapshots
              (tracker_id, fetched_at, total_price, hotel_name, hotel_rating, currency, status, error_message)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            tracker_id, snap.get("fetched_at", datetime.utcnow().isoformat()),
            snap.get("total_price"), snap.get("hotel_name"), snap.get("hotel_rating"),
            snap.get("currency", "EUR"), snap.get("status", "ok"), snap.get("error_message"),
        ))
        return cur.lastrowid


# ─── Helpers ─────────────────────────────────────────

def _get_latest(table: str, tracker_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute(
            f"SELECT * FROM {table} WHERE tracker_id=? AND status='ok' ORDER BY fetched_at DESC LIMIT 1",
            (tracker_id,)
        ).fetchone()
        return dict(row) if row else None
