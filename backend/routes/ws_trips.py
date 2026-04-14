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
    get_trackers_for_trip, mark_tracker_booked, unmark_tracker_booked,
    link_tracker_to_trip,
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

    prompt = f"""Du bist ein erfahrener Reise-Assistent. Erstelle 10 bis 15 konkrete, spezifische To-Dos für folgende Reise.

Ziel: {dest_desc}
Reiseart: {mode_label}{home_str}
Zeitraum: {dates or 'flexibel'}{budget_str}
Mitreisende: {trip.get('adults', 2)} Erw.{', ' + str(trip.get('children')) + ' Kind.' if trip.get('children') else ''}

Regeln:
- KEINE generischen To-Dos (nicht "Koffer packen" allein — stattdessen was für diese Reise spezifisch ist)
- Mische Kategorien sinnvoll: booking, documents, packing, general
- Berücksichtige Reiseziel und -art konkret (z.B. spezifische Dokumente, Währung, Klima, Aktivitäten)
- Antworte NUR mit JSON-Array, kein Text, kein Markdown:

[
  {{"task": "...", "category": "booking"}},
  {{"task": "...", "category": "documents"}},
  ...
]
Kategorien: booking, documents, packing, general."""

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
                    "max_tokens": 800,
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
            return [{"task": t.get("task",""), "category": t.get("category","general")} for t in todos[:15]]
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

    # KI To-Dos: überspringen wenn Reise in der Vergangenheit liegt
    from datetime import date
    start = trip_data.get("start_date") or ""
    is_past = start and start < date.today().isoformat()

    if is_past:
        logger.info(f"[WsTrips] Trip #{trip_id} ist vergangen — KI-Todos übersprungen")
        n_todos = 0
        todos = []
    else:
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




@router.post("/{trip_id}/todos/regenerate", status_code=200)
async def regenerate_todos(trip_id: int, user=Depends(get_current_user)):
    """Re-generate KI To-Dos for an existing trip (replaces existing todos)."""
    trip = get_ws_trip(trip_id, _uid(user))
    if not trip:
        raise HTTPException(404, "Trip nicht gefunden")
    # Delete all existing todos
    from database import db as _db
    with _db() as conn:
        conn.execute("DELETE FROM trip_todos WHERE trip_id=?", (trip_id,))
    # Regenerate
    todos = await _generate_todos(trip)
    n = create_trip_todos(trip_id, todos)
    return {"message": f"{n} To-Dos generiert ✓", "todos": todos}


# ── Tracker Slots ─────────────────────────────────────────────────────────────

@router.get("/{trip_id}/trackers")
def get_trip_trackers(trip_id: int, user=Depends(get_current_user)):
    """Return all trackers linked to this trip, grouped by type."""
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    return get_trackers_for_trip(trip_id)


class BookPayload(BaseModel):
    booked_price: float
    tracker_type: str   # 'flight' | 'google_flight' | 'hotel' | 'camping'


@router.post("/{trip_id}/trackers/{tracker_id}/book")
def book_tracker(trip_id: int, tracker_id: int, data: BookPayload, user=Depends(get_current_user)):
    """Mark a tracker as booked with a confirmed price."""
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    ok = mark_tracker_booked(tracker_id, data.tracker_type, data.booked_price, trip_id=trip_id)
    if not ok:
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Als gebucht markiert ✓", "booked_price": data.booked_price}


@router.delete("/{trip_id}/trackers/{tracker_id}/book")
def unbook_tracker(trip_id: int, tracker_id: int, tracker_type: str, user=Depends(get_current_user)):
    """Reset booking state on a tracker."""
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    ok = unmark_tracker_booked(tracker_id, tracker_type)
    if not ok:
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Buchung zurückgesetzt ✓"}


# ── Budget Breakdown ──────────────────────────────────────────────────────────

@router.get("/{trip_id}/budget")
def get_trip_budget(trip_id: int, user=Depends(get_current_user)):
    """
    Return budget breakdown:
      total_budget - booked_flight - booked_hotel = on_site_budget
    """
    trip = get_ws_trip(trip_id, _uid(user))
    if not trip:
        raise HTTPException(404, "Trip nicht gefunden")

    trackers = get_trackers_for_trip(trip_id)

    booked_flight = 0.0
    booked_hotel  = 0.0

    flight_tr = trackers.get("flight")
    if flight_tr and flight_tr.get("is_booked") and flight_tr.get("booked_price"):
        booked_flight = float(flight_tr["booked_price"])

    hotel_tr = trackers.get("hotel") or trackers.get("camping")
    if hotel_tr and hotel_tr.get("is_booked") and hotel_tr.get("booked_price"):
        booked_hotel = float(hotel_tr["booked_price"])

    total = float(trip.get("budget") or 0)
    on_site = max(0, total - booked_flight - booked_hotel)

    manual_expenses = float(trip.get("manual_expenses") or 0)
    on_site_net = max(0, total - booked_flight - booked_hotel - manual_expenses)

    return {
        "total_budget":      total,
        "booked_flight":     booked_flight,
        "booked_hotel":      booked_hotel,
        "manual_expenses":   manual_expenses,
        "on_site_budget":    on_site_net,
        "has_budget":        total > 0,
    }


class ManualExpensesPayload(BaseModel):
    manual_expenses: float = 0.0

@router.patch("/{trip_id}/manual-expenses")
def set_manual_expenses(trip_id: int, data: ManualExpensesPayload, user=Depends(get_current_user)):
    """Update manual_expenses for a trip."""
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    from database import db as _db
    with _db() as conn:
        conn.execute(
            "UPDATE ws_trips SET manual_expenses=?, updated_at=datetime('now') WHERE id=? AND user_id=?",
            (max(0.0, data.manual_expenses), trip_id, _uid(user))
        )
    return {"ok": True, "manual_expenses": data.manual_expenses}
