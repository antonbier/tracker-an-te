/**
 * triphub/helpers.js
 * Shared utilities for TripHub widgets.
 */

/**
 * Deterministic integer hash from a string (djb2).
 */
export function strHash(str) {
  let h = 5381;
  for (let i = 0; i < (str || '').length; i++) {
    h = ((h << 5) + h) ^ str.charCodeAt(i);
    h = h >>> 0; // keep unsigned 32-bit
  }
  return h;
}

/**
 * Generate a stable, brand-aligned CSS gradient from a destination string.
 * Palette: Stone, Sand, soft Orange — WanderSuite brand feel.
 * No external image requests.
 */
const GRADIENT_PALETTES = [
  // Stone/Sand warm
  ['#2c2520', '#5c4a3a', '#8b6f4e'],
  // Desert dusk
  ['#3b2a1a', '#7c4f2a', '#c4622d'],
  // Slate blue-stone
  ['#1a2030', '#2d3a4a', '#4a6070'],
  // Forest deep
  ['#1a2820', '#2d4a38', '#4a7a5a'],
  // Terracotta warm
  ['#3a1f1a', '#7a3f2a', '#c46040'],
  // Sand dune
  ['#2a2218', '#5a4a32', '#9a7a50'],
  // Ocean mist
  ['#1a2535', '#2a4555', '#3a6070'],
  // Olive grove
  ['#22281a', '#445535', '#6a7a4a'],
];

export function destinationGradient(destination, travelMode) {
  const seed = strHash(destination || 'wandersuite');
  const palette = GRADIENT_PALETTES[seed % GRADIENT_PALETTES.length];
  const angle = 110 + (seed % 60);
  // car trips lean green, flights lean blue-stone
  const [c1, c2, c3] = travelMode === 'car'
    ? [GRADIENT_PALETTES[(seed + 3) % GRADIENT_PALETTES.length][0],
       GRADIENT_PALETTES[(seed + 3) % GRADIENT_PALETTES.length][1],
       GRADIENT_PALETTES[(seed + 3) % GRADIENT_PALETTES.length][2]]
    : palette;
  return `linear-gradient(${angle}deg, ${c1} 0%, ${c2} 55%, ${c3} 100%)`;
}

/**
 * WMO weather code → emoji
 */
export function wmoIcon(code) {
  if (code === 0)  return '☀️';
  if (code <= 2)   return '🌤️';
  if (code <= 3)   return '☁️';
  if (code <= 49)  return '🌫️';
  if (code <= 67)  return '🌧️';
  if (code <= 77)  return '🌨️';
  if (code <= 82)  return '🌦️';
  if (code <= 99)  return '⛈️';
  return '🌡️';
}
