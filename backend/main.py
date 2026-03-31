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

from database import init_db
from auth_db import init_auth_tables
from scheduler import run_all_trackers
from routes import (
    trackers, prices, google_flights, discover,
    accommodations, budget, settings as settings_route,
    dashboard as dashboard_route,
    userdata as userdata_route,
)
from routes import notifications as notifications_route
from routes.auth import router_status, router_auth, router_admin
from routes import dawarich as dawarich_route

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "/app/data/tracker.db")
TZ      = os.getenv("TZ", "Europe/Rome")
CHANNEL = os.getenv("WANDERSUITE_CHANNEL", "stable")   # "beta" or "stable"

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Beta: use BUILD_DATE from Docker ARG (set at docker compose build time)
# Main: always "1.0.0"
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
    logger.info(f"✅ DB ready — {APP_VERSION}")

    scheduler = BackgroundScheduler(timezone=TZ)
    scheduler.add_job(
        run_all_trackers,
        trigger="cron", hour=7, minute=0,
        id="daily_price_fetch",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info(f"⏰ Scheduler started (07:00 {TZ})")

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

app.include_router(trackers.router,           prefix="/api/trackers",       tags=["Ryanair"])
app.include_router(prices.router,             prefix="/api/prices",         tags=["Prices"])
app.include_router(google_flights.router,     prefix="/api/google-flights", tags=["Google Flights"])
app.include_router(accommodations.router,     prefix="/api/accommodations", tags=["Accommodations"])
app.include_router(budget.router,             prefix="/api/budget",         tags=["Budget"])
app.include_router(discover.router,           prefix="/api/discover",       tags=["Discover"])
app.include_router(settings_route.router,     prefix="/api/settings",       tags=["Settings"])
app.include_router(dawarich_route.router,     prefix="/api/dawarich",       tags=["Dawarich"])
app.include_router(dashboard_route.router,    prefix="/api/dashboard",      tags=["Dashboard"])
app.include_router(userdata_route.router,     prefix="/api/userdata",       tags=["UserData"])
app.include_router(notifications_route.router,prefix="/api/notifications",  tags=["Notifications"])
app.include_router(router_status, prefix="/api", tags=["Auth"])
app.include_router(router_auth,   prefix="/api", tags=["Auth"])
app.include_router(router_admin,  prefix="/api", tags=["Admin"])


@app.get("/")
def root():
    return {"status": "ok", "service": "WanderSuite API",
            "version": APP_VERSION, "channel": CHANNEL, "db": DB_PATH, "tz": TZ}


@app.get("/health")
def health():
    return {"status": "healthy", "version": APP_VERSION, "channel": CHANNEL}
