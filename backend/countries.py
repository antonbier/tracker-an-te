"""
WanderSuite — Country name → ISO-2 mapping + visited countries query.
"""

from core.database import db

# ... (keep existing mapping table)

COUNTRY_MAP = {
    # German names
    "Deutschland": "DE", "Österreich": "AT", "Schweiz": "CH",
    "Frankreich": "FR", "Spanien": "ES", "Italien": "IT",
    "Portugal": "PT", "Niederlande": "NL", "Belgien": "BE",
    "Luxemburg": "LU", "Dänemark": "DK", "Schweden": "SE",
    "Norwegen": "NO", "Finnland": "FI", "Polen": "PL",
    "Tschechien": "CZ", "Slowakei": "SK", "Ungarn": "HU",
    "Rumänien": "RO", "Bulgarien": "BG", "Kroatien": "HR",
    "Slowenien": "SI", "Serbien": "RS", "Bosnien": "BA",
    "Montenegro": "ME", "Albanien": "AL", "Nordmazedonien": "MK",
    "Griechenland": "GR", "Türkei": "TR", "Zypern": "CY",
    "Malta": "MT", "Island": "IS", "Irland": "IE",
    "Vereinigtes Königreich": "GB", "Großbritannien": "GB",
    # English names
    "Germany": "DE", "Austria": "AT", "Switzerland": "CH",
    "France": "FR", "Spain": "ES", "Italy": "IT",
    "Portugal": "PT", "Netherlands": "NL", "Belgium": "BE",
    "Luxembourg": "LU", "Denmark": "DK", "Sweden": "SE",
    "Norway": "NO", "Finland": "FI", "Poland": "PL",
    "Czech Republic": "CZ", "Czechia": "CZ", "Slovakia": "SK",
    "Hungary": "HU", "Romania": "RO", "Bulgaria": "BG",
    "Croatia": "HR", "Slovenia": "SI", "Serbia": "RS",
    "Bosnia and Herzegovina": "BA", "Montenegro": "ME",
    "Albania": "AL", "North Macedonia": "MK", "Greece": "GR",
    "Turkey": "TR", "Cyprus": "CY", "Malta": "MT",
    "Iceland": "IS", "Ireland": "IE", "United Kingdom": "GB",
    "United States": "US", "Canada": "CA", "Mexico": "MX",
    "Japan": "JP", "China": "CN", "South Korea": "KR",
    "Thailand": "TH", "Vietnam": "VN", "Indonesia": "ID",
    "Australia": "AU", "New Zealand": "NZ", "India": "IN",
    "Brazil": "BR", "Argentina": "AR", "Chile": "CL",
    "Colombia": "CO", "Peru": "PE", "Morocco": "MA",
    "Egypt": "EG", "South Africa": "ZA", "Kenya": "KE",
    "Tanzania": "TZ", "Ethiopia": "ET", "Ghana": "GH",
    "Nigeria": "NG", "Senegal": "SN", "Tunisia": "TN",
    "Israel": "IL", "Jordan": "JO", "Lebanon": "LB",
    "United Arab Emirates": "AE", "Saudi Arabia": "SA",
    "Qatar": "QA", "Kuwait": "KW", "Bahrain": "BH",
    # Italian names
    "Germania": "DE", "Austria": "AT", "Svizzera": "CH",
    "Francia": "FR", "Spagna": "ES", "Italia": "IT",
    "Portogallo": "PT", "Paesi Bassi": "NL", "Belgio": "BE",
    "Danimarca": "DK", "Svezia": "SE", "Norvegia": "NO",
    "Finlandia": "FI", "Polonia": "PL", "Grecia": "GR",
    "Turchia": "TR", "Irlanda": "IE", "Regno Unito": "GB",
    "Stati Uniti": "US", "Canada": "CA", "Giappone": "JP",
    "Cina": "CN", "Australia": "AU", "Brasile": "BR",
    "Croazia": "HR", "Slovenia": "SI", "Ungheria": "HU",
}


def country_to_iso2(name: str) -> str | None:
    """Map a country name (DE/EN/IT) to ISO-2 code."""
    if not name:
        return None
    return COUNTRY_MAP.get(name.strip()) or COUNTRY_MAP.get(name.strip().title())


def get_visited_country_codes(user_id: int | None = None) -> dict:
    """Return ISO-2 codes of visited countries from detected_trips."""
    where = "WHERE user_id=?" if user_id else ""
    params = [user_id] if user_id else []

    with db() as conn:
        rows = conn.execute(
            f"SELECT country, COUNT(*) as trips FROM detected_trips {where} GROUP BY country",
            params
        ).fetchall()

    countries = [r["country"] for r in rows if r["country"]]
    codes = list(filter(None, [country_to_iso2(c) for c in countries]))

    return {
        "country_codes": list(set(codes)),
        "countries":     countries,
        "trip_count":    sum(r["trips"] for r in rows),
    }
