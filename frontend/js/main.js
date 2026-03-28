// frontend/js/main.js
// Entry Point – importiert alle Module und exponiert benötigte
// Funktionen global (window.*) damit onclick="fn()" im HTML weiterhin funktioniert.

import { loadLocale, t, applyTranslations, setLang }   from './ui/i18n.js';
import { navigate, toggleSidebar, closeSidebar }        from './ui/nav.js';
import { api, checkApiStatus }                          from './core/api.js';
import {
  API_URL, currentLang, trips, obStep, allExpenses,
  setApiUrl, setSelectedTrackerId, setPriceChart,
  setSelectedBags, setTrips, setObStep, setAllExpenses
} from './core/state.js';

// ─── Alle Funktionen aus dem bisherigen Monolith (inline) ────────────────────
// Sie bleiben hier bis zu einem späteren Refactoring-Schritt erhalten.
// Dabei sind state-Variablen bereits aus core/state.js importiert.

 * WanderSuite v1.0 — Main Application
 * Navigation, i18n, Ryanair Tracker, Discover, Budget, Settings
 */

// ── State ─────────────────────────────────────────────
let TRANSLATIONS = {};
let currentLang = localStorage.getItem('lang') || 'de';
let API_URL = localStorage.getItem('apiUrl') || '';
let selectedTrackerId = null;
let priceChart = null;
let selectedBags = new Set();
let currentPage = 'ryanair';
let trips = JSON.parse(localStorage.getItem('ws-trips') || '[]');

// ── i18n ──────────────────────────────────────────────
async function loadLocale(lang) {
  if (TRANSLATIONS[lang]) return;
  try {
    const r = await fetch(`/locales/${lang}.json?v=0.1`);
    if (!r.ok) throw new Error(r.status);
    TRANSLATIONS[lang] = await r.json();
  } catch(e) { console.warn(`Locale '${lang}' failed:`, e); }
}

function t(key) {
  return TRANSLATIONS[currentLang]?.[key] || TRANSLATIONS['de']?.[key] || key;
}

function applyTranslations() {
  document.documentElement.lang = currentLang;
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n')); });
  document.querySelectorAll('[data-i18n-opt]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n-opt')); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.getAttribute('data-i18n-placeholder')); });
  document.querySelectorAll('.lang-btn').forEach(btn => { btn.classList.toggle('active', btn.textContent === currentLang.toUpperCase()); });
}

async function setLang(lang) {
  await loadLocale(lang);
  currentLang = lang;
  localStorage.setItem('lang', lang);
  applyTranslations();
  loadTrackers();
  if (selectedTrackerId) selectTracker(selectedTrackerId);
}

// ── Navigation ─────────────────────────────────────────
function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + page)?.classList.add('active');
  document.getElementById('nav-' + page)?.classList.add('active');
  currentPage = page;
  // Close sidebar on mobile
  if (window.innerWidth < 900) closeSidebar();
  // Lazy-init modules
  if (page === 'home')    loadDashboard();
  if (page === 'budget')  renderBudget();
  if (page === 'journal') loadJournalTrips();
  if (page === 'google')  loadGFTrackers();
  if (page === 'homair')  loadHomairTrackers();
  if (page === 'booking') loadBookingTrackers();
}

function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  const hb = document.getElementById('hamburger');
  const isOpen = sb.classList.toggle('open');
  hb.classList.toggle('open', isOpen);
}

function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('hamburger').classList.remove('open');
}

// ── Init ───────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  const toLoad = currentLang === 'de' ? ['de'] : ['de', currentLang];
  await Promise.all(toLoad.map(loadLocale));
  applyTranslations();

  // Apply saved theme
  if (localStorage.getItem('theme') === 'light') document.body.classList.add('light-mode');

  const saved = localStorage.getItem('apiUrl') || '';
  API_URL = saved;

  const today = new Date();
  const out = new Date(today); out.setDate(out.getDate() + 30);
  const ret = new Date(today); ret.setDate(ret.getDate() + 37);
  document.getElementById('outboundDate').value = fmt(out);
  document.getElementById('returnDate').value = fmt(ret);

  checkApiStatus();
  loadTrackers();
  loadDashboard();
  checkOnboarding();

  // Hide api notice if URL already set
  if (API_URL) {
    const notice = document.querySelector('.api-notice');
    if (notice) notice.classList.add('hidden');
  }

  // Restore budget
  const savedBudget = localStorage.getItem('ws-budget');
  if (savedBudget) document.getElementById('budgetTotal').value = savedBudget;

  // Close sidebar on outside click
  document.addEventListener('click', e => {
    const sb = document.getElementById('sidebar');
    const hb = document.getElementById('hamburger');
    if (window.innerWidth < 900 && sb.classList.contains('open') &&
        !sb.contains(e.target) && !hb.contains(e.target)) {
      closeSidebar();
    }
  });

  // ESC closes modal
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSettings(); });
});

function fmt(d) { return d.toISOString().slice(0,10); }

// ── API ────────────────────────────────────────────────
async function api(path, opts = {}) {
  const base = localStorage.getItem('apiUrl') || API_URL || '';
  if (!base) throw new Error(t('missingUrl'));
  const r = await fetch(base + path, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!r.ok) { const err = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(err.detail || `HTTP ${r.status}`); }
  return r.json();
}

async function checkApiStatus() {
  const dot = document.getElementById('statusDot');
  // Always read from localStorage directly — most up to date
  const base = localStorage.getItem('apiUrl') || '';
  if (!base) {
    dot.style.background = 'var(--red)';
    dot.style.boxShadow  = '0 0 6px var(--red)';
    dot.title = 'Backend URL nicht konfiguriert';
    return;
  }
  try {
    const r2 = await fetch(base + '/health', { signal: AbortSignal.timeout(5000) });
    if (!r2.ok) throw new Error(`HTTP ${r2.status}`);
    dot.style.background = 'var(--green)';
    dot.style.boxShadow  = '0 0 6px var(--green)';
    dot.title = 'Backend online';
  } catch(e) {
    dot.style.background = 'var(--red)';
    dot.style.boxShadow  = '0 0 6px var(--red)';
    dot.title = 'Backend nicht erreichbar: ' + e.message;
  }
}

// ── Baggage ────────────────────────────────────────────
function toggleBag(type) {
  if (selectedBags.has(type)) {
    selectedBags.delete(type);
    document.getElementById('bag-'+type).classList.remove('selected');
    document.getElementById('chk-'+type).textContent = '';
  } else {
    selectedBags.add(type);
    document.getElementById('bag-'+type).classList.add('selected');
    document.getElementById('chk-'+type).textContent = '✓';
  }
}

// ── Add Tracker ────────────────────────────────────────
async function addTracker() {
  const btn = document.getElementById('addBtn');
  const origin = document.getElementById('origin').value.trim().toUpperCase();
  const dest   = document.getElementById('destination').value.trim().toUpperCase();
  const outDate = document.getElementById('outboundDate').value;
  const retDate = document.getElementById('returnDate').value;
  if (!origin || origin.length !== 3) { toast(t('invalidOrigin'), 'error'); return; }
  if (!dest   || dest.length   !== 3) { toast(t('invalidDest'), 'error'); return; }
  if (!outDate)                        { toast(t('missingDate'), 'error'); return; }
  if (!API_URL)                        { toast(t('missingUrl'), 'warning'); return; }
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> ${t('creatingTracker')}`;
  try {
    await api('/api/trackers', { method: 'POST', body: JSON.stringify({
      origin, destination: dest, outbound_date: outDate, return_date: retDate || null,
      adults: parseInt(document.getElementById('adults').value),
      children: parseInt(document.getElementById('children').value),
      baggage: [...selectedBags].map(type => ({ type, per_person: true })),
      seat_cost: parseFloat(document.getElementById('seatCost').value) || 0,
    })});
    toast(`${t('trackerAdded')} ✓ ${origin} → ${dest}`, 'success');
    document.getElementById('origin').value = '';
    document.getElementById('destination').value = '';
    document.getElementById('seatCost').value = '0';
    selectedBags.clear();
    ['10kg','20kg','23kg'].forEach(tp => {
      document.getElementById('bag-'+tp).classList.remove('selected');
      document.getElementById('chk-'+tp).textContent = '';
    });
    loadTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
  finally { btn.disabled = false; btn.innerHTML = `+ ${t('startTracker')}`; }
}

// ── Trackers ───────────────────────────────────────────
async function loadTrackers() {
  const el = document.getElementById('trackerList');
  try { renderTrackers(await api('/api/trackers')); }
  catch(e) { el.innerHTML = `<div style="color:var(--red);font-size:.76rem">⚠ ${e.message}</div>`; }
}

function renderTrackers(trackers) {
  const el = document.getElementById('trackerList');
  if (!trackers.length) { el.innerHTML = `<div style="color:var(--muted);font-size:.78rem;padding:.4rem 0">${t('noTrackers')}</div>`; return; }
  el.innerHTML = trackers.map(tr => {
    const snap = tr.latest_snapshot;
    const priceStr = snap?.total_price ? `${snap.total_price.toFixed(2)} €` : '–';
    const statusBadge = !tr.active
      ? `<span class="badge badge-paused">${t('paused')}</span>`
      : snap?.status === 'ok'
        ? (snap.baggage_fallback ? `<span class="badge badge-fallback">~${t('estimate')}</span>` : '<span class="badge badge-ok">Live</span>')
        : snap?.status === 'blocked' ? `<span class="badge badge-blocked">${t('blocked')}</span>` : '';
    const bagStr = (tr.baggage||[]).map(b => b.type).join(', ') || t('backpackOnly');
    const retStr = tr.return_date ? ` ⇄ ${tr.return_date}` : ` (${t('oneWay')})`;
    return `<div class="tracker-item ${tr.id===selectedTrackerId?'active-tracker':''}" onclick="selectTracker(${tr.id})">
      <div class="tracker-header">
        <div class="tracker-route">${tr.origin} → ${tr.destination}</div>
        <div class="tracker-price ${snap?'':'stale'}">${priceStr}</div>
      </div>
      <div class="tracker-meta">
        <span>${tr.outbound_date}${retStr}</span>
        <span>${tr.adults} ${t('adultShort')}</span>
        <span>🧳 ${bagStr}</span>
        ${statusBadge}
      </div>
      <div class="tracker-actions">
        <button class="btn-scrape" onclick="event.stopPropagation();scrapeNow(${tr.id})">⟳ ${t('current')}</button>
        <button class="btn-sm" onclick="event.stopPropagation();togglePause(${tr.id},${tr.active})">${tr.active?'⏸':'▶'}</button>
        <button class="btn-sm btn-danger" onclick="event.stopPropagation();deleteTracker(${tr.id})">✕</button>
      </div></div>`;
  }).join('');
}

// ── Chart ──────────────────────────────────────────────
async function selectTracker(id) {
  selectedTrackerId = id; loadTrackers();
  const container = document.getElementById('chartContainer');
  const empty = document.getElementById('chartEmpty');
  const tableCard = document.getElementById('tableCard');
  container.style.display = 'none'; empty.style.display = 'none';
  const card = document.getElementById('chartCard');
  const overlay = document.createElement('div');
  overlay.className = 'loading-overlay';
  overlay.innerHTML = `<span class="spinner"></span> ${t('loadingChart')}`;
  card.style.position = 'relative'; card.appendChild(overlay);
  try {
    const data = await api(`/api/prices/${id}?limit=90`);
    card.removeChild(overlay);
    if (!data.total_prices.length) {
      empty.style.display = 'flex';
      document.getElementById('chartTitle').textContent = `${t('priceHistory')} – ${t('noData')}`;
      return;
    }
    const tr = data.tracker;
    document.getElementById('chartTitle').textContent = `${tr.origin} → ${tr.destination}  ${tr.outbound_date}${tr.return_date?' ⇄ '+tr.return_date:''}`;
    renderStats(data); renderChart(data); renderTable(data.snapshots);
    container.style.display = 'block'; tableCard.style.display = 'block';
    if (window.innerWidth < 900) card.scrollIntoView({ behavior:'smooth', block:'start' });
  } catch(e) { card.removeChild(overlay); empty.style.display = 'flex'; toast(`${t('error')}: ${e.message}`, 'error'); }
}

function renderStats(data) {
  const prices = data.total_prices.filter(p => p !== null);
  if (!prices.length) return;
  const min = Math.min(...prices), cur = prices[prices.length-1], prev = prices.length>1?prices[prices.length-2]:cur;
  const diff = cur-prev, ds = (diff>=0?'+':'')+diff.toFixed(2)+' €';
  document.getElementById('chartStats').innerHTML = `
    <div class="stat"><div class="stat-label">${t('current')}</div><div class="stat-value">${cur.toFixed(2)} €</div><div style="font-size:.6rem;color:var(--sub);margin-top:.18rem">${data.labels[data.labels.length-1]}</div></div>
    <div class="stat"><div class="stat-label">${t('lowestPrice')}</div><div class="stat-value green">${min.toFixed(2)} €</div></div>
    <div class="stat"><div class="stat-label">${t('change')}</div><div class="stat-value ${diff>0?'red':diff<0?'green':''}">${ds}</div></div>`;
}

function renderChart(data) {
  if (priceChart) { priceChart.destroy(); priceChart = null; }
  priceChart = new Chart(document.getElementById('priceChart').getContext('2d'), {
    type:'line',
    data:{ labels:data.labels, datasets:[
      { label:t('total'),   data:data.total_prices,   borderColor:'#ff5533', backgroundColor:'rgba(255,85,51,.08)', borderWidth:2, pointRadius:4, pointHoverRadius:6, pointBackgroundColor:'#ff5533', fill:true, tension:.3 },
      { label:t('tickets'), data:data.flight_prices,  borderColor:'#ff8c00', backgroundColor:'transparent', borderWidth:1.5, borderDash:[4,3], pointRadius:3, fill:false, tension:.3 },
      { label:t('baggage'), data:data.baggage_prices, borderColor:'#7a7d88', backgroundColor:'transparent', borderWidth:1.5, borderDash:[2,4], pointRadius:2, fill:false, tension:.3 },
      { label:t('seat'),    data:data.seat_prices,   borderColor:'#8b5cf6', backgroundColor:'transparent', borderWidth:1.5, borderDash:[3,5], pointRadius:2, fill:false, tension:.3 },
    ]},
    options:{
      responsive:true, maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
      plugins:{
        legend:{position:'top',labels:{color:'#7a7d88',font:{family:"'Space Mono',monospace",size:10},boxWidth:12,boxHeight:2,padding:12}},
        tooltip:{backgroundColor:'#141519',borderColor:'#2a2b30',borderWidth:1,titleColor:'#e8e9ec',bodyColor:'#7a7d88',padding:10,callbacks:{label:ctx=>` ${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(2)??'–'} €`}}
      },
      scales:{
        x:{grid:{color:'rgba(42,43,48,.5)'},ticks:{color:'#7a7d88',font:{family:"'Space Mono'",size:9},maxRotation:45}},
        y:{grid:{color:'rgba(42,43,48,.5)'},ticks:{color:'#7a7d88',font:{family:"'Space Mono'",size:9},callback:v=>v+' €'}}
      }
    }
  });
}

function renderTable(snaps) {
  document.getElementById('snapshotTable').innerHTML = [...snaps].reverse().slice(0,30).map(s => {
    const st = s.status==='ok' ? (s.baggage_fallback?`<span class="badge badge-fallback">~${t('estimate')}</span>`:'<span class="badge badge-ok">✓</span>') : `<span class="badge badge-blocked">${s.status}</span>`;
    const seatP = s.seat_price != null && s.seat_price > 0 ? s.seat_price.toFixed(2)+' €' : '–';
    return `<tr><td>${(s.fetched_at||'').slice(0,10)}</td><td>${s.outbound_flight||'–'}</td><td>${s.return_flight||'–'}</td><td>${s.flight_price!=null?s.flight_price.toFixed(2)+' €':'–'}</td><td>${s.baggage_price!=null?s.baggage_price.toFixed(2)+' €':'–'}</td><td>${seatP}</td><td style="color:var(--green);font-weight:700">${s.total_price!=null?s.total_price.toFixed(2)+' €':'–'}</td><td>${st}</td></tr>`;
  }).join('');
}

// ── Tracker Actions ────────────────────────────────────
async function scrapeNow(id) {
  toast(t('scrapeStarted'), 'warning');
  try {
    const result = await api(`/api/trackers/${id}/scrape`, { method:'POST' });
    const snap = result.snapshot;
    if (snap?.total_price) toast(`${t('current')}: ${snap.total_price.toFixed(2)} €${snap.baggage_fallback?` (~${t('estimate')})`:''}`,'success');
    else toast(`${t('status')}: ${snap?.status||'?'}`, 'warning');
    loadTrackers(); if (selectedTrackerId===id) selectTracker(id);
  } catch(e) { toast(`${t('scrapeError')}: ${e.message}`, 'error'); }
}

async function deleteTracker(id) {
  if (!confirm(t('deleteConfirm'))) return;
  try {
    await api(`/api/trackers/${id}`, { method:'DELETE' });
    toast(t('deleted'), 'success');
    if (selectedTrackerId===id) {
      selectedTrackerId=null;
      document.getElementById('chartContainer').style.display='none';
      document.getElementById('chartEmpty').style.display='flex';
      document.getElementById('tableCard').style.display='none';
    }
    loadTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

async function togglePause(id, currentlyActive) {
  try { await api(`/api/trackers/${id}/toggle?active=${!currentlyActive}`, { method:'PATCH' }); toast(currentlyActive?t('paused'):t('activated'), 'success'); loadTrackers(); }
  catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

// ── Discover Module ─────────────────────────────────────
function checkDawarich(on) {
  const notice = document.getElementById('discoverDawarichNotice');
  if (on && !localStorage.getItem('s-dawarichUrl')) {
    notice.style.display = 'block';
    document.getElementById('discoverDawarich').checked = false;
  } else {
    notice.style.display = 'none';
  }
}

async function generateIdeas() {
  const q = document.getElementById('discoverQuery').value.trim();
  if (!q) { toast(t('discoverNoQuery'), 'warning'); return; }

  const provider = document.getElementById('discoverProvider')?.value || 'gemini';
  const localKey = provider === 'openai'
    ? (localStorage.getItem('s-openaiKey') || '')
    : (localStorage.getItem('s-geminiKey') || '');

  const results = document.getElementById('discoverResults');
  results.innerHTML = '<span class="spinner"></span> ' + t('discoverGenerating');

  const useDawarich = document.getElementById('discoverDawarich').checked;

  try {
    const payload = {
      query: q,
      provider,
      api_key: localKey || undefined,
      lang: currentLang,
      exclude_places: useDawarich ? [] : [],
    };

    const resp = await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/discover', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();

    if (data.error) {
      results.textContent = '❌ ' + data.error;
      return;
    }

    if (data.recommendations && Array.isArray(data.recommendations)) {
      results.innerHTML = renderRecommendations(data.recommendations);
    } else if (data.raw) {
      results.innerHTML = `<pre style="white-space:pre-wrap;font-size:.75rem;text-align:left">${data.raw}</pre>`;
    } else {
      results.textContent = '⚠ Unerwartetes Antwortformat';
    }
  } catch(e) {
    results.textContent = '❌ ' + e.message;
    toast(t('error') + ': ' + e.message, 'error');
  }
}

function renderRecommendations(recs) {
  return recs.map(r => `
    <div style="border:1px solid var(--border);border-radius:var(--radius);padding:.85rem;margin-bottom:.6rem;text-align:left">
      <div style="font-weight:800;font-size:.95rem;margin-bottom:.3rem">🌍 ${r.destination}</div>
      <div style="font-size:.78rem;color:var(--sub);margin-bottom:.4rem;line-height:1.5">${r.why}</div>
      <div style="display:flex;gap:.75rem;flex-wrap:wrap;font-size:.7rem;font-family:var(--mono)">
        <span style="color:var(--accent2)">📅 ${r.best_time}</span>
        <span style="color:var(--green)">💶 ${r.estimated_budget}</span>
        <span style="color:var(--text)">⭐ ${r.highlight}</span>
      </div>
    </div>`).join('');
}

// ── Budget Module ───────────────────────────────────────
function toggleActualSync(on) {
  document.getElementById('manualEntry').style.display = on ? 'none' : 'block';
  document.getElementById('actualEntry').style.display = on ? 'block' : 'none';
  if (on && (!localStorage.getItem('s-actualUrl') || !localStorage.getItem('s-actualFile'))) {
    document.getElementById('actualNotice').style.display = 'block';
  } else {
    document.getElementById('actualNotice').style.display = 'none';
  }
}

function addTrip() {
  const name = document.getElementById('tripName').value.trim();
  const cost = parseFloat(document.getElementById('tripCost').value);
  if (!name || isNaN(cost) || cost <= 0) { toast(t('error') + ': ' + t('budgetTripName'), 'error'); return; }
  trips.push({ name, cost, date: new Date().toISOString().slice(0,10) });
  localStorage.setItem('ws-trips', JSON.stringify(trips));
  document.getElementById('tripName').value = '';
  document.getElementById('tripCost').value = '';
  renderBudget();
}

async function syncActualBudget() {
  const url      = localStorage.getItem('s-actualUrl')      || '';
  const password = localStorage.getItem('s-actualPassword')  || '';
  const file     = localStorage.getItem('s-actualFile')       || '';

  if (!url || !password || !file) {
    document.getElementById('actualNotice').style.display = 'block';
    toast(t('actualBudgetError') + ': ' + t('budgetNoActual'), 'warning');
    return;
  }

  toast(t('actualBudgetSyncing'), 'warning');
  const resultEl = document.getElementById('actualSyncResult');

  try {
    const resp = await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/budget/actual/summary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ base_url: url, password, budget_file: file }),
    });
    const data = await resp.json();

    if (data.error) {
      toast(t('actualBudgetError') + ': ' + data.error, 'error');
      return;
    }

    // Update budget UI with ActualBudget data
    const totalSpent = data.total_spent || 0;
    const totalBudgeted = data.total_budgeted || 0;

    // Sync trips from ActualBudget categories
    if (data.travel_categories && data.travel_categories.length) {
      trips = data.travel_categories.map(cat => ({
        name: cat.name,
        cost: cat.spent,
        date: data.month,
        source: 'actualbudget',
      }));
      localStorage.setItem('ws-trips', JSON.stringify(trips));
    }

    // Show sync result
    resultEl.style.display = 'block';
    resultEl.innerHTML = `<div style="font-size:.72rem;color:var(--green)">
      ✓ ${t('actualBudgetSynced')} — ${data.month}<br>
      ${data.travel_categories?.length || 0} Reise-Kategorien | ${totalSpent.toFixed(2)} € ausgegeben
    </div>`;

    // Update budget total if available
    if (totalBudgeted > 0) {
      document.getElementById('budgetTotal').value = totalBudgeted.toFixed(2);
      localStorage.setItem('ws-budget', totalBudgeted.toFixed(2));
    }

    renderBudget();
    toast(t('actualBudgetSynced'), 'success');

  } catch(e) {
    toast(t('actualBudgetError') + ': ' + e.message, 'error');
  }
}

function updateBudget() {
  const val = document.getElementById('budgetTotal').value;
  localStorage.setItem('ws-budget', val);
  renderBudget();
}

function renderBudget() {
  const total = parseFloat(document.getElementById('budgetTotal').value) || 0;
  const used  = trips.reduce((s, t) => s + t.cost, 0);
  const remaining = Math.max(0, total - used);
  const pct = total > 0 ? Math.min(100, (used / total) * 100) : 0;

  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('progressFill').style.background = pct > 85 ? 'var(--red)' : pct > 60 ? 'var(--accent2)' : 'var(--accent)';
  document.getElementById('budgetUsedLabel').textContent = used.toFixed(2) + ' €';
  document.getElementById('budgetRemainingLabel').textContent = remaining.toFixed(2) + ' €';

  const list = document.getElementById('tripList');
  list.innerHTML = trips.length ? trips.slice().reverse().map((tr, i) => `
    <div class="trip-item">
      <div><div class="trip-item-name">${tr.name}</div><div style="font-size:.65rem;color:var(--sub)">${tr.date}</div></div>
      <div style="display:flex;align-items:center;gap:.5rem">
        <div class="trip-item-cost">${tr.cost.toFixed(2)} €</div>
        <button class="btn-sm btn-danger" onclick="removeTrip(${trips.length-1-i})">✕</button>
      </div>
    </div>`).join('') : `<div style="font-size:.76rem;color:var(--muted);padding:.5rem 0">${t('noTrackers').replace('Tracker','Reisen')}</div>`;
}

function removeTrip(idx) {
  trips.splice(idx, 1);
  localStorage.setItem('ws-trips', JSON.stringify(trips));
  renderBudget();
}

// ── Settings ────────────────────────────────────────────
function openSettings() {
  const tzSel = document.getElementById('s-timezone');
  if (!tzSel.options.length) {
    ['Europe/Rome','Europe/Berlin','Europe/London','Europe/Paris','Europe/Madrid','Europe/Zurich','Europe/Vienna','America/New_York','America/Chicago','America/Los_Angeles','Asia/Tokyo','Asia/Shanghai','Australia/Sydney','UTC'].forEach(z => {
      const o = document.createElement('option'); o.value = o.textContent = z; tzSel.appendChild(o);
    });
  }
  document.getElementById('s-backendUrl').value    = localStorage.getItem('apiUrl') || '';
  document.getElementById('s-timezone').value      = localStorage.getItem('s-timezone') || 'Europe/Rome';
  document.getElementById('s-lightMode').checked   = document.body.classList.contains('light-mode');
  document.getElementById('s-dawarichUrl').value   = localStorage.getItem('s-dawarichUrl') || '';
  document.getElementById('s-dawarichToken').value = localStorage.getItem('s-dawarichToken') || '';
  document.getElementById('s-actualUrl').value      = localStorage.getItem('s-actualUrl') || '';
  document.getElementById('s-actualPassword').value = localStorage.getItem('s-actualPassword') || '';
  document.getElementById('s-actualFile').value     = localStorage.getItem('s-actualFile') || '';
  document.getElementById('s-llmProvider').value   = localStorage.getItem('s-llmProvider') || '';
  document.getElementById('s-llmKey').value            = localStorage.getItem('s-llmKey') || '';
  document.getElementById('s-homeLat').value          = localStorage.getItem('s-homeLat') || '';
  document.getElementById('s-homeLon').value          = localStorage.getItem('s-homeLon') || '';
  document.getElementById('s-travelCategories').value = localStorage.getItem('s-travelCategories') || '';
  document.getElementById('s-serpApiKey').value    = localStorage.getItem('s-serpApiKey') || '';
  document.getElementById('s-geminiKey').value     = localStorage.getItem('s-geminiKey') || '';
  document.getElementById('s-openaiKey').value     = localStorage.getItem('s-openaiKey') || '';
  switchTab('basic');
  document.getElementById('settingsBackdrop').classList.add('open');
  document.body.style.overflow = 'hidden';
  // Quota laden wenn Key vorhanden
  if (localStorage.getItem('s-serpApiKey')) loadSerpApiQuota();
}

function closeSettings() {
  document.getElementById('settingsBackdrop').classList.remove('open');
  document.body.style.overflow = '';
}

async function loadSerpApiQuota() {
  const apiUrl = localStorage.getItem('apiUrl');
  if (!apiUrl) return;
  const wrap = document.getElementById('serpapi-quota-wrap');
  const bar  = document.getElementById('serpapi-quota-bar');
  const txt  = document.getElementById('serpapi-quota-text');
  wrap.style.display = 'block';
  txt.textContent = '…';
  try {
    const r = await fetch(`${apiUrl}/api/settings/serpapi-quota`);
    const d = await r.json();
    if (d.error) { txt.textContent = d.error; bar.style.width = '0%'; return; }
    const used  = d.used  ?? 0;
    const limit = d.limit ?? 100;
    const pct   = Math.min(100, Math.round((used / limit) * 100));
    bar.style.width = pct + '%';
    bar.style.background = pct >= 90 ? '#e07b5a' : pct >= 70 ? '#d4a843' : 'var(--accent)';
    txt.textContent = `${used} / ${limit}`;
  } catch(e) {
    txt.textContent = 'Fehler';
  }
}

function backdropClick(e) {
  if (e.target === document.getElementById('settingsBackdrop')) closeSettings();
}

function switchTab(tab) {
  ['basic','integrations'].forEach(t => {
    document.getElementById('panel-'+t).style.display = t===tab?'block':'none';
    document.getElementById('tab-'+t).classList.toggle('active', t===tab);
  });
}

function toggleTheme(isLight) {
  document.body.classList.toggle('light-mode', isLight);
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
}

async function saveSettings() {
  API_URL = document.getElementById('s-backendUrl').value.trim().replace(/\/$/, '');
  localStorage.setItem('apiUrl', API_URL);
  ['s-timezone','s-dawarichUrl','s-dawarichToken','s-actualUrl','s-actualPassword','s-actualFile','s-llmProvider','s-llmKey','s-serpApiKey','s-geminiKey','s-openaiKey','s-homeLat','s-homeLon','s-travelCategories'].forEach(k => {
    localStorage.setItem(k, document.getElementById(k).value);
  });
  // Sync keys to server (encrypted)
  try {
    await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        serpapi_key:       document.getElementById('s-serpApiKey').value || null,
        gemini_key:        document.getElementById('s-geminiKey').value  || null,
        openai_key:        document.getElementById('s-openaiKey').value  || null,
        dawarich_url:      document.getElementById('s-dawarichUrl').value   || null,
        dawarich_token:    document.getElementById('s-dawarichToken').value  || null,
        actual_url:        document.getElementById('s-actualUrl').value      || null,
        actual_token:      document.getElementById('s-actualPassword').value || null,
        actual_file:       document.getElementById('s-actualFile').value    || null,
        llm_provider:      document.getElementById('s-llmProvider').value  || null,
        timezone:          document.getElementById('s-timezone').value    || null,
        home_lat:          document.getElementById('s-homeLat').value      || null,
        home_lon:          document.getElementById('s-homeLon').value      || null,
        travel_categories: document.getElementById('s-travelCategories').value || null,
      }),
    });
  } catch(e) { /* Server sync optional — localStorage als Fallback */ }

  // Update global API_URL from saved value
  API_URL = localStorage.getItem('apiUrl') || '';
  toast(t('saved') + ' ✓', 'success');
  closeSettings();
  setTimeout(checkApiStatus, 300);
  setTimeout(loadTrackers, 600);
  loadDashboard();
  checkOnboarding();

  // Hide api notice if URL already set
  if (API_URL) {
    const notice = document.querySelector('.api-notice');
    if (notice) notice.classList.add('hidden');
  }
}

// ── Google Flights Tracker ────────────────────────────
async function addGFTracker() {
  const btn = document.getElementById('gf-addBtn');
  const origin  = document.getElementById('gf-origin').value.trim().toUpperCase();
  const dest    = document.getElementById('gf-dest').value.trim().toUpperCase();
  const outDate = document.getElementById('gf-date').value;
  const retDate = document.getElementById('gf-return')?.value || '';
  const pax     = parseInt(document.getElementById('gf-pax').value);

  if (!origin || origin.length !== 3) { toast(t('invalidOrigin'), 'error'); return; }
  if (!dest   || dest.length   !== 3) { toast(t('invalidDest'), 'error'); return; }
  if (!outDate)                        { toast(t('missingDate'), 'error'); return; }
  if (!API_URL)                        { toast(t('missingUrl'), 'warning'); return; }

  const serpKey = localStorage.getItem('s-serpApiKey') || '';
  if (!serpKey) {
    document.getElementById('gf-serpapi-notice').style.display = 'block';
    toast(t('serpApiMissing'), 'warning');
    return;
  }
  document.getElementById('gf-serpapi-notice').style.display = 'none';

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> ${t('creatingTracker')}`;

  try {
    const r = await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/google-flights', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin, destination: dest, outbound_date: outDate, return_date: retDate || null, adults: pax, children: parseInt(document.getElementById('gf-children')?.value||0) }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    toast(`${t('gfTrackerAdded')} ✓ ${origin} → ${dest}`, 'success');
    document.getElementById('gf-origin').value = '';
    document.getElementById('gf-dest').value = '';
    loadGFTrackers();
  } catch(e) {
    toast(`${t('error')}: ${e.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `+ ${t('startTracker')}`;
  }
}

async function loadGFTrackers() {
  if (!API_URL) return;
  try {
    const r = await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/google-flights');
    const trackers = await r.json();
    renderGFTrackers(trackers);
  } catch(e) { /* silent fail if backend not yet updated */ }
}

function renderGFTrackers(trackers) {
  const el = document.getElementById('gf-trackerList');
  if (!el) return;
  if (!trackers.length) {
    el.innerHTML = `<div style="color:var(--muted);font-size:.78rem;padding:.4rem 0">${t('gfNoTrackers')}</div>`;
    return;
  }
  el.innerHTML = trackers.map(tr => {
    const snap = tr.latest_snapshot;
    const priceStr = snap?.total_price ? `${snap.total_price.toFixed(2)} €` : '–';
    const airlineStr = snap?.airline ? `✈ ${snap.airline}` : '';
    const flightNo   = snap?.outbound_flight ? snap.outbound_flight : '';
    const times      = snap?.departure_time && snap?.arrival_time
      ? `${snap.departure_time} → ${snap.arrival_time}` : '';
    const durMin     = snap?.duration_min ? `${Math.floor(snap.duration_min/60)}h ${snap.duration_min%60}m` : '';
    return `<div class="tracker-item">
      <div class="tracker-header">
        <div class="tracker-route">${tr.origin} → ${tr.destination}</div>
        <div class="tracker-price ${snap?'':'stale'}">${priceStr}</div>
      </div>
      <div class="tracker-meta">
        <span>${tr.outbound_date}${tr.return_date?' ⇄ '+tr.return_date:' ('+t('oneWay')+')'}</span>
        <span>${tr.adults} ${t('adultShort')}${tr.children>0?' · '+tr.children+' Kind':''}</span>
        ${airlineStr?`<span>${airlineStr}${flightNo?' '+flightNo:''}</span>`:''}
        ${times?`<span>🕐 ${times}${durMin?' ('+durMin+')':''}</span>`:''}
        <span class="badge badge-ok">Google Flights</span>
      </div>
      <div class="tracker-actions">
        <button class="btn-scrape" onclick="scrapeGFTracker(${tr.id})">⟳ ${t('current')}</button>
        <button class="btn-sm btn-danger" onclick="deleteGFTracker(${tr.id})">✕</button>
      </div>
    </div>`;
  }).join('');
}

async function scrapeGFTracker(id) {
  const serpKey = localStorage.getItem('s-serpApiKey') || '';
  toast(t('gfSearching'), 'warning');
  try {
    const r = await fetch(`${localStorage.getItem('apiUrl')||API_URL}/api/google-flights/${id}/scrape?api_key=${encodeURIComponent(serpKey)}`, { method: 'POST' });
    const data = await r.json();
    const snap = data.snapshot;
    if (snap?.total_price) toast(`${t('current')}: ${snap.total_price.toFixed(2)} €`, 'success');
    else toast(`Status: ${snap?.status}`, 'warning');
    loadGFTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

async function deleteGFTracker(id) {
  if (!confirm(t('deleteConfirm'))) return;
  try {
    await fetch(`${localStorage.getItem('apiUrl')||API_URL}/api/google-flights/${id}`, { method: 'DELETE' });
    toast(t('deleted'), 'success');
    loadGFTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

// ── Homair Tracker ────────────────────────────────────
async function addHomairTracker() {
  const btn      = document.getElementById('hm-addBtn');
  const region   = document.getElementById('hm-region').value;
  const accType  = document.getElementById('hm-type').value;
  const checkin  = document.getElementById('hm-checkin').value;
  const checkout = document.getElementById('hm-checkout').value;
  const adults   = parseInt(document.getElementById('hm-adults').value);
  const children = parseInt(document.getElementById('hm-children').value);

  if (!checkin || !checkout) { toast(t('missingDate'), 'error'); return; }
  if (!API_URL) { toast(t('missingUrl'), 'warning'); return; }

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> ${t('creatingTracker')}`;
  try {
    const r = await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/accommodations/homair', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ region, accommodation_type: accType, checkin_date: checkin, checkout_date: checkout, adults, children }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast(t('homairTrackerAdded'), 'success');
    loadHomairTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
  finally { btn.disabled = false; btn.innerHTML = `+ ${t('startTracker')}`; }
}

async function loadHomairTrackers() {
  if (!API_URL) return;
  try {
    const r = await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/accommodations/homair');
    const trackers = await r.json();
    renderHomairTrackers(trackers);
  } catch(e) {}
}

function renderHomairTrackers(trackers) {
  const el = document.getElementById('hm-trackerList');
  if (!el) return;
  if (!trackers.length) { el.innerHTML = `<div style="color:var(--muted);font-size:.78rem;padding:.4rem 0">${t('homairNoTrackers')}</div>`; return; }
  el.innerHTML = trackers.map(tr => {
    const snap = tr.latest_snapshot;
    const priceStr = snap?.total_price ? `${snap.total_price.toFixed(2)} €` : '–';
    return `<div class="tracker-item">
      <div class="tracker-header">
        <div class="tracker-route">⛺ ${tr.region}</div>
        <div class="tracker-price ${snap?'':'stale'}">${priceStr}</div>
      </div>
      <div class="tracker-meta">
        <span>${tr.checkin_date} → ${tr.checkout_date}</span>
        <span>${tr.accommodation_type}</span>
        <span>${tr.adults} ${t('adultShort')}</span>
      </div>
      <div class="tracker-actions">
        <button class="btn-scrape" onclick="scrapeHomairTracker(${tr.id})">⟳ ${t('current')}</button>
        <button class="btn-sm btn-danger" onclick="deleteHomairTracker(${tr.id})">✕</button>
      </div>
    </div>`;
  }).join('');
}

async function scrapeHomairTracker(id) {
  toast(t('homairSearching'), 'warning');
  try {
    const r = await fetch(`${localStorage.getItem('apiUrl')||API_URL}/api/accommodations/homair/${id}/scrape`, { method: 'POST' });
    const data = await r.json();
    const snap = data.snapshot;
    if (snap?.total_price) toast(`${t('current')}: ${snap.total_price.toFixed(2)} €/Nacht`, 'success');
    else toast(`Status: ${snap?.status} — ${snap?.error_message || ''}`, 'warning');
    loadHomairTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

async function deleteHomairTracker(id) {
  if (!confirm(t('deleteConfirm'))) return;
  try {
    await fetch(`${localStorage.getItem('apiUrl')||API_URL}/api/accommodations/homair/${id}`, { method: 'DELETE' });
    toast(t('deleted'), 'success'); loadHomairTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

// ── Booking Tracker ────────────────────────────────────
async function addBookingTracker() {
  const btn     = document.getElementById('bk-addBtn');
  const dest    = document.getElementById('bk-dest').value.trim();
  const checkin = document.getElementById('bk-checkin').value;
  const checkout= document.getElementById('bk-checkout').value;
  const adults  = parseInt(document.getElementById('bk-adults').value);
  const rooms   = parseInt(document.getElementById('bk-rooms').value);
  const source  = document.getElementById('bk-source').value;

  if (!dest)              { toast(t('invalidDest'), 'error'); return; }
  if (!checkin||!checkout){ toast(t('missingDate'), 'error'); return; }
  if (!API_URL)           { toast(t('missingUrl'), 'warning'); return; }

  const serpKey = localStorage.getItem('s-serpApiKey') || '';
  if (!serpKey) {
    document.getElementById('bk-serpapi-notice').style.display = 'block';
    toast(t('serpApiMissingBooking'), 'warning'); return;
  }
  document.getElementById('bk-serpapi-notice').style.display = 'none';

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> ${t('creatingTracker')}`;
  try {
    const r = await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/accommodations/booking', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination: dest, checkin_date: checkin, checkout_date: checkout, adults, rooms, source }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast(t('bookingTrackerAdded'), 'success');
    document.getElementById('bk-dest').value = '';
    loadBookingTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
  finally { btn.disabled = false; btn.innerHTML = `+ ${t('startTracker')}`; }
}

async function loadBookingTrackers() {
  if (!API_URL) return;
  try {
    const r = await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/accommodations/booking');
    const trackers = await r.json();
    renderBookingTrackers(trackers);
  } catch(e) {}
}

function renderBookingTrackers(trackers) {
  const el = document.getElementById('bk-trackerList');
  if (!el) return;
  if (!trackers.length) { el.innerHTML = `<div style="color:var(--muted);font-size:.78rem;padding:.4rem 0">${t('bookingNoTrackers')}</div>`; return; }
  el.innerHTML = trackers.map(tr => {
    const snap = tr.latest_snapshot;
    const priceStr = snap?.total_price ? `${snap.total_price.toFixed(2)} €/Nacht` : '–';
    const hotel = snap?.hotel_name ? ` — ${snap.hotel_name}` : '';
    return `<div class="tracker-item">
      <div class="tracker-header">
        <div class="tracker-route">🏨 ${tr.destination}</div>
        <div class="tracker-price ${snap?'':'stale'}">${priceStr}</div>
      </div>
      <div class="tracker-meta">
        <span>${tr.checkin_date} → ${tr.checkout_date}</span>
        <span>${tr.adults} ${t('adultShort')}, ${tr.rooms} Zi.</span>
        <span class="badge badge-ok">${tr.source}</span>
        ${hotel ? `<span style="font-style:italic">${hotel}</span>` : ''}
      </div>
      <div class="tracker-actions">
        <button class="btn-scrape" onclick="scrapeBookingTracker(${tr.id})">⟳ ${t('current')}</button>
        <button class="btn-sm btn-danger" onclick="deleteBookingTracker(${tr.id})">✕</button>
      </div>
    </div>`;
  }).join('');
}

async function scrapeBookingTracker(id) {
  const serpKey = localStorage.getItem('s-serpApiKey') || '';
  toast(t('bookingSearching'), 'warning');
  try {
    const r = await fetch(`${localStorage.getItem('apiUrl')||API_URL}/api/accommodations/booking/${id}/scrape?api_key=${encodeURIComponent(serpKey)}`, { method: 'POST' });
    const data = await r.json();
    const snap = data.snapshot;
    if (snap?.total_price) toast(`${t('current')}: ${snap.total_price.toFixed(2)} €/Nacht${snap.hotel_name?' — '+snap.hotel_name:''}`, 'success');
    else toast(`Status: ${snap?.status} — ${snap?.error_message || ''}`, 'warning');
    loadBookingTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

async function deleteBookingTracker(id) {
  if (!confirm(t('deleteConfirm'))) return;
  try {
    await fetch(`${localStorage.getItem('apiUrl')||API_URL}/api/accommodations/booking/${id}`, { method: 'DELETE' });
    toast(t('deleted'), 'success'); loadBookingTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

// ── Toast ──────────────────────────────────────────────
function toast(msg, type='success') {
  const c = document.getElementById('toastContainer');
  const icons = { success:'✓', error:'✕', warning:'⚠' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]||'•'}</span> ${msg}`;
  c.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ── Dashboard ─────────────────────────────────────────

function loadDashboard() {
  loadDashTrackers();
  loadDashBudget();
  loadDashTrips();
}

async function loadDashTrackers() {
  const el = document.getElementById('dash-tracker-list');
  const countEl = document.getElementById('dash-tracker-count');
  if (!API_URL) {
    if (countEl) countEl.textContent = '0';
    return;
  }
  try {
    const trackers = await api('/api/trackers');
    const active = trackers.filter(t => t.active);
    if (countEl) countEl.textContent = active.length;

    if (!active.length) {
      el.innerHTML = `<div style="color:var(--sub);font-size:.8rem">${t('noTrackersYet')}</div>`;
      return;
    }

    el.innerHTML = active.map(tr => {
      const snap = tr.latest_snapshot;
      const price = snap?.total_price ? snap.total_price.toFixed(2) + ' €' : '–';
      const date  = snap?.fetched_at ? snap.fetched_at.slice(0,10) : '';
      return `<div class="dash-tracker-card" onclick="navigate('ryanair');setTimeout(()=>selectTracker(${tr.id}),200)">
        <div>
          <div class="dash-tracker-route">${tr.origin} → ${tr.destination}</div>
          <div class="dash-tracker-meta">${tr.outbound_date}${tr.return_date?' ⇄ '+tr.return_date:''} · ${date?t('lastChecked')+': '+date:''}</div>
        </div>
        <div class="dash-tracker-price">${price}</div>
      </div>`;
    }).join('');
  } catch(e) {
    if (el) el.innerHTML = `<div style="color:var(--sub);font-size:.78rem">⚠ ${e.message}</div>`;
  }
}

function loadDashBudget() {
  const total     = parseFloat(localStorage.getItem('ws-budget') || '0');
  const tripsList = JSON.parse(localStorage.getItem('ws-trips') || '[]');
  const spent     = tripsList.reduce((s, tr) => s + tr.cost, 0);
  const remaining = Math.max(0, total - spent);
  const pct       = total > 0 ? Math.min(100, (spent / total) * 100) : 0;
  const circumference = 2 * Math.PI * 38; // r=38

  // Stats
  const totalEl     = document.getElementById('dash-budget-total');
  const remainingEl = document.getElementById('dash-budget-remaining');
  const pctEl       = document.getElementById('dash-budget-pct');
  const spentLabel  = document.getElementById('dash-budget-spent-label');

  if (totalEl)     totalEl.textContent     = total > 0 ? total.toFixed(0) + ' €' : '–';
  if (remainingEl) remainingEl.textContent = total > 0 ? remaining.toFixed(0) + ' €' : '–';
  if (pctEl)       pctEl.textContent       = total > 0 ? Math.round(pct) + '% ' + t('spent').toLowerCase() : '–';
  if (spentLabel)  spentLabel.textContent  = spent > 0 ? spent.toFixed(2) + ' € ' + t('spent').toLowerCase() : '–';

  // Donut
  const fill = document.getElementById('dash-donut-fill');
  if (fill) {
    const dashArray = (pct / 100) * circumference;
    fill.setAttribute('stroke-dasharray', `${dashArray} ${circumference - dashArray}`);
    fill.setAttribute('stroke', pct > 85 ? 'var(--red)' : pct > 60 ? 'var(--accent2)' : 'var(--accent)');
  }

  const spentEl     = document.getElementById('dash-spent');
  const remainEl    = document.getElementById('dash-remaining');
  const totalBudget = document.getElementById('dash-total-budget');
  if (spentEl)     spentEl.textContent     = spent.toFixed(2) + ' €';
  if (remainEl)    remainEl.textContent    = remaining.toFixed(2) + ' €';
  if (totalBudget) totalBudget.textContent = total.toFixed(2) + ' €';
}

function loadDashTrips() {
  const tripsList = JSON.parse(localStorage.getItem('ws-trips') || '[]');
  const today = new Date().toISOString().slice(0,10);

  const upcoming  = tripsList.filter(tr => tr.date >= today);
  const completed = tripsList.filter(tr => tr.date <  today);

  const upEl = document.getElementById('dash-upcoming-list');
  const coEl = document.getElementById('dash-completed-list');

  if (upEl) {
    upEl.innerHTML = upcoming.length
      ? upcoming.map(tr => `
        <div class="trip-card">
          <div class="trip-card-icon">✈️</div>
          <div class="trip-card-info">
            <div class="trip-card-name">${tr.name}</div>
            <div class="trip-card-date">${tr.date}</div>
          </div>
          <div class="trip-card-cost">${tr.cost.toFixed(2)} €</div>
        </div>`).join('')
      : `<div style="color:var(--sub);font-size:.8rem">${t('noUpcomingTrips')}</div>`;
  }

  if (coEl) {
    // Load from Dawarich detected trips if available
    if (API_URL) {
      api('/api/dawarich/trips?limit=5').then(trips => {
        if (trips && trips.length) {
          coEl.innerHTML = trips.map(tr => {
            const loc = [tr.location_name, tr.country].filter(Boolean).join(', ') || `${tr.lat},${tr.lon}`;
            return `<div class="trip-card" style="cursor:pointer" onclick="navigate('journal')">
              <div class="trip-card-icon">✅</div>
              <div class="trip-card-info">
                <div class="trip-card-name">${loc}</div>
                <div class="trip-card-date">${tr.start_date} · ${tr.nights} ${t('tripNights')}</div>
              </div>
            </div>`;
          }).join('');
        } else if (completed.length) {
          coEl.innerHTML = completed.map(tr => `
            <div class="trip-card" style="opacity:.7">
              <div class="trip-card-icon">✅</div>
              <div class="trip-card-info">
                <div class="trip-card-name">${tr.name}</div>
                <div class="trip-card-date">${tr.date}</div>
              </div>
              <div class="trip-card-cost">${tr.cost.toFixed(2)} €</div>
            </div>`).join('');
        } else {
          coEl.innerHTML = `<div style="color:var(--sub);font-size:.8rem">${t('noCompletedTrips')}</div>`;
        }
      }).catch(() => {
        coEl.innerHTML = `<div style="color:var(--sub);font-size:.8rem">${t('noCompletedTrips')}</div>`;
      });
    } else {
      coEl.innerHTML = `<div style="color:var(--sub);font-size:.8rem">${t('noCompletedTrips')}</div>`;
    }
  }
}

// ── Field Guide ────────────────────────────────────────

function openFieldGuide() {
  // Apply translations to FAQ answers
  document.querySelectorAll('.faq-answer[data-i18n]').forEach(el => {
    el.textContent = t(el.getAttribute('data-i18n'));
  });
  document.querySelectorAll('.faq-question[data-i18n]').forEach(el => {
    el.textContent = t(el.getAttribute('data-i18n'));
  });
  document.getElementById('fieldGuideBackdrop').classList.add('open');
  document.body.style.overflow = 'hidden';
  if (window.innerWidth < 900) closeSidebar();
}

function closeFieldGuide(e) {
  if (e && e.target !== document.getElementById('fieldGuideBackdrop')) return;
  document.getElementById('fieldGuideBackdrop').classList.remove('open');
  document.body.style.overflow = '';
}

// ── Onboarding ─────────────────────────────────────────

let obStep = 1;

function checkOnboarding() {
  const hasUrl = localStorage.getItem('apiUrl');
  const seen   = localStorage.getItem('ws-onboarding-done');
  if (!hasUrl && !seen) {
    document.getElementById('onboardingBackdrop').classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeOnboarding() {
  localStorage.setItem('ws-onboarding-done', '1');
  document.getElementById('onboardingBackdrop').classList.remove('open');
  document.body.style.overflow = '';
}

function obNext() {
  if (obStep === 1) {
    const url = document.getElementById('ob-url').value.trim().replace(/\/$/, '');
    if (url) {
      API_URL = url;
      localStorage.setItem('apiUrl', url);
      const apiInput = document.getElementById('apiUrlInput');
      if (apiInput) apiInput.value = url;
      checkApiStatus();
    }
  }
  if (obStep >= 3) { closeOnboarding(); loadDashboard(); return; }
  obStep++;
  updateObStep();
}

function obBack() {
  if (obStep <= 1) return;
  obStep--;
  updateObStep();
}

function updateObStep() {
  [1,2,3].forEach(i => {
    document.getElementById('ob-panel-'+i).style.display = i===obStep ? 'block' : 'none';
    const stepEl = document.getElementById('ob-step-'+i);
    stepEl.classList.remove('active','done');
    if (i < obStep)  stepEl.classList.add('done');
    if (i === obStep) stepEl.classList.add('active');
  });
  document.getElementById('ob-back').style.display = obStep > 1 ? 'inline-flex' : 'none';
  document.getElementById('ob-next').textContent   = obStep >= 3 ? '🎒 ' + t('startTracker') : t('refresh') + ' →';
}



// ── Travel Journal ────────────────────────────────────

let allExpenses = [];

async function loadJournalTrips() {
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
      ? `${trips.length} ${trips.length === 1 ? 'Reise' : 'Reisen'} erkannt`
      : '';
  } catch(e) {
    el.innerHTML = `<div class="journal-empty"><div class="journal-empty-icon">⚠️</div><div class="journal-empty-text">${e.message}</div></div>`;
  }
}

function renderJournalTrips(trips) {
  const el = document.getElementById('journal-trip-list');
  if (!trips.length) {
    el.innerHTML = `<div class="journal-empty">
      <div class="journal-empty-icon">🗺️</div>
      <div class="journal-empty-text">${t('noJournalTrips')}</div>
    </div>`;
    return;
  }

  el.innerHTML = trips.map(trip => {
    const loc = [trip.location_name, trip.country].filter(Boolean).join(', ') || `${trip.lat},${trip.lon}`;
    const nights = trip.nights;
    const nightsStr = `${nights} ${nights === 1 ? t('tripNights').slice(0,-1) : t('tripNights')}`;
    const mapsUrl = `https://www.google.com/maps?q=${trip.lat},${trip.lon}`;

    return `<div class="journal-trip-card">
      <div class="journal-trip-pin">📍</div>
      <div class="journal-trip-body">
        <div class="journal-trip-name">${loc || '?'}</div>
        <div class="journal-trip-dates">
          ${trip.start_date} → ${trip.end_date}
        </div>
        <span class="journal-trip-nights">${nightsStr}</span>
        <div class="journal-trip-actions">
          <a href="${mapsUrl}" target="_blank" class="btn-scrape" style="text-decoration:none;font-size:.68rem">
            🗺 Maps
          </a>
          <button class="btn-sm btn-danger" onclick="deleteJournalTrip(${trip.id})">✕</button>
        </div>
      </div>
    </div>`;
  }).join('');
}

async function syncJournal() {
  const btn = document.getElementById('journal-sync-btn');
  if (!API_URL) { toast(t('missingUrl'), 'warning'); return; }

  let dawarichUrl   = localStorage.getItem('s-dawarichUrl')   || '';
  let dawarichToken = localStorage.getItem('s-dawarichToken') || '';
  let homeLat       = parseFloat(localStorage.getItem('s-homeLat') || '');
  let homeLon       = parseFloat(localStorage.getItem('s-homeLon') || '');

  // Koordinaten vom Server nachladen wenn localStorage leer oder ungültig
  if (!dawarichUrl || !dawarichToken || isNaN(homeLat) || isNaN(homeLon) || (homeLat === 0 && homeLon === 0)) {
    try {
      const serverSettings = await api('/api/settings');
      if (!dawarichUrl)            dawarichUrl   = serverSettings.dawarich_url   || '';
      if (!dawarichToken)          dawarichToken = serverSettings.dawarich_token || '';
      if (isNaN(homeLat) || homeLat === 0) homeLat = parseFloat(serverSettings.home_lat || '');
      if (isNaN(homeLon) || homeLon === 0) homeLon = parseFloat(serverSettings.home_lon || '');
    } catch(e) { /* ignorieren, weiter mit was wir haben */ }
  }

  if (!dawarichUrl || !dawarichToken) {
    toast(t('dawarichError') + ': URL/Token fehlen — Einstellungen öffnen', 'warning');
    openSettings(); return;
  }
  if (isNaN(homeLat) || isNaN(homeLon) || (homeLat === 0 && homeLon === 0)) {
    toast(t('dawarichError') + ': Home-Koordinaten fehlen — Einstellungen öffnen', 'warning');
    openSettings(); return;
  }

  if (btn) { btn.disabled = true; btn.innerHTML = `<span class="spinner"></span> ${t('dawarichSyncing')}`; }
  toast(t('dawarichSyncing'), 'warning');

  try {
    const result = await api('/api/dawarich/sync', {
      method: 'POST',
      body: JSON.stringify({
        dawarich_url:   dawarichUrl,
        dawarich_token: dawarichToken,
        home_lat:       homeLat,
        home_lon:       homeLon,
      }),
    });

    const bar  = document.getElementById('journal-sync-bar');
    const info = document.getElementById('journal-sync-info');
    if (bar)  bar.style.display = 'flex';
    // trips_saved ist nur vorhanden wenn trips_detected > 0
    const saved = result.trips_saved ?? result.trips_detected ?? 0;
    if (info) info.innerHTML = `<strong>${result.points_loaded ?? 0}</strong> Punkte geladen · <strong>${result.trips_detected ?? 0}</strong> Reisen erkannt · <strong>${saved}</strong> gespeichert`;

    toast(`${t('dawarichSynced')}: ${result.trips_detected ?? 0} Reisen`, 'success');
    loadJournalTrips();
    loadDashboard();

  } catch(e) {
    toast(`${t('dawarichError')}: ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = `🧭 ${t('syncNow')}`; }
  }
}

async function deleteJournalTrip(id) {
  if (!confirm(t('deleteConfirm'))) return;
  try {
    await api(`/api/dawarich/trips/${id}`, { method: 'DELETE' });
    toast(t('deleted'), 'success');
    loadJournalTrips();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

// ── Expense Table ─────────────────────────────────────

async function loadExpenses() {
  const wrap  = document.getElementById('expense-table-wrap');
  const sumEl = document.getElementById('expense-summary');
  const filEl = document.getElementById('expense-filters');
  if (!API_URL) return;

  const actualUrl      = localStorage.getItem('s-actualUrl')      || '';
  const actualPassword = localStorage.getItem('s-actualPassword')  || '';
  const actualFile     = localStorage.getItem('s-actualFile')       || '';
  const categories     = localStorage.getItem('s-travelCategories') || '';
  const yearSel        = document.getElementById('expense-year-filter');
  const year           = yearSel?.value ? parseInt(yearSel.value) : null;

  if (!actualUrl || !actualPassword || !actualFile) {
    wrap.innerHTML = `<div class="expense-loading">⚙ ActualBudget ${t('missingUrl')} — ${t('settings')} öffnen</div>`;
    return;
  }

  wrap.innerHTML = `<div class="expense-loading"><span class="spinner"></span> ${t('expenseSyncing')}</div>`;

  try {
    const catList = categories.split(',').map(c => c.trim()).filter(Boolean);
    const result = await api('/api/budget/actual/expenses', {
      method: 'POST',
      body: JSON.stringify({
        base_url:       actualUrl,
        password:       actualPassword,
        budget_file:    actualFile,
        category_names: catList,
        year,
      }),
    });

    allExpenses = result.transactions || [];

    // Summary
    document.getElementById('expense-total').textContent = (result.total_spent||0).toFixed(2) + ' €';
    document.getElementById('expense-year').textContent  = result.year || new Date().getFullYear();
    document.getElementById('expense-count').textContent = allExpenses.length;
    if (sumEl) sumEl.style.display = 'grid';

    // Populate category filter
    const catFilter = document.getElementById('expense-cat-filter');
    const cats = [...new Set(allExpenses.map(tx => tx.category).filter(Boolean))].sort();
    catFilter.innerHTML = `<option value="">${t('expenseCategory')} (${t('total')})</option>` +
      cats.map(c => `<option value="${c}">${c}</option>`).join('');
    if (filEl) filEl.style.display = 'flex';

    // Year filter options
    const years = [...new Set(allExpenses.map(tx => tx.date?.slice(0,4)).filter(Boolean))].sort().reverse();
    if (yearSel) {
      yearSel.innerHTML = `<option value="">Dieses Jahr</option>` +
        years.map(y => `<option value="${y}"${year==y?'selected':''}>${y}</option>`).join('');
    }

    renderExpenseTable(allExpenses);

  } catch(e) {
    wrap.innerHTML = `<div class="expense-loading">❌ ${e.message}</div>`;
    if (sumEl) sumEl.style.display = 'none';
  }
}

function filterExpenses() {
  const search  = document.getElementById('expense-search')?.value.toLowerCase() || '';
  const cat     = document.getElementById('expense-cat-filter')?.value || '';
  const filtered = allExpenses.filter(tx => {
    const matchSearch = !search || (tx.payee||'').toLowerCase().includes(search) || (tx.notes||'').toLowerCase().includes(search);
    const matchCat    = !cat    || tx.category === cat;
    return matchSearch && matchCat;
  });
  renderExpenseTable(filtered);
}

function renderExpenseTable(expenses) {
  const wrap = document.getElementById('expense-table-wrap');
  if (!expenses.length) {
    wrap.innerHTML = `<div class="expense-loading" data-i18n="expenseNoData">${t('expenseNoData')}</div>`;
    return;
  }

  wrap.innerHTML = `<div class="expense-table-wrap">
    <table class="expense-table">
      <thead><tr>
        <th data-i18n="expenseDate">${t('expenseDate')}</th>
        <th data-i18n="expensePayee">${t('expensePayee')}</th>
        <th data-i18n="expenseCategory">${t('expenseCategory')}</th>
        <th data-i18n="expenseAmount" style="text-align:right">${t('expenseAmount')}</th>
      </tr></thead>
      <tbody>
        ${expenses.map(tx => {
          const amtClass = tx.amount < 0 ? 'expense-amount-neg' : 'expense-amount-pos';
          const amt = Math.abs(tx.amount).toFixed(2);
          const sign = tx.amount < 0 ? '−' : '+';
          return `<tr>
            <td>${tx.date||'–'}</td>
            <td>${tx.payee||'–'}<br><span style="font-size:.65rem;color:var(--sub)">${tx.notes||''}</span></td>
            <td><span class="badge badge-fallback" style="font-size:.6rem">${tx.category||'–'}</span></td>
            <td style="text-align:right"><span class="${amtClass}">${sign} ${amt} €</span></td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>
  </div>`;
}



// ─── Window-Bindungen für HTML inline-Events ─────────────────────────────────
// Damit onclick="navigate(...)" und alle anderen Handler weiterhin funktionieren.
window.navigate            = navigate;
window.toggleSidebar       = toggleSidebar;
window.closeSidebar        = closeSidebar;
window.api                 = api;
window.checkApiStatus      = checkApiStatus;
window.t                   = t;
window.setLang             = setLang;
window.applyTranslations   = applyTranslations;
window.loadLocale          = loadLocale;
window.fmt                 = fmt;
window.toast               = toast;
window.addTracker          = addTracker;
window.loadTrackers        = loadTrackers;
window.renderTrackers      = renderTrackers;
window.selectTracker       = selectTracker;
window.scrapeNow           = scrapeNow;
window.deleteTracker       = deleteTracker;
window.togglePause         = togglePause;
window.toggleBag           = toggleBag;
window.checkDawarich       = checkDawarich;
window.generateIdeas       = generateIdeas;
window.renderRecommendations = renderRecommendations;
window.toggleActualSync    = toggleActualSync;
window.addTrip             = addTrip;
window.syncActualBudget    = syncActualBudget;
window.updateBudget        = updateBudget;
window.renderBudget        = renderBudget;
window.removeTrip          = removeTrip;
window.openSettings        = openSettings;
window.closeSettings       = closeSettings;
window.loadSerpApiQuota    = loadSerpApiQuota;
window.backdropClick       = backdropClick;
window.switchTab           = switchTab;
window.toggleTheme         = toggleTheme;
window.saveSettings        = saveSettings;
window.addGFTracker        = addGFTracker;
window.loadGFTrackers      = loadGFTrackers;
window.renderGFTrackers    = renderGFTrackers;
window.scrapeGFTracker     = scrapeGFTracker;
window.deleteGFTracker     = deleteGFTracker;
window.addHomairTracker    = addHomairTracker;
window.loadHomairTrackers  = loadHomairTrackers;
window.renderHomairTrackers = renderHomairTrackers;
window.scrapeHomairTracker = scrapeHomairTracker;
window.deleteHomairTracker = deleteHomairTracker;
window.addBookingTracker   = addBookingTracker;
window.loadBookingTrackers = loadBookingTrackers;
window.renderBookingTrackers = renderBookingTrackers;
window.scrapeBookingTracker = scrapeBookingTracker;
window.deleteBookingTracker = deleteBookingTracker;
window.loadDashboard       = loadDashboard;
window.loadDashTrackers    = loadDashTrackers;
window.loadDashBudget      = loadDashBudget;
window.loadDashTrips       = loadDashTrips;
window.openFieldGuide      = openFieldGuide;
window.closeFieldGuide     = closeFieldGuide;
window.checkOnboarding     = checkOnboarding;
window.closeOnboarding     = closeOnboarding;
window.obNext              = obNext;
window.obBack              = obBack;
window.updateObStep        = updateObStep;
window.loadJournalTrips    = loadJournalTrips;
window.renderJournalTrips  = renderJournalTrips;
window.syncJournal         = syncJournal;
window.deleteJournalTrip   = deleteJournalTrip;
window.loadExpenses        = loadExpenses;
window.filterExpenses      = filterExpenses;
window.renderExpenseTable  = renderExpenseTable;
