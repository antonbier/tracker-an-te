"""
WanderSuite — Google Flights Scraper
SerpAPI Google Flights endpoint — returns airline, flight number,
departure/arrival times, and duration.
Free plan: 100 searches/month (shared with Booking scraper).
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
SERPAPI_BASE = "https://serpapi.com/search"


def fetch_google_flights(tracker: dict, api_key: str) -> dict:
    if not api_key:
        return _error_snap("SerpAPI Key nicht konfiguriert")

    origin      = tracker["origin"]
    destination = tracker["destination"]
    out_date    = tracker["outbound_date"]
    ret_date    = tracker.get("return_date")
    adults      = tracker.get("adults", 1)
    children    = tracker.get("children", 0)

    logger.info(f"[GF] {origin}→{destination} {out_date} | adults={adults} children={children}")

    # SerpAPI: type=1 = Round-trip, type=2 = One-way
    outbound_price, outbound_details = _search_flight(
        origin, destination, out_date, adults, children,
        trip_type=1 if ret_date else 2, api_key=api_key
    )

    if outbound_price is None:
        return _error_snap(f"Keine Google Flights: {origin}→{destination} am {out_date}")

    total = outbound_price
    return_details = None

    if ret_date:
        return_price, return_details = _search_flight(
            destination, origin, ret_date, adults, children,
            trip_type=2, api_key=api_key  # one-way for return leg
        )
        if return_price:
            total += return_price

    total = round(total, 2)
    logger.info(f"✅ [GF] {outbound_details.get('airline','?')} | {outbound_details.get('departure_time','?')} → {outbound_details.get('arrival_time','?')} | {total} EUR")

    return {"status": "ok", "snapshot": {
        "fetched_at":      datetime.utcnow().isoformat(),
        "flight_price":    round(total, 2),
        "baggage_price":   0.0,
        "seat_price":      0.0,
        "total_price":     total,
        "outbound_flight": outbound_details.get("flight_number", ""),
        "return_flight":   return_details.get("flight_number", "") if return_details else None,
        "airline":         outbound_details.get("airline", ""),
        "departure_time":  outbound_details.get("departure_time", ""),
        "arrival_time":    outbound_details.get("arrival_time", ""),
        "duration_min":    outbound_details.get("duration_min", 0),
        "currency":        "EUR",
        "baggage_fallback": False,
        "status":          "ok",
        "source":          "google_flights",
    }}


def _search_flight(origin, destination, date, adults, children, trip_type, api_key):
    params = {
        "engine":        "google_flights",
        "departure_id":  origin,
        "arrival_id":    destination,
        "outbound_date": date,
        "currency":      "EUR",
        "hl":            "de",
        "adults":        adults,
        "children":      children,
        "type":          trip_type,
        "api_key":       api_key,
    }

    try:
        resp = requests.get(SERPAPI_BASE, params=params, timeout=20)
        logger.info(f"[GF] SerpAPI {resp.status_code}")
        if resp.status_code == 401:
            logger.error("[GF] Ungültiger API Key")
            return None, {}
        if resp.status_code == 429:
            logger.error("[GF] Rate Limit")
            return None, {}
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"[GF] Request Fehler: {e}")
        return None, {}

    all_flights = data.get("best_flights", []) + data.get("other_flights", [])
    if not all_flights:
        logger.warning(f"[GF] Keine Flüge für {origin}→{destination}")
        return None, {}

    best = None
    best_price = float("inf")

    for fg in all_flights:
        price = fg.get("price")
        if not price or price >= best_price:
            continue
        best_price = price
        legs = fg.get("flights", [{}])
        first_leg = legs[0] if legs else {}
        last_leg  = legs[-1] if legs else {}

        # Departure/arrival aus ersten und letzten Leg
        dep_airport = first_leg.get("departure_airport", {})
        arr_airport = last_leg.get("arrival_airport", {})

        best = {
            "price":          price,
            "flight_number":  first_leg.get("flight_number", ""),
            "airline":        first_leg.get("airline", ""),
            "departure_time": dep_airport.get("time", ""),
            "arrival_time":   arr_airport.get("time", ""),
            "duration_min":   fg.get("total_duration", 0),
        }

    if not best:
        return None, {}
    return best["price"], best


def _error_snap(msg):
    logger.error(f"[GF] {msg}")
    return {"status": "error", "snapshot": {
        "status": "error", "error_message": msg,
        "fetched_at": datetime.utcnow().isoformat(),
    }}
