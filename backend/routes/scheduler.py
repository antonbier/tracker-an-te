"""
WanderSuite — /api/scheduler

Fixes:
  - asyncio.get_event_loop() → asyncio.get_running_loop() (Python 3.10+)
  - POST /run now calls update_scheduler_last_run for the requesting user
"""

import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth_jwt import get_current_user
from crud.settings import (
    get_user_scheduler_settings,
    save_user_scheduler_settings,
    update_scheduler_last_run,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class SchedulerSettingsUpdate(BaseModel):
    update_interval_hours: int = 24
    notify_price_drop: bool = True
    notify_daily_summary: bool = False


@router.get("/settings")
def get_scheduler_settings(user: dict = Depends(get_current_user)):
    uid = user.get("id", 1) or 1
    s = get_user_scheduler_settings(uid)
    last_run = s.get("last_run_at")
    if last_run:
        try:
            from datetime import datetime
            from settings_manager import get_user_setting_value, get_setting_value
            import zoneinfo
            tz_name = get_user_setting_value(uid, "timezone") or get_setting_value("timezone") or "UTC"
            try:
                tz = zoneinfo.ZoneInfo(tz_name)
            except Exception:
                tz = zoneinfo.ZoneInfo("UTC")
            dt = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
            last_run = dt.astimezone(tz).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            pass
    return {
        "update_interval_hours": s.get("update_interval_hours", 24),
        "notify_price_drop":     bool(s.get("notify_price_drop", True)),
        "notify_daily_summary":  bool(s.get("notify_daily_summary", False)),
        "last_run_at":           last_run,
        "timezone":              _get_user_tz(uid),
    }


def _get_user_tz(uid: int) -> str:
    try:
        from settings_manager import get_user_setting_value, get_setting_value
        return get_user_setting_value(uid, "timezone") or get_setting_value("timezone") or "UTC"
    except Exception:
        return "UTC"


@router.put("/settings")
def update_scheduler_settings(
    data: SchedulerSettingsUpdate,
    user: dict = Depends(get_current_user),
):
    uid = user.get("id", 1) or 1
    allowed_intervals = {6, 12, 24, 48, 72, 168}
    if data.update_interval_hours not in allowed_intervals:
        raise HTTPException(400, f"Interval muss einer von {sorted(allowed_intervals)} sein")
    save_user_scheduler_settings(
        uid,
        interval_hours=data.update_interval_hours,
        notify_price_drop=data.notify_price_drop,
        notify_daily_summary=data.notify_daily_summary,
    )
    return {"message": "Scheduler-Einstellungen gespeichert"}


# NEU-BUG C: Cooldown pro User — max 1 manueller Run alle 5 Minuten
import time as _time
_run_cooldown: dict[int, float] = {}
_COOLDOWN_SECS = 300  # 5 Minuten


@router.post("/run")
async def trigger_run(user: dict = Depends(get_current_user)):
    """
    Manually trigger a price fetch for the current user's trackers.
    NEU-BUG C: Cooldown 5 min/User — verhindert Ressourcen-Missbrauch.
    Der Run ist user-scoped (nur eigene Tracker) — kein Admin nötig.
    """
    uid = user.get("id", 1) or 1

    # Cooldown-Check
    last = _run_cooldown.get(uid, 0)
    now  = _time.monotonic()
    if now - last < _COOLDOWN_SECS:
        wait = int(_COOLDOWN_SECS - (now - last))
        raise HTTPException(
            status_code=429,
            detail=f"Bitte {wait}s warten bevor du den Scan erneut startest.",
            headers={"Retry-After": str(wait)},
        )
    _run_cooldown[uid] = now

    logger.info(f"🔄 Manueller Scheduler-Lauf für user_id={uid}")
    from scheduler import run_all_trackers
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, run_all_trackers, uid)
    update_scheduler_last_run(uid)
    return {"message": "Preisabfrage wird im Hintergrund gestartet"}
