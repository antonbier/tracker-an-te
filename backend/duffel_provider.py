"""
WanderSuite — Duffel Provider

Duffel Offers API — GDS-Daten, vollständiger Tagesplan, buchbar.
Test-Mode: duffel_test_... Key → simulierte Preise (werden mit 🧪 markiert).
Prod-Mode: duffel_live_... Key → echte Preise, echte Buchungen.

SDK: pip install duffel-api (optional — wir nutzen direkten REST-Call)
Docs: https://duffel.com/docs/api
"""

import logging
import time
import httpx
from flight_search_orchestrator import FlightSearchParams

logger = logging.getLogger(__name__)
TIMEOUT = 25.0  # Duffel ist etwas langsamer (GDS lookup)
BASE_URL = "https://api.duffel.com"


async def search(params: FlightSearchParams, cfg: dict) -> list[dict]:
    api_key = cfg.get("api_key") or ""
    if not api_key:
        logger.warning("[DUFFEL] status=skip | reason=no_api_key")
        return [{"_api_key_missing": True, "provider": "Duffel"}]

    is_test = api_key.startswith("duffel_test_") or cfg.get("test_mode", False)
    t0 = time.time()

    try:
        headers = {
            "Authorization":       f"Bearer {api_key}",
            "Accept":              "application/json",
            "Content-Type":        "application/json",
            "Duffel-Version":      "v2",
            "Accept-Encoding":     "gzip",
        }

        # Build Offer Request payload
        slices = [{
            "origin":      params.origin.upper(),
            "destination": params.destination.upper(),
            "departure_date": params.outbound_date,
        }]
        if params.return_date:
            slices.append({
                "origin":      params.destination.upper(),
                "destination": params.origin.upper(),
                "departure_date": params.return_date,
            })

        passengers = [{"type": "adult"} for _ in range(params.adults)]
        passengers += [{"type": "child"} for _ in range(params.children)]

        payload = {
            "data": {
                "slices":     slices,
                "passengers": passengers,
                "cabin_class": "economy",
            }
        }

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Step 1: Create Offer Request
            resp = await client.post(
                f"{BASE_URL}/air/offer_requests?return_offers=true",
                json=payload, headers=headers,
            )
            if resp.status_code == 401:
                logger.error("[DUFFEL] status=unauthorized | invalid api_key")
                return [{"_api_key_missing": True, "provider": "Duffel"}]
            if resp.status_code == 422:
                logger.warning(f"[DUFFEL] status=422 | {resp.text[:200]}")
                return []
            resp.raise_for_status()
            data = resp.json()

        elapsed = round(time.time() - t0, 1)
        offers = data.get("data", {}).get("offers", [])

        if not offers:
            logger.info(f"[DUFFEL] status=no_offers | elapsed={elapsed}s")
            return []

        results = []
        total_pax = params.adults + params.children

        for offer in offers[:8]:
            try:
                price = float(offer.get("total_amount", 0))
                currency = offer.get("total_currency", "EUR")
                slices_data = offer.get("slices", [])
                if not slices_data: continue

                first_slice = slices_data[0]
                segs = first_slice.get("segments", [])
                if not segs: continue

                first_seg = segs[0]
                last_seg  = segs[-1]
                airline   = first_seg.get("marketing_carrier", {}).get("name", "")
                flight_num = (
                    first_seg.get("marketing_carrier_flight_number", "") or
                    first_seg.get("operating_carrier_flight_number", "")
                )
                dep_time  = _fmt_duffel_time(first_seg.get("departing_at", ""))
                arr_time  = _fmt_duffel_time(last_seg.get("arriving_at", ""))
                n_stops   = len(segs) - 1
                duration_min = first_slice.get("duration")  # ISO8601 → convert
                if duration_min:
                    duration_min = _parse_iso_duration(duration_min)

                if params.max_stops >= 0 and n_stops > params.max_stops: continue

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

                lay_airports = [
                    seg.get("destination", {}).get("iata_code", "")
                    for seg in segs[:-1]
                    if seg.get("destination", {}).get("iata_code")
                ]

                # Baggage extras
                bag = 0.0
                if params.baggage_10kg > 0: bag += params.baggage_10kg * 22.99
                elif params.baggage == "10kg": bag = 22.99 * total_pax
                if params.baggage_20kg > 0: bag += params.baggage_20kg * 34.99
                elif params.baggage == "20kg" and params.baggage_10kg == 0: bag = 34.99 * total_pax
                if params.baggage_23kg > 0: bag += params.baggage_23kg * 42.99
                scp = params.seat_cost if params.seat_cost > 0 else (8.99 if params.seat else 0.0)
                total = round(price + bag + scp * total_pax, 2)

                badges = [f"🟣 {'Nonstop' if n_stops == 0 else str(n_stops) + ' Stopp'}"]
                if is_test: badges.insert(0, "🧪 Testpreise")
                if params.baggage_10kg > 0: badges.append(f"🎒 {params.baggage_10kg}x 10kg")

                results.append({
                    "id":       f"df-{params.origin}-{params.destination}-{params.outbound_date}-{len(results)}",
                    "provider": "Duffel" + (" (Test)" if is_test else ""),
                    "title":    f"{params.origin.upper()} → {params.destination.upper()}",
                    "subtitle": f"{params.outbound_date} · {airline} · {dep_time}→{arr_time}",
                    "price":    total, "currency": currency,
                    "badges":   badges,
                    "booking_url": f"https://app.duffel.com",
                    "_test_mode": is_test,
                    "detail": {
                        "origin": params.origin.upper(), "destination": params.destination.upper(),
                        "outbound_date": params.outbound_date, "return_date": params.return_date,
                        "adults": params.adults, "children": params.children,
                        "baggage": params.baggage, "baggage_10kg": params.baggage_10kg,
                        "baggage_20kg": params.baggage_20kg, "baggage_23kg": params.baggage_23kg,
                        "seat": params.seat, "seat_cost": params.seat_cost,
                        "airline": airline, "departure_time": dep_time, "arrival_time": arr_time,
                        "duration_min": duration_min, "stops": n_stops,
                        "layover_airports": lay_airports, "layover_durations": [],
                        "flight_number": flight_num, "duffel_offer_id": offer.get("id"),
                        "test_mode": is_test,
                    },
                    "_tracker_type": "google_flight", "_tracker_table": "gf_trackers",
                })
            except Exception as e:
                logger.warning(f"[DUFFEL] offer parse error: {e}")
                continue

        cheapest = min((r["price"] for r in results), default=0)
        mode = "TEST" if is_test else "LIVE"
        logger.info(f"[DUFFEL] [{mode}] status=ok | found={len(results)} | cheapest={cheapest:.2f} EUR | elapsed={elapsed}s")
        return results

    except httpx.TimeoutException:
        logger.warning(f"[DUFFEL] status=timeout | elapsed={round(time.time()-t0,1)}s")
        return []
    except Exception as e:
        logger.error(f"[DUFFEL] status=error | error={e}")
        return []


def _fmt_duffel_time(iso: str) -> str:
    if not iso: return ""
    try:
        if "T" in iso: return iso.split("T")[1][:5]
    except Exception: pass
    return ""


def _parse_iso_duration(iso: str) -> int | None:
    """PT14H30M → 870 minutes"""
    import re
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", iso or "")
    if not m: return None
    h = int(m.group(1) or 0)
    mins = int(m.group(2) or 0)
    return h * 60 + mins
