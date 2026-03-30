import { writable, get } from 'svelte/store';
import { lang } from './stores.js';

// 1. Statische Imports (Vite verpackt diese JSONs automatisch fehlerfrei)
import de from '../locales/de.json';
import en from '../locales/en.json';
import it from '../locales/it.json';

// 2. Ein kleines Wörterbuch aller geladenen Sprachen anlegen
const allLocales = {
  de,
  en,
  it
};

// 3. Store initialisieren (Deutsch als Standard)
const _translations = writable(de);

// 4. Die Lade-Funktion (jetzt blitzschnell und ohne await/import-Fehler)
export async function loadLocale(locale) {
  // Wenn die Sprache existiert, nimm sie. Sonst Fallback auf 'de'.
  const selectedTranslations = allLocales[locale] || allLocales['de'];
  _translations.set(selectedTranslations);
}

export function t(key) {
  const translations = get(_translations);
  return translations[key] ?? key;
}

export { _translations as translations };
