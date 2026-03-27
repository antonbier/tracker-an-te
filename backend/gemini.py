"""
WanderSuite — Google Gemini Integration
AI travel recommendations for the Discover module.
Uses Gemini 2.0 Flash API (free at aistudio.google.com).
Returns structured JSON with 5 destination recommendations.
"""

import requests
import logging
import json

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL    = "gemini-2.0-flash"


def generate_travel_recommendations(
    query: str,
    api_key: str,
    exclude_places: list[str] | None = None,
    lang: str = "de",
) -> dict:
    """
    Reiseempfehlungen via Gemini generieren.
    query: z.B. "Strand, warmes Wetter, günstig"
    exclude_places: Liste bereits besuchter Orte (aus Dawarich)
    lang: Sprache der Antwort (de/it/en)
    """
    if not api_key:
        return {"error": "Gemini API Key nicht konfiguriert"}

    lang_map = {"de": "Deutsch", "it": "Italiano", "en": "English"}
    lang_name = lang_map.get(lang, "Deutsch")

    exclude_hint = ""
    if exclude_places:
        exclude_hint = f"\nBitte NICHT empfehlen (bereits besucht): {', '.join(exclude_places[:20])}"

    prompt = f"""Du bist ein Reiseexperte. Empfehle 5 Reiseziele basierend auf dieser Anfrage.

Anfrage: {query}{exclude_hint}

Antworte auf {lang_name}. Formatiere die Antwort als JSON-Array mit diesem Format:
[
  {{
    "destination": "Stadtname, Land",
    "why": "Kurze Begründung (1-2 Sätze)",
    "best_time": "Beste Reisezeit",
    "estimated_budget": "Geschätztes Budget pro Person (€)",
    "highlight": "Top-Aktivität oder Sehenswürdigkeit"
  }}
]

Antworte NUR mit dem JSON-Array, ohne Erklärungen oder Markdown."""

    url = f"{GEMINI_API_BASE}/{GEMINI_MODEL}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 1024,
        }
    }

    try:
        resp = requests.post(url, json=payload, timeout=30)
        logger.info(f"[Gemini] Status: {resp.status_code}")

        if resp.status_code == 400:
            logger.error(f"[Gemini] Bad Request: {resp.text[:300]}")
            return {"error": f"Gemini API Fehler: {resp.json().get('error', {}).get('message', 'Bad Request')}"}

        if resp.status_code == 403:
            return {"error": "Gemini API Key ungültig oder keine Berechtigung"}

        if resp.status_code == 429:
            return {"error": "Gemini Rate Limit erreicht — bitte kurz warten"}

        resp.raise_for_status()
        data = resp.json()

        # Antwort extrahieren
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # JSON parsen
        try:
            recommendations = json.loads(text)
            return {"recommendations": recommendations}
        except json.JSONDecodeError:
            # Fallback: rohen Text zurückgeben
            return {"raw": text}

    except requests.RequestException as e:
        logger.error(f"[Gemini] Request Fehler: {e}")
        return {"error": f"Netzwerkfehler: {str(e)}"}
    except (KeyError, IndexError) as e:
        logger.error(f"[Gemini] Parse Fehler: {e}")
        return {"error": "Unerwartetes Antwortformat von Gemini"}
