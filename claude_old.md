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
---

## RC Step 3 (Session 2025-04-09) — Tracker UI & Desktop Layout

### S3-1 — Buchen-Button in aktiven Tracker-Karten (PriceRadar.svelte)
**Vorher**: `Buchen ↗` Button nur in Suchergebnissen und versteckt in Action-Row unten.
**Nachher**: Button sitzt **prominent im Karten-Header** rechts neben Provider-Badge:
```
[✈️ Ryanair]              [🎯 Ziel erreicht!]  [Buchen ↗]
```
- Nur sichtbar wenn `tr.booking_url` vorhanden (analog Suchergebnisse)
- Style: `var(--ws-accent)` Background, `#fff5ec` Text — konsistent mit Rest
- Duplizierter Button aus Action-Row entfernt

### S3-2 — Desktop CSS-Grid fix (PriceRadar.svelte)
**Vorher**: Karten hatten `height:auto` → unterschiedliche Hoehen in einer Reihe.
**Nachher**: Sauberes gleichmaessiges Grid:
- Grid-Container: `items-stretch` hinzugefuegt
- Tracker-Karte: `h-full` hinzugefuegt
- Karten umbrechen synchron, gleiche Hoehe pro Zeile, gleiche Abstaende
- Layout: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-stretch`
---

## RC Step 4 (Session 2025-04-09) — i18n Refactoring

### S4-1 — Neue Locale-Keys (de.json / en.json / it.json)
10 neue Keys in allen 3 Sprachen:

| Key | DE | EN | IT |
|---|---|---|---|
| `radarBaggageSeat` | Gepäck & Sitzplätze | Baggage & Seats | Bagaglio & Posti |
| `radarTimesStops` | Zeiten & Stopps | Times & Stops | Orari & Scali |
| `radarRefreshAll` | Alle aktualisieren | Refresh all | Aggiorna tutto |
| `radarRefreshing` | Aktualisierung läuft… | Updating… | Aggiornamento… |
| `radarSet` | setzen | set | imposta |
| `radarAdultsShort` | Erw. | Ad. | Ad. |
| `radarSeatBadge` | 💺 Sitz {n}€/P | 💺 Seat {n}€/p | 💺 Posto {n}€/p |
| `radarPerNight` | €/Nacht | €/night | €/notte |
| `night` | Nacht | night | notte |
| `nights` | Nächte | nights | notti |

`radarSeatBadge` enthält `{n}` als Platzhalter → wird via `.replace('{n}', value)` befüllt.

### S4-2 — allLocales als named export (i18n.js)
`const allLocales` → `export const allLocales`
Ermöglicht dynamischen Zugriff auf verfügbare Sprachen ohne Duplizierung.

### S4-3 — Dynamischer Lang-Dropdown (Header.svelte)
- Import: `allLocales` aus `$lib/i18n.js` ergänzt
- Vorher: `{#each ['de','it','en'] as l}` — hardcodiertes Array
- Nachher: `{#each Object.keys(allLocales) as l}` — automatisch aus Locale-Map
- Neue Sprache hinzufügen: nur `de/en/it.json` Schema in neuem `xx.json` → `i18n.js` import → fertig

### S4-4 — PriceRadar.svelte: 9 hardcodierte Strings → $t()
- `'Sitz ' + n + '€/P'` → `$t('radarSeatBadge').replace('{n}', n)`
- `tr.adults + ' Erw.'` → `tr.adults + ' ' + $t('radarAdultsShort')`
- `` `💺 Sitz ${n}€/P` `` (2x) → `$t('radarSeatBadge').replace('{n}', n)`
- `🧳 Gepäck & Sitzplätze` → `$t('radarBaggageSeat')`
- `⏱️ Zeiten & Stopps` → `$t('radarTimesStops')`
- `€/Nacht` (2x, Suchergebnisse + Tracker) → `$t('radarPerNight')`
- `🔄 Alle aktualisieren` / `⏳ Aktualisierung läuft…` → `$t('radarRefreshAll')` / `$t('radarRefreshing')`
- `✏️ setzen` → `$t('radarSet')`

### S4-5 — Dashboard.svelte / MyTrips.svelte / Journal.svelte
- Dashboard: `'✓ setzen'` → `'✓ ' + $t('radarSet')`
- MyTrips + Journal: `trip.nights===1?'Nacht':'Nächte'` → `$t('night')`/`$t('nights')`
---

## RC Step 1 (Session 2025-04-09) — Backend Core, Scraper & Kritische Logik

### S1-1 — SerpAPI Datenverlust fix (Google Flights, Homair, Booking)
**Root Cause:** `routes/google_flights.py`, `routes/accommodations.py` — `/scrape` POST-Handler
riefen `save_*_snapshot()` **bedingungslos** auf, ohne `status` zu prüfen.
Bei API-Fehler (z.B. ungültiger Key, keine Ergebnisse) → `total_price=None` → NULL in DB → Preishistorie zerstört.

**Fix (alle 3 Scraper-Routen):**
```python
status = result.get("status", "error")
snap = result.get("snapshot", result)
if status == "ok" and snap.get("total_price") is not None:
    save_*_snapshot(tracker_id, snap)   # nur bei Erfolg
else:
    raise HTTPException(422, ...)        # kein DB-Write bei Fehler
```

### S1-2 — run_single_tracker Status Guard (scheduler.py)
**Root Cause:** `run_single_tracker()` rief `save_snapshot()` immer auf, unabhängig vom Ergebnis.
**Fix:** Status-Check vor `save_snapshot` — bei Fehler `ValueError` statt DB-Write.

### S1-3 — Ryanair Deeplink 404-Fix (routes/search.py)
**Root Cause:** Altes URL-Format `/de/de/buchen/fluge-finden/BGY/DUB/2026-05-09/1/0/0/0` → seit 2024 404.
**Fix:** Neue Hilfsfunktion `_ryanair_deeplink()` generiert korrektes 2025-Format:
```
https://www.ryanair.com/de/de/trip/flights/select?adults=1&dateOut=2026-05-09
  &originIata=BGY&destinationIata=DUB&tpAdults=1&...
```
Gültig für One-Way und Round-Trip.

### S1-4 — Scheduler Timezone-Anzeige (Settings.svelte)
**Root Cause:** `schedTimezone` im Template referenziert, aber nie als `$state` deklariert → `undefined`.
Das Backend in `routes/scheduler.py` lieferte `timezone` in der API-Antwort bereits korrekt.
**Fix:**
- `let schedTimezone = $state('UTC')` hinzugefügt
- `loadSchedulerSettings()` liest `s.timezone` und setzt `schedTimezone`
- `save()` persistiert `ws-timezone` zusätzlich zu `ws-date-format` in localStorage

### S1-5 — Timezone in localStorage (Settings.svelte)
`localStorage.setItem('ws-timezone', appTimezone)` in `save()` ergänzt.
Frontend-Komponenten können damit ohne Backend-Request die User-Timezone lesen.
---

## RC Step 2 (Session 2025-04-09) — Settings-Refactoring & Menü-Bugs

### S2-1 — Blockierte Tabs (Alerts/Scheduler) — `$derived` → `$derived.by()`
**Root Cause:** `const tabs = $derived([...])` — In Svelte 5 erzeugt ein Array-Literal
in `$derived` bei jedem reaktiven Update eine **neue Array-Referenz**. Das `{#each tabs}` Block
re-mountet dann alle Buttons neu → Event-Listener gehen verloren → Tabs nicht klickbar.
**Fix:** `const tabs = $derived.by(() => [...])` — `$derived.by()` cached die Funktion korrekt
und vermeidet unnötige Re-Mounts des `{#each}`-Blocks.

### S2-2 — Sub-Tab-Navigation "Mein Bereich" nach oben verschoben
**Vorher:** Sub-Tab-Buttons (`Such-Engines`, `Smart Assistant`) waren am Ende des myspace-Tabs,
nach den Dawarich/ActualBudget-Feldern.
**Nachher:** Sub-Tab-Leiste erscheint **direkt unter dem Tab-Header** von "Mein Bereich" —
als echte Tab-Navigation ganz oben, alle Inhalte darunter sind sub-tab-konditioniert.

### S2-3 — Neuer Sub-Tab "Lokale Anbindungen" (`connections`)
Dawarich und ActualBudget aus dem Fließtext herausgelöst und in eigenem Sub-Tab organisiert.
**Neue Sub-Tab-Struktur in "Mein Bereich":**
| Sub-Tab | Icon | Inhalt |
|---------|------|--------|
| `connections` | 🔌 | Dawarich (URL, Token, Heimatort) + ActualBudget (URL, PW, File, Kategorien) |
| `integrations` | 🔍 | SerpAPI Key (Such-Engines) |
| `ai` | ✨ | OpenAI Key + Google Gemini Key (Smart Assistant) |

Default-Sub-Tab ist jetzt `connections` (war: `integrations`).
---

## RC Step 3 (Session 2025-04-09) — Frontend UI & Tracker

### S3-1 — Buchen-Button auf Tracker-Karten (PriceRadar.svelte)
**Root Cause:** `tr.booking_url` ist in der DB als Spalte vorhanden (via ALTER TABLE Migration),
aber beim Erstellen von Trackern aus Suchergebnissen nicht persistiert. Gespeicherte Tracker
hatten daher immer `booking_url = null` → Button nie sichtbar.

**Fix:** Neue Hilfsfunktion `trackerBookingUrl(tr)` im Frontend:
1. Prüft zuerst `tr.booking_url` aus DB (falls gesetzt)
2. Fallback: berechnet Deep-Link aus Tracker-Feldern:
   - `flight` → Ryanair `/trip/flights/select?...` (selbes Format wie search.py)
   - `google_flight` → Google Flights `#search;f=...;t=...;d=...`
   - `hotel` → Google Travel Hotels mit Destination + Dates
   - `camping` → Homair Homepage (keine Deep-Link-Struktur bekannt)

Tracker-Karte: `{#if tr.booking_url}` → `{@const bookingUrl = trackerBookingUrl(tr)}` + `{#if bookingUrl}`

### S3-2 — Stopp-Badge mit Layover-Accordion (3 Dateien)
**database.py:** `stops INTEGER DEFAULT 0` Spalte zu `gf_snapshots` hinzugefügt
(CREATE TABLE + idempotente ALTER TABLE Migration + INSERT in `save_gf_snapshot`).

**google_scraper.py:** `_search_flight()` berechnet `stops = len(flights) - 1`
und `layover_airports = [leg.departure_airport.id for leg in flights[1:]]`.
Snapshot-Return enthält jetzt `stops` + `layover_airports`.

**PriceRadar.svelte:** Auf Tracker-Karten:
- `nStops > 0` → anklickbarer Badge `"N Stopp(s) ▾"` (blau)
- Click → verstecktes Div mit Layover-Airports (via, dann IATA-Codes) aufklappen
- `nStops === 0` + GF-Tracker → `"Nonstop"` Badge (grün)
- Ryanair: immer Nonstop (API gibt nur direkte Verbindungen zurück)

### S3-3 — ScratchMap Legende bereinigt (ScratchMap.svelte)
"Geplant" (blau) und "Wunschziel" (orange) aus der Legende entfernt.
Nur noch "Besucht" (grün) sichtbar — entspricht den tatsächlich gerenderten Pins
(planned-Array ist leer, bucket-Pins werden nicht mehr verwendet).
---

## RC Step 4 (Session 2025-04-09) — i18n Dynamischer Sprachumschalter

### S4-1 — ES-Locale aktiviert + localeLabels (i18n.js)
`es.json` war vorhanden aber nicht importiert. Jetzt vollständig eingebunden:
```js
import es from '../locales/es.json';
export const allLocales = { de, en, it, es };
export const localeLabels = { de: 'DE 🇩🇪', en: 'EN 🇬🇧', it: 'IT 🇮🇹', es: 'ES 🇪🇸' };
```
**Neue Sprache hinzufügen:** JSON-Datei in `svelte/src/locales/xx.json` anlegen →
in `i18n.js` importieren → zu `allLocales` + `localeLabels` hinzufügen → fertig.

### S4-2 — Dynamisches `<select>`-Dropdown (Header.svelte)
**Vorher:** Statische Button-Gruppe `{#each ['de','it','en'] as l}` — hardcodiert,
kein neues Locale ohne Code-Änderung in Header.svelte.
**Nachher:** `<select>` mit `{#each Object.keys(allLocales) as l}` — vollständig dynamisch:
```svelte
<select value={$lang} onchange={(e) => setLang(e.currentTarget.value)}>
  {#each availableLangs as l}
    <option value={l}>{localeLabels[l] ?? l.toUpperCase()}</option>
  {/each}
</select>
```
- Styled mit CSS `appearance:none` + Custom-Arrow via `background-image` SVG
- `localeLabels` liefert lesbare Labels mit Flaggen-Emoji
- Fallback: `l.toUpperCase()` falls Locale kein Label hat

---

## RC Release Candidate — Alle Steps abgeschlossen

### Gesamtübersicht aller Fixes (Session 2025-04-09)

| Step | Bereich | Fixes |
|------|---------|-------|
| S1 | Backend Core | SerpAPI Datenverlust (3 Routen), run_single_tracker, Ryanair Deeplink, schedTimezone |
| S2 | Settings UI | $derived.by() Tab-Fix, Sub-Tabs oben, neuer Tab Lokale Anbindungen |
| S3 | Frontend/Tracker | Buchen-Button, Stopp-Badge+Layover, Weltkarte Legende |
| S4 | i18n | ES-Locale, dynamisches Select-Dropdown |



---

## Technical Debt Abbau — Frontend Modularisierung (Session 2025-04-10)

### Ziel
Die drei größten Monolithen im Frontend wurden in saubere, modulare Svelte 5 Komponenten aufgeteilt.
**Goldene Regeln:** Zero Logic Change · Pure Svelte 5 Runes (`$props`, `$state`, `$derived`) · `$bindable` immer mit `let` · `$derived.by()` für mehrzeilige Blöcke.

---

### 1. PriceRadar.svelte Refactoring (1687 → ~165 Zeilen)

**Neue Dateistruktur:**
```
svelte/src/lib/components/
├── pages/PriceRadar.svelte                    ← Orchestrator (~165 Zeilen)
└── priceradar/
    ├── constants.js                           ← AIRPORTS, DESTINATIONS, CSS-Konstanten
    ├── helpers.js                             ← Pure Functions (fmtDate, chartPts, trackerTitle, etc.)
    ├── CategoryTabs.svelte                    ← Tab-Leiste (Flüge/Hotels/Camping/Mietwagen)
    ├── FlightSearchForm.svelte                ← Suchmaske Flüge inkl. Gepäck- & Zeit-Akkordeons
    ├── HotelSearchForm.svelte                 ← Suchmaske Hotels
    ├── CampingSearchForm.svelte               ← Suchmaske Camping
    ├── SearchResults.svelte                   ← Skeleton + Provider-Chips + Ergebnis-Karten
    ├── TrackerGrid.svelte                     ← Header + Grid + Leer-Zustand
    └── TrackerCard.svelte                     ← Einzelne Tracker-Karte inkl. Chart-Akkordeon
```

**Architektur-Entscheidungen:**
- `constants.js` + `helpers.js`: Reine JS-Exports, keine Svelte-Komponenten — ermöglicht Import in allen Sub-Komponenten ohne zirkuläre Abhängigkeiten.
- Formular-State (flOrigin, htCity, cpRegion etc.) lebt vollständig in den jeweiligen Form-Komponenten — kein Lift-Up nötig, da Payload per `onsearch(payload)`-Callback an Orchestrator gesendet wird.
- `chartState`, `wishState`, `stopsOpen` sind `$bindable` im Orchestrator und werden als gebundene Props an TrackerGrid/TrackerCard weitergegeben.
- `saveAsTracker()`, `loadAllTrackers()`, `deleteTracker()`, `scrapeTracker()`, `saveWishPrice()`, `toggleChart()`, `refreshAllTrackers()` — alle API-Calls bleiben im Orchestrator.

---

### 2. Settings.svelte Refactoring (1013 → ~230 Zeilen)

**Neue Dateistruktur:**
```
svelte/src/lib/components/
├── Settings.svelte                            ← Orchestrator (~230 Zeilen)
└── settings/
    ├── BasicTab.svelte                        ← Backend-URL, Theme, Timezone, Datumsformat
    ├── IntegrationsTab.svelte                 ← Dawarich + ActualBudget (global/Fallback)
    ├── NotificationsTab.svelte                ← Telegram + Gotify (inkl. Hilfe-Alerts)
    ├── MyspaceTab.svelte                      ← Mein Bereich Shell (Sub-Tab-Navigation)
    │   ├── MyspaceConnections.svelte          ← Dawarich + ActualBudget per-user + Geocoding
    │   ├── MyspaceProviders.svelte            ← Provider-Toggle-Liste + API-Key-Inputs
    │   └── MyspaceAI.svelte                   ← OpenAI + Gemini Keys
    ├── AccountTab.svelte                      ← Passwort ändern + PasskeyManager (self-contained)
    ├── AdminTab.svelte                        ← User-Liste + anlegen/löschen (self-contained)
    └── SchedulerTab.svelte                    ← Intervall + Notifications + Ausführen (self-contained)
```

**Architektur-Entscheidungen:**
- `AccountTab`, `AdminTab`, `SchedulerTab` sind vollständig self-contained: eigener `$state`, eigene API-Calls, kein shared State nötig. Nur `userId`/`currentUserId` als read-only Prop.
- Geteilte API-Key-State (`serpApiKey`, `openaiKey`, `geminiKey`) bleibt im Orchestrator, da er in `saveUserSettings()` UND `save()` gleichzeitig gebraucht wird.
- Tab-Array ist statisch (`TAB_IDS_*` Konstanten) — Labels werden via `$derived({...})` aus `$t()` aufgelöst. Kein `$derived.by()` mit Labels nötig (vermeidet Re-Mount-Bug durch neue Array-Referenz).
- `MyspaceConnections` verwaltet `myGeoLoading` + `myGeoResult` + `geocodeHome()` lokal — Geocoding-Callback braucht keinen Lift-Up.
- `providerKeys` ist ein `$state({})` Objekt im Orchestrator; `MyspaceProviders` nutzt `oninput`-Getter/Setter-Pattern (kein `bind:value` mit Zwei-Funktionen) für korrekte Svelte 5 Kompatibilität.

---

### 3. MyTrips.svelte Refactoring (917 → ~240 Zeilen)

**Neue Dateistruktur:**
```
svelte/src/lib/components/
├── pages/MyTrips.svelte                       ← Orchestrator (~240 Zeilen)
└── mytrips/
    ├── PageHeader.svelte                      ← Titel + Sync-Button + Jahr-Switcher + Badges + Tab-Leiste
    ├── OverviewTab.svelte                     ← Stats-Karten, Donut-Chart, ScratchMap, Previews
    ├── TripsTab.svelte                        ← Smart Planer Teaser, Formular, Upcoming/Past Listen
    ├── JournalTab.svelte                      ← Shell: Budget, Formular, Tipp, Sync-Karten, Timeline
    │   ├── JournalSyncDawarich.svelte         ← Sync-Karte 1 (Force-Full-Checkbox, self-contained)
    │   ├── JournalSyncActual.svelte           ← Sync-Karte 2 (Datei-Liste, Auto-Cost, self-contained)
    │   └── JournalTimeline.svelte             ← Timeline mit Kosten-Inline-Edit
    └── BucketListTab.svelte                   ← Formular + Grid der Wunschziele
```

**Architektur-Entscheidungen:**
- `donutGradient` bleibt als `$derived.by()` im Orchestrator (mehrzeilige Berechnung) und wird als fertiger String an `OverviewTab` übergeben — kein `BudgetDonut`-Split nötig.
- `editingCost` + `costDraft` im Orchestrator: `JournalTimeline` meldet via `oneditcost(id, draft)` + `oncanceledit()` zurück → Orchestrator setzt State → Props fließen zurück.
- `forceFull` ist `$bindable` zwischen Orchestrator und `JournalSyncDawarich`.
- `visibleYears` wird als fertiges Array-Prop an `PageHeader` übergeben (kein eigener `$derived` in PageHeader).
- CSS-Konstanten `inp`, `card`, `btn` werden als Props weitergegeben — keine Duplizierung in Sub-Komponenten.
- `TripsTab.onremovetrip(idx)` — Index bezieht sich auf `upcomingTrips`/`pastTrips` Array, nicht auf den globalen `$trips` Store. Orchestrator mappt zurück via `$trips.indexOf(tr)`.

---

### Svelte 5 Pitfalls — Gelernte Regeln

| Regel | Falsch | Richtig |
|-------|--------|---------|
| `$bindable` Destrukturierung | `const { x = $bindable() }` | `let { x = $bindable() }` |
| Mehrzeilige Derived-Blöcke | `$derived(() => { ... })` | `$derived.by(() => { ... })` |
| Input mit Getter/Setter | `bind:value={getter(), setter}` | `value={getter()} oninput={(e) => setter(e.target.value)}` |
| i18n reaktiv | `get(t)('key')` im Script | `$t('key')` im Template oder `$derived($t('key'))` |
| Tab-Array mit Labels | `$derived.by(() => [{label: $t(...)}])` | Statische IDs + `$derived({id: $t(...)})` für Labels |



---

## Discovery-Pipeline Refactoring (April 2026)

### Übersicht
Vollständiges Refactoring der Discovery-Pipeline zur Beseitigung von Technical Debt und Vorbereitung auf zukünftige Features.

### Neue Dateien

**`backend/discovery_models.py`** (neu)
Pydantic-Modelle zur strukturellen Trennung der Settings:
- `TravelPersonality` — steuert LLM-Prompt: `travel_style`, `climate_pref`, `landscape_pref`, `companions`, `wish_text`, `history_mode`, `travel_mode`, `max_travel_time`
- `TravelDefaults` — technische Reise-Parameter für Prefill: `home_airport`, `home_lat`, `home_lon`, `adults`, `children`, `unsplash_key`, `immich_url`, `immich_api_key`

### Geänderte Backend-Dateien

**`backend/database.py`**
- Neue Tabelle `discovery_pool` — persistenter Cache für KI-Vorschläge pro User (max. 200 Einträge, UNIQUE auf `user_id + destination`)
- Neue CRUD-Funktionen: `discovery_pool_get_unseen()`, `discovery_pool_upsert()`, `discovery_pool_mark_shown()`, `discovery_pool_rotate()`, `discovery_pool_clear()`, `discovery_pool_count()`
- Neue Migration-Keys: `travel_mode`, `max_travel_time`, `history_mode` in `user_settings`
- Konstanten: `DISCOVERY_POOL_MAX = 200`, `DISCOVERY_POOL_REFILL_THRESHOLD = 10`

**`backend/settings_manager.py`**
- `USER_KEYS` erweitert um: `travel_mode`, `max_travel_time`, `history_mode`

**`backend/discovery.py`** (vollständig refactored)
- `_load_prefs()` aufgespalten in `_load_personality() → TravelPersonality` und `_load_defaults() → TravelDefaults`
- `get_suggestions()` liest primär aus `discovery_pool` statt on-the-fly zu generieren; triggert `background_refresh_suggestions()` als `asyncio.create_task` wenn Pool < Threshold
- `background_refresh_suggestions()` — neuer Cronjob-Einstiegspunkt: LLM → `asyncio.gather` für parallele Bild-Anreicherung → Pool schreiben
- `_make_proxy_url()` — Proxy-URL-Erzeugung (`/api/discovery/image-proxy?url={quote(url, safe='')}`) jetzt in `_get_image()` statt in routes/; gilt für **beide** Quellen (Immich + Unsplash)
- `_build_prompt()` — neue Methode mit Smart History Toggle:
  - `history_mode=blacklist` → besuchte Orte werden ausgeschlossen
  - `history_mode=context` → besuchte Orte als KI-Inspiration für ähnliche, unbekannte Ziele
- `_build_prompt()` integriert `travel_mode` + `max_travel_time` in Prompt:
  - `travel_mode=car` → nur per Auto erreichbare Ziele
  - `travel_mode=flight` + `max_travel_time=Xh` → Flugzeit-Constraint
- Alle `httpx.AsyncClient`: `trust_env=False`, `timeout=25.0` (vorher: 20s, Immich fehlte `trust_env=False`)
- `_load_visited()` wird nicht mehr doppelt aufgerufen (war redundanter DB-Hit pro Suggestion)

**`backend/routes/discovery.py`**
- `_proxy_url()` Hilfsfunktion entfernt (Logik liegt jetzt in `discovery.py`)
- In-Memory-Cache (`_cache`) entfernt — Pool in SQLite ersetzt ihn
- Neuer Endpoint `POST /mark-shown` — Suggestion als gesehen markieren
- `GET /image-proxy` — jetzt user-scoped (liest `immich_url`/`immich_api_key` per `user_id` aus Settings statt hardcoded `user_id=1`); Unsplash-URLs explizit erlaubt (`images.unsplash.com`)
- `POST /refresh` — leert Pool via `discovery_pool_clear()` und befüllt neu

### Geänderte Frontend-Dateien

**`svelte/src/lib/components/settings/MyspaceDefaults.svelte`**
- Reisepersönlichkeit als eigenständiges Panel (strukturell getrennt von Reise-Defaults)
- Neue Props: `travelMode` (`$bindable`), `maxTravelTime` (`$bindable`), `historyMode` (`$bindable`)
- **Neuer Block „Reisemodus"**: Toggle Flugreise ✈️ / Autoreise 🚗 mit kontextsensitivem Hinweistext
- **Neuer Block „Max. Reisezeit"**: Buttons 2h / 4h / 8h / 12h / 12h+ / Egal; Label wechselt je nach `travelMode` zwischen „Flugzeit" und „Fahrzeit"
- **Neuer Block „Reisehistorie verwenden als"**: Toggle Ausschlussliste 🚫 / KI-Kontext 💡 mit erklärendem Hinweistext

**`svelte/src/lib/components/settings/MyspaceTab.svelte`**
- Neue Props: `travelMode`, `maxTravelTime`, `historyMode` als `$bindable`
- Props werden an `MyspaceDefaults` weitergereicht

**`svelte/src/lib/components/Settings.svelte`**
- Neue `$state`-Variablen: `travelMode` (default: `'flight'`), `maxTravelTime` (default: `'any'`), `historyMode` (default: `'blacklist'`)
- `loadUserSettings()`: lädt `us.travel_mode`, `us.max_travel_time`, `us.history_mode` aus API
- `saveUserSettings()`: schreibt alle drei in Payload (`payload.travel_mode`, `payload.max_travel_time`, `payload.history_mode`)
- Alle drei Props an `MyspaceTab` gebunden

### API-Contracts (unverändert, weiterhin gültig)
- Image Proxy URL-Format: `/api/discovery/image-proxy?url={urllib.parse.quote(url, safe='')}`
- Gilt jetzt für Immich **und** Unsplash (vorher nur Immich)

### Architektur-Entscheidungen
- Pool-first statt on-the-fly: Suggestions kommen aus SQLite, LLM läuft im Hintergrund
- `asyncio.create_task` für non-blocking Refresh wenn Pool < `DISCOVERY_POOL_REFILL_THRESHOLD`
- Synchroner Fallback wenn Pool komplett leer (erster Start)
- `_make_proxy_url()` als Single Source of Truth für Proxy-URLs — keine doppelte Logik in routes/
- `TravelPersonality` / `TravelDefaults` als Pydantic-Modelle — Frontend kann Personality später isoliert über eigenes API-Panel ansprechen



---

## Phase B — WanderWizzard Trips als Container-Entität (Session 2025-04-13)

### Architektur-Philosophie: Trips als zentrales Objekt

```
WanderWizzard (2-Schritt-Wizard)
    │
    ▼  POST /api/ws-trips
ws_trips (Container)
    │
    ├── trip_todos (KI-generiert via gpt-4o-mini)
    │
    └── trackers / gf_trackers / homair_trackers / booking_trackers
           (via trip_id FK → jetzt optional an Trip geknüpft)
```

**Kernprinzip:** Ein Trip ist der übergeordnete Container. Alle Tracker (Flüge, Hotels, Camping)
können optional einem Trip zugeordnet werden (`trip_id FK`). Das erlaubt künftig eine
Trip-Detailansicht, die alle gebuchten/gesuchten Elemente einer Reise bündelt.

### 2-Schritt-Wizard-Flow (Phase A + B)

```
Step 1: Details
  ├── Path-Auswahl (Karte: "Ziel bekannt" | "Lass mich überraschen")
  ├── Reisemodus (Karte: "Flugreise" | "Autoreise")
  ├── Pfad-spezifische Felder (Ziel/Datum ODER Vibe-Tags/Flexdatum)
  └── Gesamtbudget

Step 2: Zusammenfassung
  ├── Conditional Rows (Heimatflughafen nur bei Flugreise)
  └── CTA: "Trip anlegen" → POST /api/ws-trips → KI-Todos
```

### DB-Schema (neu)

#### `ws_trips`
```sql
CREATE TABLE ws_trips (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL DEFAULT 1,
    title        TEXT    NOT NULL DEFAULT '',
    destination  TEXT    NOT NULL DEFAULT '',
    start_date   TEXT,
    end_date     TEXT,
    trip_type    TEXT    NOT NULL DEFAULT 'flight',   -- 'flight'|'car'|'inspire'
    budget       REAL             DEFAULT NULL,
    path         TEXT    NOT NULL DEFAULT 'known',    -- 'known'|'inspire'
    travel_mode  TEXT    NOT NULL DEFAULT 'flight',   -- 'flight'|'car'
    vibes        TEXT    NOT NULL DEFAULT '[]',        -- JSON array
    wish_text    TEXT             DEFAULT NULL,
    flex_month   TEXT             DEFAULT NULL,
    flex_nights  INTEGER          DEFAULT NULL,
    max_time     TEXT             DEFAULT NULL,
    home_airport TEXT             DEFAULT NULL,
    adults       INTEGER NOT NULL DEFAULT 2,
    children     INTEGER NOT NULL DEFAULT 0,
    status       TEXT    NOT NULL DEFAULT 'planning', -- 'planning'|'booked'|'completed'
    notes        TEXT             DEFAULT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

#### `trip_todos`
```sql
CREATE TABLE trip_todos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id    INTEGER NOT NULL REFERENCES ws_trips(id) ON DELETE CASCADE,
    task       TEXT    NOT NULL,
    category   TEXT    NOT NULL DEFAULT 'general',  -- 'booking'|'packing'|'documents'|'general'
    is_done    INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

#### Migration: `trip_id` auf Tracker-Tabellen
```sql
ALTER TABLE trackers         ADD COLUMN trip_id INTEGER DEFAULT NULL REFERENCES ws_trips(id) ON DELETE SET NULL;
ALTER TABLE gf_trackers      ADD COLUMN trip_id INTEGER DEFAULT NULL REFERENCES ws_trips(id) ON DELETE SET NULL;
ALTER TABLE homair_trackers  ADD COLUMN trip_id INTEGER DEFAULT NULL REFERENCES ws_trips(id) ON DELETE SET NULL;
ALTER TABLE booking_trackers ADD COLUMN trip_id INTEGER DEFAULT NULL REFERENCES ws_trips(id) ON DELETE SET NULL;
```

### API — `/api/ws-trips` (routes/ws_trips.py)

| Method | Path | Beschreibung |
|--------|------|-------------|
| POST | `/api/ws-trips` | Trip anlegen + KI-Todos generieren |
| GET | `/api/ws-trips` | Alle Trips des Users |
| GET | `/api/ws-trips/{id}` | Einzelner Trip + Todos |
| PATCH | `/api/ws-trips/{id}/status` | Status ändern (planning/booked/completed) |
| DELETE | `/api/ws-trips/{id}` | Trip löschen (CASCADE auf todos) |
| GET | `/api/ws-trips/{id}/todos` | To-Dos eines Trips |
| POST | `/api/ws-trips/{id}/todos` | Manuelles To-Do hinzufügen |
| PATCH | `/api/ws-trips/{id}/todos/{todo_id}/toggle` | Erledigt-Status toggeln |
| DELETE | `/api/ws-trips/{id}/todos/{todo_id}` | To-Do löschen |

### KI-To-Do-Generierung (`_generate_todos`)

- **Modell:** `gpt-4o-mini` (kostengünstig, schnell)
- **Prompt:** Kontextsensitiv nach `destination`, `travel_mode`, `vibes`, `wish_text`, `adults/children`, `budget`
- **Output:** 5 JSON-Todos mit `task` + `category`
- **Kategorien:** `booking` | `documents` | `packing` | `general`
- **Fallback:** Statische Todos (Flug vs. Auto) wenn kein OpenAI Key vorhanden
- **Key-Source:** `settings`-Tabelle (`get_setting("openai_key")`) → gleicher Key wie Discovery
- **Fehlerbehandlung:** Exception → Fallback, Trip wird trotzdem angelegt

### Geänderte Dateien (Phase B)

| Datei | Änderung |
|-------|---------|
| `backend/database.py` | `ws_trips` + `trip_todos` Tabellen, `trip_id` Migration, 8 neue CRUD-Funktionen |
| `backend/routes/ws_trips.py` | Neuer Router (neu erstellt), 9 Endpoints |
| `backend/main.py` | `ws_trips_route` registriert unter `/api/ws-trips` |
| `CLAUDE.md` | Diese Dokumentation |

### Nächste Schritte (Phase C — Frontend)

- [ ] MyTrips: neuer Tab "WS-Trips" zeigt `ws_trips` Liste mit Status-Badges
- [ ] Trip-Detailansicht mit To-Do-Checkliste (toggle inline)
- [ ] WanderWizzard `createTrip()` → `POST /api/ws-trips` statt `priceradarParams.set()`
- [ ] Tracker-Karten: optionaler "Zu Trip hinzufügen" Button (setzt `trip_id`)



---

## Etappe 3 Phase A — Trip Hub & Navigation (Session 2025-04-13)

### Neuer Navigationspfad

```
Dashboard (Hero-Bereich)
    │
    ├── [Zur Reiseplanung] Button  →  wenn ws_trips mit status='planning'/'booked' vorhanden
    │       ↓
    │   Trip Hub (currentPage='triphub', activeWsTripId=<id>)
    │       ├── Hero-Banner (Destination, Countdown, Status)
    │       ├── Aktions-Slots: ✈️ Anreise planen → PriceRadar, 🏨 Unterkunft → PriceRadar
    │       └── Checkliste (trip_todos: toggle, add, delete)
    │
    └── [Reise planen] Button  →  wenn kein aktiver Trip (→ mytrips)

WanderWizzard (modal)
    └── "Trip anlegen" → POST /api/ws-trips → activeWsTripId.set(id) → currentPage='triphub'
```

### Neue Dateien / Änderungen (Phase A)

| Datei | Änderung |
|-------|---------|
| `svelte/src/lib/components/pages/TripHub.svelte` | Neue Seite: Hero, Aktions-Slots, Checkliste |
| `svelte/src/lib/components/WanderWizzard.svelte` | API-Call auf POST /api/ws-trips, Redirect zu TripHub, Stepper zentriert, inaktive Karten opacity-40+grayscale |
| `svelte/src/lib/components/dashboard/HeroSection.svelte` | Trip-Hub-Shortcut-Button (oben rechts) |
| `svelte/src/lib/stores.js` | `activeWsTripId` Store (writable) |
| `svelte/src/routes/+page.svelte` | Route `triphub` → TripHub.svelte |
| `svelte/src/locales/de.json` / `en.json` | 16 neue `tripHub*`/`dash*`/`wizzard*` Keys |

### Store: `activeWsTripId`

```js
// stores.js
export const activeWsTripId = writable(null);
```

Wird gesetzt von:
- `WanderWizzard.createTrip()` nach erfolgreichem POST
- `HeroSection.goToTripHub(tripId)` beim Klick auf den Shortcut-Button

### WanderWizzard UI-Fixes (Phase A)

- **Stepper**: `justify-center gap-6` statt `flex-1` — Schritte stehen mittig im Modal
- **Inaktive Karten**: `opacity:0.4;filter:grayscale(1)` — klare visuelle Hierarchie
- **Aktive Karte**: volles Accent-Glow, Checkmark-Bubble, keine Opacity-Reduktion

### TripHub: Checkliste

- Todos werden direkt von `GET /api/ws-trips/{id}` geladen (inkl. Todos im Response)
- Toggle: `PATCH /api/ws-trips/{id}/todos/{todo_id}/toggle`
- Add: `POST /api/ws-trips/{id}/todos`
- Delete: `DELETE /api/ws-trips/{id}/todos/{todo_id}`
- Fortschrittsbalken zeigt `erledigte / gesamt` als Prozent



---

## Etappe 5 Phase A — UX-Polish & Konsistenz (Session 2025-04-13)

### Neue Dateien

| Datei | Beschreibung |
|-------|-------------|
| `svelte/src/lib/components/mytrips/TripCard.svelte` | Wiederverwendbare Reisekarte (mode: 'planned' \| 'archive') |

### TripCard.svelte — API

```svelte
<TripCard
  trip={trip}
  mode="planned"          <!-- 'planned' | 'archive' -->
  ongoToHub={(t) => ...}  <!-- Klick auf Haupt-Button -->
  ondelete={(t) => ...}   <!-- Aus ⋮-Menü (nur archive) -->
/>
```

- `mode="planned"`: Accent-Gradient, Status-Badge (In Planung / ✓ Gebucht), Primär-Button
- `mode="archive"`: Gedämpfter Gradient, "ERLEBT"-Badge, sekundärer Button, ⋮-Menü mit Löschen

### MyTrips.svelte Änderungen (Phase A)

- **Planned-Tab**: Inline-Card-Markup → `<TripCard mode="planned" />`
- **Archive-Tab**: `JournalTimeline` → `<TripCard mode="archive" />` Grid (Skeleton + Leer-State)
- **Jahresauswahl**: Kompakte 3-Pill-Reihe (`selectedYear-1 | current | +1`) oben rechts in Übersicht und in der Admin-Bar des Archivs. Große Jahr-Card aus Übersicht entfernt.
- **Bucket List**: Kein permanentes Formular mehr. `BucketListTab` verwaltet eigenes Modal-State.

### BucketListTab.svelte Refactoring

- Formular entfernt, stattdessen "+ Wunschziel hinzufügen"-Button oben rechts
- Svelte-Modal mit Zielort-/Ort-Inputs und Enter-Bestätigung
- Volle Bildschirmbreite: 3-spaltige Kacheln mit Hero-Farbstreifen (grün = erledigt, Accent = offen)
- `bucketItem`/`bucketDest` State jetzt in BucketListTab, nicht mehr in MyTrips

### Phase B (noch ausstehend)
- DB: `trip_id`, `is_booked`, `booked_price` auf Tracker-Tabellen
- Tracker-Dialog: "Mit Reise verknüpfen"-Dropdown
- Trip-Hub Smart-Slots: Leer / Tracking aktiv / Gebucht
- Hub-Budget-Rechnung: Gesamt - gebuchte Komponenten = Rest vor Ort
- Backend: Archiv-Nachträge überspringen KI-Todo-Generierung



---

## Etappe 5 Phase B — Tracker-Verknüpfung & Budget (Session 2025-04-13)

### DB-Änderungen

Neue Spalten (idempotente ALTER TABLE Migration in `init_db`):

| Tabelle | Spalte | Typ |
|---------|--------|-----|
| trackers, gf_trackers, homair_trackers, booking_trackers | `trip_id` | INTEGER DEFAULT NULL → ws_trips FK |
| alle 4 | `is_booked` | INTEGER DEFAULT 0 |
| alle 4 | `booked_price` | REAL DEFAULT NULL |

Neue DB-Funktionen: `mark_tracker_booked`, `unmark_tracker_booked`, `link_tracker_to_trip`, `get_trackers_for_trip`

### Neue Backend-Endpoints (`/api/ws-trips/{id}/...`)

| Method | Path | Funktion |
|--------|------|---------|
| GET | `/trackers` | Alle Tracker des Trips, gruppiert nach Typ |
| POST | `/trackers/{tracker_id}/book` | Tracker als gebucht markieren + booked_price setzen |
| DELETE | `/trackers/{tracker_id}/book` | Buchung zurücksetzen |
| GET | `/budget` | Budget-Aufschlüsselung: Gesamt − Flug − Hotel = Vor-Ort |

### Backend-Sonderfall: Vergangene Archiv-Reisen

```python
is_past = start_date < date.today().isoformat()
if is_past:
    # KI-Todo-Generierung wird übersprungen
    todos = []
```

### TripHub.svelte — Smart Action Slots (3 Zustände)

```
Zustand A (kein Tracker):
  → Button "Flug suchen / Unterkunft suchen"
  → Deep-Link zu PriceRadar via priceradarParams (destination, dateFrom, dateTo vorausgefüllt)

Zustand B (Tracker vorhanden, nicht gebucht):
  → Zeigt aktuellen Preis aus latest_snapshot
  → "Buchen ↗" Button (booking_url)
  → "Als gebucht markieren" → Book-Modal

Zustand C (is_booked = 1):
  → Grüner Border + ✅-Badge
  → Zeigt booked_price (finaler Preis)
  → "Buchen ↗" Link bleibt sichtbar
  → "↩ zurücksetzen" zum Entmarkieren
```

### Budget-Breakdown im Hub

```
Gesamtbudget  4000 €
− Flug           380 €
− Unterkunft     620 €
────────────────────
Vor Ort        3000 €
```

Grüner Progressbalken zeigt gebuchten Anteil. Rot wenn > 85%.

### Deep-Link: TripHub → PriceRadar

```js
priceradarParams.set({
  destination:  trip.destination,
  dateFrom:     trip.start_date,
  dateTo:       trip.end_date,
  adults:       trip.adults,
  _fromTripHub: trip.id,
  _searchType:  'flight' | 'hotel',
});
currentPage.set('priceradar');
```

PriceRadar liest `priceradarParams` beim Mount und füllt Formular vor.

---

## Bugfix-Paket 1 (April 2026)

### Bug 1 – Sidebar Routing / Planer Modal-Freeze
**Problem:** `WanderWizzard` renderte sich als `fixed inset-0 z-50`-Overlay mit Backdrop. Der `$effect(() => { if (!open) open = true; })` in `Planer.svelte` verhinderte das Schließen und fror das UI ein.

**Fix:**
- `WanderWizzard.svelte`: Neuer `embedded`-Prop (default `false`). Im embedded-Modus wird der `fixed`-Backdrop-Wrapper weggelassen; der Inhalt rendert sich als normales Block-Element.
- `Planer.svelte`: `embedded={true}` gesetzt, `$effect`-Reopener entfernt.

### Bug 2 – Deep-Link TripHub → PriceRadar
**Problem:** `applyPriceradarParams()` wurde nur in `onMount()` aufgerufen. Da `currentPage`-Wechsel und Store-Setzung synchron passieren, konnte PriceRadar den Store verpassen.

**Fix:** Zusätzlich ein `$effect(() => { if ($priceradarParams) applyPriceradarParams(); })` in `PriceRadar.svelte` – reagiert reaktiv auf Store-Änderungen auch nach dem Mount.

### Bug 3 – Trip-Link Dropdown schwebt global
**Problem:** Das `wsTrips`-Dropdown war permanent sichtbar über der Tracker-Grid-Liste.

**Fix:** Dropdown wird nur noch gerendert wenn `searchResults.length > 0` – es ist damit kontextuell an den Such-/Speicher-Flow gebunden. `wsTrips`-Filter bleibt: nur Trips mit `start_date >= today`.

### Bug 4 – Settings Alerts Tab reagiert nicht
**Problem:** `tabIds` und `tabLabels` nutzten `$derived.by()` mit `$t()`-Store-Calls, was in Svelte 5 zu Reaktivitätsproblemen führen kann.

**Fix:** Umgestellt auf `$derived` (ohne `.by()`) – einfacher Ausdruck statt Callback-Funktion.

### Bug 5 – Archiv-Modus TripHub
**Problem:** Vergangene Reisen (`end_date < heute`) zeigten Status „In Planung" und waren voll editierbar.

**Fix in `TripHub.svelte`:**
- `isArchived = $derived.by(...)`: `true` wenn `trip.end_date < heute`.
- `statusLabel`: gibt `$t('tripCardExperienced')` ("ERLEBT") zurück wenn `isArchived`.
- `statusColor`: `var(--ws-muted)` wenn `isArchived`.
- Zustand A (leerer Slot): Suchen-Button ausgeblendet (`{#if !isArchived}`), ersetzt durch gedimmte Read-Only-Anzeige.
- Zustand B (Tracker aktiv): „Als gebucht markieren"-Button ausgeblendet wenn `isArchived`.
- Checkliste: Todo-Eingabefeld + Löschen-Button ausgeblendet wenn `isArchived`. Liste wird rein informativ.

---

## UX/UI-Paket 2 (April 2026)

### Feature 1 – Full-Width Layout & 2XL-Grid (MyTrips)
- Haupt-Container `<div class="w-full space-y-4">` statt fester Breite
- Grid-Klassen `2xl:grid-cols-4` ergänzt in Planned-, Archive- und TrackerGrid

### Feature 2 – Ansichts-Toggle Grid/Liste (MyTrips)
- `viewMode = $state('grid' | 'list')` in `MyTrips.svelte`
- Toggle erscheint rechts in der Tab-Bar nur wenn activeTab === 'planned' | 'archive'
- Listenansicht: kompakte tabellarische Zeilen mit Klick auf TripHub

### Feature 3 – Auto-Trip Slot-Dimming (TripHub)
- `isCarSlot` derived per Slot-Iteration: `slot.key === 'flight' && trip?.travel_mode === 'car'`
- CSS-Klassen `opacity-40 grayscale` auf dem Slot-Container

### Feature 4 – TrackerCard Redesign + "Zu Reise hinzufügen"
- Neues Hero-Band mit typ-spezifischem Gradient (Flug: Blau-Orange, Hotel: Lila, Camping: Grün)
- Buchen-Button im Hero-Header (glassmorphism)
- `wsTrips`-Prop: Liste aktiver Trips (gefiltert in PriceRadar: `start_date >= heute`)
- `onlinktrip(tracker, tripId)` Callback → `PATCH /api/{type}/{id}/link-trip`
- Verknüpfter Trip wird als Badge mit Entfernen-Option angezeigt
- Backend: neuer `PATCH /{id}/link-trip` Endpoint in trackers.py, accommodations.py, google_flights.py
- Alle nutzen `link_tracker_to_trip()` aus `database.py`

### i18n neue Keys
`trackerLinkTrip`, `trackerNoTrips`, `radarLastScan`, `radarNoScanYet`, `radarTotal`, `radarNoTypeTrackers`, `viewGrid`, `viewList` — in DE/EN/IT/ES

---

## Lifecycle-Paket 3 (April 2026)

### Feature 1 – Lifecycle-Engine (3 Phasen)
`TripHub.svelte` hat jetzt einen `phase`-Derived-State:
- `planning`: `today < start_date`
- `active`: `today >= start_date && today <= end_date` → grüner Hero-Gradient, pulsierender Badge
- `archived`: `today > end_date` → gedämpft, Read-Only

`statusLabel` gibt je Phase: „IN PLANUNG" / „ON TOUR" / „ERLEBT".
Action Slots (PriceRadar-Deep-Links) sind nur in `planning` sichtbar.

### Feature 2 – Live-Wetter Widget (Open-Meteo, kostenfrei)
Wenn `phase === 'active'` oder `daysUntilStart <= 7`:
1. Geocoding: `https://geocoding-api.open-meteo.com/v1/search?name={destination}`
2. Forecast: `https://api.open-meteo.com/v1/forecast?...&current_weather=true`
Anzeige im Hero als kleines Badge: `{icon} {temp}°C {city}`.
WMO-Wettercodes werden zu Emoji gemappt.

### Feature 3 – Vision-Platzhalter
- Phase `active`: Grid mit „Reisetagebuch" + „Tagesausflüge" (gestrichelt, Coming-Soon-Badge)
- Phase `archived`: „Foto-Galerie (Immich)" mit Hinweis-Text

### Feature 4 – Manuelle Ausgaben
- DB-Migration: `ws_trips.manual_expenses REAL NOT NULL DEFAULT 0`
- PATCH `/api/ws-trips/{id}/manual-expenses` → speichert Wert
- Budget-Endpoint gibt jetzt `manual_expenses` zurück, zieht diesen von `on_site_budget` ab
- UI: editierbares Inline-Feld im Budget-Block, alle 3 Phasen

### Feature 5 – KI To-Dos Upgrade + Regenerieren
- Prompt: „10 bis 15 spezifische To-Dos", `max_tokens` 400→800, Limit 7→15
- POST `/api/ws-trips/{id}/todos/regenerate` löscht bestehende Todos und regeneriert
- UI: „🔄 Neu generieren"-Button im Checklisten-Header, nur in Phase `planning`

### Feature 6 – Image Fallback (Picsum statt Unsplash)
- `TripCard.svelte`: `<img src="https://picsum.photos/seed/{trip.id}/400/200">` im Hero (opacity-15)
- `TripHub.svelte`: Gleiche Logik im Hero, nur in Phase `active`
- Seed = `trip.id` → Bild ist bei jedem Reload stabil

### i18n neue Keys
`tripPhaseActive`, `tripPhaseActiveCountdown`, `hubManualExp`, `hubManualExpSaved`, `hubRegenTodos`, `placeholderJournal`, `placeholderDayTrips`, `placeholderGallery`, `placeholderGalleryHint` — DE/EN/IT/ES

---

## Notfall-Patch (April 2026) — 5 Themenblöcke

### Fix 1 – Backend-Robustheit & Input-Crash

**Alt-Daten NULL-Fallback (`backend/routes/ws_trips.py`)**
- `GET /api/ws-trips/{id}`: `trip["manual_expenses"] = float(trip.get("manual_expenses") or 0.0)`
- Alte Trips (z.B. Dawarich-Syncs) ohne `manual_expenses`-Spalte crashen nicht mehr beim Laden.
- DB-Migration `DEFAULT 0` war vorhanden, aber alte Einträge vor der Migration hatten NULL.

**Float-Validation ManualExpenses**
- `ManualExpensesPayload` mit Pydantic-Validator: akzeptiert Strings mit Komma-Trenner, konvertiert zu `float`.
- Verhindert DB-Crash wenn `"12,50"` oder leerer String aus dem Frontend kommt.

**Frontend (`TripHub.svelte`)**
- Inline-Ausgaben-Input: `type="number" step="0.01"` erzwungen (war `type` fehlendes Attribut).
- `saveManualExp()`: `parseFloat` mit explizitem Komma-Replace + `isFinite`-Check.

---

### Fix 2 – Lifecycle-Logik & TripCard Badges

**Datums-/Zeitzonen-Fix (`TripHub.svelte`)**
- `today` war YYYY-MM-DDTHH:MM:SSZ — Vergleich `today > t_end` konnte fehlschlagen wenn t_end kein T-Suffix hatte.
- Fix: `today = new Date().toISOString().slice(0, 10)` und alle `t_start`/`t_end` mit `.slice(0, 10)` normiert.
- `daysUntilStart`: nutzt jetzt `T00:00:00`-Suffix für lokale Datumsarithmetik ohne Timezone-Drift.

**TripCard 3-Phasen-Logik (`TripCard.svelte`)**
- `phase`-Derived direkt aus `start_date`/`end_date` berechnet — unabhängig vom `mode`-Prop.
- Badge: `"IN PLANUNG"` / `"ON TOUR"` (grün+Pulse) / `"ERLEBT"` — basierend auf `phase`, nicht mehr auf `trip.status`.
- `heroGradient` kennt jetzt 3 Zustände (planning / active grün / archived gedämpft).
- Active-Trip-Button: `background:var(--ws-green)` statt Accent.

---

### Fix 3 – Routing & Autofill

**Zurück-Button (`TripHub.svelte`)**
- War: `onclick={() => currentPage.set('home')}` — ignorierte Browser-History.
- Fix: `onclick={() => history.back()}` — springt intelligent zurück (MyTrips, PriceRadar, Dashboard).

**Radar Autofill (`PriceRadar.svelte`)**
- `prefillParams`-Store wurde nur an `FlightSearchForm` weitergegeben.
- Fix: `<HotelSearchForm {prefillParams} />` und `<CampingSearchForm {prefillParams} />` ebenfalls.

---

### Fix 4 – Picsum-Bilder Totalausfall

**TripHub.svelte**
- War: `{#if phase === 'active' && trip.id}` — Bild nur bei aktiver Phase.
- Fix: `{#if trip.id}` — immer rendern; archived = `grayscale + opacity-10`, sonst `opacity-20`.

**TripCard.svelte**
- War: kein Bild in `mode="planned"` (falscher Conditional).
- Fix: `{#if trip.id}` — immer rendern; archived = `grayscale + opacity-10`, planning/active = `opacity-15`.

---

### Fix 5 – Lösch-Funktion mit Tracker-Sicherheit

**Backend (`backend/routes/ws_trips.py`)**
- `DELETE /api/ws-trips/{id}?mode=trip_only|all`
  - `trip_only` (default): nutzt `ON DELETE SET NULL` der FK-Constraints — Tracker bleiben, `trip_id` → NULL.
  - `all`: löscht alle 4 Tracker-Tabellen explizit (`trackers`, `gf_trackers`, `homair_trackers`, `booking_trackers`) dann Trip.

**Frontend (`TripHub.svelte`)**
- 🗑️-Button im Hub-Header (rechts neben Zurück-Button, immer sichtbar wenn Trip geladen).
- `openDeleteModal()`: lädt `GET /api/ws-trips/{id}/trackers` und zeigt verknüpfte Tracker mit Icon + Ziel.
- Warn-Modal:
  - Wenn Tracker vorhanden: zwei Buttons — „Nur Reise löschen" + „Alles löschen (Reise + Tracker)".
  - Wenn keine Tracker: ein Button — „Reise unwiderruflich löschen".
- Nach Löschen: `currentPage.set('home')`.

---

## Widget-Architektur & UX-Paket (April 2026)

### 1 — "On Tour" Tab (MyTrips)
- Neuer Tab zwischen "Geplant" und "Archiv".
- **Tab-Reihenfolge strikt:** Übersicht | Geplant | 🌍 On Tour | Archiv | Bucket List
- Filter: `start_date <= heute <= end_date` — nur laufende WS-Trips.
- Grid- und Listenansicht wie in anderen Tabs; Liste zeigt animierten grünen "ON TOUR"-Badge.
- Neue i18n-Keys: `tabOnTour`, `onTourEmpty`, `onTourEmptyHint` in DE/EN/IT/ES.

### 2 — Full-Width Layout + Smart Back-Button (TripHub)
- `TripHub.svelte`: Container `w-full px-4 md:px-8` (vorher `max-w-2xl mx-auto`).
- Smart `goBack()`: `window.history.length <= 2` → `currentPage.set('home')` (SPA-sicher), sonst `history.back()`.

### 3 — Generative Gradients (kein Picsum/Unsplash)
- **`svelte/src/lib/components/triphub/helpers.js`** (neu):
  - `strHash(str)` — deterministischer djb2-Hash für konsistente Farben.
  - `destinationGradient(destination, travelMode)` — 8 Brand-Paletten (Stone/Sand/Orange), Winkel per Hash, Autoreisen nutzen grüne Palette.
  - `wmoIcon(code)` — WMO-Code → Emoji (ausgelagert aus TripHub).
- Picsum-`<img>`-Tags aus `TripHub.svelte` und `TripCard.svelte` **vollständig entfernt**.
- `TripCard.svelte`: `heroGradient` nutzt `destinationGradient()` statt hardcodierter Gradienten.
- Archivierte Cards: `filter:saturate(0.6)` für gedämpften Look.

### 4 — Modulares Widget-System (TripHub)
Neue Dateien unter `svelte/src/lib/components/triphub/`:

| Datei | Inhalt |
|-------|--------|
| `helpers.js` | `strHash`, `destinationGradient`, `wmoIcon` |
| `WeatherWidget.svelte` | Open-Meteo Live-Wetter, nur bei `phase==='active'` oder `daysUntilStart<=7` |
| `BudgetWidget.svelte` | Budget-Breakdown + Barausgaben Inline-Edit |
| `ChecklistWidget.svelte` | To-Do-Liste inkl. Regen-Button (alle Phasen) |
| `SlotWidget.svelte` | Tracker-Slots (leer / tracking / gebucht), nur in `planning` |

`TripHub.svelte` ist jetzt **reiner Container**: importiert alle Widgets, hält State + API-Calls, rendert Grid.

Widget-Grid-Layout: `grid-cols-1 md:grid-cols-2` — Weather spannt `md:col-span-2` wenn aktiv.

### 5 — To-Do Regen global (alle Phasen)
- `ChecklistWidget.svelte`: 🔄-Button ist **immer sichtbar**, unabhängig von `phase`.
- Vorher: nur in `phase === 'planning'` gerendert.
- Checkliste bleibt in `archived` Read-Only (kein Toggle/Add/Delete), aber Regen ist möglich.
---

## QA-Hotfix Session (April 2026)

### Bug #1 + #12/#13 — DEIN_TOKEN ReferenceError (KRITISCH)
**Root Cause:** `NotificationsTab.svelte` enthielt den Platzhalter `{DEIN_TOKEN}` in einem HTML-String als Teil einer Telegram-getUpdates-URL. Im Svelte-Template wird `{...}` als JS-Ausdruck geparst → ReferenceError beim Bundle-Load → Wizard friert auf Step 0 ein.

**Fix:** `NotificationsTab.svelte` — Platzhalter ersetzt durch sicheren Literal-Text `<BOT_TOKEN>` (kein Svelte-Ausdruck mehr).

---

### Bug Sammelbug — Globales Datumsformat ignoriert
**Root Cause:** Mehrere Komponenten renderten ISO-Datum (`YYYY-MM-DD`) direkt, ohne die User-Einstellung (`ws-date-format` in localStorage) zu berücksichtigen. `fmtDate()` war bereits in `priceradar/helpers.js` definiert, aber nicht in den UI-Komponenten verwendet.

**Fix — betroffene Dateien:**
- `TripCard.svelte`: `tripDateStr` `$derived.by()` nutzt jetzt `fmtDate(s)` / `fmtDate(e)`. Import von `fmtDate` aus `priceradar/helpers.js` hinzugefügt.
- `TripHub.svelte` (Header): Datum-Anzeige nutzt jetzt `fmtDate(trip.start_date)` / `fmtDate(trip.end_date)`. Import hinzugefügt.
- `BucketListTab.svelte`: `item.created` wird jetzt via `fmtDate((item.created || '').slice(0,10))` formatiert. Import hinzugefügt.
- `TrackerCard.svelte` (Link-Dropdown): `trip.start_date` nutzt jetzt `fmtDate(trip.start_date)`.

**Zentraler Formatter:** `fmtDate(iso)` in `svelte/src/lib/components/priceradar/helpers.js` liest `localStorage.getItem('ws-date-format')` und rendert DD.MM.YYYY / MM/DD/YYYY / YYYY-MM-DD.

---

### Bug #6/#7/#9 — PriceRadar Parameter-Handoff (Analyse)
**Analyse:** `TripHub.svelte` → `goSearch(type)` liest korrekt `trip.destination`, `trip.start_date`, `trip.end_date` und schreibt sie in `priceradarParams`. `PriceRadar.svelte` liest den Store, setzt `activeCategory` basierend auf `_searchType` und übergibt `prefillParams` an alle 3 SearchForms. Kein Code-Bug gefunden — falls Dummy-Daten (Dublin) erscheinen, sind die Trip-Felder im DB-Objekt leer. Keine Code-Änderung nötig.

---

### Bug #10 — Settings Alert-Tab zeigt Scheduler-Inhalt
**Root Cause:** `Settings.svelte` — `tabLabels` wurde mit `$derived.by(() => ({...}))` gebaut. In Svelte 5 führt das mit `$t()`-Store-Calls dazu, dass reactive updates die `{#each tabIds}`-Buttons neu mounten und Event-Listener verloren gehen → Tabs nicht klickbar → `activeTab` bleibt auf `'scheduler'` (oder springt zurück) → Notifications-Tab zeigt Scheduler-Inhalt.

**Fix:** `Settings.svelte` — `tabLabels` von `$derived.by(() => ({...}))` auf `$derived({...})` umgestellt (konsistent mit CLAUDE.md Entscheidung S2-1).

---
---

## QA-Hotfix Session 2 — Mobile & Edge Cases (April 2026)

### Bug #19 — Checkliste Mobile Text-Overflow
**Datei:** `ChecklistWidget.svelte`
- Todo-Text-Span: `break-words` + `word-break:break-word;overflow-wrap:anywhere` hinzugefügt.
- Container `<div class="flex-1 min-w-0">` um `overflow-hidden` ergänzt.

### Bug #16/#18 — TripHub Datum Mobile Scrollbar
**Datei:** `TripHub.svelte` (Header-Meta-Zeile)
- Flex-Container von `flex-wrap` auf `flex-col sm:flex-row` umgestellt — auf Mobile stapelt Destination + Datum vertikal.
- Datum-Span: `text-xs sm:text-sm` + `white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%` — verhindert horizontale Overflow-Scrollbar.

### Bug #5 — Budget "-0 €"
**Datei:** `BudgetWidget.svelte`
- Barausgaben-Anzeige: Guard `parseFloat(...) === 0 ? '0' : '−' + ...` — zeigt `0 €` statt `-0 €`.
- On-Site-Budget: `(v => v === 0 ? '0' : String(v))(parseFloat(...))` — selber Guard.

### Bug #15 — Dashboard Hero statischer Text
**Datei:** `HeroSection.svelte`
- `heroTitle`: Fällt auf `nextWsTrip.destination || nextWsTrip.title` zurück wenn kein Dawarich-Trip vorhanden, aber ein WS-Trip geplant ist.
- `heroSubtitle`: Berechnet Countdown aus `nextWsTrip.start_date` (heute/morgen/N Tage) wenn kein Dawarich-Trip, aber WS-Trip existiert.
- Neue i18n-Keys in DE/EN/IT/ES: `heroNextAdventure`, `heroWelcomeTitle`, `heroTodayStart`, `heroTomorrow`, `heroInDays`, `heroNoTripsSubtitle`.

### Bug #1 — Bucket-List Validierung
**Datei:** `BucketListTab.svelte`
- `disabled={!bucketItem.trim()}` war bereits vorhanden.
- `disabled:cursor-not-allowed` zum Button ergänzt für klareres UX-Feedback.

### Bug #14 — Text-Inkonsistenzen
**de.json:** `plannedEmpty` — "Reiseplaner" → "WanderWizzard".
**TrackerGrid.svelte:** Hardcodierter DE-String für leere Tracker-Liste durch i18n-Key `radarNoTypeTrackersFull` ersetzt.
**en.json + de.json:** Neuer Key `radarNoTypeTrackersFull` — EN: `"No {type} trackers — search and save above!"` / DE: `"Keine {type}-Tracker — oben suchen und speichern!"`.
---

## QA-Hotfix Session 3 — CSP, DOM Warnings, Reaktivität, UX (April 2026)

### Bug #1 — Content Security Policy (CSP)
**Datei:** `docker/nginx.conf`
- `img-src`: `https://images.unsplash.com https://picsum.photos https://*.unsplash.com` ergänzt.
- `style-src` + `style-src-elem`: `https://fonts.googleapis.com` ergänzt.
- `font-src`: `https://fonts.gstatic.com` ergänzt (tatsächliche Font-Dateien).
- `connect-src`: `https://geocoding-api.open-meteo.com https://api.open-meteo.com` ergänzt (Wetter-Widget).

### Bug #2 — DOM Warnings (Meta-Tag + Password-Forms)
**`app.html`:** `<meta name="mobile-web-app-capable">` neben dem Apple-Variant ergänzt.
**`Login.svelte`:** Email + Passwort in `<form onsubmit=...>` eingebettet; `autocomplete="email"` / `"current-password"` gesetzt; Submit-Button als `type="submit"`.
**`AccountTab.svelte`:** Passwort-Inputs in `<form onsubmit=...>` eingebettet; `autocomplete="current-password"` / `"new-password"` gesetzt.

### Bug #3 — Dashboard Hero Reaktivität nach Trip-Anlage
**`Dashboard.svelte`:** `wsTripsVersion`-Counter und `_prevWizzardOpen`-Flag; `$effect` bumpt den Counter wenn WanderWizzard von `open` auf `closed` wechselt.
**`HeroSection.svelte`:** Neuer `refreshKey`-Prop (default 0). `$effect(() => { refreshKey; loadWsTrips(); })` — bei jeder Counter-Änderung wird `loadWsTrips()` neu ausgelöst → Hero zeigt sofort den neuen Trip.

### Bug #4 — WanderWizzard IATA-Code als Trip-Titel
**`WanderWizzard.svelte`:**
- Neuer State `s1DestIata` für den IATA-Code (zur späteren Suche).
- `pickDest(a)`: Schreibt `a.city` in `s1Dest` (statt `a.iata`) → Trip-Titel und `destination` in DB erhalten jetzt den Stadtnamen (z.B. "London").
- `s1DestIata` wird beim Reset geleert.

### Bug #6/#7/#9 — PriceRadar UX
**`PriceRadar.svelte`:** Trip-Link-Dropdown komplett aus der Such-Ergebnis-Ansicht entfernt (Verknüpfung läuft über TrackerCard).
**`SearchResults.svelte`:**
- Hotel-Titelzeile: `title`-Attribut mit vollem Namen für Browser-Tooltip (Bug #6).
- Save-Button: Lokales `savedTrackers`-Set; nach `onsavetracker()` erscheint für 2s `✓ Gespeichert` mit grünem Hintergrund (Bug #7).
- Stops-Dropdown: Identisches Verhalten wie TrackerCard — Badge zeigt Anzahl, Klick öffnet Layover-Airports mit Wartezeit. `parseJsonField` + `fmtLayoverDur` aus `helpers.js` importiert. `Nonstop`-Badge bei `stops === 0` (Bug #9).

### Bug #10 — 401 bei GET /api/settings on page load
**`stores.js` — `loadSettingsFromBackend()`:** Liest `ws-jwt` aus localStorage und setzt `Authorization: Bearer <token>` Header im fetch-Call. Verhindert 401-Fehler wenn Auth aktiviert ist.

---

### Architektur-Notizen (Session 3)
- **CSP-Quelle:** Nginx (`docker/nginx.conf`) — kein SvelteKit `hooks.server` nötig, da Static-Adapter (kein SSR-Server).
- **Password-Form-Pattern:** Svelte `<form onsubmit={(e)=>{e.preventDefault();...}}>` — verhindert Page-Reload, ermöglicht Browser-Passwort-Manager.
- **Hero-Refresh-Pattern:** `refreshKey`-Prop-Pattern ist der bevorzugte Weg um Child-Komponenten mit eigenem `$state` und API-Calls reaktiv von außen neu zu laden — vermeidet Store-Lifting.
---

## Etappe 1 — UI-Politur & Quick Wins (April 2026)

### 1 — Browser-Tab-Titel
**`app.html`:** `<title>WanderSuite</title>` vor `%sveltekit.head%` eingefügt.

### 2 — Wizard Help-Button entfernt
**`SetupWizard.svelte`:** Hilfe-Button (📖) aus dem Modal-Header entfernt — vermeidet Overlap mit FieldGuide-Modal. ✕-Schließen-Button bleibt erhalten.

### 3 — Währung fixiert auf Euro (€)
App fest auf EUR. Entfernte Dateien/Stellen:
- **`SetupWizard.svelte`:** `CURRENCIES` Const, `appCurrency` State, Load + Save + UI-Block entfernt.
- **`BasicTab.svelte`:** `CURRENCIES` Const, `appCurrency` Prop, gesamter Währungs-UI-Block entfernt.
- **`Settings.svelte`:** `appCurrency` State, Load (`gs.currency`), Save (`currency: appCurrency`), `bind:appCurrency` entfernt.

### 4 — Familie aufgeteilt
Companions-Option `family` → zwei neue Optionen:
- `family_kids` — 👶 Familie (Kleinkinder) / Family (Young Kids)
- `family_teens` — 🧒 Familie (Teenager) / Family (Teens)

**Geändert in:** `SetupWizard.svelte`, `MyspaceDefaults.svelte`.
**Neue i18n-Keys** in DE/EN/IT/ES: `defaultsCompFamilyKids`, `defaultsCompFamilyTeens`.
Alter Key `defaultsCompFamily` durch die zwei neuen Keys ersetzt.

### 5 — Live-Vorschau Datumsformat
**`BasicTab.svelte`:** Unter den Datumsformat-Buttons eine reaktive Vorschau-Zeile:
```
📅 Aktuell: 16.04.2026 14:47
```
Berechnet `_previewDate` direkt aus `appDateFormat` via `{@const}` — kein zusätzlicher State nötig. Neuer i18n-Key `settingsPreviewLabel` (DE: "Aktuell" / EN: "Current" / IT: "Attuale" / ES: "Actual").

### 6 — Telegram @userinfobot Hinweis
**`NotificationsTab.svelte`:** Nach der Chat-ID Erklärung:
> 💡 **Tipp**: Sende eine Nachricht an [@userinfobot ↗](https://t.me/userinfobot) — der Bot antwortet direkt mit deiner Chat-ID.
---

## Block 2 — Dashboard Hero Modularisierung (April 2026)

### Neue Dateien
- **`HeroPastTrip.svelte`** (`svelte/src/lib/components/dashboard/`)
- **`HeroNextTrip.svelte`** (`svelte/src/lib/components/dashboard/`)

### HeroPastTrip.svelte — Nostalgie-Kachel
- Berechnet `daysAgo` aus `trip.start_date` / `trip.dateStart`.
- Zeitanzeige: Tage → Wochen → Monate (pluralbildend per i18n-Platzhalter `{n}` / `{s}`).
- **Reiselust-Modus**: `isOld = daysAgo > 180` → orange Akzent-Gradient + 🌍-Badge + Motivationstext.
- **Immich-Bild**: `GET /api/discovery/trip-image?destination=...&date_from=...&date_to=...&source=immich`
- **fmtDate()** für Datumsdisplay (aus `priceradar/helpers.js`).
- Action-Button: `ongoToHub` Callback → `activeWsTripId.set + currentPage.set('triphub')`.
- Neue i18n-Keys (DE/EN/IT/ES): `heroPastToday`, `heroPastDays`, `heroPastWeeks`, `heroPastMonths`, `heroPastLust`, `heroPastLustHint`, `heroPastGoHub`.

### HeroNextTrip.svelte — Countdown-Kachel
- Berechnet `daysUntil` aus `trip.start_date`.
- Countdown-Label: heute/morgen/N Tage (nutzt bestehende i18n-Keys `heroTodayStart`, `heroTomorrow`, `heroInDays`).
- **Urgency**: `isUrgent = daysUntil <= 7` → pulsierender grüner Dot.
- **Unsplash-Bild**: `GET /api/discovery/trip-image?destination=...&source=unsplash`
- `fmtDate()` für Datumsanzeige. Budget-Badge wenn `trip.budget` vorhanden.
- Action-Button: primärer Gradient-Button → TripHub.

### HeroSection.svelte — Refactoring
- Importiert beide neuen Komponenten.
- **Layout-Logik**:
  - Beide vorhanden (`hasLastTrip && (hasNextTrip || nextWsTrip)`) → `grid-cols-1 sm:grid-cols-2` nebeneinander.
  - Nur nextTrip → `HeroNextTrip` allein (volle Breite).
  - Nur lastTrip → `HeroPastTrip` allein (volle Breite).
  - Kein Trip → Willkommen-Banner mit WanderWizzard-CTA.
- **Budget-Widget** als eigenständiger Dark-Block direkt unter den Kacheln (kein absolutes Positioning mehr).
- **Z-Index-Fix**: Budget-Interaktionselemente haben `relative z-10` — kein Overlay-Block mehr.
- Nostalgie-Image-Logik (`heroImageUrl` + `$effect`) aus HeroSection entfernt (jeweils in Sub-Komponente).
- `heroBg` vereinfacht zu statischem String (nur noch für No-Trips-Fallback).
