# CLAUDE.md — WanderSuite AI Assistant Context

This file gives AI assistants the full context needed to work effectively on this codebase.
Keep it updated after significant changes.

**Repository:** `antonbier/tracker-an-te`  
**Live URL:** `https://wander-epoch-69vc.here.now`  
**Stack:** FastAPI backend · Nginx + Vanilla JS frontend · SQLite · Docker Compose

---

## Project Overview

WanderSuite is a self-hosted travel management suite. One Docker Compose stack:
- **Frontend:** Nginx serving `frontend/` — HTML/CSS + native ES Modules (no bundler, no npm)
- **Backend:** FastAPI (Python 3.12) + SQLite + APScheduler
- **Deployment:** here.now (static frontend via GitHub Action) + Railway/Unraid (backend)

---

## File Structure

```
wandersuite/
├── frontend/
│   ├── index.html         ← SPA: all HTML + CSS (~3100 lines)
│   ├── manifest.json      ← PWA manifest (standalone, PNG icons)
│   ├── sw.js              ← Service Worker (network-first, cache fallback)
│   ├── _headers           ← Static host MIME type hints
│   ├── icons/             ← PWA icons (icon-192.png, icon-512.png)
│   ├── locales/           ← i18n: de.json, en.json, it.json (~280 keys each)
│   └── js/
│       ├── main.js        ← Entry point (imports + window.* + DOMContentLoaded)
│       ├── core/
│       │   ├── state.js   ← Global state + setters
│       │   └── api.js     ← HTTP client + health check
│       ├── ui/
│       │   ├── i18n.js    ← Translations
│       │   ├── nav.js     ← navigate() + bottom bar + View Transitions
│       │   ├── toast.js   ← Toast notifications
│       │   ├── settings.js← Settings slide-panel
│       │   ├── priceradar.js ← Preis-Radar tab logic
│       │   ├── tabs.js    ← Meine Reisen tab logic
│       │   └── fieldguide.js ← Field Guide slide-panel
│       └── app/
│           ├── ryanair.js     ← Ryanair + Discover/AI
│           ├── budget.js      ← Budget + ActualBudget + Expenses
│           ├── dashboard.js   ← Home dashboard + Meine Reisen live stats
│           ├── scratchmap.js  ← Scratch Map (jsvectormap)
│           ├── googleflights.js
│           ├── homair.js
│           ├── booking.js
│           ├── journal.js     ← Dawarich sync
│           ├── onboarding.js  ← Full-screen wizard
│           └── bucketlist.js  ← Wishlist (localStorage only)
│
├── backend/
│   ├── main.py            ← FastAPI app + APScheduler
│   ├── database.py        ← SQLite CRUD
│   ├── settings_manager.py← AES-Fernet encrypted settings
│   ├── countries.py       ← Country name → ISO-2 mapping (100+ entries, DE/EN/IT)
│   ├── scraper.py         ← Ryanair
│   ├── google_scraper.py  ← Google Flights via SerpAPI
│   ├── homair_scraper.py  ← Homair via SerpAPI Google Hotels
│   ├── booking_scraper.py ← Booking via SerpAPI
│   ├── dawarich.py        ← Trip detection algorithm
│   ├── actual_budget.py   ← ActualBudget client (actualpy ≥0.21.0)
│   ├── gemini.py / openai_client.py
│   ├── scheduler.py       ← Daily 07:00 cron
│   └── routes/
│       ├── trackers.py    ← /api/trackers
│       ├── prices.py      ← /api/prices
│       ├── google_flights.py← /api/google-flights
│       ├── accommodations.py← /api/accommodations/homair + /booking
│       ├── budget.py      ← /api/budget/actual/*
│       ├── dawarich.py    ← /api/dawarich/* (incl. /countries)
│       ├── discover.py    ← /api/discover
│       ├── settings.py    ← /api/settings
│       └── dashboard.py   ← /api/dashboard/stats
│
├── docker/
│   ├── Dockerfile
│   └── nginx.conf         ← Explicit locations for sw.js, manifest.json, /icons/, /js/
├── docker-compose.yml
└── .github/workflows/deploy-frontend.yml  ← Deploys frontend/ to here.now on push
```

---

## Frontend Architecture

### ES Module Pattern

All JS is split into native ES Modules. No bundler, no npm. The browser loads them directly.

**The `window.*` binding rule:**  
ES Modules don't share scope with `onclick="fn()"` inline handlers. Every function called from HTML must be explicitly bound in `main.js`:

```js
// main.js pattern
import { addTracker } from './app/ryanair.js';
window.addTracker = addTracker;  // makes it callable from onclick=""
```

**Avoiding circular imports:**  
Where modules need each other at runtime but not at load time, use dynamic `import()`:
```js
// journal.js needs openSettings() but can't static-import settings.js (would create cycle)
const { openSettings } = await import('../ui/settings.js');
```

### State Management

All mutable state lives in `core/state.js` as named exports with setter functions:
```js
export let API_URL = '';
export function setApiUrl(val) { API_URL = val; }
// Usage: import { API_URL, setApiUrl } from '../core/state.js';
```
Never reassign imported `let` variables directly across module boundaries — use setters.

### Page/DOM Architecture

All pages are `<div class="page" id="page-*">` siblings inside `<main>`.  
`navigate(page)` switches them by toggling `.active`.

**Two-level navigation embedding:**  
Some pages are embedded inside parent tabs. The original `<div class="page">` wrappers remain in a hidden `aria-hidden="true"` container so JS functions still find their DOM targets:

```
page-priceradar
  └── radar-sub-ryanair    ← former page-ryanair content
  └── radar-sub-google     ← former page-google content
  └── radar-sub-homair     ← former page-homair content
  └── radar-sub-booking    ← former page-booking content
[hidden div aria-hidden]
  └── page-ryanair         ← preserved for JS compatibility
  └── page-google
  ...

page-mytrips
  └── mytrips-panel-overview  ← Scratch Map + live stats
  └── mytrips-panel-bucketlist
  └── mytrips-panel-journal   ← former page-journal content
  └── mytrips-panel-budget    ← former page-budget content
[hidden div aria-hidden]
  └── page-journal            ← preserved for JS compatibility
  └── page-budget
```

### Navigation Map

```
Bottom Bar / Sidebar → navigate(page)
────────────────────────────────────────────
🧭 Übersicht    → navigate('home')
🎯 Preis-Radar  → navigate('priceradar') → switchRadarCategory('overview')
✨ Inspiration  → navigate('discover')
🎒 Meine Reisen → navigate('mytrips')   → switchMyTripsTab('overview') + loadScratchMap()
```

Mobile (`< 900px`): Sidebar hidden → fixed bottom nav bar.  
Hidden `<button id="nav-*">` elements in sidebar keep JS active-state sync working for sub-pages.

### Lazy Loading

Tab content is loaded on demand via dynamic imports:
```js
// nav.js
if (page === 'mytrips') import('../ui/tabs.js').then(m => {
  m.switchMyTripsTab('overview');
  import('../app/bucketlist.js').then(b => b.updateMyTripsStats());
});
```

---

## CSS Architecture

All CSS is in `index.html` in a single `<style>` block. No external CSS files.

### CSS Variables

Default = **light mode**. Dark mode is opt-in via `body.dark-mode`.

| Variable | Light | Dark ("Mitternacht") |
|----------|-------|---------------------|
| `--bg` | `#f9f8f6` | `#12141c` |
| `--surface` | `#ffffff` | `#1e212b` |
| `--surface2` | `#f2f0ec` | `#252837` |
| `--border` | `#e2ddd6` | `#323647` |
| `--text` | `#1a1612` | `#eceef5` |
| `--accent` | `#D95D39` | `#D95D39` ← unchanged |
| `--accent2` | `#1E3A5F` | `#6aaddc` |
| `--green` | `#2A5C45` | `#4dac7a` |

Dark mode also applies component-level overrides (`.header`, `.sidebar`, `.card`, etc.).

### Key CSS Patterns

| Class/ID | Purpose |
|----------|---------|
| `.radar-pills` / `.radar-pill` | Main pill tab navigation |
| `.radar-subnav` / `.radar-subtab` | Secondary sub-tabs |
| `.tracker-item` | Ticket-style cards with left accent stripe |
| `#settingsBackdrop .modal` | Slides in from right (translateX) |
| `#fieldGuideBackdrop .modal` | Same pattern as settings |
| `#onboardingBackdrop` | Full-screen overlay (no `.modal-backdrop` class) |
| `.bottom-nav` | `display:none` by default, `display:flex` at `< 900px` |
| `#scratch-map-container` | jsvectormap world map container |
| `.ob-*` | Onboarding wizard classes |
| `.fg-*` | Field Guide content classes |

---

## Backend Conventions

### API Key Storage

1. Stored in `localStorage` on the client
2. Synced to backend via `POST /api/settings` → encrypted with AES-Fernet → SQLite

Keys available via `get_setting_value(key)` in Python (decrypted).

### ActualBudget (`actual_budget.py`)

- Library: `actualpy` ≥ 0.21.0
- Auth: `password` (server password, not a token)
- Budget identifier: `budget_file` = display name as shown in ActualBudget top-left
- Date format: `YYYYMMDD` integer
- Transfer field: `transferred_id` (not `transfer_id`)

### Dawarich Trip Detection (`dawarich.py`)

1. Fetch GPS points from Dawarich API (paginated, all pages)
2. Haversine distance from `home_lat`/`home_lon`
3. Keep points > 50 km from home
4. Group by date
5. Overnight = 2+ consecutive days away (min 1 night)
6. Merge groups with ≤ 2-day gaps into one trip
7. Reverse geocode centroid via Nominatim (OSM, free, 1 req/sec)
8. Store `location_name`, `country` (full name), `lat`, `lon`, `nights` in SQLite

### Country Name → ISO-2 (`countries.py`)

Nominatim returns country names in the user's locale (e.g. „Italy", „Deutschland", „Italia").  
`countries.py` has 100+ entries covering DE/EN/IT names → ISO-2 codes.  
Used by `GET /api/dawarich/countries` for the Scratch Map.

### Scratch Map (`scratchmap.js` + `/api/dawarich/countries`)

- Library: jsvectormap 1.5.3 (CDN, world map projection)
- Backend reads `detected_trips` from SQLite → maps country names → ISO-2 codes
- Frontend: `loadScratchMap()` → fetch → `initScratchMap(codes, names, tripCount, configured)`
- Visited countries: `var(--accent)` (Terracotta)
- Unvisited: `var(--surface2)` with `var(--border)` stroke
- Fallback: flag emoji badge grid if jsvectormap fails to load

---

## PWA Setup

| File | Purpose |
|------|---------|
| `frontend/manifest.json` | PWA manifest: standalone, icons, shortcuts |
| `frontend/sw.js` | Service Worker: network-first, pre-caches app shell |
| `frontend/_headers` | MIME type hints for static hosts |
| `frontend/icons/icon-192.png` | PNG icon (required for install prompt) |
| `frontend/icons/icon-512.png` | PNG icon |

**Install button:** `beforeinstallprompt` is intercepted in `main.js`. When Chrome fires it, a `⬇ App` button appears in the header. Click → native install dialog.

**iOS:** No automatic banner — use Safari → Share → Add to Home Screen.

**nginx.conf** has explicit `location = /sw.js` with `Service-Worker-Allowed: /` header.

---

## Onboarding Wizard (`onboarding.js`)

Full-screen 3-step wizard shown when no backend URL is configured:

1. **Step 1 — Connection:** URL input + live `/health` check (`checkConnection()`). "Weiter" only enabled after successful ping.
2. **Step 2 — Toolkit:** Optional SerpAPI + Gemini keys with direct links.
3. **Step 3 — Ready:** Confirmation. Final button saves keys to localStorage + syncs to backend.

Close: fade-out via `.ob-closing` CSS class + `setTimeout`.  
Skip link: always visible, writes `ws-onboarding-done = '1'`.

---

## Field Guide (`fieldguide.js`)

Full-height slide-panel from right (identical pattern to Settings).  
4 tabs: **Start & APIs** · **Preis-Radar** · **Meine Reisen** · **Entdecken**  
Content is inline HTML (not i18n keys) — rich formatting with `.fg-infobox`, `.fg-badge`, `.fg-section-title`.

---

## localStorage Keys

| Key | Type | Description |
|-----|------|-------------|
| `apiUrl` | string | Backend URL |
| `lang` | string | `'de'` · `'en'` · `'it'` |
| `theme` | string | `'dark'` (absent = light) |
| `ws-budget` | string | Budget total in EUR |
| `ws-trips` | JSON | `[{name, cost, date, source?}]` |
| `ws-bucketlist` | JSON | `[{id, dest, when, emoji, added}]` |
| `ws-onboarding-done` | string | `'1'` when completed |
| `s-timezone` | string | e.g. `'Europe/Rome'` |
| `s-dawarichUrl` | string | Dawarich server URL |
| `s-dawarichToken` | string | Dawarich API token |
| `s-homeLat` / `s-homeLon` | string | Home coordinates |
| `s-actualUrl` | string | ActualBudget URL |
| `s-actualPassword` | string | ActualBudget password |
| `s-actualFile` | string | Budget display name |
| `s-travelCategories` | string | Comma-separated category names |
| `s-serpApiKey` | string | SerpAPI key |
| `s-geminiKey` | string | Gemini API key |
| `s-openaiKey` | string | OpenAI API key |
| `s-llmProvider` | string | `'gemini'` · `'openai'` · `'anthropic'` · `'ollama'` |

---

## Working via GitHub API (Claude's method)

Claude edits this repo directly via the GitHub Contents API. Key pattern:

```python
# 1. Always fetch SHA before writing
url = f'https://api.github.com/repos/{REPO}/contents/{path}?ref=main'
# 2. PUT with sha to update, PUT without sha to create
body = {'message': msg, 'content': base64_content, 'branch': 'main', 'sha': existing_sha}
```

For multiline content use `json=` not curl. Always work on `main` branch directly unless explicitly asked for a PR.

---

## How-to: Add a New Page

```
1. Add <div class="page" id="page-mypage"> in index.html
2. Add nav item in sidebar + bottom nav button if needed
3. Update bnMap in nav.js (page → bottom bar item)
4. Add lazy-load in doNav() in nav.js
5. Add hidden <button id="nav-mypage"> in the hidden nav div for active-state sync
6. Create frontend/js/app/mypage.js (follow googleflights.js as template)
7. Import + bind in main.js
8. Add i18n keys to all 3 locale files
```

## How-to: Add a New i18n Key

```
1. Add to frontend/locales/de.json
2. Add to frontend/locales/en.json
3. Add to frontend/locales/it.json
4. Use in HTML:   <span data-i18n="myKey">Fallback</span>
5. Use in JS:     t('myKey')
```

## How-to: Add a New Tracker Type

```
1. backend/my_scraper.py         ← scraping logic
2. backend/routes/my_route.py    ← FastAPI router
3. backend/database.py           ← tables + CRUD
4. backend/main.py               ← register router
5. js/app/my_tracker.js          ← CRUD module
6. js/main.js                    ← import + window bindings
7. index.html                    ← sub-tab in Preis-Radar + form
8. locales/*.json                ← all 3 languages
```

---

## Refactoring History

| Date | What |
|------|------|
| 2026-03-28 | **ES Module Refactoring** — split 1400-line `<script>` monolith into 18 ES modules |
| 2026-03-28 | **UX/UI Reboot** — light theme, Bottom Bar, ticket cards, Settings slide-panel |
| 2026-03-28 | **Preis-Radar** — two-level navigation (pills + sub-tabs) |
| 2026-03-28 | **Meine Reisen** — hub with Bucket List + Scratch Map |
| 2026-03-28 | **Field Guide Redesign** — small FAQ modal → full slide-panel with 4-tab manual |
| 2026-03-28 | **Onboarding Wizard** — full-screen, live /health check, API key setup |
| 2026-03-28 | **PWA** — manifest, Service Worker, install button, iOS meta tags |
| 2026-03-28 | **Dark Mode "Mitternacht"** — component-level overrides |
| 2026-03-28 | **Dashboard Live Stats** — `/api/dashboard/stats`, spinner states, setup links |
| 2026-03-28 | **Scratch Map** — jsvectormap world map, `/api/dawarich/countries`, country name→ISO mapping |

---

## Roadmap

- [ ] Skeleton loaders
- [ ] CSV export for price history  
- [ ] Currency toggle (EUR/USD/GBP)
- [ ] Price threshold alerts + Telegram/Discord/Gotify notifications
- [ ] Car rental tracker
- [ ] SerpAPI quota widget in dashboard
- [ ] Scratch Map: click country → show trip details panel
