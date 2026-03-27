"""
WanderSuite v0.1 — Datenbank-Layer
SQLite via sqlite3 (kein ORM, maximale Portabilität).
Schema: trackers + price_snapshots (inkl. Sitzplatzreservierung)
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
    """Context Manager für auto-commit/rollback."""
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
    """Tabellen anlegen + Migrationen falls nötig."""
    with db() as conn:
        conn.executescript("""
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

            CREATE INDEX IF NOT EXISTS idx_snapshots_tracker
                ON price_snapshots(tracker_id, fetched_at DESC);
        """)

        # Migration: add seat_cost column if upgrading from older schema
        try:
            conn.execute("ALTER TABLE trackers ADD COLUMN seat_cost REAL NOT NULL DEFAULT 0")
        except Exception:
            pass  # Column already exists

        # Migration: add seat_price column to snapshots
        try:
            conn.execute("ALTER TABLE price_snapshots ADD COLUMN seat_price REAL DEFAULT 0")
        except Exception:
            pass


# ─── Tracker CRUD ─────────────────────────────────────

def create_tracker(data: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO trackers
              (origin, destination, outbound_date, return_date,
               adults, children, baggage_json, seat_cost, active, created_at)
            VALUES (?,?,?,?,?,?,?,?,1,?)
        """, (
            data["origin"].upper(),
            data["destination"].upper(),
            data["outbound_date"],
            data.get("return_date"),
            data.get("adults", 1),
            data.get("children", 0),
            json.dumps(data.get("baggage", [])),
            data.get("seat_cost", 0.0),
            datetime.utcnow().isoformat(),
        ))
        return cur.lastrowid


def list_trackers(active_only: bool = True) -> list[dict]:
    with db() as conn:
        sql = "SELECT * FROM trackers"
        if active_only:
            sql += " WHERE active = 1"
        sql += " ORDER BY created_at DESC"
        rows = conn.execute(sql).fetchall()
        result = []
        for row in rows:
            t = dict(row)
            t["baggage"] = json.loads(t.pop("baggage_json", "[]"))
            result.append(t)
        return result


def get_tracker(tracker_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM trackers WHERE id = ?", (tracker_id,)
        ).fetchone()
        if not row:
            return None
        t = dict(row)
        t["baggage"] = json.loads(t.pop("baggage_json", "[]"))
        return t


def delete_tracker(tracker_id: int) -> bool:
    with db() as conn:
        cur = conn.execute("DELETE FROM trackers WHERE id = ?", (tracker_id,))
        return cur.rowcount > 0


def toggle_tracker(tracker_id: int, active: bool) -> bool:
    with db() as conn:
        cur = conn.execute(
            "UPDATE trackers SET active = ? WHERE id = ?",
            (1 if active else 0, tracker_id)
        )
        return cur.rowcount > 0


# ─── Snapshot CRUD ────────────────────────────────────

def save_snapshot(tracker_id: int, snap: dict) -> int:
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
            snap.get("flight_price"),
            snap.get("baggage_price"),
            snap.get("seat_price", 0.0),
            snap.get("total_price"),
            snap.get("outbound_flight"),
            snap.get("return_flight"),
            snap.get("currency", "EUR"),
            1 if snap.get("baggage_fallback") else 0,
            snap.get("status", "ok"),
            snap.get("error_message"),
            json.dumps(snap.get("raw")) if snap.get("raw") else None,
        ))
        return cur.lastrowid


def get_snapshots(tracker_id: int, limit: int = 90) -> list[dict]:
    with db() as conn:
        rows = conn.execute("""
            SELECT * FROM price_snapshots
            WHERE tracker_id = ?
            ORDER BY fetched_at DESC
            LIMIT ?
        """, (tracker_id, limit)).fetchall()
        return [dict(r) for r in rows]


def get_latest_snapshot(tracker_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute("""
            SELECT * FROM price_snapshots
            WHERE tracker_id = ? AND status = 'ok'
            ORDER BY fetched_at DESC LIMIT 1
        """, (tracker_id,)).fetchone()
        return dict(row) if row else None
