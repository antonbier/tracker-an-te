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
            # Sometimes LLM wraps in {"suggestions": [...]}
            if isinstance(result, dict):
                for v in result.values():
                    if isinstance(v, list):
                        return v
        except Exception as e:
            logger.warning(f"[Discovery] JSON parse failed: {e} | text={text[:200]}")
        return []

    async def _get_image(self, user_id: int, prefs: dict, destination: str) -> tuple[Optional[str], str]:
        # a) Immich
        immich_url = prefs.get("immich_url", "")
        immich_key = get_user_setting_value(user_id, "immich_api_key") or ""
        if immich_url and immich_key:
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    resp = await client.get(
                        f"{immich_url.rstrip('/')}/api/search/smart",
                        params={"q": destination, "size": 1},
                        headers={"x-api-key": immich_key},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("assets", {}).get("items", [])
                        if items:
                            asset_id = items[0].get("id")
                            if asset_id:
                                img_url = f"{immich_url.rstrip('/')}/api/assets/{asset_id}/thumbnail"
                                logger.info(f"[Discovery] Immich image for {destination}: {img_url}")
                                return img_url, "immich"
            except Exception as e:
                logger.debug(f"[Discovery] Immich failed for {destination}: {e}")

        # b) Unsplash
        unsplash_key = get_user_setting_value(user_id, "unsplash_key") or ""
        if unsplash_key:
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    resp = await client.get(
                        "https://api.unsplash.com/photos/random",
                        params={"query": f"{destination} travel", "orientation": "landscape"},
                        headers={"Authorization": f"Client-ID {unsplash_key}"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        img_url = data.get("urls", {}).get("regular")
                        if img_url:
                            logger.info(f"[Discovery] Unsplash image for {destination}")
                            return img_url, "unsplash"
            except Exception as e:
                logger.debug(f"[Discovery] Unsplash failed for {destination}: {e}")

        # c) CSS Fallback
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


# ── Module-level singleton ────────────────────────────────────────────────────

discovery_service = DiscoveryService()
