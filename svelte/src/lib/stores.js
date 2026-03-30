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
// Sync currentUser to localStorage whenever it changes
if (browser) {
  currentUser.subscribe((val) => {
    if (val) localStorage.setItem('ws-current-user', JSON.stringify(val));
    else localStorage.removeItem('ws-current-user');
  });
}

// appStatus: result of GET /api/status — drives login/setup gate
// { auth_enabled: bool, needs_setup: bool } | null
export const appStatus = writable(null);

// ── Navigation ────────────────────────────────────────────────────────
export const currentPage = writable('home');

// ── User data ─────────────────────────────────────────────────────────
export const trips      = writable([]);
export const budget     = writable(null);
export const bucketlist = writable([]);

// ── Derived ───────────────────────────────────────────────────────────
export const isDark       = derived(theme,   ($t)   => $t === 'dark');
export const isConfigured = derived(apiUrl,  ($url) => $url.length > 0);
export const isAdmin      = derived(currentUser, ($u) => $u?.role === 'admin');

// ── Logout helper ─────────────────────────────────────────────────────
export function logout() {
  jwtToken.set('');
  currentUser.set(null);
  appStatus.set(null);
}
