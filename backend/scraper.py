"""
WanderSuite v0.1 — Ryanair API Scraper
Anti-Bot: UA-Rotation, Cookie-Prefetch, Retry-Logik.
Gepäck: Fallback-Preise (dynamische API in v0.2).
Sitzplatz: Pauschale aus Tracker-Konfiguration.
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

# Fallback-Gepäckpreise (Europa, Hochsaison — dynamische Preise in v0.2)
BAGGAGE_FALLBACK = {
    "10kg": 22.99,
    "20kg": 34.99,
    "23kg": 44.99,
}


def _make_session() -> requests.Session:
    """Session mit zufälligem Browser-Fingerprint aufbauen."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://www.ryanair.com",
        "Referer": "https://www.ryanair.com/de/de/buchen/fluge-finden",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Connection": "keep-alive",
    })
    return s


def fetch_flights(tracker: dict) -> dict:
    """
    Hauptfunktion: Flugpreis + Gepäck + Sitzplatz abrufen.
    Gibt dict mit {status, snapshot} zurück.
    """
    session = _make_session()
    origin      = tracker["origin"]
    destination = tracker["destination"]
    out_date    = tracker["outbound_date"]
    ret_date    = tracker.get("return_date")
    adults      = tracker.get("adults", 1)
    baggage     = tracker.get("baggage", [])
    seat_cost   = float(tracker.get("seat_cost", 0.0))

    logger.info(f"Fetching: {origin}→{destination} {out_date} | adults={adults} | seat={seat_cost}€")

    # Cookie-Prefetch (Anti-Bot)
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
        logger.info(f"Status: {resp.status_code} | Content-Type: {resp.headers.get('content-type','?')}")
    except requests.RequestException as e:
        return _error_snap(f"Request fehlgeschlagen: {str(e)}")

    if resp.status_code == 403:
        return _error_snap("Ryanair blockiert (403)", "blocked")

    if not resp.ok:
        return _error_snap(f"API Fehler {resp.status_code}: {resp.text[:200]}")

    # JSON parsen (mit UTF-8 Fallback)
    try:
        data = resp.json()
    except Exception:
        try:
            import json
            data = json.loads(resp.content.decode("utf-8"))
        except Exception as e2:
            return _error_snap(f"JSON Parse Fehler: {str(e2)}")

    currency = data.get("currency", "EUR")
    outbound = _cheapest_flight(data, origin, destination)
    inbound  = _cheapest_flight(data, destination, origin) if ret_date else None

    if not outbound:
        return _error_snap(f"Keine Flüge: {origin}→{destination} am {out_date}")

    # Ticketpreis (alle Passagiere)
    ticket_total = outbound["price"] * adults
    if inbound:
        ticket_total += inbound["price"] * adults

    # Gepäckkosten (Fallback-Preise)
    baggage_cost = sum(
        BAGGAGE_FALLBACK.get(b["type"], 0) * (adults if b.get("per_person") else 1)
        for b in baggage
    )

    # Sitzplatzkosten: Pauschale × Passagiere × Flüge
    num_flights = 2 if ret_date else 1
    seat_total = seat_cost * adults * num_flights

    total = round(ticket_total + baggage_cost + seat_total, 2)
    logger.info(f"✅ Tickets:{ticket_total:.2f} + Gepäck:{baggage_cost:.2f} + Sitz:{seat_total:.2f} = {total} {currency}")

    return {"status": "ok", "snapshot": {
        "fetched_at":       datetime.utcnow().isoformat(),
        "flight_price":     round(ticket_total, 2),
        "baggage_price":    round(baggage_cost, 2),
        "seat_price":       round(seat_total, 2),
        "total_price":      total,
        "outbound_flight":  outbound["flight_number"],
        "return_flight":    inbound["flight_number"] if inbound else None,
        "departure_time":   outbound.get("departure_time"),
        "arrival_time":     outbound.get("arrival_time"),
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


def _parse_local_time(raw) -> str | None:
    """
    Extrahiert sauber HH:MM aus verschiedenen Zeitformaten.
    Behandelt IMMER als lokale Ortszeit — nie UTC-Konvertierung!

    Unterstützte Formate:
      - "06:15"                      → "06:15"  (plain HH:MM)
      - "06:15:00"                   → "06:15"  (HH:MM:SS)
      - "2026-05-05T06:15:00.000Z"   → "06:15"  (ISO UTC — Zeit-Anteil als lokal behandeln)
      - "2026-05-05T06:15:00"        → "06:15"  (ISO lokal)
      - "2026-05-05 06:15"           → "06:15"  (SerpAPI-Format)
    """
    if not raw:
        return None
    s = str(raw).strip()
    # ISO mit T-Trennzeichen: alles nach T nehmen, dann [:5]
    if "T" in s:
        return s.split("T")[1][:5]
    # SerpAPI-Format: "YYYY-MM-DD HH:MM"
    if len(s) > 10 and " " in s:
        return s.split(" ")[1][:5]
    # Plain HH:MM oder HH:MM:SS
    return s[:5] if len(s) >= 5 else None


def _fmt_flight_number(raw: str) -> str:
    """
    Normalisiert Flugnummer auf Format "XX 1234".
    Ryanair: "FR6125" → "FR 6125"
    Bereits korrekt: "FR 6125" → "FR 6125"
    """
    if not raw:
        return ""
    raw = str(raw).strip()
    # Schon korrekt formatiert (enthält Leerzeichen)
    if " " in raw:
        return raw
    # Suche Übergang Buchstaben → Ziffern
    import re
    m = re.match(r"^([A-Z]{1,3})([0-9].*)$", raw)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return raw


def _cheapest_flight(data: dict, orig: str, dest: str) -> dict | None:
    """Günstigsten verfügbaren Flug inkl. Zeiten + Flugnummer extrahieren."""
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
                    # Extract times from first segment
                    # Use seg.time (LOCAL airport time), NOT timeUTC
                    seg        = flight.get("segments", [{}])[0]
                    local_time = seg.get("time") or []       # [dep_local, arr_local]
                    utc_time   = seg.get("timeUTC") or []    # fallback only
                    dep_time   = _parse_local_time(local_time[0] if local_time else None) \
                                 or _parse_local_time(utc_time[0] if utc_time else None)
                    arr_time   = _parse_local_time(local_time[1] if len(local_time) > 1 else None) \
                                 or _parse_local_time(utc_time[1] if len(utc_time) > 1 else None)
                    flight_num = _fmt_flight_number(
                                     flight.get("flightNumber")
                                     or seg.get("flightNumber")
                                     or ""
                                 )
                    best = {
                        "flight_number":  flight_num,
                        "price":          price,
                        "departure_time": dep_time,
                        "arrival_time":   arr_time,
                    }
    return best


