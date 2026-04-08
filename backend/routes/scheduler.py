"""
WanderSuite — /api/scheduler
Per-user scheduler settings: update interval, notification preferences.
GET  /api/scheduler/settings        → get current user's settings
PUT  /api/scheduler/settings        → update settings
POST /api/scheduler/run             → manually trigger price fetch for current user
GET  /api/scheduler/status          → last run time + next run info
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth_jwt import get_current_user
from database import (
    get_user_scheduler_settings,
    save_user_scheduler_settings,
    update_scheduler_last_run,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class SchedulerSettingsUpdate(BaseModel):
    update_interval_hours: int = 24   # 6 | 12 | 24 | 48 | 168
    notify_price_drop: bool = True
    notify_daily_summary: bool = False


@router.get("/settings")
def get_scheduler_settings(user: dict = Depends(get_current_user)):
    uid = user.get("id", 1) or 1
    s = get_user_scheduler_settings(uid)
    last_run = s.get("last_run_at")
    # Format last_run_at using user's timezone if available
    if last_run:
        try:
            from datetime import datetime
            from settings_manager import get_user_setting_value, get_setting_value
            # Try user-level timezone first, then global
            tz_name = get_user_setting_value(uid, "timezone") or get_setting_value("timezone") or "UTC"
            import zoneinfo
            tz = zoneinfo.ZoneInfo(tz_name)
            dt = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                import zoneinfo as _zi
                dt = dt.replace(tzinfo=_zi.ZoneInfo("UTC"))
            dt_local = dt.astimezone(tz)
            last_run = dt_local.strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            pass  # keep original if parsing fails
    return {
        "update_interval_hours": s.get("update_interval_hours", 24),
        "notify_price_drop": bool(s.get("notify_price_drop", True)),
        "notify_daily_summary": bool(s.get("notify_daily_summary", False)),
        "last_run_at": last_run,
        "timezone": _get_user_tz(uid),
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
    user: dict = Depends(get_current_user)
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


@router.post("/run")
async def trigger_run(user: dict = Depends(get_current_user)):
    """Manually trigger a price fetch for the current user's trackers."""
    uid = user.get("id", 1) or 1
    logger.info(f"🔄 Manueller Scheduler-Lauf für user_id={uid}")
    import asyncio
    from scheduler import run_all_trackers
    # Run in background so request returns immediately
    asyncio.get_event_loop().run_in_executor(None, run_all_trackers, uid)
    return {"message": "Preisabfrage wird im Hintergrund gestartet"}
