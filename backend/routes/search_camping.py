"""
WanderSuite — search_camping.py
SerpAPI Camping/Homair Suchanbieter.
Wird aufgerufen von: routes/search.py (POST /api/search/camping)
"""

import asyncio
import logging

import httpx

from .search_shared import (
    CampingSearchParams,
    HEADERS_SERPAPI, SERPAPI_BASE, TIMEOUT,
    _calc_nights, _extract_price,
)

logger = logging.getLogger(__name__)

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


