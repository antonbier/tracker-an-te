"""
WanderSuite — Smoke Tests (Phase 3)

Ziel: Verifizieren dass die App startet, alle Router registriert sind
und die kritischsten Endpoints sinnvoll antworten.
Kein Full-Coverage — nur "startet es und antwortet es korrekt?"

Test-Kategorien:
  1. App-Start & Health
  2. Auth-Endpoints (Guest-Modus + Login-Validierung)
  3. Core-Endpoints (Status, Settings, Tracker, WsTrips)
  4. Input-Validierung (400/422 bei falschen Inputs)
  5. IDOR-Schutz (404 bei fremdem Tracker)
  6. Rate-Limiting-Struktur
  7. CRUD-Zyklus (Tracker anlegen → abrufen → löschen)
"""

import pytest
from datetime import date, timedelta


# ════════════════════════════════════════════════════════════════════════════
# 1. APP-START & HEALTH
# ════════════════════════════════════════════════════════════════════════════

def test_health(client):
    """Backend antwortet auf /health."""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_api_health(client):
    """/api/health ist ein Alias für /health."""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_openapi_schema(client):
    """OpenAPI-Schema ist erreichbar — alle Router sind registriert."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    # Prüfe ob alle kritischen Router-Gruppen registriert sind
    expected_prefixes = [
        "/api/trackers",
        "/api/ws-trips",
        "/api/settings",
        "/api/search/flights",
        "/api/search/hotels",
        "/api/search/camping",
        "/api/dawarich",
        "/api/discovery",
    ]
    for prefix in expected_prefixes:
        matching = [p for p in paths if p.startswith(prefix)]
        assert matching, f"Kein Endpoint mit Prefix '{prefix}' gefunden"


# ════════════════════════════════════════════════════════════════════════════
# 2. AUTH-ENDPOINTS (Guest-Modus)
# ════════════════════════════════════════════════════════════════════════════

def test_status_endpoint(client):
    """/api/status gibt auth_enabled=false zurück (Guest-Modus)."""
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert data["auth_enabled"] is False
    assert "needs_setup" in data


def test_login_rejected_when_auth_disabled(client):
    """Login schlägt fehl wenn AUTH_ENABLED=false."""
    r = client.post("/api/auth/login", json={"email": "a@b.com", "password": "test"})
    assert r.status_code == 400


def test_setup_rejected_when_auth_disabled(client):
    """Setup schlägt fehl wenn AUTH_ENABLED=false."""
    r = client.post("/api/auth/setup", json={"email": "a@b.com", "password": "test123"})
    assert r.status_code == 400


# ════════════════════════════════════════════════════════════════════════════
# 3. CORE-ENDPOINTS — SETTINGS & TRACKER
# ════════════════════════════════════════════════════════════════════════════

def test_get_settings(client):
    """GET /api/settings antwortet mit 200."""
    r = client.get("/api/settings")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_list_trackers_empty(client):
    """GET /api/trackers gibt leere Liste zurück (frische DB)."""
    r = client.get("/api/trackers")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_ws_trips_empty(client):
    """GET /api/ws-trips gibt leere Liste zurück."""
    r = client.get("/api/ws-trips")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_detected_trips_empty(client):
    """GET /api/trips gibt leere Liste zurück."""
    r = client.get("/api/trips")
    assert r.status_code == 200


def test_dashboard(client):
    """GET /api/dashboard antwortet mit 200."""
    r = client.get("/api/dashboard")
    assert r.status_code == 200


# ════════════════════════════════════════════════════════════════════════════
# 4. INPUT-VALIDIERUNG — 422 bei ungültigen Inputs
# ════════════════════════════════════════════════════════════════════════════

def test_tracker_create_invalid_iata(client):
    """Tracker mit ungültigem IATA-Code → 422."""
    r = client.post("/api/trackers", json={
        "origin": "INVALID",       # 7 Buchstaben statt 3
        "destination": "BGY",
        "outbound_date": (date.today() + timedelta(days=30)).isoformat(),
        "adults": 1,
    })
    assert r.status_code == 422


def test_tracker_create_past_date(client):
    """Tracker mit Datum in der Vergangenheit → 422."""
    r = client.post("/api/trackers", json={
        "origin": "BGY",
        "destination": "LGW",
        "outbound_date": "2020-01-01",  # Vergangenheit
        "adults": 1,
    })
    assert r.status_code == 422


def test_tracker_create_same_origin_destination(client):
    """Tracker mit origin == destination → 422."""
    r = client.post("/api/trackers", json={
        "origin": "BGY",
        "destination": "BGY",
        "outbound_date": (date.today() + timedelta(days=30)).isoformat(),
        "adults": 1,
    })
    assert r.status_code == 422


def test_ws_trip_create_invalid_budget(client):
    """WS-Trip mit negativem Budget → 422."""
    r = client.post("/api/ws-trips", json={
        "destination": "Berlin",
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=17)).isoformat(),
        "budget": -100,
    })
    assert r.status_code == 422


def test_ws_trip_end_before_start(client):
    """WS-Trip mit end_date < start_date → 422."""
    r = client.post("/api/ws-trips", json={
        "destination": "Wien",
        "start_date": (date.today() + timedelta(days=20)).isoformat(),
        "end_date": (date.today() + timedelta(days=10)).isoformat(),  # vor start
    })
    assert r.status_code == 422


def test_search_flights_missing_fields(client):
    """Flight-Suche ohne origin → 422."""
    r = client.post("/api/search/flights", json={
        "destination": "LGW",
        "outbound_date": (date.today() + timedelta(days=30)).isoformat(),
    })
    assert r.status_code in (400, 422)


# ════════════════════════════════════════════════════════════════════════════
# 5. IDOR-SCHUTZ — 404 bei nicht-existenten IDs
# ════════════════════════════════════════════════════════════════════════════

def test_get_nonexistent_tracker(client):
    """GET /api/trackers/99999 → 404."""
    r = client.get("/api/trackers/99999")
    assert r.status_code == 404


def test_get_nonexistent_price_history(client):
    """GET /api/prices/99999 → 404 (IDOR-Fix aus Bundle B)."""
    r = client.get("/api/prices/99999")
    assert r.status_code == 404


def test_get_nonexistent_ws_trip(client):
    """GET /api/ws-trips/99999 → 404."""
    r = client.get("/api/ws-trips/99999")
    assert r.status_code == 404


def test_delete_nonexistent_tracker(client):
    """DELETE /api/trackers/99999 → 404."""
    r = client.delete("/api/trackers/99999")
    assert r.status_code == 404


# ════════════════════════════════════════════════════════════════════════════
# 6. CRUD-ZYKLUS — Tracker + WS-Trip anlegen → abrufen → löschen
# ════════════════════════════════════════════════════════════════════════════

def test_tracker_full_crud(client):
    """
    Vollständiger CRUD-Zyklus für einen Ryanair-Tracker:
    POST → GET (in Liste) → GET (einzeln) → DELETE → GET (404)
    """
    future_date = (date.today() + timedelta(days=45)).isoformat()

    # CREATE
    r = client.post("/api/trackers", json={
        "origin": "BGY",
        "destination": "LGW",
        "outbound_date": future_date,
        "adults": 1,
    })
    assert r.status_code == 201, f"Create failed: {r.text}"
    tracker_id = r.json()["id"]
    assert isinstance(tracker_id, int)

    # LIST — muss in der Liste auftauchen
    r = client.get("/api/trackers")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert tracker_id in ids, f"Tracker {tracker_id} nicht in Liste: {ids}"

    # GET einzeln
    r = client.get(f"/api/trackers/{tracker_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["origin"] == "BGY"
    assert data["destination"] == "LGW"

    # DELETE
    r = client.delete(f"/api/trackers/{tracker_id}")
    assert r.status_code == 200

    # GET nach DELETE → 404
    r = client.get(f"/api/trackers/{tracker_id}")
    assert r.status_code == 404


def test_ws_trip_full_crud(client):
    """
    Vollständiger CRUD-Zyklus für einen WS-Trip:
    POST → GET (Liste) → GET (einzeln) → DELETE
    """
    r = client.post("/api/ws-trips", json={
        "destination": "Lissabon",
        "start_date": (date.today() + timedelta(days=60)).isoformat(),
        "end_date": (date.today() + timedelta(days=67)).isoformat(),
        "budget": 1500,
    })
    assert r.status_code == 201, f"Create failed: {r.text}"
    trip_id = r.json()["id"]

    # GET einzeln
    r = client.get(f"/api/ws-trips/{trip_id}")
    assert r.status_code == 200
    assert r.json()["destination"] == "Lissabon"

    # DELETE
    r = client.delete(f"/api/ws-trips/{trip_id}?mode=trip_only")
    assert r.status_code == 200

    # GET nach DELETE → 404
    r = client.get(f"/api/ws-trips/{trip_id}")
    assert r.status_code == 404


# ════════════════════════════════════════════════════════════════════════════
# 7. UTILITY-FUNKTIONEN — interne Logik
# ════════════════════════════════════════════════════════════════════════════

def test_jwt_token_creation():
    """JWT create_token + decode funktioniert korrekt."""
    from auth_jwt import create_token, JWT_SECRET, JWT_ALGO
    import jwt as pyjwt

    token = create_token(user_id=42, email="test@example.com", role="user")
    assert isinstance(token, str)
    assert len(token) > 20

    payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    assert payload["sub"] == "42"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "user"


def test_db_init_creates_tables():
    """init_db() erstellt alle erwarteten Tabellen."""
    from core.database import db

    expected_tables = [
        "trackers", "price_snapshots",
        "gf_trackers", "gf_snapshots",
        "homair_trackers", "homair_snapshots",
        "booking_trackers", "booking_snapshots",
        "detected_trips", "ws_trips", "trip_todos",
        "settings", "user_settings",
        "provider_configs",
    ]
    with db() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        existing = {r["name"] for r in rows}

    for table in expected_tables:
        assert table in existing, f"Tabelle '{table}' fehlt in der DB"


def test_get_latest_snapshots_bulk_empty():
    """get_latest_snapshots_bulk() gibt leeres Dict zurück für leere Liste."""
    from crud.trackers import get_latest_snapshots_bulk
    result = get_latest_snapshots_bulk("price_snapshots", [])
    assert result == {}


def test_evaluate_price_drop_no_previous():
    """_evaluate_price_drop() mit prev_price=None → kein Alert."""
    from scheduler import _evaluate_price_drop
    should_notify, diff, pct = _evaluate_price_drop(1, 99.0, None)
    assert should_notify is False
    assert diff == 0.0


def test_evaluate_price_drop_price_dropped():
    """_evaluate_price_drop() bei Preissturz → Alert."""
    from scheduler import _evaluate_price_drop
    should_notify, diff, pct = _evaluate_price_drop(1, 80.0, 100.0)
    assert should_notify is True
    assert diff == 20.0
    assert pct == 20.0


def test_evaluate_price_drop_price_risen():
    """_evaluate_price_drop() bei Preisanstieg → kein Alert."""
    from scheduler import _evaluate_price_drop
    should_notify, diff, pct = _evaluate_price_drop(1, 120.0, 100.0)
    assert should_notify is False


def test_evaluate_threshold_reached():
    """_evaluate_threshold() bei Unterschreitung → True."""
    from scheduler import _evaluate_threshold
    assert _evaluate_threshold(1, 79.0, 100.0, 80.0) is True


def test_evaluate_threshold_already_below():
    """_evaluate_threshold() wenn Preis schon vorher unter Threshold → False (Spam-Schutz)."""
    from scheduler import _evaluate_threshold
    assert _evaluate_threshold(1, 79.0, 75.0, 80.0) is False


def test_evaluate_threshold_not_reached():
    """_evaluate_threshold() wenn Preis noch über Threshold → False."""
    from scheduler import _evaluate_threshold
    assert _evaluate_threshold(1, 90.0, 100.0, 80.0) is False
