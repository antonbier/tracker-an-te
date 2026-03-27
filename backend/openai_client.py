"""
WanderSuite v1.0 — OpenAI Integration
Reiseempfehlungen via gpt-4o-mini (günstig, schnell).
Selbes Output-Format wie Gemini für nahtlosen Provider-Wechsel.
"""

import requests
import logging
import json

logger = logging.getLogger(__name__)

OPENAI_API_BASE = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL    = "gpt-4o-mini"


def generate_travel_recommendations(
    query: str,
    api_key: str,
    exclude_places: list[str] | None = None,
    lang: str = "de",
) -> dict:
    """
    Reiseempfehlungen via OpenAI gpt-4o-mini.
    Selbes Interface wie gemini.generate_travel_recommendations.
    """
    if not api_key:
        return {"error": "OpenAI API Key nicht konfiguriert"}

    lang_map = {"de": "Deutsch", "it": "Italiano", "en": "English"}
    lang_name = lang_map.get(lang, "Deutsch")

    exclude_hint = ""
    if exclude_places:
        exclude_hint = f"\nBitte NICHT empfehlen (bereits besucht): {', '.join(exclude_places[:20])}"

    prompt = f"""Du bist ein Reiseexperte. Empfehle 5 Reiseziele basierend auf dieser Anfrage.

Anfrage: {query}{exclude_hint}

Antworte auf {lang_name}. Formatiere die Antwort als JSON-Array:
[
  {{
    "destination": "Stadtname, Land",
    "why": "Kurze Begründung (1-2 Sätze)",
    "best_time": "Beste Reisezeit",
    "estimated_budget": "Geschätztes Budget pro Person (€)",
    "highlight": "Top-Aktivität oder Sehenswürdigkeit"
  }}
]

Antworte NUR mit dem JSON-Array, ohne Erklärungen oder Markdown-Backticks."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"},
    }

    try:
        resp = requests.post(OPENAI_API_BASE, json=payload, headers=headers, timeout=30)
        logger.info(f"[OpenAI] Status: {resp.status_code}")

        if resp.status_code == 401:
            return {"error": "OpenAI API Key ungültig"}
        if resp.status_code == 429:
            return {"error": "OpenAI Rate Limit — bitte kurz warten"}
        if resp.status_code == 400:
            err = resp.json().get("error", {})
            return {"error": f"OpenAI Fehler: {err.get('message', 'Bad Request')}"}

        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()

        # gpt-4o-mini mit response_format json_object gibt manchmal {"recommendations": [...]}
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return {"recommendations": parsed}
            if "recommendations" in parsed:
                return {"recommendations": parsed["recommendations"]}
            # Fallback: erste Liste-artige Value nehmen
            for v in parsed.values():
                if isinstance(v, list):
                    return {"recommendations": v}
            return {"raw": text}
        except json.JSONDecodeError:
            return {"raw": text}

    except requests.RequestException as e:
        logger.error(f"[OpenAI] Request Fehler: {e}")
        return {"error": f"Netzwerkfehler: {str(e)}"}
    except (KeyError, IndexError) as e:
        logger.error(f"[OpenAI] Parse Fehler: {e}")
        return {"error": "Unerwartetes Antwortformat von OpenAI"}
