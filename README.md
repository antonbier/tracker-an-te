# WanderSuite

> Self-hosted travel management suite — track flight prices, sync your travel journal, manage your budget, and discover new destinations. Built for Unraid, runs everywhere with Docker.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Version](https://img.shields.io/badge/version-1.0-green.svg)](https://github.com/antonbier/tracker-an-te/releases/tag/v1.0)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

---

## Screenshots

> Dashboard · Ryanair Tracker · Reisetagebuch · Budget

---

## Features

| Modul | Feature | Status |
|---|---|---|
| ✈️ Ryanair Tracker | Tägliches Preis-Scraping, Gepäck, Sitzplatz | ✅ Live |
| 🔵 Google Flights | Preise via SerpAPI | ✅ Live |
| ⛺ Homair | Camping-Preise via HTML-Scraping | ✅ Live |
| 🏨 Booking/Trivago | Hotelpreise via SerpAPI Google Hotels | ✅ Live |
| 🌟 Discover | KI-Reiseempfehlungen (Gemini + OpenAI) | ✅ Live |
| 💶 Travel Budget | Manuelles Tracking + ActualBudget Sync | ✅ Live |
| 📓 Reisetagebuch | Automatische Trip-Erkennung via Dawarich | ✅ Live |
| 🏠 Dashboard | Übersicht, Budget-Donut, Tracker-Cards | ✅ Live |
| 📖 Field Guide | Integriertes FAQ / Hilfe-System | ✅ Live |
| 🌍 Mehrsprachig | Deutsch, Italiano, English | ✅ Live |
| 🎨 Adventure Look | Terracotta/Earth-Tone, Playfair Display | ✅ Live |
| 🔐 Encrypted Settings | AES-Fernet verschlüsselte API Keys | ✅ Live |

---

## Schnellstart (Unraid)

```bash
# 1. Repo klonen
cd /mnt/user/appdata
git clone https://github.com/antonbier/tracker-an-te.git wandersuite
cd wandersuite

# 2. Umgebungsvariablen konfigurieren
cp .env.example .env
nano .env  # APP_SECRET und PORT anpassen

# 3. Starten
docker compose up -d --build
```

Browser: **`http://DEINE-UNRAID-IP:8765`**

**Wichtig:** Im Dashboard → Einstellungen → Backend-URL: `http://DEINE-UNRAID-IP:8766`

### Update

```bash
cd /mnt/user/appdata/wandersuite
git pull
docker compose up -d --build
```

---

## Architektur

```
wandersuite/
├── frontend/
│   ├── index.html              # Single-Page-App (HTML + CSS + JS)
│   └── locales/
│       ├── de.json             # Deutsche Übersetzungen
│       ├── it.json             # Italienische Übersetzungen
│       └── en.json             # Englische Übersetzungen
│
├── backend/
│   ├── main.py                 # FastAPI App + APScheduler
│   ├── database.py             # SQLite Layer (alle Tabellen + CRUD)
│   ├── settings_manager.py     # Verschlüsselte Settings (AES-Fernet)
│   ├── scraper.py              # Ryanair API Scraper (Anti-Bot)
│   ├── google_scraper.py       # Google Flights via SerpAPI
│   ├── homair_scraper.py       # Homair Camping HTML-Scraper
│   ├── booking_scraper.py      # Booking via SerpAPI Google Hotels
│   ├── gemini.py               # Google Gemini AI Integration
│   ├── openai_client.py        # OpenAI gpt-4o-mini Integration
│   ├── dawarich.py             # Dawarich Sync + Trip Detection
│   ├── actual_budget.py        # ActualBudget REST API Client
│   ├── scheduler.py            # Täglicher Batch-Runner (07:00 Uhr)
│   ├── requirements.txt
│   └── routes/
│       ├── trackers.py         # /api/trackers — Ryanair CRUD
│       ├── prices.py           # /api/prices — Preisverlauf
│       ├── google_flights.py   # /api/google-flights
│       ├── accommodations.py   # /api/accommodations/homair + booking
│       ├── discover.py         # /api/discover — KI-Empfehlungen
│       ├── budget.py           # /api/budget — ActualBudget Sync
│       ├── dawarich.py         # /api/dawarich — Trip Sync
│       └── settings.py         # /api/settings — Verschlüsselte Keys
│
├── docker/
│   ├── Dockerfile              # Python 3.12 slim Backend Image
│   └── nginx.conf              # Nginx Reverse Proxy Config
│
├── docker-compose.yml          # Stack Definition
├── .env.example                # Umgebungsvariablen Template
└── README.md
```

### Datenbank-Schema

```
trackers           — Ryanair Tracker
price_snapshots    — Ryanair Preis-History
gf_trackers        — Google Flights Tracker
gf_snapshots       — Google Flights Preis-History
homair_trackers    — Homair Tracker
homair_snapshots   — Homair Preis-History
booking_trackers   — Booking/Trivago Tracker
booking_snapshots  — Booking Preis-History
detected_trips     — Dawarich Trip-Erkennung
settings           — Verschlüsselte API Keys
```

---

## Konfiguration

### .env

```bash
PORT=8765              # Frontend Port
BACKEND_PORT=8766      # Backend Port (direkt erreichbar)
APP_SECRET=...         # Encryption Key für API Keys
DB_PATH=/data/tracker.db
```

### API Keys (in den App-Einstellungen)

| Service | Woher | Wofür |
|---|---|---|
| **SerpAPI** | [serpapi.com](https://serpapi.com) — Free: 100/Monat | Google Flights + Booking |
| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com) — kostenlos | KI-Reiseempfehlungen |
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | KI-Reiseempfehlungen (Alternative) |
| **Dawarich** | Eigene Instanz — Token in Dawarich Settings | Reisetagebuch |
| **ActualBudget** | Eigene Instanz — Server Password | Budget Sync |

### Dawarich Trip-Erkennung

Der Algorithmus erkennt automatisch Übernacht-Reisen:

1. Alle Location-Punkte von Dawarich API laden
2. Haversine-Distanz zu Home-Koordinaten berechnen
3. Nur Punkte **> 50 km** von Home behalten
4. Nach Datum gruppieren
5. **Overnight-Bedingung:** min. 2 aufeinanderfolgende Tage (= min. 1 Nacht)
6. Zusammenhängende Tage zu einem Trip zusammenfassen (max. 2 Tage Lücke)
7. Reverse Geocoding via Nominatim (OpenStreetMap, kostenlos)

Home-Koordinaten in Einstellungen → Integrationen → Dawarich eintragen (z.B. `46.7987` / `11.7188` für Bozen).

---

## API Dokumentation

Swagger UI: `http://DEINE-UNRAID-IP:8766/docs`

### Wichtigste Endpoints

```
GET  /health                          — Status Check
GET  /api/trackers                    — Alle Ryanair Tracker
POST /api/trackers                    — Tracker anlegen
POST /api/trackers/{id}/scrape        — Manueller Preis-Abruf
GET  /api/prices/{id}                 — Preisverlauf (Chart-Daten)
GET  /api/google-flights              — Google Flights Tracker
POST /api/google-flights/{id}/scrape  — GF Preis-Abruf
GET  /api/accommodations/homair       — Homair Tracker
GET  /api/accommodations/booking      — Booking Tracker
POST /api/discover                    — KI-Reiseempfehlungen
POST /api/dawarich/sync               — Dawarich Trip-Sync
GET  /api/dawarich/trips              — Erkannte Trips
POST /api/budget/actual/summary       — ActualBudget Summary
POST /api/budget/actual/expenses      — Reise-Transaktionen
GET  /api/settings                    — Settings abrufen (maskiert)
POST /api/settings                    — Settings speichern (verschlüsselt)
```

---

## Automatisches Scraping

Der APScheduler läuft täglich um **07:00 Uhr (Europe/Rome)** und scrapt alle aktiven Ryanair Tracker automatisch. Timezone in Einstellungen → Allgemein konfigurierbar.

Manueller Trigger: **⟳ Jetzt** Button im Dashboard.

---

## Für andere Claude-Instanzen / Contributors

### Projektstand (Stand: März 2026)

- **Version:** v1.0 (stabil)
- **Aktuelle Arbeit:** Dawarich Trip-Erkennung, ActualBudget Expense Table
- **Bekannte Issues:**
  - Homair Scraper: HTML-Struktur kann sich ändern → `homair_scraper.py` anpassen
  - Google Flights: SerpAPI Free Plan = 100 Suchen/Monat
  - Dawarich: Punkt-Format variiert je nach Version → `normalize_point()` in `dawarich.py`

### Neue Sprache hinzufügen

```bash
# 1. Neue Locale-Datei erstellen
cp frontend/locales/en.json frontend/locales/fr.json
# 2. Übersetzen
# 3. Button im Header hinzufügen (frontend/index.html, Suche: "lang-btn")
```

### Neuen Scraper hinzufügen

```bash
# 1. backend/my_scraper.py erstellen
# 2. backend/routes/my_route.py erstellen
# 3. In backend/main.py registrieren
# 4. DB-Tabellen in backend/database.py hinzufügen
```

---

## Future Roadmap / Post-v1.0

### 🎨 UX Polish
- Toast notifications mit Animation und Auto-dismiss
- Skeleton loaders für Datenabruf
- Loading spinners bei allen API-Calls

### ⚙️ Quality of Life
- **API Quota Tracking** — SerpAPI Anfragen-Zähler (100/Monat Free Plan)
- **Währungs-Toggle** — EUR / USD / GBP
- **CSV Export** — Preisverläufe als CSV herunterladen

### 🔔 Notifications
- **Telegram** — Push-Alerts bei Preisschwellen
- **Discord Webhooks** — Preisalarme in Discord-Channel
- **Gotify** — Self-hosted Push (Unraid-friendly)

### 🧭 In Progress
- Dawarich Debug-Endpoint zum Prüfen des Punkt-Formats
- ActualBudget Expense Table mit Kategorie-Filter

---

## Contributing

1. Fork → Feature Branch → Pull Request
2. Python: PEP 8, Type Hints
3. JS: Vanilla JS, keine Frameworks
4. i18n: Neue Strings immer in alle 3 Locale-Dateien

---

## License

**GNU Affero General Public License v3.0** — siehe [LICENSE](LICENSE).

> Self-hosting ist ausdrücklich erlaubt und erwünscht. Modifikationen müssen unter derselben Lizenz veröffentlicht werden.
