// frontend/js/app/dashboard.js
import { api } from '../core/api.js';
import { t } from '../ui/i18n.js';
import { API_URL } from '../core/state.js';

export function loadDashboard() {
  loadDashTrackers();
  loadDashBudget();
  loadDashTrips();
}

export async function loadDashTrackers() {
  const el      = document.getElementById('dash-tracker-list');
  const countEl = document.getElementById('dash-tracker-count');
  if (!API_URL) { if (countEl) countEl.textContent = '0'; return; }
  try {
    const trackers = await api('/api/trackers');
    const active   = trackers.filter(t => t.active);
    if (countEl) countEl.textContent = active.length;
    if (!active.length) { el.innerHTML = `<div style="color:var(--sub);font-size:.8rem">${t('noTrackersYet')}</div>`; return; }
    el.innerHTML = active.map(tr => {
      const snap  = tr.latest_snapshot;
      const price = snap?.total_price ? snap.total_price.toFixed(2) + ' €' : '–';
      const date  = snap?.fetched_at  ? snap.fetched_at.slice(0,10) : '';
      return `<div class="dash-tracker-card" onclick="navigate('ryanair');setTimeout(()=>selectTracker(${tr.id}),200)">
        <div>
          <div class="dash-tracker-route">${tr.origin} → ${tr.destination}</div>
          <div class="dash-tracker-meta">${tr.outbound_date}${tr.return_date?' ⇄ '+tr.return_date:''} · ${date?t('lastChecked')+': '+date:''}</div>
        </div>
        <div class="dash-tracker-price">${price}</div>
      </div>`;
    }).join('');
  } catch(e) { if (el) el.innerHTML = `<div style="color:var(--sub);font-size:.78rem">⚠ ${e.message}</div>`; }
}

export function loadDashBudget() {
  const total       = parseFloat(localStorage.getItem('ws-budget') || '0');
  const tripsList   = JSON.parse(localStorage.getItem('ws-trips') || '[]');
  const spent       = tripsList.reduce((s, tr) => s + tr.cost, 0);
  const remaining   = Math.max(0, total - spent);
  const pct         = total > 0 ? Math.min(100, (spent / total) * 100) : 0;
  const circumference = 2 * Math.PI * 38;
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  set('dash-budget-total',       total > 0 ? total.toFixed(0) + ' €' : '–');
  set('dash-budget-remaining',   total > 0 ? remaining.toFixed(0) + ' €' : '–');
  set('dash-budget-pct',         total > 0 ? Math.round(pct) + '% ' + t('spent').toLowerCase() : '–');
  set('dash-budget-spent-label', spent > 0 ? spent.toFixed(2) + ' € ' + t('spent').toLowerCase() : '–');
  set('dash-spent',     spent.toFixed(2) + ' €');
  set('dash-remaining', remaining.toFixed(2) + ' €');
  set('dash-total-budget', total.toFixed(2) + ' €');
  const fill = document.getElementById('dash-donut-fill');
  if (fill) {
    const da = (pct / 100) * circumference;
    fill.setAttribute('stroke-dasharray', `${da} ${circumference - da}`);
    fill.setAttribute('stroke', pct > 85 ? 'var(--red)' : pct > 60 ? 'var(--accent2)' : 'var(--accent)');
  }
}

export function loadDashTrips() {
  const tripsList = JSON.parse(localStorage.getItem('ws-trips') || '[]');
  const today     = new Date().toISOString().slice(0,10);
  const upcoming  = tripsList.filter(tr => tr.date >= today);
  const completed = tripsList.filter(tr => tr.date <  today);
  const upEl = document.getElementById('dash-upcoming-list');
  const coEl = document.getElementById('dash-completed-list');
  if (upEl) {
    upEl.innerHTML = upcoming.length
      ? upcoming.map(tr => `<div class="trip-card">
          <div class="trip-card-icon">✈️</div>
          <div class="trip-card-info"><div class="trip-card-name">${tr.name}</div><div class="trip-card-date">${tr.date}</div></div>
          <div class="trip-card-cost">${tr.cost.toFixed(2)} €</div>
        </div>`).join('')
      : `<div style="color:var(--sub);font-size:.8rem">${t('noUpcomingTrips')}</div>`;
  }
  if (coEl) {
    if (API_URL) {
      api('/api/dawarich/trips?limit=5').then(trips => {
        if (trips && trips.length) {
          coEl.innerHTML = trips.map(tr => {
            const loc = [tr.location_name, tr.country].filter(Boolean).join(', ') || `${tr.lat},${tr.lon}`;
            return `<div class="trip-card" style="cursor:pointer" onclick="navigate('journal')">
              <div class="trip-card-icon">✅</div>
              <div class="trip-card-info"><div class="trip-card-name">${loc}</div><div class="trip-card-date">${tr.start_date} · ${tr.nights} ${t('tripNights')}</div></div>
            </div>`;
          }).join('');
        } else if (completed.length) {
          coEl.innerHTML = completed.map(tr => `<div class="trip-card" style="opacity:.7">
            <div class="trip-card-icon">✅</div>
            <div class="trip-card-info"><div class="trip-card-name">${tr.name}</div><div class="trip-card-date">${tr.date}</div></div>
            <div class="trip-card-cost">${tr.cost.toFixed(2)} €</div>
          </div>`).join('');
        } else {
          coEl.innerHTML = `<div style="color:var(--sub);font-size:.8rem">${t('noCompletedTrips')}</div>`;
        }
      }).catch(() => { coEl.innerHTML = `<div style="color:var(--sub);font-size:.8rem">${t('noCompletedTrips')}</div>`; });
    } else {
      coEl.innerHTML = `<div style="color:var(--sub);font-size:.8rem">${t('noCompletedTrips')}</div>`;
    }
  }
}
