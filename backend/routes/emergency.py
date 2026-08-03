"""
WanderSuite — /api/emergency
Notfall-Infos: Notfallkontakte + Freitext-Notizen (Blutgruppe, Allergien, Medikamente).
Trip-unabhängig, Fernet-verschlüsselt über das bestehende user_settings-KV-Store
(analog ics_token) — kein neues Table-Schema nötig.
"""

import html as html_escape
import json
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from auth_jwt import get_current_user
from crud.settings import get_user_setting, save_user_setting
from settings_manager import _get_fernet
from token_auth import get_or_create_token, resolve_user_by_token

router = APIRouter()

_TAG_RE = re.compile(r"<[^>]+>")


def _sanitize(value: str | None, max_len: int = 300) -> str:
    if not value:
        return ""
    return _TAG_RE.sub("", str(value)).strip()[:max_len]


def _uid(user: dict) -> int:
    return user.get("id", 1) or 1


class Contact(BaseModel):
    name: str
    phone: str
    relation: Optional[str] = None


class EmergencyInfo(BaseModel):
    contacts: list[Contact] = []
    notes: str = ""


def _load_emergency(uid: int) -> dict:
    fernet = _get_fernet()
    raw_contacts = get_user_setting(uid, "emergency_contacts", fernet)
    notes = get_user_setting(uid, "emergency_notes", fernet) or ""
    try:
        contacts = json.loads(raw_contacts) if raw_contacts else []
    except Exception:
        contacts = []
    return {"contacts": contacts, "notes": notes}


@router.get("")
def get_emergency_info(user: dict = Depends(get_current_user)):
    return _load_emergency(_uid(user))


@router.put("")
def save_emergency_info(data: EmergencyInfo, user: dict = Depends(get_current_user)):
    uid = _uid(user)
    fernet = _get_fernet()
    contacts = [
        {
            "name": _sanitize(c.name, 100),
            "phone": _sanitize(c.phone, 40),
            "relation": _sanitize(c.relation, 60),
        }
        for c in data.contacts
        if c.name and c.phone
    ]
    save_user_setting(uid, "emergency_contacts", json.dumps(contacts), fernet)
    save_user_setting(uid, "emergency_notes", _sanitize(data.notes, 2000), fernet)
    return {"message": "Gespeichert ✓"}


# ── Notfall-Karte: druckbare/teilbare öffentliche Ansicht ─────────────────────
# Der eigentliche Mehrwert von Notfall-Infos entsteht nicht dadurch, dass der
# Reisende selbst sie im Akutfall in der App nachschlägt (unrealistisch), sondern
# dadurch, dass sie VORHER ausgedruckt (Pass/Portemonnaie) oder mit Mitreisenden
# geteilt wird. Token-Auflösung analog ICS-Kalender-Abo (token_auth.py) — der
# Token selbst ist die Auth, damit die Karte ohne Login abrufbar ist.

@router.get("/token")
def get_emergency_token(user: dict = Depends(get_current_user)):
    """Gibt den Karten-Token des eingeloggten Users zurück (erzeugt ihn beim ersten Aufruf)."""
    return {"token": get_or_create_token("emergency_token", _uid(user))}


def _esc(value: str) -> str:
    return html_escape.escape(value or "")


@router.get("/card/{token}", response_class=HTMLResponse)
def get_emergency_card(token: str):
    """Öffentliche, eigenständige HTML-Seite zum Drucken/Teilen — der Token selbst
    ist die Authentifizierung. Kein JS, kein externer Fetch (funktioniert offline
    nach dem Laden, keine CSP-Konflikte)."""
    uid = resolve_user_by_token("emergency_token", token)
    if uid is None:
        raise HTTPException(status_code=404, detail="Unbekannter Notfall-Karten-Token")
    info = _load_emergency(uid)

    contacts_html = "".join(
        f'<div class="contact"><div class="name">{_esc(c.get("name"))}'
        f'{" · " + _esc(c["relation"]) if c.get("relation") else ""}</div>'
        f'<div class="phone">📞 {_esc(c.get("phone"))}</div></div>'
        for c in info["contacts"]
    ) or '<p class="muted">Keine Notfallkontakte hinterlegt.</p>'

    notes_html = f'<div class="notes">{_esc(info["notes"])}</div>' if info["notes"] else ""

    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Notfall-Infos</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 480px; margin: 2rem auto; padding: 0 1.25rem; color: #1a1a1a; line-height: 1.5; }}
  h1 {{ font-size: 1.4rem; border-bottom: 3px solid #c4622d; padding-bottom: .6rem; margin-bottom: .25rem; }}
  h2 {{ font-size: .85rem; text-transform: uppercase; letter-spacing: .05em; color: #6b6b6b; margin-top: 1.5rem; }}
  .contact {{ padding: .6rem 0; border-bottom: 1px solid #eee; }}
  .contact .name {{ font-weight: 600; }}
  .contact .phone {{ font-size: 1.15rem; margin-top: .15rem; }}
  .notes {{ white-space: pre-wrap; background: #f7f3ee; padding: 1rem; border-radius: 10px; margin-top: .5rem; }}
  .muted {{ color: #6b6b6b; font-size: .9rem; }}
  .print-hint {{ font-size: .8rem; color: #6b6b6b; margin-top: 2rem; border-top: 1px solid #eee; padding-top: 1rem; }}
  @media print {{ .print-hint {{ display: none; }} }}
</style>
</head>
<body>
  <h1>🆘 Notfall-Infos</h1>
  <h2>Notfallkontakte</h2>
  {contacts_html}
  {notes_html}
  <p class="print-hint">💡 Diese Seite kann ausgedruckt (Strg/Cmd+P) und im Reisepass mitgeführt oder vor der Reise an Mitreisende geteilt werden.</p>
</body>
</html>"""
