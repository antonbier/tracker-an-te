"""
WanderSuite — /api/emergency
Notfall-Infos: Notfallkontakte + Freitext-Notizen (Blutgruppe, Allergien, Medikamente).
Trip-unabhängig, Fernet-verschlüsselt über das bestehende user_settings-KV-Store
(analog ics_token) — kein neues Table-Schema nötig.
"""

import json
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from auth_jwt import get_current_user
from crud.settings import get_user_setting, save_user_setting
from settings_manager import _get_fernet

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


@router.get("")
def get_emergency_info(user: dict = Depends(get_current_user)):
    uid = _uid(user)
    fernet = _get_fernet()
    raw_contacts = get_user_setting(uid, "emergency_contacts", fernet)
    notes = get_user_setting(uid, "emergency_notes", fernet) or ""
    try:
        contacts = json.loads(raw_contacts) if raw_contacts else []
    except Exception:
        contacts = []
    return {"contacts": contacts, "notes": notes}


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
