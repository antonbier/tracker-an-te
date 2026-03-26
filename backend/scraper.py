"""
Ryanair API Scraper
- Availability API v4 (Flugpreise)
- Catalog API (dynamische Gepäckpreise)
- Anti-Bot: UA-Rotation, Random Delays, Retry mit Backoff
"""

import requests
import random
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── Anti-Bot Config ─────────────────────────────────────────

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

ACCEPT_LANGUAGES = [
    "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-GB,en;q=0.9",
    "it-IT,it;q=0.9,en;q=0.8",
    "de-AT,de;q=0.9,en;q=0.8",
]

# Fallback-Gepäckpreise (Schätzwerte für Europa, Hochsaison)
BAGGAGE_FALLBACK = {
    "10kg": 22.99,
    "20kg": 34.99,
    "23kg": 44.99,
}


def _make_session() -> requests.Session:
    """Session mit zufälligem Browser-Fingerprint."""
    s = requests.Session()
    ua = random.choice(USER_AGENTS)
    lang = random.choice(ACCEPT_LANGUAGES)
    s.headers.update({
        "User-Agent": ua,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": lang,
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://www.ryanair.com",
        "Referer": "https://www.ryanair.com/de/de/buchen/fluge-finden",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    })
    return s


def _delay(min_s=2.0, max_s=5.5):
    t = random.uniform(min_s, max_s)
    logger.debug(f"Delay {t:.1f}s")
    time.sleep(t)


def _get_with_retry(session, url, params=None, max_retries=3) -> requests.Response | None:
    """GET mit exponentiellem Backoff bei 429/503."""
    for attempt in range(max_retries):
        try:
            resp = session.get(url, params=params, timeout=20)

            if resp.status_code == 200:
                return resp

            if resp.status_code == 403:
                logger.warning(f"403 Blocked auf {url} (Versuch {attempt+1})")
                if attempt < max_retries - 1:
                    wait = random.uniform(10, 25) * (attempt + 1)
                    logger.info(f"Warte {wait:.0f}s vor Retry...")
                    time.sleep(wait)
                continue

            if resp.status_code in (429, 503):
                wait = (2 ** attempt) * random.uniform(5, 10)
                logger.warning(f"Rate-limited ({resp.status_code}). Warte {wait:.0f}s")
                time.sleep(wait)
                continue

            if resp.status_code == 400:
                logger.error(f"400 Bad Request: {resp.text[:300]}")
                return None

            resp.raise_for_status()

        except requests.Timeout:
            logger.warning(f"Timeout (Versuch {attempt+1})")
            time.sleep(5 * (attempt + 1))
        except requests.RequestException as e:
            logger.error(f"Request-Fehler: {e}")
            return None

    logger.error(f"Alle {max_retries} Versuche fehlgeschlagen für {url}")
    return None


# ─── Availability API ────────────────────────────────────────

def fetch_flights(tracker: dict) -> dict:
    """
    Hauptfunktion: Gibt dict mit Ergebnis zurück.
    Format: {"status": "ok"|"blocked"|"error", "snapshot": {...}}
    """
    session = _make_session()
    origin      = tracker["origin"]
    destination = tracker["destination"]
    out_date    = tracker["outbound_date"]
    ret_date    = tracker.get("return_date")
    adults      = tracker.get("adults", 1)
    children    = tracker.get("children", 0)
    baggage     = tracker.get("baggage", [])

    # ── Schritt 1: Flugverfügbarkeit ──
    url = "https://www.ryanair.com/api/booking/v4/en-gb/availability"
    params = {
        "ADT":                    adults,
        "CHD":                    children,
        "DateOut":                out_date,
        "DateIn":                 ret_date or "",
        "Destination":            destination,
        "FlexDaysBeforeOut":      0,
        "FlexDaysAfterOut":       0,
        "FlexDaysBeforeIn":       0,
        "FlexDaysAfterIn":        0,
        "Origin":                 origin,
        "RoundTrip":              "true" if ret_date else "false",
        "ToUs":                   "AGREED",
        "IncludeConnectingFlights": "false",
    }

    logger.info(f"Fetching: {origin}→{destination} {out_date} | adults={adults}")
    resp = _get_with_retry(session, url, params)

    if resp is None:
        return {
            "status": "blocked",
            "snapshot": {
                "status": "blocked",
                "error_message": "Ryanair API nicht erreichbar (403/Timeout nach 3 Versuchen)",
                "fetched_at": datetime.utcnow().isoformat(),
            }
        }

    data = resp.json()
    currency = data.get("currency", "EUR")

    # Flüge extrahieren
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

    # ── Schritt 2: Gepäckpreise ──
    _delay(2.0, 4.5)

    baggage_cost, baggage_fallback = _get_baggage_cost(
        session, origin, destination,
        outbound["flight_number"], out_date,
        adults, baggage, currency
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
        "baggage_fallback": baggage_fallback,
        "status":           "ok",
        "raw":              {"outbound": outbound, "inbound": inbound},
    }

    return {"status": "ok", "snapshot": snapshot}


def _cheapest_flight(data: dict, orig: str, dest: str) -> dict | None:
    """Günstigsten Flug in gegebener Richtung aus API-Daten extrahieren."""
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
                        "time":          flight.get("time", []),
                    }
    return best


# ─── Gepäck API ──────────────────────────────────────────────

def _get_baggage_cost(
    session, origin, destination,
    flight_no, date, adults, baggage_config, currency
) -> tuple[float, bool]:
    """Gibt (Gesamtkosten, fallback_bool) zurück."""
    if not baggage_config:
        return 0.0, False

    # Versuche dynamische Preise über Catalog API
    prices = _fetch_baggage_prices_api(session, origin, destination, flight_no, date, adults)

    if prices is None:
        # Fallback: pauschale Schätzpreise
        logger.warning("Gepäck-API fehlgeschlagen — nutze Fallback-Preise")
        total = sum(
            BAGGAGE_FALLBACK.get(b["type"], 0) * (adults if b.get("per_person") else 1)
            for b in baggage_config
        )
        return total, True

    # Echte API-Preise
    total = _calculate_bag_cost(prices, baggage_config, adults)
    return total, False


def _fetch_baggage_prices_api(
    session, origin, destination, flight_no, date, adults
) -> dict | None:
    """
    Ryanair Extras/Catalog API für Gepäckpreise.
    Gibt {type_key: price_per_bag} zurück oder None bei Fehler.
    """
    # Endpunkt 1: Booking extras
    url = "https://www.ryanair.com/api/booking/v4/en-gb/extras/prices"
    params = {
        "flightNumber": flight_no,
        "departureDate": date,
        "ADT": adults,
        "CHD": 0,
        "origin": origin,
        "destination": destination,
    }

    resp = _get_with_retry(session, url, params)

    if resp and resp.status_code == 200:
        return _parse_baggage_response(resp.json())

    # Endpunkt 2: Catalog API (Fallback-Endpunkt)
    url2 = f"https://www.ryanair.com/api/catalog/en-gb/pricing/extras"
    resp2 = _get_with_retry(session, url2, params)

    if resp2 and resp2.status_code == 200:
        return _parse_baggage_response(resp2.json())

    return None


def _parse_baggage_response(data) -> dict | None:
    """Normalisiert verschiedene Gepäck-API-Response-Formate."""
    if not data:
        return None

    result = {}
    items = data if isinstance(data, list) else data.get("extras", data.get("items", []))

    for item in items:
        code = str(item.get("code", item.get("type", ""))).lower()
        name = str(item.get("name", "")).lower()
        price_obj = item.get("price", item.get("amount", {}))

        if isinstance(price_obj, dict):
            price = float(price_obj.get("amount", price_obj.get("value", 0)))
        else:
            price = float(price_obj or 0)

        if price <= 0:
            continue

        if "10" in code or "10" in name:
            result["10kg"] = price
        elif "20" in code or "20" in name:
            result["20kg"] = price
        elif "23" in code or "23" in name:
            result["23kg"] = price

    return result if result else None


def _calculate_bag_cost(prices: dict, baggage_config: list, adults: int) -> float:
    total = 0.0
    for bag in baggage_config:
        unit = prices.get(bag["type"], BAGGAGE_FALLBACK.get(bag["type"], 0))
        qty  = adults if bag.get("per_person") else 1
        total += unit * qty
    return total
