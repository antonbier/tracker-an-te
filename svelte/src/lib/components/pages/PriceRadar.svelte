<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { apiUrl } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';
  import { t } from '$lib/i18n.js';

  let activeTab = $state('ryanair');

  // ── Shared helpers ──────────────────────────────────────────────────
  const today = new Date();
  const d30 = new Date(today); d30.setDate(d30.getDate() + 30);
  const d37 = new Date(today); d37.setDate(d37.getDate() + 37);
  function fmt(d) { return d.toISOString().slice(0,10); }

  // ── Ryanair ─────────────────────────────────────────────────────────
  let ryTrackers  = $state([]);
  let ryLoading   = $state(true);
  let ryAdding    = $state(false);
  let ryOrigin    = $state('BGY');
  let ryDest      = $state('DUB');
  let ryOut       = $state(fmt(d30));
  let ryRet       = $state(fmt(d37));
  let ryAdults    = $state(2);
  let ryChildren  = $state(0);
  let rySeat      = $state(0);
  let ryBags      = $state([]);
  const bagOptions = [
    { type: '10kg', label: '10 kg Check-in Koffer' },
    { type: '20kg', label: '20 kg Check-in Koffer' },
    { type: '23kg', label: '23 kg Koffer (Large)' },
  ];
  function toggleBag(t) { ryBags = ryBags.includes(t) ? ryBags.filter(b=>b!==t) : [...ryBags,t]; }

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
    if (!confirm('Löschen?')) return;
    await api(`/api/trackers/${id}`,{method:'DELETE'});
    await loadRyanair();
  }

  // ── Google Flights ──────────────────────────────────────────────────
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
    if (!gfOrigin||!gfDest||!gfOut) { toast($t('radarRequired') || 'Pflichtfelder ausfüllen','error'); return; }
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
    const serpKey = browser ? localStorage.getItem('s-serpApiKey')||'' : '';
    toast('Suche Flüge…','warning');
    try {
      const r = await api(`/api/google-flights/${id}/scrape?api_key=${encodeURIComponent(serpKey)}`,{method:'POST'});
      const s = r.snapshot;
      const info = s?.airline ? ` — ${s.airline} ${s.departure_time??''}→${s.arrival_time??''}` : '';
      toast(`${s?.total_price?.toFixed(2)} €${info}`,'success');
      await loadGF();
    } catch(e) { toast(e.message,'error'); }
  }
  async function deleteGF(id) {
    if (!confirm('Löschen?')) return;
    await api(`/api/google-flights/${id}`,{method:'DELETE'});
    await loadGF();
  }

  // ── Homair ──────────────────────────────────────────────────────────
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
      toast(`${r.snapshot?.total_price?.toFixed(2)} €/Nacht`,'success');
      await loadHM();
    } catch(e) { toast(e.message,'error'); }
  }
  async function deleteHM(id) {
    if (!confirm('Löschen?')) return;
    await api(`/api/accommodations/homair/${id}`,{method:'DELETE'});
    await loadHM();
  }

  // ── Booking ──────────────────────────────────────────────────────────
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
    if (!bkDest||!bkIn||!bkOut2) { toast($t('radarRequired') || 'Pflichtfelder ausfüllen','error'); return; }
    if (!$apiUrl) { toast($t('radarNoBackend'),'warning'); return; }
    const serpKey = browser ? localStorage.getItem('s-serpApiKey')||'' : '';
    if (!serpKey) { toast($t('radarNoKey'),'warning'); return; }
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
    if (!confirm('Löschen?')) return;
    await api(`/api/accommodations/booking/${id}`,{method:'DELETE'});
    await loadBK();
  }

  // ── Init ─────────────────────────────────────────────────────────────
  onMount(() => {
    loadRyanair();
  });

  $effect(() => {
    if (activeTab==='gflights' && gfTrackers.length===0) loadGF();
    if (activeTab==='homair'   && hmTrackers.length===0) loadHM();
    if (activeTab==='booking'  && bkTrackers.length===0) loadBK();
  });

  // ── Shared UI helpers ─────────────────────────────────────────────────
  const inputCls = 'w-full px-3 py-2 rounded-xl border text-sm';
  const inputStyle = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
  const tabs = $derived([
    { id:'ryanair',  label:'🟠 ' + $t('radarRyanair') },
    { id:'gflights', label:'🔵 ' + $t('radarGoogle') },
    { id:'homair',   label:'⛺ ' + $t('radarHomair') },
    { id:'booking',  label:'🏨 ' + $t('radarBooking') },
  ]);
</script>

<div class="space-y-4">
  <h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif)">{$t('navRadar')}</h1>

  <!-- Tab bar -->
  <div class="flex gap-1.5 overflow-x-auto pb-1">
    {#each tabs as tab}
      <button onclick={() => activeTab = tab.id}
        class="px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all border"
        style={activeTab===tab.id
          ? 'background:var(--ws-accent);color:#fff5ec;border-color:var(--ws-accent)'
          : 'background:var(--ws-surface);color:var(--ws-muted);border-color:var(--ws-border)'}>
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- ── RYANAIR ── -->
  {#if activeTab==='ryanair'}
  <div class="grid md:grid-cols-2 gap-4">
    <!-- Form -->
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashStartTracker').replace('+','')} — Ryanair</h2>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('radarFrom') || 'Von'}</label>
          <input bind:value={ryOrigin} maxlength="3" placeholder="BGY" class="{inputCls} mt-1 font-mono uppercase" style={inputStyle}/>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('radarTo') || 'Nach'}</label>
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
        {$t('loading').includes('…') ? '⏳…' : '+ Tracker'}
      </button>
    </div>
    <!-- List -->
    <div class="space-y-3">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashActiveTrackers')}</h2>
      {#if ryLoading}<p class="text-xs" style="color:var(--ws-muted)">{$t('loading')}</p>
      {:else if ryTrackers.length===0}<p class="text-xs" style="color:var(--ws-muted)">{$t('dashNoTrackers')}</p>
      {:else}
        {#each ryTrackers as tr}
          {@const s=tr.latest_snapshot}
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <div class="flex items-start justify-between">
              <div>
                <div class="font-bold font-mono text-sm">{tr.origin} → {tr.destination}</div>
                <div class="text-xs font-mono mt-0.5" style="color:var(--ws-muted)">{tr.outbound_date}{tr.return_date?' ⇄ '+tr.return_date:''}</div>
              </div>
              <div class="text-right">
                <div class="font-bold font-mono text-sm" style="color:var(--ws-green)">{s?.total_price?s.total_price.toFixed(2)+' €':'–'}</div>
                <div class="text-xs font-mono" style="color:var(--ws-muted)">{s?.fetched_at?.slice(0,10)??'–'}</div>
              </div>
            </div>
            <div class="flex gap-2 mt-2">
              <button onclick={() => scrapeRy(tr.id)}
                class="flex-1 py-1.5 rounded-lg text-xs border hover:border-[var(--ws-accent)] transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">⟳ Jetzt</button>
              <button onclick={() => deleteRy(tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </div>

  <!-- ── GOOGLE FLIGHTS ── -->
  {:else if activeTab==='gflights'}
  <div class="grid md:grid-cols-2 gap-4">
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Google Flights</h2>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('radarFrom') || 'Von'}</label>
          <input bind:value={gfOrigin} maxlength="3" placeholder="MUC" class="{inputCls} mt-1 font-mono uppercase" style={inputStyle}/>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('radarTo') || 'Nach'}</label>
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
        class="w-full py-2.5 rounded-xl font-semibold text-sm transition-opacity hover:opacity-80 disabled:opacity-50"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        {$t('loading').includes('…') ? '⏳…' : '+ Tracker'}
      </button>
      <p class="text-xs" style="color:var(--ws-muted)">{$t('radarNoKey').replace('— in Einstellungen eintragen','').trim() || '⚙ SerpAPI Key erforderlich'}</p>
    </div>
    <div class="space-y-3">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashActiveTrackers')}</h2>
      {#if gfLoading}<p class="text-xs" style="color:var(--ws-muted)">Lade…</p>
      {:else if gfTrackers.length===0}<p class="text-xs" style="color:var(--ws-muted)">Noch keine GF-Tracker.</p>
      {:else}
        {#each gfTrackers as tr}
          {@const s=tr.latest_snapshot}
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <div class="flex items-start justify-between">
              <div>
                <div class="font-bold font-mono text-sm">{tr.origin} → {tr.destination}</div>
                <div class="text-xs font-mono mt-0.5" style="color:var(--ws-muted)">{tr.outbound_date}{tr.return_date?' ⇄ '+tr.return_date:''} · {tr.adults} Erw.</div>
                {#if s?.airline}<div class="text-xs mt-0.5" style="color:var(--ws-muted)">✈ {s.airline} {s.departure_time??''}→{s.arrival_time??''}{s.duration_min?' ('+Math.floor(s.duration_min/60)+'h'+s.duration_min%60+'m)':''}</div>{/if}
              </div>
              <div class="text-right">
                <div class="font-bold font-mono text-sm" style="color:var(--ws-green)">{s?.total_price?s.total_price.toFixed(2)+' €':'–'}</div>
              </div>
            </div>
            <div class="flex gap-2 mt-2">
              <button onclick={() => scrapeGF(tr.id)}
                class="flex-1 py-1.5 rounded-lg text-xs border transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">⟳ Jetzt</button>
              <button onclick={() => deleteGF(tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </div>

  <!-- ── HOMAIR ── -->
  {:else if activeTab==='homair'}
  <div class="grid md:grid-cols-2 gap-4">
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Homair Camping Tracker</h2>
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
        {$t('loading').includes('…') ? '⏳…' : '+ Tracker'}
      </button>
    </div>
    <div class="space-y-3">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashActiveTrackers')}</h2>
      {#if hmLoading}<p class="text-xs" style="color:var(--ws-muted)">Lade…</p>
      {:else if hmTrackers.length===0}<p class="text-xs" style="color:var(--ws-muted)">Noch keine Homair Tracker.</p>
      {:else}
        {#each hmTrackers as tr}
          {@const s=tr.latest_snapshot}
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <div class="flex justify-between">
              <div>
                <div class="font-bold text-sm">⛺ {hmRegions.find(r=>r.val===tr.region)?.label??tr.region}</div>
                <div class="text-xs mt-0.5" style="color:var(--ws-muted)">{tr.checkin_date} → {tr.checkout_date}</div>
                <div class="text-xs" style="color:var(--ws-muted)">{tr.accommodation_type} · {tr.adults} Erw.</div>
              </div>
              <div class="font-bold font-mono text-sm" style="color:var(--ws-green)">{s?.total_price?s.total_price.toFixed(2)+' €':'–'}</div>
            </div>
            <div class="flex gap-2 mt-2">
              <button onclick={() => scrapeHM(tr.id)}
                class="flex-1 py-1.5 rounded-lg text-xs border transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">⟳ Jetzt</button>
              <button onclick={() => deleteHM(tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </div>

  <!-- ── BOOKING ── -->
  {:else if activeTab==='booking'}
  <div class="grid md:grid-cols-2 gap-4">
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Booking / Trivago Tracker</h2>
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
        {$t('loading').includes('…') ? '⏳…' : '+ Tracker'}
      </button>
      <p class="text-xs" style="color:var(--ws-muted)">{$t('radarNoKey').replace('— in Einstellungen eintragen','').trim() || '⚙ SerpAPI Key erforderlich'}</p>
    </div>
    <div class="space-y-3">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashActiveTrackers')}</h2>
      {#if bkLoading}<p class="text-xs" style="color:var(--ws-muted)">Lade…</p>
      {:else if bkTrackers.length===0}<p class="text-xs" style="color:var(--ws-muted)">Noch keine Booking Tracker.</p>
      {:else}
        {#each bkTrackers as tr}
          {@const s=tr.latest_snapshot}
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <div class="flex justify-between">
              <div>
                <div class="font-bold text-sm">🏨 {tr.destination}</div>
                <div class="text-xs mt-0.5" style="color:var(--ws-muted)">{tr.checkin_date} → {tr.checkout_date}</div>
                <div class="text-xs" style="color:var(--ws-muted)">{tr.adults} Erw. · {tr.rooms} Zi. · {tr.source}</div>
                {#if s?.hotel_name}<div class="text-xs italic" style="color:var(--ws-muted)">{s.hotel_name}</div>{/if}
              </div>
              <div class="font-bold font-mono text-sm" style="color:var(--ws-green)">{s?.total_price?s.total_price.toFixed(2)+' €/Nacht':'–'}</div>
            </div>
            <div class="flex gap-2 mt-2">
              <button onclick={() => scrapeBK(tr.id)}
                class="flex-1 py-1.5 rounded-lg text-xs border transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">⟳ Jetzt</button>
              <button onclick={() => deleteBK(tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </div>
  {/if}

</div>
