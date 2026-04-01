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

**Backend URL für User:** Im Onboarding-Wizard die **frontend URL** eintragen.
`window.location.origin` wird automatisch als Vorschlag vorausgefüllt.

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
# rp_id + origin werden automatisch aus HTTP Origin-Header abgeleitet.
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

`_get_rp(request)` wird bei jedem Passkey-Call aufgerufen:

1. **Env-Vars explizit gesetzt** (`WEBAUTHN_RP_ID != "localhost"`) → direkt verwenden
2. **Origin-Header** (Browser sendet bei jedem POST) → `hostname` als `rp_id`
3. **Fallback** → Env-Vars (localhost defaults)

⚠️ Nie `x-forwarded-host` für rp_id verwenden — kann leer sein → `"http://"` → bug.

---

## i18n System

**Dateien:** `svelte/src/locales/de.json`, `en.json`, `it.json`
**Store:** `svelte/src/lib/i18n.js` — reaktiver `t`-Store, `$t('key')` in Komponenten

Alle Bereiche vollständig übersetzt (DE/EN/IT):
Navigation, Settings, Dashboard, MyTrips, PriceRadar, Discover, Onboarding, Login, Setup.

**Regel:** Immer alle 3 Locale-Dateien gleichzeitig updaten. Tabs nie hardcodiert.

---

## PWA / Favicon

- `svelte/static/favicon.svg` — oranges Rund-Rechteck (#D95D39) mit Kompassrose
- `svelte/static/manifest.webmanifest` — PWA-Manifest
- `svelte/static/icons/icon-192.png` + `icon-512.png` — generiert mit Pillow

---

## MyTrips — Architektur & UX

### Tab-Reihenfolge (strikt)
| # | ID | Label |
|---|----|----|
| 1 | `overview` | 📊 Übersicht |
| 2 | `trips` | ✈️ Geplante Reisen |
| 3 | `journal` | 📓 Reisechronik |
| 4 | `bucketlist` | 🌟 Bucket List |

### Grid-Layout (alle Tabs außer Übersicht)
`grid grid-cols-1 lg:grid-cols-3 gap-5`
- `lg:col-span-1` — Formular / Aktionen (links)
- `lg:col-span-2` — Liste / Timeline (rechts)

### Globaler Sync-Button (Header)
- Rund, Icon-only (SVG Refresh-Icon), neben dem Titel
- Triggert `syncJournal()` + `syncActual()` nacheinander
- State: `globalSyncing` → zeigt Spin-Indikator

### Jahr-Switcher
- Zeigt nur Jahre mit Daten + aktuelles Jahr
- `availableYears()` als `$derived` — sammelt aus `$trips`, `journalTrips`, `budgetByYear`
- Alle Views **strikt** nach `selectedYear` gefiltert (kein Year-Leak zwischen Tabs)

### Badge-Logik (Header oben rechts)
- `upcomingCount` = `$trips.filter(dateStart >= today).length`
- `totalCount` = `upcomingCount + journalTrips.length`
- Anzeige: `✈️ X geplant` (klickbar → Tab `trips`) + `Y gesamt`

### Übersicht-Tab Stats-Karte
Erste Stat-Karte ist **geteilt** (kein einzelner Wert):
- Links: `X Vergangen` → klickbar → `activeTab = 'journal'`
- Rechts: `Y Geplant` → klickbar → `activeTab = 'trips'`

### Übersicht-Tab Listen
- **Nächste Abenteuer** (upcoming, aufsteigend sortiert, max. 4)
- **Letzte Erinnerungen** (journalYear, absteigend sortiert, max. 4)
- Beide mit "X weitere →" Link zum entsprechenden Tab

### Budget
- Pro Jahr im Backend gespeichert: `PUT /api/trips/budget` `{ year, amount }`
- `GET /api/trips/budget` → `{ "2024": 3000, "2025": 4500 }`
- Legacy-Fallback: liest alten `ws-budget` Wert für aktuelles Jahr
- Budget-Input **in der Reisechronik** (wo echte Kosten anfallen)

### ActualBudget Sync
- **In der Reisechronik** (Tab 3), nicht in Geplante Reisen
- Importiert vergangene Transaktionen aus ActualBudget

### Dawarich Sync
- In der Reisechronik (linke Spalte, unter dem Formular)
- Lädt GPS-Trips vom Dawarich-Server, erkennt Übernacht-Reisen

### Reisechronik (Tab 3) — Datenquellen
- **Dawarich-Trips** (source=`dawarich`): automatisch erkannt, orange Timeline-Dot
- **Manuelle Einträge** (source=`manual`): violetter Timeline-Dot, `manuell`-Badge
- Alle in `/api/trips` gespeichert (Backend, pro User)
- Inline-Kosten-Editor: Klick auf "💶 Kosten hinterlegen" → Input → Enter/✓

---

## ScratchMap.svelte

**Props:**
- `journalTrips` — Chronik-Trips (Dawarich + manuell)
- `plannedTrips` — geplante Trips (aus localStorage `trips`-Store)
- `selectedYear` — aktuell gewähltes Jahr

**Marker-Typen & Farben:**
| Typ | Quelle | Farbe | Symbol |
|-----|--------|-------|--------|
| `visited` | journalTrips, Jahr gefiltert | `#2d6a4f` grün | ● |
| `planned` | plannedTrips, Jahr gefiltert | `#2563eb` blau | ● |
| `bucket` | $bucketlist (kein Jahresfilter) | `#c4622d` orange | ● |

**Jahr-Filter:** visited + planned werden nach `selectedYear` gefiltert.
Bucket List hat kein fixes Jahr → immer angezeigt.

**Ladelogik:** Container immer im DOM (kein conditional rendering).
Sequenzieller CDN-Load: CSS → jsvectormap.min.js → world.js (mit 80ms delay zwischen den Schritten).
`setTimeout(..., 120)` vor Init damit Container gerendert ist.

**Fallback-Demos** wenn keine echten Daten vorhanden:
- Demo visited: Salzburg, Rom, Paris
- Demo planned: London
- Demo bucket: Tokyo, Machu Picchu

---

## Backend API — /api/trips (neu)

| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/api/trips` | Alle Trips (dawarich + manual), pro User |
| POST | `/api/trips` | Manuellen Trip anlegen |
| PATCH | `/api/trips/{id}/cost` | Kosten eines Trips updaten |
| DELETE | `/api/trips/{id}` | Trip löschen |
| GET | `/api/trips/budget` | Budget nach Jahr `{"2024":3000}` |
| PUT | `/api/trips/budget` | Budget für Jahr setzen `{year, amount}` |

**DB-Migration:** `detected_trips` hat neue Spalten `cost REAL` und `notes TEXT`.
`source` unterscheidet `dawarich` vs `manual` (eigener Duplicate-Check pro Source).

---

## Multi-User Architecture

### Settings Split
- **Global** `GET/POST /api/settings` — SerpAPI, Gemini, OpenAI, Telegram, Gotify
- **Per-user** `GET/POST /api/settings/user` — Dawarich, ActualBudget, Home coords

### AUTH_ENABLED=false (guest mode)
- Returns `GUEST_USER = {id: 0, role: "admin"}`
- Fully backward compatible

---

## Security Headers (nginx.conf)

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Content-Security-Policy: default-src 'self' ...`
- `Cross-Origin-Opener-Policy: same-origin` (required for WebAuthn)

**TODO — set in Zoraxy:**
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`

---

## File Structure

```
wandersuite/
├── svelte/src/
│   ├── lib/
│   │   ├── stores.js          ← all state
│   │   ├── api.js             ← HTTP client with JWT injection
│   │   ├── i18n.js            ← reactive t() derived store
│   │   └── components/
│   │       ├── AppShell.svelte
│   │       ├── Header.svelte  ← BETA badge + version
│   │       ├── Sidebar.svelte
│   │       ├── Login.svelte
│   │       ├── Setup.svelte
│   │       ├── Settings.svelte ← tabs: basic/integrations/apis/notifications/myspace/account/admin
│   │       ├── PasskeyManager.svelte
│   │       ├── FieldGuide.svelte
│   │       ├── ScratchMap.svelte ← jsvectormap, 3 Marker-Typen, Jahr-Filter
│   │       └── pages/
│   │           ├── Dashboard.svelte
│   │           ├── PriceRadar.svelte
│   │           ├── MyTrips.svelte ← Tabs: overview/trips/journal/bucketlist
│   │           └── Discover.svelte
│   ├── locales/
│   │   ├── de.json
│   │   ├── en.json
│   │   └── it.json
│   └── routes/
│       ├── +layout.svelte
│       └── +page.svelte
├── svelte/static/
│   ├── favicon.svg
│   ├── manifest.webmanifest
│   └── icons/icon-192.png, icon-512.png
├── backend/
│   ├── main.py
│   ├── database.py            ← detected_trips mit cost/notes/source
│   ├── auth_db.py
│   ├── auth_jwt.py
│   ├── settings_manager.py
│   ├── dawarich.py
│   └── routes/
│       ├── auth.py
│       ├── passkey.py         ← _get_rp() auto-detection
│       ├── settings.py
│       ├── trips.py           ← /api/trips unified endpoint
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
url = f'https://api.github.com/repos/{REPO}/contents/{path}?ref=beta'
body = {'message': msg, 'content': base64_content, 'branch': 'beta', 'sha': sha}
```

---

## Open / Next Steps

### Erledigt
- [x] Passkeys: rp_id auto-detection via Origin-Header
- [x] i18n: alle Bereiche DE/EN/IT
- [x] Favicon + PWA (manifest, icons)
- [x] Settings: Geocoding für Home-Koordinaten (Nominatim)
- [x] MyTrips: komplettes UX-Redesign
  - [x] Tab-Reihenfolge: Übersicht → Geplant → Chronik → Bucket List
  - [x] Globaler Sync-Button (Dawarich + ActualBudget)
  - [x] Jahres-Switcher mit striktem Filter
  - [x] Budget pro Jahr im Backend
  - [x] Reisechronik: manuelle Einträge + inline Kosten-Editor
  - [x] ActualBudget + Budget-Input in Reisechronik
  - [x] Split-Stats (Vergangen/Geplant, klickbar)
  - [x] ScratchMap: 3 Marker-Typen (visited/planned/bucket)
  - [x] Nächste Abenteuer + Letzte Erinnerungen im Übersicht-Tab

### Roadmap (beta)
- [ ] Scratch Map: Geocoding für planned-Trips (lat/lon aus Ortsname)
- [ ] Price history chart (Chart.js) in PriceRadar
- [ ] Mietwagen tab in PriceRadar
- [ ] Discord webhook notifications
- [ ] Currency toggle (EUR/USD/GBP)
- [ ] HSTS header in Zoraxy

### Phase 3 (future)
- [ ] Multi-user data separation fully tested
- [ ] Merge stable features to `main`
