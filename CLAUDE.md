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
  │
  └─► Zoraxy Reverse Proxy (Unraid)
        │
        ├─► Frontend :8767 (Nginx + Svelte SPA)
        │     └─► /api/* → backend:8000 (internal Docker network)
        │
        └─► Backend :8768 (FastAPI — Swagger, direct API access)
              ⚠️  Backend NOT exposed externally via Zoraxy
              → /api/* calls go through Nginx proxy on port 8767
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
# Wenn gesetzt → direkt verwenden. Wenn nicht gesetzt (= localhost) →
# rp_id + origin automatisch aus HTTP Origin-Header abgeleitet.
WEBAUTHN_RP_ID=wandersuite.deinedomain.de
WEBAUTHN_RP_NAME=WanderSuite
WEBAUTHN_ORIGIN=https://wandersuite.deinedomain.de
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
1. **Env-Vars explizit gesetzt** (`WEBAUTHN_RP_ID != "localhost"`) → direkt verwenden
2. **HTTP Origin-Header** (Browser sendet bei jedem POST) → `hostname` als `rp_id`
3. **Fallback** → localhost defaults

⚠️ Nie `x-forwarded-host` verwenden — kann leer sein → `"http://"` → bug.

---

## i18n System

**Dateien:** `svelte/src/locales/de.json`, `en.json`, `it.json`
**Store:** `svelte/src/lib/i18n.js` — reaktiver `t`-Store, `$t('key')` in Komponenten

Vollständig übersetzt (DE/EN/IT): Navigation, Settings, Dashboard, MyTrips,
PriceRadar (alle Labels + Formular-Felder), Discover, Onboarding, Login, Setup.

**Regel:** Immer alle 3 Locale-Dateien gleichzeitig updaten. Tabs nie hardcodiert —
immer `$derived([...])` mit `$t('key')`.

---

## PWA / Favicon

- `svelte/static/favicon.svg` — oranges Rund-Rechteck (#D95D39) mit Kompassrose
- `svelte/static/manifest.webmanifest` — PWA-Manifest (name, theme_color, icons)
- `svelte/static/icons/icon-192.png` + `icon-512.png` — generiert mit Pillow
- `svelte/src/app.html` — verlinkt favicon.svg + manifest

---

## Settings — Mein Bereich (myspace Tab)

- Per-user Einstellungen: Dawarich, ActualBudget, Home-Koordinaten
- **Geocoding:** Ortsname eingeben + 📍 → Nominatim → lat/lon automatisch befüllt
- **ActualBudget Dateiname:** Hilfetext + Schritt-für-Schritt im FieldGuide (Tab Reisen)
  - Budget-Name oben links anklicken → ID aus der URL entnehmen
  - Oder: `/api/budget/actual/list-files` aufrufen → listet alle verfügbaren Dateien

---

## MyTrips — Architektur & UX

### Tab-Reihenfolge (strikt)
| # | ID | Label |
|---|----|-------|
| 1 | `overview` | 📊 Übersicht |
| 2 | `trips` | ✈️ Geplante Reisen |
| 3 | `journal` | 📓 Reisechronik |
| 4 | `bucketlist` | 🌟 Bucket List |

### Grid-Layout (Tabs 2–4)
`grid grid-cols-1 lg:grid-cols-3 gap-5`
- `lg:col-span-1` — Formular / Aktionen (links, 1/3)
- `lg:col-span-2` — Liste / Timeline (rechts, 2/3)

### Header-Elemente
- **Titel** `🎒 Meine Reisen`
- **Globaler Sync-Button** — rund, SVG-Icon, triggert `syncJournal()` + `syncActual()` nacheinander, `globalSyncing` State
- **Jahres-Switcher** — max. **4 Jahre** gleichzeitig sichtbar, `‹ ›` blättern seitenweise
  - `availableYears()` als `$derived` — sammelt aus `$trips`, `journalTrips`, `budgetByYear`
  - `yearPageStart` State + `visibleYears()` für Pagination
  - `$effect` passt Page automatisch an wenn `selectedYear` sich ändert
  - Alle Views **strikt** nach `selectedYear` gefiltert
- **Badges** — `✈️ X geplant` (klickbar → Tab `trips`) + `Y gesamt`
  - `upcomingCount` = `$trips.filter(dateStart >= today).length`
  - `totalCount` = `upcomingCount + journalTrips.length`

### Übersicht-Tab (Tab 1)

**Stats-Grid** — 4 Karten, 2×2 Grid (`grid-cols-2 sm:grid-cols-4`):
| Karte | Inhalt | Klick-Ziel |
|-------|--------|-----------|
| ✅ Vergangen | `journalYear.length` | → Tab `journal` |
| ✈️ Geplant | `upcomingCount` | → Tab `trips` |
| 🌟 Wunschziele | `$bucketlist.filter(!done).length` | → Tab `bucketlist` |
| 💸 Ausgegeben | `totalSpentYear` + verbleibendes Budget | — |

Alle 3 Reise-Karten haben Hover-Effekt + `→ Tab-Name` Subtitle.

**Budget-Progressbar** — zeigt `totalSpentYear` vs `yearBudget`, farbkodiert.
Aufschlüsselung: `📓 Vergangen: X € · ✈️ Geplant: Y €`

**ScratchMap** — Weltkarte mit Pins (siehe unten)

**Listen:**
- **Nächste Abenteuer** (upcoming, aufsteigend sortiert, max. 4 + "X weitere →")
- **Letzte Erinnerungen** (`journalYear`, absteigend, max. 4 + "X weitere →")

### Geplante Reisen (Tab 2)

**Links (1/3):**
- Smart Reise-Planer Card (Coming Soon Badge)
- Formular: Name, Von/Bis Datum, Kosten → speichert in localStorage `trips`-Store

**Rechts (2/3):**
- Budget-Progressbar für `selectedYear`
- `✈️ Nächste Abenteuer` — upcoming (alle, kein Jahresfilter für Tab-Anzeige)
- `✅ Vergangen (manuell)` — past (alle localStorage-Trips die in der Vergangenheit liegen)

⚠️ **Kein ActualBudget Sync** in diesem Tab — gehört in Reisechronik.

### Reisechronik (Tab 3)

**Links (1/3):**
- **Manuell erfassen** — Name*, Von*, Bis, Land, Kosten → `POST /api/trips` mit `source=manual`
- **💶 Jahresbudget {Jahr}** — Input → `PUT /api/trips/budget { year, amount }`
- **ActualBudget Sync** — `POST /api/budget/actual/transactions`
  - Hilfe-Panel (`<details>`) mit Schritt-für-Schritt Anleitung
  - `📂 Verfügbare Dateien anzeigen` → `POST /api/budget/actual/list-files` → zeigt alle Budget-Dateien
  - Auto-Fallback: wenn `actual_file` leer → erste verfügbare Datei verwenden
  - Fehler werden inline angezeigt mit Hinweis auf Einstellungen
- **Dawarich Sync** — `POST /api/dawarich/sync`

**Rechts (2/3): Timeline**
- Gefiltert nach `selectedYear` (strikt auf `start_date.slice(0,4)`)
- Dawarich-Trips: orange Timeline-Dot
- Manuelle Einträge: violetter Dot + `manuell`-Badge
- **Inline-Kosten-Editor** pro Eintrag: `💶 Kosten hinterlegen` → Input → Enter/✓ → `PATCH /api/trips/{id}/cost`

### Budget-Logik
- Pro Jahr im Backend: `GET/PUT /api/trips/budget`
- Response: `{ "2024": 3000, "2025": 4500 }`
- Legacy-Fallback: liest alten `ws-budget` Wert
- `yearBudget = budgetByYear[selectedYear]`
- `totalSpentYear = journalSpentYear + tripsSpentYear`
  - `journalSpentYear` = Summe aller `journalYear[].cost`
  - `tripsSpentYear` = Summe aller `$trips` für `selectedYear`

---

## ScratchMap.svelte

**Props:**
- `journalTrips` — alle Chronik-Trips (Dawarich + manuell)
- `plannedTrips` — geplante Trips (aus `$trips` Store)
- `selectedYear` — aktuell gewähltes Jahr

**Marker-Typen & Farben:**
| Typ | Quelle | Farbe | Jahresfilter |
|-----|--------|-------|-------------|
| `visited` | journalTrips mit lat/lon | `#2d6a4f` grün | ja |
| `planned` | plannedTrips mit lat/lon | `#2563eb` blau | ja |
| `bucket` | `$bucketlist` mit lat/lon | `#c4622d` orange | nein |

**Fallback-Demos** wenn keine echten Daten: Salzburg/Rom/Paris (visited), London (planned), Tokyo/Machu Picchu (bucket)

**Ladelogik (robust):**
1. Container **immer im DOM** — kein `{#if}` conditional rendering
2. `setTimeout(..., 150)` vor Init (Container braucht gerenderte Größe)
3. Sequenziell: CSS → `jsvectormap.min.js` → **poll** bis `window.jsVectorMap` verfügbar → `world.js` → 150ms pause
4. Polling: `setInterval` prüft alle 100ms, Timeout nach 2s
5. Marker-Farben per DOM-Patching (`c.setAttribute('fill', COLORS[type])`) nach 300ms
6. `destroyed`-Flag verhindert Race Conditions beim Unmount

CDN: `https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/`

---

## Backend API — Vollständige Übersicht

### /api/trips (routes/trips.py)
| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/api/trips` | Alle Trips (dawarich + manual), pro User, sortiert nach start_date |
| POST | `/api/trips` | Manuellen Trip anlegen (`source=manual`) |
| PATCH | `/api/trips/{id}/cost` | Kosten eines Trips updaten `{ cost: float\|null }` |
| DELETE | `/api/trips/{id}` | Trip löschen |
| GET | `/api/trips/budget` | Budget nach Jahr `{"2024":3000}` |
| PUT | `/api/trips/budget` | Budget für Jahr setzen `{ year: int, amount: float }` |

### /api/budget (routes/budget.py)
| Method | Path | Beschreibung |
|--------|------|-------------|
| POST | `/api/budget/actual/transactions` | Frontend-kompatibler Sync-Endpoint |
| POST | `/api/budget/actual/list-files` | Verfügbare Budget-Dateien auflisten |
| POST | `/api/trips/auto-cost` | ActualBudget Tx → Trips zuordnen (Datum-Overlap) |
| POST | `/api/budget/actual/expenses` | Interne Variante (base_url/password/budget_file) |
| POST | `/api/budget/actual/files` | Alte Variante |
| POST | `/api/budget/actual/debug` | Debug: Transaktionen + Konten anzeigen |

**`/actual/transactions` Feldmapping:**
- Frontend sendet: `actual_url`, `actual_token`, `actual_file`, `categories`
- Backend mappt auf: `base_url`, `password`, `budget_file`, `category_names`
- Auto-Fallback: wenn `actual_file` leer → erste verfügbare Datei

### /api/auth / /api/auth/passkeys
Siehe Auth-Sektion oben.

### /api/settings / /api/settings/user
- Global (Admin): SerpAPI, Gemini, OpenAI, Telegram, Gotify, language
- Per-user: dawarich_url/token, actual_url/token/file, home_lat/lon, travel_categories

### /api/dawarich
- `POST /api/dawarich/sync` — GPS-Trips aus Dawarich laden + detected_trips befüllen
- `GET /api/dawarich/trips` — Liste der erkannten Trips

---

## Datenbank — detected_trips

Tabelle für alle Reisen (Dawarich + manuell):

```sql
CREATE TABLE detected_trips (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL DEFAULT 1,
    start_date     TEXT NOT NULL,
    end_date       TEXT NOT NULL,
    location_name  TEXT,
    country        TEXT,
    lat            REAL,
    lon            REAL,
    nights         INTEGER NOT NULL DEFAULT 1,
    source         TEXT NOT NULL DEFAULT 'dawarich',  -- 'dawarich' | 'manual'
    cost           REAL DEFAULT NULL,                    -- nachträglich editierbar
    notes          TEXT DEFAULT NULL,
    created_at     TEXT NOT NULL
);
```

Duplicate-Check: `WHERE user_id=? AND start_date=? AND end_date=? AND source=?`
→ Dawarich-Trips werden bei erneutem Sync aktualisiert, manuelle nie überschrieben.

---

## Multi-User Architecture

### Data Isolation
| Table | Scope | Notes |
|-------|-------|-------|
| `trackers` | Per-user | `user_id` column |
| `gf_trackers` | Per-user | |
| `homair_trackers` | Per-user | |
| `booking_trackers` | Per-user | |
| `detected_trips` | Per-user | Dawarich + manual, cost/notes editierbar |
| `user_data` | Per-user | ws-trips, ws-bucketlist, ws-budget-years |
| `user_settings` | Per-user | dawarich, actualbudget, home coords |
| `settings` | Global (admin) | API keys, notifications |
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

**TODO — set in Zoraxy:**
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`

---

## File Structure

```
wandersuite/
├── svelte/src/
│   ├── lib/
│   │   ├── stores.js              ← all state (trips, budget, bucketlist, apiUrl, ...)
│   │   ├── api.js                 ← HTTP client with JWT injection
│   │   ├── i18n.js                ← reactive t() derived store
│   │   └── components/
│   │       ├── AppShell.svelte
│   │       ├── Header.svelte      ← BETA badge + version
│   │       ├── Sidebar.svelte     ← logout when auth enabled
│   │       ├── Login.svelte       ← passkey + password fallback
│   │       ├── Setup.svelte       ← first admin account
│   │       ├── Settings.svelte    ← tabs: basic/integrations/apis/notifications/myspace/account/admin
│   │       ├── PasskeyManager.svelte
│   │       ├── FieldGuide.svelte  ← ActualBudget filename docs
│   │       ├── ScratchMap.svelte  ← jsvectormap, 3 Marker-Typen, Jahr-Filter, robust CDN load
│   │       └── pages/
│   │           ├── Dashboard.svelte
│   │           ├── PriceRadar.svelte   ← vollständig i18n, alle Tabs
│   │           ├── MyTrips.svelte      ← Tabs: overview/trips/journal/bucketlist
│   │           └── Discover.svelte     ← vollständig i18n
│   ├── locales/
│   │   ├── de.json
│   │   ├── en.json
│   │   └── it.json
│   └── routes/
│       ├── +layout.svelte         ← gate: onboarding → setup → login → app
│       └── +page.svelte
├── svelte/static/
│   ├── favicon.svg
│   ├── manifest.webmanifest
│   └── icons/icon-192.png, icon-512.png
├── backend/
│   ├── main.py                    ← APP_VERSION, alle Router registriert
│   ├── database.py                ← detected_trips: cost/notes/source Spalten
│   ├── auth_db.py
│   ├── auth_jwt.py
│   ├── settings_manager.py        ← global + per-user settings
│   ├── actual_budget.py           ← actualpy wrapper: get_travel_expenses, list_budget_files
│   ├── dawarich.py
│   └── routes/
│       ├── auth.py
│       ├── passkey.py             ← _get_rp() auto-detection via Origin-Header
│       ├── settings.py
│       ├── trips.py               ← /api/trips unified endpoint + /api/trips/budget
│       ├── budget.py              ← /api/budget/actual/* incl. /transactions + /list-files
│       ├── trackers.py
│       ├── google_flights.py
│       ├── accommodations.py
│       ├── userdata.py
│       └── dawarich.py
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.frontend
│   └── nginx.conf
└── docker-compose.yml
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
- Frontend sendet `actual_url`/`actual_token`/`actual_file` — Backend `/actual/transactions` mappt diese
- Wenn `actual_file` leer → erste verfügbare Datei wird automatisch verwendet
- Dateiname ≠ Budget-Name in der UI — es ist die **interne ID** (aus URL kopieren)
- Debug-Endpoint: `POST /api/budget/actual/debug` mit `base_url`/`password`/`budget_file`

### here.now / CDN-Caching
- here.now generiert bei jedem Deploy eine neue zufällige URL → manuell im Dashboard pinnen
- CDN cached aggressiv nach URL-Pfad → bei gleichem Chunk-Hash kein Cache-Bust

### jsvectormap CDN-Load
- `world.js` braucht `window.jsVectorMap` global → strikt sequenziell laden
- `Promise.all` schlägt fehl weil `world.js` parallel geladen nichts findet
- Lösung: CSS → core → **poll bis bereit** → world.js → 150ms pause → init

### Svelte 5 / $derived
- `$derived(() => { ... })` gibt eine Funktion zurück → im Template mit `()` aufrufen: `availableYears()`
- `$state` Arrays/Objects: immer neu zuweisen statt mutieren: `arr = [...arr, item]`

---

## MyTrips — Letzte Änderungen (April 2026)

### Jahr-Switcher
- Zeigt immer **genau 3 Jahre**: `selectedYear-1 | selectedYear | selectedYear+1`
- `‹` / `›` dekrementieren/inkrementieren `selectedYear` direkt
- Kein `availableYears`-Paginierung mehr — einfacher, robuster

### Header Badges (4 Stück)
- `✈️ X geplant` → klickbar → Tab `trips`
- `✅ Y vergangen` → klickbar → Tab `journal`
- `🌟 Z wünsche` → klickbar → Tab `bucketlist`
- `W gesamt` → read-only

### Donut-Chart (SVG/conic-gradient)
- Kein externes Chart-Package — reines CSS `conic-gradient`
- Segmente: Vergangen (dunkelgrün `#2d6a4f`) | Geplant (hellgrün `#86efac`) | Verfügbar (grau) | Überschuss (rot)
- Legende-Buttons wechseln Tab (kein Auto-Filter)
- `auto_cost` (automatisch zugeordnet) wird in Kosten eingerechnet

### Reisechronik — Sync-Logik

#### Reihenfolge (nummeriert)
1. **Jahresbudget** (ganz oben links)
2. **Manuell erfassen** (Formular)
3. **💡 Tipp-Banner** (optimale Sync-Reihenfolge erklären)
4. **1. Dawarich Sync** (grüner Balken links) — mit `force_full` Checkbox
5. **2. ActualBudget Sync** (blauer Balken links) — mit `🔗 Kosten automatisch zuordnen` Button

#### force_full (Dawarich)
- Checkbox: "Gelöschte Reisen erzwingen (Full Sync)"
- Sendet `force_full: true` an `/api/dawarich/sync`
- Backend: `unignore_detected_trips()` → setzt `ignored=0` für alle Dawarich-Trips

#### Auto-Cost (ActualBudget → Dawarich-Trips)
- Erscheint nach erfolgreichem ActualBudget Sync
- Button: `🔗 Kosten automatisch zuordnen`
- Endpoint: `POST /api/trips/auto-cost`
- Logik: Transaktionen deren `date` im `[trip.start_date, trip.end_date]` liegt → werden dem Trip als `auto_cost` zugeordnet
- In Timeline: `(auto)` Badge wenn `cost==null` aber `auto_cost` vorhanden

#### Soft-Delete (Dawarich-Trips)
- Löschen setzt `ignored=1` in DB (kein echter DELETE)
- Beim nächsten Sync wird ignorierte Trips übersprungen
- `force_full=true` → resettet alle `ignored=1` auf `ignored=0`
- Manuelle Trips: echter DELETE

### Settings — Auth-Abhängigkeit
- `auth_enabled=false` → Tab **Integrationen** sichtbar (global, single-user)
- `auth_enabled=true`  → Tab **Mein Bereich** sichtbar (per-user, verschlüsselt)
- Beide Tabs haben Info-Banner mit Erklärung
- Beide speichern verschlüsselt in DB via `settings_manager`

### ScratchMap — Lokaler Import
- `jsvectormap` aus `node_modules` (npm, kein CDN)
- `import { default as jsVectorMap } from 'jsvectormap'`
- `import 'jsvectormap/dist/maps/world.js'`
- CSS via `<svelte:head><style>@import 'jsvectormap/dist/css/jsvectormap.min.css'</style></svelte:head>`


---

## PriceRadar — Architektur (Multi-Provider Aggregator)

### Tab-Struktur
| Tab | ID | Provider | Tracker-Tabelle |
|-----|----|----------|-----------------|
| 🟠 Ryanair | `ryanair` | ryanair.com scraper | `trackers` |
| 🔵 Google Flights | `gflights` | SerpAPI Google Flights | `gf_trackers` |
| ⛺ Camping | `homair` | SerpAPI Google Hotels (Homair-Query) | `homair_trackers` |
| 🏨 Hotels | `booking` | SerpAPI Google Hotels | `booking_trackers` |

### Tracker-Karten Features
- **Wunschpreis (`wish_price`)**: Editierbares Inline-Feld (✏️ → Input → ✓/Enter). Grüner Border + "🎯 Wunschpreis erreicht!" wenn `price ≤ wish_price`.
- **Preisverlauf-Chart**: Akkordeon (📈 Button) → SVG Liniendiagramm aus `price_history` Tabelle. Min/Max-Labels.
- **Skeleton Screens**: Animate-pulse Platzhalter beim Laden.

### Wish-Price API
`PUT /api/prices/wish/{table}/{tracker_id}` mit `{ wish_price: float | null }`
- table: `trackers` | `gf_trackers` | `homair_trackers` | `booking_trackers`
- Endpoint in `backend/routes/prices.py`

### Price History API
`GET /api/prices/history/{tracker_type}/{tracker_id}?limit=90`
- tracker_type: `flight` | `google_flight` | `hotel` | `camping`
- Returns: `{ history: [{ fetched_at, price, currency, provider, status }] }`

---

## Datenbank — Neue Tabellen (dieses Upgrade)

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
```
**Cleanup**: `DELETE FROM price_history WHERE fetched_at < datetime('now', '-180 days')`
→ Täglich 03:00 via APScheduler (`run_cleanup_job()`)

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

### wish_price Spalte (Migration)
Neue Spalte auf allen Tracker-Tabellen:
```sql
ALTER TABLE trackers         ADD COLUMN wish_price REAL DEFAULT NULL;
ALTER TABLE gf_trackers      ADD COLUMN wish_price REAL DEFAULT NULL;
ALTER TABLE homair_trackers  ADD COLUMN wish_price REAL DEFAULT NULL;
ALTER TABLE booking_trackers ADD COLUMN wish_price REAL DEFAULT NULL;
```

---

## Scheduler — Per-User Einstellungen

### API
| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| GET | `/api/scheduler/settings` | Aktuelle Einstellungen des Users |
| PUT | `/api/scheduler/settings` | Intervall (6/12/24/48/72/168h) + Notifications speichern |
| POST | `/api/scheduler/run` | Manueller Trigger (läuft im Hintergrund) |

### Settings-Tab "⏰ Scheduler"
- 6 Intervall-Buttons (6h / 12h / 1d / 2d / 3d / 1Wo)
- Toggle: Preissturz-Alarm, Tägliche Zusammenfassung
- Letzter Lauf Timestamp
- "Jetzt ausführen" Button

### Cleanup-Job
- Täglich 03:00 via APScheduler
- Löscht `price_history` + alle `*_snapshots` Einträge älter als 180 Tage
- Funktion: `run_cleanup_job()` in `backend/scheduler.py`

---

## Mobile UI

### BottomNav — Fixiert
- `position: fixed; bottom: 0; z-index: 50` (Tailwind: `fixed bottom-0 left-0 right-0 z-50`)
- Spacer-Div (`h-16`) direkt nach dem Nav-Element verhindert, dass Content verdeckt wird

### Settings — Responsive Overlay
- **Mobile**: `fixed inset-0` → Fullscreen Overlay
- **Desktop**: `fixed inset-y-0 right-0 md:max-w-md` → Side Panel (wie bisher)

---

## Backend — Scheduler Deep Logging

Format: `[PROVIDER] {icon} #{id} status={status} | price={price} | {detail}`
- `scrape=success` / `scrape=blocked_by_cf` / `source=serpapi`
- Jeder Provider-Runner (`run_ryanair_trackers`, `run_gf_trackers`, etc.) läuft unabhängig
- Fehler in einem Provider crashen nie den nächsten


## Open / Next Steps

### Erledigt (diese Session)
- [x] Passkeys: rp_id auto-detection via Origin-Header (kein x-forwarded-host)
- [x] Passkeys: `attestation="none"` String entfernt (py-webauthn erwartet Default)
- [x] i18n: alle Bereiche DE/EN/IT vollständig
- [x] PriceRadar: alle Formular-Labels, Tabs, Buttons i18n
- [x] MyTrips: komplettes UX-Redesign
  - [x] Tab-Reihenfolge: Übersicht → Geplant → Chronik → Bucket List
  - [x] Jahres-Switcher: max. 4 Jahre sichtbar, `‹ ›` navigierbar
  - [x] Globaler Sync-Button (Dawarich + ActualBudget nacheinander)
  - [x] Budget pro Jahr im Backend (`/api/trips/budget`)
  - [x] Reisechronik: manuelle Einträge (`source=manual`)
  - [x] Inline-Kosten-Editor in der Chronik (`PATCH /api/trips/{id}/cost`)
  - [x] ActualBudget + Budget-Input in Reisechronik (nicht in Geplante Reisen)
  - [x] Stats 4-Karten: Vergangen/Geplant/Wunschziele/Ausgegaben (alle 3 klickbar)
  - [x] Donut-Chart (SVG conic-gradient): Vergangen dunkelgrün / Geplant hellgrün / Frei grau / Überzogen rot
  - [x] Donut-Legende: Vergangen → Tab Chronik, Geplant → Tab Geplante Reisen
- [x] Jahr-Switcher: genau 3 Jahre (letztes/aktuelles/nächstes), Pfeile direkt selectedYear ±1
- [x] 4 Badges im Header: ✈️ Geplant | ✅ Vergangen | 🌟 Wunschziele | Gesamt (alle klickbar)
- [x] Reisechronik: nummerierte Sync-Karten (1. Dawarich, 2. ActualBudget) mit Amber-Tipp
- [x] Dawarich: force_full Checkbox → ignorierte Trips reaktivieren
- [x] Soft-Delete: Dawarich-Trips setzen ignored=1 statt echter Delete; beim Sync übersprungen
- [x] Auto-Cost: /api/trips/auto-cost — Datum-Overlap ActualBudget Tx → Trips zuordnen
  - auto_cost_txs JSON gespeichert, Anzeige in Timeline mit 🔗-Marker
- [x] Settings: Auth-abhängige Integrationen (auth=true → Mein Bereich; auth=false → Integrationen)
- [x] ScratchMap: jsvectormap als npm-Dependency (kein CDN mehr)
  - [x] Nächste Abenteuer + Letzte Erinnerungen im Übersicht-Tab
  - [x] ScratchMap: 3 Marker-Typen (visited grün / planned blau / bucket orange)
- [x] ScratchMap: robuste CDN-Ladestrategie (poll + sequenziell)
- [x] ActualBudget 404 Fix: `/actual/transactions` Endpoint mit Feldname-Mapping
- [x] ActualBudget: `📂 Dateien auflisten` Button + Hilfe-Panel in der UI
- [x] Favicon: `favicon.svg` + `manifest.webmanifest` + `icon-192.png` + `icon-512.png`
- [x] Settings Mein Bereich: Geocoding-Suche für Home-Koordinaten (Nominatim)
- [x] FieldGuide: ActualBudget Dateiname Schritt-für-Schritt Erklärung
- [x] Onboarding: `window.location.origin` als Backend-URL Vorschlag

### Roadmap (beta)
- [ ] ScratchMap: Geocoding für planned-Trips (lat/lon aus Ortsname automatisch)
- [x] Price history chart (SVG Liniendiagramm) in PriceRadar — per-Tracker Akkordeon
- [ ] Mietwagen tab in PriceRadar (future)
- [ ] Discord webhook notifications
- [ ] Currency toggle (EUR/USD/GBP)
- [x] Donut-Chart für Budget (conic-gradient)
- [x] Auto-Cost: ActualBudget → Dawarich-Trips
- [x] Soft-Delete mit ignored-Flag
- [x] Settings auth-abhängige Tabs
- [ ] HSTS header in Zoraxy setzen
- [ ] Scratch Map: planned-Trips Koordinaten via Geocoding befüllen

### Phase 3 (future)
- [ ] Multi-user data separation fully tested
- [ ] Merge stable features to `main`
