"""
WanderSuite v0.5 — FastAPI Backend
Routes: /api/trackers, /api/prices, /api/google-flights, /api/discover
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
import logging

from database import init_db
from scheduler import run_all_trackers
from routes import trackers, prices, google_flights, discover

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("✅ Datenbank initialisiert")

    scheduler = BackgroundScheduler(timezone="Europe/Rome")
    scheduler.add_job(
        run_all_trackers,
        trigger="cron",
        hour=7, minute=0,
        id="daily_price_fetch",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("⏰ Scheduler gestartet — täglich 07:00 Uhr")

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler gestoppt")


app = FastAPI(
    title="WanderSuite API",
    version="0.5.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(trackers.router,       prefix="/api/trackers",       tags=["Ryanair Tracker"])
app.include_router(prices.router,         prefix="/api/prices",          tags=["Prices"])
app.include_router(google_flights.router, prefix="/api/google-flights",  tags=["Google Flights"])
app.include_router(discover.router,       prefix="/api/discover",         tags=["Discover"])


@app.get("/")
def root():
    return {"status": "ok", "service": "WanderSuite API", "version": "0.5.0"}


@app.get("/health")
def health():
    return {"status": "healthy", "version": "0.5.0"}
