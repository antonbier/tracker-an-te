<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { apiUrl } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';
  import { t } from '$lib/i18n.js';

  let activeTab = $state('ryanair');

  // ── Shared helpers ────────────────────────────────────────────────────────
  const today = new Date();
  const d30 = new Date(today); d30.setDate(d30.getDate() + 30);
  const d37 = new Date(today); d37.setDate(d37.getDate() + 37);
  function fmt(d) { return d.toISOString().slice(0,10); }
  const inputCls   = 'w-full px-3 py-2 rounded-xl border text-sm';
  const inputStyle = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';

  // Price chart accordion — map of trackerId → { open, history, loading }
  let chartState = $state({});

  async function toggleChart(trackerType, trackerId) {
    const key = `${trackerType}-${trackerId}`;
    if (!chartState[key]) chartState[key] = { open: false, history: [], loading: false };
    chartState[key].open = !chartState[key].open;
    if (chartState[key].open && chartState[key].history.length === 0) {
      chartState[key].loading = true;
      try {
        const res = await api(`/api/prices/history/${trackerType}/${trackerId}`);
        chartState[key].history = res.history || [];
      } catch { chartState[key].history = []; }
      chartState[key].loading = false;
    }
  }

  // Wish-price editing — map of key → { editing, value, saving }
  let wishState = $state({});

  async function saveWishPrice(trackerType, trackerId, tableName, newPrice) {
    const key = `${trackerType}-${trackerId}`;
    wishState[key] = { ...wishState[key], saving: true };
    try {
      await api(`/api/prices/wish/${tableName}/${trackerId}`, {
        method: 'PUT',
        body: JSON.stringify({ wish_price: newPrice === '' ? null : parseFloat(newPrice) })
      });
      toast('Wunschpreis gespeichert ✓', 'success');
      wishState[key] = { editing: false, value: newPrice, saving: false };
    } catch(e) { toast(e.message, 'error'); wishState[key] = { ...wishState[key], saving: false }; }
  }

  function priceTrend(current, prev) {
    if (!current || !prev) return null;
    return current < prev ? 'down' : current > prev ? 'up' : 'same';
  }

  function trendStyle(trend) {
    if (trend === 'down') return 'color:#16a34a;font-weight:700';
    if (trend === 'up')   return 'color:#dc2626;font-weight:700';
    return 'color:var(--ws-green);font-weight:700';
  }

  function trendIcon(trend) {
    if (trend === 'down') return '⬇️';
    if (trend === 'up')   return '⬆️';
    return '';
  }

  // ── Ryanair ───────────────────────────────────────────────────────────────
  let ryTrackers = $state([]);
  let ryLoading  = $state(true);
  let ryAdding   = $state(false);
  let ryOrigin   = $state('BGY');
  let ryDest     = $state('DUB');
  let ryOut      = $state(fmt(d30));
  let ryRet      = $state(fmt(d37));
  let ryAdults   = $state(2);
  let ryChildren = $state(0);
  let rySeat     = $state(0);
  let ryBags     = $state([]);
  const bagOptions = [
    { type: '10kg', label: '10 kg Check-in Koffer' },
    { type: '20kg', label: '20 kg Check-in Koffer' },
    { type: '23kg', label: '23 kg Koffer (Large)' },
  ];
  function toggleBag(t) { ryBags = ryBags.includes(t) ? ryBags.filter(b=>b!==t) : [...ryBags, t]; }

  async function loadRyanair() {
    if (!$apiUrl) { ryLoading=false; return; }
    try { ryTrackers = await api('/api/trackers'); } catch {}
    ryLoading = false;
  }
  async function addRyanair() {
    if (!ryOrigin||!ryDest||!ryOut) { toast($t('radarRequired') || 'Pflichtfelder ausfüllen','error'); return; }
    if (!$apiUrl) { toast($t('radarNoBackend'),'warning'); return; }
    ryAdding=true;
    try {
      await api('/api/trackers',{method:'POST',body:JSON.stringify({
        origin:ryOrigin.toUpperCase(),destination:ryDest.toUpperCase(),
        outbound_date:ryOut,return_date:ryRet||null,
        adults:ryAdults,children:ryChildren,
        baggage:ryBags.map(t=>({type:t,per_person:true})),
        seat_cost:parseFloat(rySeat)||0,
      })});
      toast('Tracker angelegt ✓','success');
      await loadRyanair();
    } catch(e) { toast(e.message,'error'); }
    ryAdding=false;
  }
  async function scrapeRy(id) {
    toast('Preis wird abgerufen…','warning');
    try {
      const r = await api(`/api/trackers/${id}/scrape`,{method:'POST'});
      toast(`${r.snapshot?.total_price?.toFixed(2)} €`,'success');
      await loadRyanair();
    } catch(e) { toast(e.message,'error'); }
  }
  async function deleteRy(id) {
    if (!confirm($t('delete') + '?')) return;
    await api(`/api/trackers/${id}`,{method:'DELETE'});
    await loadRyanair();
  }

  // ── Google Flights ────────────────────────────────────────────────────────
  let gfTrackers = $state([]);
  let gfLoading  = $state(false);
  let gfAdding   = $state(false);
  let gfOrigin   = $state('MUC');
  let gfDest     = $state('JFK');
  let gfOut      = $state(fmt(d30));
  let gfRet      = $state('');
  let gfAdults   = $state(2);
  let gfChildren = $state(0);

  async function loadGF() {
    if (!$apiUrl) return;
    gfLoading=true;
    try { gfTrackers = await api('/api/google-flights'); } catch {}
    gfLoading=false;
  }
  async function addGF() {
    if (!gfOrigin||!gfDest||!gfOut) { toast($t('radarRequired')||'Pflichtfelder ausfüllen','error'); return; }
    if (!$apiUrl) { toast($t('radarNoBackend'),'warning'); return; }
    const serpKey = browser ? localStorage.getItem('s-serpApiKey')||'' : '';
    if (!serpKey) { toast($t('radarNoKey'),'warning'); return; }
    gfAdding=true;
    try {
      await api('/api/google-flights',{method:'POST',body:JSON.stringify({
        origin:gfOrigin.toUpperCase(),destination:gfDest.toUpperCase(),
        outbound_date:gfOut,return_date:gfRet||null,
        adults:gfAdults,children:gfChildren,
      })});
      toast('Tracker angelegt ✓','success');
      await loadGF();
    } catch(e) { toast(e.message,'error'); }
    gfAdding=false;
  }
  async function scrapeGF(id) {
    toast('Google Flights wird abgefragt…','warning');
    try {
      const r = await api(`/api/google-flights/${id}/scrape`,{method:'POST'});
      const s = r.snapshot;
      const info = s?.airline ? ` — ${s.airline} ${s.departure_time??''}→${s.arrival_time??''}` : '';
      toast(`${s?.total_price?.toFixed(2)} €${info}`,'success');
      await loadGF();
    } catch(e) { toast(e.message,'error'); }
  }
  async function deleteGF(id) {
    if (!confirm($t('delete') + '?')) return;
    await api(`/api/google-flights/${id}`,{method:'DELETE'});
    await loadGF();
  }

  // ── Homair / Camping ──────────────────────────────────────────────────────
  let hmTrackers = $state([]);
  let hmLoading  = $state(false);
  let hmAdding   = $state(false);
  let hmRegion   = $state('cote-d-azur');
  let hmType     = $state('mobilheim-standard');
  let hmIn       = $state(fmt(d30));
  let hmOut2     = $state(fmt(d37));
  let hmAdults   = $state(2);
  let hmChildren = $state(0);
  const hmRegions = [
    {val:'cote-d-azur',label:"Côte d'Azur"},
    {val:'kroatien',label:'Kroatien'},
    {val:'toskana',label:'Toskana'},
    {val:'katalonien',label:'Katalonien'},
    {val:'languedoc',label:'Languedoc'},
    {val:'provence',label:'Provence'},
    {val:'venetien',label:'Venetien'},
  ];
  const hmTypes = [
    {val:'mobilheim-standard',label:'Mobilheim Standard'},
    {val:'mobilheim-premium',label:'Mobilheim Premium'},
    {val:'chalet',label:'Chalet'},
    {val:'stellplatz',label:'Stellplatz'},
  ];
  async function loadHM() {
    if (!$apiUrl) return;
    hmLoading=true;
    try { hmTrackers = await api('/api/accommodations/homair'); } catch {}
    hmLoading=false;
  }
  async function addHM() {
    if (!hmIn||!hmOut2) { toast('Datum fehlt','error'); return; }
    if (!$apiUrl) { toast($t('radarNoBackend'),'warning'); return; }
    hmAdding=true;
    try {
      await api('/api/accommodations/homair',{method:'POST',body:JSON.stringify({
        region:hmRegion,accommodation_type:hmType,
        checkin_date:hmIn,checkout_date:hmOut2,
        adults:hmAdults,children:hmChildren,
      })});
      toast('Tracker angelegt ✓','success');
      await loadHM();
    } catch(e) { toast(e.message,'error'); }
    hmAdding=false;
  }
  async function scrapeHM(id) {
    toast('Suche Campingplätze…','warning');
    try {
      const r = await api(`/api/accommodations/homair/${id}/scrape`,{method:'POST'});
      toast(`${r.snapshot?.total_price?.toFixed(2)} €`,'success');
      await loadHM();
    } catch(e) { toast(e.message,'error'); }
  }
  async function deleteHM(id) {
    if (!confirm($t('delete') + '?')) return;
    await api(`/api/accommodations/homair/${id}`,{method:'DELETE'});
    await loadHM();
  }

  // ── Booking / Hotel ───────────────────────────────────────────────────────
  let bkTrackers = $state([]);
  let bkLoading  = $state(false);
  let bkAdding   = $state(false);
  let bkDest     = $state('');
  let bkIn       = $state(fmt(d30));
  let bkOut2     = $state(fmt(d37));
  let bkAdults   = $state(2);
  let bkRooms    = $state(1);
  let bkSource   = $state('booking');
  async function loadBK() {
    if (!$apiUrl) return;
    bkLoading=true;
    try { bkTrackers = await api('/api/accommodations/booking'); } catch {}
    bkLoading=false;
  }
  async function addBK() {
    if (!bkDest||!bkIn||!bkOut2) { toast($t('radarRequired')||'Pflichtfelder ausfüllen','error'); return; }
    if (!$apiUrl) { toast($t('radarNoBackend'),'warning'); return; }
    bkAdding=true;
    try {
      await api('/api/accommodations/booking',{method:'POST',body:JSON.stringify({
        destination:bkDest,checkin_date:bkIn,checkout_date:bkOut2,
        adults:bkAdults,rooms:bkRooms,source:bkSource,
      })});
      toast('Tracker angelegt ✓','success');
      await loadBK();
    } catch(e) { toast(e.message,'error'); }
    bkAdding=false;
  }
  async function scrapeBK(id) {
    const serpKey = browser ? localStorage.getItem('s-serpApiKey')||'' : '';
    toast('Suche Unterkünfte…','warning');
    try {
      const r = await api(`/api/accommodations/booking/${id}/scrape?api_key=${encodeURIComponent(serpKey)}`,{method:'POST'});
      const s = r.snapshot;
      const hotel = s?.hotel_name ? ` — ${s.hotel_name}` : '';
      toast(`${s?.total_price?.toFixed(2)} €/Nacht${hotel}`,'success');
      await loadBK();
    } catch(e) { toast(e.message,'error'); }
  }
  async function deleteBK(id) {
    if (!confirm($t('delete') + '?')) return;
    await api(`/api/accommodations/booking/${id}`,{method:'DELETE'});
    await loadBK();
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  onMount(() => { loadRyanair(); });
  $effect(() => {
    if (activeTab==='gflights' && gfTrackers.length===0) loadGF();
    if (activeTab==='homair'   && hmTrackers.length===0) loadHM();
    if (activeTab==='booking'  && bkTrackers.length===0) loadBK();
  });

  const tabs = $derived([
    { id:'ryanair',  label:'🟠 ' + $t('radarRyanair') },
    { id:'gflights', label:'🔵 ' + $t('radarGoogle')  },
    { id:'homair',   label:'⛺ ' + $t('radarHomair')  },
    { id:'booking',  label:'🏨 ' + $t('radarBooking') },
  ]);
</script>

<!-- ── Page wrapper ── -->
<div class="space-y-4">

  <!-- ── Tab bar ── -->
  <div class="flex border-b overflow-x-auto" style="border-color:var(--ws-border)">
    {#each tabs as tab}
      <button onclick={() => activeTab = tab.id}
        class="px-4 py-2.5 text-xs font-semibold whitespace-nowrap shrink-0 transition-colors border-b-2"
        style={activeTab===tab.id
          ? 'border-color:var(--ws-accent);color:var(--ws-accent)'
          : 'border-color:transparent;color:var(--ws-muted)'}>
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- ════════════════════════════ RYANAIR ════════════════════════════ -->
  {#if activeTab==='ryanair'}
  <div class="grid md:grid-cols-2 gap-4">

    <!-- Form -->
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">+ Ryanair Tracker</h2>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('radarFrom')||'Von'}</label>
          <input bind:value={ryOrigin} maxlength="3" placeholder="BGY" class="{inputCls} mt-1 font-mono uppercase" style={inputStyle}/>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('radarTo')||'Nach'}</label>
          <input bind:value={ryDest} maxlength="3" placeholder="DUB" class="{inputCls} mt-1 font-mono uppercase" style={inputStyle}/>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Hinflug</label>
          <input type="date" bind:value={ryOut} class="{inputCls} mt-1" style={inputStyle}/>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Rückflug (opt.)</label>
          <input type="date" bind:value={ryRet} class="{inputCls} mt-1" style={inputStyle}/>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Erwachsene</label>
          <select bind:value={ryAdults} class="{inputCls} mt-1" style={inputStyle}>
            {#each [1,2,3,4,5,6] as n}<option value={n}>{n}</option>{/each}
          </select>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Kinder</label>
          <select bind:value={ryChildren} class="{inputCls} mt-1" style={inputStyle}>
            {#each [0,1,2,3,4] as n}<option value={n}>{n}</option>{/each}
          </select>
        </div>
      </div>
      <div>
        <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">🧳 Gepäck</label>
        <div class="mt-1.5 space-y-1.5">
          {#each bagOptions as b}
            <button onclick={() => toggleBag(b.type)}
              class="w-full flex items-center gap-3 px-3 py-2 rounded-xl border text-sm text-left transition-colors"
              style={ryBags.includes(b.type)
                ? 'background:rgba(196,98,45,.1);border-color:var(--ws-accent);color:var(--ws-text)'
                : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
              <span class="w-4 h-4 rounded border flex items-center justify-center text-xs shrink-0"
                style="border-color:{ryBags.includes(b.type)?'var(--ws-accent)':'var(--ws-border)'}">
                {ryBags.includes(b.type)?'✓':''}
              </span>
              {b.label}
            </button>
          {/each}
        </div>
      </div>
      <div>
        <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">🪑 Sitzplatz €/Person/Flug</label>
        <input type="number" bind:value={rySeat} min="0" step="0.01" placeholder="0.00" class="{inputCls} mt-1" style={inputStyle}/>
      </div>
      <button onclick={addRyanair} disabled={ryAdding}
        class="w-full py-2.5 rounded-xl font-semibold text-sm transition-opacity hover:opacity-80 disabled:opacity-50"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        {ryAdding ? '⏳…' : '+ Tracker anlegen'}
      </button>
    </div>

    <!-- Tracker list -->
    <div class="space-y-3">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashActiveTrackers')}</h2>
      {#if ryLoading}
        <!-- Skeleton screens -->
        {#each [1,2] as _}
          <div class="rounded-xl p-3 border animate-pulse" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <div class="h-4 w-32 rounded mb-2" style="background:var(--ws-border)"></div>
            <div class="h-3 w-48 rounded mb-3" style="background:var(--ws-border)"></div>
            <div class="h-8 rounded" style="background:var(--ws-border)"></div>
          </div>
        {/each}
      {:else if ryTrackers.length===0}
        <p class="text-xs" style="color:var(--ws-muted)">{$t('dashNoTrackers')}</p>
      {:else}
        {#each ryTrackers as tr}
          {@const s = tr.latest_snapshot}
          {@const wKey = `flight-${tr.id}`}
          {@const cKey = `flight-${tr.id}`}
          {@const wish = tr.wish_price}
          {@const price = s?.total_price}
          {@const wishMet = wish && price && price <= wish}
          {@const prevSnap = null}
          <div class="rounded-xl p-3 border transition-all"
            style="background:var(--ws-surface);border-color:{wishMet?'var(--ws-green)':'var(--ws-border)'}">
            <!-- Header row -->
            <div class="flex items-start justify-between">
              <div>
                <div class="font-bold font-mono text-sm">{tr.origin} → {tr.destination}</div>
                <div class="text-xs font-mono mt-0.5" style="color:var(--ws-muted)">
                  {tr.outbound_date}{tr.return_date?' ⇄ '+tr.return_date:''} · {tr.adults} Erw.
                </div>
                {#if wishMet}
                  <div class="text-xs mt-1 font-semibold" style="color:var(--ws-green)">🎯 Wunschpreis erreicht!</div>
                {/if}
              </div>
              <div class="text-right">
                <div class="font-bold font-mono text-sm" style={price ? trendStyle(null) : 'color:var(--ws-muted)'}>
                  {price ? price.toFixed(2) + ' €' : '–'}
                </div>
                {#if s?.fetched_at}
                  <div class="text-xs" style="color:var(--ws-muted)">{s.fetched_at.slice(0,10)}</div>
                {/if}
              </div>
            </div>

            <!-- Wish price row -->
            <div class="mt-2 flex items-center gap-2">
              <span class="text-xs" style="color:var(--ws-muted)">🎯 Wunschpreis:</span>
              {#if wishState[wKey]?.editing}
                <input type="number" bind:value={wishState[wKey].value} min="0" step="1"
                  placeholder="z.B. 120"
                  class="flex-1 px-2 py-1 rounded-lg border text-xs font-mono"
                  style={inputStyle}
                  onkeydown={(e) => e.key==='Enter' && saveWishPrice('flight', tr.id, 'trackers', wishState[wKey].value)}/>
                <button onclick={() => saveWishPrice('flight', tr.id, 'trackers', wishState[wKey].value)}
                  disabled={wishState[wKey]?.saving}
                  class="px-2 py-1 rounded-lg text-xs font-semibold"
                  style="background:var(--ws-accent);color:#fff">✓</button>
                <button onclick={() => wishState[wKey] = { editing: false }}
                  class="px-2 py-1 rounded-lg text-xs" style="background:var(--ws-surface2);color:var(--ws-muted)">✕</button>
              {:else}
                <span class="text-xs font-mono font-semibold" style="color:{wish ? 'var(--ws-accent)' : 'var(--ws-muted)'}">
                  {wish ? wish.toFixed(2) + ' €' : 'nicht gesetzt'}
                </span>
                <button onclick={() => wishState[wKey] = { editing: true, value: wish?.toString() || '' }}
                  class="text-xs px-2 py-0.5 rounded-lg border"
                  style="border-color:var(--ws-border);color:var(--ws-muted)">✏️</button>
              {/if}
            </div>

            <!-- Action row -->
            <div class="flex gap-2 mt-2">
              <button onclick={() => scrapeRy(tr.id)}
                class="flex-1 py-1.5 rounded-lg text-xs border hover:border-[var(--ws-accent)] transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">⟳ Aktualisieren</button>
              <button onclick={() => toggleChart('flight', tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
                {chartState[cKey]?.open ? '▲' : '📈'}
              </button>
              <button onclick={() => deleteRy(tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>

            <!-- Price history accordion -->
            {#if chartState[cKey]?.open}
              <div class="mt-3 pt-3 border-t" style="border-color:var(--ws-border)">
                {#if chartState[cKey]?.loading}
                  <div class="h-24 rounded animate-pulse" style="background:var(--ws-border)"></div>
                {:else if chartState[cKey]?.history?.length < 2}
                  <p class="text-xs text-center py-4" style="color:var(--ws-muted)">Noch zu wenig Daten für Diagramm</p>
                {:else}
                  {@const hist = chartState[cKey].history}
                  {@const prices = hist.map(h => h.price)}
                  {@const minP = Math.min(...prices)}
                  {@const maxP = Math.max(...prices)}
                  {@const range = maxP - minP || 1}
                  {@const pts = hist.map((h,i) => {
                    const x = (i / (hist.length-1)) * 290 + 5;
                    const y = 75 - ((h.price - minP) / range) * 65;
                    return `${x},${y}`;
                  })}
                  {@const polyPts = `5,75 ${pts.join(' ')} ${(hist.length > 1 ? (hist.length-1)/(hist.length-1) : 1)*290+5},75`}
                  <div class="relative h-24">
                    <svg viewBox="0 0 300 80" class="w-full h-full" preserveAspectRatio="none">
                      <defs>
                        <linearGradient id="chartGrad-{tr.id}" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stop-color="var(--ws-accent)" stop-opacity="0.3"/>
                          <stop offset="100%" stop-color="var(--ws-accent)" stop-opacity="0"/>
                        </linearGradient>
                      </defs>
                      <polyline fill="none" stroke="var(--ws-accent)" stroke-width="2"
                        points={pts.join(' ')}/>
                      <polygon fill="url(#chartGrad-{tr.id})" points={polyPts}/>
                    </svg>
                    <div class="absolute top-0 right-0 text-xs font-mono" style="color:var(--ws-muted)">{maxP.toFixed(0)}€</div>
                    <div class="absolute bottom-0 right-0 text-xs font-mono" style="color:var(--ws-green)">{minP.toFixed(0)}€</div>
                    <div class="absolute bottom-0 left-0 text-xs" style="color:var(--ws-muted)">{hist[0].fetched_at.slice(0,10)}</div>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      {/if}
    </div>
  </div>

  <!-- ════════════════════════════ GOOGLE FLIGHTS ════════════════════════════ -->
  {:else if activeTab==='gflights'}
  <div class="grid md:grid-cols-2 gap-4">
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">+ Google Flights Tracker</h2>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('radarFrom')||'Von'}</label>
          <input bind:value={gfOrigin} maxlength="3" placeholder="MUC" class="{inputCls} mt-1 font-mono uppercase" style={inputStyle}/>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('radarTo')||'Nach'}</label>
          <input bind:value={gfDest} maxlength="3" placeholder="JFK" class="{inputCls} mt-1 font-mono uppercase" style={inputStyle}/>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Datum</label>
          <input type="date" bind:value={gfOut} class="{inputCls} mt-1" style={inputStyle}/>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Rückflug (opt.)</label>
          <input type="date" bind:value={gfRet} class="{inputCls} mt-1" style={inputStyle}/>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Erwachsene</label>
          <select bind:value={gfAdults} class="{inputCls} mt-1" style={inputStyle}>
            {#each [1,2,3,4,5,6] as n}<option value={n}>{n}</option>{/each}
          </select>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Kinder</label>
          <select bind:value={gfChildren} class="{inputCls} mt-1" style={inputStyle}>
            {#each [0,1,2,3,4] as n}<option value={n}>{n}</option>{/each}
          </select>
        </div>
      </div>
      <button onclick={addGF} disabled={gfAdding}
        class="w-full py-2.5 rounded-xl font-semibold text-sm disabled:opacity-50"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        {gfAdding ? '⏳…' : '+ Tracker anlegen'}
      </button>
      <p class="text-xs" style="color:var(--ws-muted)">⚙ SerpAPI Key in Einstellungen erforderlich</p>
    </div>

    <div class="space-y-3">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashActiveTrackers')}</h2>
      {#if gfLoading}
        {#each [1,2] as _}
          <div class="rounded-xl p-3 border animate-pulse" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <div class="h-4 w-32 rounded mb-2" style="background:var(--ws-border)"></div>
            <div class="h-3 w-40 rounded mb-3" style="background:var(--ws-border)"></div>
            <div class="h-8 rounded" style="background:var(--ws-border)"></div>
          </div>
        {/each}
      {:else if gfTrackers.length===0}
        <p class="text-xs" style="color:var(--ws-muted)">{$t('dashNoTrackers')}</p>
      {:else}
        {#each gfTrackers as tr}
          {@const s = tr.latest_snapshot}
          {@const wKey = `google_flight-${tr.id}`}
          {@const wish = tr.wish_price}
          {@const price = s?.total_price}
          {@const wishMet = wish && price && price <= wish}
          <div class="rounded-xl p-3 border transition-all"
            style="background:var(--ws-surface);border-color:{wishMet?'var(--ws-green)':'var(--ws-border)'}">
            <div class="flex items-start justify-between">
              <div>
                <div class="font-bold font-mono text-sm">{tr.origin} → {tr.destination}</div>
                <div class="text-xs font-mono mt-0.5" style="color:var(--ws-muted)">
                  {tr.outbound_date}{tr.return_date?' ⇄ '+tr.return_date:''} · {tr.adults} Erw.
                </div>
                {#if s?.airline}<div class="text-xs mt-0.5" style="color:var(--ws-muted)">✈ {s.airline} {s.departure_time??''}→{s.arrival_time??''}{s.duration_min?' ('+Math.floor(s.duration_min/60)+'h'+s.duration_min%60+'m)':''}</div>{/if}
                {#if wishMet}<div class="text-xs mt-1 font-semibold" style="color:var(--ws-green)">🎯 Wunschpreis erreicht!</div>{/if}
              </div>
              <div class="text-right">
                <div class="font-bold font-mono text-sm" style="color:var(--ws-green)">{price ? price.toFixed(2)+' €' : '–'}</div>
                {#if s?.fetched_at}<div class="text-xs" style="color:var(--ws-muted)">{s.fetched_at.slice(0,10)}</div>{/if}
              </div>
            </div>
            <!-- Wish price -->
            <div class="mt-2 flex items-center gap-2">
              <span class="text-xs" style="color:var(--ws-muted)">🎯</span>
              {#if wishState[wKey]?.editing}
                <input type="number" bind:value={wishState[wKey].value} min="0" step="1" placeholder="Wunschpreis"
                  class="flex-1 px-2 py-1 rounded-lg border text-xs font-mono" style={inputStyle}
                  onkeydown={(e) => e.key==='Enter' && saveWishPrice('google_flight', tr.id, 'gf_trackers', wishState[wKey].value)}/>
                <button onclick={() => saveWishPrice('google_flight', tr.id, 'gf_trackers', wishState[wKey].value)}
                  class="px-2 py-1 rounded-lg text-xs font-semibold" style="background:var(--ws-accent);color:#fff">✓</button>
                <button onclick={() => wishState[wKey]={editing:false}}
                  class="px-2 py-1 rounded-lg text-xs" style="background:var(--ws-surface2);color:var(--ws-muted)">✕</button>
              {:else}
                <span class="text-xs font-mono" style="color:{wish?'var(--ws-accent)':'var(--ws-muted)'}">{wish ? wish.toFixed(2)+' €' : 'nicht gesetzt'}</span>
                <button onclick={() => wishState[wKey]={editing:true,value:wish?.toString()||''}}
                  class="text-xs px-2 py-0.5 rounded-lg border" style="border-color:var(--ws-border);color:var(--ws-muted)">✏️</button>
              {/if}
            </div>
            <div class="flex gap-2 mt-2">
              <button onclick={() => scrapeGF(tr.id)}
                class="flex-1 py-1.5 rounded-lg text-xs border transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">⟳ Aktualisieren</button>
              <button onclick={() => toggleChart('google_flight', tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
                {chartState[wKey]?.open ? '▲' : '📈'}
              </button>
              <button onclick={() => deleteGF(tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
            {#if chartState[wKey]?.open}
              <div class="mt-3 pt-3 border-t" style="border-color:var(--ws-border)">
                {#if chartState[wKey]?.loading}
                  <div class="h-20 rounded animate-pulse" style="background:var(--ws-border)"></div>
                {:else if !chartState[wKey]?.history?.length || chartState[wKey].history.length < 2}
                  <p class="text-xs text-center py-4" style="color:var(--ws-muted)">Noch zu wenig Daten</p>
                {:else}
                  {@const hist = chartState[wKey].history}
                  {@const prices = hist.map(h => h.price)}
                  {@const minP = Math.min(...prices)}
                  {@const maxP = Math.max(...prices)}
                  {@const range = maxP - minP || 1}
                  <div class="relative h-20">
                    {@const pts = hist.map((h,i) => { const x=(i/(hist.length-1))*290+5; const y=65-((h.price-minP)/range)*58; return `${x},${y}`; })}
                    <svg viewBox="0 0 300 70" class="w-full h-full" preserveAspectRatio="none">
                      <polyline fill="none" stroke="var(--ws-accent)" stroke-width="2" points={pts.join(' ')}/>
                    </svg>
                    <div class="absolute top-0 right-0 text-xs font-mono" style="color:var(--ws-muted)">{maxP.toFixed(0)}€</div>
                    <div class="absolute bottom-0 right-0 text-xs font-mono" style="color:var(--ws-green)">{minP.toFixed(0)}€</div>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      {/if}
    </div>
  </div>

  <!-- ════════════════════════════ HOMAIR / CAMPING ════════════════════════════ -->
  {:else if activeTab==='homair'}
  <div class="grid md:grid-cols-2 gap-4">
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">⛺ Camping Tracker</h2>
      <div>
        <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Region</label>
        <select bind:value={hmRegion} class="{inputCls} mt-1" style={inputStyle}>
          {#each hmRegions as r}<option value={r.val}>{r.label}</option>{/each}
        </select>
      </div>
      <div>
        <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Unterkunftstyp</label>
        <select bind:value={hmType} class="{inputCls} mt-1" style={inputStyle}>
          {#each hmTypes as t}<option value={t.val}>{t.label}</option>{/each}
        </select>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Anreise</label>
          <input type="date" bind:value={hmIn} class="{inputCls} mt-1" style={inputStyle}/>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Abreise</label>
          <input type="date" bind:value={hmOut2} class="{inputCls} mt-1" style={inputStyle}/>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Erwachsene</label>
          <select bind:value={hmAdults} class="{inputCls} mt-1" style={inputStyle}>
            {#each [1,2,3,4,5,6] as n}<option value={n}>{n}</option>{/each}
          </select>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Kinder</label>
          <select bind:value={hmChildren} class="{inputCls} mt-1" style={inputStyle}>
            {#each [0,1,2,3,4] as n}<option value={n}>{n}</option>{/each}
          </select>
        </div>
      </div>
      <button onclick={addHM} disabled={hmAdding}
        class="w-full py-2.5 rounded-xl font-semibold text-sm disabled:opacity-50"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        {hmAdding ? '⏳…' : '+ Tracker anlegen'}
      </button>
    </div>
    <div class="space-y-3">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashActiveTrackers')}</h2>
      {#if hmLoading}
        <div class="rounded-xl p-3 border animate-pulse" style="background:var(--ws-surface);border-color:var(--ws-border)">
          <div class="h-4 w-32 rounded mb-2" style="background:var(--ws-border)"></div>
          <div class="h-8 rounded" style="background:var(--ws-border)"></div>
        </div>
      {:else if hmTrackers.length===0}
        <p class="text-xs" style="color:var(--ws-muted)">{$t('dashNoTrackers')}</p>
      {:else}
        {#each hmTrackers as tr}
          {@const s = tr.latest_snapshot}
          {@const wKey = `camping-${tr.id}`}
          {@const wish = tr.wish_price}
          {@const price = s?.total_price}
          {@const wishMet = wish && price && price <= wish}
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:{wishMet?'var(--ws-green)':'var(--ws-border)'}">
            <div class="flex justify-between">
              <div>
                <div class="font-bold text-sm">⛺ {hmRegions.find(r=>r.val===tr.region)?.label??tr.region}</div>
                <div class="text-xs mt-0.5" style="color:var(--ws-muted)">{tr.checkin_date} → {tr.checkout_date}</div>
                <div class="text-xs" style="color:var(--ws-muted)">{tr.accommodation_type} · {tr.adults} Erw.</div>
                {#if wishMet}<div class="text-xs mt-1 font-semibold" style="color:var(--ws-green)">🎯 Wunschpreis erreicht!</div>{/if}
              </div>
              <div class="font-bold font-mono text-sm" style="color:var(--ws-green)">{price ? price.toFixed(2)+' €' : '–'}</div>
            </div>
            <div class="mt-2 flex items-center gap-2">
              <span class="text-xs" style="color:var(--ws-muted)">🎯</span>
              {#if wishState[wKey]?.editing}
                <input type="number" bind:value={wishState[wKey].value} min="0" step="1" placeholder="Wunschpreis"
                  class="flex-1 px-2 py-1 rounded-lg border text-xs font-mono" style={inputStyle}
                  onkeydown={(e) => e.key==='Enter' && saveWishPrice('camping', tr.id, 'homair_trackers', wishState[wKey].value)}/>
                <button onclick={() => saveWishPrice('camping', tr.id, 'homair_trackers', wishState[wKey].value)}
                  class="px-2 py-1 rounded-lg text-xs font-semibold" style="background:var(--ws-accent);color:#fff">✓</button>
                <button onclick={() => wishState[wKey]={editing:false}}
                  class="px-2 py-1 rounded-lg text-xs" style="background:var(--ws-surface2);color:var(--ws-muted)">✕</button>
              {:else}
                <span class="text-xs font-mono" style="color:{wish?'var(--ws-accent)':'var(--ws-muted)'}">{wish ? wish.toFixed(2)+' €' : 'nicht gesetzt'}</span>
                <button onclick={() => wishState[wKey]={editing:true,value:wish?.toString()||''}}
                  class="text-xs px-2 py-0.5 rounded-lg border" style="border-color:var(--ws-border);color:var(--ws-muted)">✏️</button>
              {/if}
            </div>
            <div class="flex gap-2 mt-2">
              <button onclick={() => scrapeHM(tr.id)}
                class="flex-1 py-1.5 rounded-lg text-xs border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">⟳</button>
              <button onclick={() => toggleChart('camping', tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
                {chartState[wKey]?.open ? '▲' : '📈'}
              </button>
              <button onclick={() => deleteHM(tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
            {#if chartState[wKey]?.open}
              <div class="mt-3 pt-3 border-t" style="border-color:var(--ws-border)">
                {#if chartState[wKey]?.loading}
                  <div class="h-20 rounded animate-pulse" style="background:var(--ws-border)"></div>
                {:else if !chartState[wKey]?.history?.length || chartState[wKey].history.length < 2}
                  <p class="text-xs text-center py-4" style="color:var(--ws-muted)">Noch zu wenig Daten</p>
                {:else}
                  {@const hist = chartState[wKey].history}
                  {@const prices = hist.map(h=>h.price)}
                  {@const minP=Math.min(...prices)} {@const maxP=Math.max(...prices)} {@const range=maxP-minP||1}
                  {@const pts=hist.map((h,i)=>{const x=(i/(hist.length-1))*290+5;const y=65-((h.price-minP)/range)*58;return `${x},${y}`;})}
                  <div class="relative h-20">
                    <svg viewBox="0 0 300 70" class="w-full h-full" preserveAspectRatio="none">
                      <polyline fill="none" stroke="var(--ws-accent)" stroke-width="2" points={pts.join(' ')}/>
                    </svg>
                    <div class="absolute top-0 right-0 text-xs font-mono" style="color:var(--ws-muted)">{maxP.toFixed(0)}€</div>
                    <div class="absolute bottom-0 right-0 text-xs font-mono" style="color:var(--ws-green)">{minP.toFixed(0)}€</div>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      {/if}
    </div>
  </div>

  <!-- ════════════════════════════ BOOKING / HOTEL ════════════════════════════ -->
  {:else if activeTab==='booking'}
  <div class="grid md:grid-cols-2 gap-4">
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">🏨 Hotel Tracker</h2>
      <div>
        <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Quelle</label>
        <select bind:value={bkSource} class="{inputCls} mt-1" style={inputStyle}>
          <option value="booking">Booking.com</option>
          <option value="trivago">Trivago</option>
        </select>
      </div>
      <div>
        <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Zielort / Hotel</label>
        <input bind:value={bkDest} placeholder="z.B. Dublin, Irland" class="{inputCls} mt-1" style={inputStyle}/>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Check-in</label>
          <input type="date" bind:value={bkIn} class="{inputCls} mt-1" style={inputStyle}/>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Check-out</label>
          <input type="date" bind:value={bkOut2} class="{inputCls} mt-1" style={inputStyle}/>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Erwachsene</label>
          <select bind:value={bkAdults} class="{inputCls} mt-1" style={inputStyle}>
            {#each [1,2,3,4,5,6] as n}<option value={n}>{n}</option>{/each}
          </select>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Zimmer</label>
          <select bind:value={bkRooms} class="{inputCls} mt-1" style={inputStyle}>
            {#each [1,2,3] as n}<option value={n}>{n}</option>{/each}
          </select>
        </div>
      </div>
      <button onclick={addBK} disabled={bkAdding}
        class="w-full py-2.5 rounded-xl font-semibold text-sm disabled:opacity-50"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        {bkAdding ? '⏳…' : '+ Tracker anlegen'}
      </button>
      <p class="text-xs" style="color:var(--ws-muted)">⚙ SerpAPI Key in Einstellungen erforderlich</p>
    </div>
    <div class="space-y-3">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashActiveTrackers')}</h2>
      {#if bkLoading}
        <div class="rounded-xl p-3 border animate-pulse" style="background:var(--ws-surface);border-color:var(--ws-border)">
          <div class="h-4 w-32 rounded mb-2" style="background:var(--ws-border)"></div>
          <div class="h-8 rounded" style="background:var(--ws-border)"></div>
        </div>
      {:else if bkTrackers.length===0}
        <p class="text-xs" style="color:var(--ws-muted)">{$t('dashNoTrackers')}</p>
      {:else}
        {#each bkTrackers as tr}
          {@const s = tr.latest_snapshot}
          {@const wKey = `hotel-${tr.id}`}
          {@const wish = tr.wish_price}
          {@const price = s?.total_price}
          {@const wishMet = wish && price && price <= wish}
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:{wishMet?'var(--ws-green)':'var(--ws-border)'}">
            <div class="flex justify-between">
              <div>
                <div class="font-bold text-sm">🏨 {tr.destination}</div>
                <div class="text-xs mt-0.5" style="color:var(--ws-muted)">{tr.checkin_date} → {tr.checkout_date}</div>
                <div class="text-xs" style="color:var(--ws-muted)">{tr.adults} Erw. · {tr.rooms} Zi. · {tr.source}</div>
                {#if s?.hotel_name}<div class="text-xs italic" style="color:var(--ws-muted)">{s.hotel_name}</div>{/if}
                {#if wishMet}<div class="text-xs mt-1 font-semibold" style="color:var(--ws-green)">🎯 Wunschpreis erreicht!</div>{/if}
              </div>
              <div class="text-right">
                <div class="font-bold font-mono text-sm" style="color:var(--ws-green)">{price ? price.toFixed(2)+' €/Nacht' : '–'}</div>
              </div>
            </div>
            <div class="mt-2 flex items-center gap-2">
              <span class="text-xs" style="color:var(--ws-muted)">🎯</span>
              {#if wishState[wKey]?.editing}
                <input type="number" bind:value={wishState[wKey].value} min="0" step="1" placeholder="€/Nacht"
                  class="flex-1 px-2 py-1 rounded-lg border text-xs font-mono" style={inputStyle}
                  onkeydown={(e)=>e.key==='Enter'&&saveWishPrice('hotel',tr.id,'booking_trackers',wishState[wKey].value)}/>
                <button onclick={()=>saveWishPrice('hotel',tr.id,'booking_trackers',wishState[wKey].value)}
                  class="px-2 py-1 rounded-lg text-xs font-semibold" style="background:var(--ws-accent);color:#fff">✓</button>
                <button onclick={()=>wishState[wKey]={editing:false}}
                  class="px-2 py-1 rounded-lg text-xs" style="background:var(--ws-surface2);color:var(--ws-muted)">✕</button>
              {:else}
                <span class="text-xs font-mono" style="color:{wish?'var(--ws-accent)':'var(--ws-muted)'}">{wish?wish.toFixed(2)+' €/Nacht':'nicht gesetzt'}</span>
                <button onclick={()=>wishState[wKey]={editing:true,value:wish?.toString()||''}}
                  class="text-xs px-2 py-0.5 rounded-lg border" style="border-color:var(--ws-border);color:var(--ws-muted)">✏️</button>
              {/if}
            </div>
            <div class="flex gap-2 mt-2">
              <button onclick={()=>scrapeBK(tr.id)}
                class="flex-1 py-1.5 rounded-lg text-xs border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">⟳</button>
              <button onclick={()=>toggleChart('hotel',tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
                {chartState[wKey]?.open?'▲':'📈'}
              </button>
              <button onclick={()=>deleteBK(tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
            {#if chartState[wKey]?.open}
              <div class="mt-3 pt-3 border-t" style="border-color:var(--ws-border)">
                {#if chartState[wKey]?.loading}
                  <div class="h-20 rounded animate-pulse" style="background:var(--ws-border)"></div>
                {:else if !chartState[wKey]?.history?.length||chartState[wKey].history.length<2}
                  <p class="text-xs text-center py-4" style="color:var(--ws-muted)">Noch zu wenig Daten</p>
                {:else}
                  {@const hist=chartState[wKey].history}
                  {@const prices=hist.map(h=>h.price)}
                  {@const minP=Math.min(...prices)} {@const maxP=Math.max(...prices)} {@const range=maxP-minP||1}
                  {@const pts=hist.map((h,i)=>{const x=(i/(hist.length-1))*290+5;const y=65-((h.price-minP)/range)*58;return `${x},${y}`;})}
                  <div class="relative h-20">
                    <svg viewBox="0 0 300 70" class="w-full h-full" preserveAspectRatio="none">
                      <polyline fill="none" stroke="var(--ws-accent)" stroke-width="2" points={pts.join(' ')}/>
                    </svg>
                    <div class="absolute top-0 right-0 text-xs font-mono" style="color:var(--ws-muted)">{maxP.toFixed(0)}€</div>
                    <div class="absolute bottom-0 right-0 text-xs font-mono" style="color:var(--ws-green)">{minP.toFixed(0)}€</div>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      {/if}
    </div>
  </div>
  {/if}

</div>
