# Changelog — WanderSuite

Alle nennenswerten Änderungen am Projekt. Format basiert auf [Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.0-beta.1] — 2026-04-20

### Fixed — API-Bug-Session (API-BUG 1–7)

- **API-BUG 1 — Todo-Toggle 405** (`routes/ws_trips.py`): Kein echter Bug — der korrekte Endpoint ist `PATCH /api/ws-trips/{trip_id}/todos/{todo_id}/toggle`. `PATCH /todos/{id}` (ohne `/toggle`) existiert nicht und liefert korrekt 405. Docstring und Modul-Header aktualisiert um dies klarzustellen. Der Svelte-Code ruft bereits den richtigen Endpoint auf.
- **API-BUG 2 — Trip ohne Datum** (`routes/ws_trips.py`): `start_date`/`end_date` bleiben `Optional` (für Flex-Trips korrekt). Zusätzliche Validator-Dokumentation im Modul-Header erklärt das Design.
- **API-BUG 3 — Scrape 500 → 422/503** (`routes/trackers.py`): `_do_scrape()` fing bisher alle Exceptions als HTTP 500 mit rohem Stack. Neu: Fehler-Klassifizierung — fehlender API-Key → 422 `missing_api_key`; Anbieter-Fehler (409/429/503/„Availability declined") → 503 `provider_unavailable`; allgemein → 422 `scrape_failed`. Kein Stack-Trace mehr im HTTP-Response.
- **API-BUG 4 — PATCH /trackers/{id} fehlte** (`routes/trackers.py`): Neues `TrackerUpdate`-Pydantic-Modell mit `return_date`, `adults`, `children`, `seat_cost`, `wish_price`, `trip_id`. Neuer Endpoint `PATCH /api/trackers/{id}` schreibt nur angegebene Felder; `wish_price` wird via `set_tracker_threshold()` gesetzt. Validatoren: `adults >= 1`, `children >= 0`, Preis-Felder `>= 0`.
- **API-BUG 5 — Negatives Budget** (`routes/ws_trips.py`): `@field_validator("budget")` mit `v < 0 → 422` auf `WsTripCreate` und `WsTripUpdate`.
- **API-BUG 6 — XSS-Payload** (`routes/ws_trips.py`): Neue `_sanitize()`-Funktion (ohne externe Deps, nutzt `re` + `html` stdlib) entfernt `<script>`, `<iframe>` und alle HTML-Tags aus String-Eingaben. Angewendet auf `title`, `destination`, `notes`, `wish_text` in `WsTripCreate` und `WsTripUpdate`.
- **API-BUG 7 — Kein Längen-Limit** (`routes/ws_trips.py`): `title` max 200 Zeichen via `@field_validator`; `destination`, `notes`, `wish_text` max 500 Zeichen via `_sanitize(max_len=500)`. Zusätzlich: `adults >= 1`, `children >= 0` Constraints ergänzt.

### Fixed — Bug-Report Session (BUG 1, 2, 6, 7, 8 / UX 1–5)

- **BUG 1 — Phasenfehler archived Trip** (`HeroSection.svelte`, `HeroNextTrip.svelte`): Trips mit `end_date` in der Vergangenheit wurden im Dashboard als aktiv/geplant angezeigt obwohl ihr `status` noch `planning` war. Fix: `planning`-Filter in `HeroSection` prüft jetzt zusätzlich `endRaw >= today`. `HeroNextTrip` leitet `phase` direkt aus Datumswerten ab (analog TripCard/TripHub).
- **BUG 2 — Overnight-Flugdauer** (`backend/routes/search.py`, `SearchResults.svelte`): BGY→DUB 17:15→20:55+1 zeigte 17h40m statt 3h40m. Backend: neue Hilfsfunktion `_calc_duration_min(dep, arr)` berechnet Dauer mit Mitternachts-Wrap (`+1440 min` wenn arr < dep). Frontend: Fallback-Berechnung direkt aus `departure_time`/`arrival_time` wenn `duration_min` fehlt; Minuten-Anzeige jetzt mit `padStart(2,'0')`.
- **BUG 6 — Falscher i18n-Key Mietwagen-Tab** (`TrackerGrid.svelte`): Empty-State zeigte „Keine Camping-Tracker" für rentals-Kategorie. Fix: `rentals`-Branch in der Label-Ersetzungskette ergänzt → `$t('radarRentals')`.
- **BUG 7 — ISO-Datumsformat im WanderWizzard** (`WanderWizzard.svelte`): Zusammenfassung zeigte `2026-06-15 → 2026-06-22` statt `15.06.2026 → 22.06.2026`. Fix: `fmtDate()` aus `$lib/i18n.js` importiert und in `dateSummary`-Derived verwendet.
- **BUG 8 — ScratchMap Render-Fehler** (`ScratchMap.svelte`): „Attempt to use map which was not loaded: world" beim ersten Load. Fix: neue `ensureLib()`-Funktion lädt `jsvectormap` + `world.js` einmalig und wartet 150ms bis die Map-Registry bereit ist; `initMap()` ruft `ensureLib()` idempotent auf bevor `new jsVMClass()` aufgerufen wird.

### Changed (UX) — Bug-Report Session

- **UX 1 — autocapitalize** (`WanderWizzard.svelte`, `TripHub.svelte`): `autocapitalize="words"` auf Destination-Input im WanderWizzard und Titel-Input im Edit-Modal — verhindert Kleinschreibung bei mobiler Eingabe.
- **UX 2 — archived Trip CTA** (`HeroNextTrip.svelte`): Hero-Karte für archivierte Trips zeigt jetzt neutralen Button „📖 Trip ansehen" (halbtransparent weiß) statt orangefarbenem „🗺️ Zur Reiseplanung"-CTA.
- **UX 3 — Tracker-Label Truncate** (`CompactTrackerGrid.svelte`): `overflow-hidden` + `title`-Tooltip auf dem Label-Container — lange Hotel-/Camping-Namen brechen nicht mehr unsauber um.
- **UX 4 — Gepäck-Spalten-Header** (`FlightSearchForm.svelte`): Spalten-Header-Zeile (`Typ | Anzahl | Aufpreis / Stück | Total`) über dem Gepäck-Stepper ergänzt; `hidden sm:flex` für Mobile-Kompatibilität.
- **UX 5 — Budget-Betrag Tooltip** (`CompactTripsList.svelte`): `title="Gebuchte Kosten + Ausgaben"` auf Budget-Betrag — klärt dass Orange die Standard-Akzentfarbe ist (kein Warnsignal).

---

## [1.0.0-beta.1] — 2026-04-20

### Added — Block 8: Settings-Polish, Date-Logic & Tracker-Fix

- **Test-Buttons für Alerts** (`NotificationsTab.svelte`): Telegram- und Gotify-Sektionen haben jetzt je einen „🚀 Testnachricht"-Button. Der Button ist deaktiviert solange die nötigen Credentials (Token + Chat-ID bzw. URL + App-Token) nicht ausgefüllt sind. Nutzt die bereits vorhandenen Endpoints `POST /api/notifications/test-telegram` und `POST /api/notifications/test-gotify`.
- **Home Airport Autocomplete** (`MyspaceDefaults.svelte`): Das IATA-Eingabefeld unter Reisedefaults → Logistik hat jetzt Autocomplete aus `airports.json` (476 Einträge). Ab 2 Zeichen erscheint ein Dropdown mit passendem IATA-Code, Airportname und Stadt. Auswahl setzt `homeAirport` direkt.
- **Scheduler i18n** (`SchedulerTab.svelte`): Intervall-Buttons zeigen jetzt übersetzte Labels via i18n-Keys (`schedEvery6h` … `schedEveryWeek`) statt hartcodierter `h/d`-Kürzel. Sektionsüberschriften, Checkboxen, Buttons alle via `$t()`. Alle 4 Locale-Dateien aktualisiert.
- **i18n-Keys** (alle 4 Locales): Neu: `dashAllPlanned`, `dashToArchive`, `settingsTestSend`, `settingsTestSending`, `schedEvery6h/12h/24h/48h/72h/Week`.
- **Tracker current_price** (`routes/trackers.py`, `routes/google_flights.py`, `routes/accommodations.py`): Alle 4 Tracker-List-Endpoints (`/api/trackers`, `/api/google-flights`, `/api/accommodations/homair`, `/api/accommodations/booking`) liefern jetzt `current_price` direkt auf Root-Ebene des Tracker-Objekts — als einfach zugängliche Zahl ohne Umweg über `latest_snapshot.total_price`.

### Fixed — Block 8

- **Dashboard Hero Datum-Bug** (`HeroPastTrip.svelte`): Archivierte Reisen zeigten „Gerade zurückgekehrt / Heute" obwohl sie Monate zurücklagen. Ursache: `daysAgo` wurde vom `start_date` berechnet. Fix: `end_date` wird bevorzugt, `start_date` als Fallback. Außerdem exakte Mitternachts-Datumsberechnung via `T00:00:00`-Suffix.
- **Dashboard i18n-Variablen** (`CompactTripsList.svelte`): Buttons „Alle geplanten Reisen →" und „Zum Archiv →" nutzten `|| 'Fallback'`-Syntax. Nun direkte `$t()`-Keys — Keys in allen 4 Locales eingetragen.
- **Tracker-Preis Erstanzeige** (`TrackerCard.svelte`): `price`-Derived nutzt jetzt `tr.current_price ?? s?.total_price` — der Root-Level-Wert ist beim initialen Laden sofort verfügbar ohne Klick auf ⟳.
- **Wetter-Widget bei archivierten Trips** (`TripHub.svelte`): `WeatherWidget` wird bei `phase === 'archived'` nicht mehr gerendert — aktuelles Wetter für vergangene Reisen ist nutzlos.
- **MyTrips Reisenzähler** (`database.py`): `list_ws_trips()` hatte `LIMIT 100` als Default — bei >100 Trips zählte der „Gesamtreisen"-Counter zu wenig. Erhöht auf 2000.

---

## [1.0.0-beta.1] — 2026-04-17

### Added — Block 7: Tracker-Reaktivität, Smartes Trip-Editing & Soft-Migration

- **Smartes Trip-Edit-Modal** (`TripHub.svelte`): Stift-Icon ✏️ im Hero öffnet ein Modal mit zwei getrennten Feldern:
  - *Titel* (kosmetisch, optional): Freitext wie „Roadtrip 2025" — steuert keine Wetter- oder Kartendaten
  - *Ort / Hauptziel* (geocodiert, Pflichtfeld): Suchfeld mit Nominatim-Autocomplete via `GET /api/settings/geocode`; gewählter Eintrag setzt `destination`, `lat`, `lon`; grünes ✓ + Koordinaten-Anzeige bestätigen die Auswahl
  - Speichert `title`, `destination`, `lat`, `lon` via `PATCH /api/ws-trips/{id}`; lokaler Soft-Update ohne Reload
- **WsTripUpdate + lat/lon** (`routes/ws_trips.py`): Pydantic-Modell um `lat: Optional[float]` und `lon: Optional[float]` erweitert; Doc-String erklärt title-vs-destination-Semantik
- **DB Soft-Migration** (`database.py`): Zwei neue Spalten idempotent per `ALTER TABLE ADD COLUMN`: `lat REAL DEFAULT NULL`, `lon REAL DEFAULT NULL` auf `ws_trips` — Altdaten (Dawarich-Sync) bleiben unberührt, `DEFAULT NULL` bricht keine bestehenden Zeilen

### Fixed — Block 7

- **Tracker-Reaktivitäts-Bug** (`PriceRadar.svelte`): Nach manuellem Scrape eines Trackers (⟳-Button) aktualisierte sich Preis-Anzeige und SVG-Chart nicht.
  - Fix: `loadAllTrackers()` erzeugt bereits eine neue Array-Referenz → Svelte 5 rendert alle TrackerCards neu (tr-Prop = neues Objekt). Zusätzlich: `chartState` wird nach dem History-Reload per `chartState = { ...chartState }` als neues Objekt zugewiesen, was auch verschachtelte `$derived`-Abhängigkeiten auf `chartData` invalidiert
  - History wird jetzt **immer** nach Scrape neu geladen (nicht nur wenn Akkordeon offen), sodass die frischen Daten beim nächsten Öffnen sofort verfügbar sind
- **Soft-Migration Fallback-Kette** (`TripCard.svelte`, `TripHub.svelte`): Altdaten ohne `title`-Feld zeigen weiterhin korrekt `destination`/`location_name` an.
  - Neue strikte Priorität: `title → destination → location_name → name → country`
  - TripHub Hero: `destination` nur als Unterzeile angezeigt wenn `title` gesetzt UND verschieden von `destination` — kein Doppeln des Ortsnamens

---

### Added — Block 6: Bugfixes & Discovery-Erweiterungen

- **PersonalityModal** (`PersonalityModal.svelte`, `TravelInspo.svelte`): Neuer „🧭 Personalisieren"-Button bei den KI-Vorschlägen öffnet ein Modal mit allen Reisepersönlichkeits-Einstellungen (Stil, Klima, Landschaft, Begleitung, Modus, Max. Zeit, Freitext). Checkbox „Dauerhaft speichern": ohne Checkbox → Settings nur für diesen Refresh (temporär, kein DB-Write); mit Checkbox → `PUT /api/settings/user` + Refresh. Modal schließt sich automatisch nach erfolgreicher Generierung.
- **Discovery /refresh Payload** (`routes/discovery.py`, `discovery.py`): `POST /api/discovery/refresh` akzeptiert jetzt optionalen JSON-Body (`TemporaryPersonality`) der die Persönlichkeit ohne DB-Speicherung temporär überschreibt. `background_refresh_suggestions()` erhält `temp_personality`-Parameter.
- **Massive Daten-Erweiterung**: `airports.json` (476 Flughäfen weltweit), `destinations.json` (1114 Reiseziele), `ai_destinations.json` (614 KI-Seed-Destinationen) — alle als externe JSON-Dateien unter `svelte/src/lib/data/` und `backend/data/`.
- **constants.js Refactoring**: `AIRPORTS` und `DESTINATIONS` werden jetzt aus den JSON-Dateien importiert statt hardcoded — vollständig ersetzt durch 476 bzw. 1114 Einträge.
- **KI-Seeds Erweiterung** (`discovery.py`): `_AI_DESTINATIONS`-Liste (614 Einträge) wird beim Start aus `ai_destinations.json` geladen. `_build_prompt()` sampelt zufällig 20 Seeds als Inspiration für den LLM-Prompt → deutlich diversere Vorschläge.

### Fixed — Block 6

- **Hero Grid 2-Kachel** (`Dashboard.svelte`, `HeroSection.svelte`): `nextTrip`/`lastTrip` nutzen jetzt phase-basierte Logik (aktiver Trip = `start <= today <= end`, archivierter = `end < today`). `hasLastTrip` ist unabhängig von `hasNextTrip`. Grid-Breakpoint `md:` → `lg:` für korrekte Side-by-Side-Darstellung.
- **Tracker-Preis Reset** (`database.py`): `get_latest_snapshot()` bevorzugt jetzt `status='ok'`-Einträge — kein Preis-Reset mehr wenn ein Fehler-Snapshot folgt.
- **Chart-History nach Scrape** (`PriceRadar.svelte`): Nach manuellem Scrape eines Trackers wird `chartState[key].history` sofort neu von `GET /api/prices/history/...` geladen wenn das Akkordeon offen ist.

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
