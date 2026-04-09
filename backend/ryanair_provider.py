"""
WanderSuite — Ryanair Provider (farfnd/cheapestPerDay)

Kein API-Key nötig. Liefert den günstigsten Flug pro gesuchtem Tag.
Einschränkung: nur 1 Flug pro Tag (cheapest). Für vollständigen Tagesplan → Kiwi.
"""

import asyncio
import logging
import time
import httpx
from flight_search_orchestrator import FlightSearchParams

logger = logging.getLogger(__name__)

TIMEOUT = 15.0
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "de-DE,de;q=0.9",
    "Origin": "https://www.ryanair.com",
    "Referer": "https://www.ryanair.com/",
}


def _ryanair_deeplink(origin, destination, date_out, date_in, adults, children):
    base = "https://www.ryanair.com/de/de/trip/flights/select"
    is_return = "true" if date_in else "false"
    qs = (
        f"?adults={adults}&teens=0&children={children}&infants=0"
        f"&dateOut={date_out}&dateIn={date_in or ''}"
        f"&isConnectedFlight=false&isReturn={is_return}"
        f"&originIata={origin}&destinationIata={destination}"
        f"&tpAdults={adults}&tpTeens=0&tpChildren={children}&tpInfants=0"
        f"&tpStartDate={date_out}&tpEndDate={date_in or ''}"
        f"&tpDiscount=0&tpPromoCode=&tpOriginIata={origin}&tpDestinationIata={destination}"
    )
    return base + qs


def _fmt_flight_num(raw: str) -> str:
    import re
    if not raw: return ""
    raw = str(raw).strip()
    if " " in raw: return raw
    m = re.match(r"^([A-Z]{1,3})([0-9].*)$", raw)
    return f"{m.group(1)} {m.group(2)}" if m else raw


def _parse_iso_time(iso: str | None) -> str | None:
    if not iso: return None
    if "T" in iso: return iso.split("T")[1][:5]
    return None


def _build_extras(base_price: float, params: FlightSearchParams):
    total_pax = params.adults + params.children
    bag = 0.0
    if params.baggage_10kg > 0: bag += params.baggage_10kg * 22.99
    elif params.baggage == "10kg": bag = 22.99 * total_pax
    if params.baggage_20kg > 0: bag += params.baggage_20kg * 34.99
    elif params.baggage == "20kg" and params.baggage_10kg == 0: bag = 34.99 * total_pax
    if params.baggage_23kg > 0: bag += params.baggage_23kg * 42.99
    scp = params.seat_cost if params.seat_cost > 0 else (8.99 if params.seat else 0.0)
    total = round((base_price * total_pax) + bag + scp * total_pax, 2)
    badges = []
    if params.baggage_10kg > 0: badges.append(f"🎒 {params.baggage_10kg}x 10kg")
    elif params.baggage == "10kg": badges.append("🎒 1x 10kg")
    if params.baggage_20kg > 0: badges.append(f"🎒 {params.baggage_20kg}x 20kg")
    elif params.baggage == "20kg" and params.baggage_10kg == 0: badges.append("🎒 1x 20kg")
    if params.baggage_23kg > 0: badges.append(f"🧳 {params.baggage_23kg}x 23kg")
    if scp > 0: badges.append(f"💺 Sitz {scp:.0f}€/P")
    if params.children > 0: badges.append(f"👶 {params.children} Kind{'er' if params.children>1 else ''}")
    return total, badges


async def _fetch_day(client: httpx.AsyncClient, dep: str, arr: str, date_str: str) -> list[dict]:
    year, month, _ = date_str.split("-")
    url = f"https://www.ryanair.com/api/farfnd/3/oneWayFares/{dep}/{arr}/cheapestPerDay"
    try:
        resp = await client.get(url, params={"outboundMonthOfDate": f"{year}-{month}-01", "currency": "EUR"})
        if resp.status_code != 200:
            return []
        fares = resp.json().get("outbound", {}).get("fares", [])
        return [f for f in fares if f.get("day") == date_str and f.get("price") and not f.get("unavailable")]
    except Exception as e:
        logger.warning(f"[RYANAIR] fetch_day {dep}->{arr} {date_str}: {e}")
        return []


async def search(params: FlightSearchParams, cfg: dict) -> list[dict]:
    t0 = time.time()
    origin = params.origin.upper()
    dest   = params.destination.upper()

    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        tasks = [_fetch_day(client, origin, dest, params.outbound_date)]
        if params.return_date:
            tasks.append(_fetch_day(client, dest, origin, params.return_date))
        raw = await asyncio.gather(*tasks, return_exceptions=True)

    outbound_fares = raw[0] if not isinstance(raw[0], Exception) else []
    return_fares   = raw[1] if len(raw) > 1 and not isinstance(raw[1], Exception) else []
    elapsed = round(time.time() - t0, 1)

    if not outbound_fares:
        logger.info(f"[RYANAIR] ✈️ status=no_flights | {origin}->{dest} {params.outbound_date} | elapsed={elapsed}s")
        return []

    results = []
    ret_price = 0.0
    if return_fares:
        ret_price = float(min(
            (f.get("price", {}).get("value") or 0 for f in return_fares), default=0
        ))

    for fare in outbound_fares[:5]:
        price_val  = fare.get("price", {}).get("value")
        dep_time   = _parse_iso_time(fare.get("departureDate"))
        arr_time   = _parse_iso_time(fare.get("arrivalDate"))
        flight_num = _fmt_flight_num(fare.get("flightNumber", ""))

        if not price_val:
            continue

        # Time filter
        def _tin(t, f, to):
            if not t or (not f and not to): return True
            try:
                tv = int(t[:2])*60+int(t[3:5])
                if f and tv < int(f[:2])*60+int(f[3:5]): return False
                if to and tv > int(to[:2])*60+int(to[3:5]): return False
            except Exception: pass
            return True
        if not _tin(dep_time, params.dep_from, params.dep_to): continue

        total, badges = _build_extras(float(price_val) + ret_price, params)
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
                "origin": origin, "destination": dest,
                "outbound_date": params.outbound_date, "return_date": params.return_date,
                "adults": params.adults, "children": params.children,
                "baggage": params.baggage, "baggage_10kg": params.baggage_10kg,
                "baggage_20kg": params.baggage_20kg, "baggage_23kg": params.baggage_23kg,
                "seat": params.seat, "seat_cost": params.seat_cost,
                "departure_time": dep_time, "arrival_time": arr_time,
                "flight_number": flight_num, "airline": "Ryanair", "stops": 0,
            },
            "_tracker_type": "flight", "_tracker_table": "trackers",
        })

    cheapest = min((r["price"] for r in results), default=0)
    logger.info(f"[RYANAIR] ✈️ status=ok | found={len(results)} | cheapest={cheapest:.2f} EUR | elapsed={elapsed}s")
    return results
