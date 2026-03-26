"""
Ryanair Preistracker — FastAPI Backend
Läuft auf Railway / Render. Täglicher Scheduler via APScheduler.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
import logging

from database import init_db
from scheduler import run_all_trackers
from routes import trackers, prices

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    logger.info("✅ Datenbank initialisiert")

    scheduler = BackgroundScheduler(timezone="Europe/Rome")
    scheduler.add_job(
        run_all_trackers,
        trigger="cron",
        hour=7, minute=0,          # Täglich 07:00 Uhr (Europe/Rome)
        id="daily_price_fetch",
        replace_existing=True,
        misfire_grace_time=3600,   # 1h Toleranz bei Serverausfall
    )
    scheduler.start()
    logger.info("⏰ Scheduler gestartet — täglich 07:00 Uhr")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("Scheduler gestoppt")


app = FastAPI(
    title="Ryanair Preistracker API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # In Produktion: deine here.now-Domain
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trackers.router, prefix="/api/trackers", tags=["Trackers"])
app.include_router(prices.router, prefix="/api/prices", tags=["Prices"])


@app.get("/")
def root():
    return {"status": "ok", "service": "Ryanair Preistracker"}


@app.get("/health")
def health():
    return {"status": "healthy"}
