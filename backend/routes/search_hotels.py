"""
WanderSuite — search_hotels.py
SerpAPI Google Hotels Suchanbieter.
Wird aufgerufen von: routes/search.py (POST /api/search/hotels)
"""

import asyncio
import logging

import httpx

from .search_shared import (
    HotelSearchParams,
    HEADERS_SERPAPI, SERPAPI_BASE, TIMEOUT,
    _calc_nights, _extract_price,
)

logger = logging.getLogger(__name__)

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


