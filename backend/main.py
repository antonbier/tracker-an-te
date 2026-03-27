"""
WanderSuite v1.0 — FastAPI Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
import logging

from database import init_db
from scheduler import run_all_trackers
from routes import trackers, prices, google_flights, discover, accommodations, budget, dawarich as dawarich_route
from routes import settings as settings_route

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("✅ Datenbank initialisiert (v1.0)")

    scheduler = BackgroundScheduler(timezone="Europe/Rome")
    scheduler.add_job(run_all_trackers, trigger="cron", hour=7, minute=0,
                      id="daily_price_fetch", replace_existing=True, misfire_grace_time=3600)
    scheduler.start()
    logger.info("⏰ Scheduler gestartet")

    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="WanderSuite API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=False,
    allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
    allow_headers=["*"], expose_headers=["*"],
)

app.include_router(trackers.router,        prefix="/api/trackers",       tags=["Ryanair"])
app.include_router(prices.router,          prefix="/api/prices",          tags=["Prices"])
app.include_router(google_flights.router,  prefix="/api/google-flights",  tags=["Google Flights"])
app.include_router(accommodations.router,  prefix="/api/accommodations",   tags=["Accommodations"])
app.include_router(budget.router,          prefix="/api/budget",           tags=["Budget"])
app.include_router(discover.router,        prefix="/api/discover",         tags=["Discover"])
app.include_router(settings_route.router,  prefix="/api/settings",         tags=["Settings"])
app.include_router(dawarich_route.router,   prefix="/api/dawarich",          tags=["Dawarich"])


@app.get("/")
def root():
    return {"status": "ok", "service": "WanderSuite API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}
