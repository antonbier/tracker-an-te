"""
WanderSuite — /api/ws-trips
WanderWizzard Trip Container: anlegen, abrufen, To-Dos verwalten.
KI-To-Do-Generierung via OpenAI gpt-4o-mini beim Trip-Anlegen.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging, json, os

from database import (
    create_ws_trip, list_ws_trips, get_ws_trip,
    update_ws_trip_status, delete_ws_trip,
    create_trip_todos, list_trip_todos,
    toggle_trip_todo, delete_trip_todo,
)
from auth_jwt import get_current_user
from settings_manager import get_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


def _uid(user: dict) -> int:
    return user.get("id", 1) or 1


# ── Pydantic Models ───────────────────────────────────────────────────────────

class WsTripCreate(BaseModel):
    title:        str
    destination:  Optional[str] = ""
    start_date:   Optional[str] = None
    end_date:     Optional[str] = None
    trip_type:    Optional[str] = "flight"
    budget:       Optional[float] = None
    path:         Optional[str] = "known"
    travel_mode:  Optional[str] = "flight"
    vibes:        Optional[list[str]] = []
    wish_text:    Optional[str] = None
    flex_month:   Optional[str] = None
    flex_nights:  Optional[int] = None
    max_time:     Optional[str] = None
    home_airport: Optional[str] = None
    adults:       Optional[int] = 2
    children:     Optional[int] = 0
    notes:        Optional[str] = None


class TodoToggle(BaseModel):
    pass  # no body needed


class TodoCreate(BaseModel):
    task:     str
    category: Optional[str] = "general"


class StatusUpdate(BaseModel):
    status: str   # 'planning' | 'booked' | 'completed'


# ── KI To-Do Generierung ──────────────────────────────────────────────────────

async def _generate_todos(trip: dict) -> list[dict]:
    """
    Generiert 5 kontextbezogene To-Dos via OpenAI gpt-4o-mini.
    Gibt bei Fehler eine sinnvolle Fallback-Liste zurück.
    """
    openai_key = get_setting_value("openai_key") or os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        logger.info("[WsTrips] Kein OpenAI Key — nutze Fallback-Todos")
        return _fallback_todos(trip)

    travel_mode = trip.get("travel_mode", "flight")
    destination = trip.get("destination") or trip.get("flex_month") or "unbekannt"
    dates = ""
    if trip.get("start_date"):
        dates = f" vom {trip['start_date']}"
        if trip.get("end_date"):
            dates += f" bis {trip['end_date']}"
    budget_str = f", Budget ca. {trip['budget']} €" if trip.get("budget") else ""
    vibes_str  = ", ".join(trip.get("vibes") or [])
    path       = trip.get("path", "known")

    if path == "inspire":
        dest_desc = f"KI-empfohlenes Ziel (Vibe: {vibes_str or 'offen'})"
        if trip.get("wish_text"):
            dest_desc += f", Wunsch: {trip['wish_text']}"
    else:
        dest_desc = destination

    mode_label = "Flugreise" if travel_mode == "flight" else "Autoreise"
    home_str   = f" ab {trip['home_airport']}" if travel_mode == "flight" and trip.get("home_airport") else ""

    prompt = f"""Du bist ein präziser Reise-Assistent. Erstelle genau 5 kontextbezogene To-Dos für folgende Reise:

Ziel: {dest_desc}
Reiseart: {mode_label}{home_str}
Zeitraum: {dates or 'flexibel'}{budget_str}
Mitreisende: {trip.get('adults', 2)} Erw.{', ' + str(trip.get('children')) + ' Kind.' if trip.get('children') else ''}

Antworte NUR mit einem JSON-Array, kein Text davor/danach, kein Markdown:
[
  {{"task": "...", "category": "booking"}},
  {{"task": "...", "category": "documents"}},
  {{"task": "...", "category": "packing"}},
  {{"task": "...", "category": "general"}},
  {{"task": "...", "category": "general"}}
]
Kategorien: booking, documents, packing, general.
To-Dos sollen spezifisch für diese Reise sein, nicht generisch."""

    try:
        import httpx
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": 400,
                    "temperature": 0.7,
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip potential markdown fences
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        todos = json.loads(content.strip())
        if isinstance(todos, list) and todos:
            logger.info(f"[WsTrips] KI-Todos generiert: {len(todos)} Einträge")
            return [{"task": t.get("task",""), "category": t.get("category","general")} for t in todos[:7]]
    except Exception as e:
        logger.warning(f"[WsTrips] KI-Todo-Generierung fehlgeschlagen: {e}")

    return _fallback_todos(trip)


def _fallback_todos(trip: dict) -> list[dict]:
    """Statische Fallback-Todos, kontextsensitiv nach travel_mode."""
    mode = trip.get("travel_mode", "flight")
    dest = trip.get("destination") or "Reiseziel"
    if mode == "flight":
        return [
            {"task": f"Flug nach {dest} buchen", "category": "booking"},
            {"task": "Reisedokumente prüfen (Reisepass/Ausweis)", "category": "documents"},
            {"task": "Unterkunft buchen", "category": "booking"},
            {"task": "Reisekrankenversicherung abschließen", "category": "documents"},
            {"task": "Koffer packen", "category": "packing"},
        ]
    else:
        return [
            {"task": "Route & Stopps planen", "category": "general"},
            {"task": "Fahrzeug & Tankstand prüfen", "category": "general"},
            {"task": "Unterkunft entlang der Route buchen", "category": "booking"},
            {"task": "Pannenhilfe / ADAC-Mitgliedschaft prüfen", "category": "documents"},
            {"task": "Koffer & Dachbox packen", "category": "packing"},
        ]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def create_trip(data: WsTripCreate, user=Depends(get_current_user)):
    """
    Neuen WanderWizzard-Trip anlegen.
    Automatisch: 5 KI-generierte To-Dos via gpt-4o-mini.
    """
    uid = _uid(user)
    trip_data = data.model_dump()

    # Auto-Title wenn leer
    if not trip_data.get("title"):
        dest = trip_data.get("destination") or trip_data.get("flex_month") or "Neue Reise"
        trip_data["title"] = dest

    trip_id = create_ws_trip(trip_data, user_id=uid)
    logger.info(f"[WsTrips] Trip #{trip_id} angelegt für user {uid}: {trip_data['title']}")

    # KI To-Dos generieren
    trip_data["id"] = trip_id
    todos = await _generate_todos(trip_data)
    n_todos = create_trip_todos(trip_id, todos)
    logger.info(f"[WsTrips] {n_todos} To-Dos für Trip #{trip_id} gespeichert")

    return {
        "id":      trip_id,
        "title":   trip_data["title"],
        "todos":   todos,
        "message": "Trip angelegt ✓",
    }


@router.get("")
def get_trips(user=Depends(get_current_user)):
    """Alle WanderWizzard-Trips des Users."""
    return list_ws_trips(_uid(user))


@router.get("/{trip_id}")
def get_trip(trip_id: int, user=Depends(get_current_user)):
    trip = get_ws_trip(trip_id, _uid(user))
    if not trip:
        raise HTTPException(404, "Trip nicht gefunden")
    trip["todos"] = list_trip_todos(trip_id)
    return trip


@router.patch("/{trip_id}/status")
def set_status(trip_id: int, data: StatusUpdate, user=Depends(get_current_user)):
    if data.status not in ("planning", "booked", "completed"):
        raise HTTPException(422, "Ungültiger Status")
    if not update_ws_trip_status(trip_id, data.status, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    return {"id": trip_id, "status": data.status}


@router.delete("/{trip_id}")
def remove_trip(trip_id: int, user=Depends(get_current_user)):
    if not delete_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    return {"message": "Trip gelöscht ✓"}


# ── To-Do Endpoints ───────────────────────────────────────────────────────────

@router.get("/{trip_id}/todos")
def get_todos(trip_id: int, user=Depends(get_current_user)):
    # Verify ownership
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    return list_trip_todos(trip_id)


@router.post("/{trip_id}/todos", status_code=201)
def add_todo(trip_id: int, data: TodoCreate, user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    create_trip_todos(trip_id, [{"task": data.task, "category": data.category}])
    return {"message": "To-Do hinzugefügt ✓"}


@router.patch("/{trip_id}/todos/{todo_id}/toggle")
def toggle_todo(trip_id: int, todo_id: int, user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    if not toggle_trip_todo(todo_id, trip_id):
        raise HTTPException(404, "To-Do nicht gefunden")
    return {"message": "To-Do aktualisiert ✓"}


@router.delete("/{trip_id}/todos/{todo_id}")
def remove_todo(trip_id: int, todo_id: int, user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    if not delete_trip_todo(todo_id, trip_id):
        raise HTTPException(404, "To-Do nicht gefunden")
    return {"message": "To-Do gelöscht ✓"}

