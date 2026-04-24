"""
WanderSuite — crud/settings.py
Global settings, per-user settings, provider configs,
notification settings, scheduler settings.
"""

from core.database import db

# ── Global Settings ───────────────────────────────────────────────────────────

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



# ── User Scheduler Settings ───────────────────────────────────────────────────

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



def update_scheduler_last_run(user_id: int) -> None:
    with db() as conn:
        conn.execute(
            """INSERT INTO user_scheduler_settings (user_id, update_interval_hours,
               notify_price_drop, notify_daily_summary, last_run_at, updated_at)
               VALUES (?,24,1,0,datetime('now'),datetime('now'))
               ON CONFLICT(user_id) DO UPDATE SET last_run_at=datetime('now')""",
            (user_id,)
        )

# ── User Notification Settings ────────────────────────────────────────────────

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


# ── Provider Configs ──────────────────────────────────────────────────────────

# ── Provider config functions ──────────────────────────────────────────────

_DEFAULT_PROVIDERS = [
    # name               enabled  test_mode
    ("ryanair_native",   1,       0),   # No key needed, on by default
    ("google_flights",   1,       0),   # Uses global serpapi_key
    ("kiwi",             0,       0),   # Requires kiwi_api_key
    ("duffel",           0,       1),   # Test mode by default
]



def _seed_provider_configs(conn) -> None:
    """Insert default provider rows if they don't exist yet (idempotent)."""
    for name, enabled, test_mode in _DEFAULT_PROVIDERS:
        existing = conn.execute(
            "SELECT name FROM provider_configs WHERE name=?", (name,)
        ).fetchone()
        if not existing:
            conn.execute(
                """INSERT INTO provider_configs (name, enabled, test_mode, updated_at)
                   VALUES (?, ?, ?, datetime('now'))""",
                (name, enabled, test_mode),
            )
    conn.commit()

def save_provider_config(name: str, enabled: bool, api_key: str | None = None, test_mode: bool = False) -> None:
    """Upsert a single provider config."""
    with db() as conn:
        existing = conn.execute(
            "SELECT name FROM provider_configs WHERE name=?", (name,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE provider_configs
                   SET enabled=?, api_key=COALESCE(?, api_key), test_mode=?, updated_at=datetime('now')
                   WHERE name=?""",
                (1 if enabled else 0, api_key if api_key and api_key != "••••••••" else None,
                 1 if test_mode else 0, name),
            )
        else:
            conn.execute(
                """INSERT INTO provider_configs (name, enabled, api_key, test_mode, updated_at)
                   VALUES (?, ?, ?, ?, datetime('now'))""",
                (name, 1 if enabled else 0, api_key, 1 if test_mode else 0),
            )

def get_provider_configs() -> list[dict]:
    """Return all provider configs (name, enabled, api_key, test_mode)."""
    with db() as conn:
        rows = conn.execute(
            "SELECT name, enabled, api_key, test_mode FROM provider_configs ORDER BY name"
        ).fetchall()
    return [dict(r) for r in rows]

