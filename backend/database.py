"""
WanderSuite — database.py  (Compatibility Shim)

WICHTIG: Diese Datei ist ein Übergangs-Shim.
Die eigentliche Logik lebt jetzt in:
  core/database.py   — Connection, DB_PATH, GUEST_USER_ID, db()
  core/db_init.py    — init_db()
  crud/settings.py   — Settings, Provider, Scheduler, Notifications
  crud/trackers.py   — Alle 4 Tracker-Typen + Generics + Booking State
  crud/trips.py      — ws_trips, todos, detected_trips, user_data
  crud/discovery.py  — discovery_pool_*

Alle bestehenden "from database import X" Imports funktionieren weiter.
Neue Imports sollen direkt auf die spezifischen Module zeigen.
"""

# ── core ──────────────────────────────────────────────────────────────────────
from core.database import (
    DB_PATH, GUEST_USER_ID,
    get_connection, db, _user_filter,
)
from core.db_init import init_db

# ── crud.settings ─────────────────────────────────────────────────────────────
from crud.settings import (
    save_setting, get_setting, get_all_settings,
    save_user_setting, get_user_setting, get_all_user_settings,
    get_user_scheduler_settings, save_user_scheduler_settings,
    update_scheduler_last_run,
    get_user_notification_settings, save_user_notification_settings,
    get_provider_configs, save_provider_config,
)

# ── crud.trackers ─────────────────────────────────────────────────────────────
from crud.trackers import (
    # Generic helpers (private but sometimes imported directly)
    _tracker_table, _snapshot_table,
    _list_trackers, _get_tracker, _delete_tracker,
    _toggle_tracker, _get_latest_snapshot,
    # Ryanair
    create_tracker, list_trackers, get_tracker,
    delete_tracker, toggle_tracker,
    set_tracker_threshold, set_tracker_wish_price,
    save_price_snapshot, get_latest_snapshot, get_snapshots,
    get_price_history, record_price_history,
    cleanup_old_price_history, cleanup_old_snapshots,
    # Google Flights
    create_gf_tracker, list_gf_trackers, get_gf_tracker,
    delete_gf_tracker, toggle_gf_tracker,
    save_gf_snapshot, get_latest_gf_snapshot, get_gf_history,
    # Homair / Camping
    create_homair_tracker, list_homair_trackers, get_homair_tracker,
    delete_homair_tracker, toggle_homair_tracker,
    save_homair_snapshot, get_latest_homair_snapshot,
    # Booking / Hotel
    create_booking_tracker, list_booking_trackers, get_booking_tracker,
    delete_booking_tracker, toggle_booking_tracker,
    save_booking_snapshot, get_latest_booking_snapshot,
    # Booking state
    mark_tracker_booked, unmark_tracker_booked,
    link_tracker_to_trip, get_trackers_for_trip,
)

# ── crud.trips ────────────────────────────────────────────────────────────────
from crud.trips import (
    # Detected trips
    list_detected_trips, create_detected_trip, save_detected_trip,
    update_detected_trip_cost, delete_detected_trip,
    unignore_detected_trips, update_trip_auto_cost,
    # User data
    save_user_data, get_user_data, list_user_data_keys,
    # WS-Trips
    create_ws_trip, list_ws_trips, get_ws_trip,
    update_ws_trip_status, delete_ws_trip,
    # Todos
    create_trip_todos, list_trip_todos,
    toggle_trip_todo, delete_trip_todo,
)

# ── crud.discovery ────────────────────────────────────────────────────────────
from crud.discovery import (
    discovery_pool_count, discovery_pool_get_unseen,
    discovery_pool_mark_shown, discovery_pool_upsert,
    discovery_pool_rotate, discovery_pool_clear,
    discovery_pool_update_image, discovery_pool_get_without_image,
    DISCOVERY_POOL_MAX, DISCOVERY_POOL_REFILL_THRESHOLD,
)
