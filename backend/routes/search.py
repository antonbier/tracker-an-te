"""
WanderSuite — /api/search  (Meta-Suche Aggregator)

Strategy Pattern: Jede Kategorie feuert ALLE relevanten Provider
gleichzeitig via asyncio.gather ab. Faellt ein Provider aus, bleiben
die anderen unbeeintraichtigt (return_exceptions=True).

Endpoints:
  POST /api/search/flights  — Ryanair + Google Flights parallel
  POST /api/search/hotels   — SerpAPI Google Hotels + Booking parallel
  POST /api/search/camping  — SerpAPI Homair-Query

Anti-Scraping:
  - Realistische Browser-Header pro Provider
  - httpx.AsyncClient mit Timeout 18s pro Provider
  - Exception eines Providers wird geloggt und als leere Liste behandelt

Deep-Logging Format:
  [PROVIDER] icon #search status=ok | found=N | cheapest=XX.XX EUR
  [PROVIDER] icon #search status=error | error=MSG
"""

import asyncio
import logging
import time
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator

from auth_jwt import get_current_user
from settings_manager import get_setting_value
from flight_search_orchestrator import (
    search_flights as orchestrate_flights,
    FlightSearchParams as OrchestratorParams,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _ryanair_deeplink(origin: str, destination: str, date_out: str,
                       date_in, adults: int, children: int) -> str:
    """
    Generiert einen gültigen Ryanair Deeplink (2025-Format).
    Altes Format /buchen/fluge-finden/... war veraltet und lieferte 404.
    Neues Format: /trip/flights/select?... (gültig ab 2024).
    """
    base = "https://www.ryanair.com/de/de/trip/flights/select"
    is_return = "true" if date_in else "false"
    qs = (
        f"?adults={adults}&teens=0&children={children}&infants=0"
        f"&dateOut={date_out}"
        f"&dateIn={date_in or ''}"
        f"&isConnectedFlight=false&isReturn={is_return}"
        f"&originIata={origin}&destinationIata={destination}"
        f"&tpAdults={adults}&tpTeens=0&tpChildren={children}&tpInfants=0"
        f"&tpStartDate={date_out}"
        f"&tpEndDate={date_in or ''}"
        f"&tpDiscount=0&tpPromoCode="
        f"&tpOriginIata={origin}&tpDestinationIata={destination}"
    )
    return base + qs


def _parse_ryanair_time(local_list, utc_list, idx: int) -> str | None:
    """
    Extrahiert HH:MM als LOKALE Abflug-/Ankunftszeit.
    Bevorzugt seg.time (local), fällt auf timeUTC zurück (ebenfalls als lokal behandelt).
    Keine UTC→Lokal-Konvertierung — Zeiten werden exakt so angezeigt wie vom Airport.
    """
    def _extract(lst, i):
        if not lst or i >= len(lst): return None
        raw = str(lst[i]).strip()
        if "T" in raw: return raw.split("T")[1][:5]
        if len(raw) > 10 and " " in raw: return raw.split(" ")[1][:5]
        return raw[:5] if len(raw) >= 5 else None

    return _extract(local_list, idx) or _extract(utc_list, idx)


def _fmt_ryanair_flight_num(raw: str) -> str | None:
    """Normalisiert Ryanair Flugnummern: 'FR6125' → 'FR 6125'."""
    import re as _re
    if not raw: return None
    raw = str(raw).strip()
    if " " in raw: return raw
    m = _re.match(r"^([A-Z]{1,3})([0-9].*)$", raw)
    return f"{m.group(1)} {m.group(2)}" if m else raw

TIMEOUT = 18.0  # seconds per provider

# ── Realistic browser headers per provider ─────────────────────────────────

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


def _calc_nights(checkin: str, checkout: str) -> int:
    """Return number of nights between checkin and checkout (YYYY-MM-DD)."""
    try:
        from datetime import date
        ci = date.fromisoformat(checkin)
        co = date.fromisoformat(checkout)
        nights = (co - ci).days
        return max(nights, 1)
    except Exception:
        return 1


def _extract_price(rate_info: dict) -> float | None:
    """
    Robuste Preis-Extraktion aus SerpAPI rate_per_night / total_rate.
    SerpAPI liefert Preise als:
      - extracted_lowest / extracted_before_taxes_fees  (float, direkt nutzbar)
      - lowest / before_taxes_fees                      (String, z.B. "€ 49" oder "$99")
    Versucht alle bekannten Felder, parsed Strings via Regex.
    """
    import re
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


# ── Request / Response models ──────────────────────────────────────────────

class FlightSearchParams(BaseModel):
    origin:        str
    destination:   str
    outbound_date: str
    return_date:   Optional[str] = None
    adults:        int = 1
    children:      int = 0          # Kinder (2–11 J.)
    # Gepäck: Anzahl-Stepper pro Klasse (je Person)
    baggage:       str = "none"     # Legacy: 'none'|'10kg'|'20kg' (Ryanair-Compat)
    baggage_10kg:  int = 0          # Anzahl 10kg-Koffer gesamt
    baggage_20kg:  int = 0          # Anzahl 20kg-Koffer gesamt
    baggage_23kg:  int = 0          # Anzahl 23kg-Koffer gesamt
    seat_cost:     float = 0.0      # Sitzplatzpreis €/Person/Flug
    seat:          bool = False     # Legacy bool (wird aus seat_cost>0 abgeleitet)
    # Zeit- & Stopp-Filter
    dep_from:      Optional[str] = None   # Abflug ab  HH:MM
    dep_to:        Optional[str] = None   # Abflug bis HH:MM
    arr_from:      Optional[str] = None   # Ankunft ab HH:MM
    arr_to:        Optional[str] = None   # Ankunft bis HH:MM
    max_stops:     int = -1               # -1=alle, 0=nonstop, 1=max 1 Stopp, 2=max 2

    @model_validator(mode="after")
    def validate_flight_params(self) -> "FlightSearchParams":
        """FIX W2/W3: validate IATA codes and origin != destination."""
        import re
        for field, val in [("origin", self.origin), ("destination", self.destination)]:
            v = (val or "").strip().upper()
            if v and not re.match(r"^[A-Z]{3}$", v):
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
        """FIX B2: checkout must be after checkin."""
        if self.checkout_date and self.checkin_date:
            if self.checkout_date <= self.checkin_date:
                raise ValueError(
                    f"checkout_date ({self.checkout_date}) muss nach checkin_date ({self.checkin_date}) liegen"
                )
        return self


class CampingSearchParams(BaseModel):
    destination:     str
    checkin_date:    str
    checkout_date:   str
    adults:          int = 2
    accommodation_type: str = "mobilheim"  # 'mobilheim'|'glamping'|'stellplatz'
    bedrooms:        str = "1"             # '1'|'2'|'3'
    aircon:          bool = False
    pets:            bool = False
    covered_terrace: bool = False
    final_cleaning:  bool = False          # Endreinigung einkalkulieren

    @model_validator(mode="after")
    def validate_dates(self) -> "CampingSearchParams":
        """FIX B2: checkout must be after checkin."""
        if self.checkout_date and self.checkin_date:
            if self.checkout_date <= self.checkin_date:
                raise ValueError(
                    f"checkout_date ({self.checkout_date}) muss nach checkin_date ({self.checkin_date}) liegen"
                )
        return self


# ── Provider functions (async) ─────────────────────────────────────────────

async def _search_ryanair(params: FlightSearchParams) -> list[dict]:
    """
    Ryanair Suche via farfnd/cheapestPerDay API.
    Die alte booking/v4 availability API liefert seit 2025 generell 409 "Availability declined"
    für externe Requests. Neue Strategie: cheapestPerDay gibt den günstigsten Flug pro Tag
    inkl. exakter Abflug-/Ankunftszeit zurück.
    Bei Hin- und Rückflug werden beide Richtungen parallel abgefragt und kombiniert.
    """
    t0 = time.time()
    origin = params.origin.upper()
    dest   = params.destination.upper()

    def _parse_iso_time(iso: str | None) -> str | None:
        if not iso: return None
        # "2026-05-01T16:05:00" → "16:05"
        if "T" in iso:
            return iso.split("T")[1][:5]
        return None

    def _build_extras(base_price: float) -> tuple[float, list[str]]:
        total_pax = params.adults + params.children
        baggage_cost = 0.0
        if params.baggage_10kg > 0:
            baggage_cost += params.baggage_10kg * 22.99
        elif params.baggage == "10kg":
            baggage_cost = 22.99 * total_pax
        if params.baggage_20kg > 0:
            baggage_cost += params.baggage_20kg * 34.99
        elif params.baggage == "20kg" and params.baggage_10kg == 0:
            baggage_cost = 34.99 * total_pax
        if params.baggage_23kg > 0:
            baggage_cost += params.baggage_23kg * 42.99
        _seat_cpp = params.seat_cost if params.seat_cost > 0 else (8.99 if params.seat else 0.0)
        seat_total = _seat_cpp * total_pax
        total = round((base_price * total_pax) + baggage_cost + seat_total, 2)
        badges = []
        if params.baggage_10kg > 0: badges.append(f"🎒 {params.baggage_10kg}x 10kg")
        elif params.baggage == "10kg": badges.append("🎒 1x 10kg")
        if params.baggage_20kg > 0: badges.append(f"🎒 {params.baggage_20kg}x 20kg")
        elif params.baggage == "20kg" and params.baggage_10kg == 0: badges.append("🎒 1x 20kg")
        if params.baggage_23kg > 0: badges.append(f"🧳 {params.baggage_23kg}x 23kg")
        if _seat_cpp > 0: badges.append(f"💺 Sitz {_seat_cpp:.0f}€/P")
        if params.children > 0: badges.append(f"👶 {params.children} Kind{'er' if params.children>1 else ''}")
        return total, badges, _seat_cpp

    async def _fetch_cheapest_per_day(client, dep, arr, date_str):
        """Gibt liste von verfügbaren Fares für den gewünschten Monat zurück."""
        year, month, day = date_str.split("-")
        month_start = f"{year}-{month}-01"
        url = f"https://www.ryanair.com/api/farfnd/3/oneWayFares/{dep}/{arr}/cheapestPerDay"
        resp = await client.get(url, params={
            "outboundMonthOfDate": month_start,
            "currency": "EUR",
        })
        if resp.status_code != 200:
            return []
        raw = resp.json().get("outbound", {}).get("fares", [])
        # Filter: nur der gesuchte Tag (exact match auf "day" field)
        return [f for f in raw if f.get("day") == date_str and f.get("price") and not f.get("unavailable")]

    try:
        headers = {**HEADERS_RYANAIR, "Referer": "https://www.ryanair.com/"}
        async with httpx.AsyncClient(headers=headers, timeout=TIMEOUT, follow_redirects=True) as client:
            # Parallel: Hinflug + ggf. Rückflug
            tasks = [_fetch_cheapest_per_day(client, origin, dest, params.outbound_date)]
            if params.return_date:
                tasks.append(_fetch_cheapest_per_day(client, dest, origin, params.return_date))
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        outbound_fares = raw_results[0] if not isinstance(raw_results[0], Exception) else []
        return_fares   = raw_results[1] if len(raw_results) > 1 and not isinstance(raw_results[1], Exception) else []

        elapsed = round(time.time() - t0, 1)

        if not outbound_fares:
            logger.warning(f"[RYANAIR] ✈️ #search status=no_flights | {origin}->{dest} {params.outbound_date} | elapsed={elapsed}s")
            return []

        results = []
        for fare in outbound_fares[:5]:
            ob = fare.get("outbound") or fare  # API wraps in "outbound" key
            # cheapestPerDay structure: fare = {"day": "...", "price": {"value": 39.27}, "departureDate": "...", "arrivalDate": "...", "flightNumber": "FR4845"}
            # But sometimes the fare itself IS the outbound object
            price_val = None
            dep_time  = None
            arr_time  = None
            flight_num = None

            if "price" in fare and "departureDate" in fare:
                # Direct structure
                price_val  = fare["price"].get("value") if isinstance(fare.get("price"), dict) else fare.get("price")
                dep_time   = _parse_iso_time(fare.get("departureDate"))
                arr_time   = _parse_iso_time(fare.get("arrivalDate"))
                flight_num = fare.get("flightNumber", "")
            elif "outbound" in fare:
                ob2 = fare["outbound"]
                price_val  = ob2.get("price", {}).get("value")
                dep_time   = _parse_iso_time(ob2.get("departureDate"))
                arr_time   = _parse_iso_time(ob2.get("arrivalDate"))
                flight_num = ob2.get("flightNumber", "")

            if not price_val:
                continue

            # Zeit-Filter anwenden
            def _tin(t, f, to):
                if not t or (not f and not to): return True
                try:
                    tv = int(t[:2])*60+int(t[3:5])
                    if f and tv < int(f[:2])*60+int(f[3:5]): return False
                    if to and tv > int(to[:2])*60+int(to[3:5]): return False
                except Exception: pass
                return True
            if not _tin(dep_time, params.dep_from, params.dep_to): continue

            # Rückflug-Aufschlag
            ret_price = 0.0
            if return_fares:
                cheapest_ret = min(
                    (f.get("price", {}).get("value") or f.get("outbound", {}).get("price", {}).get("value") or 0
                     for f in return_fares), default=0
                )
                ret_price = float(cheapest_ret)

            base_price = float(price_val) + ret_price
            total, badges, _ = _build_extras(base_price)
            flight_num_fmt = _fmt_ryanair_flight_num(flight_num or "")
            time_label = f" · {dep_time} ✈ {arr_time}" if dep_time and arr_time else ""

            results.append({
                "id":        f"ry-{origin}-{dest}-{params.outbound_date}-{len(results)}",
                "provider":  "Ryanair",
                "title":     f"{origin} → {dest}",
                "subtitle":  f"{params.outbound_date}{' ⇄ ' + params.return_date if params.return_date else ''} · {params.adults} Pers.{time_label}",
                "price":     total,
                "currency":  "EUR",
                "badges":    badges,
                "booking_url": _ryanair_deeplink(origin, dest, params.outbound_date, params.return_date, params.adults, params.children),
                "detail": {
                    "origin":         origin,
                    "destination":    dest,
                    "outbound_date":  params.outbound_date,
                    "return_date":    params.return_date,
                    "adults":         params.adults,
                    "children":       params.children,
                    "baggage":        params.baggage,
                    "baggage_10kg":   params.baggage_10kg,
                    "baggage_20kg":   params.baggage_20kg,
                    "baggage_23kg":   params.baggage_23kg,
                    "seat":           params.seat,
                    "seat_cost":      params.seat_cost,
                    "departure_time": dep_time,
                    "arrival_time":   arr_time,
                    "flight_number":  flight_num_fmt,
                    "airline":        "Ryanair",
                    "stops":          0,
                },
                "_tracker_type":  "flight",
                "_tracker_table": "trackers",
            })

        found = len(results)
        cheapest = min((r["price"] for r in results), default=0)
        logger.info(f"[RYANAIR] ✈️ #search status=ok | found={found} | cheapest={cheapest:.2f} EUR | elapsed={elapsed}s")
        return results

    except httpx.TimeoutException:
        elapsed = round(time.time() - t0, 1)
        logger.warning(f"[RYANAIR] ✈️ #search status=timeout | elapsed={elapsed}s")
        return []
    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        logger.error(f"[RYANAIR] ✈️ #search status=error | error={e} | elapsed={elapsed}s")
        return []


async def _search_google_flights(params: FlightSearchParams, api_key: str) -> list[dict]:
    """SerpAPI Google Flights — returns top results."""
    if not api_key:
        logger.warning("[SERPAPI/GF] ✈️ #search status=skip | reason=no_api_key")
        return [{"_api_key_missing": True, "provider": "Google Flights"}]
    t0 = time.time()
    try:
        async with httpx.AsyncClient(headers=HEADERS_SERPAPI, timeout=TIMEOUT) as client:
            req_params = {
                "engine":        "google_flights",
                "departure_id":  params.origin.upper(),
                "arrival_id":    params.destination.upper(),
                "outbound_date": params.outbound_date,
                "currency":      "EUR",
                "hl":            "de",
                "adults":        params.adults,
                "children":      params.children,
                "api_key":       api_key,
            }
            # SerpAPI: type=1 = Round-trip, type=2 = One-way
            if params.return_date:
                req_params["return_date"] = params.return_date
                req_params["type"] = "1"   # round-trip
            else:
                req_params["type"] = "2"   # one-way
            # Stopp-Filter: 0=nonstop, 1=max 1 Stopp
            if params.max_stops >= 0:
                req_params["stops"] = params.max_stops

            resp = await client.get(SERPAPI_BASE, params=req_params)
            resp.raise_for_status()
            data = resp.json()
            elapsed = round(time.time() - t0, 1)

            best_flights = data.get("best_flights", []) or data.get("other_flights", [])
            results = []
            for fl in best_flights[:5]:
                legs = fl.get("flights", [{}])
                leg = legs[0] if legs else {}
                price = fl.get("price")
                if not price:
                    continue

                badges = []
                if params.baggage == "10kg":
                    badges.append("🎒 1x 10kg")
                elif params.baggage == "20kg":
                    badges.append("🎒 1x 20kg")
                if params.seat:
                    badges.append("💺 Sitzplatz")

                airline = leg.get("airline", "")
                # Skip Ryanair-operated flights — they are covered by the dedicated
                # Ryanair scraper and cannot be booked via Google Flights anyway.
                if "ryanair" in airline.lower():
                    continue
                dep = leg.get("departure_airport", {})
                arr = leg.get("arrival_airport", {})
                # Stopp-Anzahl
                n_stops = len(fl.get("flights", [])) - 1
                if params.max_stops >= 0 and n_stops > params.max_stops:
                    continue
                # Layover details from SerpAPI
                _layover_airports = [
                    leg.get("departure_airport", {}).get("id", "")
                    for leg in fl.get("flights", [])[1:]
                    if leg.get("departure_airport", {}).get("id")
                ]
                _layover_durations = [
                    lay.get("duration")
                    for lay in fl.get("layovers", [])
                    if lay.get("duration") is not None
                ]
                # Zeit-Filter
                # SerpAPI "time" may be "2026-05-05 08:15" (datetime) or "08:15" (time only)
                _dep_raw = dep.get("time", "")
                _arr_raw = arr.get("time", "")
                dep_t = _dep_raw[-5:] if len(_dep_raw) >= 5 else _dep_raw
                arr_t = _arr_raw[-5:] if len(_arr_raw) >= 5 else _arr_raw
                def _tin(t, f, to):
                    if not t or (not f and not to): return True
                    try:
                        tv = int(t[:2])*60+int(t[3:5])
                        if f and tv < int(f[:2])*60+int(f[3:5]): return False
                        if to and tv > int(to[:2])*60+int(to[3:5]): return False
                    except Exception: pass
                    return True
                if not _tin(dep_t, params.dep_from, params.dep_to): continue
                if not _tin(arr_t, params.arr_from, params.arr_to): continue

                # Gepäck + Sitz-Kosten aufaddieren
                total_pax = params.adults + params.children
                extra = 0.0
                extra += params.baggage_10kg * 22.99
                extra += params.baggage_20kg * 34.99
                extra += params.baggage_23kg * 42.99
                if params.baggage == "10kg" and params.baggage_10kg == 0: extra += 22.99 * total_pax
                elif params.baggage == "20kg" and params.baggage_20kg == 0: extra += 34.99 * total_pax
                _sp = params.seat_cost if params.seat_cost > 0 else (8.99 if params.seat else 0.0)
                extra += _sp * total_pax
                adj_price = float(price) + extra

                stop_badges = ["🔵 Nonstop" if n_stops == 0 else f"🔵 {n_stops} Stopp{'s' if n_stops>1 else ''}"]
                results.append({
                    "id":       f"gf-{params.origin}-{params.destination}-{params.outbound_date}-{len(results)}",
                    "provider": "Google Flights",
                    "title":    f"{params.origin.upper()} → {params.destination.upper()}",
                    "subtitle": f"{params.outbound_date} · {airline} · {dep_t[:5] if dep_t else ''}→{arr_t[:5] if arr_t else ''}",
                    "price":    round(adj_price, 2),
                    "currency": "EUR",
                    "badges":   badges + stop_badges,
                    "booking_url": f"https://www.google.com/flights#search;f={params.origin.upper()};t={params.destination.upper()};d={params.outbound_date}",
                    "detail": {
                        "origin":             params.origin.upper(),
                        "destination":        params.destination.upper(),
                        "outbound_date":      params.outbound_date,
                        "return_date":        params.return_date,
                        "adults":             params.adults,
                        "children":           params.children,
                        "baggage":            params.baggage,
                        "baggage_10kg":       params.baggage_10kg,
                        "baggage_20kg":       params.baggage_20kg,
                        "baggage_23kg":       params.baggage_23kg,
                        "seat":               params.seat,
                        "seat_cost":          params.seat_cost,
                        "airline":            airline,
                        "departure_time":     dep_t,
                        "arrival_time":       arr_t,
                        "duration_min":       fl.get("total_duration"),
                        "stops":              n_stops,
                        "layover_airports":   _layover_airports,
                        "layover_durations":  _layover_durations,
                    },
                    "_tracker_type":  "google_flight",
                    "_tracker_table": "gf_trackers",
                })

            found = len(results)
            cheapest = min((r["price"] for r in results), default=0)
            logger.info(f"[SERPAPI] 🔍 #search status=ok | source=google_flights | found={found} | cheapest={cheapest:.2f} EUR | elapsed={elapsed}s")
            return results

    except httpx.TimeoutException:
        elapsed = round(time.time() - t0, 1)
        logger.warning(f"[SERPAPI] 🔍 #search status=timeout | source=google_flights | elapsed={elapsed}s")
        return []
    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        logger.error(f"[SERPAPI] 🔍 #search status=error | source=google_flights | error={e} | elapsed={elapsed}s")
        return []


async def _search_hotels_serpapi(params: HotelSearchParams, api_key: str) -> list[dict]:
    """SerpAPI Google Hotels."""
    if not api_key:
        logger.warning("[SERPAPI/HOTELS] 🏨 #search status=skip | reason=no_api_key")
        return []
    t0 = time.time()
    try:
        async with httpx.AsyncClient(headers=HEADERS_SERPAPI, timeout=TIMEOUT) as client:
            resp = await client.get(SERPAPI_BASE, params={
                "engine":         "google_hotels",
                "q":              params.destination,
                "check_in_date":  params.checkin_date,
                "check_out_date": params.checkout_date,
                "adults":         params.adults,
                "rooms":          params.rooms,
                "currency":       "EUR",
                "hl":             "de",
                "api_key":        api_key,
            })
            resp.raise_for_status()
            data = resp.json()
            elapsed = round(time.time() - t0, 1)

            hotels = data.get("properties", [])
            results = []
            for h in hotels[:8]:
                price_info = h.get("rate_per_night") or h.get("total_rate") or {}
                raw_price  = _extract_price(price_info)
                if not raw_price:
                    # Also try top-level extracted_lowest
                    raw_price = h.get("extracted_lowest") or h.get("price") or None
                    if raw_price:
                        try:
                            raw_price = float(raw_price)
                        except (TypeError, ValueError):
                            raw_price = None
                if not raw_price:
                    continue
                nights          = _calc_nights(params.checkin_date, params.checkout_date)
                # SerpAPI rate_per_night is always a nightly rate — multiply by nights
                price_per_night = round(float(raw_price), 2)
                total_price     = round(price_per_night * nights, 2)
                per_night_avg   = price_per_night  # same, for consistency

                results.append({
                    "id":       f"ht-{params.destination}-{params.checkin_date}-{len(results)}",
                    "provider": "Google Hotels",
                    "title":    h.get("name", params.destination),
                    "subtitle": f"{params.checkin_date} → {params.checkout_date} · {params.adults} Pers. · {params.rooms} Zi. · {nights} Nächte",
                    "price":    total_price,
                    "price_per_night": per_night_avg,
                    "nights":   nights,
                    "currency": "EUR",
                    "badges":   [f"⭐ {h.get('overall_rating', '')}"] if h.get("overall_rating") else [],
                    "booking_url": h.get("link") or f"https://www.google.com/travel/hotels/entity/{h.get('serpapi_property_id', '')}",
                    "detail": {
                        "destination":   params.destination,
                        "checkin_date":  params.checkin_date,
                        "checkout_date": params.checkout_date,
                        "adults":        params.adults,
                        "rooms":         params.rooms,
                        "hotel_name":    h.get("name"),
                        "source":        "google_hotels",
                        "nights":        nights,
                        "price_per_night": per_night_avg,
                    },
                    "_tracker_type":  "hotel",
                    "_tracker_table": "booking_trackers",
                })

            found = len(results)
            cheapest = min((r["price"] for r in results), default=0)
            logger.info(f"[SERPAPI] 🏨 #search status=ok | source=google_hotels | found={found} | cheapest={cheapest:.2f} EUR | elapsed={elapsed}s")
            return results

    except httpx.TimeoutException:
        elapsed = round(time.time() - t0, 1)
        logger.warning(f"[SERPAPI] 🏨 #search status=timeout | source=google_hotels | elapsed={elapsed}s")
        return []
    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        logger.error(f"[SERPAPI] 🏨 #search status=error | source=google_hotels | error={e} | elapsed={elapsed}s")
        return []


async def _search_camping_serpapi(params: CampingSearchParams, api_key: str) -> list[dict]:
    """SerpAPI Google Hotels — Homair/Camping query."""
    if not api_key:
        logger.warning("[HOMAIR] ⛺ #search status=skip | reason=no_api_key")
        return []
    t0 = time.time()

    accom_labels = {
        "mobilheim":  "Mobilheim",
        "glamping":   "Glamping",
        "stellplatz": "Stellplatz",
    }
    query = f"Homair camping {params.destination} {accom_labels.get(params.accommodation_type, '')}".strip()

    try:
        async with httpx.AsyncClient(headers=HEADERS_SERPAPI, timeout=TIMEOUT) as client:
            resp = await client.get(SERPAPI_BASE, params={
                "engine":         "google_hotels",
                "q":              query,
                "check_in_date":  params.checkin_date,
                "check_out_date": params.checkout_date,
                "adults":         params.adults,
                "currency":       "EUR",
                "hl":             "de",
                "api_key":        api_key,
            })
            resp.raise_for_status()
            data = resp.json()
            elapsed = round(time.time() - t0, 1)

            hotels = data.get("properties", [])
            results = []
            for h in hotels[:6]:
                price_info = h.get("rate_per_night") or h.get("total_rate") or {}
                raw_price  = _extract_price(price_info)
                if not raw_price:
                    raw_price = h.get("extracted_lowest") or h.get("price") or None
                    if raw_price:
                        try:
                            raw_price = float(raw_price)
                        except (TypeError, ValueError):
                            raw_price = None
                if not raw_price:
                    continue

                badges = [f"⛺ {accom_labels.get(params.accommodation_type, params.accommodation_type)}"]
                if params.aircon:
                    badges.append("❄️ Klima")
                if params.pets:
                    badges.append("🐕 Hunde")
                if params.covered_terrace:
                    badges.append("🏠 Terrasse")
                if params.final_cleaning:
                    badges.append("🧹 Endreinigung")

                nights          = _calc_nights(params.checkin_date, params.checkout_date)
                # SerpAPI rate_per_night is always a nightly rate — multiply by nights
                price_per_night = round(float(raw_price), 2)
                total_price     = round(price_per_night * nights, 2)
                per_night_avg   = price_per_night  # same, for consistency

                results.append({
                    "id":       f"cp-{params.destination}-{params.checkin_date}-{len(results)}",
                    "provider": "Homair",
                    "title":    h.get("name", params.destination),
                    "subtitle": f"{params.checkin_date} → {params.checkout_date} · {params.adults} Pers. · {nights} Nächte",
                    "price":    total_price,
                    "price_per_night": per_night_avg,
                    "nights":   nights,
                    "currency": "EUR",
                    "badges":   badges,
                    "detail": {
                        "region":               params.destination,
                        "checkin_date":         params.checkin_date,
                        "checkout_date":        params.checkout_date,
                        "adults":               params.adults,
                        "accommodation_type":   params.accommodation_type,
                        "bedrooms":             params.bedrooms,
                        "aircon":               params.aircon,
                        "pets":                 params.pets,
                        "covered_terrace":      params.covered_terrace,
                        "campsite_name":        h.get("name"),
                        "source":               "homair",
                        "nights":               nights,
                        "price_per_night":      per_night_avg,
                        "final_cleaning":       params.final_cleaning,
                    },
                    "_tracker_type":  "camping",
                    "_tracker_table": "homair_trackers",
                })

            found = len(results)
            cheapest = min((r["price"] for r in results), default=0)
            logger.info(f"[HOMAIR] ⛺ #search status=ok | found={found} | cheapest={cheapest:.2f} EUR | elapsed={elapsed}s")
            return results

    except httpx.TimeoutException:
        elapsed = round(time.time() - t0, 1)
        logger.warning(f"[HOMAIR] ⛺ #search status=timeout | elapsed={elapsed}s")
        return []
    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        logger.error(f"[HOMAIR] ⛺ #search status=error | error={e} | elapsed={elapsed}s")
        return []


def _aggregate(raw_results: list) -> tuple[list[dict], list[str]]:
    """
    Flatten and sort results from multiple providers.
    Returns (results, missing_key_providers).
    Exceptions from gather (return_exceptions=True) are silently dropped.
    """
    flat = []
    missing_keys = []
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


# ── API Endpoints ──────────────────────────────────────────────────────────

@router.post("/flights")
async def search_flights(
    params: FlightSearchParams,
    user: dict = Depends(get_current_user),
):
    """
    Meta-Suche Flüge via Orchestrator.
    Aktive Provider werden aus der DB gelesen (GET /api/settings/providers).
    Alle aktiven Provider werden parallel via asyncio.gather aufgerufen.
    """
    if not params.origin or not params.destination or not params.outbound_date:
        raise HTTPException(400, "origin, destination und outbound_date sind Pflichtfelder")

    params.origin      = params.origin.strip().upper()
    params.destination = params.destination.strip().upper()

    logger.info(
        f"[SEARCH] ✈️ flights {params.origin}->{params.destination} "
        f"{params.outbound_date} | adults={params.adults} | via orchestrator"
    )

    # Delegate entirely to orchestrator — it reads provider configs from DB
    orch_params = OrchestratorParams(**params.model_dump())
    result = await orchestrate_flights(orch_params)
    return result


@router.post("/hotels")
async def search_hotels(
    params: HotelSearchParams,
    user: dict = Depends(get_current_user),
):
    """
    Meta-Suche Hotels: SerpAPI Google Hotels.
    Booking.com scraper wird ergaenzt sobald verf??gbar.
    """
    if not params.destination or not params.checkin_date or not params.checkout_date:
        raise HTTPException(400, "destination, checkin_date und checkout_date sind Pflichtfelder")

    serpapi_key = get_setting_value("serpapi_key") or ""
    if not serpapi_key:
        raise HTTPException(
            status_code=422,
            detail={"error": "missing_api_key", "provider": "SerpAPI",
                    "message": "API Key für SerpAPI fehlt in den Einstellungen."}
        )

    logger.info(
        f"[SEARCH] 🏨 hotels dest={params.destination} "
        f"{params.checkin_date}->{params.checkout_date} | "
        f"adults={params.adults} rooms={params.rooms}"
    )

    tasks = [
        _search_hotels_serpapi(params, serpapi_key),
    ]
    raw = await asyncio.gather(*tasks, return_exceptions=True)
    results, missing_keys = _aggregate(list(raw))

    logger.info(f"[SEARCH] 🏨 hotels total_results={len(results)}")
    return {"results": results, "count": len(results),
            "missing_api_keys": missing_keys}


@router.post("/camping")
async def search_camping(
    params: CampingSearchParams,
    user: dict = Depends(get_current_user),
):
    """
    Meta-Suche Camping: SerpAPI Homair-Query.
    """
    if not params.destination or not params.checkin_date or not params.checkout_date:
        raise HTTPException(400, "destination, checkin_date und checkout_date sind Pflichtfelder")

    serpapi_key = get_setting_value("serpapi_key") or ""
    if not serpapi_key:
        raise HTTPException(
            status_code=422,
            detail={"error": "missing_api_key", "provider": "SerpAPI",
                    "message": "API Key für SerpAPI fehlt in den Einstellungen."}
        )

    logger.info(
        f"[SEARCH] ⛺ camping dest={params.destination} "
        f"{params.checkin_date}->{params.checkout_date} | "
        f"type={params.accommodation_type} bedrooms={params.bedrooms} | "
        f"aircon={params.aircon} pets={params.pets} terrace={params.covered_terrace}"
    )

    tasks = [
        _search_camping_serpapi(params, serpapi_key),
    ]
    raw = await asyncio.gather(*tasks, return_exceptions=True)
    results, missing_keys = _aggregate(list(raw))

    logger.info(f"[SEARCH] ⛺ camping total_results={len(results)}")
    return {"results": results, "count": len(results),
            "missing_api_keys": missing_keys}

