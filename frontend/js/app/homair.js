// frontend/js/app/homair.js
import { t } from '../ui/i18n.js';
import { toast } from '../ui/toast.js';
import { API_URL } from '../core/state.js';

const base = () => localStorage.getItem('apiUrl') || API_URL;

export async function addHomairTracker() {
  const btn=document.getElementById('hm-addBtn'), region=document.getElementById('hm-region').value,
    accType=document.getElementById('hm-type').value, checkin=document.getElementById('hm-checkin').value,
    checkout=document.getElementById('hm-checkout').value, adults=parseInt(document.getElementById('hm-adults').value),
    children=parseInt(document.getElementById('hm-children').value);
  if (!checkin||!checkout) { toast(t('missingDate'),'error'); return; }
  if (!API_URL)             { toast(t('missingUrl'),'warning'); return; }
  btn.disabled=true; btn.innerHTML=`<span class="spinner"></span> ${t('creatingTracker')}`;
  try {
    const r = await fetch(base()+'/api/accommodations/homair', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({region, accommodation_type:accType, checkin_date:checkin, checkout_date:checkout, adults, children}),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast(t('homairTrackerAdded'), 'success'); loadHomairTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
  finally { btn.disabled=false; btn.innerHTML=`+ ${t('startTracker')}`; }
}

export async function loadHomairTrackers() {
  if (!API_URL) return;
  try { renderHomairTrackers(await (await fetch(base()+'/api/accommodations/homair')).json()); } catch(e) {}
}

export function renderHomairTrackers(trackers) {
  const el = document.getElementById('hm-trackerList'); if (!el) return;
  if (!trackers.length) { el.innerHTML=`<div style="color:var(--muted);font-size:.78rem;padding:.4rem 0">${t('homairNoTrackers')}</div>`; return; }
  el.innerHTML = trackers.map(tr => {
    const snap=tr.latest_snapshot, price=snap?.total_price?`${snap.total_price.toFixed(2)} €`:'–';
    return `<div class="tracker-item">
      <div class="tracker-header"><div class="tracker-route">⛺ ${tr.region}</div><div class="tracker-price ${snap?'':'stale'}">${price}</div></div>
      <div class="tracker-meta"><span>${tr.checkin_date} → ${tr.checkout_date}</span><span>${tr.accommodation_type}</span><span>${tr.adults} ${t('adultShort')}</span></div>
      <div class="tracker-actions">
        <button class="btn-scrape" onclick="scrapeHomairTracker(${tr.id})">⟳ ${t('current')}</button>
        <button class="btn-sm btn-danger" onclick="deleteHomairTracker(${tr.id})">✕</button>
      </div></div>`;
  }).join('');
}

export async function scrapeHomairTracker(id) {
  toast(t('homairSearching'), 'warning');
  try {
    const data = await (await fetch(`${base()}/api/accommodations/homair/${id}/scrape`, {method:'POST'})).json();
    const snap = data.snapshot;
    if (snap?.total_price) toast(`${t('current')}: ${snap.total_price.toFixed(2)} €/Nacht`, 'success');
    else toast(`Status: ${snap?.status} — ${snap?.error_message||''}`, 'warning');
    loadHomairTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

export async function deleteHomairTracker(id) {
  if (!confirm(t('deleteConfirm'))) return;
  try { await fetch(`${base()}/api/accommodations/homair/${id}`, {method:'DELETE'}); toast(t('deleted'),'success'); loadHomairTrackers(); }
  catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}
