# Changelog — WanderSuite

Alle nennenswerten Änderungen am Projekt. Format basiert auf [Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.0-beta.1] — 2026-04-17

### Added
- **Dashboard Hero 2-Kachel-Layout**: `HeroPastTrip.svelte` (Nostalgie, Immich-Bild, Reiselust-Modus >6 Monate) + `HeroNextTrip.svelte` (Countdown, Unsplash-Bild) — nebeneinander im Dashboard
- **sessionStorage-Cache** für Hero-Bilder (Immich + Unsplash) — kein Reload bei Navigation
- **Random-Trip + Refresh-Button** in Nostalgie-Kachel: shuffelt durch alle archivierten WS-Trips
- **TravelInspo Nostalgie-Karte**: Refresh-Button (🔄) nach Content-Button im DOM verschoben (paint-order fix), `pr-9` gegen Text-Overlap
- **Browser-Tab-Titel** "WanderSuite" in `app.html`
- **Live-Datumsformat-Vorschau** in Settings BasicTab (`$derived` in Script, kein `{@const}`)
- **@userinfobot Tipp** in NotificationsTab für einfache Telegram Chat-ID Ermittlung
- **Familie gesplittet**: `family_kids` (👶) + `family_teens` (🧒) in allen 4 Sprachen
- **WanderWizzard**: Hilfe-Button aus Header entfernt (Modal-Overlap), Währungsauswahl entfernt (fix EUR)

### Fixed
- **CSP** (`nginx.conf`): Unsplash, Picsum, Google Fonts (googleapis + gstatic), Open-Meteo erlaubt
- **DOM-Warnings**: Password-Inputs in `<form>` gewrappt (Login + AccountTab), `mobile-web-app-capable` Meta-Tag
- **401 bei Seitenstart**: `loadSettingsFromBackend()` sendet jetzt JWT-Header
- **Dashboard Hero Reaktivität**: `wsTripsVersion`-Counter bumpt bei WanderWizzard-Close → `refreshKey`-Prop triggert Re-Load
- **WanderWizzard IATA → Stadtname**: `pickDest()` speichert `a.city` statt `a.iata` als Trip-Destination
- **PriceRadar**: Trip-Link-Dropdown aus Suchergebnis-Bereich entfernt; `✓ Gespeichert`-Feedback nach Save; Stops-Dropdown in Suchergebnissen (wie TrackerCard)
- **Settings Alerts-Tab**: `tabLabels` von `$derived.by()` auf `$derived` umgestellt (Svelte-5-Reaktivitätsbug)
- **Budget Widget "-0 €"**: Guard für `=== 0` in Barausgaben + On-Site-Budget
- **TripHub Mobile**: Datum-Zeile auf `flex-col sm:flex-row` umgestellt; `break-words` für Checklisten-Todos
- **DEIN_TOKEN ReferenceError**: `NotificationsTab.svelte` — Platzhalter `{DEIN_TOKEN}` durch Literal ersetzt
- **Datumsformat global**: `fmtDate()` jetzt in TripCard, TripHub, BucketListTab, TrackerCard
- **plannedEmpty**: "Reiseplaner starten" → "WanderWizzard starten" (de.json)

### Changed
- **HeroSection**: Monolithisch → orchestriert Sub-Komponenten; Budget-Widget als eigenständiger Block
- **PriceRadar SearchResults**: `title`-Tooltip für lange Hotelnamen

---

## [0.9.0] — 2026-04 (QA & Security Sprint)

### Added
- Vollständiger QA-Lauf gegen Beta-Instanz (71 Regressionstests bestanden)
- Security-Audit: Auth, IDOR/Tenant-Isolation, Injection, Sensitive Data Exposure

### Fixed
- 8 Bugs + 9 Warnings aus QA-Lauf behoben

---

## [0.8.0] — 2026-04 (Phase 3 Branding + Widget-Architektur)

### Added
- **WanderWizzard** (ehem. "Trip Planner"): Step 0 Vision-Screen, Y-Kreuzung Step 1, Tinder-Swipe Inspirationskarten
- **TripHub Widget-Architektur**: `WeatherWidget`, `BudgetWidget`, `ChecklistWidget`, `SlotWidget` als eigenständige Komponenten
- **FieldGuide** komplett neu (6 i18n-Tabs, kontextsensitive Hilfe-Buttons)
- **PriceRadar** rebuilt: 4 Kategorien, `priceradarParams` Deep-Link Store, Buchungsstatus auf allen Tracker-Tabellen
- **Discovery Pipeline**: SQLite-Pool (200 Einträge), `asyncio.gather` Parallel-Bildladen, Immich/Unsplash Proxy
- **Multi-Provider Flugsuche**: Ryanair, Google Flights, Kiwi (Tequila v2), Duffel; `provider_configs` DB-Tabelle
- **Dawarich GPS Trip-Erkennung** + **ActualBudget Sync** (via `actualpy`)
- **ScratchMap**: lokale `jsvectormap` npm-Dependency + Nominatim Geocoding

### Changed
- README auf Englisch neu geschrieben

---

## [0.7.0] — 2026-03/04 (Auth + Multi-User)

### Added
- **JWT + WebAuthn/Passkey** Authentifizierung
- **Multi-User** Datenisolation (`user_id` auf allen Content-Tabellen)
- **Per-User verschlüsselte Credentials** (Telegram, Gotify via Fernet)
- **MyTrips** komplett redesigned: 4 Tabs, Jahres-Switcher, Donut-Budget-Chart, TripCard
- `main`/`beta` Branch-Strategie eingeführt
- Docker Multi-Stage Build (kein host-seitiges Node.js)
- Nginx Mozilla Observatory Security Headers
- `api.js` mit `resolveBase()` für Same-Origin Self-Hosted Proxy

---

## [0.5.0] — 2026-03 (Ursprüngliche App)

### Added
- Vanilla JS + FastAPI Grundgerüst
- Ryanair, Google Flights (SerpAPI), Booking.com, Homair Scraper
- Preis-Tracking mit APScheduler
- Gotify Benachrichtigungen
- CSV Export
- ActualBudget + Dawarich Integration (erste Version)
