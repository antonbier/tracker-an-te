# CLAUDE.md — WanderSuite Source of Truth (beta branch)

> Schlanker Architekt-Guide. Historische Session-Notizen → `claude_old.md`. Releases → `CHANGELOG.md`.

---

## 1. Projekt-Basics

| | |
|---|---|
| **Repo** | `antonbier/tracker-an-te` · Branch: `beta` |
| **Live-Instanz** | `wandersuite-beta.nimra89.de` |
| **Test-Login** | `claude@claude.it` / `claude_test` |
| **Stack** | Svelte 5 (Runes) + SvelteKit · FastAPI · SQLite · Docker Compose · Nginx |
| **Unraid-Pfad** | `/mnt/user/appdata/wandersuite-beta/` |

---

## 2. GitHub-API-Workflow (Claude's Methode)

Immer SHA fetchen bevor geschrieben wird. Immer `beta` Branch.

```python
# Pattern: fetch SHA → decode → edit → re-encode → PUT
def gh_get(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}?ref=beta"
    # → returns content (base64-decoded) + sha

def gh_put(path, content, sha, message):
    # PUT mit {"message", "content": base64, "sha", "branch": "beta"}
```

**Neue Datei** (kein SHA): `gh_put(path, content, sha=None, msg)` — SHA weglassen.

---

## 3. Stack & Deployment

### Network
```
Internet → Zoraxy Reverse Proxy
              ├── :8767  Nginx (Svelte SPA + /api/* Proxy → backend:8000)
              └── :8768  FastAPI (nur intern / Swagger)
```

**Backend-URL im Wizard**: Frontend-URL eintragen — `window.location.origin` wird vorausgefüllt. `/api/*`-Calls gehen über Nginx-Proxy, nie direkt ans Backend.

### Docker Build
```bash
# Update + Rebuild
git pull && BUILD_DATE="$(date '+%Y-%m-%d %H:%M')" docker compose up -d --build
```

### Wichtige .env-Werte
```env
HOST_PORT=8767 · BACKEND_PORT=8768 · TZ=Europe/Rome
AUTH_ENABLED=true
APP_SECRET=<Fernet-Key>      # Verschlüsselung der User-Credentials
JWT_SECRET=<hex-32-bytes>
WEBAUTHN_RP_ID=domain.de · WEBAUTHN_RP_NAME=WanderSuite · WEBAUTHN_ORIGIN=https://domain.de
```

---

## 4. Svelte 5 — Strikte Regeln (KRITISCH)

```svelte
<!-- ✅ RICHTIG -->
let count = $state(0);
const doubled = $derived(count * 2);
const complex = $derived.by(() => { /* Logik */ return result; });
let val = $bindable();

<!-- ❌ FALSCH -->
let count = writable(0);          // Kein Svelte 4 writable in Komponenten
$derived(() => { return x; })    // Gibt Funktion zurück → im Template mit () aufrufen (Falle!)
```

### Kritische Fallen

| Problem | Ursache | Fix |
|---------|---------|-----|
| `{@const}` Build-Error | `{@const}` nur innerhalb `{#each}` / `{#if}` erlaubt, **nie** im Template-Root | In `$derived.by()` im `<script>` verschieben |
| Tab-Buttons verlieren Event-Handler | `tabLabels = $derived.by(() => ({...}))` mit `$t()`-Calls → Re-Mount | `tabLabels = $derived({...})` (ohne `.by()`) |
| `-0 €` angezeigt | `parseFloat(...).toFixed(0)` bei 0 | Guard: `val === 0 ? '0' : '-' + val.toFixed(0)` |
| Apostroph bricht JS-String | `'Geht's los'` in einfach-gequotetem String | Double-Quotes: `"Geht's los"` |
| `$derived` Array Re-Mount | `$derived([...])` erzeugt neue Referenz → `{#each}` re-mountet | `$derived.by(() => [...])` |
| Infinite `$effect` Loop | `$effect` liest + schreibt denselben State | Intermediate Variable oder `untrack()` |

### Props & Bindable
```svelte
<!-- Komponente empfängt bindable prop -->
let { value = $bindable(), onChange } = $props();
<!-- Eltern-Nutzung -->
<Child bind:value={myVar} />
```

### DOM-Regeln
- Password-Inputs **immer** in `<form onsubmit={(e)=>{e.preventDefault();...}}>` wrappen (Browser-Passwort-Manager + keine DOM-Warnung)
- `autocomplete="current-password"` / `"new-password"` setzen

---

## 5. Datei-Struktur (Svelte)

```
svelte/src/
├── app.html                    # <title>WanderSuite</title> + meta tags
├── lib/
│   ├── stores.js               # Svelte Stores (siehe Abschnitt 6)
│   ├── api.js                  # api() Funktion mit JWT-Header
│   ├── i18n.js                 # t-Store, loadLocale()
│   └── components/
│       ├── pages/
│       │   ├── Dashboard.svelte
│       │   ├── TripHub.svelte
│       │   ├── MyTrips.svelte
│       │   ├── PriceRadar.svelte
│       │   └── Discover.svelte
│       ├── dashboard/
│       │   ├── HeroSection.svelte      # Orchestrator: 2-Kachel oder Fallback
│       │   ├── HeroPastTrip.svelte     # Nostalgie: random aus Archiv, Immich-Bild, Refresh
│       │   ├── HeroNextTrip.svelte     # Countdown: Unsplash-Bild, Urgency-Pulse
│       │   ├── TravelInspo.svelte      # 3 Quick-Action Kacheln
│       │   ├── CompactTripsList.svelte
│       │   └── CompactTrackerGrid.svelte
│       ├── triphub/
│       │   ├── WeatherWidget.svelte    # Open-Meteo, nur active/≤7d
│       │   ├── BudgetWidget.svelte     # Gesamt − Flug − Hotel − Bar = Vor-Ort
│       │   ├── ChecklistWidget.svelte  # KI-Todos, Due-Dates, Phasen-aware
│       │   ├── SlotWidget.svelte       # Tracker-Slots (A/B/C Zustand)
│       │   └── helpers.js             # destinationGradient(), wmoIcon()
│       ├── mytrips/
│       │   ├── OverviewTab.svelte
│       │   ├── TripsTab.svelte
│       │   ├── JournalTab.svelte
│       │   └── BucketListTab.svelte
│       ├── priceradar/
│       │   ├── SearchResults.svelte    # Stops-Dropdown, ✓ Gespeichert-Feedback
│       │   ├── TrackerCard.svelte      # Preisverlauf-Akkordeon, Link-Trip-Dropdown
│       │   ├── TrackerGrid.svelte
│       │   └── helpers.js             # fmtDate(), fmtRange(), chartPts(), ...
│       └── settings/
│           ├── BasicTab.svelte         # URL, Timezone, Datumsformat + Live-Preview
│           ├── NotificationsTab.svelte # Telegram (@userinfobot Tipp) + Gotify
│           ├── SchedulerTab.svelte
│           ├── MyspaceTab.svelte
│           └── AccountTab.svelte
├── locales/
│   ├── de.json · en.json · it.json · es.json
└── routes/
    ├── +layout.svelte          # Auth-Flow: Onboarding → Setup → Login → App
    └── +page.svelte
```

---

## 6. Svelte Stores (stores.js)

| Store | Typ | Zweck |
|-------|-----|-------|
| `apiUrl` | persisted | Backend-URL (localStorage `apiUrl`) |
| `lang` | persisted | Sprache (`de`/`en`/`it`/`es`) |
| `theme` | persisted | `''` / `'dark'` |
| `jwtToken` | persisted | JWT (localStorage `ws-jwt`) |
| `currentUser` | writable | `{id, email, role}` |
| `appStatus` | writable | `{auth_enabled, needs_setup}` |
| `currentPage` | writable | SPA-Routing (`'home'`/`'triphub'`/`'priceradar'`/...) |
| `activeWsTripId` | writable | TripHub-Navigation: aktive Trip-ID |
| `priceradarParams` | writable | Deep-Link von TripHub → PriceRadar |
| `trips` | writable | Dawarich/Manual-Trips (aus `/api/trips`) |
| `bucketlist` | writable | Bucket-List Items |
| `wizardOpen` | writable | SetupWizard öffnen/schließen |
| `settingsOpen` | writable | Settings-Modal |

**`loadSettingsFromBackend(baseUrl)`**: Sendet JWT-Header (`ws-jwt` aus localStorage) → kein 401.

---

## 7. i18n — Konventionen

- **4 Sprachen**: DE · EN · IT · ES (`svelte/src/locales/*.json`)
- **Neue Keys**: Immer in alle 4 Dateien gleichzeitig einfügen
- **Anker-Pattern**: Key nach dem alphabetisch nächsten existierenden Key einfügen
- **Kein Hardcoding**: Tab-Labels, Status-Texte, Fehlermeldungen immer via `$t('key')`
- **Tabs**: `tabIds = $derived([...])` mit i18n-Labels — **nie** `$derived.by()` (Re-Mount-Bug)

---

## 8. API-Endpunkte (Wichtigste)

### WS-Trips (WanderWizzard-Reisen)
| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/api/ws-trips` | Alle WS-Trips des Users |
| POST | `/api/ws-trips` | Trip anlegen |
| PATCH | `/api/ws-trips/{id}` | Trip updaten |
| DELETE | `/api/ws-trips/{id}?mode=trip_only\|all` | Löschen (Tracker behalten oder mitlöschen) |
| GET | `/api/ws-trips/{id}/trackers` | Verknüpfte Tracker |
| POST | `/api/ws-trips/{id}/todos/regenerate` | KI-Todos neu generieren |
| PATCH | `/api/ws-trips/{id}/manual-expenses` | Barausgaben setzen |
| GET | `/api/ws-trips/{id}/budget` | Budget-Breakdown |

### Settings
| Method | Path | Beschreibung |
|--------|------|-------------|
| GET/POST | `/api/settings` | Global (Admin): SerpAPI, Gemini, OpenAI |
| GET/POST | `/api/settings/user` | Per-User: Dawarich, Immich, ActualBudget, Home |
| POST | `/api/settings/wizard/step` | Wizard-Save (partial, nie überschreibt) |
| GET | `/api/settings/geocode?q=` | Nominatim-Proxy (CORS-safe) |
| GET | `/api/settings/providers` | Provider-Toggle-Liste |

### Discovery & Bilder
| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/api/discovery/trip-image?destination=X` | Immich (wenn visited) oder Unsplash |
| GET | `/api/discovery/image-proxy?url=` | CORS-Proxy für Immich + Unsplash |

### Suche & Tracker
| Method | Path | Beschreibung |
|--------|------|-------------|
| POST | `/api/search/flights\|hotels\|camping` | Meta-Suche (alle Provider parallel) |
| GET | `/api/trackers` | Ryanair-Tracker |
| POST | `/api/trackers` | Tracker speichern |
| GET | `/api/google-flights` | Google-Flights-Tracker |
| GET | `/api/accommodations/homair` | Camping-Tracker |
| GET | `/api/accommodations/booking` | Hotel-Tracker |
| PATCH | `/api/{type}/{id}/link-trip` | Tracker mit WS-Trip verknüpfen |

---

## 9. Datenbank — Schema (Aktuell)

### Kern-Tabellen
```sql
-- WanderWizzard Reisen
CREATE TABLE ws_trips (
    id           INTEGER PRIMARY KEY,
    user_id      INTEGER NOT NULL DEFAULT 1,
    title        TEXT,
    destination  TEXT,
    start_date   TEXT,
    end_date     TEXT,
    trip_type    TEXT DEFAULT 'flight',
    travel_mode  TEXT DEFAULT 'flight',
    status       TEXT DEFAULT 'planning',   -- planning|booked|completed
    budget       REAL,
    manual_expenses REAL DEFAULT 0,
    adults       INTEGER DEFAULT 2,
    children     INTEGER DEFAULT 0,
    home_airport TEXT,
    vibes        TEXT,                      -- JSON Array
    path         TEXT DEFAULT 'known'
);

-- Dawarich / Manuell erfasste Trips (Reisechronik)
CREATE TABLE detected_trips (
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER NOT NULL DEFAULT 1,
    name       TEXT,
    start_date TEXT, end_date TEXT,
    location_name TEXT, country TEXT,
    lat REAL, lon REAL,
    nights INTEGER, cost REAL, auto_cost REAL,
    source TEXT DEFAULT 'dawarich',         -- dawarich|manual
    ignored INTEGER DEFAULT 0,             -- soft-delete für Dawarich-Trips
    auto_cost_txs TEXT                     -- JSON
);

-- Tracker (alle 4 Typen haben: id, user_id, trip_id, is_booked, booked_price, wish_price, booking_url)
CREATE TABLE trackers (          -- Ryanair Flüge
    id INTEGER PRIMARY KEY, user_id INTEGER, trip_id INTEGER,
    origin TEXT, destination TEXT, outbound_date TEXT, return_date TEXT,
    adults INTEGER, children INTEGER, baggage_json TEXT, seat_cost REAL,
    is_booked INTEGER DEFAULT 0, booked_price REAL, wish_price REAL, booking_url TEXT
);
-- gf_trackers (Google Flights), homair_trackers (Camping), booking_trackers (Hotels) — analog

-- Preisverlauf
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
    tracker_type TEXT,   -- flight|google_flight|hotel|camping
    tracker_id INTEGER, price REAL, currency TEXT DEFAULT 'EUR',
    provider TEXT, status TEXT DEFAULT 'ok', fetched_at TEXT DEFAULT (datetime('now'))
);

-- User-Einstellungen (per User)
CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY,
    dawarich_url TEXT, dawarich_token TEXT,
    actual_url TEXT, actual_token TEXT, actual_file TEXT,
    immich_url TEXT, immich_api_key TEXT, immich_geo_sync TEXT,
    home_lat TEXT, home_lon TEXT, home_name TEXT,
    travel_categories TEXT,
    timezone TEXT, date_format TEXT,
    ww_adults INTEGER, ww_children INTEGER, ww_home_airport TEXT,
    -- Gepäck, Zeitfenster, Reisepräferenzen ...
    unsplash_key TEXT
);

-- Verschlüsselte Notification-Credentials (Fernet)
CREATE TABLE user_notification_settings (
    user_id INTEGER PRIMARY KEY,
    telegram_bot_token TEXT,   -- Fernet-verschlüsselt
    telegram_chat_id TEXT,     -- Fernet-verschlüsselt
    gotify_url TEXT,           -- Fernet-verschlüsselt
    gotify_app_token TEXT      -- Fernet-verschlüsselt
);

-- Bucket List
CREATE TABLE ws_bucketlist (
    id INTEGER PRIMARY KEY, user_id INTEGER,
    item TEXT, dest TEXT, done INTEGER DEFAULT 0, created TEXT
);

-- Budget pro Jahr (detected_trips Reisechronik)
CREATE TABLE budget_years (
    user_id INTEGER, year INTEGER, amount REAL,
    PRIMARY KEY (user_id, year)
);
```

---

## 10. Security

### CSP (nginx.conf — aktuell)
```
default-src 'self';
script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
style-src-elem 'self' 'unsafe-inline' https://fonts.googleapis.com;
img-src 'self' data: https://images.unsplash.com https://picsum.photos https://*.unsplash.com;
connect-src 'self' https://geocoding-api.open-meteo.com https://api.open-meteo.com;
font-src 'self' https://fonts.gstatic.com;
manifest-src 'self'; worker-src 'self';
```

**TODO Zoraxy**: `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`

### Auth-Flow
```
+layout.svelte → api('/api/status')
  → needs_setup=true  → Setup.svelte (Admin-Account anlegen)
  → auth_enabled=true, kein JWT → Login.svelte (Passwort oder Passkey)
  → ok → AppShell
```

### Passkey (WebAuthn)
- `_get_rp(request)`: 1) Env-Vars → 2) HTTP Origin-Header → 3) localhost Fallback
- **Nie** `x-forwarded-host` nutzen (kann leer sein → Bug)
- `Cross-Origin-Opener-Policy: same-origin` in Nginx zwingend für WebAuthn

### Fernet-Verschlüsselung
```python
# backend/settings_manager.py
from cryptography.fernet import Fernet
def encrypt(value): return Fernet(APP_SECRET).encrypt(value.encode()).decode()
def decrypt(value): return Fernet(APP_SECRET).decrypt(value.encode()).decode()
```
Verschlüsselt: Telegram Bot Token/Chat ID, Gotify URL/Token.
Frontend erhält immer `"••••••••"` (nie Klartext).

---

## 11. Dashboard — Hero-System

### Layout-Logik (HeroSection.svelte)
```
archivedWsTrips (end_date < heute ODER start_date < heute wenn kein end_date)
nextWsTrip      (status = planning|booked, erster)

Beide vorhanden  → grid-cols-1 sm:grid-cols-2 (HeroPastTrip | HeroNextTrip)
Nur next         → HeroNextTrip (volle Breite)
Nur past         → HeroPastTrip (volle Breite)
Keiner           → Willkommen-Banner + WanderWizzard-CTA
```

### HeroPastTrip
- Props: `archivedTrips[]`, `ongoToHub(trip)`
- Random-Start via `onMount`, `nextTrip()` = `(index+1) % length`
- Image-Cache-Key: `ws-img-past-{destination}-{startDate}` (sessionStorage)
- Reiselust-Modus: `daysAgo > 180`

### HeroNextTrip
- Props: `trip`, `ongoToHub`
- Image-Cache-Key: `ws-img-next-{destination}` (sessionStorage)
- Urgency-Pulse: `daysUntil <= 7`

---

## 12. TripHub — 3-Phasen-Lifecycle

```
phase = $derived.by(() => {
    if (today < start_date)              return 'planning';
    if (today >= start_date && today <= end_date) return 'active';
    return 'archived';
});
```

| Phase | Hero-Gradient | Aktionen |
|-------|--------------|---------|
| planning | Dunkelblau-Orange | Slots (Flug/Hotel suchen), Checkliste editierbar |
| active | Grün | Wetter-Widget, alle Widgets |
| archived | Gedämpft/Desaturiert | Read-Only, Todos Regen möglich |

### Slot-Zustände (SlotWidget)
- **A** (kein Tracker): "Flug suchen" → `priceradarParams.set({...}); currentPage.set('priceradar')`
- **B** (Tracker aktiv): Preis + "Buchen ↗" + "Als gebucht markieren"
- **C** (is_booked=1): Grün-Border, `booked_price`, "↩ zurücksetzen"

### Budget-Breakdown
```
Gesamtbudget  - booked_flight - booked_hotel - manual_expenses = Vor-Ort-Budget
```

---

## 13. PriceRadar — Architektur

### Wichtigste Regel
**"Suchen" ≠ "Tracken"** — Klick auf Suchen erzeugt keinen DB-Eintrag. Erst `[ + Als Tracker speichern ]` schreibt.

### Deep-Link von TripHub
```js
priceradarParams.set({
    destination, dateFrom, dateTo, adults, children, homeAirport,
    _fromTripHub: trip.id,
    _searchType: 'flight' | 'hotel' | 'camping'
});
currentPage.set('priceradar');
```
PriceRadar liest Store via `$effect`, setzt `activeCategory` + `prefillParams`.

### fmtDate() — zentrale Datumsformatierung
```js
// svelte/src/lib/components/priceradar/helpers.js
export function fmtDate(iso) {
    // Liest 'ws-date-format' aus localStorage
    // Gibt DD.MM.YYYY | MM/DD/YYYY | YYYY-MM-DD zurück
}
```
**Überall** verwenden: TripCard, TripHub, BucketList, TrackerCard, Hero-Komponenten.

---

## 14. MyTrips — Struktur

### Tabs (strikt in dieser Reihenfolge)
`overview` | `planned` | `ontour` | `archive` | `bucketlist`

### Archiv-Filter (archivedWsTrips)
```js
wsTrips.filter(t => {
    const e = (t.end_date || '').slice(0,10);
    const s = (t.start_date || '').slice(0,10);
    if (e) return e < today;
    return s && s < today;  // kein end_date → nach start_date archiviert
});
```

---

## 15. Bekannte Bugs / Tech Debt

| # | Komponente | Problem | Priorität |
|---|-----------|---------|----------|
| 1 | HeroPastTrip | Immich-Bild erscheint nicht wenn Immich nicht konfiguriert (kein Fallback-Hinweis) | niedrig |
| 2 | WanderWizzard | Auto-Reise-Modus (KI-Vorschläge) noch nicht vollständig implementiert | mittel |
| 3 | PriceRadar | Mietwagen-Tab zeigt nur "Coming Soon" | niedrig |
| 4 | Zoraxy | HSTS-Header muss manuell gesetzt werden | mittel |
| 5 | HeroNextTrip | Wenn kein Unsplash-Key → kein Bild, kein Hinweis | niedrig |

---

## 16. Komponenten-Abhängigkeiten (Key Imports)

```
Dashboard.svelte
    └── HeroSection.svelte
            ├── HeroPastTrip.svelte  (→ fmtDate, api, apiUrl)
            └── HeroNextTrip.svelte  (→ fmtDate, api, apiUrl)

TripHub.svelte (reiner Container)
    ├── WeatherWidget.svelte
    ├── BudgetWidget.svelte
    ├── ChecklistWidget.svelte
    └── SlotWidget.svelte

PriceRadar.svelte
    ├── SearchResults.svelte   (→ helpers.js: fmtDate, overnightSuffix, parseJsonField)
    ├── TrackerGrid.svelte
    │   └── TrackerCard.svelte (→ helpers.js)
    ├── FlightSearchForm.svelte
    ├── HotelSearchForm.svelte
    └── CampingSearchForm.svelte

Settings.svelte (Orchestrator)
    ├── BasicTab.svelte        ($derived für Live-Preview, kein {@const} im Template!)
    ├── NotificationsTab.svelte
    ├── SchedulerTab.svelte
    ├── MyspaceTab.svelte
    │   ├── MyspaceDefaults.svelte
    │   ├── MyspaceConnections.svelte
    │   ├── MyspaceProviders.svelte
    │   └── MyspaceAI.svelte
    └── AccountTab.svelte
```
