import { writable, derived, get } from 'svelte/store';
import { lang, apiUrl } from './stores.js';
import { browser } from '$app/environment';

import de from '../locales/de.json';
import en from '../locales/en.json';
import it from '../locales/it.json';

const allLocales = { de, en, it };

// Reaktiver translations-Store
export const translations = writable(allLocales[get(lang)] || de);

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
  translations.set(allLocales[locale] || allLocales['de']);
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
