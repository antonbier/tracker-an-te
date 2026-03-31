"""
WanderSuite — Auth Database Layer
Users + WebAuthn credentials (Passkeys).
"""

import bcrypt
import json
from database import db


def init_auth_tables() -> None:
    """Create auth tables if they don't exist. Safe to call on every startup."""
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT,
                role          TEXT    NOT NULL DEFAULT 'user'
                                      CHECK(role IN ('admin','user')),
                created_at    TEXT    DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

            -- WebAuthn / Passkey credentials
            CREATE TABLE IF NOT EXISTS webauthn_credentials (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                credential_id  TEXT    NOT NULL UNIQUE,
                public_key     TEXT    NOT NULL,
                sign_count     INTEGER NOT NULL DEFAULT 0,
                device_name    TEXT    NOT NULL DEFAULT 'Passkey',
                aaguid         TEXT,
                created_at     TEXT    DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_wc_user ON webauthn_credentials(user_id);
            CREATE INDEX IF NOT EXISTS idx_wc_cred ON webauthn_credentials(credential_id);

            -- WebAuthn challenges (short-lived, cleaned up after use)
            CREATE TABLE IF NOT EXISTS webauthn_challenges (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                challenge  TEXT    NOT NULL UNIQUE,
                type       TEXT    NOT NULL CHECK(type IN ('register','login')),
                created_at TEXT    DEFAULT (datetime('now'))
            );
        """)


# ── Users ─────────────────────────────────────────────────────────────────────

def count_users() -> int:
    with db() as conn:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    return row[0]

def get_user_by_email(email: str) -> dict | None:
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
    with db() as conn:
        rows = conn.execute(
            "SELECT id, email, role, created_at FROM users ORDER BY created_at"
        ).fetchall()
    return [dict(r) for r in rows]

def create_user(email: str, password: str | None, role: str = "user") -> dict:
    """Create user. password can be None for passkey-only users."""
    password_hash = None
    if password:
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
    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(rounds=12)).decode()
    with db() as conn:
        cursor = conn.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (password_hash, user_id),
        )
    return cursor.rowcount > 0

def delete_user(user_id: int) -> bool:
    with db() as conn:
        cursor = conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    return cursor.rowcount > 0

def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── WebAuthn Credentials ──────────────────────────────────────────────────────

def save_credential(user_id: int, credential_id: str, public_key: str,
                    sign_count: int, device_name: str, aaguid: str | None) -> int:
    with db() as conn:
        cursor = conn.execute(
            """INSERT INTO webauthn_credentials
               (user_id, credential_id, public_key, sign_count, device_name, aaguid)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, credential_id, public_key, sign_count, device_name, aaguid),
        )
        return cursor.lastrowid

def get_credential(credential_id: str) -> dict | None:
    with db() as conn:
        row = conn.execute(
            """SELECT wc.*, u.email, u.role FROM webauthn_credentials wc
               JOIN users u ON u.id = wc.user_id
               WHERE wc.credential_id = ?""",
            (credential_id,)
        ).fetchone()
    return dict(row) if row else None

def list_credentials(user_id: int) -> list[dict]:
    with db() as conn:
        rows = conn.execute(
            """SELECT id, credential_id, device_name, aaguid, created_at
               FROM webauthn_credentials WHERE user_id = ? ORDER BY created_at""",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def update_sign_count(credential_id: str, sign_count: int) -> None:
    with db() as conn:
        conn.execute(
            "UPDATE webauthn_credentials SET sign_count=? WHERE credential_id=?",
            (sign_count, credential_id),
        )

def delete_credential(credential_id_pk: int, user_id: int) -> bool:
    with db() as conn:
        cursor = conn.execute(
            "DELETE FROM webauthn_credentials WHERE id=? AND user_id=?",
            (credential_id_pk, user_id),
        )
    return cursor.rowcount > 0


# ── WebAuthn Challenges ───────────────────────────────────────────────────────

def save_challenge(challenge: str, type_: str, user_id: int | None = None) -> None:
    # Clean up old challenges (older than 5 minutes)
    with db() as conn:
        conn.execute(
            "DELETE FROM webauthn_challenges WHERE created_at < datetime('now', '-5 minutes')"
        )
        conn.execute(
            "INSERT OR REPLACE INTO webauthn_challenges (user_id, challenge, type) VALUES (?, ?, ?)",
            (user_id, challenge, type_),
        )

def consume_challenge(challenge: str, type_: str) -> dict | None:
    """Fetch and delete a challenge (one-time use)."""
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM webauthn_challenges WHERE challenge=? AND type=?",
            (challenge, type_),
        ).fetchone()
        if row:
            conn.execute("DELETE FROM webauthn_challenges WHERE challenge=?", (challenge,))
    return dict(row) if row else None
