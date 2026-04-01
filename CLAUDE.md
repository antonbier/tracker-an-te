# CLAUDE.md — WanderSuite AI Assistant Context (BETA branch)

**⚠️ You are on the `beta` branch.**
New features are developed here, tested, then merged into `main`.

---

## Repository
`antonbier/tracker-an-te` — GitHub token required for all API operations.

---

## Branch Strategy

| Branch | Purpose | Ports (Unraid) | Version |
|--------|---------|----------------|---------|
| `main` | Stable, production | 8765 / 8766 | `1.0.0` |
| `beta` | New features, testing | 8767 / 8768 | `beta-YYYY-MM-DD HH:MM` |

---

## Stack

- **Frontend:** Svelte 5 + SvelteKit + Tailwind CSS v4 → `svelte/`
- **Backend:** FastAPI + SQLite + APScheduler → `backend/`
- **Deploy:** Docker Compose (Unraid on-prem)
- **Reverse Proxy:** Zoraxy on Unraid (HTTPS + external access)

---

## Deployment — Unraid (beta)

### Verzeichnis
```
/mnt/user/appdata/wandersuite-beta/
```

### Erstinstallation
```bash
mkdir -p /mnt/user/appdata/wandersuite-beta
cd /mnt/user/appdata/wandersuite-beta
git clone https://github.com/antonbier/tracker-an-te .
git checkout beta
cp .env.example .env
nano .env
mkdir -p data
BUILD_DATE="$(date '+%Y-%m-%d %H:%M')" docker compose up -d --build
```

### Update
```bash
cd /mnt/user/appdata/wandersuite-beta
git pull
BUILD_DATE="$(date '+%Y-%m-%d %H:%M')" docker compose up -d --build
```

### .env (beta)
```env
HOST_PORT=8767
BACKEND_PORT=8768
TZ=Europe/Rome
DATA_DIR=/mnt/user/appdata/wandersuite-beta/data
APP_SECRET=<generate: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
AUTH_ENABLED=true
JWT_SECRET=<generate: python3 -c "import secrets; print(secrets.token_hex(32))">
WEBAUTHN_RP_ID=<deine-domain.de>
WEBAUTHN_RP_NAME=WanderSuite
WEBAUTHN_ORIGIN=https://<deine-domain.de>
```

---

## Aktueller Stand (Session-Ende)

### ✅ Läuft
- Beta läuft auf Unraid (:8767 Frontend, :8768 Backend)
- Frontend ist von außen über Zoraxy Reverse Proxy erreichbar (HTTPS)
- Docker Multi-Stage Build funktioniert (Node 20 → Nginx)
- BETA Badge + Build-Datum im Header
- Security Headers in nginx.conf (CSP, X-Frame-Options, X-Content-Type, Referrer-Policy, CORP, COOP)

### ⚠️ Offen / Nächste Schritte
1. **Backend extern erreichbar machen**
   - Backend läuft intern auf Port 8768, ist aber von außen nicht erreichbar
   - Lösung: In Zoraxy einen zweiten Proxy-Eintrag anlegen für Backend-Port 8768
   - ODER: Nginx als einziger Eintrag nach außen, /api/ wird intern weitergeleitet (bevorzugt)
   - **Bevorzugte Lösung:** Nur Frontend (8767) nach außen exponieren — Nginx proxied /api/ intern zu backend:8000
   - Backend-URL im Onboarding dann auf die externe Frontend-URL setzen (z.B. https://wandersuite.deine-domain.de)
   - Kein separater Backend-Zugriff von außen nötig

2. **Auth testen**
   - AUTH_ENABLED=true ist gesetzt, aber /api/status gibt noch false zurück
   - Problem war: AUTH_ENABLED fehlte in docker-compose.yml environment → bereits gefixt
   - Nach git pull + docker compose down + docker compose up -d sollte /api/status {"auth_enabled":true,"needs_setup":true} zurückgeben
   - Dann: Onboarding → Backend-URL = https://wandersuite.deine-domain.de → Setup-Screen erscheint

3. **Passkeys testen**
   - Erst wenn HTTPS läuft und Backend erreichbar ist
   - WEBAUTHN_RP_ID = domain ohne https:// (z.B. wandersuite.deine-domain.de)
   - WEBAUTHN_ORIGIN = https://wandersuite.deine-domain.de
   - Nach Login: Settings → Account → Passkey hinzufügen

4. **HSTS in Zoraxy setzen**
   - Nginx kann HSTS nicht setzen (nur HTTP intern)
   - In Zoraxy Custom Header hinzufügen:
     `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`

---

## Architektur (Netzwerk)

```
Internet
  │
  └─► Zoraxy Reverse Proxy (Unraid, Port 443)
        │   HTTPS terminiert hier
        │   HSTS Header hier setzen
        │
        └─► wandersuite-beta-frontend (Nginx :8767)
              │
              ├─► /* ──────────► Svelte SPA (dist/)
              └─► /api/* ──────► wandersuite-beta-backend:8000 (intern)
                                  kein externer Port nötig!
```

**Wichtig:** Nur Port 8767 (Frontend/Nginx) muss nach außen erreichbar sein.
Das Backend ist intern über Docker-Netzwerk erreichbar (backend:8000).
Nginx proxied /api/ automatisch weiter.

---

## Multi-User Architektur

### Data Isolation
| Table | Per-User | Notes |
|-------|----------|-------|
| `trackers` | ✅ `user_id` | jeder sieht nur eigene |
| `gf_trackers` | ✅ `user_id` | |
| `homair_trackers` | ✅ `user_id` | |
| `booking_trackers` | ✅ `user_id` | |
| `detected_trips` | ✅ `user_id` | Dawarich pro User |
| `user_data` | ✅ `user_id` | trips, budget, bucketlist |
| `user_settings` | ✅ `user_id` | dawarich, actualbudget, coords |
| `settings` | ❌ Global | API keys, notifications (Admin) |
| `webauthn_credentials` | ✅ `user_id` | Passkeys pro User |

### Settings Split
- **Global (Admin):** `POST /api/settings` — SerpAPI, Gemini, OpenAI, Telegram, Gotify
- **Per-User:** `GET/POST /api/settings/user` — Dawarich, ActualBudget, Home-Koordinaten

### AUTH_ENABLED=false (Guest Mode)
- `get_current_user()` → `GUEST_USER = {id: 0, role: "admin"}`
- DB-Funktionen mit `user_id=0` → kein Filter → sieht alle Daten
- Vollständig rückwärtskompatibel

---

## Auth & Passkeys

### Endpoints
```
POST /api/auth/setup                     — Ersten Admin erstellen (needs_setup=true)
POST /api/auth/login                     — Email + Passwort → JWT
POST /api/auth/passkeys/register/begin   — Passkey-Registrierung starten (eingeloggt)
POST /api/auth/passkeys/register/complete — Passkey speichern
POST /api/auth/passkeys/login/begin      — Passkey-Login starten
POST /api/auth/passkeys/login/complete   — Passkey verifizieren → JWT
GET  /api/auth/passkeys                  — Meine Passkeys auflisten
DELETE /api/auth/passkeys/{id}           — Passkey löschen
GET  /api/status                         — {auth_enabled, needs_setup}
```

### Frontend Gate (+layout.svelte)
```
kein apiUrl/onboarding → Onboarding
  ↓
GET /api/status → needs_setup=true → Setup (ersten Admin erstellen)
  ↓
auth_enabled=true + kein JWT → Login (Passkey oder Passwort)
  ↓
App
```

---

## Bekannte Bugs / Import-Fixes (Multi-User Refactoring)

Beim Multi-User Refactoring wurden Funktionen umbenannt. Bereits gefixt mit Aliases:
- `save_snapshot` → `save_price_snapshot` (scheduler.py)
- `get_snapshots` → `get_price_history` (routes/prices.py)
- `scrape_google_flights` → `fetch_google_flights` (routes/google_flights.py)
- `scrape_homair` → `fetch_homair` (routes/accommodations.py)
- `scrape_booking` → `fetch_booking` (routes/accommodations.py)

Falls weitere ImportError auftauchen: Fehlermeldung zeigt immer den genauen Namen.
Fix-Pattern: `from module import real_name as expected_name`

---

## Security Headers (nginx.conf)
Bereits implementiert:
- ✅ Content-Security-Policy
- ✅ X-Content-Type-Options: nosniff
- ✅ X-Frame-Options: SAMEORIGIN
- ✅ Referrer-Policy: strict-origin-when-cross-origin
- ✅ Cross-Origin-Resource-Policy: same-origin
- ✅ Cross-Origin-Opener-Policy: same-origin (required for WebAuthn)
- ⏳ HSTS → muss in Zoraxy als Custom Header gesetzt werden

---

## Beta-spezifische Dateien (differ from main)

| Datei | Beta-Änderung |
|-------|---------------|
| `Header.svelte` | BETA Badge + Build-Datum |
| `docker/Dockerfile.frontend` | ARG BUILD_DATE |
| `docker/nginx.conf` | Security Headers |
| `docker-compose.yml` | Ports 8767/8768, AUTH_ENABLED, JWT_SECRET, WEBAUTHN_* |
| `backend/main.py` | version = beta-{BUILD_DATE}, CHANNEL=beta |
| `backend/database.py` | user_id auf allen Content-Tabellen |
| `backend/auth_db.py` | webauthn_credentials + challenges Tabellen |
| `backend/routes/passkey.py` | WebAuthn Endpoints |
| `backend/settings_manager.py` | Global vs. Per-User Settings |
| `.env.example` | Beta-Ports + AUTH + WEBAUTHN vars |

---

## Roadmap (beta)

### In Arbeit
- [ ] Backend via Zoraxy extern erreichbar (nur /api/ über Nginx-Proxy)
- [ ] Auth-Flow vollständig testen (Setup → Login → Passkey)

### Geplant
- [ ] Scratch Map (jsvectormap) in Meine Reisen
- [ ] Preisverlauf Chart (Chart.js) in PriceRadar
- [ ] Mietwagen-Tab in Preis-Radar
- [ ] Discord Webhook Notifications
- [ ] Currency Toggle (EUR/USD/GBP)
- [ ] Skeleton Loaders

### Merge → main (wenn stabil)
- Multi-User Architektur
- Passkey Auth
- Security Headers

---

## GitHub API Workflow (für Claude)
Immer SHA holen vor dem Schreiben. Direkt auf `beta` Branch arbeiten.
```python
url = f'https://api.github.com/repos/{REPO}/contents/{path}?ref=beta'
body = {'message': msg, 'content': base64_content, 'branch': 'beta', 'sha': sha}
```
