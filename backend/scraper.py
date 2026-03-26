"""
Ryanair API Scraper
"""

import requests
import random
import time
import logging
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
        # Kein Accept-Encoding — requests handled Dekompression automatisch
        "Origin": "https://www.ryanair.com",
        "Referer": "https://www.ryanair.com/de/de/buchen/fluge-finden",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Connection": "keep-alive",
    })
    return s


def fetch_flights(tracker: dict) -> dict:
    session = _make_session()
    origin      = tracker["origin"]
    destination = tracker["destination"]
    out_date    = tracker["outbound_date"]
    ret_date    = tracker.get("return_date")
    adults      = tracker.get("adults", 1)
    baggage     = tracker.get("baggage", [])

    logger.info(f"Fetching: {origin}→{destination} {out_date} | adults={adults}")

    # Cookies holen
    try:
        session.get("https://www.ryanair.com/de/de", timeout=10)
        time.sleep(random.uniform(1.5, 3.0))
    except Exception:
        pass

    url = "https://www.ryanair.com/api/booking/v4/en-gb/availability"
    params = {
        "ADT":                      adults,
        "CHD":                      tracker.get("children", 0),
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
        logger.info(f"Status: {resp.status_code} | Encoding: {resp.encoding} | Content-Type: {resp.headers.get('content-type','?')}")
    except requests.RequestException as e:
        return _error_snap(f"Request fehlgeschlagen: {str(e)}")

    if resp.status_code == 403:
        return _error_snap(f"Ryanair blockiert (403)", "blocked")

    if not resp.ok:
        return _error_snap(f"API Fehler {resp.status_code}: {resp.text[:300]}")

    try:
        data = resp.json()
    except Exception as e:
        # Fallback: manuell dekodieren
        try:
            import json
            data = json.loads(resp.content.decode("utf-8"))
        except Exception as e2:
            return _error_snap(f"JSON Parse Fehler: {str(e2)} | encoding={resp.encoding} | content-type={resp.headers.get('content-type')}")

    currency = data.get("currency", "EUR")
    outbound = _cheapest_flight(data, origin, destination)
    inbound  = _cheapest_flight(data, destination, origin) if ret_date else None

    if not outbound:
        return _error_snap(f"Keine Flüge: {origin}→{destination} am {out_date}")

    ticket_total = outbound["price"] * adults
    if inbound:
        ticket_total += inbound["price"] * adults

    baggage_cost = sum(
        BAGGAGE_FALLBACK.get(b["type"], 0) * (adults if b.get("per_person") else 1)
        for b in baggage
    )

    total = round(ticket_total + baggage_cost, 2)
    logger.info(f"✅ Preis: {total} {currency}")

    return {"status": "ok", "snapshot": {
        "fetched_at":       datetime.utcnow().isoformat(),
        "flight_price":     round(ticket_total, 2),
        "baggage_price":    round(baggage_cost, 2),
        "total_price":      total,
        "outbound_flight":  outbound["flight_number"],
        "return_flight":    inbound["flight_number"] if inbound else None,
        "currency":         currency,
        "baggage_fallback": True,
        "status":           "ok",
    }}


def _error_snap(msg: str, status: str = "error") -> dict:
    logger.error(f"Scraper: {msg}")
    return {"status": status, "snapshot": {
        "status": status,
        "error_message": msg,
        "fetched_at": datetime.utcnow().isoformat(),
    }}


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
                        "price": price,
                    }
    return best
