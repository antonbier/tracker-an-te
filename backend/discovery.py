"""
WanderSuite — DiscoveryService
Liefert personalisierte Reiseziel-Vorschläge via LLM + Bild-Pipeline.

Pipeline:
  1. User-Settings laden (travel_style, climate_pref, …)
  2. Letzte 5 Dawarich-Trips als "bereits besucht"-Kontext
  3. LLM-Call (OpenAI oder Gemini)
  4. Bild-Pipeline pro Suggestion (Immich → Unsplash → CSS-Fallback)

Fehlerbehandlung: Jeder externe Call in try/except — kein Schritt bricht
die Pipeline komplett ab. Timeout: 8 Sekunden pro Call.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

from settings_manager import get_user_setting_value, get_setting_value
from database import list_detected_trips

logger = logging.getLogger(__name__)

TIMEOUT = 8.0


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

    async def get_suggestions(self, user_id: int, count: int = 3) -> list[Suggestion]:
        """Main entry point — returns `count` personalised travel suggestions."""
        # 1. Load user preferences
        prefs = self._load_prefs(user_id)

        # 2. Load "already visited" trips (last 5)
        visited = self._load_visited(user_id)

        # 3. LLM call
        raw_suggestions = await self._llm_suggest(prefs, visited, count)

        # 4. Build Suggestion objects with images
        suggestions = []
        for raw in raw_suggestions[:count]:
            dest = raw.get("destination", "")
            if not dest:
                continue
            reason = raw.get("reason", "")
            image_url, image_source = await self._get_image(user_id, prefs, dest)
            prefill = self._build_prefill(prefs, raw)
            suggestions.append(Suggestion(
                destination=dest,
                reason=reason,
                image_url=image_url,
                image_source=image_source,
                prefill=prefill,
            ))

        return suggestions

    async def get_trip_image(self, user_id: int, destination: str) -> tuple[Optional[str], str]:
        """Bild-Pipeline ohne LLM — für HeroSection Nostalgie-Bild."""
        prefs = self._load_prefs(user_id)
        return await self._get_image(user_id, prefs, destination)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _load_prefs(self, user_id: int) -> dict:
        keys = [
            "travel_style", "climate_pref", "landscape_pref",
            "companions", "wish_text",
            "immich_url", "immich_api_key", "immich_geo_sync",
            "unsplash_key",
            "ww_adults", "ww_children", "ww_home_airport",
        ]
        prefs = {}
        for k in keys:
            try:
                prefs[k] = get_user_setting_value(user_id, k) or ""
            except Exception:
                prefs[k] = ""
        return prefs

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

    async def _llm_suggest(self, prefs: dict, visited: list[str], count: int) -> list[dict]:
        llm_provider = get_setting_value("llm_provider") or "openai"
        visited_str = ", ".join(visited) if visited else "keine"
        budget_hint = ""  # no budget API call in this service for now

        user_prompt = f"""Schlage {count} Reiseziele vor.
Nutzer-Profil:
  Reisestil: {prefs.get('travel_style') or 'nicht angegeben'}
  Klima: {prefs.get('climate_pref') or 'nicht angegeben'}
  Landschaft: {prefs.get('landscape_pref') or 'nicht angegeben'}
  Begleitung: {prefs.get('companions') or 'nicht angegeben'}
  Wünsche: {prefs.get('wish_text') or 'keine'}
  Bereits besucht (nicht vorschlagen): {visited_str}

Antworte NUR als JSON-Array (kein Markdown, keine Erklärung) mit Feldern:
  destination (Stadtname/Region), country, reason (1 Satz warum), 
  climate (warm/mild/cold), landscape (mountains/sea/forest/city/mix), 
  trip_type (flight/hotel/camping/car)"""

        system_prompt = (
            "Du bist ein Reise-Experte. "
            "Antworte AUSSCHLIESSLICH als valides JSON-Array. "
            "Kein Markdown, keine Einleitung, kein Kommentar."
        )

            # Try the configured provider first, then fallback to the other
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
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
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
        except Exception as e:
            logger.warning(f"[Discovery] OpenAI call failed: {e}")
            return []

    async def _gemini_call(self, system_prompt: str, user_prompt: str) -> list[dict]:
        api_key = get_setting_value("gemini_key")
        if not api_key:
            logger.warning("[Discovery] Gemini key not configured")
            return []
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
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
            # Strip markdown code fences if present
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
                if "```" in cleaned:
                    cleaned = cleaned.rsplit("```", 1)[0]
            
            # Remove lingering 'json' keyword at the start if it exists
            if cleaned.startswith("json\n"):
                cleaned = cleaned[5:]

            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
            # Plain object (for detail endpoint) → wrap in list
            if isinstance(result, dict):
                # Check if it wraps a list
                for v in result.values():
                    if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "destination" in v[0]:
                        return v
                # Otherwise treat the dict itself as single item
                return [result]
        except Exception as e:
            logger.warning(f"[Discovery] JSON parse failed: {e} | text={text[:200]}")
        return []

    async def _get_image(self, user_id: int, prefs: dict, destination: str) -> tuple[Optional[str], str]:
        # ── a) Immich ─────────────────────────────────────────────────────────
        immich_url = (prefs.get("immich_url") or "").strip().rstrip("/")
        immich_key = (get_user_setting_value(user_id, "immich_api_key") or "").strip()

        logger.info(f"[Discovery/img] dest={destination!r} immich_url={bool(immich_url)} immich_key={bool(immich_key)} unsplash_key={bool(get_user_setting_value(user_id, 'unsplash_key'))}")

        if immich_url and immich_key:
            # Try POST /api/search/metadata (works across Immich versions)
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
                    resp = await client.post(
                        f"{immich_url}/api/search/metadata",
                        headers={"x-api-key": immich_key, "Content-Type": "application/json"},
                        json={"query": destination, "size": 1, "type": "IMAGE", "withExif": False},
                    )
                    logger.info(f"[Discovery/Immich] POST /search/metadata status={resp.status_code}")
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("assets", {}).get("items", [])
                        if items:
                            asset_id = items[0].get("id")
                            if asset_id:
                                img_url = f"{immich_url}/api/assets/{asset_id}/thumbnail?size=preview"
                                # Thumbnail needs auth header — frontend can't send it directly.
                                # Use the public /api/assets/{id}/original fallback or proxy.
                                # For now: return URL and let frontend add header via img tag won't work.
                                # Instead: return a data URL or use /api/assets/{id}/thumbnail with key in query
                                img_url = f"{immich_url}/api/assets/{asset_id}/thumbnail?size=preview&key={immich_key}"
                                logger.info(f"[Discovery] Immich hit: {asset_id}")
                                return img_url, "immich"
            except Exception as e:
                logger.warning(f"[Discovery/Immich] search/metadata failed: {e}")

            # Fallback: GET /api/search/quick-transform (older Immich)
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
                    resp = await client.get(
                        f"{immich_url}/api/assets",
                        params={"q": destination, "size": 1, "type": "IMAGE"},
                        headers={"x-api-key": immich_key},
                    )
                    logger.info(f"[Discovery/Immich] GET /assets status={resp.status_code}")
                    if resp.status_code == 200:
                        items = resp.json()
                        if isinstance(items, list) and items:
                            asset_id = items[0].get("id")
                            if asset_id:
                                img_url = f"{immich_url}/api/assets/{asset_id}/thumbnail?size=preview&key={immich_key}"
                                logger.info(f"[Discovery] Immich assets hit: {asset_id}")
                                return img_url, "immich"
            except Exception as e:
                logger.warning(f"[Discovery/Immich] GET /assets failed: {e}")

        # ── b) Unsplash ───────────────────────────────────────────────────────
        unsplash_key = (get_user_setting_value(user_id, "unsplash_key") or "").strip()
        if unsplash_key:
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    resp = await client.get(
                        "https://api.unsplash.com/photos/random",
                        params={"query": f"{destination} travel landscape", "orientation": "landscape", "content_filter": "high"},
                        headers={"Authorization": f"Client-ID {unsplash_key}"},
                    )
                    logger.info(f"[Discovery/Unsplash] status={resp.status_code} dest={destination!r}")
                    if resp.status_code == 200:
                        data = resp.json()
                        img_url = data.get("urls", {}).get("regular")
                        if img_url:
                            logger.info(f"[Discovery] Unsplash hit for {destination}")
                            return img_url, "unsplash"
                    else:
                        logger.warning(f"[Discovery/Unsplash] error: {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"[Discovery/Unsplash] exception: {e}")

        # ── c) CSS Fallback ───────────────────────────────────────────────────
        logger.info(f"[Discovery/img] css_fallback for {destination!r}")
        return None, "css_fallback"

    def _build_prefill(self, prefs: dict, raw: dict) -> dict:
        # Derive sensible trip_type from landscape/climate rather than trusting LLM blindly
        landscape = raw.get("landscape", "") or raw.get("climate", "")
        llm_type  = raw.get("trip_type", "") or ""
        # Only accept flight/hotel/camping — reject car (nearly never correct as primary)
        valid_types = {"flight", "hotel", "camping"}
        trip_type = llm_type if llm_type in valid_types else "flight"
        # Camping only if landscape explicitly says mountains/forest or LLM said camping
        if llm_type == "camping" and landscape in ("mountains", "forest"):
            trip_type = "camping"
        return {
            "destination": raw.get("destination", ""),
            "country":     raw.get("country", ""),
            "tripType":    trip_type,
            "adults":      int(prefs.get("ww_adults") or 2),
            "children":    int(prefs.get("ww_children") or 0),
            "homeAirport": prefs.get("ww_home_airport") or "",
        }



    async def get_destination_detail(self, user_id: int, destination: str, country: str = "") -> dict:
        """Full detail: LLM description + things_to_do + multiple images."""
        prefs = self._load_prefs(user_id)

        # LLM: detailed description
        dest_label = f"{destination}, {country}" if country else destination
        system = ("Du bist ein Reise-Experte. Antworte NUR als JSON-Objekt. "
                  "Kein Markdown, keine Erklärung.")
        user_msg = (
            f"Beschreibe das Reiseziel '{dest_label}' detailliert. "
            f"Nutzer-Profil: Reisestil={prefs.get('travel_style','?')}, "
            f"Klima={prefs.get('climate_pref','?')}, "
            f"Begleitung={prefs.get('companions','?')}. "
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
        else:
            raw_list = await self._openai_call(system, user_msg)
        if not raw_list:
            if llm_provider == "gemini":
                raw_list = await self._openai_call(system, user_msg)
            else:
                raw_list = await self._gemini_call(system, user_msg)

        # _parse_json_array wraps in list; detail is an object → unwrap
        detail_raw = raw_list[0] if raw_list else {}
        if not isinstance(detail_raw, dict):
            detail_raw = {}

        # Multiple images (up to 4)
        images = await self._get_multiple_images(user_id, prefs, destination, count=4)

        return {
            "destination":  destination,
            "country":      country,
            "description":  detail_raw.get("description", ""),
            "things_to_do": detail_raw.get("things_to_do", []),
            "best_season":  detail_raw.get("best_season", ""),
            "vibe":         detail_raw.get("vibe", ""),
            "images":       images,   # list of {url, source}
        }

    async def _get_multiple_images(self, user_id: int, prefs: dict, destination: str, count: int = 4) -> list:
        """Fetch multiple images: Unsplash first (supports multiple), then Immich."""
        images = []

        # Unsplash: /photos/search returns multiple results
        unsplash_key = (get_user_setting_value(user_id, "unsplash_key") or "").strip()
        if unsplash_key and len(images) < count:
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    resp = await client.get(
                        "https://api.unsplash.com/search/photos",
                        params={"query": f"{destination} travel", "orientation": "landscape",
                                "per_page": count, "content_filter": "high"},
                        headers={"Authorization": f"Client-ID {unsplash_key}"},
                    )
                    logger.info(f"[Discovery/Unsplash-multi] status={resp.status_code}")
                    if resp.status_code == 200:
                        for item in resp.json().get("results", [])[:count]:
                            url = item.get("urls", {}).get("regular")
                            if url:
                                images.append({"url": url, "source": "unsplash"})
            except Exception as e:
                logger.warning(f"[Discovery/Unsplash-multi] {e}")

        # Single Unsplash fallback if search returned nothing
        if not images and unsplash_key:
            url, src = await self._get_image(user_id, prefs, destination)
            if url:
                images.append({"url": url, "source": src})

        return images


# ── Module-level singleton ────────────────────────────────────────────────────

discovery_service = DiscoveryService()
