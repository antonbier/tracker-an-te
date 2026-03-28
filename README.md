# WanderSuite

> Self-hosted travel management suite — track flight prices, visualise visited countries, manage your budget, journal your trips and discover new destinations. No subscriptions, no tracking, runs on your own hardware.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)
[![PWA](https://img.shields.io/badge/PWA-installable-green.svg)](#pwa--mobile)

---

## Features

| Module | Description | Status |
|--------|-------------|--------|
| 🎯 **Preis-Radar** | Two-level nav: Flights / Accommodations / Car Rental (soon) | ✅ |
| 🟠 **Ryanair Tracker** | Daily price scraping, baggage, seat costs, price history chart | ✅ |
| ✈️ **Google Flights** | Live prices via SerpAPI | ✅ |
| ⛺ **Homair** | Camping accommodation prices via SerpAPI | ✅ |
| 🏨 **Booking.com** | Hotel prices via SerpAPI Google Hotels | ✅ |
| ✨ **Inspiration** | AI travel recommendations (Gemini / OpenAI) | ✅ |
| 🗺️ **Scratch Map** | Interactive world map — visited countries from Dawarich | ✅ |
| 🎒 **Meine Reisen** | Budget · Journal · Bucket List — all in one hub | ✅ |
| 📓 **Travel Journal** | Automatic overnight trip detection from Dawarich GPS history | ✅ |
| 💶 **Travel Budget** | Manual trips + ActualBudget sync + expense table | ✅ |
| 🗺️ **Bucket List** | Wishlist with emoji, "when" field — stored client-side | ✅ |
| 🧭 **Dashboard** | Live stats: visited countries, remaining budget, tracker summary | ✅ |
| 📖 **Field Guide** | Full slide-panel manual with 4 tabs | ✅ |
| 🌍 **Multilingual** | Deutsch · Italiano · English | ✅ |
| 🎨 **Modern Explorer** | Light-first theme, Playfair serif, dark mode opt-in | ✅ |
| 📱 **PWA + Bottom Bar** | Installable on iOS/Android, mobile bottom navigation | ✅ |
| 🔐 **Encrypted Settings** | API keys encrypted with AES-Fernet in SQLite | ✅ |

---

## Quick Start (Unraid / Docker)

```bash
# 1. Clone
cd /mnt/user/appdata
git clone https://github.com/antonbier/tracker-an-te.git wandersuite
cd wandersuite

# 2. Configure
cp .env.example .env
nano .env    # Set HOST_PORT, TZ, DATA_DIR, APP_SECRET

# 3. Start
docker compose up -d --build
```

Open **`http://YOUR-UNRAID-IP:8765`** (or your `HOST_PORT`) in your browser.  
First-time setup: ⚙️ Settings → Backend URL → `http://YOUR-UNRAID-IP:8766`

### Updating

```bash
cd /mnt/user/appdata/wandersuite
git pull && docker compose up -d --build
# Database and .env are preserved
```

### Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST_PORT` | `8765` | Frontend port (Nginx, open in browser) |
| `BACKEND_PORT` | `8766` | Backend port (FastAPI, called directly by browser for API) |
| `TZ` | `Europe/Rome` | Timezone for daily scraping cron (07:00) |
| `DATA_DIR` | `./data` | Host path for SQLite DB and persistent data |
| `APP_SECRET` | *(required)* | AES-Fernet encryption key — **change before first start!** |

**Unraid tip:** Set `DATA_DIR=/mnt/user/appdata/wandersuite/data`

### Data Persistence

The SQLite database lives at `${DATA_DIR}/tracker.db` on the host, mounted into the container at `/app/data/tracker.db`. All data (trackers, price history, detected trips, settings) survives container restarts and updates.

---

## Architecture

```
wandersuite/
├── frontend/                    # Static SPA — served by Nginx
│   ├── index.html               # All HTML + CSS (no build step)
│   ├── manifest.json            # PWA manifest
│   ├── sw.js                    # Service Worker (network-first cache)
│   ├── icons/                   # PWA icons (192×192, 512×512 PNG)
│   ├── locales/                 # i18n JSON files
│   │   ├── de.json              # German (default)
│   │   ├── en.json              # English
│   │   └── it.json              # Italian
│   └── js/                      # Native ES Modules (no bundler)
│       ├── main.js              # Entry point: imports + window.* + DOMContentLoaded
│       ├── core/
│       │   ├── state.js         # Global mutable state + setter functions
│       │   └── api.js           # HTTP client api() + checkApiStatus()
│       ├── ui/
│       │   ├── i18n.js          # loadLocale, t(), applyTranslations, setLang
│       │   ├── nav.js           # navigate(), sidebar, bottom bar, View Transitions
│       │   ├── toast.js         # Toast notifications
│       │   ├── settings.js      # Settings slide-panel (3 tabs)
│       │   ├── priceradar.js    # Preis-Radar two-level tab logic
│       │   ├── tabs.js          # Meine Reisen sub-tab logic
│       │   └── fieldguide.js    # Field Guide slide-panel (4 tabs)
│       └── app/
│           ├── ryanair.js       # Ryanair tracker CRUD + Chart.js + AI Discover
│           ├── budget.js        # Budget, ActualBudget sync, expense table
│           ├── dashboard.js     # Home dashboard + Meine Reisen live stats
│           ├── scratchmap.js    # Scratch Map (jsvectormap world map)
│           ├── googleflights.js # Google Flights tracker CRUD
│           ├── homair.js        # Homair tracker CRUD
│           ├── booking.js       # Booking.com tracker CRUD
│           ├── journal.js       # Dawarich sync + trip list
│           ├── onboarding.js    # Full-screen onboarding wizard
│           └── bucketlist.js    # Bucket List (localStorage only)
│
├── backend/                     # FastAPI application
│   ├── main.py                  # App entry point + APScheduler (daily 07:00)
│   ├── database.py              # SQLite schema + CRUD
│   ├── settings_manager.py      # AES-Fernet encrypted settings
│   ├── scraper.py               # Ryanair API scraper
│   ├── google_scraper.py        # Google Flights via SerpAPI
│   ├── homair_scraper.py        # Homair via SerpAPI Google Hotels
│   ├── booking_scraper.py       # Booking via SerpAPI Google Hotels
│   ├── dawarich.py              # Dawarich sync + trip detection algorithm
│   ├── countries.py             # Country name → ISO-2 mapping (100+ entries)
│   ├── actual_budget.py         # ActualBudget REST client (actualpy)
│   ├── gemini.py                # Google Gemini AI integration
│   ├── openai_client.py         # OpenAI gpt-4o-mini integration
│   ├── scheduler.py             # Daily batch job runner
│   └── routes/
│       ├── trackers.py          # /api/trackers
│       ├── prices.py            # /api/prices
│       ├── google_flights.py    # /api/google-flights
│       ├── accommodations.py    # /api/accommodations/homair + /booking
│       ├── budget.py            # /api/budget/actual/*
│       ├── dawarich.py          # /api/dawarich/*
│       ├── discover.py          # /api/discover
│       ├── settings.py          # /api/settings
│       └── dashboard.py         # /api/dashboard/stats
│
├── docker/
│   ├── Dockerfile               # Python 3.12 slim backend image
│   └── nginx.conf               # Nginx with explicit PWA routes
│
├── docker-compose.yml
├── .env.example
├── CLAUDE.md                    # AI assistant context + architecture reference
└── README.md
```

---

## Navigation Structure

```
🧭 Übersicht      →  Home dashboard
🎯 Preis-Radar    →  [📊 Übersicht] [✈️ Flüge: Ryanair | Google] [🏨 Unterkünfte: Homair | Booking] [🚗 Mietwagen]
✨ Inspiration    →  AI travel recommendations
🎒 Meine Reisen  →  [📊 Übersicht + Scratch Map] [🗺️ Wunschziele] [📓 Tagebuch] [💶 Budget]
```

**Mobile** (`< 900px`): Fixed bottom navigation bar (Airbnb-style).  
**Header** (always): ⚙️ Settings · 📖 Field Guide · 🌐 Language · API status dot

---

## API Reference

Swagger UI: `http://YOUR-IP:8766/docs`

### Ryanair Trackers
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/trackers` | List all trackers |
| `POST` | `/api/trackers` | Create tracker |
| `GET` | `/api/trackers/{id}` | Get single tracker |
| `DELETE` | `/api/trackers/{id}` | Delete tracker |
| `PATCH` | `/api/trackers/{id}/toggle` | Pause / resume |
| `POST` | `/api/trackers/{id}/scrape` | Manual price fetch |
| `GET` | `/api/prices/{id}` | Price history (chart data) |

### Google Flights
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/google-flights` | List trackers |
| `POST` | `/api/google-flights` | Create tracker |
| `DELETE` | `/api/google-flights/{id}` | Delete tracker |
| `POST` | `/api/google-flights/{id}/scrape` | Fetch price |

### Accommodations
| Method | Path | Description |
|--------|------|-------------|
| `GET/POST` | `/api/accommodations/homair` | List / create |
| `DELETE` | `/api/accommodations/homair/{id}` | Delete |
| `POST` | `/api/accommodations/homair/{id}/scrape` | Fetch price |
| `GET/POST` | `/api/accommodations/booking` | List / create |
| `DELETE` | `/api/accommodations/booking/{id}` | Delete |
| `POST` | `/api/accommodations/booking/{id}/scrape` | Fetch price |

### Dawarich & Journal
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/dawarich/sync` | Run full Dawarich sync |
| `GET` | `/api/dawarich/trips` | List detected trips |
| `DELETE` | `/api/dawarich/trips/{id}` | Delete trip |
| `GET` | `/api/dawarich/countries` | ISO-2 codes of visited countries |
| `POST` | `/api/dawarich/debug` | Debug Dawarich point format |

### Budget & Dashboard
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/budget/actual/summary` | ActualBudget month summary |
| `POST` | `/api/budget/actual/expenses` | Travel transactions by category |
| `GET` | `/api/dashboard/stats` | Live stats: visited places + remaining budget |

### Settings & AI
| Method | Path | Description |
|--------|------|-------------|
| `GET/POST` | `/api/settings` | Get / save encrypted settings |
| `GET` | `/api/settings/serpapi-quota` | SerpAPI monthly usage |
| `POST` | `/api/discover` | AI travel recommendations |
| `GET` | `/health` | Health check |

---

## Integrations Setup

### SerpAPI
Required for Google Flights and Booking trackers.  
Free tier: 100 searches/month → [serpapi.com](https://serpapi.com)

### Google Gemini
For AI travel recommendations in the Inspiration tab.  
Free on Google AI Studio → [aistudio.google.com](https://aistudio.google.com)

### Dawarich
Self-hosted GPS location history app. WanderSuite reads your location points, detects overnight trips and displays them on the **Scratch Map**.  
→ [dawarich.app](https://dawarich.app)

**Trip Detection Algorithm:**
1. Fetch all GPS points (paginated)
2. Haversine distance from home coordinates
3. Keep points > 50 km from home
4. Group into days → overnight = 2+ consecutive nights
5. Merge trips (max 2-day gap allowed)
6. Reverse geocode via Nominatim (no API key needed)
7. Map country names → ISO-2 codes for Scratch Map

Configure home coordinates: Settings → Integrations → Dawarich → Lat / Lon

### ActualBudget
Self-hosted budget app. WanderSuite syncs travel categories and shows remaining budget in the dashboard.  
Uses `actualpy` (≥ 0.21.0).

Configure: Settings → Integrations → ActualBudget → URL, Password, Budget Name, Travel Categories

---

## PWA & Mobile

WanderSuite is an installable Progressive Web App.

**iOS (Safari):** Share → Add to Home Screen  
**Android (Chrome):** ⬇ App button appears in header once PWA criteria are met, or ⋮ → Install app

**Requirements for install prompt:**
- Must be served over **HTTPS** (Railway, Cloudflare, etc.)
- Service Worker must be registered successfully
- Valid `manifest.json` with PNG icons

---

## Dark Mode

Toggle in Settings → General → Dark Mode.  
Stored in `localStorage` as `theme: 'dark'`. Theme is restored on page load.

The dark theme "Mitternacht" uses deep night-blue `#12141c` as background while keeping the terracotta accent `#D95D39` unchanged — preserving the Wanderlust character.

---

## Contributing

1. Fork → feature branch → pull request
2. **Python:** PEP 8, type hints where practical
3. **JS:** Vanilla ES Modules only — no bundler, no npm, no frameworks
4. **i18n:** Add all new string keys to `de.json`, `en.json` AND `it.json`

### Adding a new language

```bash
cp frontend/locales/en.json frontend/locales/fr.json
# Translate all values (keys stay in English)
# Add <button class="lang-btn" onclick="setLang('fr')">FR</button> in index.html header
```

### Adding a new tracker type

```
1. backend/my_scraper.py              — scraping logic
2. backend/routes/my_route.py         — FastAPI router
3. backend/database.py                — tables + CRUD functions
4. backend/main.py                    — register router
5. frontend/js/app/my_tracker.js      — CRUD functions (use googleflights.js as template)
6. frontend/js/main.js                — import + window.* bindings
7. frontend/index.html                — sub-tab in Preis-Radar + HTML form
8. frontend/locales/*.json            — translation keys (all 3 languages)
```

---

## Roadmap

- [ ] Skeleton loaders during data fetching
- [ ] CSV export for price history
- [ ] Currency toggle (EUR / USD / GBP)
- [ ] Price threshold alerts per tracker
- [ ] Telegram / Discord / Gotify push notifications
- [ ] Car rental tracker (Preis-Radar → Mietwagen)
- [ ] SerpAPI quota widget in dashboard
- [ ] Scratch Map: click country → show trip details

---

## License

**GNU Affero General Public License v3.0** — [LICENSE](LICENSE)

> Self-hosting is explicitly encouraged. Modifications must be published under the same license.
