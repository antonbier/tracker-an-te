# WanderSuite

> Self-hosted travel management suite — track flight prices, manage your travel budget, discover new destinations and keep a travel journal. Built for Unraid, runs everywhere with Docker.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Version](https://img.shields.io/badge/version-1.0-green.svg)](https://github.com/antonbier/tracker-an-te/releases/tag/v1.0)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

---

## Features

| Module | Feature | Status |
|---|---|---|
| 🎯 Preis-Radar | Two-level navigation: Flights, Accommodations, Car Rental (soon) | ✅ Live |
| 🟠 Ryanair Tracker | Daily price scraping, baggage, seat reservation, chart history | ✅ Live |
| ✈️ Google Flights | Prices via SerpAPI | ✅ Live |
| ⛺ Homair | Camping prices via SerpAPI Google Hotels | ✅ Live |
| 🏨 Booking / Trivago | Hotel prices via SerpAPI Google Hotels | ✅ Live |
| ✨ Inspiration | AI travel recommendations (Gemini + OpenAI) | ✅ Live |
| 🎒 Meine Reisen | Budget, Travel Journal, Bucket List — all in one | ✅ Live |
| 🗺️ Bucket List | Wishlist with localStorage persistence, random travel emojis | ✅ Live |
| 💶 Travel Budget | Manual tracking + ActualBudget sync | ✅ Live |
| 📓 Travel Journal | Automatic trip detection via Dawarich | ✅ Live |
| 🧭 Dashboard | Overview cards, budget donut, tracker summary | ✅ Live |
| 📖 Field Guide | Integrated FAQ / help system | ✅ Live |
| 🌍 Multilingual | Deutsch · Italiano · English | ✅ Live |
| 🎨 Modern Explorer | Light-first theme, Playfair serif, terracotta/navy palette | ✅ Live |
| 📱 Mobile Bottom Bar | Airbnb-style bottom navigation on mobile | ✅ Live |
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

**First-time setup:** Open Settings (⚙️ top right) → Backend URL → `http://YOUR-UNRAID-IP:8766`

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
│   ├── index.html              # Single-page app — HTML + CSS only, no build step
│   ├── locales/
│   │   ├── de.json             # German translations
│   │   ├── it.json             # Italian translations
│   │   └── en.json             # English translations
│   └── js/                     # Native ES Modules (no bundler)
│       ├── main.js             # Entry point — imports + window.* bindings + DOMContentLoaded
│       ├── core/
│       │   ├── state.js        # Global app state (exports + setters)
│       │   └── api.js          # HTTP client (api()) + health check
│       ├── ui/
│       │   ├── i18n.js         # Translations: loadLocale, t(), applyTranslations, setLang
│       │   ├── nav.js          # navigate(), sidebar, bottom bar active state, View Transitions
│       │   ├── toast.js        # Toast notification system
│       │   ├── settings.js     # Settings slide-panel (open/close/save, 3 tabs)
│       │   ├── priceradar.js   # Preis-Radar: switchRadarCategory + switchRadarSubTab
│       │   └── tabs.js         # switchMyTripsTab (Meine Reisen sub-tabs)
│       └── app/
│           ├── ryanair.js      # Ryanair tracker CRUD, chart rendering, Discover/AI
│           ├── budget.js       # ActualBudget sync, manual trips, expense table
│           ├── dashboard.js    # Dashboard cards (trackers, budget donut, trips)
│           ├── googleflights.js# Google Flights tracker CRUD
│           ├── homair.js       # Homair camping tracker CRUD
│           ├── booking.js      # Booking.com tracker CRUD
│           ├── journal.js      # Dawarich sync, trip list, journal
│           ├── onboarding.js   # Onboarding flow + Field Guide modal
│           └── bucketlist.js   # Bucket List (Wunschziele) — localStorage only
│
├── backend/
│   ├── main.py                 # FastAPI app + APScheduler entry point
│   ├── database.py             # SQLite layer (all tables + CRUD)
│   ├── settings_manager.py     # Encrypted settings (AES-Fernet)
│   ├── scraper.py              # Ryanair API scraper
│   ├── google_scraper.py       # Google Flights via SerpAPI
│   ├── homair_scraper.py       # Homair via SerpAPI Google Hotels
│   ├── booking_scraper.py      # Booking via SerpAPI Google Hotels
│   ├── gemini.py               # Google Gemini AI integration
│   ├── openai_client.py        # OpenAI gpt-4o-mini integration
│   ├── dawarich.py             # Dawarich sync + trip detection algorithm
│   ├── actual_budget.py        # ActualBudget REST API client (actualpy)
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
├── docker-compose.yml
├── .env.example
├── CLAUDE.md                   # AI assistant context + refactoring log
└── README.md
```

### Frontend Module Graph

```
main.js
├── core/state.js       ← imported by almost all modules
├── core/api.js         ← imported by all app/ modules
├── ui/i18n.js          ← t(), loadLocale, setLang
├── ui/nav.js           ← navigate() + bottom bar sync
├── ui/toast.js         ← toast()
├── ui/settings.js      ← settings slide-panel
├── ui/priceradar.js    ← Preis-Radar tab logic
├── ui/tabs.js          ← Meine Reisen tab logic
├── app/ryanair.js      ← Ryanair tracker + chart + Discover
├── app/budget.js       ← budget + ActualBudget + expenses
├── app/dashboard.js    ← dashboard cards
├── app/googleflights.js
├── app/homair.js
├── app/booking.js
├── app/journal.js      ← Dawarich sync + trip list
├── app/onboarding.js   ← onboarding flow + field guide
└── app/bucketlist.js   ← bucket list (wishlist)
```

### Database Schema

```
trackers           — Ryanair trackers (origin, dest, dates, baggage)
price_snapshots    — Ryanair price history
gf_trackers        — Google Flights trackers
gf_snapshots       — Google Flights price history
homair_trackers    — Homair camping trackers
homair_snapshots   — Homair price history
booking_trackers   — Booking/Trivago trackers
booking_snapshots  — Booking price history
detected_trips     — Dawarich auto-detected overnight trips
settings           — Encrypted API keys (AES-Fernet)
```

---

## Navigation Structure

```
🧭 Übersicht        → Dashboard
🎯 Preis-Radar      → Übersicht / ✈️ Flüge (Ryanair | GFlights) / 🏨 Unterkünfte (Homair | Booking) / 🚗 Mietwagen (soon)
✨ Inspiration      → AI travel recommendations
🎒 Meine Reisen     → 📊 Übersicht / 🗺️ Wunschziele / 📓 Tagebuch / 💶 Budget
```

On mobile (`< 900px`): sidebar is replaced by a fixed bottom navigation bar.  
Settings (⚙️) and Field Guide (📖) are accessible from the header.

---

## Configuration

### .env

```bash
PORT=8765              # Frontend port (Nginx)
BACKEND_PORT=8766      # Backend port (FastAPI, directly accessible from browser)
APP_SECRET=...         # Encryption key for API keys — change before first start!
DB_PATH=/data/tracker.db
```

### API Keys (configured in the app Settings → APIs & KI)

| Service | Where to get | Used for |
|---|---|---|
| **SerpAPI** | [serpapi.com](https://serpapi.com) — Free: 100/month | Google Flights + Booking + Homair |
| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com) — Free | AI travel recommendations |
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | AI travel recommendations (alternative) |
| **Dawarich** | Your own Dawarich instance — token in Dawarich → Settings | Travel journal auto-detection |
| **ActualBudget** | Your own ActualBudget instance — server password | Budget sync |

---

## Dawarich Trip Detection Algorithm

WanderSuite automatically detects overnight trips from your GPS location history:

1. Fetch all location points from the Dawarich API (paginated)
2. Calculate Haversine distance from each point to your home coordinates
3. Keep only points **> 50 km** from home
4. Group by date
5. **Overnight condition:** minimum 2 consecutive days (= at least 1 night away)
6. Merge consecutive day-groups into a single trip (max. 2-day gap allowed)
7. Reverse geocoding via Nominatim (OpenStreetMap — no API key required)
8. Save to `detected_trips` table with upsert logic

Configure your home coordinates: Settings → Integrations → Dawarich → Latitude / Longitude.

---

## API Reference

Swagger UI: `http://YOUR-UNRAID-IP:8766/docs`

```
GET  /health                              — Health check
GET  /api/trackers                        — List Ryanair trackers
POST /api/trackers                        — Create tracker
POST /api/trackers/{id}/scrape            — Manual price fetch
PATCH /api/trackers/{id}/toggle           — Pause / resume tracker
DELETE /api/trackers/{id}                 — Delete tracker
GET  /api/prices/{id}                     — Price history (chart data)
GET  /api/google-flights                  — List Google Flights trackers
POST /api/google-flights                  — Create GF tracker
POST /api/google-flights/{id}/scrape      — Fetch GF price
GET  /api/accommodations/homair           — List Homair trackers
POST /api/accommodations/homair           — Create Homair tracker
POST /api/accommodations/homair/{id}/scrape
GET  /api/accommodations/booking          — List Booking trackers
POST /api/accommodations/booking          — Create Booking tracker
POST /api/accommodations/booking/{id}/scrape
POST /api/discover                        — AI travel recommendations
POST /api/dawarich/sync                   — Run Dawarich trip sync
GET  /api/dawarich/trips                  — List detected trips
DELETE /api/dawarich/trips/{id}           — Delete a trip
POST /api/budget/actual/summary           — ActualBudget month summary
POST /api/budget/actual/expenses          — Travel transactions by category
GET  /api/settings                        — Get settings (keys masked)
POST /api/settings                        — Save settings (encrypted)
GET  /api/settings/serpapi-quota          — SerpAPI monthly usage
```

---

## Automatic Scraping

APScheduler runs daily at **07:00 AM (Europe/Rome)** and scrapes all active Ryanair trackers. The timezone is configurable in Settings → General.

Manual trigger: **⟳ Jetzt** button on any tracker card.

---

## Contributing

1. Fork → feature branch → pull request
2. Python: PEP 8, type hints where possible
3. JS: Vanilla JS only, native ES modules, no frameworks, no build step
4. i18n: Add new strings to all 3 locale files (`de.json`, `it.json`, `en.json`)

### Adding a new language

```bash
cp frontend/locales/en.json frontend/locales/fr.json
# Translate all values (keys stay in English)
# Add a <button class="lang-btn" onclick="setLang('fr')">FR</button> in index.html header
```

### Adding a new tracker type

```
1. backend/my_scraper.py           — scraping logic
2. backend/routes/my_route.py      — FastAPI router
3. backend/database.py             — add tables + CRUD functions
4. backend/main.py                 — register the router
5. frontend/js/app/my_tracker.js   — CRUD functions (follow googleflights.js as template)
6. frontend/js/main.js             — import + window.* bindings
7. frontend/index.html             — add sub-tab in #radar-panel-* + HTML form
8. frontend/locales/*.json         — add translation keys
```

---

## Roadmap

- [ ] Skeleton loaders during data fetching
- [ ] CSV export for price history
- [ ] Currency toggle (EUR / USD / GBP)
- [ ] Telegram / Discord / Gotify price alerts
- [ ] Price threshold alerts per tracker
- [ ] SerpAPI quota display in dashboard
- [ ] Mobile PWA support (service worker + manifest)
- [ ] Car rental tracker (Preis-Radar → Mietwagen)

---

## License

**GNU Affero General Public License v3.0** — see [LICENSE](LICENSE).

> Self-hosting is explicitly encouraged. Modifications must be published under the same license.
