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
