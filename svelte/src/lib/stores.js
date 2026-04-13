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
export const lang           = persisted('lang', 'de');
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
export const currentPage = writable('home');
export const trips      = writable([]);
export const budget     = writable(null);
export const bucketlist = writable([]);
export const appVersion = writable('');

// WanderWizzard: Suchparameter-Store (wird von WanderWizzard gesetzt, von PriceRadar gelesen)
export const priceradarParams = writable(null);


// WanderWizzard Trip Hub — active trip ID for navigation
export const activeWsTripId = writable(null);

// Global settings modal trigger — set to true from anywhere to open Settings
export const settingsOpen = writable(false);

export const isDark       = derived(theme,       ($t) => $t === 'dark');
export const isConfigured = derived(apiUrl,      ($u) => $u.length > 0);
export const isAdmin      = derived(currentUser, ($u) => $u?.role === 'admin');

export function logout() {
  jwtToken.set('');
  currentUser.set(null);
  appStatus.set(null);
}

export async function loadSettingsFromBackend(baseUrl) {
  // Guard: never fetch without a real URL
  if (!browser || !baseUrl || baseUrl.trim() === '') return;
  try {
    const res = await fetch(`${baseUrl.replace(/\/$/, '')}/api/settings`);
    if (!res.ok) return;
    const s = await res.json();
    const map = {
      'dawarich_url':      's-dawarichUrl',
      'actual_url':        's-actualUrl',
      'actual_file':       's-actualFile',
      'home_lat':          's-homeLat',
      'home_lon':          's-homeLon',
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

