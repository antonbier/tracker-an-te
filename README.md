# WanderSuite

> Self-hosted travel management suite — track flight prices, sync your travel journal, manage your travel budget, and discover new destinations. Built for Unraid, runs everywhere with Docker.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Version](https://img.shields.io/badge/version-1.0-green.svg)](https://github.com/antonbier/tracker-an-te/releases/tag/v1.0)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

---

## Features

| Module | Feature | Status |
|---|---|---|
| ✈️ Ryanair Tracker | Daily price scraping, baggage, seat reservation | ✅ Live |
| 🔵 Google Flights | Prices via SerpAPI | ✅ Live |
| ⛺ Homair | Camping prices via HTML scraping | ✅ Live |
| 🏨 Booking/Trivago | Hotel prices via SerpAPI Google Hotels | ✅ Live |
| 🌟 Discover | AI travel recommendations (Gemini + OpenAI) | ✅ Live |
| 💶 Travel Budget | Manual tracking + ActualBudget sync | ✅ Live |
| 📓 Travel Journal | Automatic trip detection via Dawarich | ✅ Live |
| 🏠 Dashboard | Overview, budget donut, tracker cards | ✅ Live |
| 📖 Field Guide | Integrated FAQ / help system | ✅ Live |
| 🌍 Multilingual | Deutsch, Italiano, English | ✅ Live |
| 🎨 Adventure Look | Terracotta/earth-tone, Playfair Display serif | ✅ Live |
| 🔐 Encrypted Settings | AES-Fernet encrypted API keys in SQLite | ✅ Live |

---

## Quick Start (Unraid)

```bash
# 1. Clone the repository
cd /mnt/user/appdata
git clone https://github.com/antonbier/tracker-an-te.git wandersuite
cd wandersuite

# 2. Configure environment variables
cp .env.example .env
nano .env  # Set APP_SECRET and PORT

# 3. Start
docker compose up -d --build
```

Open **`http://YOUR-UNRAID-IP:8765`** in your browser.

**Important:** In the dashboard → Settings → Backend URL: `http://YOUR-UNRAID-IP:8766`

### Updating

```bash
cd /mnt/user/appdata/wandersuite
git pull
docker compose up -d --build
```

---

## Architecture

```
wandersuite/
├── frontend/
│   ├── index.html              # Single-page app (HTML + CSS + JS, no build step)
│   └── locales/
│       ├── de.json             # German translations
│       ├── it.json             # Italian translations
│       └── en.json             # English translations
│
├── backend/
│   ├── main.py                 # FastAPI app + APScheduler entry point
│   ├── database.py             # SQLite layer (all tables + CRUD)
│   ├── settings_manager.py     # Encrypted settings (AES-Fernet)
│   ├── scraper.py              # Ryanair API scraper (anti-bot measures)
│   ├── google_scraper.py       # Google Flights via SerpAPI
│   ├── homair_scraper.py       # Homair camping HTML scraper
│   ├── booking_scraper.py      # Booking via SerpAPI Google Hotels
│   ├── gemini.py               # Google Gemini AI integration
│   ├── openai_client.py        # OpenAI gpt-4o-mini integration
│   ├── dawarich.py             # Dawarich sync + trip detection algorithm
│   ├── actual_budget.py        # ActualBudget REST API client
│   ├── scheduler.py            # Daily batch runner (07:00 AM)
│   ├── requirements.txt
│   └── routes/
│       ├── trackers.py         # /api/trackers — Ryanair CRUD
│       ├── prices.py           # /api/prices — price history
│       ├── google_flights.py   # /api/google-flights
│       ├── accommodations.py   # /api/accommodations/homair + booking
│       ├── discover.py         # /api/discover — AI recommendations
│       ├── budget.py           # /api/budget — ActualBudget sync
│       ├── dawarich.py         # /api/dawarich — trip sync
│       └── settings.py         # /api/settings — encrypted keys
│
├── docker/
│   ├── Dockerfile              # Python 3.12 slim backend image
│   └── nginx.conf              # Nginx reverse proxy config
│
├── docker-compose.yml          # Full stack definition
├── .env.example                # Environment variables template
├── CLAUDE.md                   # Context file for AI assistants
└── README.md
```

### Database Schema

```
trackers           — Ryanair trackers
price_snapshots    — Ryanair price history
gf_trackers        — Google Flights trackers
gf_snapshots       — Google Flights price history
homair_trackers    — Homair trackers
homair_snapshots   — Homair price history
booking_trackers   — Booking/Trivago trackers
booking_snapshots  — Booking price history
detected_trips     — Dawarich auto-detected trips
settings           — Encrypted API keys
```

---

## Configuration

### .env

```bash
PORT=8765              # Frontend port
BACKEND_PORT=8766      # Backend port (directly accessible from browser)
APP_SECRET=...         # Encryption key for API keys (change this!)
DB_PATH=/data/tracker.db
```

### API Keys (configured in the app Settings)

| Service | Where to get | Used for |
|---|---|---|
| **SerpAPI** | [serpapi.com](https://serpapi.com) — Free: 100/month | Google Flights + Booking |
| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com) — Free | AI travel recommendations |
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | AI travel recommendations (alternative) |
| **Dawarich** | Your own instance — token in Dawarich settings | Travel journal |
| **ActualBudget** | Your own instance — server password | Budget sync |

---

## Dawarich Trip Detection Algorithm

WanderSuite automatically detects overnight trips from your location history:

1. Fetch all location points from the Dawarich API (paginated)
2. Calculate Haversine distance from each point to your home coordinates
3. Keep only points **> 50 km** from home
4. Group by date
5. **Overnight condition:** minimum 2 consecutive days (= at least 1 night away)
6. Merge consecutive day-groups into a single trip (max. 2-day gap allowed)
7. Reverse geocoding via Nominatim (OpenStreetMap, no API key required)
8. Save to `detected_trips` table with upsert logic

Configure your home coordinates in Settings → Integrations → Dawarich (e.g. `46.7987` / `11.7188` for Bolzano).

---

## API Reference

Swagger UI: `http://YOUR-UNRAID-IP:8766/docs`

```
GET  /health                          — Health check
GET  /api/trackers                    — List Ryanair trackers
POST /api/trackers                    — Create tracker
POST /api/trackers/{id}/scrape        — Manual price fetch
GET  /api/prices/{id}                 — Price history (chart data)
GET  /api/google-flights              — List Google Flights trackers
POST /api/google-flights/{id}/scrape  — Fetch GF price
GET  /api/accommodations/homair       — List Homair trackers
GET  /api/accommodations/booking      — List Booking trackers
POST /api/discover                    — AI travel recommendations
POST /api/dawarich/sync               — Run Dawarich trip sync
POST /api/dawarich/debug              — Debug Dawarich point format
GET  /api/dawarich/trips              — List detected trips
POST /api/budget/actual/summary       — ActualBudget summary
POST /api/budget/actual/expenses      — Travel transactions by category
GET  /api/settings                    — Get settings (keys masked)
POST /api/settings                    — Save settings (encrypted)
```

---

## Automatic Scraping

The APScheduler runs daily at **07:00 AM (Europe/Rome)** and scrapes all active Ryanair trackers automatically. The timezone is configurable in Settings → General.

Manual trigger: **⟳ Now** button on any tracker card.

---

## Contributing

1. Fork → feature branch → pull request
2. Python: PEP 8, type hints where possible
3. JS: Vanilla JS only, no frameworks, no build step
4. i18n: Add new strings to all 3 locale files (`de.json`, `it.json`, `en.json`)

### Adding a new language

```bash
cp frontend/locales/en.json frontend/locales/fr.json
# Translate the values
# Add a button in index.html (search for "lang-btn")
```

### Adding a new scraper

```bash
# 1. backend/my_scraper.py — scraping logic
# 2. backend/routes/my_route.py — FastAPI router
# 3. backend/database.py — add tables + CRUD functions
# 4. backend/main.py — register the router
# 5. frontend/index.html — add page HTML + JS
```

---

## Future Roadmap

### UX Polish
- Skeleton loaders for data fetching
- CSV export for price history
- Currency toggle (EUR / USD / GBP)

### Notifications
- Telegram push alerts when price drops below threshold
- Discord webhooks
- Gotify (self-hosted, Unraid-friendly)

### Quality of Life
- API quota tracker (SerpAPI 100/month usage display)
- Price threshold alerts per tracker
- Mobile PWA support

---

## License

**GNU Affero General Public License v3.0** — see [LICENSE](LICENSE).

> Self-hosting is explicitly encouraged. Modifications must be published under the same license.
