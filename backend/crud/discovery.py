"""
WanderSuite — crud/discovery.py
Discovery pool CRUD: upsert, rotate, mark shown, image updates.
"""

import json
import logging
from core.database import db
DISCOVERY_POOL_MAX = 200
DISCOVERY_POOL_REFILL_THRESHOLD = 10

logger = logging.getLogger(__name__)

def discovery_pool_count(user_id: int) -> tuple[int, int]:
    """Returns (total, unseen) entries in pool for user."""
    with db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM discovery_pool WHERE user_id=?", (user_id,)
        ).fetchone()[0]
        unseen = conn.execute(
            "SELECT COUNT(*) FROM discovery_pool WHERE user_id=? AND shown=0", (user_id,)
        ).fetchone()[0]
    return total, unseen


def discovery_pool_get_unseen(user_id: int, limit: int = 6) -> list[dict]:
    """Return up to `limit` unseen suggestions from pool."""
    with db() as conn:
        rows = conn.execute(
            """SELECT * FROM discovery_pool
               WHERE user_id=? AND shown=0
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]


def discovery_pool_mark_shown(user_id: int, destination: str) -> None:
    """Mark a suggestion as shown."""
    with db() as conn:
        conn.execute(
            "UPDATE discovery_pool SET shown=1 WHERE user_id=? AND destination=?",
            (user_id, destination)
        )


def discovery_pool_upsert(user_id: int, entry: dict) -> bool:
    """Insert or ignore (UNIQUE constraint: user_id + destination).
    Returns True if inserted, False if already existed."""
    with db() as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO discovery_pool
               (user_id, destination, country, reason, climate, landscape,
                trip_type, image_url, image_source, prefill_json, shown, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,0,datetime('now'))""",
            (
                user_id,
                entry.get("destination", ""),
                entry.get("country", ""),
                entry.get("reason", ""),
                entry.get("climate"),
                entry.get("landscape"),
                entry.get("trip_type"),
                entry.get("image_url"),
                entry.get("image_source", "css_fallback"),
                json.dumps(entry.get("prefill", {})),
            )
        )
    return cur.rowcount > 0


def discovery_pool_rotate(user_id: int) -> int:
    """If pool exceeds DISCOVERY_POOL_MAX, delete oldest shown entries first.
    Returns number of deleted rows."""
    with db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM discovery_pool WHERE user_id=?", (user_id,)
        ).fetchone()[0]
        if total <= DISCOVERY_POOL_MAX:
            return 0
        to_delete = total - DISCOVERY_POOL_MAX
        # Delete oldest shown entries first
        ids = conn.execute(
            """SELECT id FROM discovery_pool WHERE user_id=? AND shown=1
               ORDER BY created_at ASC LIMIT ?""",
            (user_id, to_delete)
        ).fetchall()
        if not ids:
            # Fallback: delete oldest overall
            ids = conn.execute(
                """SELECT id FROM discovery_pool WHERE user_id=?
                   ORDER BY created_at ASC LIMIT ?""",
                (user_id, to_delete)
            ).fetchall()
        if ids:
            placeholders = ",".join("?" * len(ids))
            id_list = [r[0] for r in ids]
            conn.execute(
                f"DELETE FROM discovery_pool WHERE id IN ({placeholders})", id_list
            )
            return len(ids)
    return 0


def discovery_pool_clear(user_id: int) -> int:
    """Clear all pool entries for a user (force full refresh)."""
    with db() as conn:
        r = conn.execute(
            "DELETE FROM discovery_pool WHERE user_id=?", (user_id,)
        )
    return r.rowcount


def discovery_pool_update_image(user_id: int, destination: str,
                                 image_url: str, image_source: str) -> bool:
    """Bild-URL eines Pool-Eintrags aktualisieren (z.B. nach Retry-Job)."""
    with db() as conn:
        r = conn.execute(
            """UPDATE discovery_pool SET image_url=?, image_source=?
               WHERE user_id=? AND destination=?""",
            (image_url, image_source, user_id, destination)
        )
    return r.rowcount > 0


def discovery_pool_get_without_image(user_id: int, limit: int = 20) -> list[dict]:
    """Alle Pool-Einträge ohne echtes Bild (local_fallback oder css_fallback)."""
    with db() as conn:
        rows = conn.execute(
            """SELECT * FROM discovery_pool
               WHERE user_id=? AND image_source IN ('local_fallback', 'css_fallback')
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]



# ══════════════════════════════════════════════════════════════════════════════
# WanderWizzard Trips CRUD
# ══════════════════════════════════════════════════════════════════════════════
