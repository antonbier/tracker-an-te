"""
WanderSuite — Booking.com / Trivago Scraper
Uses SerpAPI Google Hotels endpoint for accommodation prices.
Same API key as Google Flights (SerpAPI).
Free plan: 100 searches/month shared with Google Flights.
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"


def fetch_booking(tracker: dict, api_key: str) -> dict:
    """
    Unterkunftspreise via SerpAPI Google Hotels abrufen.
    tracker: {destination, checkin_date, checkout_date, adults, rooms}
    """
    if not api_key:
        return _error_snap("SerpAPI Key nicht konfiguriert")

    destination = tracker.get("destination", "")
    checkin     = tracker.get("checkin_date", "")
    checkout    = tracker.get("checkout_date", "")
    adults      = tracker.get("adults", 2)
    rooms       = tracker.get("rooms", 1)

    if not destination or not checkin or not checkout:
        return _error_snap("Destination, Check-in und Check-out sind Pflichtfelder")

    logger.info(f"[Booking] Fetching: {destination} | {checkin}→{checkout} | {adults} Erw., {rooms} Zimmer")

    params = {
        "engine":       "google_hotels",
        "q":            destination,
        "check_in_date":  checkin,
        "check_out_date": checkout,
        "adults":       adults,
        "rooms":        rooms,
        "currency":     "EUR",
        "hl":           "de",
        "gl":           "de",
        "api_key":      api_key,
    }

    try:
        resp = requests.get(SERPAPI_BASE, params=params, timeout=25)
        logger.info(f"[Booking] SerpAPI status: {resp.status_code}")

        if resp.status_code == 401:
            return _error_snap("SerpAPI: Ungültiger API Key")
        if resp.status_code == 429:
            return _error_snap("SerpAPI: Rate Limit erreicht")

        resp.raise_for_status()
        data = resp.json()

    except requests.RequestException as e:
        return _error_snap(f"SerpAPI Request Fehler: {str(e)}")

    # Hotels aus Response extrahieren
    properties = data.get("properties", [])
    if not properties:
        return _error_snap(f"Keine Hotels für '{destination}' gefunden")

    # Günstigsten Preis finden
    best = None
    best_price = float("inf")

    for prop in properties:
        # SerpAPI gibt Preise in verschiedenen Formaten zurück
        rate_info = prop.get("rate_per_night", {})
        price_str = rate_info.get("lowest", rate_info.get("extracted_lowest", 0))

        if isinstance(price_str, str):
            # Entferne Währungssymbole und parse
            import re
            nums = re.findall(r'[\d.]+', price_str.replace(',', '.'))
            price = float(nums[0]) if nums else 0
        else:
            price = float(price_str or 0)

        if price > 0 and price < best_price:
            best_price = price
            best = {
                "name":        prop.get("name", ""),
                "price":       price,
                "rating":      prop.get("overall_rating", 0),
                "type":        prop.get("type", ""),
            }

    if not best:
        return _error_snap("Keine Preise in SerpAPI Response gefunden")

    logger.info(f"✅ [Booking] Günstigste Option: {best['name']} — {best['price']} €/Nacht")

    return {"status": "ok", "snapshot": {
        "fetched_at":    datetime.utcnow().isoformat(),
        "total_price":   round(best["price"], 2),
        "currency":      "EUR",
        "hotel_name":    best["name"],
        "hotel_rating":  best["rating"],
        "price_per_night": round(best["price"], 2),
        "status":        "ok",
        "source":        "google_hotels_serpapi",
    }}


def _error_snap(msg: str) -> dict:
    logger.error(f"[Booking] {msg}")
    return {"status": "error", "snapshot": {
        "status": "error",
        "error_message": msg,
        "fetched_at": datetime.utcnow().isoformat(),
    }}
