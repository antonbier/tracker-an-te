"""
WanderSuite — crud/trips.py
ws_trips, trip_todos, detected_trips (Dawarich/manual journal),
user_data (budget, bucket list).
"""

import json
import logging
from core.database import db

logger = logging.getLogger(__name__)

# ── Detected Trips (Dawarich / manual journal) ────────────────────────────────

def list_detected_trips(user_id: int | None = None,
                         include_ignored: bool = False,
                         limit: int = 500) -> list[dict]:
    """Returns deduplicated trips: one entry per (start_date, end_date, location_name).
    Dedup done in Python to avoid SQLite subquery binding complexity.
    Also enriches empty location_name with country as fallback.
    """
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
            f"SELECT * FROM detected_trips {where} ORDER BY id DESC LIMIT ?",
            params + [limit * 10]   # fetch more to allow dedup
        ).fetchall()

    # Deduplicate in Python: keep first seen (highest id) per logical key
    seen: dict = {}
    result = []
    for r in rows:
        d = dict(r)
        # Normalise location_name / country fallback
        name = (d.get("location_name") or "").strip()
        if not name or name == "-":
            d["location_name"] = (d.get("country") or "").strip() or None
        key = (
            d.get("start_date", ""),
            d.get("end_date", ""),
            (d.get("location_name") or d.get("country") or "").lower().strip(),
            d.get("user_id", 0),
        )
        if key not in seen:
            seen[key] = True
            result.append(d)
        if len(result) >= limit:
            break

    # Re-sort by start_date DESC (was ordered by id DESC above)
    result.sort(key=lambda x: x.get("start_date") or "", reverse=True)
    return result


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


# ── User Data (budget, bucket list, arbitrary key-value) ─────────────────────

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


# ── Internal helpers ──────────────────────────────────────────────────────────

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


# ── WS-Trips (WanderWizzard planned trips) ────────────────────────────────────

def create_ws_trip(data: dict, user_id: int) -> int:
    """Neuen WanderWizzard-Trip anlegen. Gibt die neue ID zurück."""
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO ws_trips
               (user_id, title, destination, start_date, end_date,
                trip_type, budget, path, travel_mode,
                vibes, wish_text, flex_month, flex_nights, max_time,
                home_airport, adults, children, status, notes, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id,
                data.get("title", ""),
                data.get("destination", ""),
                data.get("start_date"),
                data.get("end_date"),
                data.get("trip_type", "flight"),
                data.get("budget"),
                data.get("path", "known"),
                data.get("travel_mode", "flight"),
                json.dumps(data.get("vibes", [])),
                data.get("wish_text"),
                data.get("flex_month"),
                data.get("flex_nights"),
                data.get("max_time"),
                data.get("home_airport"),
                data.get("adults", 2),
                data.get("children", 0),
                data.get("status", "planning"),
                data.get("notes"),
                now, now,
            )
        )
    return cur.lastrowid


def list_ws_trips(user_id: int, limit: int = 2000) -> list[dict]:
    """Alle WanderWizzard-Trips eines Users, neueste zuerst.
    Block 8: Limit von 100 auf 2000 erhöht — MyTrips-Statistik zählte
    zu wenige Trips wenn >100 Einträge vorhanden.
    """
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM ws_trips WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["vibes"] = json.loads(d.get("vibes") or "[]")
        except Exception:
            d["vibes"] = []
        result.append(d)
    return result


def get_ws_trip(trip_id: int, user_id: int) -> dict | None:
    """Einzelnen Trip laden (user-scoped)."""
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM ws_trips WHERE id=? AND user_id=?",
            (trip_id, user_id)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    try:
        d["vibes"] = json.loads(d.get("vibes") or "[]")
    except Exception:
        d["vibes"] = []
    return d


def update_ws_trip_status(trip_id: int, status: str, user_id: int) -> bool:
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    with db() as conn:
        r = conn.execute(
            "UPDATE ws_trips SET status=?, updated_at=? WHERE id=? AND user_id=?",
            (status, now, trip_id, user_id)
        )
    return r.rowcount > 0


def delete_ws_trip(trip_id: int, user_id: int) -> bool:
    with db() as conn:
        r = conn.execute(
            "DELETE FROM ws_trips WHERE id=? AND user_id=?",
            (trip_id, user_id)
        )
    return r.rowcount > 0


# ── Trip To-Dos ───────────────────────────────────────────────────────────────

# ── Trip To-Dos ───────────────────────────────────────────────────────────────

def create_trip_todos(trip_id: int, todos: list[dict]) -> int:
    """Bulk-insert To-Dos (aus KI oder manuell). Gibt Anzahl eingefügter Zeilen zurück."""
    if not todos:
        return 0
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    with db() as conn:
        conn.executemany(
            """INSERT INTO trip_todos (trip_id, task, category, due_date, sort_order, created_at)
               VALUES (?,?,?,?,?,?)""",
            [
                (trip_id, t.get("task", ""), t.get("category", "general"),
                 t.get("due_date", None), i, now)
                for i, t in enumerate(todos)
            ]
        )
    return len(todos)


def list_trip_todos(trip_id: int) -> list[dict]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM trip_todos WHERE trip_id=? ORDER BY sort_order, id",
            (trip_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def toggle_trip_todo(todo_id: int, trip_id: int) -> bool:
    with db() as conn:
        r = conn.execute(
            "UPDATE trip_todos SET is_done = 1 - is_done WHERE id=? AND trip_id=?",
            (todo_id, trip_id)
        )
    return r.rowcount > 0


def delete_trip_todo(todo_id: int, trip_id: int) -> bool:
    with db() as conn:
        r = conn.execute(
            "DELETE FROM trip_todos WHERE id=? AND trip_id=?",
            (todo_id, trip_id)
        )
    return r.rowcount > 0



# ── Tracker Booking State ─────────────────────────────────────────────────────
