# CLAUDE.md — WanderSuite AI Assistant Context

Full architecture reference for AI assistants working on this codebase.
Update after significant changes.

**Repository:** `antonbier/tracker-an-te`
**Stack:** Svelte 5 + SvelteKit · FastAPI · SQLite · Docker Compose
**Deployment:** here.now (frontend via GitHub Action) · Railway (backend) · Unraid (on-prem)

---

## Repository Structure

```
wandersuite/
├── svelte/                      ← Frontend (Svelte 5 + SvelteKit + Tailwind v4)
│   ├── src/
│   │   ├── app.css              ← Design tokens (CSS variables, light/dark)
│   │   ├── app.html             ← SvelteKit entry HTML + PWA meta
│   │   ├── lib/
│   │   │   ├── stores.js        ← All Svelte stores (persisted to localStorage)
│   │   │   ├── api.js           ← HTTP client with JWT injection
│   │   │   ├── toast.js         ← Toast notification store
│   │   │   ├── i18n.js          ← Reactive i18n (t as derived store)
│   │   │   └── components/
│   │   │       ├── AppShell.svelte
│   │   │       ├── Header.svelte
│   │   │       ├── Sidebar.svelte
│   │   │       ├── BottomNav.svelte
│   │   │       ├── Toast.svelte
│   │   │       ├── FieldGuide.svelte
│   │   │       ├── Settings.svelte
│   │   │       ├── Onboarding.svelte
│   │   │       ├── Login.svelte
│   │   │       ├── Setup.svelte
│   │   │       └── pages/
│   │   │           ├── Dashboard.svelte
│   │   │           ├── PriceRadar.svelte
│   │   │           ├── MyTrips.svelte   ← includes Journal tab (Dawarich)
│   │   │           └── Discover.svelte
│   │   ├── locales/
│   │   │   ├── de.json          ← ~80 translation keys
│   │   │   ├── en.json
│   │   │   └── it.json
│   │   └── routes/
│   │       ├── +layout.js       ← ssr: false, prerender: false
│   │       ├── +layout.svelte   ← Startup gate: onboarding → setup → login → app
│   │       └── +page.svelte     ← Page router (currentPage store)
│   ├── package.json
│   ├── svelte.config.js         ← adapter-static → dist/
│   └── vite.config.js           ← Tailwind v4, SvelteKitPWA
│
├── backend/                     ← FastAPI application
│   ├── main.py                  ← Entry + APScheduler + APP_VERSION timestamp
│   ├── database.py              ← SQLite schema + CRUD (all tables)
│   ├── settings_manager.py      ← AES-Fernet encrypted settings (18 SETTING_KEYS)
│   ├── auth_db.py               ← Users table + bcrypt CRUD
│   ├── auth_jwt.py              ← JWT middleware (AUTH_ENABLED=false default)
│   ├── notifications.py         ← Telegram + Gotify
│   ├── scraper.py               ← Ryanair API scraper
│   ├── google_scraper.py        ← Google Flights via SerpAPI
│   ├── homair_scraper.py        ← Homair via SerpAPI
│   ├── booking_scraper.py       ← Booking via SerpAPI
│   ├── dawarich.py              ← Trip detection algorithm + Nominatim geocoding
│   ├── countries.py             ← Country name → ISO-2 mapping
│   ├── actual_budget.py         ← ActualBudget client (actualpy ≥ 0.21.0)
│   ├── gemini.py                ← Google Gemini AI
│   ├── openai_client.py         ← OpenAI gpt-4o-mini
│   ├── scheduler.py             ← Daily batch + price-drop trigger
│   └── routes/
│       ├── auth.py              ← /api/status, /api/auth/*, /api/admin/*
│       ├── trackers.py          ← /api/trackers
│       ├── prices.py            ← /api/prices + CSV export
│       ├── google_flights.py    ← /api/google-flights
│       ├── accommodations.py    ← /api/accommodations/homair + /booking
│       ├── budget.py            ← /api/budget/actual/*
│       ├── dawarich.py          ← /api/dawarich/*
│       ├── discover.py          ← /api/discover
│       ├── settings.py          ← /api/settings + /serpapi-quota
│       ├── dashboard.py         ← /api/dashboard/stats
│       ├── userdata.py          ← /api/userdata/*
│       └── notifications.py     ← /api/notifications/test-*
│
├── docker/
│   ├── Dockerfile               ← Backend (Python 3.12-slim)
│   ├── Dockerfile.frontend      ← Multi-Stage: Node 20 build → Nginx serve
│   └── nginx.conf               ← SPA fallback + /api/ proxy + PWA MIME types
├── frontend/
│   └── icons/                   ← PWA icons used by Docker build (icon-192/512.png)
├── docker-compose.yml
├── .env.example
└── .github/workflows/
    └── deploy-svelte.yml        ← Builds Svelte → deploys to here.now on every push

```

---

## Frontend Architecture (Svelte 5)

### Startup Gate (+layout.svelte)
```
No apiUrl/onboarding → <Onboarding />
  ↓ done
GET /api/status → needs_setup=true → <Setup />   (first admin account)
  ↓
auth_enabled=true + no JWT → <Login />
  ↓
→ <AppShell> (app is ready)
```

### State Management (stores.js)
All state in Svelte stores, auto-persisted to localStorage:

| Store | localStorage key | Description |
|-------|-----------------|-------------|
| `apiUrl` | `apiUrl` | Backend URL |
| `lang` | `lang` | `de` · `en` · `it` |
| `theme` | `theme` | `''` (light) · `'dark'` |
| `onboardingDone` | `ws-onboarding-done` | `'1'` when completed |
| `jwtToken` | `ws-jwt` | JWT for auth |
| `currentUser` | `ws-current-user` | `{email, role}` JSON |
| `trips` | — | in-memory, synced via `/api/userdata` |
| `budget` | — | in-memory |
| `bucketlist` | — | in-memory |
| `appVersion` | — | from `/health` response |
| `appStatus` | — | `{auth_enabled, needs_setup}` |

### i18n (i18n.js)
`t` is a **derived store** — use `$t('key')` in components for reactive re-render on language change.
`setLang(locale)` updates store + syncs to backend `/api/settings`.

### Navigation
Single-page app — `currentPage` store drives which page component renders.
Pages: `home` · `priceradar` · `mytrips` · `discover`
MyTrips has 5 sub-tabs: Übersicht · Reisen · Budget · Bucket List · Tagebuch (Dawarich)

### API Client (api.js)
```js
api(path, options)  // auto-injects JWT Bearer if jwtToken store is set
checkApiStatus(url) // returns bool — used by Onboarding
```

---

## Backend Conventions

### Encrypted Settings (settings_manager.py)
All 18 `SETTING_KEYS` stored AES-Fernet encrypted in SQLite `settings` table.
Read with `get_setting_value(key)` anywhere in the backend.
Non-secret values (urls, coords, language) returned unmasked by `GET /api/settings`.
Secret values (keys, tokens) returned as `••••••••`.

### Auth (auth_jwt.py)
`AUTH_ENABLED=false` (default) → all routes pass through as guest, no login required.
`AUTH_ENABLED=true` → Bearer JWT required on all `/api/*` except `/api/status`, `/api/auth/*`, `/health`.

### Version
`APP_VERSION = v.YYYY.MM.DD-HHmm` generated at startup, returned by `/health`.

### Scheduler
Daily at 07:00 (TZ from env): scrapes all active trackers → price-drop notifications.

---

## Deployment

### Unraid (on-prem)
```bash
git pull && docker compose up -d --build
```
Docker Multi-Stage Build: Node 20 compiles Svelte → Nginx serves dist/.
No Node.js needed on host. Icons copied from `frontend/icons/` during build.

### here.now (cloud frontend)
GitHub Action `deploy-svelte.yml` triggers on every push to main:
`npm ci` → `npm run build` → copy icons → deploy `svelte/dist/` to here.now.

### Railway (cloud backend)
`backend/railway.toml` configures Railway deployment.

---

## Design Tokens (app.css)

| Variable | Light | Dark |
|----------|-------|------|
| `--ws-bg` | `#f9f8f6` | `#12141c` |
| `--ws-surface` | `#ffffff` | `#1e212b` |
| `--ws-surface2` | `#f2f0ec` | `#252837` |
| `--ws-border` | `#e2ddd6` | `#323647` |
| `--ws-text` | `#1a1612` | `#eceef5` |
| `--ws-accent` | `#D95D39` | `#D95D39` |
| `--ws-accent2` | `#1E3A5F` | `#6aaddc` |
| `--ws-green` | `#2A5C45` | `#4dac7a` |
| `--ws-muted` | `#6b6560` | `#9094a8` |

Dark mode: `document.documentElement.classList.toggle('dark')`.

---

## GitHub API Workflow (Claude's method)
Always fetch SHA before writing. Work directly on `main`.
```python
url = f'https://api.github.com/repos/{REPO}/contents/{path}?ref=main'
# PUT with sha to update, omit sha to create
body = {'message': msg, 'content': base64_content, 'branch': 'main', 'sha': sha}
```

---

## Roadmap

### Planned
- [ ] Scratch Map (jsvectormap) — visited countries world map in MyTrips
- [ ] Mietwagen tab in Preis-Radar
- [ ] Currency toggle (EUR / USD / GBP)
- [ ] Price history chart (Chart.js) in PriceRadar tracker cards
- [ ] Discord webhook notifications
- [ ] Skeleton loaders

### Backlog (Phase 2)
- [ ] Multi-user support (user_id on all content tables)
- [ ] Email alerts (SMTP)
