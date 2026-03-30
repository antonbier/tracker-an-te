# WanderSuite — Unraid Setup Guide

## Voraussetzungen

- Unraid 6.12+ mit Docker aktiviert
- **Compose Manager** Plugin installiert (Community Applications → suche "Compose Manager")
- **Kein Node.js auf dem Host nötig** — der Build läuft vollständig im Docker Multi-Stage Build

---

## Erstinstallation

### 1. Repo klonen

Unraid Terminal öffnen (`Tools → Terminal`) oder SSH:

```bash
mkdir -p /mnt/user/appdata/wandersuite
cd /mnt/user/appdata/wandersuite
git clone https://github.com/antonbier/tracker-an-te .
```

### 2. Data-Verzeichnis anlegen

```bash
mkdir -p /mnt/user/appdata/wandersuite/data
```

### 3. .env anlegen

```bash
cp .env.example .env
nano .env
```

Anpassen:

| Variable | Wert |
|----------|------|
| `HOST_PORT` | `8765` (oder freier Port) |
| `BACKEND_PORT` | `8766` |
| `TZ` | z.B. `Europe/Rome` |
| `DATA_DIR` | `/mnt/user/appdata/wandersuite/data` |
| `APP_SECRET` | Zufälligen Key generieren (s.u.) |

**APP_SECRET generieren:**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
⚠️ Diesen Wert **einmalig setzen und nie mehr ändern** — sonst sind alle verschlüsselten Settings in der DB unleserlich.

### 4. Container starten

```bash
cd /mnt/user/appdata/wandersuite
docker compose up -d --build
```

Beim ersten Start wird das Frontend-Image gebaut (~3–5 Min, Node.js läuft im Container).
Danach cached Docker die npm-Layer — Rebuilds bei Code-Änderungen dauern nur Sekunden.

---

## Zugriff

| Service | URL |
|---------|-----|
| **WanderSuite** | `http://unraid-ip:8765` |
| **Backend API direkt** | `http://unraid-ip:8766` |
| **API Docs (Swagger)** | `http://unraid-ip:8766/docs` |

Beim ersten Aufruf startet der Onboarding-Wizard automatisch.
Backend URL dort eingeben: `http://unraid-ip:8765` (Nginx proxied /api/ intern weiter)

---

## Updates einspielen

```bash
cd /mnt/user/appdata/wandersuite

# 1. Neuen Code holen
git pull

# 2. Container neu bauen und starten
docker compose up -d --build
```

Docker erkennt anhand des Layer-Caches automatisch was sich geändert hat:
- Nur `backend/` geändert → nur Backend-Image wird neu gebaut
- Nur `svelte/` geändert → nur Frontend-Image wird neu gebaut (npm ci cached)
- `package-lock.json` unverändert → npm ci wird übersprungen

> **Tipp:** `git log --oneline -5` zeigt was sich geändert hat.

---

## Architektur

```
Browser
  │
  └─► Nginx :8765
        ├─ /* ──────────────────► Svelte SPA (dist/)
        ├─ /api/* ──────────────► backend:8000 (intern, kein offener Port nötig)
        └─ /health ─────────────► backend:8000/health

Docker Multi-Stage Build:
  Stage 1 (node:20-alpine)  → npm ci + npm run build → dist/
  Stage 2 (nginx:alpine)    → dist/ + nginx.conf → fertig
```

---

## Compose Manager Integration (Unraid GUI)

1. Unraid → Apps → Compose Manager
2. **Add Stack** → Name: `wandersuite`
3. Path: `/mnt/user/appdata/wandersuite/docker-compose.yml`
4. Stack lässt sich dann über die GUI starten/stoppen
5. Updates: Terminal → `git pull` → GUI: Stack neu starten mit "Rebuild"

---

## Reverse Proxy (optional, für externen Zugriff)

Empfohlen: **Nginx Proxy Manager** aus Community Applications.

1. NPM installieren und starten
2. Neuen Proxy Host anlegen:
   - Domain: `wandersuite.deinedomain.de`
   - Forward Hostname: `unraid-ip`
   - Forward Port: `8765`
3. SSL → Let's Encrypt direkt in NPM aktivieren

---

## Verzeichnisstruktur auf Unraid nach Setup

```
/mnt/user/appdata/wandersuite/
├── data/
│   └── tracker.db              ← SQLite DB (nie löschen!)
├── svelte/                     ← Svelte Quellcode (kein dist/ mehr nötig!)
├── backend/                    ← FastAPI Python Code
├── frontend/
│   └── icons/                  ← PWA Icons (werden im Docker-Build kopiert)
├── docker/
│   ├── Dockerfile              ← Backend
│   ├── Dockerfile.frontend     ← Frontend (Multi-Stage)
│   └── nginx.conf
├── docker-compose.yml
└── .env                        ← ⚠️ Geheim halten, nie committen!
```

---

## Troubleshooting

**Frontend zeigt leere Seite / 404:**
```bash
docker compose logs frontend --tail=50
# Build-Fehler? → prüfen ob svelte/package-lock.json im Repo ist
```

**405 Not Allowed bei API-Calls:**
```bash
# Nginx proxied /api/ intern → Backend-URL im Onboarding auf Frontend-URL setzen
# z.B. http://unraid-ip:8765 (NICHT :8766)
docker compose logs frontend | grep -i "upstream"
```

**Backend nicht erreichbar:**
```bash
docker compose logs backend --tail=50
docker compose exec backend curl http://localhost:8000/health
```

**DB-Berechtigungen:**
```bash
chmod -R 755 /mnt/user/appdata/wandersuite/data
```

**APP_SECRET geändert oder vergessen:**
→ Alle verschlüsselten Settings (API Keys, Tokens) in der DB sind verloren.
→ Im Frontend unter Settings alles neu eingeben und speichern.
→ Reisedaten (Trips, Budget, Bucket List) sind NICHT betroffen.

**Container startet nicht nach git pull:**
```bash
docker compose down
docker compose up -d --build
# Bei hartnäckigen Problemen:
docker compose down --remove-orphans
docker image prune -f
docker compose up -d --build
```
