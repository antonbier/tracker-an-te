"""
WanderSuite — /api/trackers (Multi-User)

Fixes applied:
  - POST /{id}/scan alias for /scrape
  - Validates return_date >= outbound_date (W1)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
import re, traceback, logging

from database import (
    create_tracker, list_trackers, get_tracker,
    delete_tracker, toggle_tracker, get_latest_snapshot,
    set_tracker_threshold, link_tracker_to_trip,
)
from scheduler import run_single_tracker
from auth_jwt import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class BaggageItem(BaseModel):
    type: str
    per_person: bool = True

    @field_validator("type")
    @classmethod
    def valid_type(cls, v):
        if v not in ("10kg", "20kg", "23kg"):
            raise ValueError("Gepäcktyp muss '10kg', '20kg' oder '23kg' sein")
        return v


class TrackerCreate(BaseModel):
    origin:        str
    destination:   str
    outbound_date: str
    return_date:   Optional[str] = None
    adults:        int = 1
    children:      int = 0
    baggage:       list[BaggageItem] = []
    seat_cost:     float = 0.0
    trip_id:       Optional[int] = None

    @field_validator("origin", "destination")
    @classmethod
    def iata_upper(cls, v):
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", v):
            raise ValueError("IATA-Code muss genau 3 Buchstaben haben")
        return v

    @field_validator("outbound_date", "return_date")
    @classmethod
    def valid_date(cls, v):
        if v is None:
            return v
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Datum muss im Format YYYY-MM-DD sein")
        # NEU-BUG 2: Datum darf nicht in der Vergangenheit liegen
        from datetime import date as _date
        try:
            parsed = _date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Ungültiges Datum: {v!r}")
        if parsed < _date.today():
            raise ValueError(
                f"outbound_date/return_date darf nicht in der Vergangenheit liegen "
                f"({v} < {_date.today().isoformat()})"
            )
        return v

    @field_validator("adults")
    @classmethod
    def min_adults(cls, v):
        if v < 1:
            raise ValueError("Mindestens 1 Erwachsener erforderlich")
        return v

    @model_validator(mode="after")
    def validate_return_after_outbound(self) -> "TrackerCreate":
        """FIX W1: Return date must not be before outbound date."""
        if self.return_date and self.outbound_date:
            if self.return_date < self.outbound_date:
                raise ValueError(
                    f"return_date ({self.return_date}) darf nicht vor "
                    f"outbound_date ({self.outbound_date}) liegen"
                )
        return self


def _uid(user: dict) -> int | None:
    uid = user.get("id", 0)
    return uid if uid else None


@router.get("")
def get_all_trackers(user: dict = Depends(get_current_user)):
    trackers = list_trackers(active_only=False, user_id=_uid(user))
    for t in trackers:
        snap = get_latest_snapshot(t["id"])
        t["latest_snapshot"] = snap
        # Block 8: current_price direkt auf Root für sofortige UI-Anzeige
        # ohne dass der User erst auf Refresh klicken muss
        t["current_price"] = snap.get("total_price") if snap else None
    return trackers


@router.post("", status_code=201)
def add_tracker(data: TrackerCreate, user: dict = Depends(get_current_user)):
    payload = data.model_dump()
    payload["baggage"] = [b.model_dump() for b in data.baggage]
    uid = user.get("id", 1) or 1
    tracker_id = create_tracker(payload, user_id=uid)
    if data.trip_id:
        link_tracker_to_trip(tracker_id, "flight", data.trip_id)
    return {"id": tracker_id, "message": "Tracker angelegt"}


@router.get("/{tracker_id}")
def get_one_tracker(tracker_id: int, user: dict = Depends(get_current_user)):
    t = get_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    t["latest_snapshot"] = get_latest_snapshot(tracker_id)
    return t


@router.delete("/{tracker_id}")
def remove_tracker(tracker_id: int, user: dict = Depends(get_current_user)):
    if not delete_tracker(tracker_id, user_id=_uid(user)):
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    return {"message": "Tracker gelöscht"}


@router.patch("/{tracker_id}/toggle")
def toggle(tracker_id: int, active: bool, user: dict = Depends(get_current_user)):
    if not toggle_tracker(tracker_id, active, user_id=_uid(user)):
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    return {"message": f"Tracker {'aktiviert' if active else 'pausiert'}"}


class ThresholdPayload(BaseModel):
    threshold: Optional[float] = None


@router.patch("/{tracker_id}/threshold")
def set_threshold(tracker_id: int, data: ThresholdPayload, user: dict = Depends(get_current_user)):
    t = get_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    value = round(data.threshold, 2) if data.threshold is not None else None
    set_tracker_threshold(tracker_id, value, user_id=_uid(user))
    label = f"gesetzt: unter {value} €" if value else "deaktiviert"
    return {"message": f"Preisalarm {label}", "threshold_price": value}


def _do_scrape(tracker_id: int, user: dict) -> dict:
    """Shared scrape logic for /scrape and /scan endpoints.
    BUG 3: Exception-Klassifizierung — kein roher 500-Stack.
    """
    t = get_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    try:
        snap = run_single_tracker(tracker_id)
        return {"message": "Scraping abgeschlossen", "snapshot": snap}
    except HTTPException:
        raise  # Bereits klassifiziert — durchreichen
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Scraping Fehler Tracker #{tracker_id}: {err_msg}")
        # Kein API-Key konfiguriert
        if "api_key" in err_msg.lower() or "serpapi" in err_msg.lower() or "key" in err_msg.lower():
            raise HTTPException(422, detail={
                "error": "missing_api_key",
                "message": "API-Key fehlt oder ist ungültig — Einstellungen → Provider prüfen",
                "raw": err_msg,
            })
        # Externe API antwortet mit Fehler (409, 503, Rate Limit …)
        if any(code in err_msg for code in ["409", "429", "503", "502", "Availability declined",
                                             "rate limit", "Rate limit", "temporarily"]):
            raise HTTPException(503, detail={
                "error": "provider_unavailable",
                "message": "Anbieter vorübergehend nicht verfügbar — später erneut versuchen",
                "raw": err_msg,
            })
        # Allgemeiner Scraping-Fehler — 422 mit verständlicher Meldung
        raise HTTPException(422, detail={
            "error": "scrape_failed",
            "message": f"Preisabfrage fehlgeschlagen: {err_msg}",
        })


class TrackerUpdate(BaseModel):
    """BUG 4 + NEU-BUG A: Partial update für einen bestehenden Ryanair-Tracker.
    NEU-BUG A: is_booked + booked_price fehlten → "Keine Änderungen" bei Buchung.
    """
    return_date:  Optional[str]   = None
    adults:       Optional[int]   = None
    children:     Optional[int]   = None
    seat_cost:    Optional[float] = None
    wish_price:   Optional[float] = None
    trip_id:      Optional[int]   = None
    # NEU-BUG A: Buchungsfelder
    is_booked:    Optional[int]   = None   # 0 oder 1
    booked_price: Optional[float] = None

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

    @field_validator("seat_cost", "wish_price")
    @classmethod
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError("Preis-Felder dürfen nicht negativ sein")
        return v


@router.patch("/{tracker_id}")
def update_tracker(tracker_id: int, data: TrackerUpdate, user: dict = Depends(get_current_user)):
    """BUG 4: Partial update — nur angegebene Felder werden überschrieben."""
    t = get_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")

    raw = data.model_dump()
    # is_booked=0 ist ein gültiger Wert (Buchung zurücksetzen) — nicht via "is not None" filtern
    updates = {}
    for k, v in raw.items():
        if v is None:
            continue
        updates[k] = v
    # is_booked=0 explizit erlauben (False-y aber gültig)
    if raw.get("is_booked") == 0:
        updates["is_booked"] = 0

    if not updates:
        return {"id": tracker_id, "message": "Keine Änderungen"}

    # wish_price → eigene Tabelle
    wish = updates.pop("wish_price", None)

    # NEU-BUG A: booked_price ohne is_booked → is_booked=1 implizit setzen
    if "booked_price" in updates and "is_booked" not in updates:
        updates["is_booked"] = 1

    # DB-Update für alle verbleibenden Felder
    if updates:
        from database import db as _db
        set_clauses = ", ".join(f"{k}=?" for k in updates)
        vals = list(updates.values()) + [tracker_id]
        with _db() as conn:
            conn.execute(
                f"UPDATE trackers SET {set_clauses} WHERE id=?", vals
            )

    if wish is not None:
        set_tracker_threshold(tracker_id, wish)

    changed = list(data.model_dump(exclude_none=True).keys())
    if raw.get("is_booked") == 0:
        changed.append("is_booked")
    logger.info(f"[Trackers] #{tracker_id} updated: {changed}")
    return {"id": tracker_id, "updated": changed, "message": "Tracker aktualisiert ✓"}


@router.post("/{tracker_id}/scrape")
def manual_scrape(tracker_id: int, user: dict = Depends(get_current_user)):
    return _do_scrape(tracker_id, user)


@router.post("/{tracker_id}/scan")
def manual_scan(tracker_id: int, user: dict = Depends(get_current_user)):
    """Alias for /scrape — both endpoints are supported."""
    return _do_scrape(tracker_id, user)


class TripLinkPayload(BaseModel):
    trip_id: Optional[int] = None


@router.patch("/{tracker_id}/link-trip")
def link_trip(tracker_id: int, data: TripLinkPayload, user: dict = Depends(get_current_user)):
    t = get_tracker(tracker_id, user_id=_uid(user))
    if not t:
        raise HTTPException(404, f"Tracker #{tracker_id} nicht gefunden")
    ok = link_tracker_to_trip(tracker_id, "flight", data.trip_id)
    return {"ok": ok, "trip_id": data.trip_id}
