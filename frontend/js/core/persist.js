/**
 * core/persist.js — Bidirectional localStorage ↔ Backend sync
 *
 * Persists client-side data (ws-trips, ws-budget, ws-bucketlist) to the
 * backend via PUT /api/userdata/{key}. On app start, restores data from
 * the backend if localStorage is empty (e.g. new browser / cleared cache).
 *
 * Design:
 *   - localStorage remains the primary runtime store (fast, synchronous)
 *   - Backend is the durable backup (survives browser cache clears)
 *   - Sync is fire-and-forget (non-blocking, errors logged but not thrown)
 *   - On conflict: localStorage wins on the same device, backend wins on new device
 *
 * Keys synced:
 *   ws-trips      — manual travel trips (JSON array)
 *   ws-budget     — budget total in EUR (string)
 *   ws-bucketlist — bucket list items (JSON array)
 */

import { API_URL } from './state.js';

const SYNC_KEYS = ['ws-trips', 'ws-budget', 'ws-bucketlist'];

/**
 * Push a single key from localStorage to the backend.
 * Silent no-op if backend URL not configured or value is empty.
 * @param {string} key  e.g. 'ws-trips'
 */
export async function syncToBackend(key) {
  if (!API_URL) return;
  const value = localStorage.getItem(key);
  if (value === null) return;
  try {
    await fetch(`${API_URL}/api/userdata/${key}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value }),
    });
  } catch(e) {
    console.debug(`[persist] sync ${key} failed:`, e.message);
  }
}

/**
 * Push all tracked keys to the backend in parallel.
 * Called after any mutation of ws-trips, ws-budget, ws-bucketlist.
 */
export async function syncAllToBackend() {
  if (!API_URL) return;
  await Promise.allSettled(SYNC_KEYS.map(syncToBackend));
}

/**
 * On app start: fetch all user data from backend and restore to localStorage
 * only if localStorage is empty for that key (new browser / cleared cache).
 *
 * This is the "cold start" restore path.
 */
export async function restoreFromBackend() {
  if (!API_URL) return;
  try {
    const resp = await fetch(`${API_URL}/api/userdata`);
    if (!resp.ok) return;
    const data = await resp.json();
    let restored = [];
    for (const [key, value] of Object.entries(data)) {
      if (!localStorage.getItem(key) && value) {
        localStorage.setItem(key, value);
        restored.push(key);
      }
    }
    if (restored.length > 0) {
      console.info(`[persist] Restored from backend: ${restored.join(', ')}`);
    }
  } catch(e) {
    console.debug('[persist] restoreFromBackend failed:', e.message);
  }
}
