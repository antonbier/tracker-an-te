// frontend/js/ui/i18n.js
import { TRANSLATIONS, currentLang, selectedTrackerId, setTranslations, setCurrentLang } from '../core/state.js';

export async function loadLocale(lang) {
  if (TRANSLATIONS[lang]) return;
  try {
    const r = await fetch(`/locales/${lang}.json?v=0.1`);
    if (!r.ok) throw new Error(r.status);
    TRANSLATIONS[lang] = await r.json();
    setTranslations(TRANSLATIONS);
  } catch(e) { console.warn(`Locale '${lang}' failed:`, e); }
}

export function t(key) {
  return TRANSLATIONS[currentLang]?.[key] || TRANSLATIONS['de']?.[key] || key;
}

export function applyTranslations() {
  document.documentElement.lang = currentLang;
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n')); });
  document.querySelectorAll('[data-i18n-opt]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n-opt')); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.getAttribute('data-i18n-placeholder')); });
  document.querySelectorAll('.lang-btn').forEach(btn => { btn.classList.toggle('active', btn.textContent === currentLang.toUpperCase()); });
}

export async function setLang(lang) {
  await loadLocale(lang);
  setCurrentLang(lang);
  applyTranslations();
  // Dynamische Imports um Zirkelabhängigkeiten zu vermeiden
  const { loadTrackers }    = await import('../app/ryanair.js');
  const { selectTracker }   = await import('../app/ryanair.js');
  loadTrackers();
  if (selectedTrackerId) selectTracker(selectedTrackerId);
}
