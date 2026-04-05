import { get } from 'svelte/store';
import { apiUrl, jwtToken } from './stores.js';

/**
 * Core HTTP client.
 * 
 * Smart URL resolution:
 * - If apiUrl is empty OR points to the same origin as the frontend
 *   → use relative path (e.g. "/api/trips") so Nginx proxies it.
 * - If apiUrl points to a different host/port
 *   → use the full URL directly (dev / external backend).
 *
 * This fixes "failed to fetch" when the backend port is not externally
 * exposed and all traffic must go through Nginx on port 80/443.
 */
function resolveBase() {
  const stored = get(apiUrl).replace(/\/$/, '');
  if (!stored) return '';
  try {
    const u = new URL(stored);
    // Same host and same port as frontend → use relative path (Nginx proxy)
    if (u.hostname === window.location.hostname &&
        u.port     === window.location.port) {
      return '';
    }
    // Different host/port → use stored URL directly
    return stored;
  } catch {
    // Not a valid absolute URL → treat as relative base
    return stored.startsWith('/') ? stored : '';
  }
}

export async function api(path, options = {}) {
  const base  = resolveBase();
  const token = get(jwtToken);

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${base}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    // Try to parse structured error detail (e.g. missing_api_key from FastAPI)
    try {
      const errBody = await res.json();
      const err = new Error(errBody?.detail?.message || errBody?.detail || res.statusText);
      err.status = res.status;
      err.detail = errBody?.detail;
      throw err;
    } catch (parseErr) {
      if (parseErr.status) throw parseErr; // re-throw structured error
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`API ${path} → ${res.status}: ${text}`);
    }
  }

  if (res.status === 204) return null;

  return res.json();
}

/** Check backend reachability (used by Onboarding) */
export async function checkApiStatus(url) {
  try {
    const res = await fetch(`${url.replace(/\/$/, '')}/health`, {
      signal: AbortSignal.timeout(5000),
    });
    return res.ok;
  } catch {
    return false;
  }
}
