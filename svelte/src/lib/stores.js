import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

// ── Persistence helper ───────────────────────────────────────────────
function persisted(key, defaultValue) {
  const initial = browser
    ? (localStorage.getItem(key) ?? defaultValue)
    : defaultValue;
  const store = writable(initial);
  if (browser) {
    store.subscribe((val) => {
      if (val === null || val === undefined) {
        localStorage.removeItem(key);
      } else {
        localStorage.setItem(key, val);
      }
    });
  }
  return store;
}

// ── Core stores ──────────────────────────────────────────────────────
export const apiUrl      = persisted('apiUrl', '');
export const lang        = persisted('lang', 'de');
export const theme       = persisted('theme', '');          // '' = light, 'dark' = dark
export const onboardingDone = persisted('ws-onboarding-done', '');

// ── Auth stores (JWT — prepared for auth-foundation branch) ──────────
export const jwtToken    = persisted('ws-jwt', '');
export const currentUser = writable(
  browser ? JSON.parse(localStorage.getItem('ws-current-user') || 'null') : null
);

// ── Navigation ───────────────────────────────────────────────────────
export const currentPage = writable('home');  // 'home' | 'priceradar' | 'mytrips' | 'discover'

// ── User data (backend-synced) ────────────────────────────────────────
export const trips      = writable([]);
export const budget     = writable(null);
export const bucketlist = writable([]);

// ── Derived ──────────────────────────────────────────────────────────
export const isDark = derived(theme, ($t) => $t === 'dark');
export const isConfigured = derived(apiUrl, ($url) => $url.length > 0);
