/**
 * app/ryanair.js — Ryanair price tracker
 *
 * Handles the full lifecycle of a Ryanair tracker:
 *   - Form: toggleBag(), addTracker()
 *   - List: loadTrackers(), renderTrackers()
 *   - Detail: selectTracker(), renderStats(), renderChart() (Chart.js), renderTable()
 *   - Actions: scrapeNow(), deleteTracker(), togglePause()
 *   - Discover / AI: checkDawarich(), generateIdeas(), renderRecommendations()
 *
 * Chart.js is loaded from CDN in index.html and available as the global `Chart`.
 * The chart instance is tracked in state.js (priceChart) and destroyed before re-render
 * to avoid "canvas already in use" errors.
 */
// frontend/js/app/ryanair.js
import { api } from '../core/api.js';
import { t } from '../ui/i18n.js';
import { toast } from '../ui/toast.js';
import { API_URL, currentLang, selectedTrackerId, selectedBags,
         setSelectedTrackerId, setPriceChart, setSelectedBags } from '../core/state.js';

export function toggleBag(type) {
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

export async function addTracker() {
  const btn     = document.getElementById('addBtn');
  const origin  = document.getElementById('origin').value.trim().toUpperCase();
  const dest    = document.getElementById('destination').value.trim().toUpperCase();
  const outDate = document.getElementById('outboundDate').value;
  const retDate = document.getElementById('returnDate').value;
  if (!origin || origin.length !== 3) { toast(t('invalidOrigin'), 'error'); return; }
  if (!dest   || dest.length   !== 3) { toast(t('invalidDest'),   'error'); return; }
  if (!outDate)                        { toast(t('missingDate'),   'error'); return; }
  if (!API_URL)                        { toast(t('missingUrl'), 'warning'); return; }
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> ${t('creatingTracker')}`;
  try {
    await api('/api/trackers', { method: 'POST', body: JSON.stringify({
      origin, destination: dest, outbound_date: outDate, return_date: retDate || null,
      adults:    parseInt(document.getElementById('adults').value),
      children:  parseInt(document.getElementById('children').value),
      baggage:   [...selectedBags].map(type => ({ type, per_person: true })),
      seat_cost: parseFloat(document.getElementById('seatCost').value) || 0,
    })});
    toast(`${t('trackerAdded')} ✓ ${origin} → ${dest}`, 'success');
    document.getElementById('origin').value      = '';
    document.getElementById('destination').value = '';
    document.getElementById('seatCost').value    = '0';
    setSelectedBags(new Set());
    ['10kg','20kg','23kg'].forEach(tp => {
      document.getElementById('bag-'+tp).classList.remove('selected');
      document.getElementById('chk-'+tp).textContent = '';
    });
    loadTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
  finally { btn.disabled = false; btn.innerHTML = `+ ${t('startTracker')}`; }
}

export async function loadTrackers() {
  const el = document.getElementById('trackerList');
  try { renderTrackers(await api('/api/trackers')); }
  catch(e) { el.innerHTML = `<div style="color:var(--red);font-size:.76rem">⚠ ${e.message}</div>`; }
}

export function renderTrackers(trackers) {
  const el = document.getElementById('trackerList');
  if (!trackers.length) {
    el.innerHTML = `<div style="color:var(--muted);font-size:.78rem;padding:.4rem 0">${t('noTrackers')}</div>`;
    return;
  }
  el.innerHTML = trackers.map(tr => {
    const snap        = tr.latest_snapshot;
    const priceStr    = snap?.total_price ? `${snap.total_price.toFixed(2)} €` : '–';
    const statusBadge = !tr.active
      ? `<span class="badge badge-paused">${t('paused')}</span>`
      : snap?.status === 'ok'
        ? (snap.baggage_fallback
            ? `<span class="badge badge-fallback">~${t('estimate')}</span>`
            : '<span class="badge badge-ok">Live</span>')
        : snap?.status === 'blocked'
          ? `<span class="badge badge-blocked">${t('blocked')}</span>` : '';
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

export async function selectTracker(id) {
  setSelectedTrackerId(id); loadTrackers();
  const container = document.getElementById('chartContainer');
  const empty     = document.getElementById('chartEmpty');
  const tableCard = document.getElementById('tableCard');
  container.style.display = 'none'; empty.style.display = 'none';
  const card    = document.getElementById('chartCard');
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
    document.getElementById('chartTitle').textContent =
      `${tr.origin} → ${tr.destination}  ${tr.outbound_date}${tr.return_date?' ⇄ '+tr.return_date:''}`;
    renderStats(data); renderChart(data); renderTable(data.snapshots);
    container.style.display = 'block'; tableCard.style.display = 'block';
    if (window.innerWidth < 900) card.scrollIntoView({ behavior:'smooth', block:'start' });
  } catch(e) {
    card.removeChild(overlay); empty.style.display = 'flex';
    toast(`${t('error')}: ${e.message}`, 'error');
  }
}

export function renderStats(data) {
  const prices = data.total_prices.filter(p => p !== null);
  if (!prices.length) return;
  const min  = Math.min(...prices);
  const cur  = prices[prices.length-1];
  const prev = prices.length > 1 ? prices[prices.length-2] : cur;
  const diff = cur - prev;
  const ds   = (diff >= 0 ? '+' : '') + diff.toFixed(2) + ' €';
  document.getElementById('chartStats').innerHTML = `
    <div class="stat"><div class="stat-label">${t('current')}</div><div class="stat-value">${cur.toFixed(2)} €</div><div style="font-size:.6rem;color:var(--sub);margin-top:.18rem">${data.labels[data.labels.length-1]}</div></div>
    <div class="stat"><div class="stat-label">${t('lowestPrice')}</div><div class="stat-value green">${min.toFixed(2)} €</div></div>
    <div class="stat"><div class="stat-label">${t('change')}</div><div class="stat-value ${diff>0?'red':diff<0?'green':''}">${ds}</div></div>`;
}

export function renderChart(data) {
  // Destroy existing chart if present
  const canvas = document.getElementById('priceChart');
  if (canvas._chartInstance) { canvas._chartInstance.destroy(); }
  const chart = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels: data.labels, datasets: [
      { label:t('total'),   data:data.total_prices,   borderColor:'#ff5533', backgroundColor:'rgba(255,85,51,.08)', borderWidth:2, pointRadius:4, pointHoverRadius:6, pointBackgroundColor:'#ff5533', fill:true, tension:.3 },
      { label:t('tickets'), data:data.flight_prices,  borderColor:'#ff8c00', backgroundColor:'transparent', borderWidth:1.5, borderDash:[4,3], pointRadius:3, fill:false, tension:.3 },
      { label:t('baggage'), data:data.baggage_prices, borderColor:'#7a7d88', backgroundColor:'transparent', borderWidth:1.5, borderDash:[2,4], pointRadius:2, fill:false, tension:.3 },
      { label:t('seat'),    data:data.seat_prices,    borderColor:'#8b5cf6', backgroundColor:'transparent', borderWidth:1.5, borderDash:[3,5], pointRadius:2, fill:false, tension:.3 },
    ]},
    options: {
      responsive:true, maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
      plugins: {
        legend:  { position:'top', labels:{color:'#7a7d88',font:{family:"'Space Mono',monospace",size:10},boxWidth:12,boxHeight:2,padding:12} },
        tooltip: { backgroundColor:'#141519',borderColor:'#2a2b30',borderWidth:1,titleColor:'#e8e9ec',bodyColor:'#7a7d88',padding:10,callbacks:{label:ctx=>` ${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(2)??'–'} €`} }
      },
      scales: {
        x: { grid:{color:'rgba(42,43,48,.5)'}, ticks:{color:'#7a7d88',font:{family:"'Space Mono'",size:9},maxRotation:45} },
        y: { grid:{color:'rgba(42,43,48,.5)'}, ticks:{color:'#7a7d88',font:{family:"'Space Mono'",size:9},callback:v=>v+' €'} }
      }
    }
  });
  canvas._chartInstance = chart;
  setPriceChart(chart);
}

export function renderTable(snaps) {
  document.getElementById('snapshotTable').innerHTML = [...snaps].reverse().slice(0,30).map(s => {
    const st    = s.status==='ok'
      ? (s.baggage_fallback ? `<span class="badge badge-fallback">~${t('estimate')}</span>` : '<span class="badge badge-ok">✓</span>')
      : `<span class="badge badge-blocked">${s.status}</span>`;
    const seatP = s.seat_price != null && s.seat_price > 0 ? s.seat_price.toFixed(2)+' €' : '–';
    return `<tr>
      <td>${(s.fetched_at||'').slice(0,10)}</td><td>${s.outbound_flight||'–'}</td><td>${s.return_flight||'–'}</td>
      <td>${s.flight_price!=null?s.flight_price.toFixed(2)+' €':'–'}</td>
      <td>${s.baggage_price!=null?s.baggage_price.toFixed(2)+' €':'–'}</td>
      <td>${seatP}</td>
      <td style="color:var(--green);font-weight:700">${s.total_price!=null?s.total_price.toFixed(2)+' €':'–'}</td>
      <td>${st}</td></tr>`;
  }).join('');
}

export async function scrapeNow(id) {
  toast(t('scrapeStarted'), 'warning');
  try {
    const result = await api(`/api/trackers/${id}/scrape`, { method:'POST' });
    const snap   = result.snapshot;
    if (snap?.total_price) toast(`${t('current')}: ${snap.total_price.toFixed(2)} €${snap.baggage_fallback?` (~${t('estimate')})`:''}`,'success');
    else toast(`${t('status')}: ${snap?.status||'?'}`, 'warning');
    loadTrackers();
    if (selectedTrackerId===id) selectTracker(id);
  } catch(e) { toast(`${t('scrapeError')}: ${e.message}`, 'error'); }
}

export async function deleteTracker(id) {
  if (!confirm(t('deleteConfirm'))) return;
  try {
    await api(`/api/trackers/${id}`, { method:'DELETE' });
    toast(t('deleted'), 'success');
    if (selectedTrackerId===id) {
      setSelectedTrackerId(null);
      document.getElementById('chartContainer').style.display = 'none';
      document.getElementById('chartEmpty').style.display     = 'flex';
      document.getElementById('tableCard').style.display      = 'none';
    }
    loadTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

export async function togglePause(id, currentlyActive) {
  try {
    await api(`/api/trackers/${id}/toggle?active=${!currentlyActive}`, { method:'PATCH' });
    toast(currentlyActive ? t('paused') : t('activated'), 'success');
    loadTrackers();
  } catch(e) { toast(`${t('error')}: ${e.message}`, 'error'); }
}

export function checkDawarich(on) {
  const notice = document.getElementById('discoverDawarichNotice');
  if (on && !localStorage.getItem('s-dawarichUrl')) {
    notice.style.display = 'block';
    document.getElementById('discoverDawarich').checked = false;
  } else {
    notice.style.display = 'none';
  }
}

export async function generateIdeas() {
  const q = document.getElementById('discoverQuery').value.trim();
  if (!q) { toast(t('discoverNoQuery'), 'warning'); return; }
  const provider = document.getElementById('discoverProvider')?.value || 'gemini';
  const localKey = provider === 'openai'
    ? (localStorage.getItem('s-openaiKey') || '')
    : (localStorage.getItem('s-geminiKey') || '');
  const results    = document.getElementById('discoverResults');
  results.innerHTML = '<span class="spinner"></span> ' + t('discoverGenerating');
  try {
    const resp = await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/discover', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q, provider, api_key: localKey || undefined, lang: currentLang, exclude_places: [] }),
    });
    const data = await resp.json();
    if (data.error) { results.textContent = '❌ ' + data.error; return; }
    if (data.recommendations && Array.isArray(data.recommendations)) {
      results.innerHTML = renderRecommendations(data.recommendations);
    } else if (data.raw) {
      results.innerHTML = `<pre style="white-space:pre-wrap;font-size:.75rem;text-align:left">${data.raw}</pre>`;
    } else { results.textContent = '⚠ Unerwartetes Antwortformat'; }
  } catch(e) { results.textContent = '❌ ' + e.message; toast(t('error') + ': ' + e.message, 'error'); }
}

export function renderRecommendations(recs) {
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
