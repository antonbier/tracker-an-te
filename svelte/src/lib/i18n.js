import { writable, get } from 'svelte/store';
import { lang, apiUrl } from './stores.js';
import { browser } from '$app/environment';

import de from '../locales/de.json';
import en from '../locales/en.json';
import it from '../locales/it.json';

const allLocales = { de, en, it };

// Reaktiver translations-Store — Komponenten subscriben automatisch
export const translations = writable(allLocales[get(lang)] || de);

export async function loadLocale(locale) {
  const selected = allLocales[locale] || allLocales['de'];
  translations.set(selected);
}

// t() als reaktive Funktion — liest direkt aus Store
export function t(key) {
  const tr = get(translations);
  return tr[key] ?? key;
}

// Sprache wechseln + in Backend speichern
export async function setLang(locale) {
  lang.set(locale);
  await loadLocale(locale);
  // Persist to backend if configured
  const url = browser ? localStorage.getItem('apiUrl') || get(apiUrl) : get(apiUrl);
  if (url) {
    try {
      await fetch(`${url.replace(/\/$/, '')}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: locale }),
      });
    } catch { /* offline — localStorage is enough */ }
  }
}
