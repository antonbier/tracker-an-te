/**
 * sw.js — WanderSuite Service Worker
 *
 * Strategy: Network-first with cache fallback for static assets.
 *
 * - On install: pre-caches the app shell (HTML, JS modules, fonts, Chart.js)
 * - On fetch:   tries network first; falls back to cache on failure
 * - On activate: cleans up old cache versions
 *
 * This gives the app PWA installability and basic offline resilience.
 * API calls (/api/*) are always network-only — no stale data.
 */

const CACHE_NAME  = 'wandersuite-v1';
const CACHE_SHELL = [
  '/',
  '/index.html',
  '/js/main.js',
  '/js/core/state.js',
  '/js/core/api.js',
  '/js/ui/i18n.js',
  '/js/ui/nav.js',
  '/js/ui/toast.js',
  '/js/ui/settings.js',
  '/js/ui/priceradar.js',
  '/js/ui/tabs.js',
  '/js/ui/fieldguide.js',
  '/js/app/ryanair.js',
  '/js/app/budget.js',
  '/js/app/dashboard.js',
  '/js/app/googleflights.js',
  '/js/app/homair.js',
  '/js/app/booking.js',
  '/js/app/journal.js',
  '/js/app/onboarding.js',
  '/js/app/bucketlist.js',
  '/locales/de.json',
  '/locales/en.json',
  '/locales/it.json',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

// ── Install: pre-cache app shell ──────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      // Use individual adds so a single 404 doesn't block the whole install
      return Promise.allSettled(CACHE_SHELL.map(url => cache.add(url).catch(() => {})));
    }).then(() => self.skipWaiting())
  );
});

// ── Activate: clean up old caches ─────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// ── Fetch: network-first, cache fallback ──────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // API calls and external resources: always network-only, no caching
  if (url.pathname.startsWith('/api/') ||
      url.hostname !== self.location.hostname) {
    return; // let the browser handle it normally
  }

  event.respondWith(
    fetch(request)
      .then(response => {
        // Cache successful GET responses for static assets
        if (response.ok && request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => caches.match(request)) // fallback to cache on network failure
  );
});
