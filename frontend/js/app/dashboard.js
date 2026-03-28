/**
 * app/dashboard.js — Home dashboard + Meine Reisen overview stats
 *
 * Renders three sections of the home dashboard:
 *   loadDashTrackers() — active Ryanair trackers with latest price
 *   loadDashBudget()   — budget donut chart + remaining/spent amounts
 *   loadDashTrips()    — upcoming manual trips + past trips from Dawarich
 *
 * Also renders the "Meine Reisen → Übersicht" stats panel:
 *   loadMyTripsDashboard() — fetches /api/dashboard/stats for live data
 *     • Besuchte Orte: from Dawarich (locally synced trips)
 *     • Verbleibendes Budget: from ActualBudget
 *     • Wunschziele: from localStorage (client-side only)
 *
 * All three are called by loadDashboard(), which is triggered by navigate('home').
 * loadMyTripsDashboard() is called by switchMyTripsTab('overview').
 */

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
      return `<div class="dash-tracker-card" onclick="navigate('priceradar');setTimeout(()=>selectTracker(${tr.id}),200)">
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
            return `<div class="trip-card" style="cursor:pointer" onclick="navigate('mytrips')">
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

// ── Meine Reisen — Übersicht Live Stats ───────────────────────────────────────

/** Spinner HTML for loading state */
const _spinner = () => `<span class="spinner" style="display:inline-block;width:16px;height:16px;border-width:2px"></span>`;

/** Render a "not configured" state with link to settings */
const _notConfigured = (key) =>
  `<span style="font-size:.72rem;color:var(--muted)">${t(key) || 'Nicht verknüpft'}</span>`;

/** Render an error state */
const _error = () =>
  `<span style="font-size:.72rem;color:var(--red)">⚠ Fehler</span>`;

/**
 * Load live stats for the "Meine Reisen → Übersicht" tab.
 * Fetches /api/dashboard/stats and updates the three stat cards.
 * Falls back gracefully if backend is not configured or unreachable.
 */
export async function loadMyTripsDashboard() {
  const placesEl  = document.getElementById('mytrips-stat-places');
  const budgetEl  = document.getElementById('mytrips-stat-budget');
  const wishEl    = document.getElementById('mytrips-stat-wishlist');

  // 1. Show spinners immediately
  if (placesEl) placesEl.innerHTML  = _spinner();
  if (budgetEl) budgetEl.innerHTML  = _spinner();
  if (wishEl)   wishEl.innerHTML    = _spinner();

  // 2. Wishlist count is always local (instant)
  const wishCount = JSON.parse(localStorage.getItem('ws-bucketlist') || '[]').length;
  if (wishEl) wishEl.textContent = wishCount || '–';

  // 3. If no backend URL, show "not configured" for both
  if (!API_URL) {
    if (placesEl) placesEl.innerHTML = _notConfigured('statNotConnected');
    if (budgetEl) budgetEl.innerHTML = _notConfigured('statNotConnected');
    _renderOverviewLinks(placesEl, budgetEl, false, false);
    return;
  }

  // 4. Fetch live stats from backend
  try {
    const stats = await api('/api/dashboard/stats');

    // Visited places (Dawarich)
    if (placesEl) {
      if (stats.dawarich_status === 'not_configured') {
        placesEl.innerHTML = _notConfigured('statDawarichNotSet');
        _addSetupLink(placesEl.parentElement);
      } else if (stats.dawarich_status === 'error') {
        placesEl.innerHTML = _error();
      } else {
        const places   = stats.visited_places   ?? '–';
        const countries = stats.unique_countries ?? 0;
        placesEl.textContent = places;
        // Add subtitle with country count
        const label = placesEl.nextElementSibling;
        if (label && countries > 0) {
          label.innerHTML = `${t('mytripsVisitedPlaces')}<br>
            <span style="font-size:.6rem;color:var(--muted);font-weight:400">${countries} ${t('mytripsCountries') || 'Länder'}</span>`;
        }
      }
    }

    // Budget remaining (ActualBudget)
    if (budgetEl) {
      if (stats.budget_status === 'not_configured') {
        budgetEl.innerHTML = _notConfigured('statActualNotSet');
        _addSetupLink(budgetEl.parentElement);
      } else if (stats.budget_status === 'error') {
        budgetEl.innerHTML = _error();
      } else {
        const remaining = stats.budget_remaining ?? 0;
        budgetEl.textContent = remaining.toFixed(2) + ' €';
        // Add subtitle with month
        if (stats.budget_month) {
          const label = budgetEl.nextElementSibling;
          if (label) {
            label.innerHTML = `${t('mytripsSavedBudget')}<br>
              <span style="font-size:.6rem;color:var(--muted);font-weight:400">${stats.budget_month}</span>`;
          }
        }
      }
    }

  } catch(e) {
    // Backend unreachable — fall back to localStorage values
    if (placesEl) {
      const trips = JSON.parse(localStorage.getItem('ws-trips') || '[]');
      placesEl.textContent = trips.length || '–';
    }
    if (budgetEl) {
      const total  = parseFloat(localStorage.getItem('ws-budget') || '0');
      const trips  = JSON.parse(localStorage.getItem('ws-trips') || '[]');
      const spent  = trips.reduce((s, t) => s + t.cost, 0);
      const remain = Math.max(0, total - spent);
      budgetEl.textContent = total > 0 ? remain.toFixed(2) + ' €' : '–';
    }
  }
}

/** Add a small "Einrichten →" link below a stat card if not configured */
function _addSetupLink(cardEl) {
  if (!cardEl || cardEl.querySelector('.stat-setup-link')) return;
  const link = document.createElement('button');
  link.className = 'stat-setup-link';
  link.textContent = t('statSetupLink') || 'Einrichten →';
  link.onclick = (e) => { e.stopPropagation(); window.openSettings(); };
  link.style.cssText = 'margin-top:.4rem;font-size:.62rem;color:var(--accent2);background:none;border:none;cursor:pointer;text-decoration:underline;font-family:var(--sans);';
  cardEl.appendChild(link);
}
