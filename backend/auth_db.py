"""
WanderSuite — Auth Database Layer
Users table + CRUD for authentication.

Schema:
    users (id, email, password_hash, role, created_at)
    role: 'admin' | 'user'

Passwords hashed with bcrypt (cost factor 12).
No WebAuthn, no user_id on content tables — Phase 1 only.
"""

import bcrypt
from database import db  # reuse existing connection/context manager


def init_auth_tables() -> None:
    """Create users table if it doesn't exist. Safe to call on every startup."""
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                email        TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT   NOT NULL,
                role         TEXT    NOT NULL DEFAULT 'user'
                                    CHECK(role IN ('admin','user')),
                created_at   TEXT    DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """)


# ── Queries ───────────────────────────────────────────────────────────────────

def count_users() -> int:
    """Return total number of registered users."""
    with db() as conn:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    return row[0]


def get_user_by_email(email: str) -> dict | None:
    """Look up a user by email (case-insensitive). Returns dict or None."""
    with db() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, role, created_at FROM users WHERE email=?",
            (email.strip().lower(),)
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute(
            "SELECT id, email, role, created_at FROM users WHERE id=?",
            (user_id,)
        ).fetchone()
    return dict(row) if row else None


def list_users() -> list[dict]:
    """Return all users (for admin panel). Password hashes excluded."""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, email, role, created_at FROM users ORDER BY created_at"
        ).fetchall()
    return [dict(r) for r in rows]


def create_user(email: str, password: str, role: str = "user") -> dict:
    """
    Create a new user. Returns the created user dict.
    Raises ValueError if email already exists.
    """
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    try:
        with db() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                (email.strip().lower(), password_hash, role),
            )
            return {"id": cursor.lastrowid, "email": email.lower(), "role": role}
    except Exception as e:
        if "UNIQUE" in str(e):
            raise ValueError(f"E-Mail bereits registriert: {email}")
        raise


def update_password(user_id: int, new_password: str) -> bool:
    """Update a user's password. Returns True if user was found and updated."""
    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(rounds=12)).decode()
    with db() as conn:
        cursor = conn.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (password_hash, user_id),
        )
    return cursor.rowcount > 0


def delete_user(user_id: int) -> bool:
    """Delete a user. Returns True if deleted, False if not found."""
    with db() as conn:
        cursor = conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    return cursor.rowcount > 0


# ── Password verification ─────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    """Check plain password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False
