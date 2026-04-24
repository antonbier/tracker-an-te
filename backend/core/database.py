"""
WanderSuite — core/database.py
Connection factory, context manager, user-filter helper.
Imported by every crud/* module.
"""

import sqlite3
import os
from contextlib import contextmanager

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
