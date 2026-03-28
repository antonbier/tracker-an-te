// frontend/js/app/googleflights.js
import { t } from '../ui/i18n.js';
import { toast } from '../ui/toast.js';
import { API_URL } from '../core/state.js';

const base = () => localStorage.getItem('apiUrl') || API_URL;

export async function addGFTracker() {
  const btn     = document.getElementById('gf-addBtn');
  const origin  = document.getElementById('gf-origin').value.trim().toUpperCase();
  const dest    = document.getElementById('gf-dest').value.trim().toUpperCase();
  const outDate = document.getElementById('gf-date').value;
  const retDate = document.getElementById('gf-return')?.value || '';
  const pax     = parseInt(document.getElementById('gf-pax').value);
  if (!origin || origin.length !== 3) { toast(t('invalidOrigin'), 'error'); return; }
  if (!dest   || dest.length   !== 3) { toast(t('invalidDest'),   'error'); return; }
  if (!outDate)                        { toast(t('missingDate'),   'error'); return; }
  if (!API_URL)                        { toast(t('missingUrl'), 'warning'); return; }
  const serpKey = localStorage.getItem('s-serpApiKey') || '';
  if (!serpKey) { document.getElementById('gf-serpapi-notice').style.display='block'; toast(t('serpApiMissing'),'warning'); return; }
  document.getElementById('gf-serpapi-notice').style.display = 'none';
  btn.disabled = true; btn.innerHTML = `<span class="spinner"></span> ${t('creatingTracker')}`;
  try {
    const r = await fetch(base() + '/api/google-flights', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin, destination: dest, outbound_date: outDate, return_date: retDate||null,
        adults: pax, children: parseInt(document.getElementById('gf-children')?.value||0) }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast(`${t('gfTrackerAdded')} ✓ ${origin} → ${dest}`, 'success');
    document.getElementById('gf-origin').value = ''; document.getElementById('gf-dest').value = '';
    loadGFTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
  finally { btn.disabled=false; btn.innerHTML=`+ ${t('startTracker')}`; }
}

export async function loadGFTrackers() {
  if (!API_URL) return;
  try { renderGFTrackers(await (await fetch(base()+'/api/google-flights')).json()); } catch(e) {}
}

export function renderGFTrackers(trackers) {
  const el = document.getElementById('gf-trackerList');
  if (!el) return;
  if (!trackers.length) { el.innerHTML=`<div style="color:var(--muted);font-size:.78rem;padding:.4rem 0">${t('gfNoTrackers')}</div>`; return; }
  el.innerHTML = trackers.map(tr => {
    const snap = tr.latest_snapshot;
    const price = snap?.total_price ? `${snap.total_price.toFixed(2)} €` : '–';
    const airline = snap?.airline ? `✈ ${snap.airline}${snap.outbound_flight?' '+snap.outbound_flight:''}` : '';
    const times   = snap?.departure_time && snap?.arrival_time ? `🕐 ${snap.departure_time} → ${snap.arrival_time}${snap.duration_min?` (${Math.floor(snap.duration_min/60)}h ${snap.duration_min%60}m)`:''}` : '';
    return `<div class="tracker-item">
      <div class="tracker-header"><div class="tracker-route">${tr.origin} → ${tr.destination}</div><div class="tracker-price ${snap?'':'stale'}">${price}</div></div>
      <div class="tracker-meta">
        <span>${tr.outbound_date}${tr.return_date?' ⇄ '+tr.return_date:' ('+t('oneWay')+')'}</span>
        <span>${tr.adults} ${t('adultShort')}${tr.children>0?' · '+tr.children+' Kind':''}</span>
        ${airline?`<span>${airline}</span>`:''}${times?`<span>${times}</span>`:''}
        <span class="badge badge-ok">Google Flights</span>
      </div>
      <div class="tracker-actions">
        <button class="btn-scrape" onclick="scrapeGFTracker(${tr.id})">⟳ ${t('current')}</button>
        <button class="btn-sm btn-danger" onclick="deleteGFTracker(${tr.id})">✕</button>
      </div></div>`;
  }).join('');
}

export async function scrapeGFTracker(id) {
  const key = encodeURIComponent(localStorage.getItem('s-serpApiKey')||'');
  toast(t('gfSearching'), 'warning');
  try {
    const data = await (await fetch(`${base()}/api/google-flights/${id}/scrape?api_key=${key}`, {method:'POST'})).json();
    const snap = data.snapshot;
    if (snap?.total_price) toast(`${t('current')}: ${snap.total_price.toFixed(2)} €`, 'success');
    else toast(`Status: ${snap?.status}`, 'warning');
    loadGFTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

export async function deleteGFTracker(id) {
  if (!confirm(t('deleteConfirm'))) return;
  try { await fetch(`${base()}/api/google-flights/${id}`, {method:'DELETE'}); toast(t('deleted'),'success'); loadGFTrackers(); }
  catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}
