"""
WanderSuite — POST /api/inspiration
KI-Zielgenerator für den "Inspiriere mich"-Pfad des WanderWizzards.
Nutzt gpt-4o-mini, um 3 passende Reiseziele als strukturiertes JSON zu generieren.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging, json, os, httpx

from auth_jwt import get_current_user
from settings_manager import get_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


class InspirationRequest(BaseModel):
    travel_mode:  str               = "flight"   # 'flight' | 'car'
    budget:       Optional[float]   = None
    adults:       Optional[int]     = 2
    children:     Optional[int]     = 0
    vibes:        Optional[list[str]] = []
    wish_text:    Optional[str]     = None
    flex_month:   Optional[str]     = None
    flex_nights:  Optional[int]     = None
    max_time:     Optional[str]     = None        # '2h'|'4h'|'6h'|'8h'|'any'
    home_airport: Optional[str]     = None


class InspirationDestination(BaseModel):
    destination_name:    str
    pitch:               str
    est_travel_time:     str
    est_budget_per_person: str
    image_query:         str   # Suchbegriff für Unsplash-Bild


@router.post("", response_model=list[InspirationDestination])
async def get_inspiration(data: InspirationRequest, user=Depends(get_current_user)):
    openai_key = get_setting_value("openai_key") or os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        # Fallback: statische Beispiele ohne KI
        return _fallback_destinations(data)

    prompt = _build_prompt(data)

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": 700,
                    "temperature": 0.85,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Du bist ein kreativer Reise-Assistent. Antworte NUR mit validem JSON. "
                                "Kein Markdown, keine Erklärungen außerhalb des JSON."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                }
            )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        parsed = json.loads(raw)

        # Accept both {"destinations": [...]} and [...]
        destinations = parsed.get("destinations", parsed) if isinstance(parsed, dict) else parsed

        result = []
        for d in destinations[:3]:
            result.append(InspirationDestination(
                destination_name    = d.get("destination_name", "Unbekannt"),
                pitch               = d.get("pitch", ""),
                est_travel_time     = d.get("est_travel_time", "—"),
                est_budget_per_person = d.get("est_budget_per_person", "—"),
                image_query         = d.get("image_query", d.get("destination_name", "")),
            ))

        if not result:
            raise ValueError("Empty destinations list from LLM")

        logger.info(f"[Inspiration] Generated {len(result)} destinations for user {user.get('id')}")
        return result

    except Exception as e:
        logger.warning(f"[Inspiration] LLM call failed: {e} — using fallback")
        return _fallback_destinations(data)


def _build_prompt(data: InspirationRequest) -> str:
    mode     = "Flugreise" if data.travel_mode == "flight" else "Autoreise"
    budget   = f"ca. {data.budget:.0f} € Gesamtbudget" if data.budget else "kein festes Budget"
    persons  = f"{data.adults} Erw." + (f", {data.children} Kinder" if data.children else "")
    vibes    = ", ".join(data.vibes) if data.vibes else "offen"
    wish     = f"\nBesonderer Wunsch: {data.wish_text}" if data.wish_text else ""
    timing   = ""
    if data.flex_month:
        timing = f"\nZeitraum: {data.flex_month}"
        if data.flex_nights:
            timing += f", ca. {data.flex_nights} Nächte"
    max_t    = ""
    if data.max_time and data.max_time != "any":
        label = "Flugzeit" if data.travel_mode == "flight" else "Fahrzeit"
        max_t = f"\nMax. {label}: {data.max_time}"
    home     = f"\nAbflughafen: {data.home_airport}" if data.home_airport and data.travel_mode == "flight" else ""

    return f"""Generiere exakt 3 passende Reiseziele für folgende Anfrage:

Reiseart: {mode}
Personen: {persons}
Budget: {budget}
Vibe/Stimmung: {vibes}{wish}{timing}{max_t}{home}

Antworte mit diesem JSON-Format:
{{
  "destinations": [
    {{
      "destination_name": "Caorle, Italien",
      "pitch": "Kleines, charmantes Fischerdorf an der Adria – ruhiger als Rimini, aber mit allem was das Herz begehrt. Perfekt für entspannte Strandtage mit authentischer Atmosphäre.",
      "est_travel_time": "3.5h",
      "est_budget_per_person": "380€",
      "image_query": "Caorle Italy beach"
    }},
    ...
  ]
}}

Wichtig:
- Ziele müssen wirklich gut zur Anfrage passen (Vibe, Budget, Reisezeit)
- pitch: 2-3 lebendige Sätze, persönlich und überzeugend
- est_budget_per_person: realistisch inkl. Unterkunft & Anreise
- image_query: kurzer englischer Suchbegriff für ein schönes Foto des Ortes
- Alle 3 Ziele sollen sich deutlich voneinander unterscheiden"""


def _fallback_destinations(data: InspirationRequest) -> list[InspirationDestination]:
    """Statische Beispiele wenn kein OpenAI Key vorhanden."""
    if data.travel_mode == "car":
        return [
            InspirationDestination(
                destination_name="Gardasee, Italien",
                pitch="Der Gardasee ist Italiens größter See und ein zeitloser Klassiker. Türkisblaues Wasser, Zitronenhaine und malerische Dörfer warten auf euch.",
                est_travel_time="3h",
                est_budget_per_person="320€",
                image_query="Lake Garda Italy"
            ),
            InspirationDestination(
                destination_name="Plitvicer Seen, Kroatien",
                pitch="Smaragdgrüne Seen, Wasserfälle und unberührte Natur – ein UNESCO-Weltnaturerbe das man gesehen haben muss. Ideal für Naturliebhaber.",
                est_travel_time="5h",
                est_budget_per_person="280€",
                image_query="Plitvice Lakes Croatia waterfalls"
            ),
            InspirationDestination(
                destination_name="Salzburg, Österreich",
                pitch="Mozarts Geburtsstadt kombiniert barocke Architektur mit alpinem Flair. Festung, Altstadt und die Umgebung der Seenregion machen jeden Tag zum Erlebnis.",
                est_travel_time="2h",
                est_budget_per_person="250€",
                image_query="Salzburg Austria old town"
            ),
        ]
    else:
        return [
            InspirationDestination(
                destination_name="Lissabon, Portugal",
                pitch="Die Sieben-Hügel-Stadt bezaubert mit Fado, Pastéis de Nata und atemberaubenden Aussichtspunkten. Europas günstigste Metropole mit maximalem Charme.",
                est_travel_time="3h Flug",
                est_budget_per_person="420€",
                image_query="Lisbon Portugal city viewpoint"
            ),
            InspirationDestination(
                destination_name="Dubrovnik, Kroatien",
                pitch="Die Perle der Adria – makellose Altstadt, kristallklares Wasser und Sonnenuntergänge die für immer im Gedächtnis bleiben.",
                est_travel_time="2h Flug",
                est_budget_per_person="480€",
                image_query="Dubrovnik Croatia old town walls"
            ),
            InspirationDestination(
                destination_name="Sevilla, Spanien",
                pitch="Flamenco, Tapas und andalusische Lebensfreude pur. Sevilla ist eine Stadt die alle Sinne anspricht – und das zu überraschend fairen Preisen.",
                est_travel_time="2.5h Flug",
                est_budget_per_person="390€",
                image_query="Seville Spain cathedral plaza"
            ),
        ]
