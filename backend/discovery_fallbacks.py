"""
WanderSuite — Discovery Fallback SVGs

Lokale Gradient-SVGs pro Landschaftstyp.
Werden als Platzhalter verwendet wenn Immich + Unsplash fehlschlagen.
Ein Hintergrund-Job versucht alle 2h echte Bilder nachzuladen.

Landscape-Typen: mountains, sea, forest, city, mix (default)
"""

from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

# ── SVG-Definitionen ──────────────────────────────────────────────────────────

_SVGS: dict[str, str] = {

    "mountains": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1a1a2e"/>
      <stop offset="60%" stop-color="#4a6fa5"/>
      <stop offset="100%" stop-color="#e8c59a"/>
    </linearGradient>
    <linearGradient id="snow" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#d0dce8"/>
    </linearGradient>
    <linearGradient id="rock" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#6b7b8d"/>
      <stop offset="100%" stop-color="#3d4a56"/>
    </linearGradient>
    <linearGradient id="valley" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2d5a27"/>
      <stop offset="100%" stop-color="#1a3a16"/>
    </linearGradient>
  </defs>
  <!-- Sky -->
  <rect width="800" height="500" fill="url(#sky)"/>
  <!-- Stars -->
  <circle cx="120" cy="40" r="1.5" fill="white" opacity="0.8"/>
  <circle cx="250" cy="25" r="1" fill="white" opacity="0.6"/>
  <circle cx="400" cy="15" r="1.5" fill="white" opacity="0.9"/>
  <circle cx="580" cy="35" r="1" fill="white" opacity="0.7"/>
  <circle cx="700" cy="20" r="1.5" fill="white" opacity="0.8"/>
  <!-- Background mountains -->
  <polygon points="0,320 120,160 240,280 360,140 480,260 600,120 720,240 800,180 800,500 0,500"
           fill="#4a5a6a" opacity="0.5"/>
  <!-- Mid mountains with snow -->
  <polygon points="0,380 80,220 160,310 280,130 400,260 520,110 640,230 760,150 800,200 800,500 0,500"
           fill="url(#rock)"/>
  <!-- Snow caps -->
  <polygon points="240,180 280,130 320,180" fill="url(#snow)" opacity="0.9"/>
  <polygon points="480,165 520,110 560,165" fill="url(#snow)" opacity="0.9"/>
  <polygon points="720,205 760,150 800,200 800,210" fill="url(#snow)" opacity="0.9"/>
  <polygon points="40,270 80,220 120,270" fill="url(#snow)" opacity="0.7"/>
  <!-- Valley / foreground -->
  <rect x="0" y="400" width="800" height="100" fill="url(#valley)"/>
  <!-- Moon -->
  <circle cx="650" cy="70" r="28" fill="#fff8e0" opacity="0.9"/>
  <circle cx="662" cy="62" r="22" fill="#4a6fa5" opacity="0.4"/>
</svg>""",

    "sea": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
  <defs>
    <linearGradient id="sky_sea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0d47a1"/>
      <stop offset="50%" stop-color="#42a5f5"/>
      <stop offset="100%" stop-color="#ffcc80"/>
    </linearGradient>
    <linearGradient id="ocean" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0277bd"/>
      <stop offset="100%" stop-color="#01579b"/>
    </linearGradient>
    <linearGradient id="sand" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffe0a0"/>
      <stop offset="100%" stop-color="#d4a44c"/>
    </linearGradient>
    <radialGradient id="sun" cx="50%" cy="50%">
      <stop offset="0%" stop-color="#fff9c4"/>
      <stop offset="100%" stop-color="#ffb300" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <!-- Sky -->
  <rect width="800" height="500" fill="url(#sky_sea)"/>
  <!-- Sun glow -->
  <circle cx="680" cy="120" r="80" fill="url(#sun)" opacity="0.6"/>
  <circle cx="680" cy="120" r="35" fill="#fff9c4"/>
  <!-- Horizon shimmer -->
  <rect x="0" y="268" width="800" height="4" fill="#ffffff" opacity="0.3"/>
  <!-- Ocean -->
  <rect x="0" y="270" width="800" height="160" fill="url(#ocean)"/>
  <!-- Waves -->
  <path d="M0,295 Q100,280 200,295 Q300,310 400,295 Q500,280 600,295 Q700,310 800,295 L800,310 Q700,325 600,310 Q500,295 400,310 Q300,325 200,310 Q100,295 0,310 Z"
        fill="#29b6f6" opacity="0.4"/>
  <path d="M0,330 Q80,318 160,330 Q240,342 320,330 Q400,318 480,330 Q560,342 640,330 Q720,318 800,330 L800,342 Q720,330 640,342 Q560,354 480,342 Q400,330 320,342 Q240,354 160,342 Q80,330 0,342 Z"
        fill="#4dd0e1" opacity="0.3"/>
  <!-- Sun reflection -->
  <ellipse cx="680" cy="290" rx="60" ry="10" fill="#fff9c4" opacity="0.25"/>
  <!-- Sand beach -->
  <path d="M0,430 Q200,410 400,420 Q600,430 800,415 L800,500 L0,500 Z"
        fill="url(#sand)"/>
  <!-- Distant island -->
  <ellipse cx="200" cy="268" rx="60" ry="12" fill="#1b5e20" opacity="0.7"/>
  <!-- Clouds -->
  <ellipse cx="150" cy="80" rx="70" ry="22" fill="white" opacity="0.7"/>
  <ellipse cx="200" cy="70" rx="50" ry="18" fill="white" opacity="0.8"/>
  <ellipse cx="350" cy="50" rx="55" ry="18" fill="white" opacity="0.6"/>
</svg>""",

    "forest": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
  <defs>
    <linearGradient id="forest_sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#263238"/>
      <stop offset="100%" stop-color="#37474f"/>
    </linearGradient>
    <linearGradient id="tree_dark" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1b5e20"/>
      <stop offset="100%" stop-color="#0a2e0a"/>
    </linearGradient>
    <linearGradient id="tree_mid" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2e7d32"/>
      <stop offset="100%" stop-color="#1b5e20"/>
    </linearGradient>
    <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3e2723"/>
      <stop offset="100%" stop-color="#1a0a00"/>
    </linearGradient>
    <radialGradient id="moon_glow" cx="50%" cy="50%">
      <stop offset="0%" stop-color="#e8f5e9" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#e8f5e9" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <!-- Night sky -->
  <rect width="800" height="500" fill="url(#forest_sky)"/>
  <!-- Stars -->
  <circle cx="100" cy="30" r="1.2" fill="white" opacity="0.9"/>
  <circle cx="220" cy="50" r="0.8" fill="white" opacity="0.7"/>
  <circle cx="350" cy="20" r="1.5" fill="white" opacity="0.8"/>
  <circle cx="500" cy="40" r="1" fill="white" opacity="0.6"/>
  <circle cx="650" cy="25" r="1.2" fill="white" opacity="0.9"/>
  <circle cx="750" cy="55" r="0.8" fill="white" opacity="0.7"/>
  <!-- Moon glow -->
  <circle cx="400" cy="80" r="60" fill="url(#moon_glow)"/>
  <circle cx="400" cy="80" r="25" fill="#e8f5e9" opacity="0.95"/>
  <!-- Background trees (dark) -->
  <polygon points="0,400 30,250 60,400" fill="url(#tree_dark)"/>
  <polygon points="50,420 90,230 130,420" fill="url(#tree_dark)"/>
  <polygon points="120,410 160,210 200,410" fill="url(#tree_dark)"/>
  <polygon points="180,420 230,190 280,420" fill="url(#tree_dark)"/>
  <polygon points="300,410 350,180 400,410" fill="url(#tree_dark)"/>
  <polygon points="400,420 450,200 500,420" fill="url(#tree_dark)"/>
  <polygon points="500,410 550,170 600,410" fill="url(#tree_dark)"/>
  <polygon points="600,420 650,190 700,420" fill="url(#tree_dark)"/>
  <polygon points="700,410 750,210 800,410" fill="url(#tree_dark)"/>
  <!-- Mid trees (slightly lighter) -->
  <polygon points="60,450 100,290 140,450" fill="url(#tree_mid)" opacity="0.85"/>
  <polygon points="200,460 250,270 300,460" fill="url(#tree_mid)" opacity="0.85"/>
  <polygon points="350,450 410,250 470,450" fill="url(#tree_mid)" opacity="0.85"/>
  <polygon points="530,455 590,260 650,455" fill="url(#tree_mid)" opacity="0.85"/>
  <polygon points="670,450 730,275 790,450" fill="url(#tree_mid)" opacity="0.85"/>
  <!-- Ground -->
  <rect x="0" y="440" width="800" height="60" fill="url(#ground)"/>
  <!-- Fog / mist layer -->
  <rect x="0" y="390" width="800" height="60" fill="#b2dfdb" opacity="0.08"/>
  <!-- Moon reflection path -->
  <ellipse cx="400" cy="445" rx="40" ry="6" fill="#e8f5e9" opacity="0.1"/>
</svg>""",

    "city": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
  <defs>
    <linearGradient id="city_sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0a1a"/>
      <stop offset="70%" stop-color="#1a1a3e"/>
      <stop offset="100%" stop-color="#3a2a5e"/>
    </linearGradient>
    <linearGradient id="building_a" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1e2a3a"/>
      <stop offset="100%" stop-color="#0d1520"/>
    </linearGradient>
    <linearGradient id="building_b" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2a1a3a"/>
      <stop offset="100%" stop-color="#150d20"/>
    </linearGradient>
    <linearGradient id="street" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1a1a2e"/>
      <stop offset="100%" stop-color="#0d0d1a"/>
    </linearGradient>
  </defs>
  <!-- Night sky -->
  <rect width="800" height="500" fill="url(#city_sky)"/>
  <!-- Stars -->
  <circle cx="80" cy="30" r="1" fill="white" opacity="0.6"/>
  <circle cx="180" cy="50" r="1.2" fill="white" opacity="0.8"/>
  <circle cx="320" cy="20" r="0.8" fill="white" opacity="0.5"/>
  <circle cx="460" cy="45" r="1" fill="white" opacity="0.7"/>
  <circle cx="580" cy="15" r="1.2" fill="white" opacity="0.9"/>
  <circle cx="720" cy="35" r="0.8" fill="white" opacity="0.6"/>
  <!-- City glow on horizon -->
  <ellipse cx="400" cy="310" rx="400" ry="80" fill="#ff6b35" opacity="0.08"/>
  <ellipse cx="400" cy="310" rx="300" ry="50" fill="#ffa500" opacity="0.06"/>
  <!-- Buildings back row -->
  <rect x="0"   y="180" width="60"  height="320" fill="url(#building_a)"/>
  <rect x="70"  y="220" width="50"  height="280" fill="url(#building_b)"/>
  <rect x="130" y="150" width="80"  height="350" fill="url(#building_a)"/>
  <rect x="220" y="200" width="55"  height="300" fill="url(#building_b)"/>
  <rect x="285" y="120" width="70"  height="380" fill="url(#building_a)"/>
  <rect x="365" y="170" width="90"  height="330" fill="url(#building_b)"/>
  <rect x="465" y="140" width="65"  height="360" fill="url(#building_a)"/>
  <rect x="540" y="190" width="75"  height="310" fill="url(#building_b)"/>
  <rect x="625" y="160" width="85"  height="340" fill="url(#building_a)"/>
  <rect x="720" y="210" width="80"  height="290" fill="url(#building_b)"/>
  <!-- Window lights (warm yellow) -->
  <rect x="10"  y="200" width="8" height="6" fill="#ffd54f" opacity="0.8"/>
  <rect x="25"  y="215" width="8" height="6" fill="#ffd54f" opacity="0.6"/>
  <rect x="10"  y="230" width="8" height="6" fill="#ffd54f" opacity="0.9"/>
  <rect x="145" y="165" width="8" height="6" fill="#ffd54f" opacity="0.7"/>
  <rect x="165" y="180" width="8" height="6" fill="#ffd54f" opacity="0.8"/>
  <rect x="145" y="200" width="8" height="6" fill="#ffd54f" opacity="0.5"/>
  <rect x="165" y="215" width="8" height="6" fill="#ffd54f" opacity="0.9"/>
  <rect x="295" y="135" width="8" height="6" fill="#ffd54f" opacity="0.8"/>
  <rect x="315" y="150" width="8" height="6" fill="#ffd54f" opacity="0.6"/>
  <rect x="295" y="170" width="8" height="6" fill="#ffd54f" opacity="0.9"/>
  <rect x="380" y="185" width="8" height="6" fill="#ffd54f" opacity="0.7"/>
  <rect x="400" y="200" width="8" height="6" fill="#ffd54f" opacity="0.8"/>
  <rect x="420" y="185" width="8" height="6" fill="#ffd54f" opacity="0.5"/>
  <rect x="480" y="155" width="8" height="6" fill="#ffd54f" opacity="0.9"/>
  <rect x="500" y="170" width="8" height="6" fill="#ffd54f" opacity="0.7"/>
  <rect x="480" y="190" width="8" height="6" fill="#ffd54f" opacity="0.8"/>
  <rect x="640" y="175" width="8" height="6" fill="#ffd54f" opacity="0.6"/>
  <rect x="660" y="190" width="8" height="6" fill="#ffd54f" opacity="0.9"/>
  <rect x="640" y="210" width="8" height="6" fill="#ffd54f" opacity="0.7"/>
  <rect x="735" y="225" width="8" height="6" fill="#ffd54f" opacity="0.8"/>
  <!-- Street / ground -->
  <rect x="0" y="430" width="800" height="70" fill="url(#street)"/>
  <!-- Street lights reflection -->
  <ellipse cx="200" cy="440" rx="30" ry="5" fill="#ffa500" opacity="0.15"/>
  <ellipse cx="500" cy="440" rx="30" ry="5" fill="#ffa500" opacity="0.15"/>
  <!-- Antenna on tallest building -->
  <line x1="319" y1="120" x2="319" y2="90" stroke="#4a5568" stroke-width="2"/>
  <circle cx="319" cy="88" r="3" fill="#ff4444" opacity="0.9"/>
</svg>""",

    "mix": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
  <defs>
    <linearGradient id="mix_sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1a237e"/>
      <stop offset="40%" stop-color="#5c6bc0"/>
      <stop offset="70%" stop-color="#ff8a65"/>
      <stop offset="100%" stop-color="#ffcc02"/>
    </linearGradient>
    <linearGradient id="mix_land" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2e7d32"/>
      <stop offset="100%" stop-color="#1b5e20"/>
    </linearGradient>
    <linearGradient id="mix_water" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0288d1"/>
      <stop offset="100%" stop-color="#01579b"/>
    </linearGradient>
    <radialGradient id="mix_sun" cx="50%" cy="50%">
      <stop offset="0%" stop-color="#fff9c4"/>
      <stop offset="50%" stop-color="#ffcc02" stop-opacity="0.5"/>
      <stop offset="100%" stop-color="#ff8a65" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <!-- Dusk sky -->
  <rect width="800" height="500" fill="url(#mix_sky)"/>
  <!-- Sun setting -->
  <circle cx="400" cy="280" r="100" fill="url(#mix_sun)" opacity="0.5"/>
  <circle cx="400" cy="280" r="40" fill="#fff9c4" opacity="0.95"/>
  <!-- Clouds pink/orange -->
  <ellipse cx="150" cy="120" rx="90" ry="28" fill="#ff8a65" opacity="0.5"/>
  <ellipse cx="200" cy="108" rx="65" ry="22" fill="#ffb74d" opacity="0.6"/>
  <ellipse cx="600" cy="100" rx="80" ry="25" fill="#ff8a65" opacity="0.4"/>
  <ellipse cx="650" cy="88" rx="55" ry="20" fill="#ffcc02" opacity="0.5"/>
  <ellipse cx="500" cy="150" rx="70" ry="20" fill="#ce93d8" opacity="0.4"/>
  <!-- Distant hills -->
  <path d="M0,310 Q100,260 200,300 Q300,340 400,280 Q500,220 600,270 Q700,320 800,290 L800,500 L0,500Z"
        fill="#388e3c" opacity="0.7"/>
  <!-- Water / lake -->
  <ellipse cx="400" cy="370" rx="200" ry="40" fill="url(#mix_water)" opacity="0.85"/>
  <!-- Sun reflection on water -->
  <ellipse cx="400" cy="375" rx="60" ry="10" fill="#fff9c4" opacity="0.4"/>
  <!-- Foreground land -->
  <path d="M0,420 Q200,400 400,415 Q600,430 800,410 L800,500 L0,500Z"
        fill="url(#mix_land)"/>
  <!-- Trees silhouette -->
  <polygon points="50,420  70,370  90,420"  fill="#1b5e20"/>
  <polygon points="90,425  115,365 140,425" fill="#1b5e20"/>
  <polygon points="640,415 665,355 690,415" fill="#1b5e20"/>
  <polygon points="690,420 715,360 740,420" fill="#1b5e20"/>
  <!-- Birds -->
  <path d="M300,130 Q308,124 316,130" stroke="#1a237e" stroke-width="1.5" fill="none"/>
  <path d="M330,115 Q338,109 346,115" stroke="#1a237e" stroke-width="1.5" fill="none"/>
  <path d="M360,125 Q368,119 376,125" stroke="#1a237e" stroke-width="1.5" fill="none"/>
</svg>""",
}

# Default fallback wenn landscape unbekannt
_DEFAULT = "mix"

LANDSCAPE_MAP = {
    "mountains": "mountains",
    "sea":       "sea",
    "forest":    "forest",
    "city":      "city",
    "mix":       "mix",
    # Aliasse
    "beach":     "sea",
    "ocean":     "sea",
    "jungle":    "forest",
    "urban":     "city",
    "rural":     "mix",
}


def get_fallback_url(landscape: str | None) -> str:
    """Gibt die interne Fallback-URL für einen Landschaftstyp zurück."""
    key = LANDSCAPE_MAP.get((landscape or "").lower(), _DEFAULT)
    return f"/api/discovery/fallback/{key}"


@router.get("/{landscape}")
async def serve_fallback(landscape: str):
    """Liefert ein eingebettetes SVG als Fallback-Bild."""
    key = LANDSCAPE_MAP.get(landscape.lower(), _DEFAULT)
    svg = _SVGS[key]
    return Response(
        content=svg.encode(),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=604800"},  # 7 Tage
    )
