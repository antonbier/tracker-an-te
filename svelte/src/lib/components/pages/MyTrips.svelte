<script>
  import { trips, budget, bucketlist, apiUrl } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';
  import { t } from '$lib/i18n.js';
  import ScratchMap from '$lib/components/ScratchMap.svelte';

  // ── Tabs (strenge Reihenfolge) ────────────────────────────────────────────
  // 1 Übersicht · 2 Geplante Reisen · 3 Reisechronik · 4 Bucket List
  let activeTab = $state('overview');
  const tabs = [
    { id: 'overview',   label: '📊 Übersicht'       },
    { id: 'trips',      label: '✈️ Geplante Reisen' },
    { id: 'journal',    label: '📓 Reisechronik'    },
    { id: 'bucketlist', label: '🌟 Bucket List'     },
  ];

  // ── Jahr-Switcher ──────────────────────────────────────────────────────────
  const currentYear = new Date().getFullYear();
  let selectedYear  = $state(currentYear);

  const availableYears = $derived(() => {
    const s = new Set([currentYear]);
    $trips.forEach(t => { const y = +((t.dateStart||t.date||'').slice(0,4)); if(y>2000) s.add(y); });
    journalTrips.forEach(t => { const y = +((t.start_date||'').slice(0,4)); if(y>2000) s.add(y); });
    Object.keys(budgetByYear).forEach(y => s.add(+y));
    return [...s].sort((a,b) => b-a);
  });

  // ── Budget (Backend) ───────────────────────────────────────────────────────
  let budgetByYear = $state({});
  let budgetInput  = $state('');
  let budgetSaving = $state(false);
  const yearBudget = $derived(parseFloat(budgetByYear[String(selectedYear)]) || 0);

  $effect(() => {
    budgetInput = budgetByYear[String(selectedYear)] != null
      ? String(budgetByYear[String(selectedYear)]) : '';
  });

  async function loadBudget() {
    if (!$apiUrl) return;
    try { budgetByYear = (await api('/api/trips/budget')) || {}; } catch {}
  }

  async function saveBudget() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const amount = parseFloat(budgetInput);
    if (isNaN(amount) || amount < 0) { toast('Ungültiger Betrag', 'error'); return; }
    budgetSaving = true;
    try {
      await api('/api/trips/budget', { method: 'PUT', body: JSON.stringify({ year: selectedYear, amount }) });
      budgetByYear = { ...budgetByYear, [String(selectedYear)]: amount };
      toast(`Budget ${selectedYear}: ${amount.toFixed(0)} € gespeichert ✓`, 'success');
    } catch (e) { toast(e.message, 'error'); }
    budgetSaving = false;
  }

  // ── Reisechronik (Backend /api/trips) ─────────────────────────────────────
  let journalTrips = $state([]);
  let journalLoad  = $state(false);
  let editingCost  = $state(null);
  let costDraft    = $state('');

  $effect(() => { if ($apiUrl) { loadJournal(); loadBudget(); } });

  async function loadJournal() {
    if (!$apiUrl) return;
    journalLoad = true;
    try { journalTrips = await api('/api/trips'); }
    catch (e) { toast('Fehler: ' + e.message, 'error'); }
    journalLoad = false;
  }

  async function deleteJournalTrip(id) {
    if (!confirm('Eintrag löschen?')) return;
    try { await api(`/api/trips/${id}`, { method: 'DELETE' }); toast('Gelöscht ✓', 'success'); }
    catch (e) { toast(e.message, 'error'); }
    await loadJournal();
  }

  async function saveCost(trip) {
    const cost = costDraft === '' ? null : parseFloat(costDraft);
    try {
      await api(`/api/trips/${trip.id}/cost`, { method: 'PATCH', body: JSON.stringify({ cost }) });
      journalTrips = journalTrips.map(t => t.id === trip.id ? { ...t, cost } : t);
      toast('Kosten gespeichert ✓', 'success');
    } catch (e) { toast(e.message, 'error'); }
    editingCost = null;
  }

  // ── Manueller Chronik-Eintrag ──────────────────────────────────────────────
  let mName    = $state('');
  let mStart   = $state(new Date().toISOString().slice(0,10));
  let mEnd     = $state('');
  let mCountry = $state('');
  let mCost    = $state('');
  let mAdding  = $state(false);

  async function addManualTrip() {
    if (!mName || !mStart) { toast('Name + Startdatum pflicht', 'error'); return; }
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    mAdding = true;
    try {
      await api('/api/trips', { method: 'POST', body: JSON.stringify({
        name: mName, start_date: mStart, end_date: mEnd||mStart,
        country: mCountry||null, cost: mCost ? parseFloat(mCost) : null,
      })});
      mName=''; mEnd=''; mCountry=''; mCost='';
      toast('Reise hinzugefügt ✓', 'success');
      await loadJournal();
    } catch (e) { toast(e.message, 'error'); }
    mAdding = false;
  }

  // ── Dawarich Sync ──────────────────────────────────────────────────────────
  let syncing  = $state(false);
  let syncInfo = $state('');

  async function syncJournal() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const url   = browser ? localStorage.getItem('s-dawarichUrl')   || '' : '';
    const token = browser ? localStorage.getItem('s-dawarichToken') || '' : '';
    const lat   = parseFloat(browser ? localStorage.getItem('s-homeLat') || '0' : '0');
    const lon   = parseFloat(browser ? localStorage.getItem('s-homeLon') || '0' : '0');
    syncing = true; syncInfo = '';
    try {
      const body = (url && token)
        ? JSON.stringify({ dawarich_url:url, dawarich_token:token, home_lat:lat||null, home_lon:lon||null })
        : '{}';
      const r = await api('/api/dawarich/sync', { method: 'POST', body });
      if (r.trips_detected===0 && r.points_loaded===0) {
        syncInfo = 'Keine GPS-Punkte — Einstellungen prüfen';
        toast('Keine Punkte geladen', 'warning');
      } else {
        syncInfo = `${r.points_loaded} Punkte · ${r.trips_detected} erkannt`;
        toast(`${r.trips_detected} Reisen erkannt ✓`, 'success');
      }
      await loadJournal();
    } catch (e) { toast('Sync-Fehler: ' + e.message, 'error'); }
    syncing = false;
  }

  // ── ActualBudget Sync ─────────────────────────────────────────────────────
  let actualSyncing = $state(false);
  let actualResult  = $state(null);

  async function syncActual() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const url      = browser ? localStorage.getItem('s-actualUrl')        || '' : '';
    const password = browser ? localStorage.getItem('s-actualPassword')   || '' : '';
    const file     = browser ? localStorage.getItem('s-actualFile')       || '' : '';
    const cats     = browser ? localStorage.getItem('s-travelCategories') || '' : '';
    if (!url || !password) { toast('ActualBudget URL + Passwort fehlen → Einstellungen', 'warning'); return; }
    actualSyncing = true; actualResult = null;
    try {
      const r = await api('/api/budget/actual/transactions', { method: 'POST',
        body: JSON.stringify({ actual_url:url, actual_token:password, actual_file:file||null, categories:cats||null }),
      });
      actualResult = r;
      toast(`${r.transactions?.length ?? 0} Transaktionen geladen ✓`, 'success');
    } catch (e) { toast('ActualBudget: ' + e.message, 'error'); }
    actualSyncing = false;
  }

  // Globaler Sync: Dawarich + ActualBudget nacheinander
  let globalSyncing = $state(false);
  async function globalSync() {
    globalSyncing = true;
    await syncJournal();
    await syncActual();
    globalSyncing = false;
  }

  // ── Geplante Trips (localStorage) ─────────────────────────────────────────
  let tripName      = $state('');
  let tripDateStart = $state(new Date().toISOString().slice(0,10));
  let tripDateEnd   = $state('');
  let tripCost      = $state('');

  function addTrip() {
    if (!tripName||!tripDateStart||!tripCost) { toast('Pflichtfelder ausfüllen', 'error'); return; }
    trips.update(l => [...l, { name:tripName, dateStart:tripDateStart, dateEnd:tripDateEnd||tripDateStart, cost:parseFloat(tripCost) }]);
    tripName=''; tripCost=''; tripDateEnd='';
    toast($t('toastTripAdded'), 'success');
  }
  function removeTrip(i) { trips.update(l => l.filter((_,idx)=>idx!==i)); }

  // ── Bucket list ────────────────────────────────────────────────────────────
  let bucketItem = $state('');
  let bucketDest = $state('');
  function addBucketItem() {
    if (!bucketItem) { toast('Bitte Eintrag eingeben', 'error'); return; }
    bucketlist.update(l => [...l, { item:bucketItem, dest:bucketDest, done:false, created:new Date().toISOString().slice(0,10) }]);
    bucketItem=''; bucketDest='';
    toast($t('toastBucketAdded'), 'success');
  }
  function toggleBucket(i) { bucketlist.update(l => l.map((x,idx)=>idx===i?{...x,done:!x.done}:x)); }
  function removeBucket(i) { bucketlist.update(l => l.filter((_,idx)=>idx!==i)); }

  // ── Derived ────────────────────────────────────────────────────────────────
  const today = new Date().toISOString().slice(0,10);

  // Journal gefiltert nach Jahr (strikt)
  const journalYear = $derived(
    journalTrips.filter(t => (t.start_date||'').slice(0,4) === String(selectedYear))
  );

  // Chronik-Kosten für Jahr
  const journalSpentYear = $derived(
    journalYear.filter(t => t.cost != null).reduce((s,t) => s+(parseFloat(t.cost)||0), 0)
  );

  // Geplante Trips: alle (kein Jahresfilter für "geplant" Tab — zeige alle zukünftigen)
  const upcomingTrips = $derived(
    [...$trips]
      .filter(t => (t.dateStart||t.date||'') >= today)
      .sort((a,b) => (a.dateStart||a.date||'').localeCompare(b.dateStart||b.date||''))
  );
  const pastTrips = $derived(
    [...$trips]
      .filter(t => (t.dateStart||t.date||'') < today)
      .sort((a,b) => (b.dateStart||b.date||'').localeCompare(a.dateStart||a.date||''))
  );

  // Trips für selectedYear (Kosten)
  const tripsSpentYear = $derived(
    $trips
      .filter(t => (t.dateStart||t.date||'').slice(0,4) === String(selectedYear))
      .reduce((s,t) => s+(parseFloat(t.cost)||0), 0)
  );

  const totalSpentYear = $derived(journalSpentYear + tripsSpentYear);
  const remainingYear  = $derived(Math.max(0, yearBudget - totalSpentYear));
  const pctYear        = $derived(yearBudget > 0 ? Math.min(100,(totalSpentYear/yearBudget)*100) : 0);

  // Badges: Gesamt = geplante (upcoming) + alle Chronik-Einträge
  const totalCount    = $derived(upcomingTrips.length + journalTrips.length);
  const upcomingCount = $derived(upcomingTrips.length);

  // Style-Helfer
  const inp  = 'bg-stone-50 border border-stone-200 text-stone-800 text-sm rounded-lg focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 p-2.5 w-full outline-none transition-all';
  const card = 'bg-white border border-stone-200 rounded-xl shadow-sm p-5';
  const btn  = 'w-full py-2.5 px-4 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-[.98]';
</script>

<div class="space-y-5">

  <!-- ── Header ───────────────────────────────────────────────────────────── -->
  <div class="flex flex-wrap items-center gap-3">

    <h1 class="text-2xl font-bold mr-auto" style="font-family:var(--ws-serif)">{$t('mytripsTitle')}</h1>

    <!-- Globaler Sync-Button -->
    <button onclick={globalSync} disabled={globalSyncing || !$apiUrl}
      title="Dawarich + ActualBudget synchronisieren"
      class="w-9 h-9 rounded-full border border-stone-200 bg-white flex items-center justify-center
             text-stone-400 hover:text-orange-600 hover:border-orange-300 transition-all shadow-sm
             disabled:opacity-40 disabled:cursor-not-allowed">
      {#if globalSyncing}
        <span class="animate-spin text-sm">⏳</span>
      {:else}
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/>
          <path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/>
        </svg>
      {/if}
    </button>

    <!-- Jahr-Switcher -->
    <div class="flex items-center gap-0.5 bg-white border border-stone-200 rounded-full px-1 py-1 shadow-sm">
      <button
        onclick={() => { const ay=availableYears(); const i=ay.indexOf(selectedYear); if(i<ay.length-1) selectedYear=ay[i+1]; }}
        disabled={availableYears().indexOf(selectedYear) >= availableYears().length-1}
        class="w-7 h-7 rounded-full flex items-center justify-center text-stone-400 hover:text-orange-600 hover:bg-orange-50 transition-all disabled:opacity-30 text-sm">‹</button>
      {#each availableYears() as y}
        <button onclick={() => selectedYear=y}
          class="px-3 py-1 rounded-full text-sm font-semibold transition-all"
          class:bg-orange-600={selectedYear===y} class:text-white={selectedYear===y}
          class:text-stone-500={selectedYear!==y} class:hover:bg-stone-100={selectedYear!==y}>
          {y}
        </button>
      {/each}
      <button
        onclick={() => { const ay=availableYears(); const i=ay.indexOf(selectedYear); if(i>0) selectedYear=ay[i-1]; }}
        disabled={availableYears().indexOf(selectedYear) <= 0}
        class="w-7 h-7 rounded-full flex items-center justify-center text-stone-400 hover:text-orange-600 hover:bg-orange-50 transition-all disabled:opacity-30 text-sm">›</button>
    </div>

    <!-- Badges: geplant + gesamt (gesamt = upcoming + chronik) -->
    <div class="flex gap-2">
      {#if upcomingCount > 0}
        <button onclick={() => activeTab='trips'}
          class="text-xs font-medium px-2.5 py-1 rounded-full border border-orange-200 text-orange-600 bg-orange-50 hover:bg-orange-100 transition-colors">
          ✈️ {upcomingCount} geplant
        </button>
      {/if}
      <div class="text-xs font-medium px-2.5 py-1 rounded-full border border-stone-200 text-stone-500 bg-white">
        {totalCount} gesamt
      </div>
    </div>
  </div>

  <!-- ── Tabs ──────────────────────────────────────────────────────────────── -->
  <div class="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1">
    {#each tabs as tab}
      <button onclick={() => activeTab=tab.id}
        class="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all border"
        class:bg-orange-600={activeTab===tab.id} class:text-white={activeTab===tab.id}
        class:border-orange-600={activeTab===tab.id} class:bg-white={activeTab!==tab.id}
        class:text-stone-500={activeTab!==tab.id} class:border-stone-200={activeTab!==tab.id}>
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- ══════════════════════════════════════════════════════
       TAB 1 — ÜBERSICHT
  ══════════════════════════════════════════════════════ -->
  {#if activeTab === 'overview'}

    <!-- Stats: Reisen-Karte aufgeteilt + Budget + Verbleibend -->
    <div class="grid grid-cols-3 gap-3">

      <!-- Reisen {Jahr}: Vergangen + Geplant, klickbar -->
      <div class="{card} p-0 overflow-hidden col-span-1">
        <div class="grid grid-cols-2 h-full divide-x divide-stone-100">
          <button onclick={() => activeTab='journal'}
            class="p-4 text-center hover:bg-stone-50 transition-colors group">
            <div class="text-xl mb-1">✅</div>
            <div class="text-xs font-medium text-stone-400 uppercase tracking-wide mb-0.5">Vergangen</div>
            <div class="text-lg font-bold text-stone-800 group-hover:text-orange-600 transition-colors" style="font-family:var(--ws-serif)">
              {journalYear.length}
            </div>
          </button>
          <button onclick={() => activeTab='trips'}
            class="p-4 text-center hover:bg-stone-50 transition-colors group">
            <div class="text-xl mb-1">✈️</div>
            <div class="text-xs font-medium text-stone-400 uppercase tracking-wide mb-0.5">Geplant</div>
            <div class="text-lg font-bold text-stone-800 group-hover:text-orange-600 transition-colors" style="font-family:var(--ws-serif)">
              {upcomingCount}
            </div>
          </button>
        </div>
      </div>

      <!-- Ausgegeben -->
      <div class="{card} text-center">
        <div class="text-2xl mb-1">💸</div>
        <div class="text-xs font-medium text-stone-400 mb-0.5 uppercase tracking-wide">{$t('mytripsStatsSpent')}</div>
        <div class="text-lg font-bold text-orange-600" style="font-family:var(--ws-serif)">{totalSpentYear.toFixed(2)} €</div>
      </div>

      <!-- Verbleibend -->
      <div class="{card} text-center">
        <div class="text-2xl mb-1">💰</div>
        <div class="text-xs font-medium text-stone-400 mb-0.5 uppercase tracking-wide">{$t('mytripsStatsRemaining')}</div>
        <div class="text-lg font-bold text-emerald-700" style="font-family:var(--ws-serif)">
          {yearBudget > 0 ? remainingYear.toFixed(2) + ' €' : '–'}
        </div>
      </div>
    </div>

    <!-- Budget-Progress -->
    {#if yearBudget > 0}
      <div class={card}>
        <div class="flex justify-between text-xs text-stone-500 mb-2">
          <span>Budget-Fortschritt {selectedYear}</span>
          <span class="font-semibold {pctYear>85?'text-red-500':'text-stone-700'}">{pctYear.toFixed(0)}%</span>
        </div>
        <div class="h-2.5 rounded-full bg-stone-100 overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500"
            style="width:{pctYear}%;background:{pctYear>85?'#ef4444':pctYear>60?'#f97316':'#059669'}"></div>
        </div>
        <div class="flex justify-between text-xs text-stone-400 mt-2">
          <span>{totalSpentYear.toFixed(2)} € ausgegeben</span>
          <span>{yearBudget.toFixed(2)} € gesamt</span>
        </div>
        {#if journalSpentYear > 0 || tripsSpentYear > 0}
          <div class="flex gap-4 mt-3 pt-3 border-t border-stone-100 text-xs text-stone-400">
            <span>📓 Vergangen: <strong class="text-stone-600">{journalSpentYear.toFixed(2)} €</strong></span>
            <span>✈️ Geplant: <strong class="text-stone-600">{tripsSpentYear.toFixed(2)} €</strong></span>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Karte -->
    <div class="{card} !p-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-stone-700">🗺️ Meine Reisekarte — {selectedYear}</h2>
        <span class="text-xs text-stone-400">{journalYear.length} Chronik · {upcomingCount} geplant</span>
      </div>
      <ScratchMap {journalTrips} plannedTrips={$trips} {selectedYear} />
    </div>

    <!-- Nächste Abenteuer -->
    {#if upcomingTrips.length > 0}
      <div class={card}>
        <h2 class="text-sm font-semibold text-stone-700 mb-3">
          ✈️ Nächste Abenteuer
          <span class="ml-1 text-xs font-normal text-stone-400">({upcomingTrips.length})</span>
        </h2>
        <div class="space-y-2">
          {#each upcomingTrips.slice(0,4) as tr}
            {@const start = tr.dateStart||tr.date||''}
            {@const end   = tr.dateEnd||''}
            <div class="flex items-center gap-3 py-2 border-b border-stone-100 last:border-0">
              <span class="text-lg">✈️</span>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-semibold text-stone-800 truncate" style="font-family:var(--ws-serif)">{tr.name}</div>
                <div class="text-xs text-stone-400 font-mono">{start}{end&&end!==start?' → '+end:''}</div>
              </div>
              <div class="text-sm font-bold text-orange-600 font-mono shrink-0">{parseFloat(tr.cost).toFixed(2)} €</div>
            </div>
          {/each}
          {#if upcomingTrips.length > 4}
            <button onclick={() => activeTab='trips'} class="text-xs text-orange-600 hover:underline pt-1">
              + {upcomingTrips.length-4} weitere →
            </button>
          {/if}
        </div>
      </div>
    {/if}

    <!-- Letzte Erinnerungen -->
    {#if journalYear.length > 0}
      <div class={card}>
        <h2 class="text-sm font-semibold text-stone-700 mb-3">
          ✅ Letzte Erinnerungen — {selectedYear}
          <span class="ml-1 text-xs font-normal text-stone-400">({journalYear.length})</span>
        </h2>
        <div class="space-y-2">
          {#each journalYear.slice(0,4) as tr}
            {@const name  = tr.location_name||tr.name||'–'}
            {@const start = tr.start_date||''}
            {@const end   = tr.end_date||''}
            {@const cost  = tr.cost!=null ? parseFloat(tr.cost) : null}
            <div class="flex items-center gap-3 py-2 border-b border-stone-100 last:border-0">
              <span class="text-lg">{tr.source==='manual'?'✍️':'📍'}</span>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-semibold text-stone-800 truncate" style="font-family:var(--ws-serif)">{name}</div>
                <div class="text-xs text-stone-400 font-mono">{start}{end&&end!==start?' → '+end:''}</div>
              </div>
              {#if cost!=null}
                <div class="text-sm font-bold text-stone-500 font-mono shrink-0">{cost.toFixed(2)} €</div>
              {/if}
            </div>
          {/each}
          {#if journalYear.length > 4}
            <button onclick={() => activeTab='journal'} class="text-xs text-orange-600 hover:underline pt-1">
              + {journalYear.length-4} weitere →
            </button>
          {/if}
        </div>
      </div>
    {/if}

  <!-- ══════════════════════════════════════════════════════
       TAB 2 — GEPLANTE REISEN
  ══════════════════════════════════════════════════════ -->
  {:else if activeTab === 'trips'}
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

      <!-- 1/3 Links -->
      <div class="lg:col-span-1 space-y-4">

        <!-- Smart Planer -->
        <div class="bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-200 rounded-xl shadow-sm p-5 relative overflow-hidden">
          <span class="absolute top-3 right-3 text-[10px] font-bold uppercase tracking-wider bg-orange-600 text-white px-2 py-0.5 rounded-full">Bald verfügbar</span>
          <div class="text-xl mb-2">✨</div>
          <h3 class="font-bold text-stone-800 text-sm mb-1" style="font-family:var(--ws-serif)">Smart Reise-Planer</h3>
          <p class="text-xs text-stone-500 leading-relaxed">Budget, Personen & Zeitraum — WanderSuite findet Flüge, Mietwagen und Hotels auf einmal.</p>
        </div>

        <!-- Reise planen -->
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-3">➕ Reise planen</h3>
          <div class="space-y-2.5">
            <input bind:value={tripName} placeholder="Ziel / Name *" class={inp} />
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="text-xs text-stone-400 mb-1 block">Von *</label>
                <input type="date" bind:value={tripDateStart} class={inp} />
              </div>
              <div>
                <label class="text-xs text-stone-400 mb-1 block">Bis (opt.)</label>
                <input type="date" bind:value={tripDateEnd} class={inp} />
              </div>
            </div>
            <input type="number" bind:value={tripCost} placeholder="Budget / Kosten €" class={inp} />
            <button onclick={addTrip} class={btn} style="background:linear-gradient(135deg,#c4622d,#b84928)">+ Hinzufügen</button>
          </div>
        </div>
      </div>

      <!-- 2/3 Rechts -->
      <div class="lg:col-span-2 space-y-4">

        <!-- Budget Progress -->
        {#if yearBudget > 0}
          <div class={card}>
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-semibold text-stone-500 uppercase tracking-wide">Budget {selectedYear}</span>
              <span class="text-xs font-bold {pctYear>85?'text-red-500':'text-emerald-600'}">{pctYear.toFixed(0)}% verbraucht</span>
            </div>
            <div class="h-3 rounded-full bg-stone-100 overflow-hidden">
              <div class="h-full rounded-full transition-all duration-500"
                style="width:{pctYear}%;background:{pctYear>85?'#ef4444':pctYear>60?'#f97316':'#059669'}"></div>
            </div>
            <div class="flex justify-between text-xs text-stone-400 mt-1.5">
              <span>{totalSpentYear.toFixed(2)} € ausgegeben</span>
              <span class="text-emerald-600 font-medium">{remainingYear.toFixed(2)} € frei</span>
            </div>
          </div>
        {/if}

        <!-- Geplante -->
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-3">✈️ Nächste Abenteuer <span class="ml-1 text-xs font-normal text-stone-400">({upcomingTrips.length})</span></h3>
          {#if upcomingTrips.length === 0}
            <p class="text-sm text-stone-400 py-6 text-center">Noch keine Reisen geplant.</p>
          {:else}
            <div class="space-y-2">
              {#each upcomingTrips as tr}
                {@const start = tr.dateStart||tr.date||''}
                {@const end   = tr.dateEnd||''}
                {@const idx   = $trips.indexOf(tr)}
                <div class="flex items-center gap-3 p-3 rounded-lg bg-orange-50 border border-orange-100 hover:border-orange-200 transition-colors group">
                  <div class="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center shrink-0 text-base">✈️</div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-semibold text-stone-800 truncate" style="font-family:var(--ws-serif)">{tr.name}</div>
                    <div class="text-xs text-stone-400 font-mono">{start}{end&&end!==start?' → '+end:''}</div>
                  </div>
                  <div class="text-sm font-bold text-orange-600 font-mono shrink-0">{parseFloat(tr.cost).toFixed(2)} €</div>
                  <button onclick={() => removeTrip(idx)} class="opacity-0 group-hover:opacity-100 transition-opacity text-stone-400 hover:text-red-500 text-xs px-1.5 py-1 rounded border border-stone-200 hover:border-red-200">✕</button>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Vergangene (manuelle aus localStorage) -->
        {#if pastTrips.length > 0}
          <div class={card}>
            <h3 class="text-sm font-semibold text-stone-700 mb-3">✅ Vergangen (manuell) <span class="ml-1 text-xs font-normal text-stone-400">({pastTrips.length})</span></h3>
            <div class="space-y-2">
              {#each pastTrips as tr}
                {@const start = tr.dateStart||tr.date||''}
                {@const end   = tr.dateEnd||''}
                {@const idx   = $trips.indexOf(tr)}
                <div class="flex items-center gap-3 p-3 rounded-lg bg-stone-50 border border-stone-100 hover:border-stone-200 group transition-colors">
                  <div class="w-8 h-8 rounded-full bg-stone-100 flex items-center justify-center shrink-0 text-base">✅</div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-semibold text-stone-800 truncate" style="font-family:var(--ws-serif)">{tr.name}</div>
                    <div class="text-xs text-stone-400 font-mono">{start}{end&&end!==start?' → '+end:''}</div>
                  </div>
                  <div class="text-sm font-bold text-stone-500 font-mono shrink-0">{parseFloat(tr.cost).toFixed(2)} €</div>
                  <button onclick={() => removeTrip(idx)} class="opacity-0 group-hover:opacity-100 transition-opacity text-stone-400 hover:text-red-500 text-xs px-1.5 py-1 rounded border border-stone-200 hover:border-red-200">✕</button>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>

  <!-- ══════════════════════════════════════════════════════
       TAB 3 — REISECHRONIK
  ══════════════════════════════════════════════════════ -->
  {:else if activeTab === 'journal'}
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

      <!-- 1/3 Links: Formular + Budget + ActualBudget -->
      <div class="lg:col-span-1 space-y-4">

        <!-- Manuell erfassen -->
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-1">➕ Reise erfassen</h3>
          <p class="text-xs text-stone-400 mb-3">Manuell eintragen — kein Dawarich nötig.</p>
          <div class="space-y-2.5">
            <input bind:value={mName}    placeholder="Ort / Name *"       class={inp} />
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="text-xs text-stone-400 mb-1 block">Von *</label>
                <input type="date" bind:value={mStart} class={inp} />
              </div>
              <div>
                <label class="text-xs text-stone-400 mb-1 block">Bis</label>
                <input type="date" bind:value={mEnd}   class={inp} />
              </div>
            </div>
            <input bind:value={mCountry} placeholder="Land (optional)" class={inp} />
            <input type="number" bind:value={mCost} placeholder="Kosten € (optional)" class={inp} />
            <button onclick={addManualTrip} disabled={mAdding||!$apiUrl}
              class="{btn} disabled:opacity-50" style="background:linear-gradient(135deg,#c4622d,#b84928)">
              {mAdding ? '⏳…' : '+ Hinzufügen'}
            </button>
          </div>
        </div>

        <!-- Jahresbudget (hier, wo echte Kosten anfallen) -->
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-3">💶 Jahresbudget {selectedYear}</h3>
          <input type="number" bind:value={budgetInput} placeholder="z.B. 4000" class="{inp} mb-3" />
          <button onclick={saveBudget} disabled={budgetSaving}
            class="{btn} disabled:opacity-50" style="background:linear-gradient(135deg,#c4622d,#b84928)">
            {budgetSaving ? '⏳…' : 'Speichern'}
          </button>
        </div>

        <!-- ActualBudget Sync -->
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-1">{$t('mytripsActualSync')}</h3>
          <p class="text-xs text-stone-400 mb-3">{$t('mytripsActualDesc')}</p>
          <button onclick={syncActual} disabled={actualSyncing||!$apiUrl}
            class="w-full py-2 px-4 rounded-lg text-sm font-semibold border border-stone-200 bg-stone-50 text-stone-700 hover:border-orange-300 hover:text-orange-600 transition-all disabled:opacity-40">
            {actualSyncing ? '⏳ Sync…' : '🔄 Synchronisieren'}
          </button>
          {#if actualResult?.transactions?.length}
            <div class="mt-3 pt-3 border-t border-stone-100 space-y-1 max-h-40 overflow-y-auto">
              {#each actualResult.transactions.slice(0,12) as tx}
                <div class="flex justify-between text-xs py-1 border-b border-stone-50">
                  <span class="truncate flex-1 mr-2 text-stone-600">{tx.payee_name||tx.notes||'–'}</span>
                  <span class="font-mono font-bold text-orange-600 shrink-0">{Math.abs(tx.amount??0).toFixed(2)} €</span>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Dawarich Sync -->
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-1">🧭 Dawarich Sync</h3>
          <p class="text-xs text-stone-400 mb-3">GPS-Reisen automatisch erkennen.</p>
          <button onclick={syncJournal} disabled={syncing||!$apiUrl}
            class="w-full py-2 px-4 rounded-lg text-sm font-semibold border border-stone-200 bg-stone-50 text-stone-700 hover:border-orange-300 hover:text-orange-600 transition-all disabled:opacity-50">
            {syncing ? '⏳ Sync…' : '🧭 Synchronisieren'}
          </button>
          {#if syncInfo}
            <p class="text-xs text-stone-400 mt-2">ℹ️ {syncInfo}</p>
          {/if}
        </div>
      </div>

      <!-- 2/3 Rechts: Timeline gefiltert nach Jahr -->
      <div class="lg:col-span-2">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-stone-700">
            Reisen {selectedYear}
            <span class="ml-1 text-xs font-normal text-stone-400">({journalYear.length})</span>
          </h3>
          {#if journalTrips.length !== journalYear.length}
            <span class="text-xs text-stone-400">Gesamt: {journalTrips.length}</span>
          {/if}
        </div>

        {#if !$apiUrl}
          <div class="{card} text-center py-12"><div class="text-4xl mb-3">🔌</div><p class="text-sm text-stone-400">{$t('journalNoBackend')}</p></div>
        {:else if journalLoad}
          <div class="space-y-3">{#each [1,2,3] as _}<div class="h-20 rounded-xl bg-stone-100 animate-pulse"></div>{/each}</div>
        {:else if journalYear.length === 0}
          <div class="{card} text-center py-12">
            <div class="text-4xl mb-3">🗺️</div>
            <p class="text-sm font-semibold text-stone-700 mb-1">Keine Reisen in {selectedYear}</p>
            <p class="text-xs text-stone-400 mb-4">Links manuell erfassen oder Dawarich synchronisieren.</p>
          </div>
        {:else}
          <div class="relative pl-6">
            <div class="absolute left-2.5 top-2 bottom-2 w-0.5 bg-stone-200 rounded-full"></div>
            {#each journalYear as trip}
              {@const loc      = trip.location_name || trip.name || '–'}
              {@const mapsUrl  = trip.lat&&trip.lon ? `https://www.google.com/maps?q=${trip.lat},${trip.lon}` : null}
              {@const isManual = trip.source==='manual'}
              <div class="relative pb-4">
                <div class="absolute -left-6 top-4 w-4 h-4 rounded-full border-2 border-white shadow-sm z-10"
                  style="background:{isManual?'#6366f1':'linear-gradient(135deg,#c4622d,#b84928)'}"></div>
                <div class="{card} ml-2 hover:shadow-md transition-shadow">
                  <div class="flex items-start justify-between gap-3">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 flex-wrap">
                        <span class="font-bold text-stone-800 truncate" style="font-family:var(--ws-serif)">
                          {isManual?'✍️':'📍'} {loc}
                        </span>
                        {#if isManual}
                          <span class="text-[10px] bg-indigo-100 text-indigo-600 px-1.5 py-0.5 rounded font-semibold shrink-0">manuell</span>
                        {/if}
                      </div>
                      <div class="text-xs text-stone-400 font-mono mt-0.5">{trip.start_date} → {trip.end_date}</div>
                      {#if trip.country}
                        <div class="text-xs text-stone-400 mt-0.5">🌍 {trip.country}</div>
                      {/if}
                    </div>
                    <span class="shrink-0 px-2.5 py-1 rounded-full text-xs font-bold" style="background:rgba(196,98,45,.1);color:#c4622d">
                      {trip.nights} {trip.nights===1?'Nacht':'Nächte'}
                    </span>
                  </div>
                  <!-- Kosten inline -->
                  <div class="mt-3 flex items-center gap-2 flex-wrap">
                    {#if editingCost === trip.id}
                      <input type="number" bind:value={costDraft} placeholder="Kosten €"
                        class="flex-1 min-w-0 bg-stone-50 border border-stone-200 text-stone-800 text-xs rounded-lg px-2.5 py-1.5 outline-none focus:border-orange-500"
                        onkeydown={(e) => e.key==='Enter' && saveCost(trip)} />
                      <button onclick={() => saveCost(trip)} class="px-3 py-1.5 rounded-lg text-xs font-semibold text-white shrink-0" style="background:#c4622d">✓</button>
                      <button onclick={() => editingCost=null} class="px-2 py-1.5 rounded-lg text-xs border border-stone-200 text-stone-400 shrink-0">✕</button>
                    {:else}
                      <button onclick={() => { editingCost=trip.id; costDraft=trip.cost!=null?String(trip.cost):''; }}
                        class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs border transition-colors
                               {trip.cost!=null?'border-orange-200 bg-orange-50 text-orange-600 font-semibold':'border-stone-200 text-stone-400 hover:border-orange-200 hover:text-orange-500'}">
                        💶 {trip.cost!=null ? parseFloat(trip.cost).toFixed(2)+' €' : 'Kosten hinterlegen'}
                      </button>
                    {/if}
                    <div class="flex gap-1.5 ml-auto">
                      {#if mapsUrl}
                        <a href={mapsUrl} target="_blank" class="py-1.5 px-2.5 rounded-lg text-xs border border-stone-200 text-stone-500 hover:border-orange-300 hover:text-orange-600 transition-colors">🗺</a>
                      {/if}
                      <button onclick={() => deleteJournalTrip(trip.id)} class="py-1.5 px-2.5 rounded-lg text-xs border border-stone-200 text-stone-400 hover:border-red-200 hover:text-red-500 transition-colors">✕</button>
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

  <!-- ══════════════════════════════════════════════════════
       TAB 4 — BUCKET LIST
  ══════════════════════════════════════════════════════ -->
  {:else if activeTab === 'bucketlist'}
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
      <div class="lg:col-span-1">
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-3">🌟 {$t('mytripsBucketAdd')}</h3>
          <div class="space-y-2.5">
            <input bind:value={bucketItem} placeholder={$t('mytripsBucketItemPlaceholder')} class={inp} />
            <input bind:value={bucketDest} placeholder={$t('mytripsBucketDestPlaceholder')} class={inp} />
            <button onclick={addBucketItem} class={btn} style="background:linear-gradient(135deg,#c4622d,#b84928)">{$t('mytripsAddBtn')}</button>
          </div>
          {#if $bucketlist.length > 0}
            <div class="mt-4 pt-4 border-t border-stone-100 text-xs text-stone-400 text-center">
              {$bucketlist.filter(x=>x.done).length} / {$bucketlist.length} erledigt
            </div>
          {/if}
        </div>
      </div>
      <div class="lg:col-span-2">
        {#if $bucketlist.length === 0}
          <div class="{card} text-center py-14"><div class="text-5xl mb-3">🌍</div><p class="text-sm text-stone-400">{$t('mytripsBucketEmpty')}</p></div>
        {:else}
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {#each $bucketlist as item, i}
              <div class="group relative {card} transition-all hover:shadow-md" class:opacity-50={item.done}>
                <button onclick={() => toggleBucket(i)} class="absolute top-4 right-4 w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs transition-all" style="border-color:{item.done?'#059669':'#d1d5db'};background:{item.done?'#059669':'transparent'};color:white">{item.done?'✓':''}</button>
                <button onclick={() => removeBucket(i)} class="absolute top-4 right-12 w-6 h-6 rounded-full border border-stone-200 flex items-center justify-center text-xs text-stone-400 hover:text-red-500 hover:border-red-200 opacity-0 group-hover:opacity-100 transition-all">✕</button>
                <div class="text-2xl mb-2">🌟</div>
                <div class="text-sm font-semibold text-stone-800 pr-14" style="font-family:var(--ws-serif)" class:line-through={item.done}>{item.item}</div>
                {#if item.dest}<div class="text-xs text-stone-400 mt-1">📍 {item.dest}</div>{/if}
                <div class="text-xs text-stone-300 mt-2 font-mono">{item.created}</div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
