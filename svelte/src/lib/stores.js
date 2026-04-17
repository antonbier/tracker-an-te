import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

function persisted(key, defaultValue) {
  const initial = browser ? (localStorage.getItem(key) ?? defaultValue) : defaultValue;
  const store = writable(initial);
  if (browser) {
    store.subscribe((val) => {
      if (val === null || val === undefined) localStorage.removeItem(key);
      else localStorage.setItem(key, val);
    });
  }
  return store;
}

export const apiUrl         = persisted('apiUrl', '');
// Sprache: localStorage → Browser-Sprache → 'en' als Fallback
function getInitialLang() {
  if (typeof localStorage === 'undefined') return 'en';
  const stored = localStorage.getItem('ws-lang') || localStorage.getItem('lang');
  const supported = ['de', 'en', 'it', 'es'];
  if (stored && supported.includes(stored)) return stored;
  // Browser-Sprache auslesen
  if (typeof navigator !== 'undefined' && navigator.language) {
    const browserLang = navigator.language.split('-')[0];
    if (supported.includes(browserLang)) return browserLang;
  }
  return 'en';
}
export const lang = (() => {
  const initial = typeof window !== 'undefined' ? getInitialLang() : 'en';
  const store = writable(initial);
  if (typeof window !== 'undefined') {
    store.subscribe((val) => {
      if (val) {
        localStorage.setItem('ws-lang', val);
        localStorage.setItem('lang', val);
      }
    });
  }
  return store;
})();
export const theme          = persisted('theme', '');
export const onboardingDone = persisted('ws-onboarding-done', '');

export const jwtToken    = persisted('ws-jwt', '');
export const currentUser = writable(
  browser ? JSON.parse(localStorage.getItem('ws-current-user') || 'null') : null
);
if (browser) {
  currentUser.subscribe((val) => {
    if (val) localStorage.setItem('ws-current-user', JSON.stringify(val));
    else localStorage.removeItem('ws-current-user');
  });
}

export const appStatus  = writable(null);
export const currentPage  = writable('home');
export const previousPage    = writable('home');
export const activeMyTripsTab = writable('overview');
export const trips      = writable([]);
export const budget     = writable(null);
export const bucketlist = writable([]);
export const appVersion = writable('');

// WanderWizzard: Suchparameter-Store
export const priceradarParams = writable(null);

// WanderWizzard Trip Hub — active trip ID for navigation
export const activeWsTripId = writable(null);

// Global settings modal trigger
export const settingsOpen = writable(false);

// Setup Wizard trigger — set to true from anywhere to open the 5-step wizard
export const wizardOpen = writable(false);

export const isDark       = derived(theme,       ($t) => $t === 'dark');
export const isConfigured = derived(apiUrl,      ($u) => $u.length > 0);
export const isAdmin      = derived(currentUser, ($u) => $u?.role === 'admin');

export function logout() {
  jwtToken.set('');
  currentUser.set(null);
  appStatus.set(null);
}

export async function loadSettingsFromBackend(baseUrl) {
  if (!browser || !baseUrl || baseUrl.trim() === '') return;
  try {
    const token = localStorage.getItem('ws-jwt') || '';
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    const res = await fetch(`${baseUrl.replace(/\/$/, '')}/api/settings`, { headers });
    if (!res.ok) return;
    const s = await res.json();
    const map = {
      'dawarich_url':      's-dawarichUrl',
      'actual_url':        's-actualUrl',
      'actual_file':       's-actualFile',
      'home_lat':          's-homeLat',
      'home_lon':          's-homeLon',
      'home_name':         's-homeName',
      'travel_categories': 's-travelCategories',
    };
    for (const [dbKey, lsKey] of Object.entries(map)) {
      if (s[dbKey]) localStorage.setItem(lsKey, s[dbKey]);
    }
    if (s.language && s.language !== localStorage.getItem('lang')) {
      lang.set(s.language);
    }
    const health = await fetch(`${baseUrl.replace(/\/$/, '')}/health`);
    if (health.ok) {
      const h = await health.json();
      if (h.version) appVersion.set(h.version);
    }
  } catch { /* offline — fail silently */ }
}
