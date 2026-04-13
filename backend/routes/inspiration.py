"""
WanderSuite — POST /api/inspiration
KI-Zielgenerator für den "Inspiriere mich"-Pfad.
Unterstützt: OpenAI (gpt-4o-mini) und Google Gemini (gemini-1.5-flash).
Fallback: statische Beispiele wenn kein Key vorhanden.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import logging, json, os, httpx

from auth_jwt import get_current_user
from settings_manager import get_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


class InspirationRequest(BaseModel):
    travel_mode:  str = "flight"
    budget:       Optional[float]     = None
    adults:       Optional[int]       = 2
    children:     Optional[int]       = 0
    vibes:        Optional[list[str]] = []
    wish_text:    Optional[str]       = None
    flex_month:   Optional[str]       = None
    flex_nights:  Optional[int]       = None
    max_time:     Optional[str]       = None
    home_airport: Optional[str]       = None


class InspirationDestination(BaseModel):
    destination_name:       str
    pitch:                  str
    est_travel_time:        str
    est_budget_per_person:  str
    image_query:            str


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(data: InspirationRequest) -> str:
    mode    = "Flugreise" if data.travel_mode == "flight" else "Autoreise"
    budget  = f"ca. {data.budget:.0f} € Gesamtbudget" if data.budget else "kein festes Budget"
    persons = f"{data.adults} Erw." + (f", {data.children} Kinder" if data.children else "")
    vibes   = ", ".join(data.vibes) if data.vibes else "offen"
    wish    = f"\nBesonderer Wunsch: {data.wish_text}" if data.wish_text else ""
    timing  = ""
    if data.flex_month:
        timing = f"\nZeitraum: {data.flex_month}"
        if data.flex_nights:
            timing += f", ca. {data.flex_nights} Nächte"
    max_t = ""
    if data.max_time and data.max_time != "any":
        label = "Flugzeit" if data.travel_mode == "flight" else "Fahrzeit"
        max_t = f"\nMax. {label}: {data.max_time}"
    home = f"\nAbflughafen: {data.home_airport}" if data.home_airport and data.travel_mode == "flight" else ""

    return f"""Generiere exakt 3 passende Reiseziele für folgende Anfrage:

Reiseart: {mode}
Personen: {persons}
Budget: {budget}
Vibe/Stimmung: {vibes}{wish}{timing}{max_t}{home}

Antworte NUR mit diesem JSON-Objekt (kein Markdown, kein Text davor/danach):
{{
  "destinations": [
    {{
      "destination_name": "Caorle, Italien",
      "pitch": "Kleines Fischerdorf an der Adria – ruhiger als Rimini, mit allem was das Herz begehrt.",
      "est_travel_time": "3.5h",
      "est_budget_per_person": "380€",
      "image_query": "Caorle Italy beach"
    }}
  ]
}}

Wichtig:
- pitch: 2-3 lebendige Sätze, persönlich und überzeugend
- est_budget_per_person: realistisch inkl. Unterkunft & Anreise
- image_query: kurzer englischer Suchbegriff für ein schönes Foto
- Alle 3 Ziele sollen sich deutlich voneinander unterscheiden"""


def _parse_destinations(raw: str) -> list[InspirationDestination]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    parsed = json.loads(text.strip())
    destinations = parsed.get("destinations", parsed) if isinstance(parsed, dict) else parsed
    return [
        InspirationDestination(
            destination_name      = d.get("destination_name", "Unbekannt"),
            pitch                 = d.get("pitch", ""),
            est_travel_time       = d.get("est_travel_time", "—"),
            est_budget_per_person = d.get("est_budget_per_person", "—"),
            image_query           = d.get("image_query", d.get("destination_name", "")),
        )
        for d in destinations[:3]
    ]


# ── OpenAI ────────────────────────────────────────────────────────────────────

async def _call_openai(prompt: str, api_key: str) -> list[InspirationDestination]:
    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "max_tokens": 700,
                "temperature": 0.85,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "Du bist ein kreativer Reise-Assistent. Antworte NUR mit validem JSON."},
                    {"role": "user", "content": prompt},
                ],
            }
        )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"]
    return _parse_destinations(raw)


# ── Gemini ────────────────────────────────────────────────────────────────────

async def _call_gemini(prompt: str, api_key: str) -> list[InspirationDestination]:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 700,
            "responseMimeType": "application/json",
        },
    }
    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(url, json=body)
    resp.raise_for_status()
    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_destinations(raw)


# ── Fallback ──────────────────────────────────────────────────────────────────

def _fallback(data: InspirationRequest) -> list[InspirationDestination]:
    if data.travel_mode == "car":
        return [
            InspirationDestination(destination_name="Gardasee, Italien", pitch="Italiens größter See – türkisblaues Wasser, Zitronenhaine und malerische Dörfer warten. Ein zeitloser Klassiker für Erholung und Genuss.", est_travel_time="3h", est_budget_per_person="320€", image_query="Lake Garda Italy"),
            InspirationDestination(destination_name="Plitvicer Seen, Kroatien", pitch="Smaragdgrüne Seen und Wasserfälle in einem UNESCO-Weltnaturerbe. Ideal für Naturliebhaber die echte Wildnis suchen.", est_travel_time="5h", est_budget_per_person="280€", image_query="Plitvice Lakes Croatia waterfalls"),
            InspirationDestination(destination_name="Salzburg, Österreich", pitch="Mozarts Geburtsstadt mit barockem Charme und alpinem Flair. Festung, Altstadt und Seenregion vereint.", est_travel_time="2h", est_budget_per_person="250€", image_query="Salzburg Austria old town"),
        ]
    return [
        InspirationDestination(destination_name="Lissabon, Portugal", pitch="Die Sieben-Hügel-Stadt bezaubert mit Fado, Pastéis de Nata und atemberaubenden Aussichtspunkten. Europas günstigste Hauptstadt mit maximalem Charme.", est_travel_time="3h Flug", est_budget_per_person="420€", image_query="Lisbon Portugal city viewpoint"),
        InspirationDestination(destination_name="Dubrovnik, Kroatien", pitch="Die Perle der Adria – makellose Altstadt, kristallklares Wasser und Sonnenuntergänge die für immer im Gedächtnis bleiben.", est_travel_time="2h Flug", est_budget_per_person="480€", image_query="Dubrovnik Croatia old town walls"),
        InspirationDestination(destination_name="Sevilla, Spanien", pitch="Flamenco, Tapas und andalusische Lebensfreude pur. Eine Stadt die alle Sinne anspricht – zu überraschend fairen Preisen.", est_travel_time="2.5h Flug", est_budget_per_person="390€", image_query="Seville Spain cathedral plaza"),
    ]


# ── Main endpoint ─────────────────────────────────────────────────────────────

@router.post("", response_model=list[InspirationDestination])
async def get_inspiration(data: InspirationRequest, user=Depends(get_current_user)):
    openai_key = get_setting_value("openai_key") or os.getenv("OPENAI_API_KEY", "")
    gemini_key = get_setting_value("gemini_key") or os.getenv("GEMINI_API_KEY", "")

    prompt = _build_prompt(data)

    # Try OpenAI first, then Gemini, then fallback
    if openai_key:
        try:
            result = await _call_openai(prompt, openai_key)
            logger.info(f"[Inspiration] OpenAI → {len(result)} destinations for user {user.get('id')}")
            return result
        except Exception as e:
            logger.warning(f"[Inspiration] OpenAI failed: {e} — trying Gemini")

    if gemini_key:
        try:
            result = await _call_gemini(prompt, gemini_key)
            logger.info(f"[Inspiration] Gemini → {len(result)} destinations for user {user.get('id')}")
            return result
        except Exception as e:
            logger.warning(f"[Inspiration] Gemini failed: {e} — using fallback")

    logger.info(f"[Inspiration] No LLM key — static fallback for user {user.get('id')}")
    return _fallback(data)
