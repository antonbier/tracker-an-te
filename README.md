# WanderSuite

> Self-hosted travel management suite — track flight prices, manage your budget, journal your trips and discover new destinations. No subscriptions, no tracking, runs on your own hardware.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)
[![PWA](https://img.shields.io/badge/PWA-installable-green.svg)](#pwa--mobile)

---

## Features

| Module | Description |
|--------|-------------|
| 🎯 **Preis-Radar** | Track Ryanair, Google Flights, Homair and Booking prices with daily auto-scraping |
| 🔔 **Price Alerts** | Telegram + Gotify notifications when a price drops below your target |
| ✨ **Inspiration** | AI travel recommendations via Gemini or OpenAI |
| 🎒 **Meine Reisen** | Trips · Budget · Bucket List · Travel Journal — all in one hub |
| 📓 **Travel Journal** | Automatic trip detection from Dawarich GPS history |
| 💶 **Budget** | Manual budget tracking + ActualBudget sync |
| 🧭 **Dashboard** | Live overview: active trackers, budget donut, recent trips |
| 🌍 **Multilingual** | Deutsch · Italiano · English |
| 📱 **PWA** | Installable on iOS and Android, mobile bottom navigation |
| 🔐 **Encrypted Settings** | All API keys AES-Fernet encrypted in SQLite |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/antonbier/tracker-an-te.git wandersuite
cd wandersuite

# 2. Configure
cp .env.example .env
nano .env

# 3. Start — Docker builds everything (no Node.js needed on host)
docker compose up -d --build
```

Open `http://YOUR-IP:8765` — the onboarding wizard will guide you through setup.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST_PORT` | `8765` | Frontend port (Nginx) |
| `BACKEND_PORT` | `8766` | Backend port (FastAPI / Swagger) |
| `TZ` | `Europe/Rome` | Timezone for daily scraping (07:00) |
| `DATA_DIR` | `./data` | Host path for SQLite DB |
| `APP_SECRET` | *(required)* | AES-Fernet encryption key — set once, never change |
| `AUTH_ENABLED` | `false` | Set `true` to require login |
| `JWT_SECRET` | *(required if auth)* | JWT signing secret |

**Generate APP_SECRET:**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Updating

```bash
git pull && docker compose up -d --build
```

Docker cache skips unchanged layers — only what changed gets rebuilt.

---

## Architecture

```
Browser
  └─► Nginx :8765
        ├─ /* ──────────► Svelte SPA (built by Docker Multi-Stage)
        └─ /api/* ──────► FastAPI backend:8000 (internal proxy)

Stack:
  Frontend  — Svelte 5 + SvelteKit + Tailwind CSS v4 (built via Node 20 in Docker)
  Backend   — FastAPI + SQLite + APScheduler
  Deploy    — Docker Compose (Unraid / any Linux host)
  Cloud     — here.now (frontend) · Railway (backend)
```

```
wandersuite/
├── svelte/              # Frontend (Svelte 5 + SvelteKit)
│   ├── src/
│   │   ├── lib/         # Stores, API client, i18n, components
│   │   └── routes/      # SvelteKit routes (+layout, +page)
│   └── package.json
├── backend/             # FastAPI backend
│   ├── main.py          # Entry point + scheduler
│   ├── database.py      # SQLite schema + CRUD
│   ├── settings_manager.py  # AES-Fernet encryption
│   └── routes/          # API route handlers
├── docker/
│   ├── Dockerfile           # Backend (Python)
│   ├── Dockerfile.frontend  # Frontend (Node build → Nginx)
│   └── nginx.conf           # SPA + API proxy config
├── docker-compose.yml
└── .env.example
```

---

## Integrations

### SerpAPI
Required for Google Flights, Homair and Booking trackers.
Free tier: 100 searches/month → [serpapi.com](https://serpapi.com)

### Dawarich
Self-hosted GPS tracker. WanderSuite detects overnight trips automatically:
points > 50 km from home, 2+ consecutive nights → geocoded via Nominatim.
→ [dawarich.app](https://dawarich.app)

### ActualBudget
Self-hosted budget app. WanderSuite syncs travel category expenses.
→ [actualbudget.org](https://actualbudget.org)

### AI (Gemini / OpenAI)
For the Inspiration tab. Gemini is free via Google AI Studio.
→ [aistudio.google.com](https://aistudio.google.com)

### Notifications
**Telegram:** BotFather → `/newbot` → Bot Token + Chat ID from @myidbot  
**Gotify:** Apps → Create Application → App Token

---

## API

Swagger UI: `http://YOUR-IP:8766/docs`

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET/POST` | `/api/trackers` | Ryanair trackers |
| `POST` | `/api/trackers/{id}/scrape` | Manual price fetch |
| `GET` | `/api/prices/{id}/export.csv` | Download price history |
| `GET/POST` | `/api/google-flights` | Google Flights trackers |
| `GET/POST` | `/api/accommodations/homair` | Homair trackers |
| `GET/POST` | `/api/accommodations/booking` | Booking trackers |
| `POST` | `/api/dawarich/sync` | Sync Dawarich GPS trips |
| `GET` | `/api/dawarich/trips` | List detected trips |
| `POST` | `/api/budget/actual/transactions` | ActualBudget sync |
| `GET/POST` | `/api/settings` | Encrypted settings |
| `POST` | `/api/discover` | AI recommendations |
| `GET` | `/health` | Health check + version |

---

## PWA & Mobile

Installable as a Progressive Web App.

**iOS (Safari):** Share → Add to Home Screen  
**Android (Chrome):** Install button in header or ⋮ → Install app

Requires HTTPS for full PWA support (Railway / Cloudflare Tunnel / reverse proxy).

---

## Auth (optional)

By default `AUTH_ENABLED=false` — no login required, suitable for home network use.

To enable login:
```bash
AUTH_ENABLED=true
JWT_SECRET=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
```

On first start with auth enabled, a setup screen appears to create the admin account.
Additional users can be managed in Settings → Admin.

---

## License

**GNU Affero General Public License v3.0** — [LICENSE](LICENSE)

> Self-hosting is explicitly encouraged. Modifications must be published under the same license.
