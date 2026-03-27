"""
WanderSuite v0.5 — Google Flights Scraper
Nutzt SerpAPI (serpapi.com) — keine Cloudflare-Probleme,
kostenlos bis 100 Suchen/Monat im Free Plan.
Docs: https://serpapi.com/google-flights-api
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"


def fetch_google_flights(tracker: dict, api_key: str) -> dict:
    """
    Günstigsten Flug via Google Flights (SerpAPI) abrufen.
    tracker: {origin, destination, outbound_date, return_date, adults, children}
    """
    if not api_key:
        return _error_snap("SerpAPI Key nicht konfiguriert")

    origin      = tracker["origin"]
    destination = tracker["destination"]
    out_date    = tracker["outbound_date"]
    ret_date    = tracker.get("return_date")
    adults      = tracker.get("adults", 1)
    children    = tracker.get("children", 0)

    logger.info(f"[GF] Fetching: {origin}→{destination} {out_date} | adults={adults}")

    # Outbound flight
    outbound_price, outbound_details = _search_flight(
        origin, destination, out_date, adults, children,
        trip_type=2 if ret_date else 1,
        api_key=api_key
    )

    if outbound_price is None:
        return _error_snap(f"Keine Google Flights gefunden: {origin}→{destination}")

    total = outbound_price

    # Return flight (separate search for one-way legs)
    return_details = None
    if ret_date:
        return_price, return_details = _search_flight(
            destination, origin, ret_date, adults, children,
            trip_type=2, api_key=api_key
        )
        if return_price:
            total += return_price

    total = round(total, 2)
    logger.info(f"✅ [GF] Total: {total} EUR")

    return {"status": "ok", "snapshot": {
        "fetched_at":      datetime.utcnow().isoformat(),
        "flight_price":    round(total, 2),
        "baggage_price":   0.0,
        "seat_price":      0.0,
        "total_price":     total,
        "outbound_flight": outbound_details.get("flight_number", ""),
        "return_flight":   return_details.get("flight_number", "") if return_details else None,
        "currency":        "EUR",
        "baggage_fallback": False,
        "status":          "ok",
        "source":          "google_flights",
    }}


def _search_flight(
    origin: str, destination: str, date: str,
    adults: int, children: int, trip_type: int,
    api_key: str
) -> tuple[float | None, dict]:
    """
    Einzelne Flugsuche via SerpAPI Google Flights.
    Gibt (günstigster_preis, details_dict) zurück.
    trip_type: 1=Einweg, 2=Hin+Rück
    """
    params = {
        "engine":            "google_flights",
        "departure_id":      origin,
        "arrival_id":        destination,
        "outbound_date":     date,
        "currency":          "EUR",
        "hl":                "de",
        "adults":            adults,
        "children":          children,
        "type":              trip_type,
        "api_key":           api_key,
    }

    try:
        resp = requests.get(SERPAPI_BASE, params=params, timeout=20)
        logger.info(f"[GF] SerpAPI status: {resp.status_code}")

        if resp.status_code == 401:
            logger.error("[GF] SerpAPI: Ungültiger API Key")
            return None, {}

        if resp.status_code == 429:
            logger.error("[GF] SerpAPI: Rate Limit erreicht")
            return None, {}

        resp.raise_for_status()
        data = resp.json()

    except requests.RequestException as e:
        logger.error(f"[GF] SerpAPI Request Fehler: {e}")
        return None, {}

    # SerpAPI gibt Flüge unter best_flights oder other_flights zurück
    all_flights = data.get("best_flights", []) + data.get("other_flights", [])

    if not all_flights:
        logger.warning(f"[GF] Keine Flüge in SerpAPI Response für {origin}→{destination}")
        return None, {}

    # Günstigsten Flug finden
    best = None
    best_price = float("inf")

    for flight_group in all_flights:
        price = flight_group.get("price")
        if price and price < best_price:
            best_price = price
            # Erste Flugnummer aus dem ersten Leg
            flights = flight_group.get("flights", [{}])
            best = {
                "price": price,
                "flight_number": flights[0].get("flight_number", ""),
                "airline": flights[0].get("airline", ""),
                "duration": flight_group.get("total_duration", 0),
            }

    if not best:
        return None, {}

    return best["price"], best


def _error_snap(msg: str) -> dict:
    logger.error(f"[GF] {msg}")
    return {"status": "error", "snapshot": {
        "status": "error",
        "error_message": msg,
        "fetched_at": datetime.utcnow().isoformat(),
    }}
