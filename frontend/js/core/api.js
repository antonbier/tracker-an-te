/**
 * core/api.js — Central HTTP client for the WanderSuite backend
 *
 * All backend requests go through api() so error handling is consistent.
 * The base URL is always read fresh from localStorage so it reflects
 * the latest saved Settings without requiring a page reload.
 */

import { API_URL } from './state.js';
import { t } from '../ui/i18n.js';

/**
 * Make a JSON request to the backend.
 * @param {string} path - API path, e.g. '/api/trackers'
 * @param {object} opts - fetch() options (method, body, headers override)
 * @returns {Promise<any>} Parsed JSON response
 * @throws {Error} If the backend URL is not set, or the response is not ok
 */
export async function api(path, opts = {}) {
  const base = localStorage.getItem('apiUrl') || API_URL || '';
  if (!base) throw new Error(t('missingUrl'));
  // Inject JWT if present
  const token = localStorage.getItem('ws-jwt');
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const r = await fetch(base + path, { ...opts, headers });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(err.detail || `HTTP ${r.status}`);
  }
  return r.json();
}

/**
 * Ping the backend /health endpoint and update the status dot in the header.
 * Called on startup, after saving Settings, and after onboarding.
 * Green = backend reachable, Red = unreachable or URL not set.
 */
export async function checkApiStatus() {
  const dot  = document.getElementById('statusDot');
  const base = localStorage.getItem('apiUrl') || '';
  if (!base) {
    dot.style.background = 'var(--red)';
    dot.style.boxShadow  = '0 0 6px var(--red)';
    dot.title = 'Backend URL nicht konfiguriert';
    return;
  }
  try {
    const r2 = await fetch(base + '/health', { signal: AbortSignal.timeout(5000) });
    if (!r2.ok) throw new Error(`HTTP ${r2.status}`);
    dot.style.background = 'var(--green)';
    dot.style.boxShadow  = '0 0 6px var(--green)';
    dot.title = 'Backend online';
  } catch(e) {
    dot.style.background = 'var(--red)';
    dot.style.boxShadow  = '0 0 6px var(--red)';
    dot.title = 'Backend nicht erreichbar: ' + e.message;
  }
}
