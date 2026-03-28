/**
 * ui/i18n.js — Internationalization (i18n)
 *
 * Translation files: /frontend/locales/{lang}.json
 * Path must be RELATIVE (not /locales/) for GitHub Pages compatibility.
 *
 * HTML usage:  <span data-i18n="myKey">Fallback</span>
 *              <input data-i18n-placeholder="myKey">
 * JS usage:    t('myKey')
 */

import { TRANSLATIONS, currentLang, selectedTrackerId, setTranslations, setCurrentLang } from '../core/state.js';

/**
 * Fetch and cache a locale JSON file. No-op if already loaded.
 * Fails silently — app stays functional, showing raw key names as fallback.
 */
export async function loadLocale(lang) {
  if (TRANSLATIONS[lang]) return;
  try {
    const r = await fetch(`locales/${lang}.json?v=0.1`);
    if (!r.ok) throw new Error(r.status);
    TRANSLATIONS[lang] = await r.json();
    setTranslations(TRANSLATIONS);
  } catch(e) { console.warn(`Locale '${lang}' failed:`, e); }
}

/**
 * Translate a key. Falls back to German, then to the raw key name.
 * @param {string} key
 * @returns {string}
 */
export function t(key) {
  return TRANSLATIONS[currentLang]?.[key] || TRANSLATIONS['de']?.[key] || key;
}

/**
 * Walk the DOM and fill all data-i18n / data-i18n-placeholder elements.
 * Also syncs the active state of .lang-btn buttons.
 */
export function applyTranslations() {
  document.documentElement.lang = currentLang;
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n')); });
  document.querySelectorAll('[data-i18n-opt]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n-opt')); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.getAttribute('data-i18n-placeholder')); });
  document.querySelectorAll('.lang-btn').forEach(btn => { btn.classList.toggle('active', btn.textContent === currentLang.toUpperCase()); });
}

/**
 * Switch the active language: loads locale if missing, updates state,
 * re-renders all translations, and reloads tracker lists (they contain
 * translated status badge text).
 */
export async function setLang(lang) {
  await loadLocale(lang);
  setCurrentLang(lang);
  applyTranslations();
  const { loadTrackers }  = await import('../app/ryanair.js');
  const { selectTracker } = await import('../app/ryanair.js');
  loadTrackers();
  if (selectedTrackerId) selectTracker(selectedTrackerId);
}
