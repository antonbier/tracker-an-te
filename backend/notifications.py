"""
WanderSuite -- Notification System (Multi-User, erweiterbar)

Zwei Provider-Klassen: TelegramProvider, GotifyProvider.
Credentials werden pro User verschluesselt aus user_notification_settings geladen.

Globale Fallback-Funktion send_telegram/send_gotify (fuer Admin-Test via Settings)
bleibt erhalten fuer Rueckwaertskompatibilitaet.

Neue API:
    notify_user(user_id, title, message)
        -- sendet ueber alle konfigurierten Provider des Users
        -- Fehler eines Providers stoppt andere nicht

Logging-Format:
    [Telegram] user=N status=ok
    [Gotify]   user=N status=error | reason=...
"""

import logging
import requests as _requests
from crud.settings import get_setting

logger = logging.getLogger(__name__)
TIMEOUT = 8


# ── Global admin send (backward compat) ───────────────────────────────────────

def send_telegram(message: str) -> bool:
    """Send via global (admin) Telegram credentials."""
    token   = get_setting_value("telegram_bot_token")
    chat_id = get_setting_value("telegram_chat_id")
    if not token or not chat_id:
        logger.debug("[Telegram] Not configured -- skipping")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = _requests.post(url, json={
            "chat_id": chat_id, "text": message,
            "parse_mode": "HTML", "disable_web_page_preview": True,
        }, timeout=TIMEOUT)
        if resp.ok:
            logger.info("[Telegram] Message sent (global)")
            return True
        logger.warning(f"[Telegram] Error {resp.status_code}: {resp.json().get('description','')}")
        return False
    except Exception as e:
        logger.warning(f"[Telegram] Exception: {e}")
        return False


def send_gotify(title: str, message: str, priority: int = 5) -> bool:
    """Send via global (admin) Gotify credentials."""
    url_base = get_setting_value("gotify_url")
    token    = get_setting_value("gotify_token")
    if not url_base or not token:
        logger.debug("[Gotify] Not configured -- skipping")
        return False
    try:
        resp = _requests.post(
            f"{url_base.rstrip('/')}/message",
            json={"title": title, "message": message, "priority": priority},
            headers={"X-Gotify-Key": token},
            timeout=TIMEOUT,
        )
        if resp.ok:
            logger.info("[Gotify] Message sent (global)")
            return True
        logger.warning(f"[Gotify] Error {resp.status_code}: {resp.text[:80]}")
        return False
    except Exception as e:
        logger.warning(f"[Gotify] Exception: {e}")
        return False


# ── Per-User Provider classes ─────────────────────────────────────────────────

class _TelegramProvider:
    def __init__(self, token: str, chat_id: str):
        self.token   = token
        self.chat_id = chat_id

    def send(self, user_id: int, title: str, message: str) -> bool:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        text = f"<b>{title}</b>\n\n{message}"
        try:
            resp = _requests.post(url, json={
                "chat_id": self.chat_id, "text": text,
                "parse_mode": "HTML", "disable_web_page_preview": True,
            }, timeout=TIMEOUT)
            ok = resp.ok
            if ok:
                logger.info(f"[Telegram] user={user_id} status=ok")
            else:
                logger.warning(f"[Telegram] user={user_id} status=error | reason={resp.json().get('description','')}")
            return ok
        except Exception as e:
            logger.warning(f"[Telegram] user={user_id} status=error | reason={e}")
            return False


class _GotifyProvider:
    def __init__(self, url: str, token: str):
        self.url   = url.rstrip('/')
        self.token = token

    def send(self, user_id: int, title: str, message: str) -> bool:
        try:
            resp = _requests.post(
                f"{self.url}/message",
                json={"title": title, "message": message, "priority": 5},
                headers={"X-Gotify-Key": self.token},
                timeout=TIMEOUT,
            )
            ok = resp.ok
            if ok:
                logger.info(f"[Gotify] user={user_id} status=ok")
            else:
                logger.warning(f"[Gotify] user={user_id} status=error | code={resp.status_code}")
            return ok
        except Exception as e:
            logger.warning(f"[Gotify] user={user_id} status=error | reason={e}")
            return False


def _get_providers(user_id: int) -> list:
    """Load and instantiate all configured providers for this user."""
    providers = []
    try:
        from crud.settings import get_user_notification_settings
        from settings_manager import _get_fernet
        fernet = _get_fernet()
        creds  = get_user_notification_settings(user_id, fernet)

        tg_token   = creds.get("telegram_bot_token", "")
        tg_chat    = creds.get("telegram_chat_id",   "")
        gf_url     = creds.get("gotify_url",          "")
        gf_token   = creds.get("gotify_app_token",    "")

        if tg_token and tg_chat:
            providers.append(_TelegramProvider(tg_token, tg_chat))
        if gf_url and gf_token:
            providers.append(_GotifyProvider(gf_url, gf_token))
    except Exception as e:
        logger.error(f"[notify] Failed to load providers for user={user_id}: {e}")
    return providers


def notify_user(user_id: int, title: str, message: str) -> None:
    """
    Send via all configured providers for this user.
    A failure in one provider never stops others.
    """
    providers = _get_providers(user_id)
    if not providers:
        logger.debug(f"[notify] user={user_id} -- no providers configured, skip")
        return
    for p in providers:
        try:
            p.send(user_id, title, message)
        except Exception as e:
            logger.warning(f"[notify] user={user_id} provider={type(p).__name__} exception: {e}")


# ── Tracker alert helpers ─────────────────────────────────────────────────────

def notify_price_drop(tracker: dict, old_price: float, new_price: float) -> None:
    """Send a price-drop notification. Falls back to global credentials if user_id missing."""
    user_id  = tracker.get("user_id", 1) or 1
    origin   = tracker.get("origin", "")
    dest     = tracker.get("destination", tracker.get("region", tracker.get("destination", "?")))
    date     = tracker.get("outbound_date", tracker.get("checkin_date", ""))
    diff     = round(old_price - new_price, 2)
    pct      = round((diff / old_price) * 100, 1) if old_price else 0

    title   = f"Preissenkung: {origin} -> {dest}"
    message = (
        f"Preis gefallen um {diff:.2f} EUR ({pct}%)\n"
        f"Neu: {new_price:.2f} EUR | Alt: {old_price:.2f} EUR\n"
        f"Datum: {date}"
    )
    notify_user(user_id, title, message)


def notify_threshold_reached(tracker: dict, price: float, threshold: float) -> None:
    """Send a wish-price-reached notification."""
    user_id = tracker.get("user_id", 1) or 1
    origin  = tracker.get("origin", "")
    dest    = tracker.get("destination", tracker.get("region", "?"))
    date    = tracker.get("outbound_date", tracker.get("checkin_date", ""))

    title   = f"Ziel erreicht: {origin} -> {dest}"
    message = (
        f"Aktueller Preis {price:.2f} EUR unterschreitet deinen Wunschpreis von {threshold:.2f} EUR!\n"
        f"Datum: {date}"
    )
    notify_user(user_id, title, message)
