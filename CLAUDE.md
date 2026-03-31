# CLAUDE.md — WanderSuite AI Assistant Context (BETA branch)

**⚠️ You are on the `beta` branch.**
- New features are developed here first
- Stable, tested features get merged into `main`
- Never commit breaking changes without testing
- Beta runs on ports 8767 (frontend) / 8768 (backend) on Unraid

For full architecture reference see `main` branch CLAUDE.md.

---

## Branch Strategy

| Branch | Purpose | Ports | Version |
|--------|---------|-------|---------|
| `main` | Stable, production | 8765 / 8766 | `1.0.0` |
| `beta` | New features, testing | 8767 / 8768 | `beta-YYYY-MM-DD HH:MM` |

## Workflow

1. **New feature** → develop on `beta`
2. **Test** on Unraid beta instance (`http://unraid-ip:8767`)
3. **Merge** to `main` via PR when stable
4. **Never** push breaking changes directly to `main`

## Beta-specific files (differ from main)

| File | Beta change |
|------|-------------|
| `svelte/src/lib/components/Header.svelte` | BETA badge + build date shown |
| `docker/Dockerfile.frontend` | `ARG BUILD_DATE` passed through |
| `docker-compose.yml` | Ports 8767/8768, container names `wandersuite-beta-*` |
| `backend/main.py` | `WANDERSUITE_CHANNEL=beta`, version = `beta-{BUILD_DATE}` |
| `.env.example` | Beta ports + DATA_DIR + BUILD_DATE docs |

## Build + Start (beta)

```bash
cd /mnt/user/appdata/wandersuite-beta
git pull
BUILD_DATE="$(date '+%Y-%m-%d %H:%M')" docker compose up -d --build
```

The build date appears in the header next to the BETA badge.

## Merging beta → main

```bash
git checkout main
git merge beta --no-ff -m "merge: <feature description>"
# Remove beta-specific changes (Header badge, docker-compose ports, .env.example)
# Then push
git push origin main
```

---

## Stack (same as main)

- **Frontend:** Svelte 5 + SvelteKit + Tailwind CSS v4
- **Backend:** FastAPI + SQLite + APScheduler
- **Deploy:** Docker Compose (Unraid)

See `main` CLAUDE.md for full architecture, API reference, and design tokens.

---

## Active Development (beta)

Add features being worked on here:
- [ ] Scratch Map (jsvectormap)
- [ ] Mietwagen tab in Preis-Radar
- [ ] Price history chart (Chart.js)
- [ ] Discord webhook notifications
- [ ] Currency toggle (EUR/USD/GBP)
