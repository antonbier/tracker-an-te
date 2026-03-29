# CLAUDE.md — WanderSuite AI Assistant Context

Full architecture reference for AI assistants working on this codebase.
Update after significant changes.

**Repository:** `antonbier/tracker-an-te`  
**Live URL:** `https://wander-epoch-69vc.here.now`  
**Stack:** FastAPI backend · Nginx + Vanilla JS frontend · SQLite · Docker Compose  
**Deployment:** here.now (static frontend via GitHub Action on push to main) + backend on host/Railway

---

## File Structure

```
wandersuite/
├── frontend/
│   ├── index.html         ← SPA: all HTML + CSS (~3300 lines, no build step)
│   ├── manifest.json      ← PWA: standalone, PNG icons, shortcuts
│   ├── sw.js              ← Service Worker: network-first, pre-caches app shell
│   ├── _headers           ← Static host MIME type hints (here.now)
│   ├── icons/             ← PWA icons: icon-192.png, icon-512.png
│   ├── locales/           ← i18n JSON: de.json, en.json, it.json (~300 keys each)
│   └── js/
│       ├── main.js        ← Entry point: static imports + window.* + DOMContentLoaded
│       ├── core/
│       │   ├── state.js   ← Global mutable state + setter functions
│       │   ├── api.js     ← HTTP client api() + checkApiStatus()
│       │   └── persist.js ← localStorage ↔ backend sync (ws-trips, ws-budget, ws-bucketlist)
│       ├── ui/
│       │   ├── i18n.js       ← loadLocale, t(), applyTranslations, setLang
│       │   ├── nav.js        ← navigate(), bnMap, sidebar, bottom bar, View Transitions
│       │   ├── toast.js      ← toast(msg, type)
│       │   ├── settings.js   ← 4-tab slide-panel: basic|integrations|apis|notifications
│       │   ├── priceradar.js ← switchRadarCategory(), switchRadarSubTab()
│       │   ├── tabs.js       ← switchMyTripsTab()
│       │   └── fieldguide.js ← openFieldGuide(), closeFieldGuide(), switchFieldGuideTab()
│       └── app/
│           ├── ryanair.js     ← Ryanair CRUD + Chart.js + Discover/AI
│           ├── budget.js      ← Budget + ActualBudget + expense table
│           ├── dashboard.js   ← Home dashboard + Meine Reisen live stats
│           ├── scratchmap.js  ← initScratchMap(), loadScratchMap() (jsvectormap)
│           ├── googleflights.js
│           ├── homair.js
│           ├── booking.js
│           ├── journal.js     ← Dawarich sync + trip list
│           ├── onboarding.js  ← 3-step full-screen wizard + checkConnection()
│           └── bucketlist.js  ← Bucket list (localStorage + backend sync)
│
├── backend/
│   ├── main.py            ← FastAPI entry point + APScheduler (07:00 TZ)
│   ├── database.py        ← SQLite schema + CRUD (all tables)
│   ├── settings_manager.py← AES-Fernet encrypted settings (16 SETTING_KEYS)
│   ├── notifications.py   ← send_telegram(), send_gotify(), notify_price_drop()
│   ├── scraper.py         ← Ryanair API scraper
│   ├── google_scraper.py  ← Google Flights via SerpAPI
│   ├── homair_scraper.py  ← Homair via SerpAPI Google Hotels
│   ├── booking_scraper.py ← Booking via SerpAPI
│   ├── dawarich.py        ← Trip detection algorithm + Nominatim geocoding
│   ├── countries.py       ← Country name → ISO-2 mapping (100+ entries, DE/EN/IT)
│   ├── actual_budget.py   ← ActualBudget client (actualpy ≥ 0.21.0)
│   ├── gemini.py          ← Google Gemini AI
│   ├── openai_client.py   ← OpenAI gpt-4o-mini
│   ├── scheduler.py       ← Daily batch + price-drop notification trigger
│   └── routes/
│       ├── trackers.py       ← /api/trackers (Ryanair CRUD)
│       ├── prices.py         ← /api/prices
│       ├── google_flights.py ← /api/google-flights
│       ├── accommodations.py ← /api/accommodations/homair + /booking
│       ├── budget.py         ← /api/budget/actual/*
│       ├── dawarich.py       ← /api/dawarich/* (incl. /countries)
│       ├── discover.py       ← /api/discover
│       ├── settings.py       ← /api/settings + /serpapi-quota
│       ├── dashboard.py      ← /api/dashboard/stats
│       ├── userdata.py       ← /api/userdata/* (ws-trips, ws-budget, ws-bucketlist)
│       └── notifications.py  ← /api/notifications/test-telegram + test-gotify
│
├── docker/
│   ├── Dockerfile         ← Python 3.12-slim + curl; creates /app/data
│   └── nginx.conf         ← Explicit locations: /sw.js, /manifest.json, /icons/, /js/
├── docker-compose.yml     ← HOST_PORT, BACKEND_PORT, TZ, DATA_DIR, APP_SECRET
├── .env.example           ← Template with all variables + comments
└── .github/workflows/deploy-frontend.yml  ← Deploys frontend/ to here.now on push
```

---

## Frontend Architecture

### ES Module Pattern

All JS in native ES Modules — no bundler, no npm, browser loads directly.

**`window.*` binding rule:** Every function called from `onclick="fn()"` in HTML must be bound in `main.js`:
```js
import { addTracker } from './app/ryanair.js';
window.addTracker = addTracker;
```

**Circular import avoidance:** Use dynamic `import()` inside functions:
```js
// journal.js needs openSettings() but can't static-import (cycle risk)
const { openSettings } = await import('../ui/settings.js');
```

### State Management (`core/state.js`)

Named `let` exports + setter functions. Never reassign across module boundary:
```js
export let API_URL = '';
export function setApiUrl(val) { API_URL = val; }
```

### Data Persistence (`core/persist.js`)

localStorage is the runtime store. Backend is the durable backup:
```
ws-trips / ws-budget / ws-bucketlist
  → syncToBackend(key)   — fire-and-forget PUT after every mutation
  → restoreFromBackend() — cold start: fills localStorage if empty
```

Trigger points:
- `setTrips()` in `state.js` → `syncToBackend('ws-trips')`
- `updateBudget()` in `budget.js` → `syncToBackend('ws-budget')`
- `save()` in `bucketlist.js` → `syncToBackend('ws-bucketlist')`
- `DOMContentLoaded` in `main.js` → `restoreFromBackend()`

### Page/DOM Architecture

All pages are `<div class="page" id="page-*">`. `navigate(page)` switches by toggling `.active`.

**Two-level nesting (original page divs preserved in hidden `aria-hidden` container):**
```
page-priceradar → radar-sub-ryanair, radar-sub-google, radar-sub-homair, radar-sub-booking
page-mytrips   → mytrips-panel-overview (Scratch Map), mytrips-panel-bucketlist, mytrips-panel-journal, mytrips-panel-budget
[hidden aria-hidden] → page-ryanair, page-google, page-homair, page-booking, page-journal, page-budget
```
The hidden legacy pages keep JS DOM targets intact — never remove them.

### Navigation Flow
```
🧭 navigate('home')        → loadDashboard()
🎯 navigate('priceradar')  → switchRadarCategory('overview')
✨ navigate('discover')
🎒 navigate('mytrips')     → switchMyTripsTab('overview') → loadMyTripsDashboard() + loadScratchMap()
```

### Lazy Loading

Content loaded on demand via dynamic imports in `nav.js`:
```js
if (page === 'mytrips') import('../ui/tabs.js').then(m => m.switchMyTripsTab('overview'));
```

---

## CSS Architecture

All CSS in `index.html` inside a single `<style>` block.

### CSS Variables (Light / Dark)

| Variable | Light | Dark "Mitternacht" |
|----------|-------|-------------------|
| `--bg` | `#f9f8f6` | `#12141c` |
| `--surface` | `#ffffff` | `#1e212b` |
| `--surface2` | `#f2f0ec` | `#252837` |
| `--border` | `#e2ddd6` | `#323647` |
| `--text` | `#1a1612` | `#eceef5` |
| `--accent` | `#D95D39` | `#D95D39` ← unchanged |
| `--accent2` | `#1E3A5F` | `#6aaddc` |
| `--green` | `#2A5C45` | `#4dac7a` |

Dark mode is opt-in via `body.dark-mode`. Component-level overrides exist for `.header`, `.sidebar`, `.card`, inputs, panels.

### Key CSS Patterns

| Class/ID | Purpose |
|----------|---------|
| `.radar-pills` / `.radar-pill` | Main pill tab navigation |
| `.radar-subnav` / `.radar-subtab` | Secondary sub-tabs |
| `.tracker-item` | Ticket-style card with left accent stripe (`::before`) |
| `#settingsBackdrop .modal` | Slides in from right via `translateX` |
| `#fieldGuideBackdrop .modal` | Same slide pattern |
| `#onboardingBackdrop` | Full-screen overlay (no `.modal-backdrop` class) |
| `.ob-*` | Onboarding wizard elements |
| `.fg-*` | Field Guide content classes |
| `.notif-segmented` / `.notif-seg-btn` | Telegram/Gotify segmented control |
| `.btn-test-notif` / `.notif-result` | Notification test button + result area |
| `#scratch-map-container` | jsvectormap world map container |
| `.bottom-nav` | `display:none` default, `flex` at `< 900px` |

---

## Backend Conventions

### Encrypted Settings (`settings_manager.py`)

All 16 `SETTING_KEYS` stored AES-Fernet encrypted in SQLite `settings` table:
```python
SETTING_KEYS = [
    "serpapi_key", "gemini_key", "openai_key",
    "dawarich_url", "dawarich_token",
    "actual_url", "actual_token", "actual_file",
    "llm_provider", "timezone", "home_lat", "home_lon",
    "travel_categories",
    "telegram_bot_token", "telegram_chat_id",
    "gotify_url", "gotify_token",
]
```

Read with `get_setting_value(key)` anywhere in the backend.

### Notification System (`notifications.py`)

```python
send_telegram(message: str) -> bool      # HTML-formatted, uses telegram_bot_token + telegram_chat_id
send_gotify(title, message, priority) -> bool  # uses gotify_url + gotify_token
notify_price_drop(tracker, old_price, new_price)  # called by scheduler
```

Price-drop trigger in `scheduler.py`: when `new_price < previous_price` → `notify_price_drop()`.

### User Data (`routes/userdata.py`)

Stores client-side data that previously lived only in localStorage:
- Allowed keys: `ws-trips`, `ws-budget`, `ws-bucketlist`
- Values stored as JSON strings in `user_data` table (unencrypted — not secrets)
- Routes: `GET /api/userdata`, `GET /api/userdata/{key}`, `PUT /api/userdata/{key}`

### ActualBudget Notes

- Library: `actualpy` ≥ 0.21.0
- Auth field: `actual_token` = server password (not a token)
- Budget identifier: `actual_file` = display name shown top-left in ActualBudget
- Date format: `YYYYMMDD` integer

### Dawarich Trip Detection

1. Fetch GPS points (paginated), 2. Haversine > 50 km from home, 3. Group by date,
4. 2+ consecutive nights = trip, 5. Merge groups with ≤ 2-day gap, 6. Nominatim geocoding,
7. Store `location_name`, `country` (full name) → `countries.py` maps to ISO-2 for Scratch Map.

---

## Settings Panel (4 Tabs)

| Tab ID | `switchTab()` arg | Content |
|--------|-------------------|---------|
| Allgemein | `'basic'` | Backend URL, timezone, dark mode toggle |
| Integrationen | `'integrations'` | Dawarich, ActualBudget |
| APIs & KI | `'apis'` | SerpAPI, Gemini, OpenAI |
| 🔔 Alerts | `'notifications'` | Telegram (token + chat ID + test) / Gotify (URL + token + test) |

Notification sub-tabs: `switchNotifTab('telegram')` / `switchNotifTab('gotify')`  
Test buttons call `testTelegram()` / `testGotify()` → save keys first → `POST /api/notifications/test-*` → show result inline.

Security: after `saveSettings()`, these keys are **removed from localStorage**:  
`s-serpApiKey`, `s-geminiKey`, `s-openaiKey`, `s-dawarichToken`, `s-actualPassword`, `s-telegramToken`, `s-gotifyToken`

---

## localStorage Keys

| Key | Type | Backend backup | Description |
|-----|------|----------------|-------------|
| `apiUrl` | string | ✗ | Backend URL |
| `lang` | string | ✗ | `'de'` · `'en'` · `'it'` |
| `theme` | string | ✗ | `'dark'` (absent = light) |
| `ws-budget` | string | ✅ `/api/userdata/ws-budget` | Budget total in EUR |
| `ws-trips` | JSON | ✅ `/api/userdata/ws-trips` | `[{name, cost, date, source?}]` |
| `ws-bucketlist` | JSON | ✅ `/api/userdata/ws-bucketlist` | `[{id, dest, when, emoji, added}]` |
| `ws-onboarding-done` | string | ✗ | `'1'` when completed |
| `s-timezone` | string | ✅ encrypted DB | Timezone |
| `s-dawarichUrl` | string | ✅ encrypted DB | Dawarich server URL |
| `s-dawarichToken` | string | ✅ encrypted DB → **cleared after sync** | Dawarich token |
| `s-homeLat` / `s-homeLon` | string | ✅ encrypted DB | Home coordinates |
| `s-actualUrl` | string | ✅ encrypted DB | ActualBudget URL |
| `s-actualPassword` | string | ✅ encrypted DB → **cleared after sync** | ActualBudget password |
| `s-actualFile` | string | ✅ encrypted DB | Budget display name |
| `s-travelCategories` | string | ✅ encrypted DB | Comma-separated categories |
| `s-serpApiKey` | string | ✅ encrypted DB → **cleared after sync** | SerpAPI key |
| `s-geminiKey` | string | ✅ encrypted DB → **cleared after sync** | Gemini key |
| `s-openaiKey` | string | ✅ encrypted DB → **cleared after sync** | OpenAI key |
| `s-llmProvider` | string | ✅ encrypted DB | AI provider |
| `s-telegramToken` | string | ✅ encrypted DB → **cleared after sync** | Telegram bot token |
| `s-telegramChatId` | string | ✅ encrypted DB | Telegram chat ID |
| `s-gotifyUrl` | string | ✅ encrypted DB | Gotify server URL |
| `s-gotifyToken` | string | ✅ encrypted DB → **cleared after sync** | Gotify app token |

---

## PWA Setup

| File | Purpose |
|------|---------|
| `frontend/manifest.json` | standalone, PNG icons, 2 shortcuts |
| `frontend/sw.js` | network-first, pre-caches app shell, skips /api/* |
| `frontend/_headers` | MIME hints for here.now static host |
| `frontend/icons/icon-{192,512}.png` | Required for Chrome install prompt |

SW registration + `beforeinstallprompt` intercept in `main.js`. ⬇ App button shows in header.

`nginx.conf` has explicit `location = /sw.js` with `Service-Worker-Allowed: /` header.

---

## Onboarding Wizard (`onboarding.js`)

Full-screen 3-step wizard on first launch:
1. **Step 1:** Backend URL + live `/health` check via `checkConnection()` — Weiter disabled until success
2. **Step 2:** Optional SerpAPI + Gemini keys
3. **Step 3:** Confirmation — saves everything to localStorage + backend

Close: fade-out via `.ob-closing` + `setTimeout(400)`. Skip link always visible.

---

## Deployment

### Quickstart

```bash
cp .env.example .env
nano .env          # set HOST_PORT, TZ, DATA_DIR, APP_SECRET
docker compose up -d --build
```

### .env Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST_PORT` | `8765` | Frontend (Nginx) |
| `BACKEND_PORT` | `8766` | Backend (FastAPI, direct browser access) |
| `TZ` | `Europe/Rome` | Cron timezone |
| `DATA_DIR` | `./data` | Host path → mounted as `/app/data` in container |
| `APP_SECRET` | *(required)* | AES-Fernet key — change before first start, never change after |

SQLite DB: `${DATA_DIR}/tracker.db` on host → `/app/data/tracker.db` in container.

### Local Development (no Docker)

```bash
cd backend
DB_PATH=./tracker.db APP_SECRET=dev uvicorn main:app --reload --port 8000

cd frontend
python3 -m http.server 8765
# Settings → Backend URL: http://localhost:8000
```

---

## How-To Guides

### Add a new i18n key
1. Add to `frontend/locales/de.json`
2. Add to `frontend/locales/en.json`
3. Add to `frontend/locales/it.json`
4. HTML: `<span data-i18n="myKey">Fallback</span>`
5. JS: `t('myKey')`

### Add a new page
1. `<div class="page" id="page-mypage">` in `index.html`
2. Nav item in sidebar + bottom bar + hidden `<button id="nav-mypage">`
3. `bnMap` entry in `nav.js` + lazy-load in `doNav()`
4. `frontend/js/app/mypage.js` + import + `window.*` in `main.js`
5. i18n keys in all 3 locale files

### Add a new tracker type
1. `backend/my_scraper.py` — scraping logic
2. `backend/routes/my_route.py` — FastAPI router
3. `backend/database.py` — tables + CRUD
4. `backend/main.py` — register router
5. `frontend/js/app/my_tracker.js` — CRUD module (template: `googleflights.js`)
6. `frontend/js/main.js` — import + `window.*`
7. `frontend/index.html` — sub-tab in Preis-Radar + form
8. `frontend/locales/*.json` — all 3 languages

### GitHub API workflow (Claude's method)
Always fetch SHA before writing. Use Python `urllib.request` + `json=`:
```python
url = f'https://api.github.com/repos/{REPO}/contents/{path}?ref=main'
# PUT with sha to update, omit sha to create
body = {'message': msg, 'content': base64_content, 'branch': 'main', 'sha': sha}
```
Work directly on `main` unless explicitly asked for a PR.

---

## Refactoring History

| Date | Change |
|------|--------|
| 2026-03-28 | **ES Module Refactoring** — split 1400-line `<script>` monolith into 19 ES modules |
| 2026-03-28 | **UX/UI Reboot** — light theme, Bottom Bar, ticket cards, Settings slide-panel |
| 2026-03-28 | **Preis-Radar** — two-level navigation (pills + sub-tabs) |
| 2026-03-28 | **Meine Reisen** — hub page: Scratch Map + Bucket List + Journal + Budget |
| 2026-03-28 | **Field Guide Redesign** — small FAQ modal → full slide-panel with 4-tab manual |
| 2026-03-28 | **Onboarding Wizard** — full-screen 3-step, live `/health` check, API key setup |
| 2026-03-28 | **PWA** — manifest, Service Worker, icons, install button, iOS meta tags |
| 2026-03-28 | **Dark Mode "Mitternacht"** — component-level overrides, theme-color meta sync |
| 2026-03-28 | **Dashboard Live Stats** — `/api/dashboard/stats`, spinner states, setup links |
| 2026-03-28 | **Scratch Map** — jsvectormap, `/api/dawarich/countries`, country name→ISO mapping |
| 2026-03-28 | **Docker/Unraid** — HOST_PORT, TZ, DATA_DIR env vars, /app/data volume |
| 2026-03-28 | **Data Persistence** — `user_data` table, `/api/userdata`, `core/persist.js` |
| 2026-03-28 | **Security Hardening** — `actual_file` in SETTING_KEYS, API keys cleared from localStorage after sync |
| 2026-03-29 | **Notifications** — Telegram + Gotify, `notifications.py`, 🔔 Alerts tab in Settings, scheduler trigger |

---

## Roadmap

### Next
- [ ] Price threshold alerts — user-defined trigger price per tracker
- [ ] Car rental tracker (Mietwagen tab in Preis-Radar)

### Planned
- [ ] CSV / Excel export for price history
- [ ] Currency toggle (EUR / USD / GBP)
- [ ] SerpAPI quota widget in dashboard
- [ ] Skeleton loaders during data fetching
- [ ] Scratch Map: click country → show trip details panel
- [ ] Discord webhook notifications

### Ideas / Backlog
- [ ] Multi-user support
- [ ] Email alerts (SMTP)
- [ ] Repeat-trip suggestions
