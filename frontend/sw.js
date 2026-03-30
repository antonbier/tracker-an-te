// Build: 2026-03-30 11:26 UTC
/**
 * sw.js — WanderSuite Service Worker
 *
 * Strategy: Network-first with cache fallback for static assets.
 * API calls (/api/*) are always network-only.
 *
 * Cache version: increment CACHE_VER to force re-install on deploy.
 */

const CACHE_VER  = 'v6';
const CACHE_NAME = 'wandersuite-' + CACHE_VER;

const CACHE_SHELL = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/locales/de.json',
  '/locales/en.json',
  '/locales/it.json',
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
];

// ── Install: pre-cache app shell ──────────────────────────────────────────────
self.addEventListener('install', event => {
  console.log('[SW] Installing cache:', CACHE_NAME);
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => Promise.allSettled(
        CACHE_SHELL.map(url => cache.add(url).catch(e => console.warn('[SW] Cache miss:', url, e)))
      ))
      .then(() => {
        console.log('[SW] App shell cached');
        self.skipWaiting();
      })
  );
});

// ── Activate: clean up old caches ─────────────────────────────────────────────
self.addEventListener('activate', event => {
  console.log('[SW] Activating, cleaning old caches');
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => {
          console.log('[SW] Deleting old cache:', k);
          return caches.delete(k);
        })
      ))
      .then(() => self.clients.claim())
  );
});

// ── Fetch: network-first, cache fallback ──────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip: non-GET, cross-origin, API calls, Chrome extensions
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/')) return;
  if (url.pathname.startsWith('/health')) return;
  if (url.pathname.startsWith('/docs')) return;

  event.respondWith(
    fetch(request)
      .then(response => {
        // Cache successful responses for static assets
        if (response.ok && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        // Network failed — try cache
        return caches.match(request).then(cached => {
          if (cached) return cached;
          // Last resort for navigation: return cached index.html
          if (request.mode === 'navigate') {
            return caches.match('/index.html');
          }
          return new Response('Offline', { status: 503 });
        });
      })
  );
});
