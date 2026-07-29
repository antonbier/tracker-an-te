"""
WanderSuite — /api/ics
ICS-Kalender-Export/Abo für WanderWizzard-Trips (ws_trips).

GET  /api/ics/token       (JWT)    -- gibt den (ggf. neu erzeugten) Abo-Token zurück
GET  /api/ics/{token}.ics (public) -- liefert den VCALENDAR-Feed; der Token selbst ist die Auth,
                                       damit Kalender-Apps (Google/Apple) den Feed ohne Login abonnieren können.
"""

import hmac as _hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from auth_db import list_users
from auth_jwt import get_current_user
from crud.settings import get_user_setting, save_user_setting
from crud.trips import list_ws_trips
from settings_manager import _get_fernet

router = APIRouter()
logger = logging.getLogger(__name__)


def _uid(user: dict) -> int:
    return user.get("id", 1) or 1


def _get_or_create_ics_token(user_id: int) -> str:
    fernet = _get_fernet()
    token = get_user_setting(user_id, "ics_token", fernet)
    if not token:
        token = secrets.token_urlsafe(24)
        save_user_setting(user_id, "ics_token", token, fernet)
    return token


def _resolve_user_by_ics_token(token: str) -> int | None:
    """Find which user owns this ICS token. Self-hosted scale (few users) -> linear scan is fine."""
    fernet = _get_fernet()
    candidate_ids = {1}  # Guest/Single-User-Default (kein users-Datensatz im AUTH_ENABLED=false-Modus)
    try:
        candidate_ids.update(u["id"] for u in list_users())
    except Exception:
        pass
    for uid in candidate_ids:
        stored = get_user_setting(uid, "ics_token", fernet)
        if stored and _hmac.compare_digest(stored, token):
            return uid
    return None


def _ics_escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> str:
    """RFC 5545 line folding — Zeilen dürfen max. 75 Oktette lang sein."""
    if len(line.encode()) <= 75:
        return line
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode()) > 74:
            out.append(cur)
            cur = " " + ch
        else:
            cur += ch
    out.append(cur)
    return "\r\n".join(out)


def _add_day(yyyymmdd: str) -> str:
    d = datetime.strptime(yyyymmdd, "%Y%m%d") + timedelta(days=1)
    return d.strftime("%Y%m%d")


def _build_ics(trips: list[dict]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//WanderSuite//ws-trips//DE",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:WanderSuite Reisen",
    ]
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for t in trips:
        start = (t.get("start_date") or "")[:10].replace("-", "")
        if not start:
            continue  # Trips ohne Datum (z.B. reine Inspire-Ideen) können nicht in den Kalender
        end_raw = (t.get("end_date") or "")[:10].replace("-", "") or start
        end = _add_day(end_raw)  # DTEND ist in ICS exklusiv -> +1 Tag für den letzten Reisetag
        title = t.get("title") or t.get("destination") or "Reise"
        lines += [
            "BEGIN:VEVENT",
            f"UID:ws-trip-{t['id']}@wandersuite",
            f"DTSTAMP:{now}",
            f"DTSTART;VALUE=DATE:{start}",
            f"DTEND;VALUE=DATE:{end}",
            _fold(f"SUMMARY:{_ics_escape(title)}"),
            _fold(f"LOCATION:{_ics_escape(t.get('destination') or '')}"),
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


@router.get("/token")
def get_ics_token(user: dict = Depends(get_current_user)):
    """Gibt den Abo-Token des eingeloggten Users zurück (erzeugt ihn beim ersten Aufruf)."""
    return {"token": _get_or_create_ics_token(_uid(user))}


@router.get("/{token}.ics")
def get_ics_feed(token: str):
    """Öffentlicher Kalender-Feed — der Token selbst ist die Authentifizierung."""
    uid = _resolve_user_by_ics_token(token)
    if uid is None:
        raise HTTPException(status_code=404, detail="Unbekannter Kalender-Token")
    trips = list_ws_trips(uid)
    body = _build_ics(trips)
    return Response(content=body, media_type="text/calendar; charset=utf-8")
