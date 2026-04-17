// ── PriceRadar Constants ──────────────────────────────────────────────────
// Shared across all PriceRadar sub-components. No logic, no imports.

export const CATEGORY_IDS = ['flights', 'hotels', 'camping', 'rentals'];

export const TRACKER_TYPES_BY_CAT = {
  flights: ['flight', 'google_flight'],
  hotels:  ['hotel'],
  camping: ['camping'],
  rentals: [],
};

// Shared Tailwind + inline-style constants for form inputs
export const inputCls   = 'w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]';
export const inputStyle = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
export const labelCls   = 'block text-xs font-bold uppercase tracking-wider mb-1';

// Autocomplete-Daten aus externen JSON-Dateien (476 Flughäfen, 1114 Destinationen)
import airportsData    from '$lib/data/airports.json';
import destinationsData from '$lib/data/destinations.json';

export const AIRPORTS     = airportsData;
export const DESTINATIONS = destinationsData;
