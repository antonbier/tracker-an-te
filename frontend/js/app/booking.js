// frontend/js/app/booking.js
import { t } from '../ui/i18n.js';
import { toast } from '../ui/toast.js';
import { API_URL } from '../core/state.js';

const base = () => localStorage.getItem('apiUrl') || API_URL;

export async function addBookingTracker() {
  const btn=document.getElementById('bk-addBtn'), dest=document.getElementById('bk-dest').value.trim(),
    checkin=document.getElementById('bk-checkin').value, checkout=document.getElementById('bk-checkout').value,
    adults=parseInt(document.getElementById('bk-adults').value), rooms=parseInt(document.getElementById('bk-rooms').value),
    source=document.getElementById('bk-source').value;
  if (!dest)               { toast(t('invalidDest'), 'error'); return; }
  if (!checkin||!checkout) { toast(t('missingDate'), 'error'); return; }
  if (!API_URL)            { toast(t('missingUrl'), 'warning'); return; }
  const serpKey = localStorage.getItem('s-serpApiKey')||'';
  if (!serpKey) { document.getElementById('bk-serpapi-notice').style.display='block'; toast(t('serpApiMissingBooking'),'warning'); return; }
  document.getElementById('bk-serpapi-notice').style.display='none';
  btn.disabled=true; btn.innerHTML=`<span class="spinner"></span> ${t('creatingTracker')}`;
  try {
    const r = await fetch(base()+'/api/accommodations/booking', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({destination:dest, checkin_date:checkin, checkout_date:checkout, adults, rooms, source}),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast(t('bookingTrackerAdded'), 'success');
    document.getElementById('bk-dest').value=''; loadBookingTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
  finally { btn.disabled=false; btn.innerHTML=`+ ${t('startTracker')}`; }
}

export async function loadBookingTrackers() {
  if (!API_URL) return;
  try { renderBookingTrackers(await (await fetch(base()+'/api/accommodations/booking')).json()); } catch(e) {}
}

export function renderBookingTrackers(trackers) {
  const el=document.getElementById('bk-trackerList'); if (!el) return;
  if (!trackers.length) { el.innerHTML=`<div style="color:var(--muted);font-size:.78rem;padding:.4rem 0">${t('bookingNoTrackers')}</div>`; return; }
  el.innerHTML = trackers.map(tr => {
    const snap=tr.latest_snapshot, price=snap?.total_price?`${snap.total_price.toFixed(2)} €/Nacht`:'–', hotel=snap?.hotel_name?` — ${snap.hotel_name}`:'';
    return `<div class="tracker-item">
      <div class="tracker-header"><div class="tracker-route">🏨 ${tr.destination}</div><div class="tracker-price ${snap?'':'stale'}">${price}</div></div>
      <div class="tracker-meta">
        <span>${tr.checkin_date} → ${tr.checkout_date}</span><span>${tr.adults} ${t('adultShort')}, ${tr.rooms} Zi.</span>
        <span class="badge badge-ok">${tr.source}</span>${hotel?`<span style="font-style:italic">${hotel}</span>`:''}
      </div>
      <div class="tracker-actions">
        <button class="btn-scrape" onclick="scrapeBookingTracker(${tr.id})">⟳ ${t('current')}</button>
        <button class="btn-sm btn-danger" onclick="deleteBookingTracker(${tr.id})">✕</button>
      </div></div>`;
  }).join('');
}

export async function scrapeBookingTracker(id) {
  const key=encodeURIComponent(localStorage.getItem('s-serpApiKey')||'');
  toast(t('bookingSearching'), 'warning');
  try {
    const data=await (await fetch(`${base()}/api/accommodations/booking/${id}/scrape?api_key=${key}`, {method:'POST'})).json();
    const snap=data.snapshot;
    if (snap?.total_price) toast(`${t('current')}: ${snap.total_price.toFixed(2)} €/Nacht${snap.hotel_name?' — '+snap.hotel_name:''}`, 'success');
    else toast(`Status: ${snap?.status} — ${snap?.error_message||''}`, 'warning');
    loadBookingTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

export async function deleteBookingTracker(id) {
  if (!confirm(t('deleteConfirm'))) return;
  try { await fetch(`${base()}/api/accommodations/booking/${id}`, {method:'DELETE'}); toast(t('deleted'),'success'); loadBookingTrackers(); }
  catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}
