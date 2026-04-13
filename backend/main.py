"""
WanderSuite — FastAPI Backend Entry Point (BETA)
"""

import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

import asyncio
from database import init_db, discovery_pool_count
from auth_db import init_auth_tables
from scheduler import run_all_trackers, run_cleanup_job
from routes import (
    trackers, prices, google_flights, discover, discovery as discovery_route,
    accommodations, budget, settings as settings_route,
    dashboard as dashboard_route,
    userdata as userdata_route,
    search as search_route,
)
from routes import notifications as notifications_route
from discovery import discovery_service
from discovery_fallbacks import router as fallback_router
from routes.auth import router_status, router_auth, router_admin
from routes import dawarich as dawarich_route
from routes import trips as trips_route
from routes import ws_trips as ws_trips_route
from routes import passkey as passkey_route
from routes import scheduler as scheduler_route

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "/app/data/tracker.db")
TZ      = os.getenv("TZ", "Europe/Rome")
CHANNEL = os.getenv("WANDERSUITE_CHANNEL", "stable")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

_build_date = os.getenv("BUILD_DATE", "").strip()
if CHANNEL == "beta" and _build_date and _build_date != "unknown":
    APP_VERSION = f"beta-{_build_date}"
else:
    APP_VERSION = "1.0.0"

logger.info(f"WanderSuite {APP_VERSION} ({CHANNEL}) starting — DB: {DB_PATH}, TZ: {TZ}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_auth_tables()
    logger.info(f"DB ready — {APP_VERSION}")

    scheduler = BackgroundScheduler(timezone=TZ)

    # Daily price fetch at 07:00
    scheduler.add_job(
        run_all_trackers,
        trigger="cron", hour=7, minute=0,
        id="daily_price_fetch",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Daily cleanup at 03:00
    scheduler.add_job(
        run_cleanup_job,
        trigger="cron", hour=3, minute=0,
        id="daily_cleanup",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Sync wrapper für APScheduler
    def _run_image_retry():
        import asyncio as _asyncio
        try:
            loop = _asyncio.get_event_loop()
            if loop.is_running():
                _asyncio.ensure_future(discovery_service.retry_missing_images(1))
            else:
                loop.run_until_complete(discovery_service.retry_missing_images(1))
        except Exception as e:
            logger.warning(f"[Discovery] Retry-Job Fehler: {e}")

    scheduler.add_job(
        _run_image_retry,
        trigger="interval", hours=2,
        id="discovery_image_retry",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"Scheduler started — price fetch 07:00, cleanup 03:00, img-retry 2h ({TZ})")

    # Discovery pool warmup — im Hintergrund, blockiert nicht den Start
    async def _warmup_pool():
        try:
            _, unseen = discovery_pool_count(1)  # user_id=1 (guest/admin)
            if unseen < 3:
                logger.info("[Discovery] Pool leer — starte Hintergrund-Warmup")
                await discovery_service.background_refresh_suggestions(1, batch=6)
                logger.info("[Discovery] Pool-Warmup abgeschlossen")
        except Exception as e:
            logger.warning(f"[Discovery] Pool-Warmup fehlgeschlagen: {e}")

    asyncio.ensure_future(_warmup_pool())

    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="WanderSuite API", version=APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

app.include_router(trackers.router,            prefix="/api/trackers",         tags=["Ryanair"])
app.include_router(prices.router,              prefix="/api/prices",           tags=["Prices"])
app.include_router(google_flights.router,      prefix="/api/google-flights",   tags=["Google Flights"])
app.include_router(accommodations.router,      prefix="/api/accommodations",   tags=["Accommodations"])
app.include_router(budget.router,              prefix="/api/budget",           tags=["Budget"])
app.include_router(discover.router,            prefix="/api/discover",         tags=["Discover"])
app.include_router(settings_route.router,      prefix="/api/settings",         tags=["Settings"])
app.include_router(dawarich_route.router,      prefix="/api/dawarich",         tags=["Dawarich"])
app.include_router(trips_route.router,         prefix="/api/trips",            tags=["Trips"])
app.include_router(ws_trips_route.router,    prefix="/api/ws-trips",         tags=["WsTrips"])
app.include_router(dashboard_route.router,     prefix="/api/dashboard",        tags=["Dashboard"])
app.include_router(userdata_route.router,      prefix="/api/userdata",         tags=["UserData"])
app.include_router(notifications_route.router, prefix="/api/notifications",    tags=["Notifications"])
app.include_router(scheduler_route.router,     prefix="/api/scheduler",        tags=["Scheduler"])
app.include_router(search_route.router,        prefix="/api/search",           tags=["Search"])
app.include_router(discovery_route.router,     prefix="/api/discovery",        tags=["Discovery"])
app.include_router(fallback_router,            prefix="/api/discovery/fallback", tags=["Discovery"])
app.include_router(router_status, prefix="/api", tags=["Status"])
app.include_router(router_auth,   prefix="/api", tags=["Auth"])
app.include_router(router_admin,  prefix="/api", tags=["Admin"])
app.include_router(passkey_route.router,     prefix="/api/auth/passkeys",  tags=["Passkeys"])


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok", "version": APP_VERSION, "channel": CHANNEL}

