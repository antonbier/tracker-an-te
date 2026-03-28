/**
 * app/journal.js — Travel Journal powered by Dawarich
 *
 * Fetches automatically detected overnight trips from the backend
 * (/api/dawarich/trips). Trips are detected by the backend from GPS
 * points imported from Dawarich (Haversine distance > 50 km from home,
 * 2+ consecutive nights away).
 *
 * syncJournal() triggers a full Dawarich sync: fetches points, detects
 * trips, reverse-geocodes with Nominatim, and saves to the database.
 *
 * Note: openSettings() is imported dynamically to avoid a circular
 * dependency (journal.js → settings.js → ... → journal.js).
 *
 * Functions: loadJournalTrips, renderJournalTrips, syncJournal, deleteJournalTrip
 */
// frontend/js/app/journal.js
import { api } from '../core/api.js';
import { t } from '../ui/i18n.js';
import { toast } from '../ui/toast.js';
import { API_URL } from '../core/state.js';

export async function loadJournalTrips() {
  const el = document.getElementById('journal-trip-list');
  if (!API_URL) {
    el.innerHTML = `<div class="journal-empty"><div class="journal-empty-icon">⚙️</div><div class="journal-empty-text">${t('missingUrl')}</div></div>`;
    return;
  }
  try {
    const trips = await api('/api/dawarich/trips?limit=100');
    renderJournalTrips(trips);
    const subtitle = document.getElementById('journal-subtitle');
    if (subtitle) subtitle.textContent = trips.length > 0
      ? `${trips.length} ${trips.length === 1 ? 'Reise' : 'Reisen'} erkannt` : '';
  } catch(e) {
    el.innerHTML = `<div class="journal-empty"><div class="journal-empty-icon">⚠️</div><div class="journal-empty-text">${e.message}</div></div>`;
  }
}

export function renderJournalTrips(trips) {
  const el = document.getElementById('journal-trip-list');
  if (!trips.length) {
    el.innerHTML = `<div class="journal-empty"><div class="journal-empty-icon">🗺️</div><div class="journal-empty-text">${t('noJournalTrips')}</div></div>`;
    return;
  }
  el.innerHTML = trips.map(trip => {
    const loc      = [trip.location_name, trip.country].filter(Boolean).join(', ') || `${trip.lat},${trip.lon}`;
    const nights   = trip.nights;
    const nightsStr = `${nights} ${nights === 1 ? t('tripNights').slice(0,-1) : t('tripNights')}`;
    const mapsUrl  = `https://www.google.com/maps?q=${trip.lat},${trip.lon}`;
    return `<div class="journal-trip-card">
      <div class="journal-trip-pin">📍</div>
      <div class="journal-trip-body">
        <div class="journal-trip-name">${loc || '?'}</div>
        <div class="journal-trip-dates">${trip.start_date} → ${trip.end_date}</div>
        <span class="journal-trip-nights">${nightsStr}</span>
        <div class="journal-trip-actions">
          <a href="${mapsUrl}" target="_blank" class="btn-scrape" style="text-decoration:none;font-size:.68rem">🗺 Maps</a>
          <button class="btn-sm btn-danger" onclick="deleteJournalTrip(${trip.id})">✕</button>
        </div>
      </div>
    </div>`;
  }).join('');
}

export async function syncJournal() {
  const btn = document.getElementById('journal-sync-btn');
  if (!API_URL) { toast(t('missingUrl'), 'warning'); return; }
  let dawarichUrl   = localStorage.getItem('s-dawarichUrl')   || '';
  let dawarichToken = localStorage.getItem('s-dawarichToken') || '';
  let homeLat       = parseFloat(localStorage.getItem('s-homeLat') || '');
  let homeLon       = parseFloat(localStorage.getItem('s-homeLon') || '');
  // Koordinaten vom Server nachladen wenn localStorage leer oder ungültig
  if (!dawarichUrl || !dawarichToken || isNaN(homeLat) || isNaN(homeLon) || (homeLat===0 && homeLon===0)) {
    try {
      const ss = await api('/api/settings');
      if (!dawarichUrl)   dawarichUrl   = ss.dawarich_url   || '';
      if (!dawarichToken) dawarichToken = ss.dawarich_token || '';
      if (isNaN(homeLat)||homeLat===0) homeLat = parseFloat(ss.home_lat||'');
      if (isNaN(homeLon)||homeLon===0) homeLon = parseFloat(ss.home_lon||'');
    } catch(e) {}
  }
  if (!dawarichUrl || !dawarichToken) {
    toast(t('dawarichError') + ': URL/Token fehlen — Einstellungen öffnen', 'warning');
    const { openSettings } = await import('../ui/settings.js');
    openSettings(); return;
  }
  if (isNaN(homeLat)||isNaN(homeLon)||(homeLat===0&&homeLon===0)) {
    toast(t('dawarichError') + ': Home-Koordinaten fehlen — Einstellungen öffnen', 'warning');
    const { openSettings } = await import('../ui/settings.js');
    openSettings(); return;
  }
  if (btn) { btn.disabled=true; btn.innerHTML=`<span class="spinner"></span> ${t('dawarichSyncing')}`; }
  toast(t('dawarichSyncing'), 'warning');
  try {
    const result = await api('/api/dawarich/sync', {
      method: 'POST',
      body: JSON.stringify({ dawarich_url: dawarichUrl, dawarich_token: dawarichToken, home_lat: homeLat, home_lon: homeLon }),
    });
    const bar  = document.getElementById('journal-sync-bar');
    const info = document.getElementById('journal-sync-info');
    if (bar)  bar.style.display = 'flex';
    const saved = result.trips_saved ?? result.trips_detected ?? 0;
    if (info) info.innerHTML = `<strong>${result.points_loaded??0}</strong> Punkte geladen · <strong>${result.trips_detected??0}</strong> Reisen erkannt · <strong>${saved}</strong> gespeichert`;
    toast(`${t('dawarichSynced')}: ${result.trips_detected??0} Reisen`, 'success');
    loadJournalTrips();
    const { loadDashboard } = await import('./dashboard.js');
    loadDashboard();
  } catch(e) { toast(`${t('dawarichError')}: ${e.message}`, 'error'); }
  finally { if (btn) { btn.disabled=false; btn.innerHTML=`🧭 ${t('syncNow')}`; } }
}

export async function deleteJournalTrip(id) {
  if (!confirm(t('deleteConfirm'))) return;
  try {
    await api(`/api/dawarich/trips/${id}`, { method: 'DELETE' });
    toast(t('deleted'), 'success');
    loadJournalTrips();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}
