"""
WanderSuite — search_shared.py
Gemeinsame Typen, Konstanten und Hilfsfunktionen für alle Search-Module.
Importiert von: search_flights.py, search_hotels.py, search_camping.py
"""

import logging
import re
from typing import Optional

import httpx
from pydantic import BaseModel, model_validator

logger = logging.getLogger(__name__)

TIMEOUT: float = 18.0  # seconds per provider

# ── Browser headers ────────────────────────────────────────────────────────

HEADERS_RYANAIR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8",
    "Origin": "https://www.ryanair.com",
    "Referer": "https://www.ryanair.com/de/de/buchen/fluge-finden",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

HEADERS_SERPAPI = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

SERPAPI_BASE = "https://serpapi.com/search"

# ── Helper functions ───────────────────────────────────────────────────────

def _calc_nights(checkin: str, checkout: str) -> int:
    """Return number of nights between checkin and checkout (YYYY-MM-DD)."""
    try:
        from datetime import date
        ci = date.fromisoformat(checkin)
        co = date.fromisoformat(checkout)
        return max((co - ci).days, 1)
    except Exception:
        return 1


def _extract_price(rate_info: dict) -> float | None:
    """
    Robuste Preis-Extraktion aus SerpAPI rate_per_night / total_rate.
    Versucht alle bekannten Felder, parsed Strings via Regex.
    """
    for key in ("extracted_lowest", "extracted_before_taxes_fees",
                "extracted_total", "lowest", "before_taxes_fees", "total"):
        val = rate_info.get(key)
        if val is None:
            continue
        if isinstance(val, (int, float)) and val > 0:
            return float(val)
        if isinstance(val, str):
            nums = re.findall(r"[\d]+(?:[.,][\d]+)?", val.replace(",", "."))
            if nums:
                try:
                    price = float(nums[0].replace(",", "."))
                    if price > 0:
                        return price
                except ValueError:
                    continue
    return None


def _aggregate(raw_results: list) -> tuple[list[dict], list[str]]:
    """
    Flatten and sort results from multiple providers.
    Returns (results, missing_key_providers).
    Exceptions from gather (return_exceptions=True) are silently dropped.
    """
    flat: list[dict] = []
    missing_keys: list[str] = []
    for r in raw_results:
        if isinstance(r, Exception):
            logger.error(f"[SEARCH] Provider exception suppressed: {r}")
            continue
        if isinstance(r, list):
            for item in r:
                if item.get("_api_key_missing"):
                    missing_keys.append(item.get("provider", "Unbekannt"))
                else:
                    flat.append(item)
    flat.sort(key=lambda x: x.get("price") or float("inf"))
    return flat, missing_keys


# ── Request / Response models ──────────────────────────────────────────────

class FlightSearchParams(BaseModel):
    origin:        str
    destination:   str
    outbound_date: str
    return_date:   Optional[str] = None
    adults:        int = 1
    children:      int = 0
    baggage:       str = "none"
    baggage_10kg:  int = 0
    baggage_20kg:  int = 0
    baggage_23kg:  int = 0
    seat_cost:     float = 0.0
    seat:          bool = False
    dep_from:      Optional[str] = None
    dep_to:        Optional[str] = None
    arr_from:      Optional[str] = None
    arr_to:        Optional[str] = None
    max_stops:     int = -1

    @model_validator(mode="after")
    def validate_flight_params(self) -> "FlightSearchParams":
        import re as _re
        for field, val in [("origin", self.origin), ("destination", self.destination)]:
            v = (val or "").strip().upper()
            if v and not _re.match(r"^[A-Z]{3}$", v):
                raise ValueError(f"{field} muss ein gültiger 3-Buchstaben IATA-Code sein (z.B. BGY, DUB)")
        if self.origin and self.destination:
            if self.origin.strip().upper() == self.destination.strip().upper():
                raise ValueError("origin und destination dürfen nicht identisch sein")
        if self.return_date and self.outbound_date:
            if self.return_date < self.outbound_date:
                raise ValueError(
                    f"return_date ({self.return_date}) darf nicht vor outbound_date ({self.outbound_date}) liegen"
                )
        return self


class HotelSearchParams(BaseModel):
    destination:   str
    checkin_date:  str
    checkout_date: str
    adults:        int = 2
    rooms:         int = 1

    @model_validator(mode="after")
    def validate_dates(self) -> "HotelSearchParams":
        if self.checkout_date and self.checkin_date:
            if self.checkout_date <= self.checkin_date:
                raise ValueError(
                    f"checkout_date ({self.checkout_date}) muss nach checkin_date ({self.checkin_date}) liegen"
                )
        return self


class CampingSearchParams(BaseModel):
    destination:        str
    checkin_date:       str
    checkout_date:      str
    adults:             int = 2
    accommodation_type: str = "mobilheim"
    bedrooms:           str = "1"
    aircon:             bool = False
    pets:               bool = False
    covered_terrace:    bool = False
    final_cleaning:     bool = False

    @model_validator(mode="after")
    def validate_dates(self) -> "CampingSearchParams":
        if self.checkout_date and self.checkin_date:
            if self.checkout_date <= self.checkin_date:
                raise ValueError(
                    f"checkout_date ({self.checkout_date}) muss nach checkin_date ({self.checkin_date}) liegen"
                )
        return self
