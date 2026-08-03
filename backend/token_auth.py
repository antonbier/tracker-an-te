"""
WanderSuite — token_auth.py
Gemeinsamer Resolver für Setting-basierte Zugriffs-Token (ICS-Kalender-Abo,
Notfall-Karte, ...): jeder dieser Token ist ein zufälliger String, der als
gewöhnlicher Wert im user_settings-KV-Store liegt (Fernet-verschlüsselt,
analog jedem anderen Setting) — kein eigenes Tabellenschema pro Token-Typ.

Auflösung "Token -> User" läuft über einen linearen Scan aller User-IDs
(Self-hosted-Skala mit wenigen Usern macht das unkritisch) statt über eine
separate Lookup-Tabelle, weil Fernet-Werte nicht durchsuchbar sind.
"""

import hmac as _hmac
import secrets

from auth_db import list_users
from crud.settings import get_user_setting, save_user_setting
from settings_manager import _get_fernet


def get_or_create_token(setting_key: str, user_id: int) -> str:
    """Gibt den bestehenden Token zurück oder erzeugt beim ersten Aufruf einen neuen."""
    fernet = _get_fernet()
    token = get_user_setting(user_id, setting_key, fernet)
    if not token:
        token = secrets.token_urlsafe(24)
        save_user_setting(user_id, setting_key, token, fernet)
    return token


def resolve_user_by_token(setting_key: str, token: str) -> int | None:
    """Findet den User, dessen gespeicherter Token unter setting_key mit dem
    übergebenen Token übereinstimmt. None wenn kein Treffer."""
    fernet = _get_fernet()
    candidate_ids = {1}  # Guest/Single-User-Default (kein users-Datensatz im AUTH_ENABLED=false-Modus)
    try:
        candidate_ids.update(u["id"] for u in list_users())
    except Exception:
        pass
    for uid in candidate_ids:
        stored = get_user_setting(uid, setting_key, fernet)
        if stored and _hmac.compare_digest(stored, token):
            return uid
    return None
