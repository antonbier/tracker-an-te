"""
WanderSuite — Dawarich Integration
Trip Detection via Haversine + Overnight Algorithm.
Reverse Geocoding via Nominatim (OpenStreetMap, kostenlos).
"""

import requests
import logging
import math
import time
from datetime import datetime, date
from collections import defaultdict
from typing import Optional

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_HEADERS = {
    "User-Agent": "WanderSuite/1.0 (self-hosted travel tracker)"
}


# ─── Haversine ───────────────────────────────────────

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Entfernung zwischen zwei Koordinaten in km (Haversine-Formel)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─── Dawarich API ────────────────────────────────────

def fetch_points(
    base_url: str,
    token: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page_size: int = 1000,
) -> list[dict]:
    """
    Alle Location-Punkte von Dawarich abrufen.
    Dawarich API: GET /api/v1/points?start_at=...&end_at=...&per_page=...
    Gibt Liste von {lat, lon, timestamp, ...} zurück.
    """
    url = f"{base_url.rstrip('/')}/api/v1/points"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    all_points = []
    page = 1

    while True:
        params = {
            "per_page": page_size,
            "page":     page,
        }
        if start_date:
            params["start_at"] = start_date
        if end_date:
            params["end_at"] = end_date

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            logger.info(f"[Dawarich] Page {page}: HTTP {resp.status_code}")

            if resp.status_code == 401:
                raise ValueError("Dawarich: Ungültiger API Token")
            if resp.status_code == 404:
                raise ValueError(f"Dawarich API nicht gefunden: {url}")
            resp.raise_for_status()

            data = resp.json()

            # Dawarich gibt entweder {"points": [...]} oder direkt [...]
            points = data if isinstance(data, list) else data.get("points", data.get("data", []))

            if not points:
                break

            all_points.extend(points)
            logger.info(f"[Dawarich] Page {page}: {len(points)} Punkte geladen (total: {len(all_points)})")

            # Prüfe ob es noch weitere Seiten gibt
            if isinstance(data, dict):
                total = data.get("total", data.get("count", 0))
                if total and len(all_points) >= total:
                    break
            if len(points) < page_size:
                break

            page += 1
            time.sleep(0.3)  # Rate limiting

        except requests.RequestException as e:
            logger.error(f"[Dawarich] Request Fehler: {e}")
            raise

    logger.info(f"[Dawarich] Insgesamt {len(all_points)} Punkte geladen")
    return all_points


def normalize_point(point: dict) -> Optional[dict]:
    """
    Verschiedene Dawarich-Punkt-Formate normalisieren.
    Gibt {lat, lon, date_str} zurück oder None wenn ungültig.
    """
    # Koordinaten
    lat = point.get("latitude", point.get("lat"))
    lon = point.get("longitude", point.get("lng", point.get("lon")))

    if lat is None or lon is None:
        return None

    try:
        lat, lon = float(lat), float(lon)
    except (ValueError, TypeError):
        return None

    # Timestamp → Datum
    ts = (point.get("timestamp") or point.get("recorded_at") or
          point.get("created_at") or point.get("datetime") or "")

    if not ts:
        return None

    try:
        # ISO-Format: 2024-10-12T14:30:00Z oder 2024-10-12 14:30:00
        date_str = str(ts)[:10]
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

    return {"lat": lat, "lon": lon, "date": date_str}


# ─── Trip Detection Algorithm ────────────────────────

def detect_trips(
    points: list[dict],
    home_lat: float,
    home_lon: float,
    min_distance_km: float = 50.0,
    gap_days: int = 2,
) -> list[dict]:
    """
    Erkennt Übernacht-Reisen aus Location-Punkten.

    Algorithmus:
    1. Punkte normalisieren
    2. Punkte > min_distance_km von Home filtern
    3. Nach Datum gruppieren
    4. Zusammenhängende Tage zu Trips zusammenfassen (max gap_days Lücke)
    5. Overnight-Bedingung: min. 2 verschiedene Tage (= mind. 1 Nacht)
    6. Pro Trip: Mittelpunkt-Koordinaten für Reverse Geocoding
    """
    # 1. Normalisieren
    normalized = []
    for p in points:
        n = normalize_point(p)
        if n:
            normalized.append(n)

    if not normalized:
        logger.warning("[Dawarich] Keine gültigen Punkte nach Normalisierung")
        return []

    # 2. Filter: > 50km von Home
    away_points = [
        p for p in normalized
        if haversine_km(p["lat"], p["lon"], home_lat, home_lon) > min_distance_km
    ]

    logger.info(f"[Dawarich] {len(away_points)} / {len(normalized)} Punkte > {min_distance_km}km von Home")

    if not away_points:
        return []

    # 3. Nach Datum gruppieren
    by_date: dict[str, list[dict]] = defaultdict(list)
    for p in away_points:
        by_date[p["date"]].append(p)

    # 4. Sortierte Tage
    sorted_dates = sorted(by_date.keys())

    # 5. Zusammenhängende Tage zu Trips zusammenfassen
    trips = []
    current_trip_dates = [sorted_dates[0]]

    for i in range(1, len(sorted_dates)):
        prev = date.fromisoformat(sorted_dates[i-1])
        curr = date.fromisoformat(sorted_dates[i])
        gap  = (curr - prev).days

        if gap <= gap_days:
            current_trip_dates.append(sorted_dates[i])
        else:
            # Trip abschließen
            if len(current_trip_dates) >= 2:  # Overnight-Bedingung
                trips.append(_build_trip(current_trip_dates, by_date))
            current_trip_dates = [sorted_dates[i]]

    # Letzten Trip abschließen
    if len(current_trip_dates) >= 2:
        trips.append(_build_trip(current_trip_dates, by_date))

    logger.info(f"[Dawarich] {len(trips)} Übernacht-Reisen erkannt")
    return trips


def _build_trip(trip_dates: list[str], by_date: dict) -> dict:
    """Einen Trip aus einer Liste von Tagen aufbauen."""
    all_points = []
    for d in trip_dates:
        all_points.extend(by_date[d])

    # Mittelpunkt berechnen
    avg_lat = sum(p["lat"] for p in all_points) / len(all_points)
    avg_lon = sum(p["lon"] for p in all_points) / len(all_points)

    start = trip_dates[0]
    end   = trip_dates[-1]
    nights = (date.fromisoformat(end) - date.fromisoformat(start)).days

    return {
        "start_date": start,
        "end_date":   end,
        "nights":     max(1, nights),
        "lat":        round(avg_lat, 4),
        "lon":        round(avg_lon, 4),
        "point_count": len(all_points),
    }


# ─── Reverse Geocoding ───────────────────────────────

def reverse_geocode(lat: float, lon: float) -> tuple[str, str]:
    """
    Stadt + Land via Nominatim (OpenStreetMap).
    Gibt (location_name, country) zurück.
    Rate limit: max 1 req/sec laut Nominatim Policy.
    """
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 10},
            headers=NOMINATIM_HEADERS,
            timeout=10,
        )
        if not resp.ok:
            return f"{lat:.3f},{lon:.3f}", ""

        data = resp.json()
        address = data.get("address", {})

        city = (address.get("city") or address.get("town") or
                address.get("village") or address.get("county") or
                address.get("state") or "")
        country = address.get("country", "")

        return city, country

    except requests.RequestException as e:
        logger.warning(f"[Nominatim] Fehler: {e}")
        return f"{lat:.3f},{lon:.3f}", ""


# ─── Main Sync Function ──────────────────────────────

def sync_trips(
    base_url: str,
    token: str,
    home_lat: float,
    home_lon: float,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """
    Kompletter Sync: Dawarich → Trip Detection → DB.
    Gibt Zusammenfassung zurück.
    """
    from database import save_detected_trip

    # 1. Punkte laden
    try:
        raw_points = fetch_points(base_url, token, start_date, end_date)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Dawarich Verbindungsfehler: {str(e)}"}

    if not raw_points:
        return {"error": "Keine Punkte von Dawarich erhalten — API korrekt konfiguriert?"}

    # 2. Trip Detection
    trips = detect_trips(raw_points, home_lat, home_lon)

    if not trips:
        return {
            "points_loaded": len(raw_points),
            "trips_detected": 0,
            "message": f"{len(raw_points)} Punkte geladen, keine Übernacht-Reisen erkannt (>50km von Home, min. 2 Tage)"
        }

    # 3. Reverse Geocoding + DB speichern
    saved = 0
    results = []

    for i, trip in enumerate(trips):
        logger.info(f"[Dawarich] Geocoding Trip {i+1}/{len(trips)}: {trip['lat']},{trip['lon']}")

        city, country = reverse_geocode(trip["lat"], trip["lon"])
        trip["location_name"] = city
        trip["country"] = country
        trip["source"] = "dawarich"

        save_detected_trip(trip)
        saved += 1
        results.append({
            "start_date":    trip["start_date"],
            "end_date":      trip["end_date"],
            "nights":        trip["nights"],
            "location_name": city,
            "country":       country,
        })

        # Nominatim Rate Limit: 1 req/sec
        if i < len(trips) - 1:
            time.sleep(1.1)

    return {
        "points_loaded":  len(raw_points),
        "trips_detected": len(trips),
        "trips_saved":    saved,
        "trips":          results,
    }
