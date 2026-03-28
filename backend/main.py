"""
WanderSuite v1.0 — FastAPI Backend Entry Point
===============================================
Startet die FastAPI-App mit APScheduler für tägliches Scraping.

Konfiguration via Umgebungsvariablen (alle mit sinnvollen Fallbacks):

  DB_PATH      Pfad zur SQLite-Datenbank
               Default: /app/data/tracker.db
               Im Docker-Container wird /app/data als Volume gemountet,
               sodass die DB Container-Neustarts überlebt.

  APP_SECRET   AES-Fernet Encryption Key für gespeicherte API Keys
               Default: wandersuite-change-me (NUR für Entwicklung!)
               In Produktion zwingend via .env setzen.

  TZ           Zeitzone für den APScheduler-Cronjob
               Default: Europe/Rome (liest OS-Zeitzone via os.environ)
               Wird via docker-compose als TZ-Variable gesetzt.

Ports:
  8000 intern  → gemappt auf ${BACKEND_PORT:-8766} auf dem Host
  8765 Frontend (Nginx) → serviert index.html + JS + locales

API Routes:
  /api/trackers        — Ryanair Tracker CRUD
  /api/prices          — Preisverlauf für Charts
  /api/google-flights  — Google Flights via SerpAPI
  /api/accommodations  — Homair + Booking/Trivago
  /api/discover        — KI-Empfehlungen (Gemini/OpenAI)
  /api/budget          — ActualBudget Sync
  /api/dawarich        — Trip-Erkennung via Dawarich
  /api/dashboard       — Live-Stats für Meine Reisen Dashboard
  /api/settings        — Verschlüsselte API Key Verwaltung
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

from database import init_db
from scheduler import run_all_trackers
from routes import (
    trackers, prices, google_flights, discover,
    accommodations, budget, settings as settings_route,
    dashboard as dashboard_route,
)
from routes import dawarich as dawarich_route

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Configuration from environment ────────────────────────────────────────────
# DB_PATH: where the SQLite database lives.
# In Docker: /app/data/tracker.db (mounted from host via DATA_DIR volume).
# Locally: falls back to ./tracker.db for development convenience.
DB_PATH = os.getenv("DB_PATH", "/app/data/tracker.db")

# Timezone for the daily scraping cron job (APScheduler).
# TZ env var is set by docker-compose from .env → matches host timezone.
TZ = os.getenv("TZ", "Europe/Rome")

# Ensure the data directory exists (safety net if volume not mounted)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

logger.info(f"WanderSuite starting — DB: {DB_PATH}, TZ: {TZ}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pass DB_PATH to the database module via environment (already set)
    init_db()
    logger.info("✅ Datenbank initialisiert")

    scheduler = BackgroundScheduler(timezone=TZ)
    scheduler.add_job(
        run_all_trackers,
        trigger="cron", hour=7, minute=0,
        id="daily_price_fetch",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info(f"⏰ Scheduler gestartet (täglich 07:00 Uhr {TZ})")

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(title="WanderSuite API", version="1.0.0", lifespan=lifespan)

# CORS: allow all origins — needed because frontend (port 8765) calls
# backend (port 8766) directly from the browser in local network setups.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

app.include_router(trackers.router,        prefix="/api/trackers",       tags=["Ryanair"])
app.include_router(prices.router,          prefix="/api/prices",          tags=["Prices"])
app.include_router(google_flights.router,  prefix="/api/google-flights",  tags=["Google Flights"])
app.include_router(accommodations.router,  prefix="/api/accommodations",  tags=["Accommodations"])
app.include_router(budget.router,          prefix="/api/budget",          tags=["Budget"])
app.include_router(discover.router,        prefix="/api/discover",        tags=["Discover"])
app.include_router(settings_route.router,  prefix="/api/settings",        tags=["Settings"])
app.include_router(dawarich_route.router,  prefix="/api/dawarich",        tags=["Dawarich"])
app.include_router(dashboard_route.router, prefix="/api/dashboard",       tags=["Dashboard"])


@app.get("/")
def root():
    return {"status": "ok", "service": "WanderSuite API", "version": "1.0.0",
            "db": DB_PATH, "tz": TZ}


@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}
