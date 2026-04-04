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
from pydantic import BaseModel

from auth_jwt import get_current_user
from settings_manager import get_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)

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


class HotelSearchParams(BaseModel):
    destination:   str
    checkin_date:  str
    checkout_date: str
    adults:        int = 2
    rooms:         int = 1


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


# ── Provider functions (async) ─────────────────────────────────────────────

async def _search_ryanair(params: FlightSearchParams) -> list[dict]:
    """Ryanair availability API — returns cheapest flights."""
    t0 = time.time()
    try:
        async with httpx.AsyncClient(headers=HEADERS_RYANAIR, timeout=TIMEOUT) as client:
            # Step 1: get session cookie
            await client.get("https://www.ryanair.com/de/de", follow_redirects=True)

            url = "https://www.ryanair.com/api/booking/v4/de-de/availability"
            params_req = {
                "ADT": params.adults,
                "CHD": 0,
                "DateOut": params.outbound_date,
                "Destination": params.destination.upper(),
                "FlexDaysBeforeOut": 0,
                "FlexDaysOut": 0,
                "Origin": params.origin.upper(),
                "RoundTrip": "true" if params.return_date else "false",
                "ToUs": "AGREED",
            }
            if params.return_date:
                params_req["DateIn"] = params.return_date

            resp = await client.get(url, params=params_req)
            elapsed = round(time.time() - t0, 1)

            if resp.status_code == 403:
                logger.warning(f"[RYANAIR] ✈️ #search status=blocked_by_cf | elapsed={elapsed}s")
                return []

            resp.raise_for_status()
            data = resp.json()

            results = []
            trips = data.get("trips", [])
            for trip in trips:
                for date_info in trip.get("dates", []):
                    for flight in date_info.get("flights", []):
                        regular = flight.get("regularFare")
                        if not regular:
                            continue
                        fares = regular.get("fares", [])
                        if not fares:
                            continue
                        base_price = fares[0].get("amount", 0)
                        if not base_price:
                            continue

                        # Gepäck-Kosten (neue Stepper-Logik + Legacy-Fallback)
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

                        # Sitzplatz: seat_cost €/Person/Flug (neue Logik) oder Legacy bool
                        _seat_cost_per_pax = params.seat_cost if params.seat_cost > 0 else (8.99 if params.seat else 0.0)
                        seat_total = _seat_cost_per_pax * total_pax

                        total = round((base_price * total_pax) + baggage_cost + seat_total, 2)

                        badges = []
                        if params.baggage_10kg > 0: badges.append(f"🎒 {params.baggage_10kg}x 10kg")
                        elif params.baggage == "10kg": badges.append("🎒 1x 10kg")
                        if params.baggage_20kg > 0: badges.append(f"🎒 {params.baggage_20kg}x 20kg")
                        elif params.baggage == "20kg" and params.baggage_10kg == 0: badges.append("🎒 1x 20kg")
                        if params.baggage_23kg > 0: badges.append(f"🧳 {params.baggage_23kg}x 23kg")
                        if _seat_cost_per_pax > 0: badges.append(f"💺 Sitz {_seat_cost_per_pax:.0f}€/P")
                        if params.children > 0: badges.append(f"👶 {params.children} Kind{'er' if params.children>1 else ''}")

                        seg = flight.get("segments", [{}])[0]
                        results.append({
                            "id":          f"ry-{params.origin}-{params.destination}-{params.outbound_date}-{len(results)}",
                            "provider":    "Ryanair",
                            "title":       f"{params.origin.upper()} → {params.destination.upper()}",
                            "subtitle":    f"{params.outbound_date}{' ⇄ ' + params.return_date if params.return_date else ''} · {params.adults} Pers.",
                            "price":       total,
                            "currency":    "EUR",
                            "badges":      badges,
                            "detail": {
                                "origin":        params.origin.upper(),
                                "destination":   params.destination.upper(),
                                "outbound_date": params.outbound_date,
                                "return_date":   params.return_date,
                                "adults":        params.adults,
                                "baggage":       params.baggage,
                                "seat":          params.seat,
                                "departure_time": seg.get("timeUTC", [""])[0][:5] if seg.get("timeUTC") else None,
                            },
                            "_tracker_type": "flight",
                            "_tracker_table": "trackers",
                        })

            # Zeit- & Stopp-Filter anwenden
            def _time_in(t, from_t, to_t):
                """Prüft ob HH:MM-Zeit t im Fenster [from_t, to_t] liegt."""                if not t or (not from_t and not to_t): return True
                try:
                    th, tm = int(t[:2]), int(t[3:5])
                    if from_t:
                        fh, fm = int(from_t[:2]), int(from_t[3:5])
                        if (th*60+tm) < (fh*60+fm): return False
                    if to_t:
                        toh, tom = int(to_t[:2]), int(to_t[3:5])
                        if (th*60+tm) > (toh*60+tom): return False
                except Exception: pass
                return True

            filtered = []
            for res in results:
                dep_t = res.get("detail", {}).get("departure_time") or ""
                if not _time_in(dep_t, params.dep_from, params.dep_to): continue
                filtered.append(res)

            found = len(filtered)
            cheapest = min((r["price"] for r in filtered), default=0)
            logger.info(f"[RYANAIR] ✈️ #search status=ok | found={found} | cheapest={cheapest:.2f} EUR | elapsed={elapsed}s")
            return filtered[:10]

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
        return []
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
                "api_key":       api_key,
            }
            # SerpAPI: type=1 = Round-trip, type=2 = One-way
            if params.return_date:
                req_params["return_date"] = params.return_date
                req_params["type"] = "1"   # round-trip
            else:
                req_params["type"] = "2"   # one-way

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
                dep = leg.get("departure_airport", {})
                arr = leg.get("arrival_airport", {})
                # Stopp-Anzahl
                n_stops = len(fl.get("flights", [])) - 1
                if params.max_stops >= 0 and n_stops > params.max_stops:
                    continue
                # Zeit-Filter
                dep_t = dep.get("time", "")
                arr_t = arr.get("time", "")
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
                    "detail": {
                        "origin":          params.origin.upper(),
                        "destination":     params.destination.upper(),
                        "outbound_date":   params.outbound_date,
                        "return_date":     params.return_date,
                        "adults":          params.adults,
                        "children":        params.children,
                        "baggage":         params.baggage,
                        "baggage_10kg":    params.baggage_10kg,
                        "baggage_20kg":    params.baggage_20kg,
                        "baggage_23kg":    params.baggage_23kg,
                        "seat":            params.seat,
                        "seat_cost":       params.seat_cost,
                        "airline":         airline,
                        "departure_time":  dep_t,
                        "arrival_time":    arr_t,
                        "duration_min":    fl.get("total_duration"),
                        "stops":           n_stops,
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
                results.append({
                    "id":       f"ht-{params.destination}-{params.checkin_date}-{len(results)}",
                    "provider": "Google Hotels",
                    "title":    h.get("name", params.destination),
                    "subtitle": f"{params.checkin_date} → {params.checkout_date} · {params.adults} Pers. · {params.rooms} Zi.",
                    "price":    float(raw_price),
                    "currency": "EUR",
                    "badges":   [f"⭐ {h.get('overall_rating', '')}"] if h.get("overall_rating") else [],
                    "detail": {
                        "destination":  params.destination,
                        "checkin_date":  params.checkin_date,
                        "checkout_date": params.checkout_date,
                        "adults":        params.adults,
                        "rooms":         params.rooms,
                        "hotel_name":    h.get("name"),
                        "source":        "google_hotels",
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

                results.append({
                    "id":       f"cp-{params.destination}-{params.checkin_date}-{len(results)}",
                    "provider": "Homair",
                    "title":    h.get("name", params.destination),
                    "subtitle": f"{params.checkin_date} → {params.checkout_date} · {params.adults} Pers.",
                    "price":    float(raw_price),
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


def _aggregate(raw_results: list) -> list[dict]:
    """
    Flatten and sort results from multiple providers.
    Exceptions from gather (return_exceptions=True) are silently dropped.
    """
    flat = []
    for r in raw_results:
        if isinstance(r, Exception):
            logger.error(f"[SEARCH] Provider exception suppressed: {r}")
            continue
        if isinstance(r, list):
            flat.extend(r)
    flat.sort(key=lambda x: x.get("price") or float("inf"))
    return flat


# ── API Endpoints ──────────────────────────────────────────────────────────

@router.post("/flights")
async def search_flights(
    params: FlightSearchParams,
    user: dict = Depends(get_current_user),
):
    """
    Meta-Suche Fluege: Ryanair + Google Flights parallel.
    Faellt ein Provider aus, liefert der andere trotzdem Ergebnisse.
    """
    if not params.origin or not params.destination or not params.outbound_date:
        raise HTTPException(400, "origin, destination und outbound_date sind Pflichtfelder")

    params.origin      = params.origin.strip().upper()
    params.destination = params.destination.strip().upper()

    serpapi_key = get_setting_value("serpapi_key") or ""

    logger.info(
        f"[SEARCH] ✈️ flights {params.origin}->{params.destination} "
        f"{params.outbound_date} | adults={params.adults} | "
        f"baggage={params.baggage} | seat={params.seat} | "
        f"providers=ryanair,google_flights"
    )

    tasks = [
        _search_ryanair(params),
        _search_google_flights(params, serpapi_key),
    ]
    raw = await asyncio.gather(*tasks, return_exceptions=True)
    results = _aggregate(list(raw))

    logger.info(f"[SEARCH] ✈️ flights total_results={len(results)}")
    return {"results": results, "count": len(results)}


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

    logger.info(
        f"[SEARCH] 🏨 hotels dest={params.destination} "
        f"{params.checkin_date}->{params.checkout_date} | "
        f"adults={params.adults} rooms={params.rooms}"
    )

    tasks = [
        _search_hotels_serpapi(params, serpapi_key),
    ]
    raw = await asyncio.gather(*tasks, return_exceptions=True)
    results = _aggregate(list(raw))

    logger.info(f"[SEARCH] 🏨 hotels total_results={len(results)}")
    return {"results": results, "count": len(results)}


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
    results = _aggregate(list(raw))

    logger.info(f"[SEARCH] ⛺ camping total_results={len(results)}")
    return {"results": results, "count": len(results)}
