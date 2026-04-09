"""
WanderSuite — Kiwi Tequila Provider

Kiwi Tequila API (v2) — liefert MEHRERE Flüge pro Tag inkl. LCCs (Ryanair, Wizz, etc.)
API-Key: https://tequila.kiwi.com/ (kostenlos bis 500 req/month)

Vorteile gegenüber Ryanair Native:
  - Mehrere Abflugzeiten pro Tag (voller Tagesplan)
  - Alle Airlines inkl. Ryanair mit echten Preisen
  - Stopps/Layovers vollständig abgebildet
"""

import logging
import time
import httpx
from flight_search_orchestrator import FlightSearchParams

logger = logging.getLogger(__name__)
TIMEOUT = 18.0
BASE_URL = "https://tequila-api.kiwi.com"


async def search(params: FlightSearchParams, cfg: dict) -> list[dict]:
    api_key = cfg.get("api_key") or ""
    if not api_key:
        logger.warning("[KIWI] status=skip | reason=no_api_key")
        return [{"_api_key_missing": True, "provider": "Kiwi"}]

    t0 = time.time()
    try:
        req_params = {
            "fly_from":        params.origin.upper(),
            "fly_to":          params.destination.upper(),
            "date_from":       params.outbound_date.replace("-", "/")[5:] + "/" + params.outbound_date[:4]
                               if "-" in params.outbound_date else params.outbound_date,
            "date_to":         params.outbound_date.replace("-", "/")[5:] + "/" + params.outbound_date[:4]
                               if "-" in params.outbound_date else params.outbound_date,
            "adults":          params.adults,
            "children":        params.children,
            "curr":            "EUR",
            "locale":          "de",
            "limit":           10,
            "sort":            "price",
            "asc":             1,
            "one_per_date":    0,  # 0 = mehrere Flüge pro Tag (Kiwi v2 korrekte param)
        }

        # Kiwi date format: DD/MM/YYYY
        from datetime import datetime
        def _kiwi_date(iso: str) -> str:
            d = datetime.strptime(iso, "%Y-%m-%d")
            return d.strftime("%d/%m/%Y")

        req_params["date_from"] = _kiwi_date(params.outbound_date)
        req_params["date_to"]   = _kiwi_date(params.outbound_date)

        if params.return_date:
            req_params["return_from"] = _kiwi_date(params.return_date)
            req_params["return_to"]   = _kiwi_date(params.return_date)

        if params.max_stops >= 0:
            req_params["max_stopovers"] = params.max_stops

        # Time filters
        if params.dep_from: req_params["dtime_from"] = params.dep_from
        if params.dep_to:   req_params["dtime_to"]   = params.dep_to
        if params.arr_from: req_params["atime_from"]  = params.arr_from
        if params.arr_to:   req_params["atime_to"]    = params.arr_to

        headers = {
            "apikey": api_key,
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(f"{BASE_URL}/v2/search", params=req_params, headers=headers)
            if resp.status_code in (401, 403):
                logger.error(f"[KIWI] status=unauthorized | http={resp.status_code} | {resp.text[:100]}")
                return [{"_api_key_missing": True, "provider": "Kiwi"}]
            resp.raise_for_status()
            data = resp.json()

        elapsed = round(time.time() - t0, 1)
        flights = data.get("data", [])
        results = []

        total_pax = params.adults + params.children

        for fl in flights[:8]:
            price = fl.get("price")
            if not price: continue

            # Kiwi response structure
            route = fl.get("route", [])
            first_leg = route[0] if route else {}
            last_leg  = route[-1] if route else {}

            dep_time = _fmt_time(first_leg.get("local_departure", ""))
            arr_time = _fmt_time(last_leg.get("local_arrival", ""))
            # Kiwi: "airline" = IATA code (e.g. "FR"), "airline_name" = full name
            airline_code = first_leg.get("airline", "")
            airline      = first_leg.get("airline_name", "") or airline_code
            flight_num   = f"{airline_code}{first_leg.get('flight_no', '')}".strip()
            n_stops  = max(len(route) - 1, 0)
            # Kiwi: duration.departure is in SECONDS
            _dur_raw = fl.get("duration", {}).get("departure") if fl.get("duration") else None
            duration_min = int(_dur_raw // 60) if _dur_raw else None

            # Layover airports (intermediate stops)
            lay_airports = [
                leg.get("flyFrom", "") for leg in route[1:]
                if leg.get("flyFrom")
            ]
            # Kiwi doesn't give layover durations directly — compute from consecutive legs
            lay_durations = []
            for i in range(len(route) - 1):
                try:
                    from datetime import datetime
                    arr_prev = datetime.fromisoformat(route[i]["utc_arrival"])
                    dep_next = datetime.fromisoformat(route[i+1]["utc_departure"])
                    diff_min = int((dep_next - arr_prev).total_seconds() / 60)
                    lay_durations.append(diff_min)
                except Exception:
                    lay_durations.append(None)

            # Add baggage/seat extras
            bag = 0.0
            if params.baggage_10kg > 0: bag += params.baggage_10kg * 22.99
            elif params.baggage == "10kg": bag = 22.99 * total_pax
            if params.baggage_20kg > 0: bag += params.baggage_20kg * 34.99
            elif params.baggage == "20kg" and params.baggage_10kg == 0: bag = 34.99 * total_pax
            if params.baggage_23kg > 0: bag += params.baggage_23kg * 42.99
            scp = params.seat_cost if params.seat_cost > 0 else (8.99 if params.seat else 0.0)
            total = round(float(price) + bag + scp * total_pax, 2)

            badges = [f"🟢 {'Nonstop' if n_stops == 0 else str(n_stops) + ' Stopp'}"]
            if params.baggage_10kg > 0: badges.append(f"🎒 {params.baggage_10kg}x 10kg")
            if params.baggage_20kg > 0: badges.append(f"🎒 {params.baggage_20kg}x 20kg")
            if params.baggage_23kg > 0: badges.append(f"🧳 {params.baggage_23kg}x 23kg")

            results.append({
                "id":       f"kw-{params.origin}-{params.destination}-{params.outbound_date}-{len(results)}",
                "provider": "Kiwi",
                "title":    f"{params.origin.upper()} → {params.destination.upper()}",
                "subtitle": f"{params.outbound_date} · {airline} · {dep_time}→{arr_time}",
                "price":    total, "currency": "EUR",
                "badges":   badges,
                "booking_url": fl.get("deep_link", "https://www.kiwi.com"),
                "detail": {
                    "origin": params.origin.upper(), "destination": params.destination.upper(),
                    "outbound_date": params.outbound_date, "return_date": params.return_date,
                    "adults": params.adults, "children": params.children,
                    "baggage": params.baggage, "baggage_10kg": params.baggage_10kg,
                    "baggage_20kg": params.baggage_20kg, "baggage_23kg": params.baggage_23kg,
                    "seat": params.seat, "seat_cost": params.seat_cost,
                    "airline": airline, "departure_time": dep_time, "arrival_time": arr_time,
                    "duration_min": duration_min, "stops": n_stops,
                    "layover_airports": lay_airports, "layover_durations": lay_durations,
                    "flight_number": flight_num,
                },
                "_tracker_type": "google_flight", "_tracker_table": "gf_trackers",
            })

        cheapest = min((r["price"] for r in results), default=0)
        logger.info(f"[KIWI] status=ok | found={len(results)} | cheapest={cheapest:.2f} EUR | elapsed={elapsed}s")
        return results

    except httpx.TimeoutException:
        logger.warning(f"[KIWI] status=timeout | elapsed={round(time.time()-t0,1)}s")
        return []
    except Exception as e:
        logger.error(f"[KIWI] status=error | error={e}")
        return []


def _fmt_time(iso: str) -> str:
    if not iso: return ""
    try:
        if "T" in iso: return iso.split("T")[1][:5]
        if " " in iso: return iso.split(" ")[1][:5]
    except Exception: pass
    return ""

