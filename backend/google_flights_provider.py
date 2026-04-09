"""
WanderSuite — Google Flights Provider (SerpAPI)

Benötigt: serpapi_key in cfg oder global settings.
"""

import logging
import time
import httpx
from flight_search_orchestrator import FlightSearchParams
from settings_manager import get_setting_value

logger = logging.getLogger(__name__)
TIMEOUT = 18.0
SERPAPI_BASE = "https://serpapi.com/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


async def search(params: FlightSearchParams, cfg: dict) -> list[dict]:
    api_key = cfg.get("api_key") or get_setting_value("serpapi_key") or ""
    if not api_key:
        logger.warning("[GF] status=skip | reason=no_api_key")
        return [{"_api_key_missing": True, "provider": "Google Flights"}]

    t0 = time.time()
    try:
        req_params = {
            "engine": "google_flights",
            "departure_id": params.origin.upper(),
            "arrival_id": params.destination.upper(),
            "outbound_date": params.outbound_date,
            "currency": "EUR", "hl": "de",
            "adults": params.adults, "children": params.children,
            "api_key": api_key,
            "type": "1" if params.return_date else "2",
        }
        if params.return_date:
            req_params["return_date"] = params.return_date
        if params.max_stops >= 0:
            req_params["stops"] = params.max_stops

        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
            resp = await client.get(SERPAPI_BASE, params=req_params)
            resp.raise_for_status()
            data = resp.json()

        elapsed = round(time.time() - t0, 1)
        all_flights = data.get("best_flights", []) or data.get("other_flights", [])
        results = []

        for fl in all_flights[:5]:
            legs = fl.get("flights", [{}])
            leg  = legs[0] if legs else {}
            price = fl.get("price")
            if not price: continue

            airline = leg.get("airline", "")
            if "ryanair" in airline.lower():
                continue  # covered by Ryanair provider

            dep = leg.get("departure_airport", {})
            arr = leg.get("arrival_airport", {})
            n_stops = len(fl.get("flights", [])) - 1
            if params.max_stops >= 0 and n_stops > params.max_stops: continue

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

            total_pax = params.adults + params.children
            extra = (params.baggage_10kg * 22.99 + params.baggage_20kg * 34.99 + params.baggage_23kg * 42.99)
            if params.baggage == "10kg" and params.baggage_10kg == 0: extra += 22.99 * total_pax
            elif params.baggage == "20kg" and params.baggage_20kg == 0: extra += 34.99 * total_pax
            scp = params.seat_cost if params.seat_cost > 0 else (8.99 if params.seat else 0.0)
            extra += scp * total_pax
            adj_price = round(float(price) + extra, 2)

            lay_airports = [
                leg2.get("departure_airport", {}).get("id", "")
                for leg2 in fl.get("flights", [])[1:]
                if leg2.get("departure_airport", {}).get("id")
            ]
            lay_durations = [
                lay.get("duration") for lay in fl.get("layovers", [])
                if lay.get("duration") is not None
            ]

            results.append({
                "id": f"gf-{params.origin}-{params.destination}-{params.outbound_date}-{len(results)}",
                "provider": "Google Flights",
                "title": f"{params.origin.upper()} → {params.destination.upper()}",
                "subtitle": f"{params.outbound_date} · {airline} · {dep_t}→{arr_t}",
                "price": adj_price, "currency": "EUR",
                "badges": [f"🔵 {'Nonstop' if n_stops == 0 else str(n_stops) + ' Stopp'}"],
                "booking_url": f"https://www.google.com/flights#search;f={params.origin.upper()};t={params.destination.upper()};d={params.outbound_date}",
                "detail": {
                    "origin": params.origin.upper(), "destination": params.destination.upper(),
                    "outbound_date": params.outbound_date, "return_date": params.return_date,
                    "adults": params.adults, "children": params.children,
                    "baggage": params.baggage, "baggage_10kg": params.baggage_10kg,
                    "baggage_20kg": params.baggage_20kg, "baggage_23kg": params.baggage_23kg,
                    "seat": params.seat, "seat_cost": params.seat_cost,
                    "airline": airline, "departure_time": dep_t, "arrival_time": arr_t,
                    "duration_min": fl.get("total_duration"), "stops": n_stops,
                    "layover_airports": lay_airports, "layover_durations": lay_durations,
                },
                "_tracker_type": "google_flight", "_tracker_table": "gf_trackers",
            })

        cheapest = min((r["price"] for r in results), default=0)
        logger.info(f"[GF] status=ok | found={len(results)} | cheapest={cheapest:.2f} EUR | elapsed={elapsed}s")
        return results

    except httpx.TimeoutException:
        logger.warning(f"[GF] status=timeout | elapsed={round(time.time()-t0,1)}s")
        return []
    except Exception as e:
        logger.error(f"[GF] status=error | error={e}")
        return []
