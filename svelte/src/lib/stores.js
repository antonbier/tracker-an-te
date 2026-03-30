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

// ── Core ─────────────────────────────────────────────────────────────
export const apiUrl         = persisted('apiUrl', '');
export const lang           = persisted('lang', 'de');
export const theme          = persisted('theme', '');
export const onboardingDone = persisted('ws-onboarding-done', '');

// ── Auth ─────────────────────────────────────────────────────────────
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

export const appStatus = writable(null);

// ── Navigation ────────────────────────────────────────────────────────
export const currentPage = writable('home');

// ── User data ─────────────────────────────────────────────────────────
export const trips      = writable([]);
export const budget     = writable(null);
export const bucketlist = writable([]);

// ── App version (from backend /health) ───────────────────────────────
export const appVersion = writable('');

// ── Derived ───────────────────────────────────────────────────────────
export const isDark       = derived(theme,       ($t) => $t === 'dark');
export const isConfigured = derived(apiUrl,      ($u) => $u.length > 0);
export const isAdmin      = derived(currentUser, ($u) => $u?.role === 'admin');

// ── Logout ────────────────────────────────────────────────────────────
export function logout() {
  jwtToken.set('');
  currentUser.set(null);
  appStatus.set(null);
}

/**
 * loadSettingsFromBackend — called once after onboarding/startup.
 * Pulls non-secret settings (urls, coords, language) from backend
 * and writes them to localStorage as fallback for offline use.
 * Secret keys (tokens, passwords) stay encrypted in DB only.
 */
export async function loadSettingsFromBackend(baseUrl) {
  if (!browser || !baseUrl) return;
  try {
    const res = await fetch(`${baseUrl.replace(/\/$/, '')}/api/settings`);
    if (!res.ok) return;
    const s = await res.json();
    // Non-secret fields — safe to cache in localStorage
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
    // Language sync
    if (s.language && s.language !== localStorage.getItem('lang')) {
      lang.set(s.language);
    }
    // Version
    const health = await fetch(`${baseUrl.replace(/\/$/, '')}/health`);
    if (health.ok) {
      const h = await health.json();
      if (h.version) appVersion.set(h.version);
    }
  } catch { /* offline */ }
}
