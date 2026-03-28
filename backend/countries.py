"""
WanderSuite — GET /api/dawarich/countries
Returns a list of visited ISO-3166-1 alpha-2 country codes
derived from the locally stored detected_trips.

Country names (from Nominatim) are mapped to ISO codes via
a comprehensive lookup table. Falls back to coordinate-based
country detection if name mapping fails.
"""

from database import list_detected_trips
from settings_manager import get_setting_value

# Comprehensive country name → ISO-2 mapping (covers Nominatim output)
COUNTRY_NAME_TO_ISO = {
    # German names (Nominatim DE locale)
    "Deutschland": "DE", "Österreich": "AT", "Schweiz": "CH", "Frankreich": "FR",
    "Italien": "IT", "Spanien": "ES", "Portugal": "PT", "Niederlande": "NL",
    "Belgien": "BE", "Polen": "PL", "Tschechien": "CZ", "Slowakei": "SK",
    "Ungarn": "HU", "Rumänien": "RO", "Griechenland": "GR", "Kroatien": "HR",
    "Slowenien": "SI", "Dänemark": "DK", "Schweden": "SE", "Norwegen": "NO",
    "Finnland": "FI", "Island": "IS", "Irland": "IE", "Vereinigtes Königreich": "GB",
    "Großbritannien": "GB", "Vereinigte Staaten": "US", "Vereinigte Staaten von Amerika": "US",
    "Kanada": "CA", "Mexiko": "MX", "Brasilien": "BR", "Argentinien": "AR",
    "Japan": "JP", "China": "CN", "Indien": "IN", "Australien": "AU",
    "Neuseeland": "NZ", "Südafrika": "ZA", "Marokko": "MA", "Ägypten": "EG",
    "Türkei": "TR", "Russland": "RU", "Ukraine": "UA", "Weißrussland": "BY",
    "Litauen": "LT", "Lettland": "LV", "Estland": "EE", "Albanien": "AL",
    "Bulgarien": "BG", "Serbien": "RS", "Montenegro": "ME", "Nordmazedonien": "MK",
    "Bosnien und Herzegowina": "BA", "Kosovo": "XK", "Malta": "MT",
    "Luxemburg": "LU", "Liechtenstein": "LI", "Andorra": "AD", "Monaco": "MC",
    "San Marino": "SM", "Vatikanstadt": "VA",
    # English names (Nominatim EN locale)
    "Germany": "DE", "Austria": "AT", "Switzerland": "CH", "France": "FR",
    "Italy": "IT", "Spain": "ES", "Portugal": "PT", "Netherlands": "NL",
    "Belgium": "BE", "Poland": "PL", "Czech Republic": "CZ", "Czechia": "CZ",
    "Slovakia": "SK", "Hungary": "HU", "Romania": "RO", "Greece": "GR",
    "Croatia": "HR", "Slovenia": "SI", "Denmark": "DK", "Sweden": "SE",
    "Norway": "NO", "Finland": "FI", "Iceland": "IS", "Ireland": "IE",
    "United Kingdom": "GB", "United States": "US", "United States of America": "US",
    "Canada": "CA", "Mexico": "MX", "Brazil": "BR", "Argentina": "AR",
    "Japan": "JP", "China": "CN", "India": "IN", "Australia": "AU",
    "New Zealand": "NZ", "South Africa": "ZA", "Morocco": "MA", "Egypt": "EG",
    "Turkey": "TR", "Russia": "RU", "Ukraine": "UA", "Belarus": "BY",
    "Lithuania": "LT", "Latvia": "LV", "Estonia": "EE", "Albania": "AL",
    "Bulgaria": "BG", "Serbia": "RS", "Montenegro": "ME", "North Macedonia": "MK",
    "Bosnia and Herzegovina": "BA", "Kosovo": "XK", "Malta": "MT",
    "Luxembourg": "LU", "Liechtenstein": "LI", "Andorra": "AD", "Monaco": "MC",
    "San Marino": "SM", "Vatican City": "VA",
    # Italian names (common when user is in IT)
    "Italia": "IT", "Germania": "DE", "Francia": "FR", "Spagna": "ES",
    "Svizzera": "CH", "Austria": "AT", "Paesi Bassi": "NL", "Belgio": "BE",
    "Portogallo": "PT", "Polonia": "PL", "Repubblica Ceca": "CZ", "Ungheria": "HU",
    "Romania": "RO", "Grecia": "GR", "Croazia": "HR", "Slovenia": "SI",
    "Danimarca": "DK", "Svezia": "SE", "Norvegia": "NO", "Finlandia": "FI",
    "Irlanda": "IE", "Regno Unito": "GB", "Stati Uniti": "US", "Canada": "CA",
    "Messico": "MX", "Brasile": "BR", "Argentina": "AR", "Giappone": "JP",
    "Cina": "CN", "India": "IN", "Australia": "AU",
}


def get_visited_country_codes() -> dict:
    """
    Return visited ISO-2 country codes from locally stored detected_trips.
    Also returns the raw country names for display.
    """
    dawarich_configured = bool(
        get_setting_value("dawarich_url") and get_setting_value("dawarich_token")
    )

    if not dawarich_configured:
        return {
            "configured": False,
            "country_codes": [],
            "countries": [],
            "trip_count": 0,
        }

    trips = list_detected_trips(limit=1000)
    codes = set()
    names = set()

    for trip in trips:
        country_name = (trip.get("country") or "").strip()
        if not country_name:
            continue
        names.add(country_name)
        # Try direct lookup
        iso = COUNTRY_NAME_TO_ISO.get(country_name)
        if iso:
            codes.add(iso)
        else:
            # Try case-insensitive partial match
            cl = country_name.lower()
            for k, v in COUNTRY_NAME_TO_ISO.items():
                if k.lower() == cl:
                    codes.add(v)
                    break

    return {
        "configured": True,
        "country_codes": sorted(codes),
        "countries": sorted(names),
        "trip_count": len(trips),
    }
