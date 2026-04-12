"""
WanderSuite — Discovery Data Models

Trennung zwischen:
  - TravelPersonality: steuert LLM-Prompt & Discovery-Logik
  - TravelDefaults:    technische Reise-Parameter (Prefill, Buchung)
"""

from pydantic import BaseModel


class TravelPersonality(BaseModel):
    """Reisepersönlichkeit — KI-Prompt-Kontext."""
    travel_style:    str = ""        # adventure / relaxation / culture / nature / city
    climate_pref:    str = ""        # warm / mild / cold / any
    landscape_pref:  str = ""        # mountains / sea / forest / city / mix
    companions:      str = ""        # solo / couple / family / friends
    wish_text:       str = ""        # Freitext
    history_mode:    str = "blacklist"  # "blacklist" | "context"
    travel_mode:     str = "flight"  # "flight" | "car"
    max_travel_time: str = "any"     # "2h" | "4h" | "8h" | "12h" | "12h+"


class TravelDefaults(BaseModel):
    """Technische Reise-Defaults — Prefill & Buchungsparameter."""
    home_airport:   str = ""
    home_lat:       str = ""
    home_lon:       str = ""
    adults:         int = 2
    children:       int = 0
    unsplash_key:   str = ""
    immich_url:     str = ""
    immich_api_key: str = ""
