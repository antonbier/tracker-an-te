"""
WanderSuite — routes/search.py  (Meta-Suche Router)

Strategy Pattern: Jede Kategorie feuert ALLE relevanten Provider
gleichzeitig via asyncio.gather ab. Fällt ein Provider aus, bleiben
die anderen unbeeinträchtigt (return_exceptions=True).

Endpoints:
  POST /api/search/flights  — Ryanair + Google Flights parallel (via Orchestrator)
  POST /api/search/hotels   — SerpAPI Google Hotels
  POST /api/search/camping  — SerpAPI Camping/Homair

Provider-Logik ist in separate Module ausgelagert:
  search_shared.py   — Shared types, constants, helpers (_aggregate, _calc_nights …)
  search_flights.py  — Ryanair + Google Flights (_search_ryanair, _search_google_flights)
  search_hotels.py   — SerpAPI Hotels (_search_hotels_serpapi)
  search_camping.py  — SerpAPI Camping (_search_camping_serpapi)
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from auth_jwt import get_current_user
from settings_manager import get_setting_value
from flight_search_orchestrator import (
    search_flights as orchestrate_flights,
    FlightSearchParams as OrchestratorParams,
)

from .search_shared import (
    FlightSearchParams,
    HotelSearchParams,
    CampingSearchParams,
    _aggregate,
)
from .search_flights import _search_ryanair, _search_google_flights
from .search_hotels  import _search_hotels_serpapi
from .search_camping import _search_camping_serpapi

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/flights")
async def search_flights(
    params: FlightSearchParams,
    user: dict = Depends(get_current_user),
):
    """
    Meta-Suche Flüge via Orchestrator.
    Aktive Provider werden aus der DB gelesen (GET /api/settings/providers).
    """
    if not params.origin or not params.destination or not params.outbound_date:
        raise HTTPException(400, "origin, destination und outbound_date sind Pflichtfelder")

    params.origin      = params.origin.strip().upper()
    params.destination = params.destination.strip().upper()

    logger.info(
        f"[SEARCH] ✈️ flights {params.origin}->{params.destination} "
        f"{params.outbound_date} | adults={params.adults} | via orchestrator"
    )

    orch_params = OrchestratorParams(**params.model_dump())
    return await orchestrate_flights(orch_params)


@router.post("/hotels")
async def search_hotels(
    params: HotelSearchParams,
    user: dict = Depends(get_current_user),
):
    """Meta-Suche Hotels: SerpAPI Google Hotels."""
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

    raw = await asyncio.gather(
        _search_hotels_serpapi(params, serpapi_key),
        return_exceptions=True,
    )
    results, missing_keys = _aggregate(list(raw))
    logger.info(f"[SEARCH] 🏨 hotels total_results={len(results)}")
    return {"results": results, "count": len(results), "missing_api_keys": missing_keys}


@router.post("/camping")
async def search_camping(
    params: CampingSearchParams,
    user: dict = Depends(get_current_user),
):
    """Meta-Suche Camping: SerpAPI Camping/Homair-Query."""
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
        f"type={params.accommodation_type} bedrooms={params.bedrooms}"
    )

    raw = await asyncio.gather(
        _search_camping_serpapi(params, serpapi_key),
        return_exceptions=True,
    )
    results, missing_keys = _aggregate(list(raw))
    logger.info(f"[SEARCH] ⛺ camping total_results={len(results)}")
    return {"results": results, "count": len(results), "missing_api_keys": missing_keys}
