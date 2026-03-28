/**
 * app/bucketlist.js — Bucket List / Wunschziele
 *
 * A fully client-side wishlist for travel destinations.
 * No backend required — data is stored in localStorage under 'ws-bucketlist'.
 *
 * Data structure per item:
 *   { id: timestamp, dest: string, when: string, emoji: string, added: date }
 *
 * Emojis are chosen randomly from a curated travel set on item creation.
 *
 * updateMyTripsStats() is called whenever the bucket list changes, and also
 * when the Meine Reisen overview tab opens — it updates the 3 stat counters.
 *
 * Functions: addBucketListItem, renderBucketList, deleteBucketListItem, updateMyTripsStats
 */
// frontend/js/app/bucketlist.js
// Bucket List (Wunschziele) — localStorage-backed, no backend needed

const STORAGE_KEY = 'ws-bucketlist';
const EMOJIS = ['🌍','🏝️','🏔️','🏛️','🌋','🏜️','🗼','🏯','🌊','🗺️','✈️','🌴'];

function load() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
  catch { return []; }
}

function save(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  // Fire-and-forget sync to backend
  import('../core/persist.js').then(m => m.syncToBackend(STORAGE_KEY));
}

export function addBucketListItem() {
  const dest = document.getElementById('bl-destination')?.value.trim();
  const when = document.getElementById('bl-when')?.value.trim();
  if (!dest) {
    const input = document.getElementById('bl-destination');
    if (input) { input.focus(); input.style.borderColor = 'var(--red)'; setTimeout(() => input.style.borderColor = '', 1500); }
    return;
  }
  const items = load();
  items.push({
    id:    Date.now(),
    dest,
    when:  when || '',
    emoji: EMOJIS[Math.floor(Math.random() * EMOJIS.length)],
    added: new Date().toISOString().slice(0,10),
  });
  save(items);
  document.getElementById('bl-destination').value = '';
  document.getElementById('bl-when').value = '';
  renderBucketList();
  updateMyTripsStats();
}

export function deleteBucketListItem(id) {
  save(load().filter(i => i.id !== id));
  renderBucketList();
  updateMyTripsStats();
}

export function renderBucketList() {
  const grid = document.getElementById('bucketListGrid');
  if (!grid) return;
  const items = load();
  if (!items.length) {
    grid.innerHTML = '<div class="bucket-empty">Noch keine Wunschziele — füge dein erstes hinzu! 🗺️</div>';
    return;
  }
  grid.innerHTML = items.map(item => `
    <div class="bucket-card">
      <button class="bucket-card-delete" onclick="deleteBucketListItem(${item.id})" title="Entfernen">✕</button>
      <div class="bucket-card-emoji">${item.emoji}</div>
      <div class="bucket-card-dest">${item.dest}</div>
      ${item.when ? `<div class="bucket-card-when">📅 ${item.when}</div>` : ''}
    </div>`).join('');
}

export function updateMyTripsStats() {
  // Wishlist count
  const wishEl = document.getElementById('mytrips-stat-wishlist');
  if (wishEl) wishEl.textContent = load().length;

  // Budget remaining
  const budgetEl = document.getElementById('mytrips-stat-budget');
  if (budgetEl) {
    const total   = parseFloat(localStorage.getItem('ws-budget') || '0');
    const trips   = JSON.parse(localStorage.getItem('ws-trips') || '[]');
    const spent   = trips.reduce((s, t) => s + t.cost, 0);
    const remain  = Math.max(0, total - spent);
    budgetEl.textContent = total > 0 ? remain.toFixed(0) + ' €' : '–';
  }

  // Visited places (from Dawarich trips in localStorage fallback)
  const placesEl = document.getElementById('mytrips-stat-places');
  if (placesEl) {
    const trips = JSON.parse(localStorage.getItem('ws-trips') || '[]');
    placesEl.textContent = trips.length || '–';
  }
}
