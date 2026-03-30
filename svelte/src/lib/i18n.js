import { writable, get } from 'svelte/store';
import { lang } from './stores.js';

const _translations = writable({});

export async function loadLocale(locale) {
  try {
    const mod = await import(`../locales/${locale}.json`, { assert: { type: 'json' } });
    _translations.set(mod.default);
  } catch {
    // Fallback to de
    const mod = await import('../locales/de.json', { assert: { type: 'json' } });
    _translations.set(mod.default);
  }
}

export function t(key) {
  const translations = get(_translations);
  return translations[key] ?? key;
}

export { _translations as translations };
