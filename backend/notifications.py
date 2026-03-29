"""
WanderSuite — Notification System
Sends price-drop alerts via Telegram and/or Gotify.

Config keys (stored encrypted in SQLite via settings_manager):
  telegram_bot_token  — Telegram Bot API token (from @BotFather)
  telegram_chat_id    — Telegram chat/user ID (from @userinfobot)
  gotify_url          — Gotify server URL (e.g. https://gotify.example.com)
  gotify_token        — Gotify application token

Both services are optional and independent — any combination works.
Errors are caught and logged; a failed notification never crashes the scraper.
"""

import logging
import requests
from settings_manager import get_setting_value

logger = logging.getLogger(__name__)

TIMEOUT = 8  # seconds per HTTP request


def send_telegram(message: str) -> bool:
    """
    Send a Markdown message via Telegram Bot API.
    Returns True on success, False on any error.
    """
    token = get_setting_value("telegram_bot_token")
    chat_id = get_setting_value("telegram_chat_id")

    if not token or not chat_id:
        logger.debug("[Telegram] Not configured — skipping")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=TIMEOUT,
        )
        if resp.ok:
            logger.info("[Telegram] ✅ Nachricht gesendet")
            return True
        else:
            data = resp.json()
            logger.warning(f"[Telegram] ❌ Fehler {resp.status_code}: {data.get('description', resp.text)}")
            return False
    except requests.Timeout:
        logger.warning("[Telegram] ❌ Timeout")
        return False
    except requests.RequestException as e:
        logger.warning(f"[Telegram] ❌ Verbindungsfehler: {e}")
        return False


def send_gotify(title: str, message: str, priority: int = 5) -> bool:
    """
    Send a notification via Gotify REST API.
    Returns True on success, False on any error.
    Priority: 1=low, 5=normal, 8=high, 10=max.
    """
    url_base = get_setting_value("gotify_url")
    token    = get_setting_value("gotify_token")

    if not url_base or not token:
        logger.debug("[Gotify] Not configured — skipping")
        return False

    url_base = url_base.rstrip("/")
    try:
        resp = requests.post(
            f"{url_base}/message",
            json={"title": title, "message": message, "priority": priority},
            headers={"X-Gotify-Key": token},
            timeout=TIMEOUT,
        )
        if resp.ok:
            logger.info("[Gotify] ✅ Nachricht gesendet")
            return True
        else:
            logger.warning(f"[Gotify] ❌ Fehler {resp.status_code}: {resp.text[:200]}")
            return False
    except requests.Timeout:
        logger.warning("[Gotify] ❌ Timeout")
        return False
    except requests.RequestException as e:
        logger.warning(f"[Gotify] ❌ Verbindungsfehler: {e}")
        return False


def notify_price_drop(tracker: dict, old_price: float, new_price: float) -> None:
    """
    Send a price-drop alert via all configured notification services.
    Called by the scheduler when a new price is lower than the previous one.

    Args:
        tracker:   tracker dict with origin, destination, outbound_date, etc.
        old_price: previous lowest price (EUR)
        new_price: new price (EUR)
    """
    origin      = tracker.get("origin", "?")
    destination = tracker.get("destination", "?")
    date        = tracker.get("outbound_date", "")
    savings     = round(old_price - new_price, 2)
    savings_pct = round((savings / old_price) * 100) if old_price else 0

    tg_msg = (
        f"✈️ <b>Preissturz!</b>\n"
        f"<b>{origin} → {destination}</b>  {date}\n"
        f"\n"
        f"Neu:  <b>{new_price:.2f} €</b>\n"
        f"Alt:  {old_price:.2f} €\n"
        f"Gespart: -{savings:.2f} € ({savings_pct}%)\n"
        f"\n"
        f"<i>WanderSuite Preis-Radar</i>"
    )

    gotify_title = f"✈️ {origin} → {destination} — {new_price:.2f} €"
    gotify_msg   = (
        f"Preissturz: {old_price:.2f} € → {new_price:.2f} €\n"
        f"Datum: {date}\n"
        f"Gespart: -{savings:.2f} € ({savings_pct}%)"
    )

    sent_via = []
    if send_telegram(tg_msg):    sent_via.append("Telegram")
    if send_gotify(gotify_title, gotify_msg, priority=7): sent_via.append("Gotify")

    if sent_via:
        logger.info(f"[Notify] Preissturz-Alert gesendet via: {', '.join(sent_via)}")
    else:
        logger.debug("[Notify] Keine Benachrichtigungsdienste konfiguriert")
