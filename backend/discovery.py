"""
WanderSuite — DiscoveryService (refactored)

Pipeline:
  1. TravelPersonality + TravelDefaults laden
  2. Dawarich-History laden
  3. Pool aus SQLite bedienen (get_suggestions)
  4. Hintergrund-Refresh: LLM → parallel Bild-Anreicherung → Pool schreiben

Fixes in dieser Version:
  - asyncio.gather für parallele Bild-Pipeline
  - Alle httpx.AsyncClient: trust_env=False, timeout=25.0
  - Proxy-URL-Erzeugung in _get_image() statt in routes/
  - Unsplash-URLs ebenfalls durch Image-Proxy geschleust
  - _load_visited() wird nicht mehr doppelt aufgerufen
  - Smart History Toggle: blacklist | context
  - travel_mode + max_travel_time in LLM-Prompt integriert
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import quote

import httpx

from discovery_models import TravelPersonality, TravelDefaults
from settings_manager import get_user_setting_value, get_setting_value
from database import (
    list_detected_trips,
    discovery_pool_get_unseen,
    discovery_pool_upsert,
    discovery_pool_rotate,
    discovery_pool_count,
    DISCOVERY_POOL_REFILL_THRESHOLD,
)

logger = logging.getLogger(__name__)

TIMEOUT = 25.0


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class Suggestion:
    destination:  str
    reason:       str
    image_url:    Optional[str]
    image_source: str          # immich | unsplash | css_fallback
    prefill:      dict = field(default_factory=dict)


# ── DiscoveryService ──────────────────────────────────────────────────────────

class DiscoveryService:

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_suggestions(self, user_id: int, count: int = 3) -> list[Suggestion]:
        """Liefert `count` Vorschläge — primär aus Pool, triggert Refresh wenn nötig."""
        _, unseen = discovery_pool_count(user_id)

        # Hintergrund-Refresh anstoßen wenn Pool fast leer
        if unseen < DISCOVERY_POOL_REFILL_THRESHOLD:
            asyncio.create_task(self.background_refresh_suggestions(user_id, batch=6))

        rows = discovery_pool_get_unseen(user_id, limit=count)

        # Pool war komplett leer → synchron warten
        if not rows:
            await self.background_refresh_suggestions(user_id, batch=count)
            rows = discovery_pool_get_unseen(user_id, limit=count)

        suggestions = []
        for r in rows:
            try:
                prefill = json.loads(r.get("prefill_json") or "{}")
            except Exception:
                prefill = {}
            suggestions.append(Suggestion(
                destination=r["destination"],
                reason=r["reason"],
                image_url=r.get("image_url"),
                image_source=r.get("image_source", "css_fallback"),
                prefill=prefill,
            ))
        return suggestions

    async def background_refresh_suggestions(self, user_id: int, batch: int = 6) -> int:
        """LLM-Call + parallele Bild-Anreicherung → Pool befüllen.
        Returns number of new entries inserted."""
        personality = self._load_personality(user_id)
        defaults = self._load_defaults(user_id)
        visited = self._load_visited(user_id)

        raw_suggestions = await self._llm_suggest(personality, visited, batch)
        if not raw_suggestions:
            return 0

        # Parallele Bild-Anreicherung
        tasks = [
            self._get_image(user_id, defaults, visited, r.get("destination", ""))
            for r in raw_suggestions
        ]
        images = await asyncio.gather(*tasks, return_exceptions=True)

        inserted = 0
        for raw, img_result in zip(raw_suggestions, images):
            dest = raw.get("destination", "")
            if not dest:
                continue
            if isinstance(img_result, Exception):
                image_url, image_source = None, "css_fallback"
            else:
                image_url, image_source = img_result

            entry = {
                "destination":  dest,
                "country":      raw.get("country", ""),
                "reason":       raw.get("reason", ""),
                "climate":      raw.get("climate"),
                "landscape":    raw.get("landscape"),
                "trip_type":    raw.get("trip_type"),
                "image_url":    image_url,
                "image_source": image_source,
                "prefill":      self._build_prefill(defaults, raw),
            }
            if discovery_pool_upsert(user_id, entry):
                inserted += 1

        discovery_pool_rotate(user_id)
        logger.info(f"[Discovery] Pool refresh: {inserted} new entries for user={user_id}")
        return inserted

    async def get_trip_image(self, user_id: int, destination: str) -> tuple[Optional[str], str]:
        """Bild-Pipeline ohne LLM — für HeroSection Nostalgie-Bild."""
        defaults = self._load_defaults(user_id)
        visited = self._load_visited(user_id)
        return await self._get_image(user_id, defaults, visited, destination)

    async def get_destination_detail(self, user_id: int, destination: str, country: str = "") -> dict:
        """Full detail: LLM description + things_to_do + multiple images (mit Proxy)."""
        personality = self._load_personality(user_id)
        defaults = self._load_defaults(user_id)

        dest_label = f"{destination}, {country}" if country else destination
        system = ("Du bist ein Reise-Experte. Antworte NUR als JSON-Objekt. "
                  "Kein Markdown, keine Erklärung.")
        user_msg = (
            f"Beschreibe das Reiseziel '{dest_label}' detailliert. "
            f"Nutzer-Profil: Reisestil={personality.travel_style or '?'}, "
            f"Klima={personality.climate_pref or '?'}, "
            f"Begleitung={personality.companions or '?'}. "
            "Antworte als JSON mit: "
            "description (3-4 Saetze warum ideal fuer dieses Profil), "
            "things_to_do (Array mit 5-7 Aktivitaeten als kurze Strings), "
            "best_season (Fruehling/Sommer/Herbst/Winter oder Kombination), "
            "vibe (2-3 Adjektive)"
        )

        llm_provider = get_setting_value("llm_provider") or "openai"
        raw_list = []
        if llm_provider == "gemini":
            raw_list = await self._gemini_call(system, user_msg)
            if not raw_list:
                raw_list = await self._openai_call(system, user_msg)
        else:
            raw_list = await self._openai_call(system, user_msg)
            if not raw_list:
                raw_list = await self._gemini_call(system, user_msg)

        detail_raw = raw_list[0] if raw_list and isinstance(raw_list[0], dict) else {}

        # Mehrere Bilder parallel laden
        images = await self._get_multiple_images(user_id, defaults, destination, count=4)

        return {
            "destination":  destination,
            "country":      country,
            "description":  detail_raw.get("description", ""),
            "things_to_do": detail_raw.get("things_to_do", []),
            "best_season":  detail_raw.get("best_season", ""),
            "vibe":         detail_raw.get("vibe", ""),
            "images":       images,
        }

    # ── Settings laden ────────────────────────────────────────────────────────

    def _load_personality(self, user_id: int) -> TravelPersonality:
        keys = ["travel_style", "climate_pref", "landscape_pref",
                "companions", "wish_text", "history_mode",
                "travel_mode", "max_travel_time"]
        data = {}
        for k in keys:
            try:
                data[k] = get_user_setting_value(user_id, k) or ""
            except Exception:
                data[k] = ""
        return TravelPersonality(
            travel_style=data["travel_style"],
            climate_pref=data["climate_pref"],
            landscape_pref=data["landscape_pref"],
            companions=data["companions"],
            wish_text=data["wish_text"],
            history_mode=data["history_mode"] or "blacklist",
            travel_mode=data["travel_mode"] or "flight",
            max_travel_time=data["max_travel_time"] or "any",
        )

    def _load_defaults(self, user_id: int) -> TravelDefaults:
        keys = ["ww_home_airport", "home_lat", "home_lon",
                "ww_adults", "ww_children", "unsplash_key",
                "immich_url", "immich_api_key"]
        data = {}
        for k in keys:
            try:
                data[k] = get_user_setting_value(user_id, k) or ""
            except Exception:
                data[k] = ""
        return TravelDefaults(
            home_airport=data["ww_home_airport"],
            home_lat=data["home_lat"],
            home_lon=data["home_lon"],
            adults=int(data["ww_adults"] or 2),
            children=int(data["ww_children"] or 0),
            unsplash_key=data["unsplash_key"],
            immich_url=data["immich_url"].rstrip("/"),
            immich_api_key=data["immich_api_key"],
        )

    def _load_visited(self, user_id: int) -> list[str]:
        try:
            trips = list_detected_trips(user_id=user_id, limit=5)
            names = []
            for t in trips:
                name = t.get("location_name") or t.get("country") or ""
                if name and name not in names:
                    names.append(name)
            return names[:5]
        except Exception as e:
            logger.warning(f"[Discovery] Failed to load visited trips: {e}")
            return []

    # ── LLM ──────────────────────────────────────────────────────────────────

    def _build_prompt(self, personality: TravelPersonality,
                      visited: list[str], count: int) -> str:
        visited_str = ", ".join(visited) if visited else "keine"

        # History-Modus
        if personality.history_mode == "context" and visited:
            history_block = (
                f"  Bereits bereiste Orte (als Kontext nutzen, NICHT nochmals vorschlagen): {visited_str}\n"
                f"  → Leite daraus neue, unbesuchte Ziele ab, die zum gleichen Reiseprofil passen."
            )
        else:
            history_block = f"  Bereits besucht (nicht vorschlagen): {visited_str}"

        # Mobilitäts-Block
        mode = personality.travel_mode
        max_time = personality.max_travel_time
        if mode == "car":
            if max_time == "any":
                mobility_block = "  Reiseart: Auto — keine Zeitbeschränkung."
            else:
                mobility_block = (
                    f"  Reiseart: Auto — maximale Fahrtzeit {max_time}. "
                    f"Schlage NUR Ziele vor, die per Auto in maximal {max_time} erreichbar sind "
                    f"(ausgehend von den Heimatkoordinaten lat={personality.travel_style or '?'})."
                )
        else:
            if max_time == "any":
                mobility_block = "  Reiseart: Flug — keine Flugzeitbeschränkung."
            else:
                mobility_block = (
                    f"  Reiseart: Flug — maximale Flugzeit {max_time}. "
                    f"Schlage NUR Ziele vor, die per Direktflug oder mit max. 1 Umstieg "
                    f"in {max_time} erreichbar sind."
                )

        return f"""Schlage {count} Reiseziele vor.
Nutzer-Profil:
  Reisestil: {personality.travel_style or 'nicht angegeben'}
  Klima: {personality.climate_pref or 'nicht angegeben'}
  Landschaft: {personality.landscape_pref or 'nicht angegeben'}
  Begleitung: {personality.companions or 'nicht angegeben'}
  Wünsche: {personality.wish_text or 'keine'}
{history_block}
{mobility_block}

Antworte NUR als JSON-Array (kein Markdown, keine Erklärung) mit Feldern:
  destination (Stadtname/Region), country, reason (1 Satz warum), 
  climate (warm/mild/cold), landscape (mountains/sea/forest/city/mix), 
  trip_type (flight/hotel/camping/car)"""

    async def _llm_suggest(self, personality: TravelPersonality,
                            visited: list[str], count: int) -> list[dict]:
        system_prompt = (
            "Du bist ein Reise-Experte. "
            "Antworte AUSSCHLIESSLICH als valides JSON-Array. "
            "Kein Markdown, keine Einleitung, kein Kommentar."
        )
        user_prompt = self._build_prompt(personality, visited, count)

        llm_provider = get_setting_value("llm_provider") or "openai"
        if llm_provider == "gemini":
            result = await self._gemini_call(system_prompt, user_prompt)
            if not result:
                result = await self._openai_call(system_prompt, user_prompt)
        else:
            result = await self._openai_call(system_prompt, user_prompt)
            if not result:
                result = await self._gemini_call(system_prompt, user_prompt)
        return result

    async def _openai_call(self, system_prompt: str, user_prompt: str) -> list[dict]:
        api_key = get_setting_value("openai_key")
        if not api_key:
            logger.warning("[Discovery] OpenAI key not configured")
            return []
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT, trust_env=False) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user",   "content": user_prompt},
                        ],
                        "max_tokens": 800,
                        "temperature": 0.7,
                    },
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"]
                return self._parse_json_array(text)
        except httpx.HTTPStatusError as e:
            logger.warning(f"[Discovery] OpenAI HTTP {e.response.status_code}: {e.response.text}")
            return []
        except Exception as e:
            logger.warning(f"[Discovery] OpenAI call failed: {e}")
            return []

    async def _gemini_call(self, system_prompt: str, user_prompt: str) -> list[dict]:
        api_key = get_setting_value("gemini_key")
        if not api_key:
            logger.warning("[Discovery] Gemini key not configured")
            return []
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT, trust_env=False) as client:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
                    json={
                        "contents": [{
                            "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
                        }],
                        "generationConfig": {"maxOutputTokens": 800, "temperature": 0.7},
                    },
                )
                resp.raise_for_status()
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return self._parse_json_array(text)
        except Exception as e:
            logger.warning(f"[Discovery] Gemini call failed: {e}")
            return []

    def _parse_json_array(self, text: str) -> list[dict]:
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
                if "```" in cleaned:
                    cleaned = cleaned.rsplit("```", 1)[0]
            if cleaned.startswith("json\n"):
                cleaned = cleaned[5:]
            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                for v in result.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict) and "destination" in v[0]:
                        return v
                return [result]
        except Exception as e:
            logger.warning(f"[Discovery] JSON parse failed: {e} | text={text[:200]}")
        return []

    # ── Bild-Pipeline ─────────────────────────────────────────────────────────

    def _make_proxy_url(self, url: str) -> str:
        """Nur Immich-URLs durch Backend-Proxy schleusen (brauchen x-api-key).
        Unsplash-URLs werden DIREKT zurückgegeben — CDN akzeptiert nur Browser-Requests."""
        return f"/api/discovery/image-proxy?url={quote(url, safe='')}"

    async def _get_image(self, user_id: int, defaults: TravelDefaults,
                          visited: list[str], destination: str) -> tuple[Optional[str], str]:
        is_visited = any(destination.lower() in v.lower() for v in visited)

        # ── a) Immich (nur für bereits besuchte Orte) ─────────────────────────
        if is_visited and defaults.immich_url and defaults.immich_api_key:
            immich_url = defaults.immich_url
            immich_key = defaults.immich_api_key
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT, trust_env=False, follow_redirects=True) as client:
                    resp = await client.post(
                        f"{immich_url}/api/search/metadata",
                        headers={"x-api-key": immich_key, "Content-Type": "application/json"},
                        json={"query": destination, "size": 1, "type": "IMAGE", "withExif": False},
                    )
                    if resp.status_code == 200:
                        items = resp.json().get("assets", {}).get("items", [])
                        if items:
                            asset_id = items[0].get("id")
                            if asset_id:
                                raw_url = f"{immich_url}/api/assets/{asset_id}/thumbnail?size=preview"
                                logger.info(f"[Discovery] Immich hit: {asset_id}")
                                return self._make_proxy_url(raw_url), "immich"
            except Exception as e:
                logger.warning(f"[Discovery/Immich] search/metadata failed: {e}")

            # Fallback: GET /api/assets
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT, trust_env=False, follow_redirects=True) as client:
                    resp = await client.get(
                        f"{immich_url}/api/assets",
                        params={"q": destination, "size": 1, "type": "IMAGE"},
                        headers={"x-api-key": immich_key},
                    )
                    if resp.status_code == 200:
                        items = resp.json()
                        if isinstance(items, list) and items:
                            asset_id = items[0].get("id")
                            if asset_id:
                                raw_url = f"{immich_url}/api/assets/{asset_id}/thumbnail?size=preview"
                                return self._make_proxy_url(raw_url), "immich"
            except Exception as e:
                logger.warning(f"[Discovery/Immich] GET /assets failed: {e}")

        # ── b) Unsplash ────────────────────────────────────────────────────────
        if defaults.unsplash_key:
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT, trust_env=False) as client:
                    resp = await client.get(
                        "https://api.unsplash.com/photos/random",
                        params={
                            "query": f"{destination} travel landscape",
                            "orientation": "landscape",
                            "content_filter": "high",
                        },
                        headers={"Authorization": f"Client-ID {defaults.unsplash_key}"},
                    )
                    if resp.status_code == 200:
                        img_url = resp.json().get("urls", {}).get("regular")
                        if img_url:
                            logger.info(f"[Discovery] Unsplash hit for {destination}")
                            return img_url, "unsplash"  # Direkt — Unsplash CDN nur Browser
                    else:
                        logger.warning(f"[Discovery/Unsplash] {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"[Discovery/Unsplash] exception: {e}")

        # ── c) CSS Fallback ───────────────────────────────────────────────────
        return None, "css_fallback"

    async def _get_multiple_images(self, user_id: int, defaults: TravelDefaults,
                                    destination: str, count: int = 4) -> list:
        """Mehrere Bilder parallel: Unsplash search + Immich kombiniert."""
        images = []

        if defaults.unsplash_key:
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT, trust_env=False) as client:
                    resp = await client.get(
                        "https://api.unsplash.com/search/photos",
                        params={
                            "query": f"{destination} travel",
                            "orientation": "landscape",
                            "per_page": count,
                            "content_filter": "high",
                        },
                        headers={"Authorization": f"Client-ID {defaults.unsplash_key}"},
                    )
                    if resp.status_code == 200:
                        for item in resp.json().get("results", [])[:count]:
                            url = item.get("urls", {}).get("regular")
                            if url:
                                images.append({
                                    "url": url,  # Direkt — kein Proxy für Unsplash
                                    "source": "unsplash"
                                })
            except Exception as e:
                logger.warning(f"[Discovery/Unsplash-multi] {e}")

        # Einzel-Fallback wenn search leer
        if not images and defaults.unsplash_key:
            visited = []  # detail view: kein visited-kontext nötig
            url, src = await self._get_image(user_id, defaults, visited, destination)
            if url:
                images.append({"url": url, "source": src})

        return images

    def _build_prefill(self, defaults: TravelDefaults, raw: dict) -> dict:
        landscape = raw.get("landscape", "") or raw.get("climate", "")
        llm_type = raw.get("trip_type", "") or ""
        valid_types = {"flight", "hotel", "camping"}
        trip_type = llm_type if llm_type in valid_types else "flight"
        if llm_type == "camping" and landscape in ("mountains", "forest"):
            trip_type = "camping"
        return {
            "destination": raw.get("destination", ""),
            "country":     raw.get("country", ""),
            "tripType":    trip_type,
            "adults":      defaults.adults,
            "children":    defaults.children,
            "homeAirport": defaults.home_airport,
        }


# ── Module-level singleton ────────────────────────────────────────────────────

discovery_service = DiscoveryService()
