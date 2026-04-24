"""
WanderSuite — Flight Search Orchestrator

Zentrale Schnittstelle für alle Flug-Provider.
Liest aktive Provider aus der DB, ruft sie parallel via asyncio.gather ab
und aggregiert die Ergebnisse.

Provider-Registry:
  ryanair_native  — Ryanair farfnd/cheapestPerDay (kein Key nötig)
  google_flights  — SerpAPI Google Flights (serpapi_key)
  kiwi            — Kiwi Tequila API (kiwi_api_key)
  duffel          — Duffel Offers API (duffel_api_key, test_mode flag)

Neuen Provider hinzufügen:
  1. Datei backend/<name>_provider.py erstellen mit async search(params, cfg) -> list[dict]
  2. Eintrag in PROVIDER_REGISTRY unten hinzufügen
  3. In DB provider_configs einen Row anlegen (via init_provider_configs)
"""

import asyncio
import logging
from typing import Optional
from pydantic import BaseModel

from settings_manager import get_setting_value
from crud.trackers import get_provider_configs

logger = logging.getLogger(__name__)


# ── Shared search params model ─────────────────────────────────────────────

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


# ── Provider registry ──────────────────────────────────────────────────────

# Lazy imports — only load a provider module when it is actually called.
# This prevents import errors from crashing the whole app if a provider's
# optional dependency (e.g. duffel-api-python) is not installed yet.

async def _run_ryanair(params: FlightSearchParams, cfg: dict) -> list[dict]:
    from ryanair_provider import search as ryanair_search
    return await ryanair_search(params, cfg)

async def _run_google_flights(params: FlightSearchParams, cfg: dict) -> list[dict]:
    from google_flights_provider import search as gf_search
    return await gf_search(params, cfg)

async def _run_kiwi(params: FlightSearchParams, cfg: dict) -> list[dict]:
    from kiwi_provider import search as kiwi_search
    return await kiwi_search(params, cfg)

async def _run_duffel(params: FlightSearchParams, cfg: dict) -> list[dict]:
    from duffel_provider import search as duffel_search
    return await duffel_search(params, cfg)


PROVIDER_REGISTRY: dict[str, callable] = {
    "ryanair_native": _run_ryanair,
    "google_flights":  _run_google_flights,
    "kiwi":            _run_kiwi,
    "duffel":          _run_duffel,
}


# ── Orchestrator ───────────────────────────────────────────────────────────

async def search_flights(params: FlightSearchParams) -> dict:
    """
    Haupteinstiegspunkt für alle Flugsuchen.
    Liest aktive Provider aus der DB, ruft sie parallel ab,
    aggregiert und sortiert nach Preis.
    """
    # Load provider configs from DB
    configs = get_provider_configs()  # -> list[dict] with keys: id, name, enabled, api_key, test_mode

    # Build list of (name, cfg) for enabled providers
    active = [c for c in configs if c.get("enabled")]

    if not active:
        logger.warning("[ORCHESTRATOR] Keine aktiven Provider konfiguriert")
        return {"results": [], "count": 0, "missing_api_keys": [], "providers_used": []}

    # Load global settings fallbacks (e.g. serpapi_key for google_flights)
    try:
        from settings_manager import get_setting_value
        _serpapi_key = get_setting_value("serpapi_key") or ""
    except Exception:
        _serpapi_key = ""

    # Build coroutine tasks — only for providers in the registry
    tasks = []
    names = []
    for cfg in active:
        name = cfg["name"]
        runner = PROVIDER_REGISTRY.get(name)
        if not runner:
            logger.warning(f"[ORCHESTRATOR] Unbekannter Provider: {name} — übersprungen")
            continue
        # Enrich cfg with global settings fallbacks
        enriched_cfg = dict(cfg)
        if name == "google_flights" and not enriched_cfg.get("api_key"):
            enriched_cfg["api_key"] = _serpapi_key
        tasks.append(runner(params, enriched_cfg))
        names.append(name)

    if not tasks:
        return {"results": [], "count": 0, "missing_api_keys": [], "providers_used": []}

    logger.info(f"[ORCHESTRATOR] Starte {len(tasks)} Provider parallel: {names}")
    raw = await asyncio.gather(*tasks, return_exceptions=True)

    # Aggregate results
    flat = []
    missing_keys = []
    for name, result in zip(names, raw):
        if isinstance(result, Exception):
            logger.error(f"[ORCHESTRATOR] Provider {name} Exception: {result}")
            continue
        if isinstance(result, list):
            for item in result:
                if item.get("_api_key_missing"):
                    missing_keys.append(item.get("provider", name))
                else:
                    flat.append(item)
        elif isinstance(result, dict) and result.get("_api_key_missing"):
            missing_keys.append(result.get("provider", name))

    # Sort by price ascending
    flat.sort(key=lambda x: x.get("price") or float("inf"))

    logger.info(f"[ORCHESTRATOR] Gesamt: {len(flat)} Ergebnisse | missing_keys={missing_keys}")
    return {
        "results":          flat,
        "count":            len(flat),
        "missing_api_keys": missing_keys,
        "providers_used":   names,
    }

