"""
WanderSuite — core/db_init.py
Database initialisation: CREATE TABLE + migrations + seed data.
Called once at startup from main.py.
"""

import logging
from .database import db

logger = logging.getLogger(__name__)


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
                stops            INTEGER DEFAULT 0,
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

            -- ── WanderWizzard Trips (Container-Entität) ──────────────────────────────
            CREATE TABLE IF NOT EXISTS ws_trips (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL DEFAULT 1,
                title        TEXT    NOT NULL DEFAULT '',
                destination  TEXT    NOT NULL DEFAULT '',
                start_date   TEXT,
                end_date     TEXT,
                trip_type    TEXT    NOT NULL DEFAULT 'flight',  -- 'flight'|'car'|'inspire'
                budget       REAL             DEFAULT NULL,
                path         TEXT    NOT NULL DEFAULT 'known',   -- 'known'|'inspire'
                travel_mode  TEXT    NOT NULL DEFAULT 'flight',  -- 'flight'|'car'
                vibes        TEXT    NOT NULL DEFAULT '[]',       -- JSON array
                wish_text    TEXT             DEFAULT NULL,
                flex_month   TEXT             DEFAULT NULL,
                flex_nights  INTEGER          DEFAULT NULL,
                max_time     TEXT             DEFAULT NULL,
                home_airport TEXT             DEFAULT NULL,
                adults       INTEGER NOT NULL DEFAULT 2,
                children     INTEGER NOT NULL DEFAULT 0,
                status       TEXT    NOT NULL DEFAULT 'planning', -- 'planning'|'booked'|'completed'
                notes        TEXT             DEFAULT NULL,
                created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            -- ── Trip To-Dos (KI-generiert) ────────────────────────────────────────────
            CREATE TABLE IF NOT EXISTS trip_todos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id    INTEGER NOT NULL REFERENCES ws_trips(id) ON DELETE CASCADE,
                task       TEXT    NOT NULL,
                category   TEXT    NOT NULL DEFAULT 'general',  -- 'booking'|'packing'|'documents'|'general'
                is_done    INTEGER NOT NULL DEFAULT 0,
                due_date   TEXT             DEFAULT NULL,        -- YYYY-MM-DD optional
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );

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

            -- Flight provider configuration (enabled/disabled + API keys)
            CREATE TABLE IF NOT EXISTS provider_configs (
                name       TEXT PRIMARY KEY,
                enabled    INTEGER NOT NULL DEFAULT 0,
                api_key    TEXT    DEFAULT NULL,
                test_mode  INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );


            -- Discovery Pool: pre-generated AI suggestions per user (max ~200)
            CREATE TABLE IF NOT EXISTS discovery_pool (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL,
                destination    TEXT    NOT NULL,
                country        TEXT    NOT NULL DEFAULT '',
                reason         TEXT    NOT NULL DEFAULT '',
                climate        TEXT    DEFAULT NULL,
                landscape      TEXT    DEFAULT NULL,
                trip_type      TEXT    DEFAULT NULL,
                image_url      TEXT    DEFAULT NULL,
                image_source   TEXT    NOT NULL DEFAULT 'css_fallback',
                prefill_json   TEXT    NOT NULL DEFAULT '{}',
                shown          INTEGER NOT NULL DEFAULT 0,
                created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, destination)
            );

            -- Per-user data (trips list, budget, bucketlist)
            CREATE TABLE IF NOT EXISTS user_data (
                user_id    INTEGER NOT NULL DEFAULT 1,
                key        TEXT    NOT NULL,
                value      TEXT    NOT NULL,
                updated_at TEXT    DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, key)
            );

            -- Dokumenten-Vault: Metadaten. Der Dateiinhalt selbst liegt Fernet-verschlüsselt
            -- auf Disk (/app/data/vault/{user_id}/{filename}) — siehe document_vault.py.
            -- Metadaten sind bewusst unverschlüsselt (keine Geheimnisse, nur der Inhalt ist es).
            CREATE TABLE IF NOT EXISTS documents (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id             INTEGER NOT NULL DEFAULT 1,
                trip_id             INTEGER DEFAULT NULL REFERENCES ws_trips(id) ON DELETE SET NULL,
                doc_type            TEXT    NOT NULL DEFAULT 'other',
                title               TEXT    NOT NULL,
                filename            TEXT    NOT NULL,
                orig_filename       TEXT,
                mime_type           TEXT,
                size_bytes          INTEGER,
                expiry_date         TEXT    DEFAULT NULL,
                notes               TEXT    DEFAULT NULL,
                expiry_notified_at  TEXT    DEFAULT NULL,
                created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            -- Packlisten-Vorlagen: wiederverwendbare, trip-unabhängige Packlisten.
            -- is_done ist persistent (kein Instanzierungsmodell) — Reset-Endpoint setzt
            -- vor der nächsten Reise wieder alles zurück statt jedes Mal neu zu bauen.
            CREATE TABLE IF NOT EXISTS packing_templates (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL DEFAULT 1,
                name       TEXT    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS packing_template_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL REFERENCES packing_templates(id) ON DELETE CASCADE,
                text        TEXT    NOT NULL,
                category    TEXT    NOT NULL DEFAULT 'general',
                is_done     INTEGER NOT NULL DEFAULT 0,
                sort_order  INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)

        # ── Seed default provider configs (idempotent) ────────────────────
        _seed_provider_configs(conn)

        # ── Fix: Guest-Settings (user_id=0) auf 1 migrieren (idempotent) ───
        _migrate_guest_settings(conn)

        # ── Safe migrations (idempotent ALTER TABLE) ──────────────────────────
        migrations = [
            ("trackers",         "user_id INTEGER NOT NULL DEFAULT 1"),
            ("gf_trackers",      "user_id INTEGER NOT NULL DEFAULT 1"),
            ("homair_trackers",  "user_id INTEGER NOT NULL DEFAULT 1"),
            ("booking_trackers", "user_id INTEGER NOT NULL DEFAULT 1"),
            ("detected_trips",   "user_id INTEGER NOT NULL DEFAULT 1"),
            ("ws_trips",          "source_detected_id INTEGER DEFAULT NULL"),
            ("ws_trips",          "synced_expenses REAL DEFAULT NULL"),
            ("ws_trips",          "synced_transactions_json TEXT DEFAULT NULL"),
            ("ws_trips",          "synced_at TEXT DEFAULT NULL"),
            ("ws_trips",          "image_url TEXT DEFAULT NULL"),
            ("ws_trips",          "image_author TEXT DEFAULT NULL"),
            ("ws_trips",          "image_author_url TEXT DEFAULT NULL"),
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
            ("price_snapshots",  "departure_time TEXT DEFAULT NULL"),
            ("price_snapshots",  "arrival_time TEXT DEFAULT NULL"),
            ("price_snapshots",  "flight_number TEXT DEFAULT NULL"),
            # gf_snapshots: stops field for layover display
            ("gf_snapshots",    "stops INTEGER DEFAULT 0"),
            # gf_snapshots: layover details (airports + durations as JSON)
            ("gf_snapshots",    "layover_airports TEXT DEFAULT NULL"),
            ("gf_snapshots",    "layover_durations TEXT DEFAULT NULL"),
            # booking_url for deeplinks
            ("trackers",         "booking_url TEXT DEFAULT NULL"),
            ("gf_trackers",      "booking_url TEXT DEFAULT NULL"),
            ("homair_trackers",  "booking_url TEXT DEFAULT NULL"),
            ("booking_trackers", "booking_url TEXT DEFAULT NULL"),
            # CRITICAL FIX (Code-Review-Sprint): trip_id/is_booked/booked_price fehlten
            # in ALLEN 4 Tracker-Tabellen komplett — crud/trackers.py (mark_tracker_booked,
            # unmark_tracker_booked, link_tracker_to_trip, get_trackers_for_trip) nutzt diese
            # Spalten seit jeher, jeder Aufruf warf "no such column" (silent 500 bzw. vom
            # Try/Except verschluckt). TripHub-Tracker-Buchen/Verknüpfen war dadurch komplett
            # kaputt. CLAUDE.md dokumentierte das Schema bereits so, die Migration fehlte nur.
            ("trackers",         "trip_id INTEGER DEFAULT NULL"),
            ("gf_trackers",      "trip_id INTEGER DEFAULT NULL"),
            ("homair_trackers",  "trip_id INTEGER DEFAULT NULL"),
            ("booking_trackers", "trip_id INTEGER DEFAULT NULL"),
            ("trackers",         "is_booked INTEGER NOT NULL DEFAULT 0"),
            ("gf_trackers",      "is_booked INTEGER NOT NULL DEFAULT 0"),
            ("homair_trackers",  "is_booked INTEGER NOT NULL DEFAULT 0"),
            ("booking_trackers", "is_booked INTEGER NOT NULL DEFAULT 0"),
            ("trackers",         "booked_price REAL DEFAULT NULL"),
            ("gf_trackers",      "booked_price REAL DEFAULT NULL"),
            ("homair_trackers",  "booked_price REAL DEFAULT NULL"),
            ("booking_trackers", "booked_price REAL DEFAULT NULL"),
            # user_settings: Immich integration (per-user)
            ("user_settings",    "immich_url TEXT DEFAULT NULL"),
            ("user_settings",    "immich_api_key TEXT DEFAULT NULL"),
            ("user_settings",    "immich_geo_sync INTEGER DEFAULT 0"),
            # user_settings: WanderWizzard defaults (per-user)
            ("user_settings",    "ww_adults INTEGER DEFAULT 2"),
            ("user_settings",    "ww_children INTEGER DEFAULT 0"),
            ("user_settings",    "ww_home_airport TEXT DEFAULT NULL"),
            ("user_settings",    "ww_lug_s10 INTEGER DEFAULT 0"),
            ("user_settings",    "ww_lug_s20 INTEGER DEFAULT 0"),
            ("user_settings",    "ww_lug_s23 INTEGER DEFAULT 0"),
            ("user_settings",    "ww_lug_l10 INTEGER DEFAULT 0"),
            ("user_settings",    "ww_lug_l20 INTEGER DEFAULT 1"),
            ("user_settings",    "ww_lug_l23 INTEGER DEFAULT 0"),
            ("user_settings",    "ww_dep_min TEXT DEFAULT NULL"),
            ("user_settings",    "ww_dep_max TEXT DEFAULT NULL"),
            ("user_settings",    "ww_arr_min TEXT DEFAULT NULL"),
            ("user_settings",    "ww_arr_max TEXT DEFAULT NULL"),
            # WanderWizzard: Reisepersönlichkeit
            ("user_settings",    "travel_style TEXT DEFAULT NULL"),
            ("user_settings",    "climate_pref TEXT DEFAULT NULL"),
            ("user_settings",    "landscape_pref TEXT DEFAULT NULL"),
            ("user_settings",    "companions TEXT DEFAULT NULL"),
            ("user_settings",    "wish_text TEXT DEFAULT NULL"),
            ("user_settings",    "unsplash_key TEXT DEFAULT NULL"),
            # WanderWizzard: Reisepersönlichkeit — Mobilitäts-Prefs
            ("user_settings",    "travel_mode TEXT DEFAULT NULL"),
            ("user_settings",    "max_travel_time TEXT DEFAULT NULL"),
            ("user_settings",    "history_mode TEXT DEFAULT NULL"),
            # Discovery Pool
            ("discovery_pool",   "shown INTEGER NOT NULL DEFAULT 0"),
            # WS-Trips: manual expenses
            ("ws_trips",         "manual_expenses REAL NOT NULL DEFAULT 0"),
            ("trip_todos",        "due_date TEXT DEFAULT NULL"),
            # Block 7 — Smart Trip Editing: kosmetischer title + geocodierte Geodaten
            # lat/lon: Koordinaten des Hauptziels (optional, aus Geocoder befüllt)
            # Altdaten (Dawarich-Sync) behalten ihre bestehenden Werte, da ADD COLUMN
            # DEFAULT NULL ist → keine Datenverlust, Wetter/Maps weiterhin funktional
            ("ws_trips",         "lat REAL DEFAULT NULL"),
            ("ws_trips",         "lon REAL DEFAULT NULL"),
            # Outgoing webhook notifications (Fernet-verschlüsselt, analog Telegram/Gotify)
            ("user_notification_settings", "webhook_url TEXT DEFAULT NULL"),
        ]
        for table, col_def in migrations:
            col_name = col_def.split()[0]
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
                conn.commit()
            except Exception as e:
                if "duplicate column name" not in str(e).lower():
                    logger.warning(f"[Migration] {table}.{col_name} fehlgeschlagen: {e}")




def _seed_provider_configs(conn) -> None:
    """Insert default provider rows if they don't exist yet (idempotent)."""
    _DEFAULT_PROVIDERS = [
        ("ryanair_native",  1, 0),
        ("google_flights",  1, 0),
        ("kiwi",            0, 0),
        ("duffel",          0, 1),
    ]
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


def _migrate_guest_settings(conn) -> None:
    """
    Fix: routes/settings.py speicherte Pro-User-Settings (Heimatort, Dawarich,
    Immich, ActualBudget, ...) frueher unter der rohen Guest-User-ID (0) statt der
    im Rest der Codebase ueblichen Normalisierung auf 1 (siehe _uid()-Konvention
    in ws_trips.py, dawarich.py, scheduler.py, discovery.py -- user.get("id", 1) or 1).
    Kein anderer Consumer sucht unter user_id=0, d.h. im No-Auth-Modus gespeicherte
    Settings wurden von jedem Feature ausser dem Settings-Modal selbst ignoriert.
    Migriert bestehende Zeilen einmalig nach user_id=1, ueberschreibt NIE bereits
    vorhandene user_id=1-Werte (die haben Vorrang, falls schon manuell gesetzt).
    """
    rows = conn.execute(
        "SELECT key, value_enc, updated_at FROM user_settings WHERE user_id=0"
    ).fetchall()
    if not rows:
        return
    migrated = 0
    for key, value_enc, updated_at in rows:
        existing = conn.execute(
            "SELECT 1 FROM user_settings WHERE user_id=1 AND key=?", (key,)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO user_settings (user_id, key, value_enc, updated_at) VALUES (1, ?, ?, ?)",
                (key, value_enc, updated_at)
            )
            migrated += 1
    conn.execute("DELETE FROM user_settings WHERE user_id=0")
    conn.commit()
    if migrated:
        logger.info(f"[Migration] {migrated} Guest-Settings (user_id=0 -> 1) migriert")
