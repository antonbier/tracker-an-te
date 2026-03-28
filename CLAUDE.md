# CLAUDE.md – WanderSuite Refactoring Log

Dieses Dokument beschreibt alle Änderungen, die Claude (claude-sonnet-4-6) im Rahmen der ES-Module-Refactorings durchgeführt hat.

---

## PR #1 – Monolith → ES-Module Basis

**Branch:** `refactor/es-modules`  
**Datum:** 2026-03-28  
**Status:** ✅ Gemerged (oder offen für Review)

Der ~1400-zeilige Inline-`<script>`-Block in `frontend/index.html` wurde herausgelöst und durch `<script type="module" src="js/main.js">` ersetzt. Gleichzeitig wurden die ersten Kernmodule angelegt.

### Neue Dateien (PR #1)
| Datei | Inhalt |
|-------|--------|
| `frontend/js/core/state.js` | Globaler App-State als ES-Exports + Setter |
| `frontend/js/core/api.js` | `api()` HTTP-Client + `checkApiStatus()` |
| `frontend/js/ui/i18n.js` | `loadLocale()`, `t()`, `applyTranslations()`, `setLang()` |
| `frontend/js/ui/nav.js` | `navigate()`, `toggleSidebar()`, `closeSidebar()` |
| `frontend/js/main.js` | Entry Point (damals noch mit Monolith-Code) |
| `frontend/index.html` | Bereinigt: 3155 → 1748 Zeilen (−43%) |

---

## PR #2 – Feature-Module: vollständige Modularisierung

**Branch:** `refactor/feature-modules`  
**Datum:** 2026-03-28  
**Status:** ✅ Bereit für Review

Der verbleibende Monolith-Code in `main.js` wurde vollständig in Fach-Module aufgeteilt. `main.js` besteht jetzt nur noch aus Imports, `window.*`-Bindungen und dem `DOMContentLoaded`-Init-Block.

### Neue Dateien (PR #2)
| Datei | Extrahierte Funktionen |
|-------|------------------------|
| `frontend/js/ui/toast.js` | `toast()` |
| `frontend/js/ui/settings.js` | `openSettings`, `closeSettings`, `saveSettings`, `loadSerpApiQuota`, `backdropClick`, `switchTab`, `toggleTheme` |
| `frontend/js/app/ryanair.js` | `toggleBag`, `addTracker`, `loadTrackers`, `renderTrackers`, `selectTracker`, `renderStats`, `renderChart`, `renderTable`, `scrapeNow`, `deleteTracker`, `togglePause`, `checkDawarich`, `generateIdeas`, `renderRecommendations` |
| `frontend/js/app/budget.js` | `toggleActualSync`, `addTrip`, `syncActualBudget`, `updateBudget`, `renderBudget`, `removeTrip`, `loadExpenses`, `filterExpenses`, `renderExpenseTable` |
| `frontend/js/app/dashboard.js` | `loadDashboard`, `loadDashTrackers`, `loadDashBudget`, `loadDashTrips` |
| `frontend/js/app/googleflights.js` | `addGFTracker`, `loadGFTrackers`, `renderGFTrackers`, `scrapeGFTracker`, `deleteGFTracker` |
| `frontend/js/app/homair.js` | `addHomairTracker`, `loadHomairTrackers`, `renderHomairTrackers`, `scrapeHomairTracker`, `deleteHomairTracker` |
| `frontend/js/app/booking.js` | `addBookingTracker`, `loadBookingTrackers`, `renderBookingTrackers`, `scrapeBookingTracker`, `deleteBookingTracker` |
| `frontend/js/app/journal.js` | `loadJournalTrips`, `renderJournalTrips`, `syncJournal`, `deleteJournalTrip` |
| `frontend/js/app/onboarding.js` | `checkOnboarding`, `closeOnboarding`, `obNext`, `obBack`, `updateObStep`, `openFieldGuide`, `closeFieldGuide` |

### Ergebnis main.js
- **Vorher:** 1493 Zeilen (Monolith)  
- **Nachher:** 156 Zeilen (nur Imports + window.\* + DOMContentLoaded)

---

## Finale Dateistruktur

```
frontend/
├── index.html                       ← 1748 Zeilen, sauber
└── js/
    ├── main.js                      ← 156 Zeilen: Imports + window.* + Init
    ├── core/
    │   ├── state.js                 ← App-State mit Settern
    │   └── api.js                   ← HTTP-Client
    └── ui/
    │   ├── i18n.js                  ← Internationalisierung
    │   ├── nav.js                   ← Navigation + Sidebar
    │   ├── toast.js                 ← Toast-Notifications
    │   └── settings.js              ← Settings-Modal
    └── app/
        ├── ryanair.js               ← Ryanair Tracker + Chart + Discover
        ├── budget.js                ← Budget, Trips, ActualBudget, Expenses
        ├── dashboard.js             ← Dashboard-Karten
        ├── googleflights.js         ← Google Flights Tracker
        ├── homair.js                ← Homair Unterkunfts-Tracker
        ├── booking.js               ← Booking.com Tracker
        ├── journal.js               ← Travel Journal (Dawarich)
        └── onboarding.js            ← Onboarding + Field Guide
```

---

## Roadmap

- [x] `js/core/state.js` – Zentraler App-State
- [x] `js/core/api.js` – HTTP-Client
- [x] `js/ui/i18n.js` – Internationalisierung
- [x] `js/ui/nav.js` – Navigation
- [x] `js/ui/toast.js` – Toast-Notifications
- [x] `js/ui/settings.js` – Settings-Modal
- [x] `js/app/ryanair.js` – Ryanair Tracker
- [x] `js/app/budget.js` – Budget & ActualBudget
- [x] `js/app/dashboard.js` – Dashboard
- [x] `js/app/googleflights.js` – Google Flights
- [x] `js/app/homair.js` – Homair
- [x] `js/app/booking.js` – Booking.com
- [x] `js/app/journal.js` – Travel Journal
- [x] `js/app/onboarding.js` – Onboarding & Field Guide
- [ ] Skeleton Loaders
- [ ] CSV Export
- [ ] Currency Toggle
- [ ] Notifications (Telegram/Discord/Gotify)
- [ ] SerpAPI Quota Tracking
- [ ] Price Threshold Alerts
- [ ] Mobile PWA Support

---

## Technische Hinweise

**Warum `window.*`-Bindungen?**  
Da `<script type="module">` seinen Scope nicht global teilt, sind alle Funktionen, die per `onclick="fn()"` im HTML aufgerufen werden, explizit an `window` gebunden. Kein HTML-Code musste dafür geändert werden.

**Zirkuläre Imports vermieden durch:**  
Dynamische `import()` an Stellen, wo Module sich gegenseitig brauchen würden (z.B. `journal.js` importiert `dashboard.js` und `settings.js` erst zur Laufzeit).
