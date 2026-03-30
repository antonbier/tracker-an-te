import { get } from 'svelte/store';
import { apiUrl, jwtToken } from './stores.js';

/**
 * Core HTTP client — mirrors the old core/api.js pattern.
 * Automatically injects JWT if available.
 */
export async function api(path, options = {}) {
  const base = get(apiUrl).replace(/\/$/, '');
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
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }

  // 204 No Content
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
