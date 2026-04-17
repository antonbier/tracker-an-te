import { writable, derived, get } from 'svelte/store';
import { lang, apiUrl } from './stores.js';
import { browser } from '$app/environment';

import de from '../locales/de.json';
import en from '../locales/en.json';
import it from '../locales/it.json';
import es from '../locales/es.json';

// Alle verfügbaren Locales — neue Sprache: JSON importieren + hier eintragen
export const allLocales = { de, en, it, es };

// Lesbare Namen für Dropdown-Labels
export const localeLabels = {
  de: 'DE 🇩🇪',
  en: 'EN 🇬🇧',
  it: 'IT 🇮🇹',
  es: 'ES 🇪🇸',
};

// Reaktiver translations-Store
export const translations = writable(allLocales[get(lang)] || en);

// t als derived Store — Komponenten nutzen $t('key') und re-rendern automatisch
export const t = derived(
  translations,
  ($tr) => (key) => $tr[key] ?? key
);

export async function loadLocale(locale) {
  translations.set(allLocales[locale] || allLocales['de']);
}

// Sprache wechseln + reaktiv updaten + Backend-Sync
export async function setLang(locale) {
  lang.set(locale);
  translations.set(allLocales[locale] || allLocales['en']);
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('ws-lang', locale);
    localStorage.setItem('lang', locale);
  }
  if (!browser) return;
  const url = localStorage.getItem('apiUrl') || get(apiUrl);
  if (url) {
    try {
      await fetch(`${url.replace(/\/$/, '')}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: locale }),
      });
    } catch { /* offline */ }
  }
}

// ── Globaler Datumsformat-Helper ──────────────────────────────────────────
// Nutzt ws-date-format aus localStorage (gesetzt von Settings)
// Format: DD.MM.YYYY (default) | MM/DD/YYYY | YYYY-MM-DD
export function fmtDate(iso) {
  if (!iso) return '–';
  const parts = String(iso).slice(0, 10).split('-');
  if (parts.length !== 3) return iso;
  const [yyyy, mm, dd] = parts;
  const fmt = typeof localStorage !== 'undefined' ? (localStorage.getItem('ws-date-format') || 'DD.MM.YYYY') : 'DD.MM.YYYY';
  if (fmt === 'MM/DD/YYYY') return `${mm}/${dd}/${yyyy}`;
  if (fmt === 'YYYY-MM-DD') return `${yyyy}-${mm}-${dd}`;
  return `${dd}.${mm}.${yyyy}`;
}

// Datumsbereich formatieren
export function fmtDateRange(from, to) {
  return to ? `${fmtDate(from)} – ${fmtDate(to)}` : fmtDate(from);
}
