# WanderSuite — Kontext für Claude-Instanzen

Diese Datei gibt einer neuen Claude-Instanz den nötigen Kontext um direkt weiterzuarbeiten.

## Projekt-Überblick

WanderSuite ist eine self-hosted Travel Management Suite. Das Repo ist:
`https://github.com/antonbier/tracker-an-te`

## Aktueller Stand (März 2026)

### ✅ Implementiert und live
- Ryanair Tracker (Scraping, Gepäck, Sitzplatz, täglicher Scheduler)
- Google Flights Tracker (SerpAPI)
- Homair Camping Tracker (HTML-Scraping)
- Booking/Trivago Tracker (SerpAPI Google Hotels)
- KI-Reiseempfehlungen (Gemini 2.0 Flash + OpenAI gpt-4o-mini)
- Travel Budget (manuell + ActualBudget Sync)
- Reisetagebuch (Dawarich Trip-Erkennung via Haversine + Overnight-Algo)
- Dashboard (Budget-Donut, Tracker-Übersicht, Upcoming/Completed Trips)
- Field Guide (FAQ Modal)
- Onboarding (3-Schritt Setup-Wizard)
- Adventure Look (Terracotta/Playfair Display)
- Mehrsprachig DE/IT/EN (externe JSON Locale-Files)
- Docker/Unraid Deployment (Port 8765 Frontend, 8766 Backend)
- Verschlüsselte Settings (AES-Fernet in SQLite)

### 🔧 Bekannte offene Punkte
- Dawarich: `normalize_point()` in `dawarich.py` könnte je nach Dawarich-Version
  das Timestamp-Format nicht korrekt parsen → Debug-Endpoint `/api/dawarich/debug`
  hilft beim Prüfen des Roh-Formats
- ActualBudget: API nutzt Server-Passwort als Bearer Token
- Google Flights: SerpAPI Free Plan = 100 Suchen/Monat

## Deployment

**Unraid (Produktiv):**
```
Frontend: http://192.168.1.51:8765
Backend:  http://192.168.1.51:8766
```

Backend-URL im WanderSuite Dashboard (Einstellungen → Allgemein) auf
`http://192.168.1.51:8766` setzen — der Browser ruft die API direkt auf diesem Port auf.

**here.now (Frontend Preview):**
Automatisch via GitHub Action bei jedem Push auf `frontend/**`.
URL erscheint im Action-Log.

**Railway (Backend Preview):**
Automatisch via GitHub bei Push auf `main`.

## Wichtige Designentscheidungen

1. **Kein npm/Webpack** — reines Vanilla JS, kein Build-Step nötig
2. **SQLite** — einfach, persistent via Docker Volume `/data/tracker.db`
3. **Relative URLs** — `localStorage.getItem('apiUrl')` überall, kein hardcoded Host
4. **i18n** — externe JSON-Files in `frontend/locales/`, kein Framework
5. **Verschlüsselung** — AES-Fernet aus `APP_SECRET` Env-Variable abgeleitet

## Häufige Aufgaben

### Neue Sprache hinzufügen
1. `frontend/locales/xx.json` erstellen (Kopie von `en.json`)
2. In `index.html` Suche nach `lang-btn` → Button hinzufügen
3. In `setLang()` wird die Datei automatisch geladen

### Neuen Tracker-Typ hinzufügen
1. `backend/my_scraper.py` — Scraping-Logik
2. `backend/routes/my_route.py` — FastAPI Router
3. `backend/database.py` — Tabellen + CRUD Funktionen
4. `backend/main.py` — Router registrieren
5. `frontend/index.html` — Page HTML + JS

### Debugging
- Backend Logs: `docker compose logs backend -f`
- Swagger UI: `http://192.168.1.51:8766/docs`
- Dawarich Format prüfen: `POST /api/dawarich/debug`

## Tech Stack

| Komponente | Technologie |
|---|---|
| Frontend | Vanilla HTML/CSS/JS, Chart.js, Playfair Display + DM Sans |
| Backend | Python 3.12, FastAPI, APScheduler, SQLite |
| Scraping | requests, SerpAPI, Nominatim |
| AI | Google Gemini 2.0 Flash, OpenAI gpt-4o-mini |
| Crypto | cryptography (AES-Fernet) |
| Hosting | Docker + Nginx, Unraid |
