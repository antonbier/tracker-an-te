# Changelog — WanderSuite

Alle nennenswerten Änderungen am Projekt. Format basiert auf [Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.0-beta.1] — 2026-04-17

### Added — Block 5 Teil 1: UX-Polish, Routing & Bugfixes

- **i18n Browser-Language Fallback** (`stores.js`, `i18n.js`): App liest beim ersten Start `navigator.language` aus und nutzt Browser-Sprache sofern unterstützt (de/en/it/es), sonst `en` als sicherer Fallback. User-Wahl wird in `ws-lang` und `lang` im localStorage persistiert.
- **Dashboard-Routing Bucket List** (`TravelInspo.svelte`): Klick auf Bucket-List-Kachel setzt `activeMyTripsTab.set('bucketlist')` vor der Navigation zu MyTrips.
- **Dashboard-Routing Listen-Buttons** (`CompactTripsList.svelte`): Generischer „Alle im Reisetagebuch"-Button ersetzt durch „Alle geplanten Reisen →" (setzt Tab auf `planned`) unter der Geplant-Liste und „Zum Archiv →" (setzt Tab auf `archive`) unter der Abgeschlossen-Liste.

### Added — Block 5 Teil 2: TripHub Hero-Bilder & Unsplash-Caching

- **DB-Migration** (`database.py`): Drei neue Spalten idempotent zu `ws_trips` hinzugefügt: `image_url TEXT DEFAULT NULL`, `image_author TEXT DEFAULT NULL`, `image_author_url TEXT DEFAULT NULL` — persistiert das gecachte Unsplash-Bild inkl. Fotografen-Credits direkt am Trip-Datensatz.
- **Backend-Endpoint** (`routes/ws_trips.py`): `PATCH /api/ws-trips/{id}/image` — speichert `image_url`, `image_author` und `image_author_url` am Trip. Idempotenter Partial-Update, ignoriert `null`-Werte nicht (überschreibt bewusst für Reset-Möglichkeit).
- **TripHub Hero-Bild** (`TripHub.svelte`): In allen 3 Phasen (Planning / Active / Archived) wird jetzt ein Unsplash-Bild im Hero angezeigt:
  1. Ist `trip.image_url` gesetzt → gecachtes Bild sofort anzeigen (kein API-Call).
  2. Kein Bild gecacht → `GET /api/discovery/trip-image?destination=...&source=unsplash` aufrufen.
  3. Erhaltenes Bild sofort anzeigen UND per `PATCH /api/ws-trips/{id}/image` am Backend cachen (fire-and-forget).
- **Unsplash Attribution** (`TripHub.svelte`): Dezentes, halbdurchsichtiges Overlay unten rechts im Hero: „Foto von [Autor] auf Unsplash". Links enthalten `?utm_source=wandersuite&utm_medium=referral` gemäß Unsplash API-Richtlinien.
- **Bild-Skalierung**: Hero-`<img>` hat `absolute inset-0 w-full h-full object-cover` mit `.35` Opacity + `rgba(0,0,0,.45)` Overlay für Lesbarkeit des Textes.

### Fixed — Block 5 Teil 1

- **Immich Zeitraum-Bilder** (`backend/discovery.py`, `routes/discovery.py`, `HeroPastTrip.svelte`): `GET /api/discovery/trip-image` akzeptiert jetzt `date_from` und `date_to` Query-Parameter; Backend leitet diese als `takenAfter`/`takenBefore` an die Immich Metadata-Search-API weiter. `HeroPastTrip` übergibt `start_date`/`end_date` des Trips.
- **HeroSection Grid** (`HeroSection.svelte`): `sm:grid-cols-2` → `md:grid-cols-2` für korrektes 2-Kachel-Layout bei Tablet-Breakpoint.
- **ScratchMap 401-Fehler** (`ScratchMap.svelte`): Geocoding-Funktion nutzt jetzt `api()`-Helper statt rohem `fetch()` → JWT-Token wird korrekt mitgesendet.

### Added — Block 1: Unsplash Attribution & PWA

- **Unsplash Attribution**: `discovery.py` extrahiert `author_name` + `author_url` aus Unsplash-Response; `HeroNextTrip`, `TravelInspo`-Thumbnails und `DestinationDetail`-Galerie zeigen dezentes Foto-Attribution-Overlay (UTM-Links mit `?utm_source=wandersuite&utm_medium=referral`)
- **Image Scaling Fix**: `TravelInspo` Thumbnail-Wrapper mit `self-stretch`; alle Hero-Images haben `absolute inset-0 w-full h-full object-cover`
- **PWA FOUC-Fix** (`app.html`): Inline-IIFE im `<head>` liest `localStorage('ws-theme')` und setzt `dark`-Klasse sofort vor dem Render — eliminiert weißes Aufblitzen
- **Dual `theme-color`**: `<meta name="theme-color">` mit `media`-Query für Dark/Light (#0f172a / #f5ebe0)
- **API Rate-Limit (429)**: `_openai_call()` und Unsplash werfen sauber `RuntimeError("api_rate_limit:*")` → HTTP 429 mit lesbarer Fehlermeldung ans Frontend

### Added — Block 2: Archiv-Refactoring & Trip-Quellen

- **Unified Archive Timeline**: Archiv zeigt alle Trips chronologisch in einem Grid — keine Gruppierung nach Typ mehr
- **Source-Badge** auf `TripCard`: `📡` Dawarich · `✍️` Manuell · `🪄` WanderWizzard
- **Geocoding im Add-Modal**: `onblur` auf Ortsfeld → `GET /api/settings/geocode` → `lat/lon` werden mit gespeichert (Karte + Wetter-Widget)
- **Einheitlicher CTA**: Alle Archiv-Karten haben „Trip Hub →"-Button; `⋮`-Menü entfernt
- **On-the-fly TripHub-Container**: Klick auf Dawarich/Manuelle Karte erstellt bei Bedarf automatisch einen `ws_trips`-Container (`source_detected_id`-Verknüpfung)
- **Dawarich Force-Full Checkbox** im Archiv-Admin-Bar: „Gelöschte Reisen erneut laden" setzt `ignored=0` vor dem Sync
- **3-Wege-Löschlogik** (`DELETE /api/ws-trips/{id}`): Typ A (Dawarich) → Soft-Delete `ignored=1`; Typ B (Manuell) → Hard-Delete; Typ C (WanderWizzard) → vollständiger Hard-Delete

### Fixed — Block 2

- **Duplikat-Trips im Archiv**: `list_detected_trips()` dedupliziert Python-seitig nach `(start_date, end_date, location_name, user_id)` — behebt 4x-Anzeige durch Dawarich-Mehrfachimporte
- **Leere Titel (`—`)**: `location_name`-Fallback auf `country` im Backend + in `TripCard` `location_name` an erster Stelle der Fallback-Kette
- **`SyntaxError` in `discovery.py`**: Ungültige Backslash-Escapes in f-Strings entfernt (`\'?\'` → `chr(63)`); `_make_proxy_url` ohne f-String-Backslash
- **SQLite Binding-Fehler (`database.py`)**: `list_detected_trips`-Subquery-Ansatz durch Python-seitiges Dedup ersetzt → `ProgrammingError: Incorrect number of bindings` behoben

### Added — Block 3: Finanz-Upgrade

- **`POST /api/ws-trips/{id}/sync-budget`**: Holt ActualBudget-Transaktionen im Reisezeitraum (`start_date`–`end_date`), filtert nach Travel-Kategorien aus Settings, speichert `synced_expenses` + `synced_transactions_json` + `synced_at` in `ws_trips`
- **Budget-Breakdown erweitert**: `GET /api/ws-trips/{id}/budget` liefert jetzt `synced_expenses`, `synced_transactions`, `synced_at`, `remaining`, `total_spent`
- **`BudgetWidget.svelte` Redesign** — 4 klare Finanz-Säulen:
  1. Gesamtbudget (editierbar via ✏️)
  2. Gebuchte Kosten (Tracker: Flug + Hotel, aufklappbar)
  3. Manuelle Ausgaben (inline editierbar)
  4. ActualBudget Synced (ausklappbar Akkordeon mit Transaktionsliste, 🔄 Sync-Button, ↗ Link)
- **Progress Bar** mit Color-Coding: Grün (≤85%), Orange (85–100%), Rot (>100% / überschritten)
- **DB-Migrationen**: `synced_expenses REAL`, `synced_transactions_json TEXT`, `synced_at TEXT` zu `ws_trips`


### Added — Block 4: Dashboard & MyTrips Cleanup

- **Bucket List Widget** (Dashboard `TravelInspo`): ersetzt die grüne Nostalgie-Kachel; zeigt Top-3-Wunschziele + offene Ziel-Anzahl, navigiert zu Meine Reisen → Bucket List
- **Unified Trip-Listen** (`CompactTripsList`): „Geplante Reisen" und „Abgeschlossene Reisen" im Dashboard zeigen jetzt alle 3 Typen — `📡` Dawarich, `✍️` Manuell, `🪄` WanderWizzard — mit Source-Badge und `capitalize`-Titel
- **`wsTrips` im Dashboard** (`Dashboard.svelte`): `/api/ws-trips` wird beim Mount geladen; `upcoming` + `completed` basieren auf `wsTrips` statt Legacy-`$trips`-Store

### Fixed — Block 4

- **Statistik-Kacheln** (`MyTrips` Übersicht): „Reisen gesamt" zählt jetzt `wsTrips.length`; „Reisen [Jahr]" filtert `wsTrips` nach `selectedYear`; „Wunschziele" zeigt `$bucketlist.filter(!done).length` (war: `upcomingTrips.length`)
- **ScratchMap Initialisierung**: `$effect`-Abhängigkeit auf `JSON.stringify(journalTrips.map(id))` statt nur `.length` → sofortige Initialisierung beim ersten Tab-Öffnen ohne Jahreswechsel-Workaround
- **Budget Jahressumme** (`MyTrips`, `Dashboard`): `totalSpentYear` und `yearSpent` berechnen sich aus `wsTrips` (booked + manual + synced) statt altem `detected_trips`/`$trips`-Ansatz
- **Archive ActualBudget-Sync** (`syncActual()`): liest Credentials aus DB-Settings via `/api/ws-trips/{id}/sync-budget` statt `localStorage` — behebt „URL + Passwort fehlen"-Fehler bei gespeicherten Settings


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
