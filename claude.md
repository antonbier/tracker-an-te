# WanderSuite — Architekturdokumentation

> Letzte Aktualisierung: Phase 2B (Beta Branch)

## Projekt-Übersicht

WanderSuite ist eine **selbst-gehostete Travel-Tracking- und Preis-Monitoring-Anwendung**.

- **Frontend**: Svelte 5 + SvelteKit, Tailwind CSS v4
- **Backend**: FastAPI (Python)
- **Datenbank**: SQLite
- **Deployment**: Docker Compose (Unraid), Zoraxy Reverse Proxy
- **Repository**: `antonbier/tracker-an-te`
- **Branches**: `main` (stabil), `beta` (aktiv, Ports 8767/8768)

---

## Branch-Strategie

| Branch | Port Backend | Port Frontend | Zweck |
|--------|-------------|---------------|-------|
| `main` | 8765 | 8766 | Stabile Production-Release |
| `beta` | 8768 | 8767 | Aktive Entwicklung |

---

## Architektur-Entscheidungen

### Heimatort — Globale Verknüpfung (seit Phase 2A)

Der **Heimatort** (`home_lat`, `home_lon`, `home_name`) ist aus den Dawarich-Settings herausgelöst
und als **globale Basis-Einstellung** implementiert:

- **Backend-Keys**: `GLOBAL_KEYS` in `settings_manager.py` enthält `home_lat`, `home_lon`, `home_name`
- **Lookup-Priorität**: Per-User-Setting > Global-Setting > `None` (via `resolve_home_location(user_id)`)
- **Frontend**: `BasicTab.svelte` enthält die vollständige Heimatort-Sektion mit Nominatim-Geocode-Suche
- **IntegrationsTab**: Die `homeLat`/`homeLon`-Felder wurden entfernt — keine doppelte Datenhaltung
- **Wizard Step 1**: Beinhaltet das Heimatort-Feld inkl. Suche
- **Speicherung**: localStorage (`s-homeLat`, `s-homeLon`, `s-homeName`) + DB

### Partial Update Safety

Alle Settings-Endpunkte (`POST /api/settings`, `POST /api/settings/user`, `POST /api/settings/wizard/step`)
nutzen **Partial Updates**: Nur explizit übergebene Felder werden geschrieben. `None`/leere Werte überschreiben
**nie** bestehende Daten. Dies verhindert, dass Step 1 des Wizards die Keys aus Step 4 nullt.

```python
# settings_manager.py
def save_settings_bulk(settings: dict) -> None:
    # Only non-None values are written
    for key, value in settings.items():
        if key in GLOBAL_KEYS and value is not None:
            save_setting(key, str(value), fernet)
```

### Wizard-Endpoint

`POST /api/settings/wizard/step` — dedizierter Endpunkt für den 5-Step-Wizard:
- Akzeptiert `WizardStepPayload` (alle Felder optional)
- Teilt automatisch in `global_fields` vs. `user_fields`
- Schreibt nur non-None Werte

---

## 5-Step Setup-Wizard

Getriggert via 🪄-Icon im Header (`wizardOpen` Svelte-Store).

| Step | Titel | Inhalt | Gespeichert via |
|------|-------|--------|-----------------|
| 1 | Basis & Heimat | Backend-URL, Zeitzone, Datumsformat, Währung, Heimatort | `/api/settings/wizard/step` (global) |
| 2 | Self-Hosted Bridges | Dawarich, Immich, ActualBudget | `/api/settings/wizard/step` (user) |
| 3 | Reise-Defaults | 2 Akkordeons: Logistik + Persönlichkeit | `/api/settings/wizard/step` (user: ww_*) |
| 4 | KI & Engines | OpenAI, Gemini, SerpAPI Keys (mit Links) | `/api/settings/wizard/step` (global: *_key) |
| 5 | Erfolg | Konfetti-Animation, Summary-Chips, Abschluss-Button | — |

### Akkordeon-Muster (Step 3 / MyspaceDefaults)

Beide Wizard Step 3 und `MyspaceDefaults.svelte` verwenden dasselbe 2-Akkordeon-Layout:

```
Akkordeon 1 — 🧳 Logistik-Defaults
  ├── Reisende (Erwachsene, Kinder, Heimatflughafen)
  ├── Gepäck-Matrix (Kurz- und Langtrip, je 10/20/23 kg)
  └── Bevorzugte Flugzeiten (Abflug + Ankunft, ab/bis)

Akkordeon 2 — 🧭 Reisepersönlichkeit
  ├── Reisestil (Adventure/Entspannung/Kultur/Natur/City)
  ├── Klimapräferenz (Warm/Mild/Kalt/Egal)
  ├── Landschaft (Berge/Meer/Wald/Stadt/Mix)
  ├── Reisebegleitung (Solo/Pärchen/Familie/Freunde)
  ├── Reisemodus (Flug/Auto)
  ├── Max. Reisezeit
  ├── History-Modus (Blacklist/KI-Kontext)
  └── Freitext-Wunsch (max 500 Zeichen)
```

---

## Store-Architektur (Svelte)

```
stores.js
├── apiUrl          — persisted, Backend-URL
├── lang            — persisted, aktive Sprache
├── theme           — persisted, dark/light
├── jwtToken        — persisted, JWT für Auth
├── currentUser     — User-Objekt (localStorage)
├── appStatus       — auth_enabled etc.
├── currentPage     — aktive Seite
├── settingsOpen    — globaler Trigger für ⚙️ Modal
├── wizardOpen      — globaler Trigger für 🪄 Wizard
├── priceradarParams — WanderWizzard → PriceRadar Übergabe
└── activeWsTripId  — aktiver WS-Trip für TripHub
```

---

## Settings-Architektur

### Globale Settings (Admin, DB-Tabelle `settings`)

```
serpapi_key, gemini_key, openai_key, llm_provider
telegram_bot_token, telegram_chat_id, gotify_url, gotify_token
language, timezone, date_format, currency
home_lat, home_lon, home_name        ← NEU (Phase 2A)
```

### Per-User Settings (DB-Tabelle `user_settings`)

```
dawarich_url, dawarich_token
actual_url, actual_token, actual_file, travel_categories
home_lat, home_lon, home_name        ← User-Override möglich
timezone, date_format, currency      ← User-Override möglich
immich_url, immich_api_key, immich_geo_sync
ww_adults, ww_children, ww_home_airport
ww_lug_s10/s20/s23, ww_lug_l10/l20/l23
ww_dep_min/max, ww_arr_min/max
travel_style, climate_pref, landscape_pref, companions
wish_text, unsplash_key
travel_mode, max_travel_time, history_mode
```

---

## i18n

- Lokalisierungsdateien: `svelte/src/locales/de.json`, `en.json`
- i18n-Helper: `svelte/src/lib/i18n.js`
- Zugriff im Template: `{$t('key')}`
- Alle neuen UI-Strings **müssen** in beiden Dateien angelegt werden

---

## Docker Logging

Alle Services nutzen den `json-file` Driver mit Rotation:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## GitHub API Commit-Pattern

**Kritisch**: Patch-Skripte immer nach `/tmp/scriptname.py` schreiben, nie heredocs verwenden.
Verification-Output ausschließlich nach `sys.stderr`. Niemals `stdout` kontaminieren (base64-Korruption).

```python
# Korrekt:
python3 /tmp/patch.py
# Ausgabe nur: print("...", file=sys.stderr)
```

---

## Bekannte Svelte 5 Patterns

### $derived mit $t() Store-Reads

```svelte
<!-- ❌ Falsch — verliert Reaktivität -->
const tabLabels = $derived({ key: $t('someKey') });

<!-- ✅ Korrekt -->
const tabLabels = $derived.by(() => ({ key: $t('someKey') }));
```

### bind: Props in Child-Komponenten

Bei `$bindable()` Props immer explizit auflisten:
```svelte
<Child bind:propA bind:propB />
```
