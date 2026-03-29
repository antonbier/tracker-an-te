"""
WanderSuite — REST Routes: /api/notifications
Test endpoints for Telegram and Gotify notification configuration.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging

from notifications import send_telegram, send_gotify
from settings_manager import save_settings_bulk

router = APIRouter()
logger = logging.getLogger(__name__)


class NotificationConfig(BaseModel):
    telegram_bot_token: Optional[str] = None
    telegram_chat_id:   Optional[str] = None
    gotify_url:         Optional[str] = None
    gotify_token:       Optional[str] = None


@router.post("/test-telegram")
def test_telegram():
    """
    Send a test message via Telegram to verify the configuration.
    Reads credentials from the encrypted DB (must be saved first via /api/settings).
    """
    ok = send_telegram(
        "🔔 <b>WanderSuite Test</b>\n\n"
        "Telegram-Benachrichtigungen sind aktiv! ✅\n"
        "Du wirst ab jetzt bei Preissenkungen informiert."
    )
    if ok:
        return {"success": True,  "message": "Telegram-Testnachricht gesendet ✅"}
    return      {"success": False, "message": "Fehler beim Senden. Bitte Token und Chat-ID prüfen."}


@router.post("/test-gotify")
def test_gotify():
    """
    Send a test notification via Gotify to verify the configuration.
    Reads credentials from the encrypted DB (must be saved first via /api/settings).
    """
    ok = send_gotify(
        title="WanderSuite Test 🔔",
        message="Gotify-Benachrichtigungen sind aktiv! ✅\nDu wirst ab jetzt bei Preissenkungen informiert.",
        priority=5,
    )
    if ok:
        return {"success": True,  "message": "Gotify-Testnachricht gesendet ✅"}
    return      {"success": False, "message": "Fehler beim Senden. Bitte URL und Token prüfen."}
