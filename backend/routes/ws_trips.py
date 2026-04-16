"""
WanderSuite — /api/ws-trips
WanderWizzard Trip Container: anlegen, abrufen, To-Dos verwalten.
KI-To-Do-Generierung via OpenAI gpt-4o-mini beim Trip-Anlegen.

Fixes applied:
  - POST todos returns real id
  - PATCH /{id} full/partial trip update
  - PATCH /{id}/status shortcut
  - Validates end_date >= start_date (B2)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, model_validator
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

VALID_STATUSES = {"planning", "booked", "completed", "archived", "experienced"}


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

    @model_validator(mode="after")
    def validate_dates(self) -> "WsTripCreate":
        """FIX B2: Ensure end_date >= start_date when both are provided."""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError(
                    f"end_date ({self.end_date}) darf nicht vor start_date ({self.start_date}) liegen"
                )
        return self


class WsTripUpdate(BaseModel):
    """Partial update — all fields optional."""
    title:        Optional[str]   = None
    destination:  Optional[str]   = None
    start_date:   Optional[str]   = None
    end_date:     Optional[str]   = None
    budget:       Optional[float] = None
    travel_mode:  Optional[str]   = None
    home_airport: Optional[str]   = None
    adults:       Optional[int]   = None
    children:     Optional[int]   = None
    notes:        Optional[str]   = None
    status:       Optional[str]   = None

    @model_validator(mode="after")
    def validate_status_and_dates(self) -> "WsTripUpdate":
        if self.status is not None and self.status not in VALID_STATUSES:
            raise ValueError(f"Ungültiger Status. Erlaubt: {sorted(VALID_STATUSES)}")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) darf nicht vor start_date ({self.start_date}) liegen"
            )
        return self


class StatusUpdate(BaseModel):
    status: str

    @model_validator(mode="after")
    def validate_status(self) -> "StatusUpdate":
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Ungültiger Status. Erlaubt: {sorted(VALID_STATUSES)}")
        return self


class TodoCreate(BaseModel):
    task:     str
    category: Optional[str] = "general"
    due_date: Optional[str] = None


class TodoUpdate(BaseModel):
    due_date: Optional[str] = None


# ── KI To-Do Generierung ──────────────────────────────────────────────────────

async def _generate_todos(trip: dict) -> list[dict]:
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
- KEINE generischen To-Dos — was für diese Reise spezifisch ist
- Mische Kategorien: booking, documents, packing, general
- Antworte NUR mit JSON-Array, kein Text, kein Markdown:

[
  {{"task": "...", "category": "booking"}},
  ...
]"""

    try:
        import httpx
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": 800,
                    "temperature": 0.7,
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
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
    return [
        {"task": "Route & Stopps planen", "category": "general"},
        {"task": "Fahrzeug & Tankstand prüfen", "category": "general"},
        {"task": "Unterkunft entlang der Route buchen", "category": "booking"},
        {"task": "Pannenhilfe / ADAC prüfen", "category": "documents"},
        {"task": "Koffer & Dachbox packen", "category": "packing"},
    ]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def create_trip(data: WsTripCreate, user=Depends(get_current_user)):
    uid = _uid(user)
    trip_data = data.model_dump()

    if not trip_data.get("title"):
        dest = trip_data.get("destination") or trip_data.get("flex_month") or "Neue Reise"
        trip_data["title"] = dest

    trip_id = create_ws_trip(trip_data, user_id=uid)
    logger.info(f"[WsTrips] Trip #{trip_id} angelegt für user {uid}: {trip_data['title']}")

    from datetime import date
    start   = trip_data.get("start_date") or ""
    is_past = start and start < date.today().isoformat()

    if is_past:
        todos = []
    else:
        trip_data["id"] = trip_id
        todos = await _generate_todos(trip_data)
        create_trip_todos(trip_id, todos)

    return {"id": trip_id, "title": trip_data["title"], "todos": todos, "message": "Trip angelegt ✓"}


@router.get("")
def get_trips(user=Depends(get_current_user)):
    return list_ws_trips(_uid(user))


@router.get("/{trip_id}")
def get_trip(trip_id: int, user=Depends(get_current_user)):
    trip = get_ws_trip(trip_id, _uid(user))
    if not trip:
        raise HTTPException(404, "Trip nicht gefunden")
    trip["manual_expenses"] = float(trip.get("manual_expenses") or 0.0)
    trip["budget"]          = float(trip.get("budget") or 0.0) or None
    trip["adults"]          = int(trip.get("adults") or 2)
    trip["children"]        = int(trip.get("children") or 0)
    trip["travel_mode"]     = trip.get("travel_mode") or "flight"
    trip["status"]          = trip.get("status") or "planning"
    trip["vibes"]           = trip.get("vibes") or "[]"
    try:
        trip["todos"] = list_trip_todos(trip_id)
    except Exception:
        trip["todos"] = []
    return trip


@router.patch("/{trip_id}")
def update_trip(trip_id: int, data: WsTripUpdate, user=Depends(get_current_user)):
    """Partial update — only provided (non-None) fields are written."""
    trip = get_ws_trip(trip_id, _uid(user))
    if not trip:
        raise HTTPException(404, "Trip nicht gefunden")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        return {"id": trip_id, "message": "Keine Änderungen"}

    # If only one date is being updated, validate against existing stored date
    new_start = updates.get("start_date", trip.get("start_date"))
    new_end   = updates.get("end_date",   trip.get("end_date"))
    if new_start and new_end and new_end < new_start:
        raise HTTPException(422, f"end_date ({new_end}) darf nicht vor start_date ({new_start}) liegen")

    from database import db as _db
    set_clauses = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [trip_id, _uid(user)]
    with _db() as conn:
        conn.execute(
            f"UPDATE ws_trips SET {set_clauses}, updated_at=datetime('now') WHERE id=? AND user_id=?",
            values,
        )
    logger.info(f"[WsTrips] Trip #{trip_id} updated: {list(updates.keys())}")
    return {"id": trip_id, "updated": list(updates.keys()), "message": "Trip aktualisiert ✓"}


@router.patch("/{trip_id}/status")
def set_status(trip_id: int, data: StatusUpdate, user=Depends(get_current_user)):
    if not update_ws_trip_status(trip_id, data.status, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    return {"id": trip_id, "status": data.status, "message": "Status aktualisiert ✓"}


@router.delete("/{trip_id}")
def remove_trip(trip_id: int, mode: str = "trip_only", user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")

    if mode == "all":
        from database import db as _db
        try:
            with _db() as conn:
                for tbl in ("trackers", "gf_trackers", "homair_trackers", "booking_trackers"):
                    try:
                        conn.execute(f"DELETE FROM {tbl} WHERE trip_id=?", (trip_id,))
                    except Exception as e:
                        logger.warning(f"[WsTrips] Delete {tbl}: {e}")
        except Exception as e:
            logger.warning(f"[WsTrips] Tracker-Cleanup teilweise fehlgeschlagen: {e}")

    if not delete_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")

    return {"message": "Trip + Tracker gelöscht ✓" if mode == "all" else "Trip gelöscht ✓"}


# ── To-Do Endpoints ───────────────────────────────────────────────────────────

@router.get("/{trip_id}/todos")
def get_todos(trip_id: int, user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    return list_trip_todos(trip_id)


@router.post("/{trip_id}/todos", status_code=201)
def add_todo(trip_id: int, data: TodoCreate, user=Depends(get_current_user)):
    """Returns the new todo id + full object so frontend never needs Date.now() fake-ids."""
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")

    create_trip_todos(trip_id, [{"task": data.task, "category": data.category, "due_date": data.due_date}])

    from database import db as _db
    with _db() as conn:
        row = conn.execute(
            "SELECT id, task, category, is_done, due_date, sort_order, created_at "
            "FROM trip_todos WHERE trip_id=? ORDER BY id DESC LIMIT 1",
            (trip_id,)
        ).fetchone()

    if row:
        todo = dict(row)
        return {
            "id":       todo["id"],
            "task":     todo["task"],
            "category": todo["category"],
            "is_done":  todo["is_done"],
            "due_date": todo["due_date"],
            "trip_id":  trip_id,
            "message":  "To-Do hinzugefügt ✓",
        }
    return {"message": "To-Do hinzugefügt ✓"}


@router.patch("/{trip_id}/todos/{todo_id}/due")
def set_todo_due(trip_id: int, todo_id: int, data: TodoUpdate, user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    from database import db as _db
    with _db() as conn:
        r = conn.execute(
            "UPDATE trip_todos SET due_date=? WHERE id=? AND trip_id=?",
            (data.due_date, todo_id, trip_id)
        )
    if r.rowcount == 0:
        raise HTTPException(404, "To-Do nicht gefunden")
    return {"ok": True, "due_date": data.due_date}


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
    trip = get_ws_trip(trip_id, _uid(user))
    if not trip:
        raise HTTPException(404, "Trip nicht gefunden")
    from database import db as _db
    with _db() as conn:
        conn.execute("DELETE FROM trip_todos WHERE trip_id=?", (trip_id,))
    todos = await _generate_todos(trip)
    n = create_trip_todos(trip_id, todos)
    return {"message": f"{n} To-Dos generiert ✓", "todos": todos}


# ── Tracker Slots ─────────────────────────────────────────────────────────────

@router.get("/{trip_id}/trackers")
def get_trip_trackers(trip_id: int, user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    return get_trackers_for_trip(trip_id)


class BookPayload(BaseModel):
    booked_price: float
    tracker_type: str


@router.post("/{trip_id}/trackers/{tracker_id}/book")
def book_tracker(trip_id: int, tracker_id: int, data: BookPayload, user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    if not mark_tracker_booked(tracker_id, data.tracker_type, data.booked_price, trip_id=trip_id):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Als gebucht markiert ✓", "booked_price": data.booked_price}


@router.delete("/{trip_id}/trackers/{tracker_id}/book")
def unbook_tracker(trip_id: int, tracker_id: int, tracker_type: str, user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    if not unmark_tracker_booked(tracker_id, tracker_type):
        raise HTTPException(404, "Tracker nicht gefunden")
    return {"message": "Buchung zurückgesetzt ✓"}


# ── Budget Breakdown ──────────────────────────────────────────────────────────

@router.get("/{trip_id}/budget")
def get_trip_budget(trip_id: int, user=Depends(get_current_user)):
    trip = get_ws_trip(trip_id, _uid(user))
    if not trip:
        raise HTTPException(404, "Trip nicht gefunden")

    try:
        trackers = get_trackers_for_trip(trip_id)
    except Exception:
        trackers = {}

    booked_flight = 0.0
    booked_hotel  = 0.0
    try:
        ft = trackers.get("flight")
        if ft and ft.get("is_booked") and ft.get("booked_price"):
            booked_flight = float(ft["booked_price"])
        ht = trackers.get("hotel") or trackers.get("camping")
        if ht and ht.get("is_booked") and ht.get("booked_price"):
            booked_hotel = float(ht["booked_price"])
    except Exception:
        pass

    total           = float(trip.get("budget") or 0)
    manual_expenses = float(trip.get("manual_expenses") or 0)
    on_site_net     = max(0, total - booked_flight - booked_hotel - manual_expenses)

    return {
        "total_budget":    total,
        "booked_flight":   booked_flight,
        "booked_hotel":    booked_hotel,
        "manual_expenses": manual_expenses,
        "on_site_budget":  on_site_net,
        "has_budget":      total > 0,
    }


class ManualExpensesPayload(BaseModel):
    manual_expenses: float = 0.0


@router.patch("/{trip_id}/manual-expenses")
def set_manual_expenses(trip_id: int, data: ManualExpensesPayload, user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    val = max(0.0, float(data.manual_expenses))
    from database import db as _db
    with _db() as conn:
        conn.execute(
            "UPDATE ws_trips SET manual_expenses=?, updated_at=datetime('now') WHERE id=? AND user_id=?",
            (val, trip_id, _uid(user))
        )
    return {"ok": True, "manual_expenses": val}
