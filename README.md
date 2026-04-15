# 🧭 WanderSuite

**Your self-hosted AI travel hub.** Plan, track and relive every journey — all data stays on your own server.

[![Beta](https://img.shields.io/badge/branch-beta-orange)](https://github.com/antonbier/tracker-an-te/tree/beta)
[![Stack](https://img.shields.io/badge/stack-Svelte5%20%2B%20FastAPI-blue)](#tech-stack)
[![License](https://img.shields.io/badge/license-MIT-green)](#license)

---

## ✨ Vision

WanderSuite accompanies you through **three phases** of every trip:

| Phase | Name | What it does |
|-------|------|-------------|
| 1 | ✈️ **Planning** | WanderWizzard assistant, PriceRadar (4 sources), AI destination suggestions, Trip Hub |
| 2 | 🌍 **On Tour** | Live checklists, weather widget, budget tracker, booking slots |
| 3 | 📓 **Experienced** | GPS journal (Dawarich), photo gallery (Immich), expense sync (ActualBudget) |

---

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose
- Optional: Dawarich, Immich, ActualBudget instances

### 1. Clone & configure

```bash
git clone https://github.com/antonbier/tracker-an-te.git
cd tracker-an-te
cp .env.example .env
# Edit .env with your values
```

### 2. docker-compose.yml

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: wandersuite-backend
    restart: unless-stopped
    environment:
      - TZ=${TZ:-Europe/Rome}
      - APP_SECRET=${APP_SECRET}
      - DB_PATH=/app/data/tracker.db
      - AUTH_ENABLED=${AUTH_ENABLED:-false}
      - JWT_SECRET=${JWT_SECRET:-change-me-in-production}
    volumes:
      - ${DATA_DIR:-./data}:/app/data
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    container_name: wandersuite-frontend
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    ports:
      - "${HOST_PORT:-8080}:80"
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. Run

```bash
docker compose up -d
# Open http://localhost:8080
# Click 🪄 in the header to run the Setup Wizard
```

---

## 🌟 Core Features

### 🪄 WanderWizzard (5-step Trip Assistant)
- Choose destination manually or let AI suggest one
- Configure travelers, luggage presets, flight time windows
- One-click launch into PriceRadar for price tracking
- Connects with Trip Hub for full lifecycle management

### 🎯 PriceRadar (4 Providers)
| Provider | Key Required | Notes |
|----------|-------------|-------|
| 🟠 Ryanair | No | Native API, IATA codes |
| 🔵 Google Flights | SerpAPI | Airline + flight numbers |
| ⛺ Homair | No | Camping via scraping |
| 🏨 Booking.com | SerpAPI | Hotels via Google Hotels |

### 🗺️ Trip Hub (Widget System)
Each planned WS-Trip gets a dedicated hub page with modular widgets:
- **🌤️ Weather** — 7-day Open-Meteo forecast (auto-fetched when ≤7 days to departure)
- **💶 Budget** — Breakdown: flight + hotel + cash expenses vs. total budget
- **✈️ Booking Slots** — Link PriceRadar trackers to trips, mark as booked with final price
- **✅ Checklist** — AI-generated todo list (KI-aware of destination + travel type)

### 📊 Dashboard
- Hero section with next/last trip, countdown, budget progress
- Travel inspiration: nostalgia tile (archived trips), KI suggestions
- Compact trips list + active tracker grid

### 🌍 Discovery (AI Suggestions)
- Personalized suggestions using your travel personality profile
- Powered by Gemini Flash (free) or OpenAI gpt-4o-mini
- Image enrichment via Immich (your own photos) or Unsplash

---

## 🔗 Self-Hosted Integrations

### 📡 Dawarich (GPS Journey Detection)
Automatically detects trips from your GPS history:
- Points >50 km from home location for ≥2 consecutive days
- Reverse geocoding via Nominatim (OSM)
- Populates travel journal + ScratchMap

**Setup:** Dawarich → Settings → API Keys → copy token → enter in WanderSuite Wizard Step 2

### 📸 Immich (Photo Integration)
- Provides trip background images matched by location
- Future: photo gallery widget in Trip Hub

**Setup:** Immich → Account Settings → API Keys → copy key → enter in Wizard Step 2

### 💳 ActualBudget (Expense Sync)
- Import travel expenses by category name (e.g. `Holiday, Flights, Hotel`)
- Auto-maps to WanderSuite trip budget

**Setup:** ActualBudget → click budget name → copy ID from URL → enter in Wizard Step 2

---

## 🤖 AI Configuration

All keys stored Fernet-encrypted. All optional — app works without them.

| Provider | Use | Cost | Where to get |
|----------|-----|------|-------------|
| **Google Gemini** | AI suggestions, Discovery | Free (Flash) | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| **OpenAI** | Alternative to Gemini | ~$0.00015/1k tokens | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **SerpAPI** | Google Flights + Hotels | 100/mo free | [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key) |

---

## ⚙️ Settings Architecture

### Global Settings (admin, all users)
`timezone` · `date_format` · `currency` · `home_lat/lon/name` · `serpapi_key` · `gemini_key` · `openai_key` · notification keys

### Per-User Settings (each user)
`dawarich_url/token` · `immich_url/key` · `actual_url/token/file` · `home_lat/lon/name` (override) · WanderWizzard defaults · travel personality

**Priority for home location:** per-user setting → global setting → none

---

## 🛡️ Authentication

Disabled by default (`AUTH_ENABLED=false`). Enable for multi-user:

```env
AUTH_ENABLED=true
JWT_SECRET=your-very-long-secret-here
WEBAUTHN_RP_ID=your-domain.com
WEBAUTHN_ORIGIN=https://your-domain.com
```

Supports: password login + WebAuthn/Passkeys

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Svelte 5, SvelteKit, Tailwind CSS v4 |
| Backend | FastAPI, Python 3.12 |
| Database | SQLite (single-file, no migrations needed) |
| Deployment | Docker Compose, Nginx |
| GPS | Dawarich integration + Nominatim geocoding |
| Photos | Immich integration |
| Weather | Open-Meteo (no key needed) |
| AI | Google Gemini Flash, OpenAI gpt-4o-mini |
| Price search | SerpAPI, Ryanair native, Homair scraper |

---

## 📁 Project Structure

```
tracker-an-te/
├── backend/
│   ├── main.py              # FastAPI app + routes
│   ├── database.py          # SQLite helpers
│   ├── settings_manager.py  # Global + per-user settings (Fernet-encrypted)
│   ├── auth_jwt.py          # JWT + WebAuthn
│   └── routes/
│       ├── settings.py      # /api/settings + /api/settings/wizard/step
│       ├── ws_trips.py      # WS-Trip CRUD + todos + budget
│       ├── trackers.py      # PriceRadar trackers
│       ├── discovery.py     # AI suggestions
│       └── ...
├── svelte/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   │   ├── SetupWizard.svelte   # 6-step onboarding wizard
│   │   │   │   ├── FieldGuide.svelte    # In-app help (6 tabs)
│   │   │   │   ├── WanderWizzard.svelte # Trip planning assistant
│   │   │   │   ├── Settings.svelte      # Settings overlay
│   │   │   │   └── pages/
│   │   │   │       ├── Dashboard.svelte
│   │   │   │       ├── TripHub.svelte
│   │   │   │       └── PriceRadar.svelte
│   │   │   ├── stores.js    # Svelte stores (wizardOpen, settingsOpen, ...)
│   │   │   └── i18n.js      # i18n helper
│   │   └── locales/
│   │       ├── de.json      # German (primary)
│   │       └── en.json      # English
├── docker/
│   ├── Dockerfile
│   └── Dockerfile.frontend
├── docker-compose.yml
├── claude.md                # Architecture docs for AI assistants
└── README.md
```

---

## 🌐 i18n

Full German + English support. All UI strings in `svelte/src/locales/{de,en}.json`.
Switch language via the language selector in the top navigation bar.

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

*Built with ❤️ for self-hosters who love to travel.*
