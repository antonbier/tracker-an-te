"""
WanderSuite -- REST Routes: /api/notifications
Endpoints for per-user notification settings + admin test.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from notifications import send_telegram, send_gotify
from auth_jwt import get_current_user
from crud.settings import get_user_notification_settings, save_user_notification_settings
from settings_manager import _get_fernet

router = APIRouter()
logger = logging.getLogger(__name__)


class UserNotificationConfig(BaseModel):
    telegram_bot_token: Optional[str] = None
    telegram_chat_id:   Optional[str] = None
    gotify_url:         Optional[str] = None
    gotify_app_token:   Optional[str] = None


@router.get("/settings")
def get_notification_settings(user: dict = Depends(get_current_user)):
    """
    Return current notification settings for the logged-in user.
    Sensitive fields are masked (shows empty string if not set, or mask if set).
    """
    uid    = user.get("id", 1) or 1
    fernet = _get_fernet()
    creds  = get_user_notification_settings(uid, fernet)
    # Mask secrets -- frontend only needs to know if set or not
    def _mask(v):
        return "configured" if v else ""
    return {
        "telegram_bot_token": _mask(creds.get("telegram_bot_token")),
        "telegram_chat_id":   creds.get("telegram_chat_id") or "",   # chat_id not secret
        "gotify_url":         creds.get("gotify_url") or "",          # URL not secret
        "gotify_app_token":   _mask(creds.get("gotify_app_token")),
    }


@router.put("/settings")
def save_notification_settings(
    config: UserNotificationConfig,
    user: dict = Depends(get_current_user),
):
    """
    Save (upsert) notification credentials for the logged-in user.
    All values are Fernet-encrypted before storage.
    Empty string -> NULL (clears the credential).
    """
    uid    = user.get("id", 1) or 1
    fernet = _get_fernet()
    # Load existing to allow partial updates (reuse same fernet instance)
    existing = get_user_notification_settings(uid, fernet)
    merged = {
        "telegram_bot_token": config.telegram_bot_token
            if config.telegram_bot_token is not None else existing.get("telegram_bot_token", ""),
        "telegram_chat_id":   config.telegram_chat_id
            if config.telegram_chat_id   is not None else existing.get("telegram_chat_id",   ""),
        "gotify_url":         config.gotify_url
            if config.gotify_url         is not None else existing.get("gotify_url",          ""),
        "gotify_app_token":   config.gotify_app_token
            if config.gotify_app_token   is not None else existing.get("gotify_app_token",    ""),
    }
    save_user_notification_settings(uid, merged, fernet)
    return {"success": True, "message": "Einstellungen gespeichert"}


@router.post("/test-telegram")
def test_telegram(user: dict = Depends(get_current_user)):
    """
    Send a test Telegram message using the logged-in user's credentials.
    Falls back to global admin credentials if user has none configured.
    """
    uid    = user.get("id", 1) or 1
    fernet = _get_fernet()
    creds  = get_user_notification_settings(uid, fernet)
    token   = creds.get("telegram_bot_token") or ""
    chat_id = creds.get("telegram_chat_id")   or ""

    # Use user creds if available, else fall back to global admin
    if token and chat_id:
        import requests as _req
        resp = _req.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": "WanderSuite Test -- Telegram-Benachrichtigungen sind aktiv!", "parse_mode": "HTML"},
            timeout=8,
        )
        ok = resp.ok
    else:
        ok = send_telegram("WanderSuite Test -- Telegram-Benachrichtigungen sind aktiv!")
    if ok:
        return {"success": True,  "message": "Telegram-Testnachricht gesendet"}
    return      {"success": False, "message": "Fehler -- Token und Chat-ID pruefen"}


@router.post("/test-gotify")
def test_gotify(user: dict = Depends(get_current_user)):
    """
    Send a test Gotify notification using the logged-in user's credentials.
    Falls back to global admin credentials if user has none configured.
    """
    uid    = user.get("id", 1) or 1
    fernet = _get_fernet()
    creds  = get_user_notification_settings(uid, fernet)
    gf_url   = creds.get("gotify_url")       or ""
    gf_token = creds.get("gotify_app_token") or ""

    if gf_url and gf_token:
        import requests as _req
        resp = _req.post(
            f"{gf_url.rstrip('/')}/message",
            json={"title": "WanderSuite Test", "message": "Gotify-Benachrichtigungen sind aktiv!", "priority": 5},
            headers={"X-Gotify-Key": gf_token},
            timeout=8,
        )
        ok = resp.ok
    else:
        ok = send_gotify("WanderSuite Test", "Gotify-Benachrichtigungen sind aktiv!")
    if ok:
        return {"success": True,  "message": "Gotify-Testnachricht gesendet"}
    return      {"success": False, "message": "Fehler -- URL und App-Token pruefen"}
