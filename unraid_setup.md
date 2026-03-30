# WanderSuite — Unraid Setup Guide

## Voraussetzungen

- Unraid 6.12+ mit Docker aktiviert
- **Compose Manager** Plugin installiert (Community Applications → suche "Compose Manager")
- **Node.js** auf Unraid verfügbar — entweder via:
  - Community Applications → "NerdTools" → `nodejs` aktivieren
  - oder einmalig per Docker Node-Image (s.u. Option B)

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

### 4. Svelte Frontend bauen

**Option A — NerdTools Node.js auf Unraid (empfohlen):**
```bash
cd /mnt/user/appdata/wandersuite/svelte
npm ci
npm run build
cd ..
```

**Option B — via Docker (falls kein Node.js auf Unraid installiert):**
```bash
docker run --rm \
  -v /mnt/user/appdata/wandersuite/svelte:/app \
  -w /app \
  node:20-alpine \
  sh -c "npm ci && npm run build"
```

Der Build landet in `svelte/dist/` — genau dort, wo Nginx es erwartet.

### 5. PWA Icons kopieren

```bash
cp -r /mnt/user/appdata/wandersuite/frontend/icons \
      /mnt/user/appdata/wandersuite/svelte/dist/icons
```

### 6. Container starten

```bash
cd /mnt/user/appdata/wandersuite
docker compose up -d --build
```

Beim ersten Start wird das Backend-Image gebaut (~2 Min).

---

## Zugriff

| Service | URL |
|---------|-----|
| **WanderSuite** | `http://unraid-ip:8765` |
| **Backend API direkt** | `http://unraid-ip:8766` |
| **API Docs (Swagger)** | `http://unraid-ip:8766/docs` |

Beim ersten Aufruf startet der Onboarding-Wizard automatisch.
Backend URL dort eingeben: `http://unraid-ip:8766`

---

## Updates einspielen

```bash
cd /mnt/user/appdata/wandersuite

# 1. Neuen Code holen
git pull

# 2. Svelte neu bauen (nur wenn svelte/** geändert hat)
cd svelte && npm ci && npm run build && cd ..
cp -r frontend/icons svelte/dist/icons

# 3. Backend neu bauen (nur wenn backend/** oder Dockerfile geändert hat)
docker compose up -d --build backend

# 4. Frontend-Container neu starten (liest dist/ direkt — meist reicht restart)
docker compose restart frontend
```

> **Tipp:** `git log --oneline -5` zeigt was sich geändert hat —
> so siehst du ob ein Backend-Rebuild wirklich nötig ist.

---

## Compose Manager Integration (Unraid GUI)

1. Unraid → Apps → Compose Manager
2. **Add Stack** → Name: `wandersuite`
3. Path: `/mnt/user/appdata/wandersuite/docker-compose.yml`
4. Stack lässt sich dann über die GUI starten/stoppen
5. Updates aber weiterhin per Terminal (`git pull` + `npm run build`)

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
├── svelte/
│   ├── src/                    ← Svelte Quellcode
│   ├── dist/                   ← Build Output → Nginx Volume
│   │   └── icons/              ← PWA Icons (nach build kopieren)
│   └── package.json
├── backend/                    ← FastAPI Python Code
├── frontend/
│   └── icons/                  ← Quell-Icons (bleiben im Repo)
├── docker/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── .env                        ← ⚠️ Geheim halten, nie committen!
```

---

## Troubleshooting

**Frontend zeigt leere Seite / 404:**
```bash
ls /mnt/user/appdata/wandersuite/svelte/dist/
# Muss index.html enthalten — falls nicht: Schritt 4 wiederholen
```

**Backend nicht erreichbar im Onboarding:**
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
→ Reisedaten (Trips, Budget, Bucket List) sind NICHT betroffen — liegen unverschlüsselt.

**Container startet nicht nach git pull:**
```bash
docker compose down
docker compose up -d --build
# Bei hartnäckigen Problemen:
docker compose down --remove-orphans
docker image prune -f
docker compose up -d --build
```
