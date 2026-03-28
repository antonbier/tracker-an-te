# CLAUDE.md – WanderSuite AI Assistant Context

This file gives AI assistants (Claude, Copilot, etc.) the context they need to work effectively on this codebase. It documents architecture decisions, refactoring history, and conventions.

---

## Project Overview

**WanderSuite** is a self-hosted travel management suite. It is a single Docker Compose stack with:
- **Frontend:** Vanilla HTML/CSS + native ES Modules (no bundler, no npm)
- **Backend:** FastAPI (Python) + SQLite + APScheduler
- **Reverse proxy:** Nginx

The app runs on Unraid but works anywhere with Docker.

---

## Repository Layout

```
antonbier/tracker-an-te
├── frontend/
│   ├── index.html          ← SPA: 2700+ lines — HTML structure + all CSS
│   ├── locales/            ← i18n JSON files (de, en, it)
│   └── js/                 ← Native ES Modules
│       ├── main.js         ← Entry point (imports + window.* + DOMContentLoaded)
│       ├── core/           ← Shared infrastructure
│       └── ui/ + app/      ← Feature modules
├── backend/                ← FastAPI app
├── docker-compose.yml
├── README.md
└── CLAUDE.md               ← You are here
```

---

## Frontend Module Architecture

All JavaScript is split into native ES Modules loaded via `<script type="module" src="js/main.js">`.  
**No bundler. No npm. No build step.**

### Why `window.*` bindings?

ES Modules have their own scope — they don't pollute `window` automatically. Because `index.html` uses `onclick="someFunction()"` inline handlers throughout, every exported function that is called from HTML must be explicitly bound to `window` in `main.js`. This is the single source of truth for all global bindings.

```js
// main.js pattern
import { addTracker } from './app/ryanair.js';
window.addTracker = addTracker;
```

### Module Map

```
main.js
│
├── core/state.js       ← Mutable app state (let exports + setter functions)
│                          currentLang, API_URL, selectedTrackerId, trips, ...
│
├── core/api.js         ← api(path, opts) — central HTTP client
│                          checkApiStatus() — pings /health, updates status dot
│
├── ui/i18n.js          ← loadLocale(lang), t(key), applyTranslations(), setLang(lang)
│                          Fetches /locales/{lang}.json — uses RELATIVE path (not /locales/)
│
├── ui/nav.js           ← navigate(page) — switches .page divs + syncs bottom bar
│                          Uses document.startViewTransition() with graceful degradation
│                          toggleSidebar(), closeSidebar()
│
├── ui/toast.js         ← toast(msg, type) — appends to #toastContainer, auto-removes after 4s
│
├── ui/settings.js      ← openSettings(), closeSettings(), saveSettings()
│                          switchTab(tab) — supports 'basic', 'integrations', 'apis'
│                          toggleTheme(isDark) — toggles body.dark-mode class
│
├── ui/priceradar.js    ← switchRadarCategory(cat) — main pill nav for Preis-Radar
│                          switchRadarSubTab(trackerId) — secondary sub-nav
│
├── ui/tabs.js          ← switchMyTripsTab(tabId) — Meine Reisen sub-tabs
│                          Lazy-loads journal/budget/bucketlist on first open
│
├── app/ryanair.js      ← Full Ryanair tracker: addTracker, loadTrackers, renderTrackers,
│                          selectTracker, renderChart (Chart.js), scrapeNow, deleteTracker,
│                          togglePause, checkDawarich, generateIdeas, renderRecommendations
│
├── app/budget.js       ← toggleActualSync, addTrip, syncActualBudget, updateBudget,
│                          renderBudget, removeTrip, loadExpenses, filterExpenses, renderExpenseTable
│
├── app/dashboard.js    ← loadDashboard() → calls loadDashTrackers, loadDashBudget, loadDashTrips
│
├── app/googleflights.js← addGFTracker, loadGFTrackers, renderGFTrackers,
│                          scrapeGFTracker, deleteGFTracker
│
├── app/homair.js       ← addHomairTracker, loadHomairTrackers, renderHomairTrackers,
│                          scrapeHomairTracker, deleteHomairTracker
│
├── app/booking.js      ← addBookingTracker, loadBookingTrackers, renderBookingTrackers,
│                          scrapeBookingTracker, deleteBookingTracker
│
├── app/journal.js      ← loadJournalTrips, renderJournalTrips, syncJournal, deleteJournalTrip
│                          Uses dynamic import for settings.js to avoid circular deps
│
├── app/onboarding.js   ← checkOnboarding, closeOnboarding, obNext/obBack, updateObStep
│                          openFieldGuide, closeFieldGuide
│
└── app/bucketlist.js   ← addBucketListItem, renderBucketList, deleteBucketListItem, updateMyTripsStats
                           Persisted to localStorage key 'ws-bucketlist' — no backend needed
```

### Avoiding Circular Imports

Some modules need each other at runtime but not at load time. Use **dynamic imports** inside functions:

```js
// journal.js calls openSettings if Dawarich config is missing — but we can't static-import
// settings.js at the top (would create a cycle). Solution:
const { openSettings } = await import('../ui/settings.js');
```

### Page/DOM Architecture

`index.html` contains all pages as `<div class="page" id="page-*">` siblings. `navigate(page)` switches them by toggling the `.active` class. 

Some pages were **nested** into two-level navigation views:

- `page-ryanair`, `page-google`, `page-homair`, `page-booking` → moved into `page-priceradar` as `radar-sub-*` panels. The original `<div class="page">` wrappers still exist in a hidden `aria-hidden="true"` container so that JS functions like `loadTrackers()` can still find their DOM targets (`#trackerList` etc.) without modification.
- `page-journal`, `page-budget` → moved into `page-mytrips` as `mytrips-panel-*` panels. Same pattern.

---

## Navigation Structure

```
Bottom Bar / Sidebar item → navigate(page) call
─────────────────────────────────────────────
🧭 Übersicht    → navigate('home')
🎯 Preis-Radar  → navigate('priceradar')  → switchRadarCategory('overview')
✨ Inspiration  → navigate('discover')
🎒 Meine Reisen → navigate('mytrips')    → switchMyTripsTab('overview')
```

**Mobile (`< 900px`):** Sidebar hidden, replaced by bottom navigation bar.  
**Desktop:** Sidebar with 4 top-level items + hidden `<button id="nav-*">` elements for JS active-state sync.

---

## CSS Architecture

All CSS lives in `index.html` inside a single `<style>` block (no external CSS files).

### CSS Variables (`:root`)

The app defaults to **light mode**. Dark mode is opt-in via `body.dark-mode`.

| Variable | Light | Dark |
|----------|-------|------|
| `--bg` | `#f9f8f6` (off-white) | `#14120f` |
| `--accent` | `#D95D39` (terracotta) | `#E8704A` |
| `--accent2` | `#1E3A5F` (navy) | `#5b9fd4` |
| `--green` | `#2A5C45` (forest) | `#4a9a72` |

### Key CSS Patterns

- **Pill nav** (`.radar-pills`, `.radar-pill`) — used for Preis-Radar + Meine Reisen main tabs
- **Sub-nav** (`.radar-subnav`, `.radar-subtab`) — used for tracker sub-tabs inside Preis-Radar
- **Ticket-style cards** (`.tracker-item`) — left accent stripe (`::before`), dashed border before actions
- **Settings slide-panel** — `#settingsBackdrop .modal` slides in from the right (`translateX`)
- **Bottom nav** (`.bottom-nav`) — `display:none` by default, `display:flex` at `< 900px`

---

## Backend Conventions

### API Key Storage

API keys (SerpAPI, Gemini, OpenAI, Dawarich token, ActualBudget password) are:
1. Stored in `localStorage` on the client (never sent in URLs)
2. Optionally synced to the backend via `POST /api/settings` where they are encrypted with AES-Fernet before storing in SQLite

### ActualBudget Integration

Uses `actualpy` (≥ 0.21.0). Key fields:
- `base_url` — ActualBudget server URL
- `password` — server password (not a token)
- `budget_file` — budget name as displayed in ActualBudget top-left
- Date format: `YYYYMMDD` integer
- Transfer field: `transferred_id` (not `transfer_id`)

### Dawarich Integration

Fetches GPS points from Dawarich API (paginated). Haversine distance calculation to home coordinates. Points > 50 km from home qualify. Overnight = 2+ consecutive days away. Max 2-day gap between consecutive days to merge into one trip.

---

## Refactoring History

### 2026-03-28 — ES Module Refactoring (PR #1 + PR #2)

The original `index.html` had a ~1400-line inline `<script>` block (monolith). This was split into native ES Modules across two PRs:

- **PR #1** (`refactor/es-modules` → `main`): Extracted `core/` and `ui/` modules, replaced `<script>` with `<script type="module" src="js/main.js">`. index.html: 3155 → 1748 lines (−43%).
- **PR #2** (`refactor/feature-modules` → `main`): Extracted all `app/` modules. `main.js`: 1493 → 156 lines.

**Key decision:** All functions called from `onclick="..."` in HTML are explicitly bound to `window` in `main.js`. No HTML was modified.

### 2026-03-28 — UX/UI Reboot

- **Theme:** Dark → Light default. New palette: off-white bg, terracotta accent, navy accent2, forest green.
- **Navigation:** Sidebar restructured from scraper-sorted to workflow-oriented (4 sections). Mobile bottom bar added.
- **Ticket cards:** Tracker items restyled with left accent stripe + dashed action separator.
- **Settings:** Compact modal → full-height slide-panel from right, 3 tabs (Allgemein / Integrationen / APIs & KI).
- **View Transitions:** `document.startViewTransition()` for smooth page switches (graceful degradation).
- **Dark mode:** Now opt-in via `body.dark-mode` (was `body.light-mode`).

### 2026-03-28 — Preis-Radar

New two-level navigation page (`page-priceradar`):
- **Level 1:** Pill tabs — Übersicht / Flüge / Unterkünfte / Mietwagen
- **Level 2:** Sub-tabs — Ryanair|Google, Homair|Booking
- Old `page-ryanair` etc. kept as hidden DOM nodes for JS compatibility.
- Logic in `frontend/js/ui/priceradar.js`.

### 2026-03-28 — Meine Reisen

New hub page (`page-mytrips`) bundles Budget, Journal + new Bucket List feature:
- **Level 1:** Pill tabs — Übersicht / Wunschziele / Tagebuch / Budget
- **Bucket List:** Wishlist stored in `localStorage['ws-bucketlist']` as JSON array. Each item has `{id, dest, when, emoji, added}`. Random emoji from a curated travel set.
- **Stats panel:** Shows visited places count, remaining budget, wishlist count. Lazy-loaded on tab open.
- Logic in `frontend/js/app/bucketlist.js` + `frontend/js/ui/tabs.js`.

---

## Working with This Codebase

### Making changes via GitHub API

Claude uses Python `urllib.request` with the GitHub Contents API. Key pattern:

```python
# Always fetch SHA before writing
url = f'https://api.github.com/repos/{REPO}/contents/{path}?ref={branch}'
# PUT to create or update (sha required for updates)
body = {'message': msg, 'content': base64_content, 'branch': branch, 'sha': existing_sha}
```

For large files, fetch with `?ref=branch` first to get the SHA, then PUT with the new content.

### Adding a new i18n key

1. Add to `frontend/locales/de.json`
2. Add to `frontend/locales/en.json`  
3. Add to `frontend/locales/it.json`
4. Use in HTML: `data-i18n="myKey"` or `data-i18n-placeholder="myKey"`
5. Use in JS: `t('myKey')`

### Adding a new page

1. Add `<div class="page" id="page-mypage">` in `index.html` (inside `<main class="main-content">`)
2. Add nav item in sidebar + bottom nav if needed
3. Update `bnMap` in `nav.js`
4. Add lazy-load in `doNav()` in `nav.js`
5. Add hidden `<button id="nav-mypage">` in the hidden nav div for active-state sync
6. Create `frontend/js/app/mypage.js` (follow existing modules as template)
7. Import + bind in `main.js`

---

## localStorage Keys

| Key | Type | Contents |
|-----|------|----------|
| `apiUrl` | string | Backend URL (e.g. `http://192.168.1.51:8766`) |
| `lang` | string | Active language code (`de`, `en`, `it`) |
| `theme` | string | `'dark'` or absent (light is default) |
| `ws-budget` | string | Budget total in EUR |
| `ws-trips` | JSON array | Manual + ActualBudget trips `[{name, cost, date, source?}]` |
| `ws-bucketlist` | JSON array | Bucket list items `[{id, dest, when, emoji, added}]` |
| `ws-onboarding-done` | string | `'1'` when onboarding completed |
| `s-timezone` | string | Timezone (e.g. `Europe/Rome`) |
| `s-dawarichUrl` | string | Dawarich instance URL |
| `s-dawarichToken` | string | Dawarich API token |
| `s-homeLat` / `s-homeLon` | string | Home coordinates for trip detection |
| `s-actualUrl` | string | ActualBudget server URL |
| `s-actualPassword` | string | ActualBudget password |
| `s-actualFile` | string | ActualBudget budget name |
| `s-travelCategories` | string | Comma-separated ActualBudget travel categories |
| `s-serpApiKey` | string | SerpAPI key |
| `s-geminiKey` | string | Google Gemini API key |
| `s-openaiKey` | string | OpenAI API key |
| `s-llmProvider` | string | AI provider (`gemini`, `openai`, `anthropic`, `ollama`) |

---

## Roadmap

- [ ] Skeleton loaders for data fetching states
- [ ] CSV export for price history
- [ ] Currency toggle (EUR / USD / GBP)
- [ ] Telegram / Discord / Gotify price drop alerts
- [ ] Price threshold configuration per tracker
- [ ] SerpAPI quota tracker in dashboard
- [ ] Mobile PWA (service worker + manifest.json)
- [ ] Car rental tracker (Preis-Radar → Mietwagen tab)
---

## Feldführer UX-Redesign

**Datum:** 2026-03-28

### Was geändert wurde

Das alte Feldführer-Modal (kleines, überladenes Popup mit 5 FAQ-Einträgen) wurde in ein elegantes **Full-Height Slide-Panel** umgebaut – identisches Muster wie das Settings-Panel.

**Neue Datei:** `frontend/js/ui/fieldguide.js`
- `openFieldGuide()` — öffnet das Panel, setzt Standardtab 'start'
- `closeFieldGuide(e)` — schließt Panel (auch als Backdrop-Klick-Handler)
- `switchFieldGuideTab(tab)` — wechselt zwischen 4 Tabs
- Aus `onboarding.js` ausgelagert (war dort als Export, was semantisch falsch war)

**4 Tabs mit vollständigem Handbuch-Inhalt:**

| Tab | Inhalt |
|-----|--------|
| 🚀 Start & APIs | Cronjob 07:00, IATA-Codes, SerpAPI/Gemini/OpenAI Keys mit direkten Links, Key-Speicherung |
| 🎯 Preis-Radar | Direktes vs. SerpAPI-Scraping, Status-Badges (pausiert/geblockt/~Schätzwert), Tracker-Limits |
| 🎒 Meine Reisen | Dawarich-Algorithmus (5 Schritte), ActualBudget-Setup, manueller Modus, Bucket List |
| ✨ Entdecken | KI-Anbieter-Vergleich (Gemini vs. OpenAI), Dawarich-Filter-Toggle, Datenschutz |

**Neues CSS:**
- `.fg-infobox` — hervorgehobene URL-Boxen mit Monospace-Font und direkten Links
- `.fg-section-title` — Serif/Italic-Abschnittsüberschriften innerhalb eines Tabs
- `.fg-badge` + Varianten (`-green`, `-orange`, `-navy`) — Status-Badges in Erklärungstexten
- `.faq-question` — Playfair Display, italic, accent2-Farbe (edler als vorher)
- `.faq-answer` — klare DM Sans, besserer Zeilenabstand
---

## PWA & Dark Mode Polish

**Datum:** 2026-03-28

### PWA Setup

WanderSuite ist jetzt eine installierbare Progressive Web App.

**`frontend/manifest.json`**
- `display: "standalone"` — läuft ohne Browser-Chrome
- `theme_color: "#D95D39"` (Terracotta) — Titelleiste auf Android
- `background_color: "#f9f8f6"` — Splash-Screen
- Icons: SVG-Kompass (Base64-inline, 192×512px) — kein CDN, kein Build-Schritt
- Shortcuts: "Preis-Radar" + "Meine Reisen" — Long-Press auf iOS/Android

**`frontend/sw.js`**
- Strategie: Network-first, Cache-Fallback
- Pre-cached beim Install: alle JS-Module, Locale-Dateien, HTML
- API-Calls (`/api/*`) und externe Ressourcen: immer network-only
- Cache-Versionierung via `CACHE_NAME = 'wandersuite-v1'`
- Sauberes Cleanup alter Cache-Versionen im `activate`-Event

**`frontend/index.html` — Meta-Tags**
```html
<link rel="manifest" href="/manifest.json">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="WanderSuite">
<meta name="theme-color" content="#f9f8f6" id="meta-theme-color">
<meta name="mobile-web-app-capable" content="yes">
```
- `viewport-fit=cover` für iOS Notch/Dynamic Island
- Safe-area-inset CSS für Bottom Bar und Header (`env(safe-area-inset-*)`)

**`frontend/js/main.js`**
- Service Worker Registrierung in `DOMContentLoaded`
- `MutationObserver` auf `body.classList` → aktualisiert `#meta-theme-color` automatisch bei Dark-Mode-Wechsel

### iOS Installation

1. Safari → Teilen → "Zum Home-Bildschirm"
2. App startet ohne Browser-Chrome (standalone)
3. Status Bar: light-mode → weiß, dark-mode → `#12141c`

### Android Installation

Chrome → drei Punkte → "App installieren" (oder Banner)

---

### Dark Mode "Mitternacht" — Farbpalette

| Variable | Light | Dark (Mitternacht) |
|----------|-------|-------------------|
| `--bg` | `#f9f8f6` | `#12141c` (tief nachtblau) |
| `--surface` | `#ffffff` | `#1e212b` |
| `--surface2` | `#f2f0ec` | `#252837` |
| `--border` | `#e2ddd6` | `#323647` |
| `--text` | `#1a1612` | `#eceef5` |
| `--accent` | `#D95D39` | `#D95D39` (unverändert ← Wanderlust) |
| `--accent2` | `#1E3A5F` | `#6aaddc` (aufgehellt für Kontrast) |
| `--green` | `#2A5C45` | `#4dac7a` |

**Component-Level Overrides** (zusätzlich zu den CSS-Variablen):
- `.header`, `.sidebar`, `.bottom-nav` — eigene Dark-Mode Backgrounds
- `.card`, `.tracker-item` — explizit `background: var(--surface)`
- Settings- und Field-Guide-Panels — `background: var(--surface)`
- `input`, `select`, `textarea` — `background: var(--surface2)`
- Pill-Navigation, Overview-Cards, Bucket-Cards

**Toggle:** `Settings → Allgemein → Dark Mode` (speichert `theme: 'dark'` in localStorage, stellt beim Neuladen via `main.js` korrekt wieder her)
