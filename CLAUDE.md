# WanderSuite — Context for AI Assistants

This file gives a new Claude instance the context needed to continue development immediately.

## Project Overview

WanderSuite is a self-hosted travel management suite.
Repository: `https://github.com/antonbier/tracker-an-te`

## Current State (March 2026)

### Implemented and live
- Ryanair Tracker (scraping, baggage, seat reservation, daily scheduler)
- Google Flights Tracker (SerpAPI)
- Homair Camping Tracker (HTML scraping)
- Booking/Trivago Tracker (SerpAPI Google Hotels)
- AI travel recommendations (Gemini 2.0 Flash + OpenAI gpt-4o-mini)
- Travel Budget (manual + ActualBudget sync)
- Travel Journal (Dawarich trip detection via Haversine + overnight algorithm)
- Dashboard (budget donut chart, tracker overview, upcoming/completed trips)
- Field Guide (FAQ modal)
- Onboarding (3-step setup wizard)
- Adventure Look (terracotta palette, Playfair Display serif)
- Multilingual DE/IT/EN (external JSON locale files)
- Docker/Unraid deployment (port 8765 frontend, 8766 backend)
- Encrypted settings (AES-Fernet in SQLite)

### Known open issues

> All previously documented issues have been resolved.

- ~~Dawarich timestamp parsing~~ **fixed** (62278ff): `_parse_timestamp()` handles ISO-8601, date-only, Unix int/float/string.
- ~~ActualBudget millicents~~ **fixed** (ece14b1): amounts divided by 1000 everywhere.
- ~~SerpAPI quota invisible~~ **fixed** (a0e920c + 09f2b5c): `/api/settings/serpapi-quota` endpoint + progress bar in Settings.

## Deployment (Production — Unraid)

```
Frontend: http://192.168.1.51:8765
Backend:  http://192.168.1.51:8766
```

The backend URL must be set in the WanderSuite dashboard (Settings → General)
to `http://192.168.1.51:8766`. The browser calls the API directly on this port —
there is no nginx proxy between frontend and backend in the Unraid setup.

## Key Design Decisions

1. **No npm/Webpack** — pure Vanilla JS, no build step required
2. **SQLite** — simple, persistent via Docker volume at `/data/tracker.db`
3. **No hardcoded URLs** — `localStorage.getItem('apiUrl')` used everywhere
4. **External i18n** — JSON files in `frontend/locales/`, no framework
5. **Encryption** — AES-Fernet key derived from `APP_SECRET` env variable
6. **Port separation** — frontend on 8765, backend on 8766 (required for
   reverse proxy setups like Zoraxy on Unraid where cross-port calls happen)

## Common Tasks

### Add a new language
1. Copy `frontend/locales/en.json` to `frontend/locales/xx.json`
2. Translate all values
3. Search for `lang-btn` in `index.html` and add a new button

### Add a new tracker type
1. `backend/my_scraper.py` — scraping logic
2. `backend/routes/my_route.py` — FastAPI router
3. `backend/database.py` — add tables + CRUD functions
4. `backend/main.py` — register the router
5. `frontend/index.html` — add page HTML, CSS, JS

### Debug Dawarich point format
```bash
curl -X POST http://192.168.1.51:8766/api/dawarich/debug \
  -H "Content-Type: application/json" \
  -d '{}'
```
This returns the first 5 raw points and how they normalize — useful to fix
timestamp parsing issues.

### Rebuild on Unraid after code changes
```bash
cd /mnt/user/appdata/wandersuite
git pull
docker compose up -d --build
```
For frontend-only changes (index.html, locales), no rebuild needed —
just `git pull` since the frontend folder is mounted as a volume.

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS, Chart.js, Playfair Display + DM Sans + JetBrains Mono |
| Backend | Python 3.12, FastAPI, APScheduler, SQLite |
| Scraping | requests, SerpAPI, Nominatim (OpenStreetMap) |
| AI | Google Gemini 2.0 Flash, OpenAI gpt-4o-mini |
| Encryption | cryptography library (AES-Fernet) |
| Hosting | Docker + Nginx, Unraid (primary), Railway + here.now (preview) |

## File Map (most important files)

```
backend/main.py            — FastAPI entry point, register all routers here
backend/database.py        — ALL database tables and CRUD — add new tables here
backend/settings_manager.py — encrypted settings read/write
backend/dawarich.py        — trip detection algorithm (Haversine + overnight)
backend/scraper.py         — Ryanair scraper (most complex, anti-bot logic)
frontend/index.html        — entire frontend (1 file, ~2500 lines)
frontend/locales/*.json    — all UI strings for DE/IT/EN
docker-compose.yml         — port 8765 (frontend) + 8766 (backend)
.env.example               — environment variable template
```
