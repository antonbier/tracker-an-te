"""
WanderSuite — /api/ws-trips
WanderWizzard Trip Container: anlegen, abrufen, To-Dos verwalten.
KI-To-Do-Generierung via OpenAI gpt-4o-mini beim Trip-Anlegen.

Fixes applied:
  - POST todos returns real id
  - PATCH /{id} full/partial trip update
  - PATCH /{id}/status shortcut
  - Validates end_date >= start_date (B2)
  - BUG 2: start_date optional (Flex-Trips), aber Response-Warning wenn beide fehlen
  - BUG 5: budget >= 0 Validierung
  - BUG 6: HTML-Sanitizer auf title/destination/notes
  - BUG 7: max_length Constraints

API-BUG 1 Klarstellung:
  Todo-Toggle läuft über PATCH /{trip_id}/todos/{todo_id}/toggle
  (nicht über PATCH /{trip_id}/todos/{todo_id} — dieser Endpoint existiert nicht).
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, model_validator, field_validator, constr
from typing import Optional
import logging, json, os, re, html


# ── Minimal HTML-Sanitizer (kein externen Deps) ───────────────────────────────
# Entfernt <script>, <iframe>, Event-Handler-Attribute und HTML-Tags komplett.
# Für reine Texteingaben (Titel, Notizen) ausreichend — BUG 6.
_TAG_RE   = re.compile(r'<[^>]+>')
_SCRIPT_RE = re.compile(r'<\s*script[\s\S]*?</\s*script\s*>', re.IGNORECASE)
_IFRAME_RE = re.compile(r'<\s*iframe[\s\S]*?</\s*iframe\s*>', re.IGNORECASE)

def _sanitize(value: str | None, max_len: int = 500) -> str | None:
    """Strip HTML tags + limit length. Returns None for empty strings."""
    if value is None:
        return None
    v = str(value)
    v = _SCRIPT_RE.sub('', v)
    v = _IFRAME_RE.sub('', v)
    v = _TAG_RE.sub('', v)
    v = html.unescape(v).strip()
    v = v[:max_len]
    return v or None

from crud.trackers import (
    get_trackers_for_trip,
    mark_tracker_booked,
    unmark_tracker_booked,
    link_tracker_to_trip,
)
from crud.trips import (
    create_ws_trip,
    list_ws_trips,
    get_ws_trip,
    update_ws_trip_status,
    delete_ws_trip,
    create_trip_todos,
    list_trip_todos,
    toggle_trip_todo,
    delete_trip_todo,
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
    # BUG 7: max_length Validierung auf alle String-Felder
    title:              str
    destination:        Optional[str] = ""
    start_date:         Optional[str] = None
    end_date:           Optional[str] = None
    trip_type:          Optional[str] = "flight"
    # BUG 5: budget darf nicht negativ sein
    budget:             Optional[float] = None
    path:               Optional[str] = "known"
    travel_mode:        Optional[str] = "flight"
    vibes:              Optional[list[str]] = []
    wish_text:          Optional[str] = None
    flex_month:         Optional[str] = None
    flex_nights:        Optional[int] = None
    max_time:           Optional[str] = None
    home_airport:       Optional[str] = None
    adults:             Optional[int] = 2
    children:           Optional[int] = 0
    notes:              Optional[str] = None
    # On-the-fly container: verknüpft mit detected_trip
    source_detected_id: Optional[int] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        # BUG 7: Längen-Limit
        if len(v) > 200:
            raise ValueError("title darf maximal 200 Zeichen haben")
        # BUG 6: HTML-Sanitizing
        clean = _sanitize(v, max_len=200)
        if not clean:
            raise ValueError("title darf nicht leer oder nur HTML sein")
        return clean

    @field_validator("destination", "wish_text", mode="before")
    @classmethod
    def sanitize_short_text(cls, v):
        if v is None: return v
        return _sanitize(str(v), max_len=500)

    @field_validator("notes", mode="before")
    @classmethod
    def sanitize_notes(cls, v):
        # DES-1: notes max 2000 Zeichen (50.000 wurde ohne Fehler akzeptiert)
        if v is None: return v
        return _sanitize(str(v), max_len=2000)

    @field_validator("budget", mode="before")
    @classmethod
    def validate_budget(cls, v):
        # BUG 5: kein negatives Budget
        if v is not None and float(v) < 0:
            raise ValueError("budget muss >= 0 sein")
        return v

    @field_validator("adults")
    @classmethod
    def validate_adults(cls, v):
        if v is not None and v < 1:
            raise ValueError("adults muss mindestens 1 sein")
        return v

    @field_validator("children")
    @classmethod
    def validate_children(cls, v):
        if v is not None and v < 0:
            raise ValueError("children darf nicht negativ sein")
        return v

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
    """Partial update — all fields optional.

    title vs. destination:
      - title       = kosmetischer Anzeigename (z.B. "Roadtrip 2025"), darf NULL sein
      - destination = geocodierter Ortname, steuert Wetter/Maps, zwingend bei Geo-Edit
      - lat / lon   = Koordinaten zum Ort, werden zusammen mit destination gesetzt
    """
    title:           Optional[str]   = None
    destination:     Optional[str]   = None
    lat:             Optional[float] = None
    lon:             Optional[float] = None
    start_date:      Optional[str]   = None
    end_date:        Optional[str]   = None
    budget:          Optional[float] = None
    # NEU-BUG B: manual_expenses fehlte — Budget-Widget konnte nicht speichern
    manual_expenses: Optional[float] = None
    travel_mode:     Optional[str]   = None
    home_airport: Optional[str]   = None
    adults:       Optional[int]   = None
    children:     Optional[int]   = None
    notes:        Optional[str]   = None
    status:       Optional[str]   = None

    @field_validator("title", "destination", mode="before")
    @classmethod
    def sanitize_update_short(cls, v):
        if v is None: return v
        return _sanitize(str(v), max_len=200)

    @field_validator("notes", mode="before")
    @classmethod
    def sanitize_update_notes(cls, v):
        # DES-1: notes max 2000 Zeichen
        if v is None: return v
        return _sanitize(str(v), max_len=2000)

    @field_validator("budget", mode="before")
    @classmethod
    def validate_update_budget(cls, v):
        if v is not None and float(v) < 0:
            raise ValueError("budget muss >= 0 sein")
        return v

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

    @field_validator("task")
    @classmethod
    def validate_task(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("task darf nicht leer sein")
        if len(v) > 500:
            raise ValueError("task darf maximal 500 Zeichen haben")
        return _sanitize(v, max_len=500) or v

    @field_validator("due_date")
    @classmethod
    def validate_due_date_create(cls, v):
        # NEU-BUG 5: Format prüfen, Vergangenheit erlaubt (für Import-Szenarien)
        if v is None: return v
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"due_date muss im Format YYYY-MM-DD sein, erhalten: {v!r}")
        return v


class TodoUpdate(BaseModel):
    """NEU-BUG 4 + API-BUG 1: is_done + due_date + task editierbar."""
    is_done:  Optional[int] = None   # 0 oder 1 — direktes Setzen statt Toggle
    due_date: Optional[str] = None
    task:     Optional[str] = None


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

    # On-the-fly: link to detected_trip if provided
    detected_id = trip_data.pop("source_detected_id", None)
    trip_id = create_ws_trip(trip_data, user_id=uid)
    logger.info(f"[WsTrips] Trip #{trip_id} angelegt für user {uid}: {trip_data['title']}")
    # Store link in ws_trips row for future hub lookups
    if detected_id:
        try:
            from core.database import db as _db
            with _db() as conn:
                conn.execute(
                    "ALTER TABLE ws_trips ADD COLUMN source_detected_id INTEGER DEFAULT NULL"
                )
        except Exception:
            pass  # column already exists
        try:
            from core.database import db as _db
            with _db() as conn:
                conn.execute(
                    "UPDATE ws_trips SET source_detected_id=? WHERE id=?",
                    (detected_id, trip_id)
                )
        except Exception as e:
            logger.warning(f"[WsTrips] source_detected_id link failed: {e}")

    from datetime import date
    start   = trip_data.get("start_date") or ""
    is_past = start and start < date.today().isoformat()

    if is_past:
        todos = []
    else:
        trip_data["id"] = trip_id
        todos = await _generate_todos(trip_data)
        create_trip_todos(trip_id, todos)

    warnings = []
    if not trip_data.get("start_date"):
        warnings.append("start_date fehlt — Phasenberechnung und Wetter-Widget nicht verfügbar")
    if not trip_data.get("end_date"):
        warnings.append("end_date fehlt — Archivierungserkennung nicht verfügbar")
    resp = {"id": trip_id, "title": trip_data["title"], "todos": todos, "message": "Trip angelegt ✓"}
    if warnings:
        resp["warnings"] = warnings
    return resp


@router.get("")
def get_trips(user=Depends(get_current_user)):
    return list_ws_trips(_uid(user))


@router.get("/export")
def export_trips(user=Depends(get_current_user)):
    """NEU-BUG 3: Route muss VOR /{trip_id} stehen — sonst 422 'not a valid int'.
    Exportiert alle Trips des Users als JSON.
    """
    trips = list_ws_trips(_uid(user))
    return {
        "exported_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "count":       len(trips),
        "trips":       trips,
    }


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

    from core.database import db as _db
    set_clauses = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [trip_id, _uid(user)]
    with _db() as conn:
        conn.execute(
            f"UPDATE ws_trips SET {set_clauses}, updated_at=datetime('now') WHERE id=? AND user_id=?",
            values,
        )
    logger.info(f"[WsTrips] Trip #{trip_id} updated: {list(updates.keys())}")
    # D1: vollständiges Objekt zurückgeben
    updated_trip = get_ws_trip(trip_id, _uid(user))
    if updated_trip:
        updated_trip.setdefault("todos", [])
        return {"id": trip_id, "updated": list(updates.keys()),
                "message": "Trip aktualisiert ✓", "trip": updated_trip}
    return {"id": trip_id, "updated": list(updates.keys()), "message": "Trip aktualisiert ✓"}


@router.patch("/{trip_id}/status")
def set_status(trip_id: int, data: StatusUpdate, user=Depends(get_current_user)):
    if not update_ws_trip_status(trip_id, data.status, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    return {"id": trip_id, "status": data.status, "message": "Status aktualisiert ✓"}


@router.delete("/{trip_id}")
def remove_trip(trip_id: int, mode: str = "trip_only", user=Depends(get_current_user)):
    """3-Wege-Löschlogik:
    - Dawarich-Trips (source_detected_id gesetzt, source='dawarich'): SOFT-DELETE → ignored=1
    - Manuelle Trips (source_detected_id, source='manual'): HARD-DELETE des detected_trip
    - WanderWizzard-Trips (kein source_detected_id): HARD-DELETE ws_trip + optional Tracker
    """
    uid = _uid(user)
    trip = get_ws_trip(trip_id, uid)
    if not trip:
        raise HTTPException(404, "Trip nicht gefunden")

    detected_id = trip.get("source_detected_id")

    if detected_id:
        # Typ A/B: Hat verknüpften detected_trip
        from core.database import db as _db
from crud.trips import delete_detected_trip
        # Herausfinden ob Dawarich oder Manuell
with db() as conn:
            det_row = conn.execute(
                "SELECT source FROM detected_trips WHERE id=?", (detected_id,)
            ).fetchone()
if det_row and det_row["source"] == "dawarich":
            # Typ A: Soft-Delete — ignored=1
            delete_detected_trip(detected_id, user_id=uid, hard=False)
            delete_ws_trip(trip_id, uid)
            logger.info(f"[WsTrips] Dawarich Trip #{detected_id} soft-deleted (ignored=1), ws_trip #{trip_id} removed")
            return {"message": "Reise archiviert (Dawarich-Sync bleibt aktiv) ✓"}
        else:
            # Typ B: Hard-Delete des detected_trip
            delete_detected_trip(detected_id, user_id=uid, hard=True)
            delete_ws_trip(trip_id, uid)
            logger.info(f"[WsTrips] Manual Trip #{detected_id} hard-deleted, ws_trip #{trip_id} removed")
            return {"message": "Manuelle Reise vollständig gelöscht ✓"}

    # Typ C: Reiner WanderWizzard-Trip — kein detected_trip
    if mode == "all":
        from core.database import db as _db
        try:
            with _db() as conn:
                for tbl in ("trackers", "gf_trackers", "homair_trackers", "booking_trackers"):
                    try:
                        conn.execute(f"DELETE FROM {tbl} WHERE trip_id=?", (trip_id,))
                    except Exception as e:
                        logger.warning(f"[WsTrips] Delete {tbl}: {e}")
        except Exception as e:
            logger.warning(f"[WsTrips] Tracker-Cleanup teilweise fehlgeschlagen: {e}")

    if not delete_ws_trip(trip_id, uid):
        raise HTTPException(404, "Trip nicht gefunden")

    return {"message": "Trip + Tracker gelöscht ✓" if mode == "all" else "Trip gelöscht ✓"}





# ── Trip Hero-Bild ────────────────────────────────────────────────────────────

class TripImagePayload(BaseModel):
    image_url:        Optional[str] = None
    image_author:     Optional[str] = None
    image_author_url: Optional[str] = None


@router.patch("/{trip_id}/image")
def set_trip_image(trip_id: int, data: TripImagePayload, user=Depends(get_current_user)):
    """Speichert gecachtes Unsplash-Bild + Fotografen-Credits am Trip."""
    uid = _uid(user)
    trip = get_ws_trip(trip_id, uid)
    if not trip:
        raise HTTPException(404, "Trip nicht gefunden")
    from core.database import db as _db
    with _db() as conn:
        conn.execute(
            """UPDATE ws_trips
               SET image_url=?, image_author=?, image_author_url=?,
                   updated_at=datetime('now')
               WHERE id=? AND user_id=?""",
            (data.image_url, data.image_author, data.image_author_url, trip_id, uid)
        )
    logger.info(f"[WsTrips] Trip #{trip_id} image cached: {data.image_url}")
    return {"ok": True, "image_url": data.image_url}

# ── ActualBudget Sync ─────────────────────────────────────────────────────────

@router.post("/{trip_id}/sync-budget")
def sync_actual_budget(trip_id: int, user=Depends(get_current_user)):
    """Sync ActualBudget transactions for the trip date range.
    Reads actual_url, actual_token, actual_file from user settings.
    Stores total + compact transaction list in ws_trips row.
    """
    uid  = _uid(user)
    trip = get_ws_trip(trip_id, uid)
    if not trip:
        raise HTTPException(404, "Trip nicht gefunden")

    start_date = trip.get("start_date")
    end_date   = trip.get("end_date") or start_date
    if not start_date:
        raise HTTPException(400, "Trip hat kein Startdatum — Budget-Sync nicht möglich")

    from settings_manager import get_user_setting_value, get_setting_value
    actual_url   = (get_user_setting_value(uid, "actual_url")   or get_setting_value("actual_url")   or "").strip()
    actual_token = (get_user_setting_value(uid, "actual_token") or get_setting_value("actual_token") or "").strip()
    actual_file  = (get_user_setting_value(uid, "actual_file")  or get_setting_value("actual_file")  or "").strip()
    travel_cats  = (get_user_setting_value(uid, "travel_categories") or "").strip()

    if not actual_url or not actual_token:
        raise HTTPException(400, "ActualBudget URL oder Passwort nicht konfiguriert (Einstellungen → Bridges)")

    # Parse category filter
    cats = [c.strip() for c in travel_cats.split(",") if c.strip()] if travel_cats else []

    try:
        from actual_budget import get_travel_expenses
        result = get_travel_expenses(
            base_url=actual_url,
            password=actual_token,
            budget_file=actual_file or "",
            category_names=cats,
            year=None,  # Wir filtern manuell nach Datum
        )
    except Exception as e:
        raise HTTPException(502, f"ActualBudget Verbindung fehlgeschlagen: {e}")

    if "error" in result:
        raise HTTPException(502, result["error"])

    # Filter transactions to trip date range
    all_txs = result.get("transactions", [])
    trip_txs = [
        tx for tx in all_txs
        if start_date <= (tx.get("date") or "") <= end_date
    ]

    # Compact transaction list: date, payee/notes, amount
    compact = [
        {
            "date":   tx.get("date", ""),
            "name":   (tx.get("payee") or tx.get("notes") or "").strip()[:60],
            "amount": round(abs(tx.get("amount", 0)), 2),
        }
        for tx in trip_txs
        if tx.get("amount", 0) != 0
    ]
    compact.sort(key=lambda x: x["date"], reverse=True)

    total_synced = round(sum(c["amount"] for c in compact), 2)

    from core.database import db as _db
    from datetime import datetime
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    with _db() as conn:
        conn.execute(
            """UPDATE ws_trips
               SET synced_expenses=?, synced_transactions_json=?, synced_at=?,
                   updated_at=datetime('now')
               WHERE id=? AND user_id=?""",
            (total_synced, json.dumps(compact), now, trip_id, uid)
        )

    logger.info(f"[WsTrips] Budget-Sync Trip #{trip_id}: {len(compact)} Tx, {total_synced} €")
    return {
        "synced_expenses":     total_synced,
        "synced_transactions": compact,
        "synced_at":           now,
        "tx_count":            len(compact),
        "message":             f"{len(compact)} Transaktionen synchronisiert ✓",
    }
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

    from core.database import db as _db
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
    from core.database import db as _db
    with _db() as conn:
        r = conn.execute(
            "UPDATE trip_todos SET due_date=? WHERE id=? AND trip_id=?",
            (data.due_date, todo_id, trip_id)
        )
    if r.rowcount == 0:
        raise HTTPException(404, "To-Do nicht gefunden")
    return {"ok": True, "due_date": data.due_date}


@router.patch("/{trip_id}/todos/{todo_id}")
def update_todo(trip_id: int, todo_id: int, data: TodoUpdate, user=Depends(get_current_user)):
    """API-BUG 1: Direkter PATCH auf Todo — setzt is_done, task oder due_date.
    Ergänzt den /toggle-Endpoint: ist_done=0/1 kann direkt gesetzt werden.
    """
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    updates: dict = {}
    if data.is_done is not None:
        if data.is_done not in (0, 1):
            raise HTTPException(422, "is_done muss 0 oder 1 sein")
        updates["is_done"] = data.is_done
    if data.due_date is not None:
        updates["due_date"] = data.due_date
    if data.task is not None:
        task = data.task.strip()
        if not task:
            raise HTTPException(422, "task darf nicht leer sein")
        updates["task"] = _sanitize(task, max_len=500) or task
    if not updates:
        return {"ok": True, "message": "Keine Änderungen"}
    from core.database import db as _db
    set_clause = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [todo_id, trip_id]
    with _db() as conn:
        r = conn.execute(
            f"UPDATE trip_todos SET {set_clause} WHERE id=? AND trip_id=?", vals
        )
    if r.rowcount == 0:
        raise HTTPException(404, "To-Do nicht gefunden")
    return {"ok": True, "updated": list(updates.keys()), "message": "To-Do aktualisiert ✓"}


@router.patch("/{trip_id}/todos/{todo_id}/toggle")
def toggle_todo(trip_id: int, todo_id: int, user=Depends(get_current_user)):
    """Toggle is_done (0→1 oder 1→0) für ein einzelnes To-Do.
    API-BUG 1 Klarstellung: Der korrekte Endpoint ist
    PATCH /api/ws-trips/{trip_id}/todos/{todo_id}/toggle
    — nicht PATCH /api/ws-trips/{trip_id}/todos/{todo_id}.
    Letzterer existiert nicht und liefert 405.
    """
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
    from core.database import db as _db
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
    synced_expenses = float(trip.get("synced_expenses") or 0)

    # synced_transactions: parse stored JSON list
    synced_tx_raw = trip.get("synced_transactions_json") or "[]"
    try:
        synced_transactions = json.loads(synced_tx_raw)
    except Exception:
        synced_transactions = []

    total_spent = booked_flight + booked_hotel + manual_expenses + synced_expenses
    remaining   = total - total_spent  # kann negativ sein
    on_site_net = max(0.0, total - booked_flight - booked_hotel - manual_expenses - synced_expenses)

    return {
        "total_budget":         total,
        "booked_flight":        booked_flight,
        "booked_hotel":         booked_hotel,
        "manual_expenses":      manual_expenses,
        "synced_expenses":      synced_expenses,
        "synced_transactions":  synced_transactions,
        "synced_at":            trip.get("synced_at"),
        "on_site_budget":       on_site_net,
        "remaining":            remaining,
        "total_spent":          total_spent,
        "has_budget":           total > 0,
    }


class ManualExpensesPayload(BaseModel):
    manual_expenses: float = 0.0


@router.patch("/{trip_id}/manual-expenses")
def set_manual_expenses(trip_id: int, data: ManualExpensesPayload, user=Depends(get_current_user)):
    if not get_ws_trip(trip_id, _uid(user)):
        raise HTTPException(404, "Trip nicht gefunden")
    val = max(0.0, float(data.manual_expenses))
    from core.database import db as _db
    with _db() as conn:
        conn.execute(
            "UPDATE ws_trips SET manual_expenses=?, updated_at=datetime('now') WHERE id=? AND user_id=?",
            (val, trip_id, _uid(user))
        )
    return {"ok": True, "manual_expenses": val}
