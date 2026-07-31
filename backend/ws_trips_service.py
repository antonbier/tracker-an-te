"""
WanderSuite — ws_trips Business-Logik

Extrahiert aus routes/ws_trips.py (Monolith-Refactor): Todo-Generierung,
Immich-Foto-Galerie, Budget-Breakdown-Berechnung und ActualBudget-Sync.
routes/ws_trips.py bleibt für Pydantic-Modelle + Route-Handler (inkl. DB-
Writes, wie im übrigen File üblich) zuständig und ruft diese Funktionen auf.
"""

import base64
import json
import logging
import math
import os
from datetime import date

import httpx

import immich_client
from llm_client import call_openai, suggest
from settings_manager import get_setting_value

logger = logging.getLogger(__name__)


# ── KI To-Do Generierung ──────────────────────────────────────────────────────

def _build_todo_prompt(trip: dict) -> str:
    travel_mode = trip.get("travel_mode", "flight")
    destination = trip.get("destination") or trip.get("flex_month") or "unbekannt"
    dates = ""
    if trip.get("start_date"):
        dates = f" vom {trip['start_date']}"
        if trip.get("end_date"):
            dates += f" bis {trip['end_date']}"
    budget_str = f", Budget ca. {trip['budget']} €" if trip.get("budget") else ""
    vibes_str = ", ".join(trip.get("vibes") or [])
    path = trip.get("path", "known")

    if path == "inspire":
        dest_desc = f"KI-empfohlenes Ziel (Vibe: {vibes_str or 'offen'})"
        if trip.get("wish_text"):
            dest_desc += f", Wunsch: {trip['wish_text']}"
    else:
        dest_desc = destination

    mode_label = "Flugreise" if travel_mode == "flight" else "Autoreise"
    home_str = f" ab {trip['home_airport']}" if travel_mode == "flight" and trip.get("home_airport") else ""

    return f"""Du bist ein erfahrener Reise-Assistent. Erstelle 10 bis 15 konkrete, spezifische To-Dos für folgende Reise.

Ziel: {dest_desc}
Reiseart: {mode_label}{home_str}
Zeitraum: {dates or 'flexibel'}{budget_str}
Mitreisende: {trip.get('adults', 2)} Erw.{', ' + str(trip.get('children')) + ' Kind.' if trip.get('children') else ''}

Regeln:
- KEINE generischen To-Dos — was für diese Reise spezifisch ist
- Mische Kategorien: booking, documents, packing, general
- Antworte NUR mit JSON-Array, kein Text, kein Markdown:

[
  {{"task": "...", "category": "booking"}},
  ...
]"""


def fallback_todos(trip: dict) -> list[dict]:
    mode = trip.get("travel_mode", "flight")
    dest = trip.get("destination") or "Reiseziel"
    if mode == "flight":
        return [
            {"task": f"Flug nach {dest} buchen", "category": "booking"},
            {"task": "Reisedokumente prüfen (Reisepass/Ausweis)", "category": "documents"},
            {"task": "Unterkunft buchen", "category": "booking"},
            {"task": "Reisekrankenversicherung abschließen", "category": "documents"},
            {"task": "Koffer packen", "category": "packing"},
        ]
    return [
        {"task": "Route & Stopps planen", "category": "general"},
        {"task": "Fahrzeug & Tankstand prüfen", "category": "general"},
        {"task": "Unterkunft entlang der Route buchen", "category": "booking"},
        {"task": "Pannenhilfe / ADAC prüfen", "category": "documents"},
        {"task": "Koffer & Dachbox packen", "category": "packing"},
    ]


async def generate_todos(trip: dict) -> list[dict]:
    openai_key = get_setting_value("openai_key") or os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        logger.info("[WsTrips] Kein OpenAI Key — nutze Fallback-Todos")
        return fallback_todos(trip)

    prompt = _build_todo_prompt(trip)
    try:
        todos = await call_openai(prompt, openai_key, timeout=20.0)
        if todos:
            logger.info(f"[WsTrips] KI-Todos generiert: {len(todos)} Einträge")
            return [{"task": t.get("task", ""), "category": t.get("category", "general")} for t in todos[:15]]
    except Exception as e:
        logger.warning(f"[WsTrips] KI-Todo-Generierung fehlgeschlagen: {e}")

    return fallback_todos(trip)


# ── Immich Foto-Galerie ───────────────────────────────────────────────────────

async def fetch_trip_gallery(immich_url: str, immich_key: str, trip: dict) -> dict:
    """Lädt bis zu 12 Immich-Fotos für den Reisezeitraum inkl. Base64-Thumbnails
    und liefert Deep-Link + Metadaten."""
    date_from = (trip.get("start_date") or "")[:10]
    date_to = (trip.get("end_date") or trip.get("start_date") or "")[:10]
    destination = trip.get("destination") or trip.get("title") or ""

    async with httpx.AsyncClient(timeout=15.0, trust_env=False, follow_redirects=True) as client:
        items = await immich_client.search_metadata(
            immich_url, immich_key,
            query=destination or None, size=12, with_exif=True,
            taken_after=date_from + "T00:00:00.000Z" if date_from else None,
            taken_before=date_to + "T23:59:59.999Z" if date_to else None,
            client=client,
        )

        photos = []
        for item in items[:12]:
            asset_id = item.get("id")
            if not asset_id:
                continue
            thumb_data = None
            try:
                t_resp = await immich_client.fetch_thumbnail(immich_url, immich_key, asset_id, client=client)
                if t_resp.status_code == 200:
                    ct = t_resp.headers.get("content-type", "image/jpeg")
                    thumb_data = f"data:{ct};base64,{base64.b64encode(t_resp.content).decode()}"
            except Exception:
                pass
            photos.append({
                "asset_id": asset_id,
                "thumbnail_url": thumb_data or "",
                "taken_at": (item.get("fileCreatedAt") or "")[:10],
                "city": item.get("exifInfo", {}).get("city") or "",
                "country": item.get("exifInfo", {}).get("country") or "",
            })

    deep_link_params = ""
    if date_from and date_to:
        deep_link_params = f"?dateAfter={date_from}&dateBefore={date_to}"
    immich_deep_link = f"{immich_url}/photos{deep_link_params}"

    return {
        "photos": photos,
        "count": len(photos),
        "immich_url": immich_url,
        "deep_link": immich_deep_link,
        "date_from": date_from,
        "date_to": date_to,
    }


# ── Budget-Breakdown ──────────────────────────────────────────────────────────

def compute_budget_breakdown(trip: dict, trackers: dict) -> dict:
    booked_flight = 0.0
    booked_hotel = 0.0
    try:
        ft = trackers.get("flight")
        if ft and ft.get("is_booked") and ft.get("booked_price"):
            booked_flight = float(ft["booked_price"])
        ht = trackers.get("hotel") or trackers.get("camping")
        if ht and ht.get("is_booked") and ht.get("booked_price"):
            booked_hotel = float(ht["booked_price"])
    except Exception:
        pass

    total = float(trip.get("budget") or 0)
    manual_expenses = float(trip.get("manual_expenses") or 0)
    synced_expenses = float(trip.get("synced_expenses") or 0)

    synced_tx_raw = trip.get("synced_transactions_json") or "[]"
    try:
        synced_transactions = json.loads(synced_tx_raw)
    except Exception:
        synced_transactions = []

    total_spent = booked_flight + booked_hotel + manual_expenses + synced_expenses
    remaining = total - total_spent  # kann negativ sein
    on_site_net = max(0.0, total - booked_flight - booked_hotel - manual_expenses - synced_expenses)

    return {
        "total_budget": total,
        "booked_flight": booked_flight,
        "booked_hotel": booked_hotel,
        "manual_expenses": manual_expenses,
        "synced_expenses": synced_expenses,
        "synced_transactions": synced_transactions,
        "synced_at": trip.get("synced_at"),
        "on_site_budget": on_site_net,
        "remaining": remaining,
        "total_spent": total_spent,
        "has_budget": total > 0,
    }


# ── CO2-Schätzung ──────────────────────────────────────────────────────────────
# Grobe Heuristik, keine wissenschaftliche Bilanzierung — Distanz per Haversine
# zwischen Heimatort und geocodierten Ziel-Koordinaten (trip.lat/lon, nur gefüllt
# wenn Geocoding lief). Emissionsfaktoren in der Größenordnung gängiger
# Reise-CO2-Rechner (myclimate/atmosfair): Flug pro Passagier-km, Auto pro
# Fahrzeug-km (nicht mit Personenzahl multipliziert, da ein Auto unabhängig von
# der Belegung dieselbe Strecke fährt).
CO2_KG_PER_KM_FLIGHT = 0.195
CO2_KG_PER_KM_CAR    = 0.147


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def compute_co2_estimate(trip: dict, home_lat, home_lon) -> dict | None:
    """Grobe CO2-Schätzung für Hin+Rückflug/-fahrt. None wenn Ziel- oder
    Heimat-Koordinaten fehlen (kein Geocoding erfolgt bzw. kein Heimatort gesetzt)."""
    dest_lat, dest_lon = trip.get("lat"), trip.get("lon")
    if dest_lat is None or dest_lon is None or home_lat is None or home_lon is None:
        return None
    try:
        home_lat, home_lon = float(home_lat), float(home_lon)
        dest_lat, dest_lon = float(dest_lat), float(dest_lon)
    except (TypeError, ValueError):
        return None

    one_way_km = _haversine_km(home_lat, home_lon, dest_lat, dest_lon)
    roundtrip_km = one_way_km * 2

    mode = trip.get("travel_mode") or "flight"
    if mode == "car":
        kg = roundtrip_km * CO2_KG_PER_KM_CAR
    else:
        pax = max(1, int(trip.get("adults") or 1) + int(trip.get("children") or 0))
        kg = roundtrip_km * CO2_KG_PER_KM_FLIGHT * pax

    return {
        "distance_km": round(one_way_km),
        "roundtrip_km": round(roundtrip_km),
        "co2_kg": round(kg),
        "travel_mode": mode,
    }


# ── Smart-Zeile: Freitext → Formularfelder (WanderWizzard) ────────────────────
# Nutzt denselben LLM-Call+Parse-Pfad wie discovery.py (llm_client.suggest()) —
# globale Provider-Settings, kein eigener dritter LLM-Call-Pfad (siehe CLAUDE.md-Regel).

def _build_smart_parse_prompt(text: str) -> str:
    today = date.today().isoformat()
    return (
        f'Heute ist der {today}. Extrahiere aus folgendem Reisewunsch strukturierte Daten. '
        f'Antworte AUSSCHLIESSLICH mit einem JSON-Array, das genau ein Objekt enthält, mit exakt diesen Feldern:\n'
        f'[{{"destination": string|null, "start_date": "YYYY-MM-DD"|null, "end_date": "YYYY-MM-DD"|null, '
        f'"budget": number|null, "adults": number|null, "children": number|null, "travel_mode": "flight"|"car"|null}}]\n\n'
        f'Regeln:\n'
        f'- destination: Stadt oder Region als Klartext (z.B. "Lissabon"), null wenn kein konkretes Ziel genannt wird.\n'
        f'- Wenn nur ein Monat + Aufenthaltsdauer genannt wird (z.B. "5 Tage im September"), wähle ein plausibles '
        f'Datum in diesem Monat (nächstes Vorkommen ab heute) für start_date und end_date entsprechend der Dauer.\n'
        f'- budget: Gesamtbudget als Zahl ohne Währungssymbol, null wenn nicht genannt.\n'
        f'- adults/children: null wenn nicht genannt.\n'
        f'- travel_mode: "car" nur wenn explizit Auto/Roadtrip erwähnt wird, sonst null.\n\n'
        f'Reisewunsch: "{text}"'
    )


async def parse_smart_trip_query(text: str) -> dict | None:
    """Extrahiert Reise-Eckdaten aus einem Freitext-Wunsch. None wenn kein LLM-Key
    konfiguriert ist oder die Extraktion fehlschlägt — Caller zeigt dann einen
    Hinweis, das Formular manuell auszufüllen."""
    llm_provider = get_setting_value("llm_provider") or "openai"
    openai_key = get_setting_value("openai_key") or ""
    gemini_key = get_setting_value("gemini_key") or ""
    if not openai_key and not gemini_key:
        return None

    prompt = _build_smart_parse_prompt(text)
    try:
        result = await suggest(
            prompt, system_prompt=None,
            openai_key=openai_key, gemini_key=gemini_key,
            prefer=llm_provider, timeout=15.0, max_tokens=300, temperature=0.3,
        )
    except Exception as e:
        logger.warning(f"[SmartParse] LLM-Call fehlgeschlagen: {e}")
        return None
    if not result:
        return None

    parsed = result[0] if isinstance(result, list) else result
    if not isinstance(parsed, dict):
        return None
    return {
        "destination": parsed.get("destination") or None,
        "start_date": parsed.get("start_date") or None,
        "end_date": parsed.get("end_date") or None,
        "budget": parsed.get("budget") or None,
        "adults": parsed.get("adults") or None,
        "children": parsed.get("children") or None,
        "travel_mode": parsed.get("travel_mode") if parsed.get("travel_mode") in ("flight", "car") else None,
    }


# ── ActualBudget Sync ──────────────────────────────────────────────────────────

def compute_actual_budget_sync(start_date: str, end_date: str, actual_url: str,
                                actual_token: str, actual_file: str,
                                category_names: list[str]) -> dict:
    """Holt + filtert ActualBudget-Transaktionen für den Reisezeitraum.
    Gibt {"error": ...} bei Verbindungsfehler zurück (get_travel_expenses fängt
    intern ab), sonst {"transactions": [...], "total": float}."""
    from actual_budget import get_travel_expenses
    result = get_travel_expenses(
        base_url=actual_url,
        password=actual_token,
        budget_file=actual_file or "",
        category_names=category_names,
        year=None,  # Wir filtern manuell nach Datum
    )
    if "error" in result:
        return result

    all_txs = result.get("transactions", [])
    trip_txs = [
        tx for tx in all_txs
        if start_date <= (tx.get("date") or "") <= end_date
    ]

    compact = [
        {
            "date": tx.get("date", ""),
            "name": (tx.get("payee") or tx.get("notes") or "").strip()[:60],
            "amount": round(abs(tx.get("amount", 0)), 2),
        }
        for tx in trip_txs
        if tx.get("amount", 0) != 0
    ]
    compact.sort(key=lambda x: x["date"], reverse=True)
    total_synced = round(sum(c["amount"] for c in compact), 2)

    return {"transactions": compact, "total": total_synced}
