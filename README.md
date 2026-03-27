# WanderSuite v0.4

> A comprehensive, self-hosted travel management suite. Track flight prices, discover new destinations, and manage your travel budget — all in one place.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Version](https://img.shields.io/badge/version-0.4-orange.svg)](https://github.com/antonbier/tracker-an-te/releases/tag/v0.4)

---

## Features (v0.4)

- ✈️ **Ryanair Price Tracker** — Automatic daily scraping with anti-bot measures
- 🧳 **Baggage Cost Tracking** — Per-type baggage costs per tracker
- 🪑 **Seat Reservation** — Flat-rate seat cost per person/flight
- 📈 **Price History Charts** — Tickets / Baggage / Seat breakdown (Chart.js)
- 🌍 **Multilingual** — DE / IT / EN via external JSON locale files
- 📱 **Mobile-First** — Responsive sidebar nav, hamburger menu, touch-optimized
- ⚙️ **Settings Modal** — Backend URL, Timezone, Light/Dark mode, Integrations
- 🗺️ **Navigation** — Flights, Accommodations, Discover, Budget modules
- 🔵 **Google Flights UI** — Interface ready, scraper coming in v0.5
- ⛺ **Homair UI** — Interface ready, scraper coming in v0.6
- 🏨 **Booking/Trivago UI** — Interface ready, scraper coming in v0.6
- 💶 **Travel Budget** — Manual trip tracking, yearly budget, progress bar
- 🌟 **Discover** — AI recommendation shell (LLM integration in v0.5)
- 🐳 **Self-hosted** — Docker + docker-compose, SQLite, Unraid-ready
- ⏰ **Auto Scheduling** — Daily price fetch at 07:00 (Europe/Rome)

---

## Roadmap

- [x] v0.1 — Ryanair Tracker, i18n DE/IT/EN, Docker/Unraid
- [x] v0.2 — Mobile-first responsive redesign + Settings Modal
- [x] v0.3 — Main navigation (Flights, Accommodations, Discover, Budget)
- [x] v0.4 — Google Flights / Homair / Booking UI shells + Seat Reservation
- [ ] v0.5 — Google Flights scraper + AI recommendations (Gemini)
- [ ] v0.6 — Homair + Booking scrapers + ActualBudget sync
- [ ] v1.0 — Stable release, full test coverage

---

## Getting Started

### Quick Start (Docker)

```bash
git clone https://github.com/antonbier/tracker-an-te.git wandersuite
cd wandersuite
docker compose up -d --build
# Open http://localhost:8765
```

### Unraid

```bash
cd /mnt/user/appdata
git clone https://github.com/antonbier/tracker-an-te.git wandersuite
cd wandersuite
docker compose up -d --build
# Open http://YOUR-UNRAID-IP:8765
```

### Railway (Backend) + here.now (Frontend)

Push to GitHub → Railway auto-deploys backend, GitHub Action deploys frontend.

---

## Architecture

```
frontend/
  index.html          # Single-page app — navigation, all modules
  locales/
    de.json           # German translations
    it.json           # Italian translations
    en.json           # English translations
backend/
  main.py             # FastAPI app + APScheduler (daily 07:00)
  database.py         # SQLite layer — trackers + price_snapshots
  scraper.py          # Ryanair API scraper, anti-bot, seat cost
  scheduler.py        # Daily batch runner + manual trigger
  routes/
    trackers.py       # REST: CRUD + /scrape endpoint
    prices.py         # REST: price history for charts
docker/
  Dockerfile          # Python 3.12 slim image
  nginx.conf          # Reverse proxy → backend
docker-compose.yml    # Full stack: nginx + backend + volume
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

**Adding a new language:** Create `frontend/locales/xx.json` based on `en.json` and add a button in the header.

---

## License

Licensed under **GNU Affero General Public License v3.0** — see [LICENSE](LICENSE).
