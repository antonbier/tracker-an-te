# WanderSuite v0.1

> A comprehensive, self-hosted travel management suite. Track flight prices, discover new destinations, and manage your travel budget — all in one place.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Version](https://img.shields.io/badge/version-0.1-orange.svg)](https://github.com/antonbier/tracker-an-te/releases/tag/v0.1)

---

## Features (v0.1)

- ✈️ **Ryanair Price Tracker** — Monitor flight prices with automatic daily scraping
- 🧳 **Baggage Cost Tracking** — Includes baggage costs per tracker
- 📈 **Price History Charts** — Visualize price trends over time (Chart.js)
- 🌍 **Multilingual** — German, Italian, English (DE/IT/EN)
- 🐳 **Self-hosted** — Docker + docker-compose ready, SQLite database
- ⏰ **Automatic Scheduling** — Daily price fetch at 07:00 (Europe/Rome)

---

## Roadmap

- [ ] v0.2 — Mobile-first responsive redesign + Settings Modal
- [ ] v0.3 — Main navigation (Flights, Accommodations, Discover, Budget)
- [ ] v0.4 — Google Flights Tracker, Homair/Booking placeholders
- [ ] v0.5 — "Discover Something New" AI recommendations (Gemini integration)
- [ ] v0.6 — Travel Budget module + ActualBudget sync
- [ ] v1.0 — Stable release, full test coverage

---

## Getting Started

### Installation

```bash
git clone https://github.com/antonbier/tracker-an-te.git wandersuite
cd wandersuite
docker compose up -d --build
```

Access via `http://localhost:8765`

### Unraid

```bash
cd /mnt/user/appdata
git clone https://github.com/antonbier/tracker-an-te.git wandersuite
cd wandersuite
docker compose up -d --build
```

---

## Architecture

```
frontend/          # Static HTML + Vanilla JS (Nginx)
backend/
  main.py          # FastAPI + APScheduler
  database.py      # SQLite layer
  scraper.py       # Ryanair API scraper
  scheduler.py     # Daily batch runner
  routes/          # REST endpoints
docker/            # Dockerfile + nginx.conf
docker-compose.yml
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

Licensed under **GNU Affero General Public License v3.0** — see [LICENSE](LICENSE).
