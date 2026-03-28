# CLAUDE.md – WanderSuite Refactoring Log

Dieses Dokument beschreibt alle Änderungen, die Claude (claude-sonnet-4-6) durchgeführt hat.

---

## Deployment-Status

| Umgebung | Branch | Status |
|----------|--------|--------|
| Production (Railway) | `main` | ✅ Beide PRs gemerged – wird via GitHub Action deployed |
| GitHub Pages (Test) | `refactor/feature-modules` | ✅ https://antonbier.github.io/tracker-an-te/ |

### Merge-Historie
| PR | Titel | Gemerged | Main-SHA |
|----|-------|----------|----------|
| #1 | Monolith → ES-Module Basis | 2026-03-28 | `7d4e69db89` |
| #2 | Feature-Module – vollständige Modularisierung | 2026-03-28 | `de9c23b666` |

### Rückgängig machen (falls nötig)
Falls der Deploy fehlschlägt: Auf GitHub bei PR #1 oder #2 den **"Revert"-Button** drücken.
Das erstellt automatisch einen neuen PR der alle Änderungen rückgängig macht.

---

## PR #1 – Monolith → ES-Module Basis

**Branch:** `refactor/es-modules` → `main`
**Datum:** 2026-03-28

Der ~1400-zeilige Inline-`<script>`-Block in `frontend/index.html` wurde herausgelöst
und durch `<script type="module" src="js/main.js">` ersetzt.

### Neue Dateien
| Datei | Inhalt |
|-------|--------|
| `frontend/js/core/state.js` | Globaler App-State als ES-Exports + Setter |
| `frontend/js/core/api.js` | `api()` HTTP-Client + `checkApiStatus()` |
| `frontend/js/ui/i18n.js` | `loadLocale()`, `t()`, `applyTranslations()`, `setLang()` |
| `frontend/js/ui/nav.js` | `navigate()`, `toggleSidebar()`, `closeSidebar()` |
| `frontend/js/main.js` | Entry Point |
| `frontend/index.html` | Bereinigt: 3155 → 1748 Zeilen (−43%) |

---

## PR #2 – Feature-Module: vollständige Modularisierung

**Branch:** `refactor/feature-modules` → `main`
**Datum:** 2026-03-28

Der verbleibende Monolith-Code in `main.js` (1493 Zeilen) wurde vollständig in Fach-Module aufgeteilt.
`main.js` besteht jetzt nur noch aus Imports, `window.*`-Bindungen und DOMContentLoaded-Init (156 Zeilen).

### Neue Dateien
| Datei | Extrahierte Funktionen |
|-------|------------------------|
| `frontend/js/ui/toast.js` | `toast()` |
| `frontend/js/ui/settings.js` | `openSettings`, `closeSettings`, `saveSettings`, `loadSerpApiQuota`, `backdropClick`, `switchTab`, `toggleTheme` |
| `frontend/js/app/ryanair.js` | Tracker CRUD, Chart, Discover/AI – 14 Fns |
| `frontend/js/app/budget.js` | ActualBudget-Sync, Trips, Expense-Tabelle – 9 Fns |
| `frontend/js/app/dashboard.js` | `loadDashboard`, `loadDashTrackers`, `loadDashBudget`, `loadDashTrips` |
| `frontend/js/app/googleflights.js` | Google Flights Tracker CRUD |
| `frontend/js/app/homair.js` | Homair Unterkunfts-Tracker CRUD |
| `frontend/js/app/booking.js` | Booking.com Tracker CRUD |
| `frontend/js/app/journal.js` | `loadJournalTrips`, `renderJournalTrips`, `syncJournal`, `deleteJournalTrip` |
| `frontend/js/app/onboarding.js` | `checkOnboarding`, `closeOnboarding`, `obNext/Back`, `openFieldGuide`, `closeFieldGuide` |

### Bugfix im selben PR
- `fix: use relative path for locale fetch (GitHub Pages compat)` – `i18n.js` nutzte `/locales/` (absolut), jetzt `locales/` (relativ)

---

## Finale Dateistruktur

```
frontend/
├── index.html                  ← 1748 Zeilen (war 3155)
└── js/
    ├── main.js                 ← 156 Zeilen: nur Imports + window.* + Init
    ├── core/
    │   ├── state.js
    │   └── api.js
    └── ui/
    │   ├── i18n.js
    │   ├── nav.js
    │   ├── toast.js
    │   └── settings.js
    └── app/
        ├── ryanair.js
        ├── budget.js
        ├── dashboard.js
        ├── googleflights.js
        ├── homair.js
        ├── booking.js
        ├── journal.js
        └── onboarding.js
```

---

## Roadmap

- [x] `js/core/state.js`
- [x] `js/core/api.js`
- [x] `js/ui/i18n.js`
- [x] `js/ui/nav.js`
- [x] `js/ui/toast.js`
- [x] `js/ui/settings.js`
- [x] `js/app/ryanair.js`
- [x] `js/app/budget.js`
- [x] `js/app/dashboard.js`
- [x] `js/app/googleflights.js`
- [x] `js/app/homair.js`
- [x] `js/app/booking.js`
- [x] `js/app/journal.js`
- [x] `js/app/onboarding.js`
- [ ] Skeleton Loaders
- [ ] CSV Export
- [ ] Currency Toggle
- [ ] Notifications (Telegram/Discord/Gotify)
- [ ] SerpAPI Quota Tracking
- [ ] Price Threshold Alerts
- [ ] Mobile PWA Support

---

## Technische Hinweise

**`window.*`-Bindungen:** Da `<script type="module">` keinen globalen Scope teilt,
sind alle per `onclick="fn()"` aufgerufenen Funktionen explizit an `window` gebunden.
Kein HTML wurde dafür geändert.

**Zirkuläre Imports vermieden** durch dynamische `import()` zur Laufzeit
(z.B. `journal.js` → `dashboard.js` und `settings.js`).

**Kein Build-Tool** – läuft nativ im Browser mit `<script type="module">`.
---

## UX/UI Refresh — "Modern Explorer"

**Datum:** 2026-03-28  
**Commits:** direkt auf `main` (4 Commits)

### Farbschema — Hell als Standard

| Variable | Vorher (dunkel) | Nachher (hell) |
|----------|----------------|---------------|
| `--bg` | `#12100e` | `#f9f8f6` (altes Papier) |
| `--surface` | `#1c1814` | `#ffffff` |
| `--accent` | `#c4622d` | `#D95D39` (Terracotta) |
| `--accent2` | `#e8a020` | `#1E3A5F` (Navy) |
| `--green` | `#3a8c62` | `#2A5C45` (Waldgrün) |

Dark Mode ist jetzt Opt-in via `body.dark-mode` (Toggle in Einstellungen).

### Neue Menüstruktur (workflow-orientiert)

**Vorher:** Sortiert nach Scraper (Ryanair, Google, Homair, Booking, Discover, Budget, Journal)  
**Nachher:** Sortiert nach Nutzer-Workflow:

| Icon | Bereich | Enthält |
|------|---------|---------|
| 🧭 | Übersicht | Dashboard |
| 🎯 | Preis-Radar | Ryanair, Google Flights, Homair, Booking |
| ✨ | Inspiration | Discover / AI-Empfehlungen |
| 🎒 | Meine Reisen | Budget + Reisetagebuch |

### Mobile Bottom Navigation Bar

Auf `@media (max-width: 900px)` wird die Sidebar durch eine feste Bottom-Bar ersetzt (Airbnb/Instagram-Pattern). Die Sidebar bleibt als Slide-in erreichbar via Hamburger.

Bottom-Bar Tabs: 🧭 Übersicht · 🎯 Radar · ✨ Inspiration · 🎒 Reisen

### Ticket-Style Tracker-Items

Tracker-Karten haben jetzt:
- Farbigen Streifen links (wie ein Flugticket)
- Gestrichelte Trennlinie vor den Action-Buttons
- Leichter Schatten + Hover-Lift-Effekt

### Settings — Slide-Panel von rechts

Das Settings-Modal wurde zum Full-Height Slide-Panel umgebaut (rechtsseitig, 520px breit). Drei Tabs:
1. **Allgemein** — Backend-URL, Zeitzone, Erscheinungsbild
2. **Integrationen** — Dawarich, ActualBudget, Home-Koordinaten
3. **APIs & KI** — SerpAPI, Gemini, OpenAI, LLM-Anbieter

### View Transitions API

`document.startViewTransition()` für weiche Seitenübergänge (mit graceful degradation für ältere Browser).

### Geänderte Dateien

| Datei | Änderung |
|-------|---------|
| `frontend/index.html` | CSS-Variablen, Sidebar HTML, Bottom Nav HTML, Settings-Panel CSS |
| `frontend/js/ui/nav.js` | Bottom-Bar Active-Sync, View Transition API |
| `frontend/js/ui/settings.js` | 3. Tab "APIs & KI", Dark-Mode Toggle |
| `frontend/js/main.js` | Theme-Init auf `dark-mode` Klasse umgestellt |
