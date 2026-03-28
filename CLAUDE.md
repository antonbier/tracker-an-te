# CLAUDE.md – WanderSuite Refactoring Log

Dieses Dokument beschreibt alle Änderungen, die Claude (claude-sonnet-4-6) im Rahmen des ES-Module-Refactorings durchgeführt hat.

---

## Refactoring: Monolith → ES-Module

**Branch:** `refactor/es-modules`  
**Datum:** 2026-03-28  
**Ziel:** Die ~1400-zeilige Inline-`<script>`-Block in `frontend/index.html` wurde in native ES-Module aufgeteilt, ohne Build-Tools (kein Webpack/npm) und ohne dass bestehende `onclick="..."` Handler im HTML kaputtgehen.

---

## Neue Dateistruktur

```
frontend/
├── index.html                  ← bereinigt (1748 statt 3155 Zeilen)
└── js/
    ├── main.js                 ← Entry Point, alle window.*-Bindungen
    ├── core/
    │   ├── state.js            ← Zentraler App-State (Exports + Setter)
    │   └── api.js              ← api(), checkApiStatus()
    └── ui/
        ├── i18n.js             ← loadLocale(), t(), applyTranslations(), setLang()
        └── nav.js              ← navigate(), toggleSidebar(), closeSidebar()
```

---

## Schritt-für-Schritt-Übersicht

### Schritt 1 – Analyse
- `frontend/index.html` hatte 3155 Zeilen, davon ~1407 Zeilen reines JavaScript in einem `<script>`-Block (Zeilen 1742–3148).
- Identifiziert: 70+ Funktionen, 9 globale State-Variablen, 1 `DOMContentLoaded`-Init-Block.

### Schritt 2 – Core-Module (`frontend/js/core/`)

**`state.js`**  
- Exportiert alle globalen Zustandsvariablen: `TRANSLATIONS`, `currentLang`, `API_URL`, `selectedTrackerId`, `priceChart`, `selectedBags`, `currentPage`, `trips`, `obStep`, `allExpenses`
- Zu jedem `let` gibt es einen Setter (`setCurrentLang()`, `setApiUrl()`, etc.), damit Module den State ändern können ohne direkte Variablenzuweisung über Modulgrenzen hinweg.

**`api.js`**  
- Exportiert `api(path, opts)`: zentraler HTTP-Client mit Error-Handling
- Exportiert `checkApiStatus()`: prüft `/health` und setzt den Status-Dot im UI

### Schritt 3 – UI-Module (`frontend/js/ui/`)

**`i18n.js`**  
- Exportiert `loadLocale(lang)`: lädt JSON-Sprachdateien aus `/locales/`
- Exportiert `t(key)`: Übersetzungsfunktion mit Fallback auf Deutsch
- Exportiert `applyTranslations()`: aktualisiert alle `data-i18n`-Elemente im DOM
- Exportiert `setLang(lang)`: Sprachwechsel inkl. Re-Render

**`nav.js`**  
- Exportiert `navigate(page)`: wechselt aktive Seite + Sidebar-Handling + Lazy-Init der Untermodule
- Exportiert `toggleSidebar()` / `closeSidebar()`: Hamburger-Menü-Logik

### Schritt 4 – Entry Point (`frontend/js/main.js`)
- Importiert alle neuen Module
- Enthält den gesamten bisherigen Monolith-Code (alle übrigen Funktionen) – bereit für weiteres Refactoring in späteren PRs
- Bindet **alle** benötigten Funktionen explizit an `window.*`, damit `onclick="navigate(...)"` und ähnliche Inline-Handler weiterhin funktionieren

### Schritt 5 – HTML-Update (`frontend/index.html`)
- Der ~1407-zeilige `<script>`-Block wurde entfernt
- Ersetzt durch: `<script type="module" src="js/main.js"></script>`
- Dateigröße: 3155 → 1748 Zeilen (−43%)

---

## Warum kein vollständiges Aufteilen aller 70 Funktionen?

Der Scope dieses PRs ist bewusst konservativ:
- **Risiko minimieren**: Ein vollständiges Aufteilen aller Funktionen (Ryanair, Budget, Dashboard, Journal, etc.) in je eigene Module würde viele zirkuläre Import-Abhängigkeiten erfordern.
- **Schrittweise vorgehen**: Der Monolith lebt jetzt in `main.js` und ist **bereit** für weitere Extraktion in `js/app/ryanair.js`, `js/app/budget.js` etc.
- **Sofort lauffähig**: Die App funktioniert nach diesem PR identisch wie zuvor.

---

## Nächste Schritte (Roadmap)

- [ ] `js/app/ryanair.js` – Tracker-Logik auslagern
- [ ] `js/app/budget.js` – Budget & Trips
- [ ] `js/app/dashboard.js` – Dashboard-Karten
- [ ] `js/app/journal.js` – Journal & Expenses
- [ ] `js/app/googleflights.js`, `homair.js`, `booking.js`
- [ ] `js/ui/settings.js` – Settings-Modal
- [ ] `js/ui/toast.js` – Toast-Notifications
- [ ] `js/ui/onboarding.js` – Onboarding-Flow
