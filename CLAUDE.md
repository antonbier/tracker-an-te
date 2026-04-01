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
              → Only frontend is publicly accessible
              → /api/* calls go through Nginx proxy on port 8767
```

**Backend URL für User:** Im Onboarding-Wizard die **frontend URL** eintragen
(z.B. `https://wandersuite.deinedomain.de`) — Nginx proxied `/api/*` intern.
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
# Wenn gesetzt, werden diese Werte direkt verwendet (Priorität 1).
# Wenn nicht gesetzt (= localhost), leitet das Backend rp_id + origin
# automatisch aus dem HTTP Origin-Header ab (funktioniert hinter Zoraxy ohne Konfiguration).
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
- ✅ Passkey/WebAuthn backend routes
- ✅ Passkey UI (Login.svelte + PasskeyManager.svelte)
- ✅ Passkeys funktionieren hinter Zoraxy (HTTPS + Origin-Header auto-detection)

### Passkey — rp_id / Origin Logik (`backend/routes/passkey.py`)

`_get_rp(request)` wird bei jedem Passkey-Call aufgerufen:

1. **Env-Vars explizit gesetzt** (`WEBAUTHN_RP_ID != "localhost"`) → direkt verwenden
2. **Origin-Header** (Browser sendet ihn bei jedem POST automatisch) → `hostname` als `rp_id`, `scheme://netloc` als `origin`
3. **Fallback** → Env-Vars (localhost defaults)

⚠️ **Wichtig:** Nie `x-forwarded-host` für rp_id verwenden — dieser Header kann leer sein
und ergibt dann `"http://"` → `urlparse` → `hostname=None` → falscher Fallback.
Der `origin`-Header ist zuverlässig und reicht vollständig.

### Flow
```
GET /api/status → { auth_enabled, needs_setup }
  ↓
needs_setup=true  → Setup screen (create first admin)
needs_setup=false → Login screen
  ↓ JWT stored in localStorage
App loads
```

### Endpoints
```
GET  /api/status                          — public
POST /api/auth/setup                      — first admin (public)
POST /api/auth/login                      — password login (public)
GET  /api/auth/me                         — current user (auth)
POST /api/auth/change-password            — (auth)
POST /api/auth/passkeys/register/begin    — (auth, HTTPS only)
POST /api/auth/passkeys/register/complete — (auth, HTTPS only)
POST /api/auth/passkeys/login/begin       — (public, HTTPS only)
POST /api/auth/passkeys/login/complete    — (public, HTTPS only)
GET  /api/auth/passkeys                   — list my passkeys (auth)
DELETE /api/auth/passkeys/{id}            — delete passkey (auth)
GET  /api/admin/users                     — admin only
POST /api/admin/users                     — admin only
DELETE /api/admin/users/{id}              — admin only
```

---

## i18n System

**Dateien:** `svelte/src/locales/de.json`, `en.json`, `it.json`
**Store:** `svelte/src/lib/i18n.js` — reaktiver `t`-Store, `$t('key')` in Komponenten

### Abgedeckte Bereiche (alle übersetzt in DE/EN/IT)
- Navigation, Settings-Tabs, alle Labels + Buttons in Settings
- Dashboard, MyTrips (inkl. Tabs), PriceRadar (inkl. Tabs + alle Formular-Labels)
- Discover, Onboarding, Login, Setup
- Radar-spezifische Keys: `radarFrom`, `radarTo`, `radarDate`, `radarReturn`,
  `radarAdults`, `radarChildren`, `radarBaggage`, `radarSeat`, `radarRegion`,
  `radarType`, `radarCheckin`, `radarCheckout`, `radarDest`, `radarRooms`,
  `radarSource`, `radarStart`, `radarNewTracker`, `radarActiveTrackers`,
  `radarNoKey`, `radarNoBackend`, `radarRequired`
- Settings: `settingsMyspace`, alle Account/Admin-Strings
- Discover: `discoverProvider`, `discoverQuery`, `discoverPlaceholder`,
  `discoverBtn`, `discoverLoading`

### Regel
Immer alle 3 Locale-Dateien gleichzeitig updaten wenn neue Keys hinzukommen.
Tabs nie hardcodiert — immer `$derived([...])` mit `$t('key')`.

---

## PWA / Favicon

- `svelte/static/favicon.svg` — oranges Rund-Rechteck (#D95D39) mit Kompassrose
- `svelte/static/manifest.webmanifest` — PWA-Manifest (name, theme_color, icons)
- `svelte/static/icons/icon-192.png` + `icon-512.png` — generiert mit Pillow
- `svelte/src/app.html` — verlinkt favicon.svg + manifest

---

## Settings — Mein Bereich (myspace Tab)

- Per-user Einstellungen (Dawarich, ActualBudget, Home-Koordinaten)
- **Geocoding:** Ortsname eingeben + 📍 Button → Nominatim (OpenStreetMap) → lat/lon wird automatisch befüllt. Enter-Taste triggert ebenfalls Suche.
- **ActualBudget Dateiname:** Hilfetext direkt im Feld + im FieldGuide (Tab "Reisen") erklärt:
  Budget-Name oben links in ActualBudget anklicken → ID aus der URL entnehmen

---

## Multi-User Architecture

### Data Isolation
| Table | Scope | Notes |
|-------|-------|-------|
| `trackers` | Per-user | `user_id` column |
| `gf_trackers` | Per-user | |
| `homair_trackers` | Per-user | |
| `booking_trackers` | Per-user | |
| `detected_trips` | Per-user | Dawarich per user |
| `user_data` | Per-user | trips, budget, bucketlist |
| `user_settings` | Per-user | dawarich, actualbudget, home coords |
| `settings` | Global (admin) | API keys, notifications |
| `webauthn_credentials` | Per-user | passkeys |

### Settings Split
- **Global** `GET/POST /api/settings` — SerpAPI, Gemini, OpenAI, Telegram, Gotify
- **Per-user** `GET/POST /api/settings/user` — Dawarich, ActualBudget, Home coords

### AUTH_ENABLED=false (guest mode)
- Returns `GUEST_USER = {id: 0, role: "admin"}`
- DB functions with `user_id=0` → no filter → sees all data
- Fully backward compatible

---

## Security Headers (nginx.conf)

Currently set:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self' ...`
- `Cross-Origin-Resource-Policy: same-origin`
- `Cross-Origin-Opener-Policy: same-origin` (required for WebAuthn)

**TODO — set in Zoraxy:**
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`

---

## Beta-Specific Files (differ from main)

| File | Beta change |
|------|-------------|
| `Header.svelte` | BETA badge + build date |
| `docker/Dockerfile.frontend` | `ARG BUILD_DATE` |
| `docker-compose.yml` | Ports 8767/8768, auth env vars |
| `backend/main.py` | `WANDERSUITE_CHANNEL=beta` |
| `.env.example` | Beta ports + auth + WebAuthn |

---

## File Structure

```
wandersuite/
├── svelte/src/
│   ├── lib/
│   │   ├── stores.js          ← all state, loadSettingsFromBackend()
│   │   ├── api.js             ← HTTP client with JWT injection
│   │   ├── i18n.js            ← reactive t() derived store
│   │   └── components/
│   │       ├── AppShell.svelte
│   │       ├── Header.svelte  ← BETA badge + version
│   │       ├── Sidebar.svelte ← logout button when auth enabled
│   │       ├── Login.svelte   ← passkey + password fallback
│   │       ├── Setup.svelte   ← first admin account
│   │       ├── Settings.svelte ← tabs: basic/integrations/apis/notifications/myspace/account/admin
│   │       ├── PasskeyManager.svelte
│   │       ├── FieldGuide.svelte ← ActualBudget filename docs
│   │       └── pages/
│   │           ├── Dashboard.svelte
│   │           ├── PriceRadar.svelte  ← vollständig i18n
│   │           ├── MyTrips.svelte     ← tabs i18n, journal tab included
│   │           └── Discover.svelte    ← vollständig i18n
│   ├── locales/
│   │   ├── de.json
│   │   ├── en.json
│   │   └── it.json
│   └── routes/
│       ├── +layout.svelte     ← gate: onboarding → setup → login → app
│       └── +page.svelte
├── svelte/static/
│   ├── favicon.svg
│   ├── manifest.webmanifest
│   └── icons/
│       ├── icon-192.png
│       └── icon-512.png
├── backend/
│   ├── main.py                ← APP_VERSION, CHANNEL
│   ├── database.py            ← all tables with user_id
│   ├── auth_db.py             ← users + webauthn_credentials
│   ├── auth_jwt.py            ← JWT + GUEST_USER
│   ├── settings_manager.py    ← global + per-user settings
│   ├── dawarich.py            ← sync_trips(user_id=)
│   └── routes/
│       ├── auth.py            ← login, setup, admin
│       ├── passkey.py         ← WebAuthn, _get_rp() auto-detection
│       ├── settings.py        ← /api/settings + /api/settings/user
│       ├── trackers.py        ← user_id aware
│       ├── google_flights.py  ← user_id aware
│       ├── accommodations.py  ← user_id aware
│       ├── userdata.py        ← per user_id
│       └── dawarich.py        ← per user_id
├── docker/
│   ├── Dockerfile             ← backend
│   ├── Dockerfile.frontend    ← multi-stage node→nginx
│   └── nginx.conf             ← security headers + /api/ proxy
└── docker-compose.yml         ← all env vars incl. AUTH_ENABLED
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

## Open / Next Steps

### Erledigt (diese Session)
- [x] Onboarding: `window.location.origin` als Backend-URL Vorschlag
- [x] Passkeys: `email` aus `RegisterBeginPayload` entfernt (kommt aus JWT)
- [x] Passkeys: `_get_rp()` leitet `rp_id` + `origin` aus HTTP `Origin`-Header ab — funktioniert hinter Zoraxy ohne .env-Konfiguration
- [x] Passkeys: `attestation="none"` (String) entfernt — py-webauthn erwartet Enum oder Default
- [x] i18n: Settings-Tabs, alle Labels + Buttons vollständig übersetzt (DE/EN/IT)
- [x] i18n: PriceRadar — Tabs, alle Formular-Labels, Section-Header, Buttons
- [x] i18n: MyTrips — Tabs auf `$t()` umgestellt
- [x] i18n: Discover — alle Labels + Buttons
- [x] Favicon: `favicon.svg` + `manifest.webmanifest` + `icon-192.png` + `icon-512.png`
- [x] Settings Mein Bereich: Geocoding-Suche für Home-Koordinaten (Nominatim)
- [x] Settings Mein Bereich: ActualBudget mit Icon-Badge + Hilfetext für Dateiname
- [x] FieldGuide: Schritt-für-Schritt Erklärung ActualBudget Dateiname

### Roadmap (beta)
- [ ] Scratch Map (jsvectormap) in MyTrips
- [ ] Price history chart (Chart.js) in PriceRadar
- [ ] Mietwagen tab in PriceRadar
- [ ] Discord webhook notifications
- [ ] Currency toggle (EUR/USD/GBP)
- [ ] HSTS header in Zoraxy setzen

### Phase 3 (future)
- [ ] Multi-user data separation fully tested
- [ ] Merge stable features to `main`
