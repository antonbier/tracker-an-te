/**
 * $lib/utils.js — WanderSuite shared utilities
 *
 * Reine Funktionen ohne $state / Svelte-Importe.
 * Alles was früher in mehreren Komponenten inline stand, lebt hier.
 *
 * Exports:
 *   today          — aktuelles Datum als YYYY-MM-DD (einmal pro Modul-Load)
 *   getTodayStr()  — frisches Datum (für Komponenten die spät mounten)
 *   getTripPhase() — kanonische 3-Phasen-Logik für jeden Trip
 *   fmtCurrency()  — Euro-Formatierung
 *   daysBetween()  — Tage zwischen zwei ISO-Daten (positiv = Zukunft)
 */

// ── Datum ──────────────────────────────────────────────────────────────────

/**
 * Heutiges Datum als YYYY-MM-DD.
 * Wird einmal beim ersten Import berechnet — ausreichend für alles
 * was innerhalb einer Session rendered.
 */
export const today = new Date().toISOString().slice(0, 10);

/**
 * Frisches heutiges Datum — für Komponenten die ein neues Datum
 * bei jedem Aufruf benötigen (z.B. Checklist due-date min).
 */
export function getTodayStr() {
  return new Date().toISOString().slice(0, 10);
}

// ── Trip-Phase ─────────────────────────────────────────────────────────────

/**
 * Kanonische Trip-Phasen-Logik.
 *
 * @param {object} trip - Trip-Objekt mit start_date, end_date
 * @returns {'planning' | 'active' | 'archived'}
 *
 * Regeln (konsistent mit TripCard, TripHub, Dashboard):
 *   archived: end_date < today          (Reise ist vorbei)
 *   active:   start_date <= today <= end_date  (Reise läuft)
 *   planning: start_date > today        (noch in der Zukunft)
 */
export function getTripPhase(trip) {
  if (!trip) return 'planning';
  const t = today;
  const s = (trip.start_date || '').slice(0, 10);
  const e = (trip.end_date   || trip.start_date || '').slice(0, 10);
  if (!s && !e) return 'planning';
  if (e && t > e)  return 'archived';
  if (s && t >= s) return 'active';
  return 'planning';
}

/**
 * Prüft ob ein Trip als "upcoming" gilt (geplant, noch nicht gestartet).
 * Nutzt status als zusätzlichen Signal falls vorhanden.
 */
export function isUpcomingTrip(trip) {
  const phase = getTripPhase(trip);
  if (phase === 'active' || phase === 'planning') {
    const s = (trip.start_date || '').slice(0, 10);
    return !s || s > today || phase === 'active';
  }
  return false;
}

// ── Zahlen / Währung ───────────────────────────────────────────────────────

/**
 * Formatiert einen Betrag als Euro-String.
 * @param {number|string|null} amount
 * @param {number} decimals — Nachkommastellen (default 2)
 * @returns {string} z.B. "1.234,56 €"
 */
export function fmtCurrency(amount, decimals = 2) {
  const n = parseFloat(amount);
  if (isNaN(n)) return '– €';
  return n.toLocaleString('de-DE', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }) + ' €';
}

// ── Datum-Arithmetik ───────────────────────────────────────────────────────

/**
 * Tage zwischen zwei ISO-Daten.
 * Positiv = target liegt in der Zukunft.
 * @param {string} targetIso — YYYY-MM-DD
 * @param {string} [fromIso] — YYYY-MM-DD (default: today)
 */
export function daysBetween(targetIso, fromIso) {
  const from = fromIso ? new Date(fromIso + 'T00:00:00') : new Date(today + 'T00:00:00');
  const to   = new Date(targetIso + 'T00:00:00');
  return Math.round((to - from) / 86400000);
}

// ── Trip-Visuals (re-export aus triphub/helpers.js für App-weite Nutzung) ─
// Komponenten außerhalb von /triphub sollen hier importieren, nicht direkt
// aus $lib/components/triphub/helpers.js.
export { destinationGradient, strHash, wmoIcon } from '$lib/components/triphub/helpers.js';

// fmtDate + fmtRange aus priceradar/helpers — ebenfalls App-weit nützlich
export { fmtDate, fmtRange, dateOffset } from '$lib/components/priceradar/helpers.js';
