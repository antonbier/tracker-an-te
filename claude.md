# WanderSuite — Architekturdokumentation für KI-Assistenten

> Letzte Aktualisierung: Block 6 Refactoring (Punkt 1–4, 6) — `$lib/utils.js`, DB-Generics, MyTrips + TripHub Decomposition, localStorage-Credentials eliminiert

## Projekt-Übersicht

WanderSuite ist eine **selbst-gehostete KI-gestützte Travel-Hub-Anwendung**.

- **Frontend**: Svelte 5 + SvelteKit, Tailwind CSS v4
- **Backend**: FastAPI (Python 3.12)
- **Datenbank**: SQLite
- **Deployment**: Docker Compose (Unraid), Zoraxy Reverse Proxy
- **Repository**: `antonbier/tracker-an-te`
- **Branches**: `main` (stabil), `beta` (aktiv, Ports 8767/8768)

---

## Branch-Strategie

| Branch | Port Backend | Port Frontend | Zweck |
|--------|-------------|---------------|-------|
| `main`  | 8765 | 8766 | Stabile Production-Release |
| `beta`  | 8768 | 8767 | Aktive Entwicklung |

---

## title vs. destination — Semantik (Block 7)

In `ws_trips` gibt es zwei konzeptionell verschiedene Felder:

| Feld | Bedeutung | Steuert |
|------|-----------|---------|
| `title` | Kosmetischer Anzeigename (optional, z.B. „Roadtrip 2025") | Nur UI-Anzeige |
| `destination` | Geocodierter Ortname (z.B. „Barcelona, Spanien") | Wetter-Widget, Maps, Bildsuche |
| `lat` / `lon` | Koordinaten aus Geocoder | Wetter-API, zukünftige Map-Features |

**Fallback-Kette** (in TripCard, TripHub Hero, Dashboard):
`title → destination → location_name → name → country`

**Regel**: `title` darf `NULL` sein. `destination` ist das Pflichtfeld für alle Geo-Features.
Alte Dawarich-Sync-Trips haben kein `title` — sie fallen sauber auf `destination` zurück.

---

## 3-Phasen-Logik (Kernkonzept)

Jede WS-Trip durchläuft drei Phasen — berechnet aus Datum, nicht aus DB-Status:

```
phase = "archived"   if today > end_date
phase = "active"     if today >= start_date AND today <= end_date
phase = "planning"   otherwise
```

Alle UI-Komponenten (TripCard, TripHub, Hero) reagieren auf die Phase:
- **Planning**: WanderWizzard-Flow, PriceRadar-Links, Checkliste generieren
- **Active**: ON TOUR Badge (grün, pulsierend), Wetter-Widget prominent, Buchungen
- **Archived**: Grau/desaturiert, Foto-Galerie (Coming Soon), Nostalgie-Kachel im Dashboard

---

## Navigation (finale Benennung)

| ID | Icon | Label DE | Label EN | i18n Key |
|----|------|----------|----------|----------|
| `home` | 🏠 | Übersicht | Overview | `navHome` |
| `priceradar` | 🎯 | Preis-Radar | Price Radar | `navRadar` |
| `planer` | 🪄 | WanderWizzard | WanderWizzard | `navWizzard` |
| `mytrips` | 🎒 | Meine Reisen | My Trips | `navTrips` |

> **Wichtig**: Der Menüpunkt heißt **WanderWizzard** (nicht mehr "Trip Planner" / "Reiseplaner").
> Die Svelte-Route bleibt `planer` (historisch). i18n-Key: `navWizzard` / `navWizzardShort`.

---

## Onboarding / Setup-Wizard (Phase 2A-2B + 3)

Getriggert via 🪄-Icon im Header (`wizardOpen` Svelte-Store, Komponente: `SetupWizard.svelte`).

| Step | Titel | Inhalt | Save-Endpoint |
|------|-------|--------|---------------|
| **0** | Vision | Willkommen, 3-Phasen-Erklärung, Feature-Highlights | — (kein Save) |
| **1** | Basis & Heimat | Backend-URL, TZ, Datum, Währung, Heimatort | `/api/settings/wizard/step` (global) |
| **2** | Self-Hosted Bridges | Dawarich, Immich, ActualBudget | `/api/settings/wizard/step` (user) |
| **3** | Reise-Defaults | 2 Akkordeons: Logistik + Persönlichkeit | `/api/settings/wizard/step` (user: ww_*) |
| **4** | KI & Engines | OpenAI, Gemini, SerpAPI + Links | `/api/settings/wizard/step` (global: *_key) |
| **5** | Erfolg | Konfetti-Animation + Summary-Chips | — |

**Step 0** ist der neue Einstieg: Inspirierender Willkommenstext, 3-Phasen-Karten, Feature-Grid.
Nach Step 0 läuft der Wizard normal durch Steps 1–5 mit Save-on-Next.

### Hilfe-Buttons (kontextuell)
Jeder Step ab 1 zeigt einen `📖 Hilfe`-Button in der Wizard-Headerleiste.
Klick öffnet `FieldGuide.svelte` als überlagerndes Modal mit dem zum Step passenden Tab:

```
Step 1 → tab: 'wizard'
Step 2 → tab: 'bridges'
Step 3 → tab: 'trips'
Step 4 → tab: 'apis'
Step 5 → tab: 'vision'
```

---

## Heimatort — Globale Verknüpfung

Der **Heimatort** (`home_lat`, `home_lon`, `home_name`) ist aus den Dawarich-Settings herausgelöst:

- **`GLOBAL_KEYS`** in `settings_manager.py` enthält `home_lat`, `home_lon`, `home_name`
- **`USER_KEYS`** auch (per-user Override möglich)
- **Lookup-Priorität**: Per-User > Global > `None` (via `resolve_home_location(user_id)`)
- **Frontend**: `BasicTab.svelte` enthält vollständige Geocode-Suche + manuelle Koordinaten
- **IntegrationsTab**: `homeLat`/`homeLon` Felder **entfernt** — keine Doppelhaltung
- **Gespeichert in**: localStorage (`s-homeLat`, `s-homeLon`, `s-homeName`) + DB

---

## FieldGuide (In-App Hilfe)

`FieldGuide.svelte` — 6 Tabs, vollständig i18n, deep-link via `initialTab` Prop:

| Tab ID | Inhalt |
|--------|--------|
| `vision` | WanderSuite Überblick, 3 Phasen, Quickstart |
| `wizard` | Setup-Wizard 5 Schritte erklärt |
| `radar` | PriceRadar: 4 Quellen, IATA-Codes |
| `trips` | WanderWizzard, Trip Hub Widgets, Dashboard |
| `bridges` | Dawarich, Immich, ActualBudget Setup-Anleitungen |
| `apis` | SerpAPI, Gemini, OpenAI Keys + Links |

**Deep-Link Verwendung** (z.B. aus Wizard):
```svelte
<FieldGuide bind:open={guideOpen} initialTab="bridges" />
```

---

## Partial Update Safety

Alle Settings-Endpunkte nutzen **Partial Updates**:
- Nur explizit übergebene Felder werden geschrieben
- `None`/leere Werte überschreiben nie bestehende DB-Einträge
- `POST /api/settings/wizard/step` teilt automatisch in global vs. user fields

---

## Settings-Architektur

### Globale Keys (`GLOBAL_KEYS` in `settings_manager.py`)
```
serpapi_key, gemini_key, openai_key, llm_provider
telegram_bot_token, telegram_chat_id, gotify_url, gotify_token
language, timezone, date_format, currency
home_lat, home_lon, home_name
```

### Per-User Keys (`USER_KEYS`)
```
dawarich_url, dawarich_token, actual_url, actual_token, actual_file, travel_categories
home_lat, home_lon, home_name, timezone, date_format, currency
immich_url, immich_api_key, immich_geo_sync
ww_adults, ww_children, ww_home_airport
ww_lug_s10/s20/s23, ww_lug_l10/l20/l23
ww_dep_min/max, ww_arr_min/max
travel_style, climate_pref, landscape_pref, companions, wish_text, unsplash_key
travel_mode, max_travel_time, history_mode
```

---

## Store-Architektur (Svelte)

```
stores.js
├── apiUrl            — persisted, Backend-URL
├── lang              — persisted, aktive Sprache (de/en)
├── theme             — persisted, dark/light
├── jwtToken          — persisted, JWT
├── currentUser       — User-Objekt
├── appStatus         — auth_enabled, version etc.
├── currentPage       — aktive Seite ('home'|'priceradar'|'planer'|'mytrips'|'triphub'|...)
├── previousPage      — für TripHub Back-Navigation
├── activeMyTripsTab  — wiederhergestellt nach TripHub-Rückkehr
├── settingsOpen      — globaler Trigger für ⚙️ Modal
├── wizardOpen        — globaler Trigger für 🪄 Wizard
├── priceradarParams  — WanderWizzard → PriceRadar Übergabe
└── activeWsTripId    — aktiver WS-Trip für TripHub
```

---

## Akkordeon-Muster (Reise-Defaults)

`MyspaceDefaults.svelte` und Wizard Step 3 verwenden identisches 2-Akkordeon-Layout:

```
Akkordeon 1 — 🧳 Logistik-Defaults  [Standard: offen]
  ├── Reisende (Erwachsene ±, Kinder ±, Heimatflughafen)
  ├── Gepäck-Matrix (Kurz- und Langtrip, 10/20/23 kg Stepper)
  └── Bevorzugte Flugzeiten (Abflug ab/bis, Ankunft ab/bis)

Akkordeon 2 — 🧭 Reisepersönlichkeit  [Standard: geschlossen]
  ├── Reisestil (Adventure/Entspannung/Kultur/Natur/City)
  ├── Klimapräferenz (Warm/Mild/Kalt/Egal)
  ├── Landschaft (Berge/Meer/Wald/Stadt/Mix)
  ├── Reisebegleitung (Solo/Pärchen/Familie/Freunde)
  ├── Reisemodus (Flug/Auto) + Max. Reisezeit
  ├── History-Modus (Blacklist/KI-Kontext)
  └── Freitext-Wunsch (max 500 Zeichen)
```

---

## i18n

- Lokalisierungsdateien: `svelte/src/locales/de.json`, `en.json`
- i18n-Helper: `svelte/src/lib/i18n.js`
- Zugriff im Template: `{$t('key')}`
- **Alle neuen UI-Strings müssen in beiden Dateien angelegt werden — keine Ausnahmen**
- Pipe-getrennte Listen für FieldGuide-Features: `"key|key|key"` → gesplittet im Template

---

## Docker Logging (alle Services)

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## GitHub API Commit-Pattern (kritisch)

```bash
# IMMER: Skript nach /tmp/ schreiben, dann ausführen
python3 /tmp/patch.py

# NIEMALS heredocs verwenden (base64-Korruption)
# Verification-Output NUR nach sys.stderr
print("OK", file=sys.stderr)

# SHA immer frisch holen vor Commit
# Bei mehreren Commits: SHA aus vorherigem Response für nächsten verwenden
```


---

## Architektur-Entscheidungen & Refactoring-Log

### Shared Utilities (`$lib/utils.js`) — eingeführt Block 6 Refactoring

Alle zustandslosen Hilfsfunktionen die app-weit gebraucht werden leben in `svelte/src/lib/utils.js`.
**Niemals** inline in Komponenten neu definieren — immer aus utils importieren.

| Export | Typ | Zweck |
|--------|-----|-------|
| `today` | `const string` | Heutiges Datum YYYY-MM-DD (einmal berechnet) |
| `getTodayStr()` | Funktion | Frisches Datum für Laufzeit-kritische Aufrufe |
| `getTripPhase(trip)` | Funktion | Kanonische 3-Phasen-Logik → `'planning'\|'active'\|'archived'` |
| `daysBetween(target, from?)` | Funktion | Tage zwischen Daten, positiv = Zukunft |
| `fmtCurrency(amount)` | Funktion | Euro-Formatierung z.B. `"1.234,56 €"` |
| `fmtDate` | Re-Export | Aus `priceradar/helpers.js` — benutze immer diesen Pfad |
| `fmtRange` | Re-Export | Datums-Range formatiert |
| `destinationGradient` | Re-Export | Aus `triphub/helpers.js` — benutze immer diesen Pfad |
| `wmoIcon` | Re-Export | WMO Wetter-Code → Emoji |

**Regel**: Komponenten außerhalb von `/triphub/` dürfen nicht direkt aus `$lib/components/triphub/helpers.js` importieren — stattdessen `$lib/utils.js`.

---

### Backend CRUD-Generics (`database.py`) — eingeführt Block 6 Refactoring

Für alle 4 Tracker-Typen (ryanair/flight, google_flight, homair/camping, booking/hotel) gibt es generische Unterfunktionen mit `_`-Präfix:

```python
_list_trackers(table, active_only, user_id)
_get_tracker(table, tracker_id, user_id)
_delete_tracker(table, tracker_id, user_id)
_toggle_tracker(table, tracker_id, active, user_id)
_get_latest_snapshot(snap_table, tracker_id)   # status='ok' mit Fallback
_snapshot_table(tracker_type) → str            # Typ → Snapshot-Tabelle
_tracker_table(tracker_type) → str             # Typ → Tracker-Tabelle
```

Die öffentlichen Funktionen (z.B. `list_gf_trackers`, `delete_homair_tracker`) sind 1-Zeilen-Wrapper die an die Generics delegieren. **Nie** die WHERE-Builder-Pattern duplizieren — neuen Tracker-Typ immer über die Generics implementieren.

---

### MyTrips.svelte Komponentenstruktur — eingeführt Block 6 Refactoring

`MyTrips.svelte` (Seiten-Container) delegiert an Sub-Komponenten:

| Komponente | Datei | Inhalt |
|------------|-------|--------|
| `AddTripModal` | `mytrips/AddTripModal.svelte` | Modal zum Eintragen manueller Reisen inkl. Geocoding |
| `ArchiveSyncBar` | `mytrips/ArchiveSyncBar.svelte` | Dawarich-Sync + ActualBudget-Sync Buttons im Archiv-Tab |
| `TripCard` | `mytrips/TripCard.svelte` | Einzelne Reisekarte (planned/archive Modus) |
| `BucketListTab` | `mytrips/BucketListTab.svelte` | Wunschliste-Tab |
| `JournalTimeline` | `mytrips/JournalTimeline.svelte` | Chronik-Ansicht der erkannten Reisen |
| `OverviewTab` | `mytrips/OverviewTab.svelte` | Statistik-Übersicht mit Donut + Karte |

**Regel**: Neue MyTrips-Features als Sub-Komponente unter `mytrips/` anlegen — nie direkt in `MyTrips.svelte` hineinschreiben wenn es eine eigenständige Logikeinheit ist.

### TripHub.svelte Komponentenstruktur — eingeführt Block 6 Refactoring

`TripHub.svelte` (Seiten-Container) delegiert an Sub-Komponenten:

| Komponente | Datei | Inhalt |
|------------|-------|--------|
| `TripEditModal` | `triphub/TripEditModal.svelte` | Edit-Modal für Titel + Zielort mit Geocoding-Autocomplete |
| `WeatherWidget` | `triphub/WeatherWidget.svelte` | Wetter-Vorschau (7-Tage) |
| `BudgetWidget` | `triphub/BudgetWidget.svelte` | Budget-Übersicht + Buchungs-Tracking |
| `ChecklistWidget` | `triphub/ChecklistWidget.svelte` | KI-Checkliste mit due-dates |
| `SlotWidget` | `triphub/SlotWidget.svelte` | Flug/Hotel/Camping Buchungs-Slots |

**Regel**: Neue TripHub-Features als Widget unter `triphub/` anlegen. Jedes Widget erhält `trip` und `phase` als Props.

---

### Credentials-Handling — Security-Regel

**Niemals** Credentials (Dawarich-Token, ActualBudget-Passwort, API-Keys) aus dem Frontend an das Backend schicken.

Das Backend liest alle Credentials aus `user_settings` (Fernet-verschlüsselt in SQLite):
```python
# Korrekt:
url = data.dawarich_url or get_user_setting_value(uid, "dawarich_url") or ""
# Das Frontend schickt nur noch Aktions-Parameter (force_full, year etc.)
```

`localStorage.getItem('s-...')` für Backend-Credentials ist **verboten**. Credentials gehören in die Settings-DB, nicht in den Browser.

---

## Bekannte Svelte 5 Patterns

```svelte
<!-- $derived.by() für $t()-Store-Reads in Objekten -->
const labels = $derived.by(() => ({ key: $t('someKey') }));

<!-- bind: Props explizit auflisten -->
<Child bind:propA bind:propB />

<!-- $state-Arrays reaktiv updaten (kein .push!) -->
items = [...items, newItem];
```
