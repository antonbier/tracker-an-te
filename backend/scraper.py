"""
Ryanair API Scraper
"""

import requests
import random
import time
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

BAGGAGE_FALLBACK = {
    "10kg": 22.99,
    "20kg": 34.99,
    "23kg": 44.99,
}


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://www.ryanair.com",
        "Referer": "https://www.ryanair.com/de/de/buchen/fluge-finden",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Connection": "keep-alive",
    })
    return s


def fetch_flights(tracker: dict) -> dict:
    """Hauptfunktion: Flugpreis + Gepäck abrufen."""
    session = _make_session()
    origin      = tracker["origin"]
    destination = tracker["destination"]
    out_date    = tracker["outbound_date"]
    ret_date    = tracker.get("return_date")
    adults      = tracker.get("adults", 1)
    children    = tracker.get("children", 0)
    baggage     = tracker.get("baggage", [])

    logger.info(f"Fetching: {origin}→{destination} {out_date} | adults={adults}")

    url = "https://www.ryanair.com/api/booking/v4/en-gb/availability"
    params = {
        "ADT":                      adults,
        "CHD":                      children,
        "DateOut":                  out_date,
        "DateIn":                   ret_date or "",
        "Destination":              destination,
        "FlexDaysBeforeOut":        0,
        "FlexDaysAfterOut":         0,
        "FlexDaysBeforeIn":         0,
        "FlexDaysAfterIn":          0,
        "Origin":                   origin,
        "RoundTrip":                "true" if ret_date else "false",
        "ToUs":                     "AGREED",
        "IncludeConnectingFlights": "false",
    }

    try:
        resp = session.get(url, params=params, timeout=20)
        logger.info(f"Ryanair API Status: {resp.status_code}")
    except requests.RequestException as e:
        logger.error(f"Request failed: {traceback.format_exc()}")
        return {
            "status": "error",
            "snapshot": {
                "status": "error",
                "error_message": f"Request fehlgeschlagen: {str(e)}",
                "fetched_at": datetime.utcnow().isoformat(),
            }
        }

    if resp.status_code == 403:
        return {
            "status": "blocked",
            "snapshot": {
                "status": "blocked",
                "error_message": "Ryanair hat die Anfrage blockiert (403)",
                "fetched_at": datetime.utcnow().isoformat(),
            }
        }

    if not resp.ok:
        logger.error(f"API error {resp.status_code}: {resp.text[:500]}")
        return {
            "status": "error",
            "snapshot": {
                "status": "error",
                "error_message": f"API Fehler {resp.status_code}: {resp.text[:200]}",
                "fetched_at": datetime.utcnow().isoformat(),
            }
        }

    try:
        data = resp.json()
    except Exception as e:
        logger.error(f"JSON parse error: {resp.text[:300]}")
        return {
            "status": "error",
            "snapshot": {
                "status": "error",
                "error_message": f"JSON Parse Fehler: {str(e)}",
                "fetched_at": datetime.utcnow().isoformat(),
            }
        }

    currency = data.get("currency", "EUR")
    outbound = _cheapest_flight(data, origin, destination)
    inbound  = _cheapest_flight(data, destination, origin) if ret_date else None

    if not outbound:
        return {
            "status": "no_flights",
            "snapshot": {
                "status": "error",
                "error_message": f"Keine Flüge gefunden für {origin}→{destination} am {out_date}",
                "fetched_at": datetime.utcnow().isoformat(),
            }
        }

    ticket_total = outbound["price"] * adults
    if inbound:
        ticket_total += inbound["price"] * adults

    # Gepäck via Fallback-Preise (sicher, kein extra API-Call der crashen könnte)
    baggage_cost = sum(
        BAGGAGE_FALLBACK.get(b["type"], 0) * (adults if b.get("per_person") else 1)
        for b in baggage
    )

    total = round(ticket_total + baggage_cost, 2)

    snapshot = {
        "fetched_at":       datetime.utcnow().isoformat(),
        "flight_price":     round(ticket_total, 2),
        "baggage_price":    round(baggage_cost, 2),
        "total_price":      total,
        "outbound_flight":  outbound["flight_number"],
        "return_flight":    inbound["flight_number"] if inbound else None,
        "currency":         currency,
        "baggage_fallback": True,
        "status":           "ok",
    }

    logger.info(f"✅ Preis: {total} {currency}")
    return {"status": "ok", "snapshot": snapshot}


def _cheapest_flight(data: dict, orig: str, dest: str) -> dict | None:
    best = None
    best_price = float("inf")

    for trip in data.get("trips", []):
        if trip.get("origin") != orig or trip.get("destination") != dest:
            continue
        for date_entry in trip.get("dates", []):
            for flight in date_entry.get("flights", []):
                if flight.get("faresLeft", 0) == 0:
                    continue
                fares = flight.get("regularFare", {}).get("fares", [])
                if not fares:
                    continue
                price = min(f.get("amount", 9999) for f in fares)
                if price < best_price:
                    best_price = price
                    best = {
                        "flight_number": flight.get("flightNumber", ""),
                        "price":         price,
                        "fares_left":    flight.get("faresLeft", 0),
                    }
    return best
