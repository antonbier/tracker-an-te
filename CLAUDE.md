# CLAUDE.md — WanderSuite AI Assistant Context (BETA branch)

**⚠️ You are on the `beta` branch.**
New features developed here. Tested → merged into `main`.

---

## Repository

**Repo:** `antonbier/tracker-an-te`
**Stack:** Svelte 5 + SvelteKit · FastAPI · SQLite · Docker Compose
**Unraid path:** `/mnt/user/appdata/wandersuite-beta/`

---

## Branch Strategy

| Branch | Purpose | Ports | Version |
|--------|---------|-------|---------|
| `main` | Stable, production | 8765 / 8766 | `1.0.0` |
| `beta` | New features, testing | 8767 / 8768 | `beta-YYYY-MM-DD HH:MM` |

---

## Deployment — Unraid (Beta)

```bash
# Initial setup
mkdir -p /mnt/user/appdata/wandersuite-beta
cd /mnt/user/appdata/wandersuite-beta
git clone https://github.com/antonbier/tracker-an-te .
git checkout beta
cp .env.example .env
nano .env
mkdir -p data

# Build + start
BUILD_DATE="$(date '+%Y-%m-%d %H:%M')" docker compose up -d --build

# Update
git pull && BUILD_DATE="$(date '+%Y-%m-%d %H:%M')" docker compose up -d --build
```

---

## Network Architecture

```
Internet
  |
  +-> Zoraxy Reverse Proxy (Unraid)
        |
        +-> Frontend :8767 (Nginx + Svelte SPA)
        |     +-> /api/* -> backend:8000 (internal Docker network)
        |
        +-> Backend :8768 (FastAPI -- Swagger, direct API access)
              WARNING: Backend NOT exposed externally via Zoraxy
              -> /api/* calls go through Nginx proxy on port 8767
```

**Backend URL:** Im Onboarding-Wizard die **frontend URL** eintragen.
`window.location.origin` wird automatisch vorausgefüllt.

---

## .env Configuration

```env
HOST_PORT=8767
BACKEND_PORT=8768
TZ=Europe/Rome
DATA_DIR=/mnt/user/appdata/wandersuite-beta/data
APP_SECRET=<generate: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# Authentication
AUTH_ENABLED=true
JWT_SECRET=<generate: python3 -c "import secrets; print(secrets.token_hex(32))">

# WebAuthn / Passkeys
WEBAUTHN_RP_ID=wandersuite.deinedomain.de
WEBAUTHN_RP_NAME=WanderSuite
WEBAUTHN_ORIGIN=https://wandersuite.deinedomain.de

# Notifications (User-level -- verschlüsselt pro User in DB)
# Nur zur Dokumentation in .env.example -- echte Werte via Settings-UI setzen.
# TELEGRAM_BOT_TOKEN=<Bot Token von @BotFather>
# TELEGRAM_CHAT_ID=<Chat-ID>
# GOTIFY_URL=<https://gotify.deine-domain.de>
# GOTIFY_APP_TOKEN=<App-Token aus Gotify>
```

---

## Auth System

### Status
- ✅ Password login (email + bcrypt)
- ✅ JWT tokens (30-day expiry)
- ✅ Setup screen (first admin account)
- ✅ Admin panel (create/delete users)
- ✅ Passkeys funktionieren hinter Zoraxy (Origin-Header auto-detection)

### Passkey — rp_id / Origin Logik (`backend/routes/passkey.py`)

`_get_rp(request)` Priorität:
1. **Env-Vars explizit gesetzt** (`WEBAUTHN_RP_ID != "localhost"`) -> direkt verwenden
2. **HTTP Origin-Header** (Browser sendet bei jedem POST) -> `hostname` als `rp_id`
3. **Fallback** -> localhost defaults

WARNING: Nie `x-forwarded-host` verwenden -- kann leer sein -> `"http://"` -> bug.

---

## i18n System

**Dateien:** `svelte/src/locales/de.json`, `en.json`, `it.json`
**Store:** `svelte/src/lib/i18n.js` -- reaktiver `t`-Store, `$t('key')` in Komponenten

Vollständig übersetzt (DE/EN/IT): Navigation, Settings, Dashboard, MyTrips,
PriceRadar (alle Labels + Formular-Felder), Discover, Onboarding, Login, Setup.

**Regel:** Immer alle 3 Locale-Dateien gleichzeitig updaten. Tabs nie hardcodiert --
immer `$derived([...])` mit `$t('key')`.

---

## PWA / Favicon

- `svelte/static/favicon.svg` -- oranges Rund-Rechteck (#D95D39) mit Kompassrose
- `svelte/static/manifest.webmanifest` -- PWA-Manifest (name, theme_color, icons)
- `svelte/static/icons/icon-192.png` + `icon-512.png` -- generiert mit Pillow
- `svelte/src/app.html` -- verlinkt favicon.svg + manifest

---

## Settings -- Mein Bereich (myspace Tab)

- Per-user Einstellungen: Dawarich, ActualBudget, Home-Koordinaten
- **Geocoding:** Ortsname eingeben + Klick -> Nominatim -> lat/lon automatisch befüllt
- **ActualBudget Dateiname:** Hilfetext + Schritt-für-Schritt im FieldGuide (Tab Reisen)

---

## MyTrips -- Architektur & UX

### Tab-Reihenfolge (strikt)
| # | ID | Label |
|---|----|-------|
| 1 | `overview` | Übersicht |
| 2 | `trips` | Geplante Reisen |
| 3 | `journal` | Reisechronik |
| 4 | `bucketlist` | Bucket List |

### Grid-Layout (Tabs 2-4)
`grid grid-cols-1 lg:grid-cols-3 gap-5`
- `lg:col-span-1` -- Formular / Aktionen (links, 1/3)
- `lg:col-span-2` -- Liste / Timeline (rechts, 2/3)

### Header-Elemente
- **Jahres-Switcher** -- zeigt genau 3 Jahre: `selectedYear-1 | selectedYear | selectedYear+1`
- **Badges** -- Geplant / Vergangen / Wunschziele / Gesamt (alle klickbar ausser gesamt)

### Donut-Chart (SVG/conic-gradient)
- Kein externes Chart-Package -- reines CSS `conic-gradient`
- Segmente: Vergangen (dunkelgrün #2d6a4f) | Geplant (hellgrün #86efac) | Verfügbar (grau) | Überschuss (rot)

### Reisechronik -- Sync-Reihenfolge
1. Jahresbudget
2. Manuell erfassen
3. Tipp-Banner
4. Dawarich Sync (mit force_full Checkbox)
5. ActualBudget Sync (mit Auto-Cost Button)

#### Soft-Delete (Dawarich-Trips)
- Löschen setzt `ignored=1` in DB (kein echter DELETE)
- `force_full=true` -> resettet alle `ignored=1` auf `ignored=0`
- Manuelle Trips: echter DELETE

#### Auto-Cost (ActualBudget -> Dawarich-Trips)
- `POST /api/trips/auto-cost` -- Datum-Overlap Tx -> Trips
- `auto_cost_txs` JSON gespeichert, Anzeige in Timeline mit Marker

---

## ScratchMap.svelte

**Props:** `journalTrips`, `plannedTrips`, `selectedYear`

**Marker-Typen & Farben:**
| Typ | Quelle | Farbe | Jahresfilter |
|-----|--------|-------|-------------|
| `visited` | journalTrips mit lat/lon | `#2d6a4f` grün | ja |
| `planned` | plannedTrips mit lat/lon | `#2563eb` blau | ja |
| `bucket` | `$bucketlist` mit lat/lon | `#c4622d` orange | nein |

**Import:** `jsvectormap` als npm-Dependency (kein CDN)
```js
import { default as jsVectorMap } from 'jsvectormap'
import 'jsvectormap/dist/maps/world.js'
```

---

## Backend API -- Vollständige Übersicht

### /api/trips (routes/trips.py)
| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/api/trips` | Alle Trips (dawarich + manual), pro User |
| POST | `/api/trips` | Manuellen Trip anlegen (`source=manual`) |
| PATCH | `/api/trips/{id}/cost` | Kosten updaten |
| DELETE | `/api/trips/{id}` | Trip löschen (soft für dawarich, hard für manual) |
| GET | `/api/trips/budget` | Budget nach Jahr |
| PUT | `/api/trips/budget` | Budget für Jahr setzen |

### /api/search (routes/search.py) -- NEU
| Method | Path | Beschreibung |
|--------|------|-------------|
| POST | `/api/search/flights` | Meta-Suche Flüge: alle Provider parallel |
| POST | `/api/search/hotels` | Meta-Suche Hotels: alle Provider parallel |
| POST | `/api/search/camping` | Meta-Suche Camping: alle Provider parallel |

### /api/prices (routes/prices.py)
| Method | Path | Beschreibung |
|--------|------|-------------|
| PUT | `/api/prices/wish/{table}/{id}` | Wunschpreis setzen |
| GET | `/api/prices/history/{type}/{id}` | Preisverlauf (limit=90) |

### /api/trackers (routes/trackers.py)
| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/api/trackers` | Alle aktiven Tracker des Users |
| POST | `/api/trackers` | Tracker aus Suchergebnis anlegen |
| DELETE | `/api/trackers/{id}` | Tracker löschen |

### /api/scheduler (routes/scheduler.py)
| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/api/scheduler/settings` | Einstellungen des Users |
| PUT | `/api/scheduler/settings` | Intervall + Notifications speichern |
| POST | `/api/scheduler/run` | Manueller Trigger |

### /api/settings / /api/settings/user
- Global (Admin): SerpAPI, Gemini, OpenAI, language
- Per-user: dawarich, actualbudget, home coords, Telegram (verschlüsselt), Gotify (verschlüsselt)

---

## PriceRadar -- Architektur (Meta-Suche Aggregator)

### Konzept: Live-Suche vs. Tracker-Speicherung (STRIKT GETRENNT)

```
Suchmaske (Kategorie-spezifisch)
    |
    v  POST /api/search/{category}
Backend Aggregator (async, alle Provider parallel)
    |
    +-- Provider A scraper (timeout, eigene Header)
    +-- Provider B scraper (timeout, eigene Header)
    +-- Provider C scraper (timeout, eigene Header)
    |
    v  gebündelte Ergebnisse
Frontend Ergebnisliste (Skeleton -> Chips-Filter -> Karten)
    |
    v  [ + Als Tracker speichern ] (expliziter User-Action)
POST /api/trackers  ->  Tracker-Karte in "Aktive Tracker"
```

**Regel:** Ein Klick auf "Suchen" erzeugt **keinen** Tracker. Erst der explizite
Button `[ + Als Tracker speichern ]` schreibt in die DB.

### 4 Haupt-Kategorien

| Kategorie | Icon | Provider | Status |
|-----------|------|----------|--------|
| Flüge | Flugzeug | Ryanair scraper, SerpAPI Google Flights | aktiv |
| Hotels | Hotel | SerpAPI Google Hotels, Booking.com scraper | aktiv |
| Camping | Zelt | SerpAPI Google Hotels (Homair-Query) | aktiv |
| Mietwagen | Auto | -- | Coming Soon |

### Suchmasken (kategoriespezifisch)

#### Flüge
- Abflug (IATA-Code, Autocomplete)
- Ziel (IATA-Code, Autocomplete)
- Datum (Abflugdatum)
- Personen (Anzahl)
- Inklusivleistungen: Gepäck (Kein / 10kg / 20kg), Sitzplatz (Nein / Ja)

#### Hotels
- Ort/Stadt (Freitext, Autocomplete Ortsname)
- Check-In / Check-Out Datum
- Zimmer (Anzahl)
- Personen (Anzahl)

#### Camping
- Region/Ort (Freitext, Autocomplete Ortsname)
- Check-In / Check-Out Datum
- Personen (Anzahl)
- Unterkunftsart (Dropdown: Mobilheim / Glamping / Stellplatz)
- Schlafzimmer (Dropdown: 1 / 2 / 3+)
- Extras (Checkboxen): Klimaanlage / Hunde erlaubt / Überdachte Terrasse

#### Mietwagen
- Zeigt "Coming Soon" Badge -- kein Formular

### Autocomplete-Logik (schlank, lokal)
- Flughafen-Felder: statische JSON-Liste (IATA-Codes + Städtenamen), lokales Filter
- Ortsfelder (Hotels/Camping): einfacher Freitext-Filter auf bekannte Destinationen
- **Kein externer API-Call für Autocomplete** -- alles clientseitig

### Frontend-Workflow (PriceRadar.svelte)
1. User wählt Kategorie (Tab: Flüge / Hotels / Camping / Mietwagen)
2. Suchmaske ausfüllen -> `[ Suchen ]`
3. **Lade-Skeletons** erscheinen (animate-pulse)
4. Ergebnisse kommen -> **Provider-Filter-Chips** (horizontal scrollbar)
5. Ergebniskarten mit `[ + Als Tracker speichern ]` Button
6. "Aktive Tracker" Sektion darunter -- zeigt gespeicherte Tracker

### Backend Aggregator -- Strategy Pattern

```python
# POST /api/search/flights
async def search_flights(params: FlightSearchParams, user=Depends(get_current_user)):
    tasks = [
        run_ryanair_search(params),       # eigener Timeout + Header
        run_google_flights_search(params) # eigener Timeout + Header
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Fällt Provider A aus -> Provider B unberührt
    return aggregate_results(results)
```

**Anti-Scraping & Robustheit:**
- Realistische Browser-Header pro Provider (User-Agent, Accept-Language, Referer)
- `httpx.AsyncClient` mit `timeout=15.0` pro Provider
- `return_exceptions=True` -> Exception eines Providers bricht andere nicht ab
- Jeder Provider-Aufruf wrapped in `try/except` mit Logging

**Deep-Logging Format:**
```
[RYANAIR]   #search status=ok | found=12 | cheapest=49.99 EUR
[RYANAIR]   #search status=blocked_by_cf | error=403
[SERPAPI]   #search status=ok | found=8 | source=google_flights
[HOMAIR]    #search status=timeout | elapsed=15.1s
```

### Aktive Tracker -- UX & Responsive Design

#### Grid-Layout
```
grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4
```

#### Tracker-Karte Aufbau
```
+-----------------------------------------+
| [Ziel erreicht!]           [Ryanair]    |  <- Badge + Provider
| Wien -> Barcelona  28. Jun  2 Pers.     |  <- Titel
| [1x 10kg] [Sitzplatz]                   |  <- Inklusiv-Badges
|                                         |
| Aktuell: 49,99 EUR   Wunsch: [89,00] ✏️ |  <- Preis + Inline-Edit
|                                         |
| [ Preisverlauf ]            [X Löschen] |  <- Buttons (weit voneinander)
|                                         |
| v SVG Liniendiagramm (Akkordeon)        |  <- bei Klick auf Preisverlauf
+-----------------------------------------+
```

#### Wunschpreis Inline-Edit
- Anzeige: Zahl + Stift-Icon (klickbar)
- Edit-Mode: `<input type="number">` + Bestätigen/Abbrechen Buttons
- `PUT /api/prices/wish/{table}/{id}` bei Bestätigung
- Grüner Border (`ring-2 ring-green-500`) + "Ziel erreicht!" Badge wenn `current_price <= wish_price`

#### Inklusiv-Badges (unter Titel)
```svelte
{#each tracker.inclusions as badge}
  <span class="badge">{badge}</span>
{/each}
```
Beispiele: "1x 10kg", "Mobilheim", "Klimaanlage"

#### Preisverlauf-Akkordeon (inline SVG)
- Klick auf Preisverlauf-Button -> `showChart = !showChart`
- `GET /api/prices/history/{type}/{id}?limit=90`
- SVG Liniendiagramm: Min/Max Labels, Tooltips per hover
- Öffnet **innerhalb** der Karte (kein Modal, kein neues Panel)

#### Button-Sicherheit
- Preisverlauf-Button -- links (primäre Aktion)
- Löschen-Button -- rechts, `ml-auto`, Abstand >= 8px zu anderen Buttons

---

## Datenbank -- Schema

### price_history
```sql
CREATE TABLE price_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL DEFAULT 1,
    tracker_type TEXT    NOT NULL,   -- 'flight'|'google_flight'|'hotel'|'camping'
    tracker_id   INTEGER NOT NULL,
    price        REAL    NOT NULL,
    currency     TEXT    NOT NULL DEFAULT 'EUR',
    provider     TEXT,               -- 'ryanair'|'google_flights'|'homair'|'booking'
    status       TEXT    NOT NULL DEFAULT 'ok',
    error_msg    TEXT,
    fetched_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_price_history_tracker ON price_history(tracker_type, tracker_id, user_id);
```

### user_scheduler_settings
```sql
CREATE TABLE user_scheduler_settings (
    user_id               INTEGER PRIMARY KEY,
    update_interval_hours INTEGER NOT NULL DEFAULT 24,
    notify_price_drop     INTEGER NOT NULL DEFAULT 1,
    notify_daily_summary  INTEGER NOT NULL DEFAULT 0,
    last_run_at           TEXT,
    updated_at            TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

### user_notification_settings (NEU -- verschlüsselte Felder)
```sql
CREATE TABLE user_notification_settings (
    user_id             INTEGER PRIMARY KEY,
    telegram_bot_token  TEXT DEFAULT NULL,   -- Fernet-verschlüsselt
    telegram_chat_id    TEXT DEFAULT NULL,   -- Fernet-verschlüsselt
    gotify_url          TEXT DEFAULT NULL,   -- Fernet-verschlüsselt
    gotify_app_token    TEXT DEFAULT NULL,   -- Fernet-verschlüsselt
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Verschlüsselung:** Alle 4 Felder via `cryptography.fernet.Fernet(APP_SECRET)`
symmetrisch verschlüsselt. Entschlüsselung nur im Backend, nie im Klartext ins Frontend.

### wish_price Spalte (Migration -- alle Tracker-Tabellen)
```sql
ALTER TABLE trackers         ADD COLUMN wish_price REAL DEFAULT NULL;
ALTER TABLE gf_trackers      ADD COLUMN wish_price REAL DEFAULT NULL;
ALTER TABLE homair_trackers  ADD COLUMN wish_price REAL DEFAULT NULL;
ALTER TABLE booking_trackers ADD COLUMN wish_price REAL DEFAULT NULL;
```

### Cleanup-Job (APScheduler)
```python
# Täglich 03:00 -- löscht Einträge älter als 60 Tage
DELETE FROM price_history WHERE fetched_at < datetime('now', '-60 days')
```
Funktion: `run_cleanup_job()` in `backend/scheduler.py`

---

## Sicherheitskonzept -- Verschlüsselte User-API-Keys

### Prinzip
User-spezifische Credentials (Telegram Bot Token, Chat ID, Gotify URL + Token)
werden **niemals im Klartext** in der DB gespeichert.

### Implementierung
```python
from cryptography.fernet import Fernet
import os

def get_fernet():
    key = os.environ["APP_SECRET"]
    return Fernet(key.encode() if isinstance(key, str) else key)

def encrypt(value: str) -> str:
    return get_fernet().encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return get_fernet().decrypt(value.encode()).decode()
```

- `APP_SECRET` = Fernet-kompatibler 32-Byte URL-safe Base64-Key
- Gleicher `APP_SECRET` wie für bestehende Settings-Verschlüsselung

### Was wird verschlüsselt
| Feld | Tabelle | Wer sieht Klartext |
|------|---------|-------------------|
| `telegram_bot_token` | `user_notification_settings` | Nur Backend beim Senden |
| `telegram_chat_id` | `user_notification_settings` | Nur Backend beim Senden |
| `gotify_url` | `user_notification_settings` | Nur Backend beim Senden |
| `gotify_app_token` | `user_notification_settings` | Nur Backend beim Senden |

Frontend erhält immer nur maskierte Strings (z.B. "••••••••" oder leeren String).

---

## Benachrichtigungs-Engine (erweiterbar)

```python
# backend/notifications.py

class NotificationProvider:
    async def send(self, user_id: int, title: str, message: str): ...

class TelegramProvider(NotificationProvider):
    async def send(self, user_id, title, message):
        # Decrypt credentials, POST to Telegram Bot API
        pass

class GotifyProvider(NotificationProvider):
    async def send(self, user_id, title, message):
        # Decrypt credentials, POST to Gotify /message
        pass

async def notify_user(user_id: int, title: str, message: str):
    # Versucht alle konfigurierten Provider
    # Fehler eines Providers stoppt andere nicht
    providers = await get_configured_providers(user_id)
    results = await asyncio.gather(
        *[p.send(user_id, title, message) for p in providers],
        return_exceptions=True
    )
```

**Trigger-Events:**
- Preis <= Wunschpreis eines Trackers -> `notify_user(...)` nach jedem Scheduler-Lauf
- (Future) Tägliche Zusammenfassung

---

## Multi-User Architecture

### Data Isolation
| Table | Scope | Notes |
|-------|-------|-------|
| `trackers` | Per-user | `user_id` column |
| `gf_trackers` | Per-user | |
| `homair_trackers` | Per-user | |
| `booking_trackers` | Per-user | |
| `price_history` | Per-user | `user_id` column |
| `user_scheduler_settings` | Per-user | PK = user_id |
| `user_notification_settings` | Per-user | PK = user_id, verschlüsselt |
| `detected_trips` | Per-user | Dawarich + manual |
| `user_data` | Per-user | ws-trips, ws-bucketlist, ws-budget-years |
| `user_settings` | Per-user | dawarich, actualbudget, home coords |
| `settings` | Global (admin) | SerpAPI, Gemini, OpenAI, language |
| `webauthn_credentials` | Per-user | passkeys |

### AUTH_ENABLED=false (guest mode)
- Returns `GUEST_USER = {id: 0, role: "admin"}`
- Fully backward compatible

---

## Security Headers (nginx.conf)

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self' ...`
- `Cross-Origin-Resource-Policy: same-origin`
- `Cross-Origin-Opener-Policy: same-origin` (required for WebAuthn)

**TODO -- set in Zoraxy:**
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`

---

## File Structure

```
wandersuite/
+-- svelte/src/
|   +-- lib/
|   |   +-- stores.js
|   |   +-- api.js
|   |   +-- i18n.js
|   |   +-- components/
|   |       +-- AppShell.svelte
|   |       +-- Header.svelte
|   |       +-- Sidebar.svelte
|   |       +-- Login.svelte
|   |       +-- Setup.svelte
|   |       +-- Settings.svelte
|   |       +-- PasskeyManager.svelte
|   |       +-- FieldGuide.svelte
|   |       +-- ScratchMap.svelte
|   |       +-- pages/
|   |           +-- Dashboard.svelte
|   |           +-- PriceRadar.svelte   <- Meta-Suche Aggregator, 4 Kategorien
|   |           +-- MyTrips.svelte
|   |           +-- Discover.svelte
|   +-- locales/
|   |   +-- de.json
|   |   +-- en.json
|   |   +-- it.json
|   +-- routes/
|       +-- +layout.svelte
|       +-- +page.svelte
+-- svelte/static/
|   +-- favicon.svg
|   +-- manifest.webmanifest
|   +-- icons/icon-192.png, icon-512.png
+-- backend/
|   +-- main.py
|   +-- database.py
|   +-- auth_db.py
|   +-- auth_jwt.py
|   +-- settings_manager.py
|   +-- notifications.py            <- NEU: Telegram + Gotify Engine
|   +-- actual_budget.py
|   +-- dawarich.py
|   +-- scheduler.py                <- APScheduler + Cleanup-Job (60 Tage)
|   +-- routes/
|       +-- auth.py
|       +-- passkey.py
|       +-- settings.py
|       +-- trips.py
|       +-- budget.py
|       +-- trackers.py             <- unified tracker CRUD
|       +-- search.py               <- NEU: /api/search/* Aggregator
|       +-- prices.py               <- wish_price + history
|       +-- scheduler.py            <- /api/scheduler/* endpoints
|       +-- google_flights.py
|       +-- accommodations.py
|       +-- userdata.py
|       +-- dawarich.py
+-- docker/
|   +-- Dockerfile
|   +-- Dockerfile.frontend
|   +-- nginx.conf
+-- docker-compose.yml
```

---

## GitHub API Workflow (Claude's method)
Always fetch SHA before writing. Work on `beta` branch.
```python
# GET SHA
url = f'https://api.github.com/repos/{REPO}/contents/{path}?ref=beta'
# PUT to update
body = {'message': msg, 'content': base64_content, 'branch': 'beta', 'sha': sha}
```

---

## Bekannte Quirks & Fallen

### ActualBudget
- Frontend sendet `actual_url`/`actual_token`/`actual_file` -- Backend `/actual/transactions` mappt diese
- Wenn `actual_file` leer -> erste verfügbare Datei wird automatisch verwendet

### jsvectormap
- `jsvectormap` aus `node_modules` (npm, kein CDN)
- `import { default as jsVectorMap } from 'jsvectormap'`

### Svelte 5 / $derived
- `$derived(() => { ... })` gibt eine Funktion zurück -> im Template mit `()` aufrufen
- `$state` Arrays/Objects: immer neu zuweisen statt mutieren

---


---

## Step 1 RC (Session 2025-04-08) — Bugfixing, API/DB-Sync, Deeplinks, Lokalisierung

### 1. API-Keys DB-Sync
- `serpapi_key`, `openai_key`, `gemini_key` werden jetzt serverseitig in `settings`-Tabelle gespeichert
- `Settings.svelte`: beim Öffnen werden API-Keys aus DB geladen (nicht mehr aus localStorage)
  — wichtig damit der Background-Scheduler die Keys findet
- Beim Speichern: Keys werden mit `••••••••` maskiert — nur echte Werte (kein ••••) gehen an die API

### 2. Geocoding Fix (CORS-Proxy)
- Nominatim direkt im Browser → CORS-Fehler auf HTTPS-Seiten
- Fix: `GET /api/settings/geocode?q=...` Backend-Proxy Endpoint in `routes/settings.py`
- `geocodeHome()` in Settings.svelte nutzt jetzt `api('/api/settings/geocode?q=...')` statt direkten fetch

### 3. Lokalisierung (Timezone & Datumsformat)
- `settings_manager.py`: `date_format` als GLOBAL_KEY; `timezone` + `date_format` auch als USER_KEYS (per-user Override)
- `routes/settings.py`: `GlobalSettingsPayload` + `UserSettingsPayload` um `timezone`/`date_format` erweitert
- `Settings.svelte` Allgemein-Tab: Timezone-Dropdown (13 Zonen) + Datumsformat-Buttons (DD.MM.YYYY | MM/DD/YYYY | YYYY-MM-DD)
- `routes/scheduler.py`: `last_run_at` wird timezone-aware formatiert (User-TZ → Global-TZ → UTC)

### 4. Buchungs-Links (Deeplinks)
- `database.py`: Migration `booking_url TEXT DEFAULT NULL` für alle 4 Tracker-Tabellen
- `routes/search.py`: `booking_url` in jedem Suchergebnis-Objekt:
  - Ryanair → `https://www.ryanair.com/de/de/buchen/fluge-finden?...` mit Origin/Dest/Datum
  - Google Flights → `https://www.google.com/flights#search;f=...;t=...;d=...`
  - Hotels → SerpAPI `link`-Feld (direkt zur Unterkunft)
  - Camping → analog zu Hotels via SerpAPI `link`


---

## Step 2 RC (Session 2025-04-08) — Tracker UI, Charts & State Management

### Buchen-Button (Deeplinks)
- Tracker-Karten: `{#if tr.booking_url}` → `<a href=... target="_blank">Buchen ↗</a>` (orange accent)
- Suchergebnis-Karten: Button unter "Als Tracker speichern" — nur wenn `result.booking_url` vorhanden
- `booking_url` kommt aus DB (Step 1 Migration) resp. frisch aus der Suche

### "Alle aktualisieren" Button
- In `PriceRadar.svelte`: Header der Aktiven-Tracker-Sektion (nur wenn `allTrackers.length > 0`)
- `refreshAllTrackers()`: POST `/api/scheduler/run` → Backend verarbeitet im Hintergrund
- `isRefreshing` State: Button wechselt auf "⏳ Aktualisierung läuft…", nach 90s `loadAllTrackers()`
- Rate-Limit-sicher: Batching im Backend (Scheduler läuft seriell mit delays)

### Preisvergleich-Grafik verbessert
- `chartPts()` gibt jetzt `minPt` + `maxPt` zurück (koordinaten des Tiefst-/Höchstpreises)
- SVG: Grüner Punkt am Minimum, roter Punkt am Maximum
- Gestrichelte Referenzlinien (Y-Achse oben/unten) für bessere Lesbarkeit
- Y-Achse startet nicht mehr bei 0 — Preisbereich dynamisch (range = max - min)

### Datumsformat global angewendet
- `fmtDate(iso)` in PriceRadar liest `localStorage.getItem('ws-date-format')`
- Mögliche Werte: `DD.MM.YYYY` (default) | `MM/DD/YYYY` | `YYYY-MM-DD`
- Settings speichert `ws-date-format` bei globalem Save und per-User Save ins localStorage


---

## Step 3 RC (Session 2025-04-08) — Dashboard, Meine Reisen & UX-Polish

### Budget-Sync Dashboard ↔ MyTrips
- `Dashboard.svelte`: lädt `budgetByYear` aus `/api/trips/budget` via `loadBudget()`
- Zeigt immer aktuelles Jahr (`currentYear`), kein Jahreswechsler
- Inline-Budget-Eingabe direkt in der Budget-Übersicht-Card (Zahl + ✓ Button)
- `saveBudget()` PUT `/api/trips/budget` → identische Logik wie in MyTrips

### ScratchMap — Besuchte Pins + Geocoding Fix
- Besuchte Pins: War zuvor auf Trips mit `lat && lon` beschränkt → jetzt geocodet ScratchMap
  auch Trips ohne Koordinaten via Backend-Proxy (`/api/settings/geocode?q=`)
- Geocoding-Funktion: nutzt jetzt `$apiUrl + /api/settings/geocode` statt direkten Nominatim-
  fetch (CORS-safe, Rate-Limit 1.1s → 0.6s durch Backend-Caching)
- Year-Filter bleibt: nur Pins des `selectedYear` werden angezeigt

### Settings Overlay — Desktop Fullscreen (zentriert)
- War: `md:max-w-md` rechts angedockt (schneidet UI auf Desktop ab)
- Jetzt: `md:max-w-2xl md:inset-[5vh_auto] md:left-1/2 md:-translate-x-1/2` → zentriertes
  Overlay mit max 90vh Höhe, abgerundeten Ecken, overflow-hidden

### Dark Mode Fixes — MyTrips Chronik
- Alle `text-stone-700` → `color:var(--ws-text)` inline style
- Alle `text-stone-400` → `color:var(--ws-muted)` inline style
- `border-stone-100` → `border-color:var(--ws-border)` inline style
- Kostenbetrag Chronik: `text-stone-500` → `color:var(--ws-muted)`


---

## Step 3 RC (Session 2025-04-08) — Dashboard, Meine Reisen & UX-Polish

### Dashboard Budget-Card (Jahr-bewusst)
- `Dashboard.svelte`: neues `yearBudget`/`yearSpent`/`yearRemaining` — filtert `$trips` auf `currentYear`
- Donut zeigt % des aktuellen Jahresbudgets mit Prozent-Label in der Mitte
- Inline Budget-Edit: "✏️ Budget setzen" Button → Input-Zeile mit Enter-Confirm → PUT `/api/trips/budget`
- Synced mit MyTrips: beide lesen/schreiben `/api/trips/budget` API

### ScratchMap Geocoding (CORS-Fix)
- `ScratchMap.svelte`: `geocode()` nutzt jetzt `/api/settings/geocode?q=` Backend-Proxy statt direktem Nominatim
- Kein CORS-Fehler mehr auf HTTPS-Seiten
- Dark-Mode: Kartenregionen `fill` dynamisch — `'#2a2a2a'` im Dark-Mode, `'#e8ddd0'` im Light-Mode

### Settings Fullscreen (Desktop)
- `Settings.svelte`: `md:max-w-2xl` → `md:max-w-4xl` für zentriertes Fullscreen auf Desktop

### MyTrips Dark Mode (Global Fix)
- `MyTrips.svelte`: ~20 hardcodierte Tailwind-Farben auf CSS-Vars umgestellt
  - `text-stone-400` → `style="color:var(--ws-muted)"`
  - `bg-white` → `style="background:var(--ws-surface)"`
  - `border-stone-200` → `style="border-color:var(--ws-border)"`
  - Timeline-Dot `border-white` → `border-color:var(--ws-surface)`
  - Manuell-Badge `bg-indigo-100 text-indigo-600` → rgba mit CSS-var


---

## Step 3 RC (Session 2025-04-08) — Dashboard, Meine Reisen & UX-Polish

### Dark Mode Fixes (MyTrips.svelte)
- Jahr-Switcher: `bg-white`/`border-stone-200` → `var(--ws-surface)`/`var(--ws-border)`
- Pfeil-Buttons: `text-stone-400` → `color:var(--ws-muted)`
- Jahres-Buttons: `border-stone-100` → `border-color:var(--ws-border)`, inaktiv → `color:var(--ws-muted)`
- Upcoming-Zähler-Badge: `bg-white border-stone-200 text-stone-400` → CSS-Vars
- ActualBudget-Sync-Button: `bg-white border-stone-200` → CSS-Vars
- Chronik-Eintrags-Texte: alle `text-stone-*` global durch CSS-Var-`style=` ersetzt via `re.sub`
- Summary-Badge-Chips: `bg-white border-stone-200` → `var(--ws-surface2)`

### Fullscreen Modals (Desktop)
- `Settings.svelte`: `md:inset-[4vh_auto] md:left-1/2 md:-translate-x-1/2 md:max-w-4xl md:max-h-[92vh]`
  → `md:inset-[5vh_10vw] md:rounded-2xl` — echtes zentriertes Overlay ohne Seitenpanel
- `FieldGuide.svelte`: `inset-y-0 right-0 max-w-lg` (Sidepanel)
  → `inset-0 md:inset-[5vh_10vw] md:rounded-2xl` — konsistent mit Settings

### Dashboard Budget
- Bleibt auf `currentYear` fixiert (kein Jahreswechsler auf Home)
- Inline-Budgetfeld bereits vorhanden — kein Patch nötig
- Budget-Sync mit MyTrips über gemeinsamen `/api/trips/budget` Endpoint

### Weltkarte Pins
- Bereits korrekt: `journalTrips` gefiltert nach `selectedYear` via `start_date.slice(0,4)`
- Geocoding via Backend-Proxy (Step 1), sessionStorage-Cache — kein Fix nötig


---

## Step 4 RC (Session 2025-04-08) — Settings Umzug & Kategorisierung

### Neue Sektionen in „Mein Bereich" (myspace Tab)
Direkt vor dem Speichern-Button in `Settings.svelte`:

**🔍 Such-Engines**
- SerpAPI Key — `bind:value={serpApiKey}` (dieselbe State-Variable wie `apis`-Tab)
- Erklärungs-Text + Link zu serpapi.com

**✨ Smart Assistant & Automatisierung**
- OpenAI Key — `bind:value={openaiKey}`
- Google Gemini Key — `bind:value={geminiKey}`
- Links zu platform.openai.com + aistudio.google.com

### Datenbindung
- Keys sind dieselben State-Variablen wie im globalen `apis`-Tab
- `saveUserSettings()` wurde erweitert: speichert API-Keys zusätzlich via `POST /api/settings`
  (da Keys global sind — werden vom Scheduler genutzt)
- Maskierung `'••••••••'` bleibt aktiv — nur echte Werte werden gesendet

### apis-Tab bleibt
- Der globale `apis`-Tab bleibt als Admin-Ansicht erhalten
- Myspace bietet Nutzern eine übersichtlichere Kategorisierung ihrer eigenen Keys

## Open / Next Steps

### Erledigt (bisherige Sessions)
- [x] Passkeys: rp_id auto-detection via Origin-Header
- [x] i18n: alle Bereiche DE/EN/IT vollständig
- [x] MyTrips: komplettes UX-Redesign (Tabs, Jahres-Switcher, Donut-Chart, Badges)
- [x] Soft-Delete: Dawarich-Trips (ignored=1)
- [x] Auto-Cost: ActualBudget -> Dawarich-Trips
- [x] ScratchMap: jsvectormap npm + 3 Marker-Typen
- [x] Price history chart (SVG) in PriceRadar
- [x] Wish-price inline edit + grüner Border
- [x] Scheduler: APScheduler + per-user settings
- [x] CLAUDE.md: PriceRadar auf neue Aggregator-Architektur dokumentiert (STEP 1)

### Roadmap (beta) -- PriceRadar Umbau
- [x] STEP 2: PriceRadar.svelte -- alte Tabs zerstört, neue Kategorie-Suchmasken (IATA-Autocomplete, Camping-Extras)
- [x] STEP 3: Backend /api/search/* Aggregator (httpx, asyncio.gather, anti-scraping headers, deep-logging)
- [x] STEP 4: Aktive Tracker UX (Responsive Grid 1/2/3, Inklusiv-Badges, saveAsTracker routing, latest_snapshot)
- [x] STEP 5: Backend Security (user_notification_settings verschluesselt, per-user Engine, Cleanup 60d)

### Phase 3 (future)
- [ ] Mietwagen-Tab (echte Provider)
- [ ] Discord webhook notifications
- [ ] Currency toggle (EUR/USD/GBP)
- [ ] Multi-user data separation fully tested
- [ ] Merge stable features to `main`

---

## Step 1 — Stabilisierung & Core-Bugfixes (abgeschlossen)

### Bug 1 — Mobile Auth (BottomNav)
- `BottomNav.svelte`: Neues "Mehr"-Tab öffnet ein Overlay über der BottomNav
- Overlay zeigt User-Avatar (Initial), E-Mail und Rolle aus `$currentUser`
- Logout-Button ruft `logout()` aus `stores.js` auf
- Einstellungs-Button delegiert an `onSettings` Prop (kommt von AppShell)
- `AppShell.svelte`: `onSettings` Prop jetzt an BottomNav weitergeleitet

### Bug 2 — /api/trips 500-Fehler
- `database.py`: `list_detected_trips()` hatte keinen `limit`-Parameter
- Route in `trips.py` übergab `limit=limit` → TypeError → 500
- Fix: `limit: int = 500` als Default-Parameter + `LIMIT ?` in SQL-Query

### Bug 3 — Geocoding (Nominatim)
- `Settings.svelte` → `geocodeHome()`: User-Agent Header hinzugefügt
  (`WanderSuite/1.0 (self-hosted travel tracker)`) — Nominatim blockiert
  Requests ohne User-Agent (HTTP 403/429)
- Koordinaten werden jetzt als reiner Float-String gespeichert (`String(parseFloat(...))`)
  ohne `toFixed()` um Grad-Zeichen oder Formatierung zu vermeiden
- Button liest `myHomeSearch.trim()` korrekt aus (war kein Binding-Problem,
  sondern fehlender User-Agent)

### Bug 4 — Scheduler Tab Blackscreen
- `Settings.svelte`: Der Scheduler-Inhalt war in einem syntaktisch falschen
  `{#if}...{:else if activeTab === 'scheduler'}` Block verschachtelt — dieser
  Block war nie erreichbar (falsche Svelte-Template-Logik)
- Fix: Scheduler-Tab als normaler `{:else if activeTab === 'scheduler'}` Block
  im Haupt-Tab-Switcher eingefügt (nach dem Admin-Tab)

### Bug 5 — Doppelter Speichern-Button (Mein Bereich)
- `Settings.svelte`: Footer-Speichern-Button wurde für den `myspace`-Tab
  fälschlicherweise angezeigt (fehlendes `myspace` in der Ausschlussbedingung)
- Fix: `activeTab !== 'myspace'` zur Footer-Button-Bedingung hinzugefügt
- Der `myspace`-Tab hat seinen eigenen inline Speichern-Button (korrekt)

### Bug 6 — MyTrips Dark Mode (weiße Statistik-Karten)
- `MyTrips.svelte`: `card`-Konstante war `bg-white border-stone-200` →
  im Dark Mode weiße Boxen
- Fix: `card` nutzt jetzt nur strukturelle Klassen, alle Farben via
  `style="background:var(--ws-surface);border-color:var(--ws-border)"`
- Alle 4 Statistik-Karten, Donut-Chart-Karte, Map-Karte und Preview-Karten
  haben explizite CSS-Variablen-Styles bekommen
- Donut-Loch: `bg-white` → `background:var(--ws-surface)`
- Text: `text-stone-*` → `color:var(--ws-text/muted)`

---

## Step 2 — Backend-Scraper & API-Reparatur (abgeschlossen)

### Google Flights — SerpAPI `type`-Parameter vertauscht
- `google_scraper.py` und `routes/search.py`: SerpAPI kodiert `type=1` = Round-trip,
  `type=2` = One-way — war **vertauscht** (One-way-Suchen wurden als Round-trip gesendet)
- Fix: `trip_type=1 if ret_date else 2` in `google_scraper.py`
- Fix: Gleiche Logik in `_search_google_flights()` in `search.py` (war bereits korrekt,
  nur Kommentar zur Klarheit hinzugefügt)

### Hotels & Camping — „No results found" Bug
- **Root cause**: `_search_hotels_serpapi()` und `_search_camping_serpapi()` extrahierten
  Preise nur aus `extracted_lowest` / `extracted_before_taxes_fees` (numerische Felder).
  SerpAPI liefert aber oft nur String-Felder wie `lowest: "€ 49"` oder `before_taxes_fees: "$ 99"`.
- Fix in `routes/search.py`: Neue `_extract_price()` Hilfsfunktion die alle bekannten
  SerpAPI Preisfelder durchsucht (numerisch + String via Regex) mit `total_rate` Fallback
- Fix in `booking_scraper.py`: Robuste Preis-Extraktion mit `total_rate` Fallback
  und Regex-Parsing für String-Preise
- Fix in `homair_scraper.py`: Gleiche robuste Extraktion für alle bekannten Felder

### Architektur-Anmerkung
- `routes/search.py` ist der Meta-Aggregator (Suche → mehrere Provider parallel)
- `google_scraper.py`, `booking_scraper.py`, `homair_scraper.py` sind die
  Einzel-Scraper für gespeicherte Tracker (Scheduler + manueller Scrape)
- Beide Ebenen wurden gepatcht

---

## Step 3 — Tracker UI & UX-Verfeinerung (abgeschlossen)

### S3-1: Dynamischer Tracker-Filter nach aktivem Tab
- `PriceRadar.svelte`: `allTrackers`-Liste wird jetzt nach `activeCategory` gefiltert
- Mapping: `flights` → `['flight', 'google_flight']`, `hotels` → `['hotel']`, `camping` → `['camping']`
- Neue `visibleTrackers` Variable (via `{@const}`) ersetzt direkte `allTrackers`-Referenz im Template
- Leerzustand zeigt kontextbezogene Meldung: z.B. „Keine Flug-Tracker — oben suchen und speichern!"
- Counter zeigt gefilterte + Gesamtzahl: „(2 / 5 gesamt)"

### S3-2: Fluglinie (Logo/Name) + Abflug-/Ankunftszeit
**Suchergebniskarten:**
- `{@const d = result.detail || {}}` extrahiert Detail-Felder
- Wenn `d.airline` vorhanden: Airline-Name mit ✈️-Icon + `departure_time → arrival_time` + Dauer
- Gilt für Google Flights Ergebnisse (Ryanair liefert keine Airline, nur Zeiten teilweise)

**Gespeicherte Tracker-Karten:**
- `trackerSubtitle()` ergänzt Airline + Zeiten aus `latest_snapshot`
- Zusätzliche Airline-Zeile direkt auf der Karte wenn `latest_snapshot.airline` vorhanden
- Format: ✈️ **Lufthansa** `09:35 → 12:10`

### S3-3: i18n Cleanup
- Neue Keys in alle 3 Sprachen (DE/EN/IT) hinzugefügt:
  `radarCurrentPrice`, `radarAirline`, `radarFlightTimes`, `radarFilterTab`
  `settingsSchedulerInterval`, `settingsSchedulerNotifications`,
  `settingsSchedulerPriceDrop`, `settingsSchedulerDaily`,
  `settingsSchedulerLastRun`, `settingsSchedulerRun`
- Hardcodierter String „Aktuell" in Tracker-Karte → `$t('radarCurrentPrice')`
- Alle bestehenden Radar-Labels (`radarInclusions`, `radarSeat`, etc.) waren bereits korrekt via `$t()`

---

## Step 4 — Suchmasken-Upgrade (abgeschlossen)

### S4-1: Personen-Split — Erwachsene + Kinder
- **Flüge**: `flAdults` + `flChildren` mit ±-Steppern (Erw. ab 12 J., Kinder 2–11 J.)
- **Hotels**: 3-spaltige Stepper-Gruppe: Erwachsene / Kinder / Zimmer
- **Camping**: 2-spaltiger Personen-Split: Erwachsene / Kinder (bis 17 J.)
- Backend: `children`-Feld in alle drei `SearchParams`-Modelle
- SerpAPI GF: `children`-Parameter wird an API übergeben

### S4-2: Gepäck-Anzahl-Stepper (Flüge)
- Drei Stepper-Reihen: **10 kg** (22,99 €), **20 kg** (34,99 €), **23 kg** (42,99 €)
- Anzahl je Klasse unabhängig wählbar (0–9 Koffer)
- Echtzeit-Preview: „🧳 Gepäck gesamt: X,XX €"
- Backend: `baggage_10kg`, `baggage_20kg`, `baggage_23kg` als Integer-Felder
- Preiskalkulation: `Anzahl × Koffer-Preis` (nicht mehr per Person)

### S4-3: Sitzplatz-Kalkulation (Flüge)
- Neues Feld: **Sitzplatz €/Person/Flug** mit ±-Stepper + manueller Eingabe
- Echtzeit-Preview: „💺 N Pers. × X € = Y €"
- Backend: `seat_cost: float` — Kalkulation: `(Flugpreis) + Gepäck + ((Erw + Kind) × Sitzplatz)`
- Legacy-Kompatibilität: `seat: bool` wird aus `seat_cost > 0` abgeleitet

### S4-4: Zeit- & Stopp-Filter (Flüge)
- **Stopp-Filter**: Toggle-Chips: Alle / Nonstop / Max 1 / Max 2
- **Zeitfenster** (in `<details>`-Akkordeon):
  - Abflug-Fenster: `ab HH:MM` + `bis HH:MM`
  - Ankunfts-Fenster: `ab HH:MM` + `bis HH:MM`
  - Reset-Button: setzt alle 4 Zeit-Felder auf leer
- Backend:
  - `max_stops: int` → SerpAPI `stops`-Parameter + clientseitiger Filter
  - `dep_from/dep_to/arr_from/arr_to: Optional[str]` → HH:MM-Vergleich
  - Ryanair: Post-Processing-Filter nach Abflugzeit
  - Google Flights: Filter pro Ergebnis vor dem Append

### Neue i18n-Keys (Step 4): 13 Keys je Sprache (DE/EN/IT)
`radarStops`, `radarNonstop`, `radarMaxStops1/2`, `radarTimeWindow`,
`radarDepWindow`, `radarArrWindow`, `radarTimeFrom/To`,
`radarResetFilter`, `radarBaggage23`, `radarExtrasPreview`

### Architektur-Änderung `routes/search.py`
- `FlightSearchParams` hat jetzt 14 Felder (war 6)
- `_extract_price()` Hilfsfunktion (Step 2) bleibt unverändert
- Rückwärtskompatibilität: Legacy-Felder `baggage: str` + `seat: bool`
  werden weiter akzeptiert und korrekt verarbeitet


---

## Step 1 (Session 2025-04) — Tracker-Datenpersistenz Bugfix

### Problem
Beim Speichern eines Suchergebnisses als Tracker gingen essenzielle Metadaten verloren.

### Fixes

#### Backend — database.py
- **Migration**: `homair_trackers` + `campsite_name TEXT DEFAULT NULL` Spalte
- **Migration**: `booking_trackers` + `hotel_name TEXT DEFAULT NULL` Spalte
- **Migration**: `gf_trackers` + `seat_cost REAL NOT NULL DEFAULT 0` Spalte
- **Migration**: `gf_trackers` + `baggage_json TEXT NOT NULL DEFAULT '[]'` Spalte
- `create_homair_tracker()`: speichert jetzt `campsite_name`
- `create_booking_tracker()`: speichert jetzt `hotel_name`
- `create_gf_tracker()`: speichert jetzt `seat_cost` + `baggage_json` (dict mit baggage/10kg/20kg/23kg)

#### Backend — accommodations.py
- `HomairCreate`: neue optionale Felder `campsite_name` + `initial_price`
- `BookingCreate`: neue optionale Felder `hotel_name` + `initial_price`
- Nach `create_*_tracker()`: wenn `initial_price` übergeben → sofort ersten Snapshot speichern
  (damit Tracker-Karte direkt nach dem Speichern einen Preis zeigt)

#### Backend — google_flights.py
- `GFTrackerCreate`: neue Felder `baggage_10kg/20kg/23kg`, `seat_cost`
- Neue optionale Felder: `initial_price`, `initial_airline`, `initial_dep_time`, `initial_arr_time`, `initial_duration`
- Nach `create_gf_tracker()`: wenn `initial_price` übergeben → sofort ersten `gf_snapshot` speichern

#### Backend — search.py
- Ryanair `detail`-Objekt enthält jetzt: `children`, `baggage_10kg`, `baggage_20kg`, `baggage_23kg`, `seat_cost`
  (waren zuvor missing → `saveAsTracker` konnte diese nicht korrekt mappen)

#### Frontend — PriceRadar.svelte / saveAsTracker()
- **Ryanair**: Rekonstruiert `BaggageItem[]` aus `baggage_10kg/20kg/23kg` Stepper-Counts
  statt einfachem Legacy-String. `seat_cost` korrekt aus `d.seat_cost` gelesen.
- **Google Flights**: überträgt jetzt `baggage_10kg/20kg/23kg`, `seat_cost`, und alle
  Initial-Snapshot-Felder (`initial_airline`, `initial_dep_time`, etc.)
- **Camping**: überträgt `campsite_name` (aus `d.campsite_name || result.title`) + `initial_price`
- **Hotel**: überträgt `hotel_name` (aus `d.hotel_name || result.title`) + `initial_price`

#### Frontend — PriceRadar.svelte / trackerTitle()
- Hotel: zeigt `tr.hotel_name || tr.destination` statt nur `tr.destination`
- Camping: zeigt `tr.campsite_name || tr.region || tr.destination` statt nur `tr.region`

#### Frontend — PriceRadar.svelte / trackerBadges()
- **Ryanair** (`flight`): parst `baggage_json` (Array von BaggageItems) → zeigt `🎒 Nx 10kg` etc.
- **Google Flights** (`google_flight`): parst `baggage_json` (Objekt mit Counts) → zeigt Badges
- Beide: zeigt `💺 Sitz X€/P` wenn `seat_cost > 0`


---

## Step 2 (Session 2025-04) — Preis-Logik & Suchmasken-Felder

### Hotel & Camping Gesamtpreis (Backend — routes/search.py)
- Neue Hilfsfunktion `_calc_nights(checkin, checkout)` → berechnet Nächte aus ISO-Datums-Strings
- SerpAPI liefert Preise primär als **Rate pro Nacht** (`rate_per_night`) oder als Gesamtpreis (`total_rate`)
- Logik: wenn `rate_per_night` in Response-Keys UND kein `total_rate` → `total = rate × nights`
  sonst wird `raw_price` direkt als Gesamtpreis behandelt
- Result-Objekte enthalten jetzt: `price` (Gesamtpreis), `price_per_night` (Ø/Nacht), `nights`
- Subtitle zeigt `N Nächte` mit an
- Frontend Suchergebniskarte: Gesamtpreis groß (`price.toFixed(2) €`), darunter `Ø X.XX €/Nacht` (bei >1 Nacht)
- Tracker-Karte: berechnet Nächte reaktiv aus `checkin_date`/`checkout_date` → zeigt `Ø X.XX €/Nacht`

### Camping Endreinigung (Frontend + Backend)
- Neues State: `cpFinalClean = $state(false)` in PriceRadar.svelte
- Neue Checkbox in Extras-Liste: `radarFinalCleaning` (Key in allen 3 Locales)
- Backend `CampingSearchParams`: `final_cleaning: bool = False`
- Wird als Badge `🧹 Endreinigung` in Suchergebnissen angezeigt und im `detail`-Objekt weitergereicht
- Tracker-Speicherung: `final_cleaning` in Camping-Payload übergeben

### Camping Kategorie-Dropdown (dynamisch vorbereitet)
- State `cpAccomOptions = $state([...])` ersetzt hardcodierte `<option>`-Tags
- Dropdown rendert jetzt `{#each cpAccomOptions as opt}<option value={opt.value}>{opt.label}</option>{/each}`
- Initiale Werte: `Mobilheim (Standard)`, `Mobilheim (Premium)`, `Glamping`, `Stellplatz`
- `mobilheim-premium` als neuer Wert vorbereitet — Klassen können später aus API befüllt werden
- `accommodation_type` wird weiterhin als String ans Backend gesendet (kein Schema-Bruch)

### Gepäck-Stepper Preisfelder (Frontend — Flüge)
- Neue State-Vars: `fl10kgPrice`, `fl20kgPrice`, `fl23kgPrice` (Default: 0)
- Gepäck-Stepper-Zeile: Anzahl-Stepper (links) + freies Eingabefeld `€/Koffer` (rechts)
- Eingabefeld deaktiviert (opacity 0.4) wenn Anzahl = 0
- Zeilensumme rechts: `(Anzahl × Preis).toFixed(2) €` — nur wenn beide > 0
- `flBaggageCost` berechnet dynamisch aus User-Preisen statt fest codierten 22.99/34.99/42.99
- Neues i18n-Key: `radarFinalCleaning` in DE/EN/IT


---

## Step 3 (Session 2025-04) — Frontend UX & Error-Handling

### Mobile UX — Flugextras Akkordeon
- Gepäck-Stepper, Sitzplatz, Stopp-Filter, Zeitfenster-Filter in `<details>`-Element ausgelagert
- Summary: `🧳 Flugextras` + `aktiv`-Badge (orange) wenn irgendein Extra-Feld gesetzt ist
- Inhalt: selbe Felder wie bisher, jetzt im aufgeklappten `<div class="p-3 space-y-4">` Container
- Mobile: kompakte Suchmaske (nur Origin/Dest/Datum/Personen sichtbar)

### Flugzeiten-Format Fix (Backend — routes/search.py)
- SerpAPI Google Flights liefert `departure_airport.time` als `"2026-05-05 08:15"` (Datetime-String)
- Bisher: `dep_t[:5]` → `"2026-"` (falsches Format!)
- Fix: `dep_t = _dep_raw[-5:]` — letzten 5 Zeichen = immer `HH:MM`
- Betrifft: `dep_t`, `arr_t` im Google-Flights-Provider und damit `subtitle` + `detail`-Objekt

### Text-Glitch Fix — doppeltes Label Sitzplatz
- `radarSeat` locale = `"Sitzplatz €/Person/Flug"` + Template hatte `— €/Person/Flug` hardcoded
- Fix: Label-Template auf `💺 {$t('radarSeat')}` gekürzt (kein doppelter Suffix mehr)

### Datum-Lokalisierung (Frontend — PriceRadar.svelte)
- Neue Hilfsfunktionen: `fmtDate(iso)` → `TT.MM.JJJJ`, `fmtRange(from, to)` → `TT.MM.JJJJ – TT.MM.JJJJ`
- `trackerSubtitle()`: Datumsangaben über `fmtDate()` lokalisiert
- Suchergebnis-Subtitle: JavaScript `.replace(/(\d{4})-(\d{2})-(\d{2})/g, ...)` konvertiert ISO-Dates inline
- `fetched_at` auf Tracker-Karten und Chart-Achse: `fmtDate()` statt `.slice(0, 10)`
- Kein US-Format mehr sichtbar im Frontend

### API-Key Error Handling
**Backend (search.py):**
- `_aggregate()` gibt jetzt Tuple `(results, missing_keys)` zurück
- Google Flights ohne Key: gibt Sentinel `{"_api_key_missing": True, "provider": "..."}` zurück
- Hotels/Camping ohne Key: `HTTPException(422, detail={"error": "missing_api_key", ...})`
- Response enthält `missing_api_keys: string[]` Liste

**Frontend (api.js):**
- `api()` parst jetzt JSON-Body bei Fehlern: `err.detail = errBody?.detail`
- Strukturierte Fehler (FastAPI 422) werden als Objekt weitergegeben, nicht als String

**Frontend (PriceRadar.svelte):**
- Nach Suche: wenn `res.missing_api_keys.length > 0` → roter Toast mit Providernamen
- Im catch-Block: `e.detail?.error === 'missing_api_key'` → `⚠️ API Key für X fehlt...`

### Preis-Trends & Top-Preis Badge (Frontend — PriceRadar.svelte)
- `priceTrend(history)` → `{dir: 'up'|'down'|'equal', pct: string}` aus letzten 2 Einträgen
- `isTopPrice(history, currentPrice)` → `true` wenn aktueller Preis ≤ historischem Minimum
- Tracker-Karte Preis-Row: Trend-Pfeil `⬇ X.X%` (grün) / `⬆ X.X%` (rot) — sichtbar wenn chart-History geladen
- Top-Preis Badge: `🏆 Top Preis` (gold/gelb) — erscheint wenn Preis = historisches Allzeit-Tief
- Daten-Basis: `chartState[cKey].history` — wird beim Öffnen des Preisverlauf-Akkordeons geladen
  → Trend/Badge erscheinen **nach erstem Klick auf Preisverlauf** (lazy load)

---

## Phase 2 Step 1 (Session 2025-04) — Scraper-Reparatur & Preis-Mathematik

### Ryanair Zeiten-Fix (search.py + scraper.py + database.py)

**Ursache:** `timeUTC`-Array von Ryanair enthält abhängig von API-Version entweder
`["HH:MM", "HH:MM"]` (lokale Zeit) oder `["2026-05-05T06:15:00.000Z", "..."]` (ISO).
Alter Code: `seg.get("timeUTC", [""])[0][:5]` → bei ISO-Format = `"2026-"` (falsch).
Ankunftszeit (`timeUTC[1]`) wurde gar nicht extrahiert.

**Fix — `_hhmm(ts_list, idx)` Hilfsfunktion:**
- `raw[-8:][:5]` funktioniert für **beide** Formate:
  - `"06:15"` → `[-8:] = "06:15"` → `[:5] = "06:15"` ✓
  - `"2026-05-05T06:15:00.000Z"` → `[-8:] = "6:15:00"` → hmm, besser:
  - Eigentlich: `raw[-14:-9]` oder einfacher: Split auf `T` falls ISO
- Implementiert als: `raw[-8:][:5]` + Validierung `":" in extracted`
- Abflug = `timeUTC[0]`, Ankunft = `timeUTC[1]`, Flugnummer = `flight.flightNumber`

**`backend/routes/search.py`:** Live-Suche (Suchergebniskarte)
- `dep_time`, `arr_time` korrekt extrahiert
- `detail.airline = "Ryanair"` ergänzt (konsistent mit GF)
- Subtitle zeigt `08:15 ✈ 10:50` wenn Zeiten verfügbar

**`backend/scraper.py`:** Scheduler-Scraper (gespeicherte Tracker)
- `_hhmm()` Hilfsfunktion hinzugefügt
- `_cheapest_flight()` gibt jetzt `departure_time`, `arrival_time` zurück
- `fetch_flights()` Snapshot-Dict enthält `departure_time` + `arrival_time`

**`backend/database.py`:**
- Migration: `price_snapshots` + `departure_time TEXT`, `arrival_time TEXT`, `flight_number TEXT`
- `save_price_snapshot()` speichert alle 3 neuen Felder

### Hotel & Camping Preis-Logik Fix (search.py)

**Ursache:** Fehlerhafte Heuristik `is_per_night`:
```python
# ALT (falsch):
is_per_night = "rate_per_night" in h.keys() and not ("total_rate" in h and h.get("total_rate"))
total_price = price_per_night * nights if is_per_night else raw_price
```
SerpAPI `rate_per_night` ist **per Definition** eine Nachtrate. Die Heuristik
konnte `is_per_night=False` liefern wenn `total_rate` ebenfalls vorhanden war,
was zu `total_price = raw_price` (nicht multipliziert) führte.

**Fix (Hotels + Camping):**
```python
# NEU (korrekt):
price_per_night = round(float(raw_price), 2)   # raw_price ist immer Nachtrate
total_price     = round(price_per_night * nights, 2)  # immer multiplizieren
per_night_avg   = price_per_night  # identisch, für konsistentes API-Format
```

---

## Phase 2 Step 2 (Session 2025-04) — UI-Layout, Akkordeons & Cleanup

### Flug-Akkordeons aufgeteilt (PriceRadar.svelte)
Ehemals ein `<details>` „🧳 Flugextras" → jetzt zwei separate:

**Akkordeon 1: „🧳 Gepäck & Sitzplätze"**
- Gepäck-Stepper 10/20/23kg mit Preisfeldern
- Sitzplatz €/Person/Flug
- `aktiv`-Badge wenn fl10kg/fl20kg/fl23kg > 0 oder flSeatCost > 0

**Akkordeon 2: „⏱️ Zeiten & Stopps"**
- Stopp-Filter (Alle/Nonstop/Max 1/Max 2)
- Abflug-Zeitfenster (ab/bis)
- Ankunft-Zeitfenster (ab/bis)
- Reset-Button setzt jetzt auch flMaxStops=-1 zurück
- `aktiv`-Badge wenn flMaxStops >= 0 oder Zeitfelder gesetzt

### CSS Clipping Fix — Suchergebnis-Karten
- **Problem**: Subtitle mit `truncate` + rechter Preisblock mit `shrink-0` → Text wurde auf < 50% Breite gequetscht
- **Fix**: `truncate` → `break-words leading-relaxed` auf Subtitle-Div
- Rechter Block: `shrink-0` → `flex-none` mit explizitem `min-width:90px; max-width:130px`
- Kein Text mehr abgeschnitten (z.B. „2 Pers." vollständig)

### Google Flights Tracker-Karten — Redundanz entfernt
- `trackerSubtitle()`: Airline + Zeiten entfernt (waren doppelt mit separater Airline-Zeile)
  → Subtitle zeigt jetzt nur: Datum · Erwachsene · Zimmer
- Separate Airline-Zeile (unter Subtitle): zeigt jetzt für **alle Flug-Typen** (Ryanair + GF)
  - ✈️ Airline-Name (wenn vorhanden)
  - Flugnummer als Code-Badge (z.B. `FR 1234`) — NEU für Ryanair
  - Abflug → Ankunft (HH:MM → HH:MM)
- Condition: `tr._type === 'flight' || tr._type === 'google_flight'`

### API Error Handling — bestätigt aktiv
- `api.js`: parst JSON-Body bei HTTP-Fehlern, gibt `err.detail` als Objekt weiter
- PriceRadar: 422 mit `detail.error === 'missing_api_key'` → roter Toast
- Hotels/Camping ohne SerpAPI-Key: `HTTPException(422)` → Frontend zeigt Alert
- Flights ohne SerpAPI-Key: `missing_api_keys` in Response → Toast nach Suche

---

## Phase 3 Step 1 (Session 2025-04) — Scraper Time-Parsing & Flugnummern

### Root Cause: Kaputte Zeiten ":00.0 → :00.0"
Ryanair API liefert `seg.timeUTC` als ISO-Strings: `"2026-05-05T06:15:00.000Z"`.
Alter `_hhmm`-Code: `raw[-8:][:5]` → bei `.000Z`-Suffix = `":00.0"` (falsch).

**Zweites Problem:** `timeUTC` ist UTC, nicht lokale Abflugzeit. Für korrekte
Anzeige muss `seg.time` (lokale Ortszeit des Airports) verwendet werden.

### Fix: `_parse_local_time()` / `_parse_ryanair_time()` Hilfsfunktionen

Alle Scraper nutzen jetzt robuste Zeitextraktion:
```python
if "T" in s:            return s.split("T")[1][:5]   # ISO → "06:15"
if len(s) > 10 and " ": return s.split(" ")[1][:5]   # SerpAPI → "06:15"
else:                   return s[:5]                  # plain HH:MM
```

**Zeitzonen-Regel (strikt):** Flugzeiten werden IMMER als lokale Ortszeit behandelt.
Keine UTC→Lokal-Konvertierung im Backend. Browser-Zeitzone hat keinen Einfluss.
- Ryanair: `seg.time[0/1]` (lokal), Fallback: `seg.timeUTC[0/1]` (als lokal behandelt)
- SerpAPI: `departure_airport.time` / `arrival_airport.time` (lokale Flughafenzeit)

### Flugnummer-Normalisierung: `_fmt_flight_number()`
Ryanair gibt `flightNumber = "FR6125"` — wird jetzt zu `"FR 6125"` normalisiert.
```python
m = re.match(r"^([A-Z]{1,3})([0-9].*)$", raw)
return f"{m.group(1)} {m.group(2)}"  # "FR 6125"
```

### Geänderte Dateien
- `backend/scraper.py`: `_parse_local_time()` + `_fmt_flight_number()` ersetzt `_hhmm()`;
  `_cheapest_flight()` nutzt `seg.time` primär
- `backend/routes/search.py`: `_parse_ryanair_time()` + `_fmt_ryanair_flight_num()` als
  Top-Level-Funktionen; Inline-`_hhmm`-Closure entfernt
- `backend/google_scraper.py`: `_parse_serpapi_time()` + `_fmt_flight_number()` normalisieren
  SerpAPI-Zeiten und Flugnummern

---

## Phase 3 Step 2 (Session 2025-04) — Tracker UI & Suchergebnisse

### GF Doppel-Anzeige bereinigt (Suchergebnis-Karten)
**Problem:** GF subtitle = `"2026-05-05 · Lufthansa · 08:15→10:50"` + Body-Zeile zeigt
nochmal `✈️ Lufthansa 08:15 → 10:50`.

**Fix:** Subtitle wird für Flüge mit Airline dynamisch bereinigt:
```js
const cleanSubtitle = d.airline
  ? subtitle.replace(/·\s*[^·]+·\s*\d{2}:\d{2}→\d{2}:\d{2}/, '').trim()
  : subtitle;
```
Body-Zeile (Airline + Flugnummer + Zeiten) ist jetzt die **einzige** Quelle.
Flugnummer `d.flight_number` wird auch auf Suchergebnis-Karten angezeigt.

### Tracker-Karten Fluginfos (Aktive Tracker)
- `snap.airline`, `snap.flight_number`, `snap.departure_time`, `snap.arrival_time` zeigen korrekt
- Fallback auf `snap.outbound_flight` wenn `flight_number` leer
- Airline-Fallback: `"Ryanair"` / `"Google Flights"` wenn kein Snapshot-Airline
- Kein Snapshot vorhanden → `"✈️ Ryanair · noch kein Preis-Scan"` als Hinweis
- Dauer `(Xh Ym)` aus `snap.duration_min` ergänzt

### Provider-Label — echter Name statt "_type"
Neue Funktion `providerLabel(tr)`:
```js
'flight'        → 'Ryanair'
'google_flight' → 'Google Flights'
'hotel'         → 'Google Hotels' oder 'Booking.com'
'camping'       → 'Homair'
```
Ersetzt `tr._type.replace('_', ' ')` im Provider-Badge (oben links auf Tracker-Karte).

### Wunschpreis — prominente Fußzeile
**Vorher:** Eingequetscht als rechte Hälfte der Preis-Row (flex justify-between).
**Jetzt:** Eigener `<div>` mit Border direkt unter dem Preis-Block:
- Zeigt aktuellen Wunschpreis groß (`text-sm font-mono font-bold`)
- `✏️ setzen`-Button öffnet Inline-Edit mit `placeholder="Zielpreis in €"`
- Border-Farbe: `var(--ws-accent)` wenn Wunschpreis gesetzt, sonst `var(--ws-border)`
- Preis-Anzeige vergrößert auf `text-xl` für bessere Lesbarkeit

---

## Phase 3 Step 3 (Session 2025-04) — MyTrips Dark Mode & Kartenfilter

### ScratchMap.svelte — Jahresfilter für Visited-Pins
**Vorher:** `journalTrips.filter(t => t.lat && t.lon)` — alle Lifetime-Trips auf Karte.
**Jetzt:** Filtert auf `(t.start_date || '').slice(0, 4) === String(selectedYear)`.
Karte zeigt damit nur die Reisen des im Header ausgewählten Jahres.
Geplante Trips (planned) waren bereits jahresgefiltert — unverändert.
Bucket-Ziele: jahresunabhängig (immer sichtbar) — unverändert.

### ScratchMap.svelte — Dark Mode
Alle `bg-stone-50`/`bg-white/90`/`text-stone-*` → `var(--ws-surface)`/`var(--ws-muted)`/etc.:
- Outer container: `bg-stone-50 border-stone-200` → `var(--ws-surface2)` + `var(--ws-border)`
- Lade-Overlay: `bg-stone-50/90` → `color-mix(in srgb, var(--ws-surface2) 90%, transparent)`
- Geocoding-Overlay: `bg-white/90 border-stone-200 text-stone-500` → CSS-Variablen
- Fehler-Overlay: `bg-stone-50 text-stone-500` → CSS-Variablen
- Legende: `bg-white/90 border-stone-200 text-stone-600` → CSS-Variablen + `backdrop-filter:blur(4px)`

### MyTrips.svelte — Dark Mode Fixes

**Weltkarte-Titel + Counter:**
`text-stone-700` / `text-stone-400` → `var(--ws-text)` / `var(--ws-muted)`

**Donut-Legende:**
- Alle `text-stone-600/800/700/400` → `var(--ws-muted)` / `var(--ws-text)`
- `border-stone-100` → `var(--ws-border)`

**Smart Reise-Planer Teaser:**
- `from-orange-50 to-amber-50 border-orange-200` → `color-mix(in srgb, var(--ws-accent) 8%, var(--ws-surface))`
- Badge: `bg-orange-600 text-white` → `var(--ws-accent)` / `#fff5ec`
- Titel + Text: `text-stone-800/500` → CSS-Variablen

**Chronik + Reise-Titel:**
- Alle `font-bold text-stone-800` und `text-sm font-semibold text-stone-800` → `color:var(--ws-text)`
- `font-family:var(--ws-serif)` bleibt, Farbe über `style` gesetzt
- Bucketlist-Titel: `text-stone-800 pr-14` → CSS-Variable
- Kosten-Input in Chronik: `bg-stone-50 border-stone-200 text-stone-800` → CSS-Variablen

**Ergebnis:** 0 verbleibende `text-stone-800` Klassen in MyTrips.svelte.
---

## RC Step 1 (Session 2025-04-09) — Backend-Sicherheit, Scraper & globale Formate

### Fix 1 — SerpAPI Datenverlust verhindert (scheduler.py)
**Problem:** Bei API-Fehler oder scraper-Exception wurde `save_snapshot(tid, {"status": "error", ...})`
aufgerufen. Dieser Error-Snapshot wurde als neuester Eintrag in DB geschrieben → UI zeigte `-` als Preis.

**Fix:** Snapshots werden **nur noch bei `status == "ok"`** in die DB geschrieben.
Fehler → nur Log-Eintrag, letzter valider Preis bleibt vollständig erhalten.
Gilt für alle 4 Provider: Ryanair, Google Flights, Homair, Booking.

### Fix 2 — Ryanair Deeplink (routes/search.py)
**Problem:** URL `ryanair.com/de/de/buchen/fluge-finden?departureAirport=...` war veraltet → 404.

**Fix:** Neues URL-Format (pfadbasiert):
`https://www.ryanair.com/de/de/buchen/fluge-finden/{ORIGIN}/{DEST}/{DATE}/{ADULTS}/0/{CHILDREN}/0`

### Fix 3 — Globale Datums- & Zeitzonenformatierung (Frontend)
**Problem:** Scheduler-Tab zeigte `UTC` hardcodiert statt der tatsächlichen User-Zeitzone.
`fmtDate()` war nur lokal in PriceRadar definiert.

**Fix:**
- `Settings.svelte`: `schedTimezone` State aus `/api/scheduler/settings` geladen; Anzeige zeigt
  jetzt `{schedLastRun} {schedTimezone}` statt hardcodiertem `UTC`
- `svelte/src/lib/i18n.js`: `fmtDate(iso)` und `fmtDateRange(from, to)` als globale Exports
  → alle Komponenten können `import { fmtDate } from '$lib/i18n.js'` nutzen
  → liest `ws-date-format` aus localStorage (gesetzt in Settings: DD.MM.YYYY / MM/DD/YYYY / YYYY-MM-DD)
---

## RC Step 2 (Session 2025-04-09) — Settings, Dashboard UX & Weltkarte

### S2-1 — APIs-Tab entfernt (Settings.svelte)
- Tab `{ id: 'apis', label: 'APIs & KI' }` aus Hauptmenü-Liste entfernt
- Alle API-Key-Felder sind jetzt ausschliesslich unter **Mein Bereich** zugaenglich
- Backward-compat: Tab-State `apis` rendert implizit nichts mehr (kein 404)

### S2-2 — Top-Tabs in Mein Bereich (Settings.svelte)
- Neuer State: `myspaceTab = $state('integrations')`
- Horizontale 2er Tab-Nav im Mein-Bereich-Tab:
  - `🔍 Such-Engines` → SerpAPI Key + Link
  - `✨ Smart Assistant` → OpenAI Key + Gemini Key + Links
- Design: Pill-Nav mit `var(--ws-accent)` Aktiv-Highlighting, `var(--ws-surface2)` Container

### S2-3 — Alert-Hilfetexte Telegram & Gotify (Settings.svelte)
- **Telegram**: Info-Box mit Link zu @BotFather (Bot-Token) + getUpdates-Link (Chat-ID)
- **Gotify**: Info-Box mit Schritt-Beschreibung fuer App-Token-Generierung
- Style: `rgba(accent, .08)` Hintergrund, konsistent mit bestehenden Hilfe-Elementen

### S2-4 — Dashboard Jahresbudget primae Kachel (Dashboard.svelte)
- Budget-Eingabefeld nach **ganz oben** verschoben (erstes UI-Element)
- Neue prominente Kachel: "📅 Jahresbudget {currentYear}" + aktueller Wert + Eingabefeld
- Beschriftung: `placeholder="Budget fuer {currentYear} festlegen (€)"` — klar kommuniziert
- 3 Stats → 2 Stats (Tracker-Anzahl + Verfuegbar): Donut-Karte bleibt als Detailansicht
- Altes verstecktes Eingabefeld am Ende der Donut-Karte entfernt

### S2-5 — Weltkarte nur Dawarich GPS-Daten (ScratchMap.svelte)
- **Vorher**: journalTrips ohne lat/lon wurden via Nominatim geocodet (Netz-Request)
- **Nachher**: nur Trips mit echten `lat` + `lon` Koordinaten werden als Pin angezeigt
- Geplante Reisen (plannedTrips): komplett von Karte entfernt (`planned = []`)
- Bucket-Ziele: unveraendert (jahresunabhaengig, mit Geocoding)
- Jahresfilter bleibt: `.filter(t => t.start_date.slice(0,4) === selectedYear)`

