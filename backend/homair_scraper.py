"""
WanderSuite — Homair Camping Scraper
Uses SerpAPI Google Hotels to find Homair campsite prices.

Homair's website is a fully JS-rendered Nuxt.js app with no
scrapeable HTML and no public API. SerpAPI Google Hotels reliably
returns Homair pricing data.

Same API key as Booking/Google Flights (SerpAPI).
Free plan: 100 searches/month shared across all scrapers.
"""

import requests
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"


def fetch_homair(tracker: dict, api_key: str = "") -> dict:
    """
    Homair Campingpreise via SerpAPI Google Hotels abrufen.
    tracker: {region, accommodation_type, checkin_date, checkout_date, adults, children}
    api_key: SerpAPI Key (wird auch aus settings_manager geladen wenn leer)
    """
    if not api_key:
        try:
            from settings_manager import get_setting_value
            api_key = get_setting_value("serpapi_key") or ""
        except Exception:
            pass

    if not api_key:
        return _error_snap("SerpAPI Key nicht konfiguriert — in den Einstellungen eintragen")

    region   = tracker.get("region", "")
    acc_type = tracker.get("accommodation_type", "")
    checkin  = tracker.get("checkin_date", "")
    checkout = tracker.get("checkout_date", "")
    adults   = tracker.get("adults", 2)
    children = tracker.get("children", 0)

    if not checkin or not checkout:
        return _error_snap("Check-in und Check-out Datum sind Pflichtfelder")

    # Suchbegriff: "Homair [Region]" → findet Homair-Campingplätze auf Google Hotels
    query = f"Homair camping {region}".strip() if region else "Homair camping"
    total_guests = int(adults) + int(children)

    logger.info(f"[Homair] SerpAPI: '{query}' | {checkin}→{checkout} | {total_guests} Pers.")

    params = {
        "engine":         "google_hotels",
        "q":              query,
        "check_in_date":  checkin,
        "check_out_date": checkout,
        "adults":         max(1, int(adults)),
        "currency":       "EUR",
        "hl":             "de",
        "gl":             "de",
        "api_key":        api_key,
    }

    try:
        resp = requests.get(SERPAPI_BASE, params=params, timeout=25)
        logger.info(f"[Homair] SerpAPI status: {resp.status_code}")

        if resp.status_code == 401:
            return _error_snap("SerpAPI: Ungültiger API Key")
        if resp.status_code == 429:
            return _error_snap("SerpAPI: Rate Limit / Monatskontingent erschöpft")
        resp.raise_for_status()
        data = resp.json()

    except requests.RequestException as e:
        return _error_snap(f"SerpAPI Request Fehler: {str(e)}")

    properties = data.get("properties", [])
    if not properties:
        return _error_snap(f"Keine Homair-Campingplätze für '{region}' gefunden")

    # Günstigstes Homair-Ergebnis finden
    best = None
    best_price = float("inf")

    for prop in properties:
        name = prop.get("name", "").lower()
        # Nur Homair-Ergebnisse berücksichtigen
        if "homair" not in name and "hom air" not in name:
            continue

        rate_info = prop.get("rate_per_night") or prop.get("total_rate") or {}
        raw = (rate_info.get("extracted_lowest")
               or rate_info.get("extracted_before_taxes_fees")
               or rate_info.get("lowest")
               or rate_info.get("before_taxes_fees")
               or 0)
        if isinstance(raw, str):
            nums = re.findall(r'[\d]+(?:[.,][\d]+)?', raw.replace(",", "."))
            price = float(nums[0].replace(",", ".")) if nums else 0.0
        else:
            price = float(raw or 0)

        if price > 0 and price < best_price:
            best_price = price
            best = {
                "name":    prop.get("name", ""),
                "price":   price,
                "rating":  prop.get("overall_rating", 0),
            }

    # Falls kein Homair-Treffer: günstigstes Ergebnis aller Camping-Optionen nehmen
    if not best:
        logger.warning("[Homair] Kein explizites Homair-Ergebnis — nehme günstigstes Camping-Ergebnis")
        for prop in properties:
            rate_info2 = prop.get("rate_per_night") or prop.get("total_rate") or {}
            raw2 = (rate_info2.get("extracted_lowest")
                    or rate_info2.get("extracted_before_taxes_fees")
                    or rate_info2.get("lowest")
                    or 0)
            if isinstance(raw2, str):
                nums = re.findall(r'[\d]+(?:[.,][\d]+)?', raw2.replace(",", "."))
                price = float(nums[0].replace(",", ".")) if nums else 0.0
            else:
                price = float(raw2 or 0)
            if price > 0 and price < best_price:
                best_price = price
                best = {"name": prop.get("name", ""), "price": price, "rating": prop.get("overall_rating", 0)}

    if not best:
        return _error_snap("Keine Preise in SerpAPI Response gefunden")

    logger.info(f"✅ [Homair] {best['name']} — {best['price']} €/Nacht")

    return {"status": "ok", "snapshot": {
        "fetched_at":      datetime.utcnow().isoformat(),
        "total_price":     round(best["price"], 2),
        "price_per_night": round(best["price"], 2),
        "currency":        "EUR",
        "hotel_name":      best["name"],
        "hotel_rating":    best["rating"],
        "status":          "ok",
        "source":          "google_hotels_serpapi",
    }}


def _error_snap(msg: str) -> dict:
    logger.error(f"[Homair] {msg}")
    return {"status": "error", "snapshot": {
        "status": "error",
        "error_message": msg,
        "fetched_at": datetime.utcnow().isoformat(),
    }}
