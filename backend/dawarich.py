"""
WanderSuite — Dawarich Integration (Multi-User)

Fix: float(home_lat) now guarded via normalize_coordinate()
     to handle legacy DMS strings in user_settings.
"""

import requests
import logging
import math
import time
from datetime import datetime, date, timezone
from collections import defaultdict
from typing import Optional
from crud.trips import save_detected_trip, list_detected_trips, unignore_detected_trips

logger = logging.getLogger(__name__)

NOMINATIM_URL     = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_HEADERS = {"User-Agent": "WanderSuite/1.0 (self-hosted travel tracker)"}


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def fetch_points(base_url: str, token: str,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 page_size: int = 1000) -> list[dict]:
    url = f"{base_url.rstrip('/')}/api/v1/points"
    headers = {"Authorization": f"Bearer {token}"}
    params  = {"per_page": page_size, "page": 1}
    if start_date: params["start_at"] = f"{start_date}T00:00:00Z"
    if end_date:   params["end_at"]   = f"{end_date}T23:59:59Z"

    all_points = []
    while True:
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.warning(f"[Dawarich] fetch error page {params['page']}: {e}")
            break

        if isinstance(data, dict):
            points = data.get("data", data.get("points", []))
        elif isinstance(data, list):
            points = data
        else:
            break

        if not points:
            break

        all_points.extend(points)

        total = data.get("total", 0) if isinstance(data, dict) else 0
        if total and len(all_points) >= total:
            break
        if len(points) < page_size:
            break
        params["page"] += 1

    return all_points


def normalize_point(p: dict) -> dict | None:
    try:
        lat = float(p.get("latitude") or p.get("lat") or 0)
        lon = float(p.get("longitude") or p.get("lng") or p.get("lon") or 0)
        if not lat or not lon or math.isnan(lat) or math.isnan(lon):
            return None

        ts = p.get("timestamp") or p.get("recorded_at") or p.get("created_at") or ""
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            try:
                ts_str = str(ts).replace("Z", "+00:00")
                dt = datetime.fromisoformat(ts_str)
            except Exception:
                return None

        return {"lat": lat, "lon": lon, "date": dt.date().isoformat()}
    except Exception:
        return None


def _reverse_geocode(lat: float, lon: float) -> tuple[str, str]:
    try:
        time.sleep(1)
        r = requests.get(
            NOMINATIM_URL,
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 10},
            headers=NOMINATIM_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        address = data.get("address", {})
        city    = (address.get("city") or address.get("town") or
                   address.get("village") or address.get("county") or "")
        country = address.get("country", "")
        return city, country
    except Exception:
        return "", ""


def _safe_float_coord(value: str | float | None, label: str) -> float | None:
    """
    FIX B1: Safely convert a coordinate value to float.
    Calls normalize_coordinate() first to handle legacy DMS strings
    (e.g. "46°47'57.91\"N") in user_settings.
    Returns None if the value cannot be parsed.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if not math.isnan(float(value)) else None
    # String: try normalize first (handles DMS), then direct float
    normalized = normalize_coordinate(str(value))
    if normalized:
        try:
            return float(normalized)
        except ValueError:
            pass
    # Fallback: try direct float conversion
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        logger.warning(f"[Dawarich] Invalid {label} value: {repr(value)}")
        return None


def sync_trips(base_url: str, token: str, home_lat: float, home_lon: float,
               start_date: Optional[str] = None, end_date: Optional[str] = None,
               user_id: int = 1, force_full: bool = False) -> dict:
    
    if force_full:
        n = unignore_detected_trips(user_id=user_id)
        logger.info(f"[Dawarich] Full sync: {n} ignorierte Trips reaktiviert")

    points_raw = fetch_points(base_url, token, start_date, end_date)
    if not points_raw:
        return {"points_loaded": 0, "trips_detected": 0, "trips_saved": 0}

    points = [p for raw in points_raw if (p := normalize_point(raw)) is not None]
    away   = [p for p in points if haversine_km(home_lat, home_lon, p["lat"], p["lon"]) > 50]

    by_date = defaultdict(list)
    for p in away:
        by_date[p["date"]].append(p)

    dates = sorted(by_date.keys())
    if not dates:
        return {"points_loaded": len(points), "trips_detected": 0, "trips_saved": 0}

    groups = []
    current = [dates[0]]
    for d in dates[1:]:
        from datetime import timedelta
        prev = date.fromisoformat(current[-1])
        curr = date.fromisoformat(d)
        if (curr - prev).days <= 2:
            current.append(d)
        else:
            groups.append(current)
            current = [d]
    groups.append(current)

    trips = [g for g in groups if len(g) >= 2]

    ignored_keys: set[tuple] = set()
    if not force_full:
        all_trips = list_detected_trips(limit=5000, user_id=user_id, include_ignored=True)
        for t in all_trips:
            if t.get("ignored"):
                ignored_keys.add((t["start_date"], t["end_date"]))

    saved = 0
    for g in trips:
        key = (g[0], g[-1])
        if key in ignored_keys:
            continue
        pts = []
        for d in g:
            pts.extend(by_date[d])
        mid = pts[len(pts)//2]
        city, country = _reverse_geocode(mid["lat"], mid["lon"])
        nights = (date.fromisoformat(g[-1]) - date.fromisoformat(g[0])).days + 1
        save_detected_trip({
            "start_date":    g[0],
            "end_date":      g[-1],
            "location_name": city,
            "country":       country,
            "lat":           mid["lat"],
            "lon":           mid["lon"],
            "nights":        nights,
            "source":        "dawarich",
        }, user_id=user_id)
        saved += 1

    return {
        "points_loaded":  len(points),
        "trips_detected": len(trips),
        "trips_saved":    saved,
    }
