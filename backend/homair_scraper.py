"""
WanderSuite — Homair Camping Scraper
Scrapes prices from homair.com directly via requests.
Homair has less aggressive bot detection than Ryanair.
Falls back to HTML price extraction if JSON API is unavailable.
"""

import requests
import random
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# Homair Regions → interne Region-IDs (approximiert, anpassbar)
HOMAIR_REGIONS = {
    "cote-d-azur":  "france-cote-azur",
    "kroatien":     "croatia",
    "toskana":      "italy-tuscany",
    "katalonien":   "spain-catalonia",
    "languedoc":    "france-languedoc",
    "provence":     "france-provence",
    "venetien":     "italy-veneto",
}

HOMAIR_ACCOMMODATION_TYPES = {
    "mobilheim-standard":  "mobile-home-standard",
    "mobilheim-premium":   "mobile-home-premium",
    "chalet":              "chalet",
    "stellplatz":          "pitch",
}


def fetch_homair(tracker: dict) -> dict:
    """
    Homair Preise scrapen.
    tracker: {region, accommodation_type, checkin, checkout, adults, children}
    """
    region   = tracker.get("region", "cote-d-azur")
    acc_type = tracker.get("accommodation_type", "mobilheim-standard")
    checkin  = tracker.get("checkin_date")
    checkout = tracker.get("checkout_date")
    adults   = tracker.get("adults", 2)
    children = tracker.get("children", 0)

    logger.info(f"[Homair] Fetching: {region} | {acc_type} | {checkin}→{checkout}")

    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Referer": "https://www.homair.com/",
    })

    # Homair Search API (inoffizielle JSON-Endpunkte)
    url = "https://www.homair.com/api/search/accommodations"
    params = {
        "region":       HOMAIR_REGIONS.get(region, region),
        "type":         HOMAIR_ACCOMMODATION_TYPES.get(acc_type, acc_type),
        "arrival":      checkin,
        "departure":    checkout,
        "adults":       adults,
        "children":     children,
        "currency":     "EUR",
        "lang":         "de",
    }

    try:
        resp = session.get(url, params=params, timeout=20)
        logger.info(f"[Homair] Status: {resp.status_code}")

        if resp.status_code == 404:
            # Kein JSON-Endpunkt — HTML scrapen als Fallback
            return _scrape_homair_html(session, tracker)

        if not resp.ok:
            return _error_snap(f"Homair API Fehler {resp.status_code}")

        data = resp.json()
        return _parse_homair_response(data, tracker)

    except requests.RequestException as e:
        logger.error(f"[Homair] Request Fehler: {e}")
        # Fallback zu HTML-Scraping
        return _scrape_homair_html(session, tracker)


def _scrape_homair_html(session: requests.Session, tracker: dict) -> dict:
    """
    HTML-Scraping Fallback für Homair.
    Parst Preise direkt aus der Suchergebnisseite.
    """
    region   = tracker.get("region", "cote-d-azur")
    checkin  = tracker.get("checkin_date", "")
    checkout = tracker.get("checkout_date", "")
    adults   = tracker.get("adults", 2)

    url = f"https://www.homair.com/de/camping/{region}/suche/"
    params = {
        "arrival":   checkin,
        "departure": checkout,
        "adults":    adults,
    }

    try:
        resp = session.get(url, params=params, timeout=20)
        if not resp.ok:
            return _error_snap(f"Homair HTML Fehler {resp.status_code}: {url}")

        # Preise aus HTML extrahieren (€ XX,XX oder € XX.XX Pattern)
        prices = re.findall(r'(?:€|EUR)\s*(\d+[.,]\d{2})', resp.text)
        numeric_prices = []
        for p in prices:
            try:
                numeric_prices.append(float(p.replace(',', '.')))
            except ValueError:
                continue

        if not numeric_prices:
            return _error_snap("Keine Preise auf Homair gefunden — Seitenstruktur möglicherweise geändert")

        min_price = min(numeric_prices)
        logger.info(f"[Homair] HTML scraping: {len(numeric_prices)} Preise, Minimum: {min_price} €")

        return {"status": "ok", "snapshot": {
            "fetched_at":   datetime.utcnow().isoformat(),
            "total_price":  round(min_price, 2),
            "price_source": "html_scrape",
            "currency":     "EUR",
            "status":       "ok",
            "note":         f"Günstigster Preis aus {len(numeric_prices)} Ergebnissen",
        }}

    except requests.RequestException as e:
        return _error_snap(f"Homair HTML Fehler: {str(e)}")


def _parse_homair_response(data: dict, tracker: dict) -> dict:
    """JSON-API Response parsen."""
    items = data.get("results", data.get("accommodations", []))
    if not items:
        return _error_snap("Keine Homair-Unterkünfte gefunden")

    prices = [float(item.get("price", 0)) for item in items if item.get("price")]
    if not prices:
        return _error_snap("Keine Preise in Homair-Response")

    min_price = min(prices)
    return {"status": "ok", "snapshot": {
        "fetched_at":  datetime.utcnow().isoformat(),
        "total_price": round(min_price, 2),
        "currency":    "EUR",
        "status":      "ok",
    }}


def _error_snap(msg: str) -> dict:
    logger.error(f"[Homair] {msg}")
    return {"status": "error", "snapshot": {
        "status": "error",
        "error_message": msg,
        "fetched_at": datetime.utcnow().isoformat(),
    }}
