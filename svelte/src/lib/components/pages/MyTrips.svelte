<script>
  import { trips, budget, bucketlist, apiUrl, activeWsTripId, currentPage, previousPage, activeMyTripsTab } from '$lib/stores.js';
  import { get as storeGet } from 'svelte/store';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';
  import { t } from '$lib/i18n.js';

  import ScratchMap    from '$lib/components/ScratchMap.svelte';
  import BucketListTab from '$lib/components/mytrips/BucketListTab.svelte';
  import JournalTimeline from '$lib/components/mytrips/JournalTimeline.svelte';
  import JournalSyncDawarich from '$lib/components/mytrips/JournalSyncDawarich.svelte';
  import JournalSyncActual   from '$lib/components/mytrips/JournalSyncActual.svelte';
  import TripCard from '$lib/components/mytrips/TripCard.svelte';

  // ── Tabs ───────────────────────────────────────────────────────────────────
  // Restore tab if returning from TripHub
  let activeTab  = $state(storeGet(activeMyTripsTab));

  // Keep store in sync whenever tab changes
  $effect(() => { activeMyTripsTab.set(activeTab); });
  let viewMode   = $state('grid'); // 'grid' | 'list'

  const tabs = $derived([
    { id: 'overview',   label: $t('tabOverview') },
    { id: 'planned',    label: $t('tabPlanned') },
    { id: 'ontour',     label: $t('tabOnTour') },
    { id: 'archive',    label: $t('tabArchive') },
    { id: 'bucketlist', label: $t('tabBucketList') },
  ]);

  // "On Tour" filter: trips where start_date <= today <= end_date
  const onTourTrips = $derived(
    wsTrips.filter(t => {
      const s = (t.start_date || '').slice(0, 10);
      const e = (t.end_date   || t.start_date || '').slice(0, 10);
      return s && e && today >= s && today <= e;
    })
  );

  // ── Jahr ───────────────────────────────────────────────────────────────────
  const currentYear = new Date().getFullYear();
  let selectedYear  = $state(currentYear);
  const today       = new Date().toISOString().slice(0, 10);
  // Changes whenever tab or year changes — forces ScratchMap redraw
  const mapRefreshKey = $derived(`${activeTab}-${selectedYear}`);

  // ── Budget ─────────────────────────────────────────────────────────────────
  let budgetByYear  = $state({});
  let budgetInput   = $state('');
  let budgetSaving  = $state(false);
  let budgetEditing = $state(false);
  const yearBudget  = $derived(parseFloat(budgetByYear[String(selectedYear)]) || 0);

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
      budgetEditing = false;
      toast(`Budget ${selectedYear}: ${amount.toFixed(0)} € gespeichert ✓`, 'success');
    } catch (e) { toast(e.message, 'error'); }
    budgetSaving = false;
  }

  // ── WS-Trips (WanderWizzard) ───────────────────────────────────────────────
  let wsTrips     = $state([]);
  let wsTripsLoad = $state(false);

  // FIX: "Geplant" zeigt nur strikt zukünftige Trips (start_date > heute)
  // "On Tour" zeigt laufende — keine Doppelung
  const plannedWsTrips = $derived(
    wsTrips.filter(t => {
      const s = (t.start_date || '').slice(0, 10);
      return (t.status === 'planning' || t.status === 'booked') && (!s || s > today);
    })
  );

  async function loadWsTrips() {
    if (!$apiUrl) return;
    wsTripsLoad = true;
    try { wsTrips = await api('/api/ws-trips'); } catch {}
    wsTripsLoad = false;
  }

  function goToTripHub(id) {
    // Speichere den aktiven Tab damit TripHub "Zurück" zum richtigen Tab führt
    previousPage.set(activeTab);
    activeWsTripId.set(id);
    currentPage.set('triphub');
  }

  // ── Archive (Reisechronik) ─────────────────────────────────────────────────
  let journalTrips = $state([]);
  let journalLoad  = $state(false);
  let editingCost  = $state(null);
  let costDraft    = $state('');

  const journalYear = $derived(
    journalTrips.filter(t => (t.start_date || '').slice(0, 4) === String(selectedYear))
  );
  const journalSpentYear = $derived(
    journalYear.reduce((s, t) => s + (parseFloat(t.cost ?? t.auto_cost) || 0), 0)
  );

  async function loadJournal() {
    if (!$apiUrl) return;
    journalLoad = true;
    try { journalTrips = await api('/api/trips'); } catch (e) { toast('Fehler: ' + e.message, 'error'); }
    journalLoad = false;
  }

  async function deleteJournalTrip(id) {
    if (!confirm('Eintrag löschen?')) return;
    try { await api(`/api/trips/${id}`, { method: 'DELETE' }); toast('Gelöscht ✓', 'success'); } catch (e) { toast(e.message, 'error'); }
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

  // ── Add trip modal ─────────────────────────────────────────────────────────
  let addModalOpen = $state(false);
  let mName  = $state('');
  let mStart = $state(new Date().toISOString().slice(0, 10));
  let mEnd   = $state('');
  let mCost  = $state('');
  let mAdding = $state(false);

  async function addManualTrip() {
    if (!mName || !mStart) { toast('Name + Startdatum pflicht', 'error'); return; }
    mAdding = true;
    try {
      await api('/api/trips', { method: 'POST', body: JSON.stringify({
        name: mName, start_date: mStart, end_date: mEnd || mStart,
        cost: mCost ? parseFloat(mCost) : null,
      }) });
      mName = ''; mEnd = ''; mCost = '';
      addModalOpen = false;
      toast('Reise eingetragen ✓', 'success');
      await loadJournal();
    } catch (e) { toast(e.message, 'error'); }
    mAdding = false;
  }

  // ── Dawarich Sync ──────────────────────────────────────────────────────────
  let syncing   = $state(false);
  let syncInfo  = $state('');
  let forceFull = $state(false);

  async function syncJournal() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const url   = browser ? localStorage.getItem('s-dawarichUrl')   || '' : '';
    const token = browser ? localStorage.getItem('s-dawarichToken') || '' : '';
    const lat   = parseFloat(browser ? localStorage.getItem('s-homeLat') || '0' : '0');
    const lon   = parseFloat(browser ? localStorage.getItem('s-homeLon') || '0' : '0');
    syncing = true; syncInfo = '';
    try {
      const body = (url && token)
        ? JSON.stringify({ dawarich_url: url, dawarich_token: token, home_lat: lat || null, home_lon: lon || null, force_full: forceFull })
        : JSON.stringify({ force_full: forceFull });
      const r = await api('/api/dawarich/sync', { method: 'POST', body });
      syncInfo = `${r.points_loaded} Punkte · ${r.trips_detected} erkannt`;
      toast(`${r.trips_detected} Reisen erkannt ✓`, 'success');
      await loadJournal();
    } catch (e) { toast('Sync-Fehler: ' + e.message, 'error'); }
    syncing = false;
  }

  // ── ActualBudget Sync ──────────────────────────────────────────────────────
  let actualSyncing   = $state(false);
  let actualResult    = $state(null);
  let actualFiles     = $state([]);
  let actualFilesLoad = $state(false);
  let autoCostRunning = $state(false);
  let autoCostResult  = $state(null);

  async function listActualFiles() {
    const url   = browser ? localStorage.getItem('s-actualUrl')      || '' : '';
    const token = browser ? localStorage.getItem('s-actualPassword') || '' : '';
    if (!url || !token) { toast('ActualBudget URL + Passwort fehlen → Einstellungen', 'warning'); return; }
    actualFilesLoad = true;
    try { const r = await api('/api/budget/actual/list-files', { method: 'POST', body: JSON.stringify({ actual_url: url, actual_token: token }) }); actualFiles = r.files || []; } catch (e) { toast(e.message, 'error'); }
    actualFilesLoad = false;
  }

  async function syncActual() {
    const url      = browser ? localStorage.getItem('s-actualUrl')        || '' : '';
    const password = browser ? localStorage.getItem('s-actualPassword')   || '' : '';
    const file     = browser ? localStorage.getItem('s-actualFile')       || '' : '';
    const cats     = browser ? localStorage.getItem('s-travelCategories') || '' : '';
    if (!url || !password) { toast('ActualBudget URL + Passwort fehlen → Einstellungen', 'warning'); return; }
    actualSyncing = true;
    try { const r = await api('/api/budget/actual/transactions', { method: 'POST', body: JSON.stringify({ actual_url: url, actual_token: password, actual_file: file || null, categories: cats || null }) }); actualResult = r; toast(`${r.transactions?.length ?? 0} Transaktionen ✓`, 'success'); } catch (e) { toast(e.message, 'error'); }
    actualSyncing = false;
  }

  async function runAutoCost() {
    const url      = browser ? localStorage.getItem('s-actualUrl')        || '' : '';
    const password = browser ? localStorage.getItem('s-actualPassword')   || '' : '';
    const file     = browser ? localStorage.getItem('s-actualFile')       || '' : '';
    const cats     = browser ? localStorage.getItem('s-travelCategories') || '' : '';
    if (!url || !password) { toast('URL + Passwort fehlen', 'warning'); return; }
    autoCostRunning = true;
    try { const r = await api('/api/trips/auto-cost', { method: 'POST', body: JSON.stringify({ actual_url: url, actual_token: password, actual_file: file || null, categories: cats || null }) }); autoCostResult = r; toast(`${r.trips_updated} Reisen verknüpft ✓`, 'success'); await loadJournal(); } catch (e) { toast(e.message, 'error'); }
    autoCostRunning = false;
  }

  // ── Overview derived ───────────────────────────────────────────────────────
  const totalSpentYear = $derived(journalSpentYear);
  const remainingYear  = $derived(Math.max(0, yearBudget - totalSpentYear));
  const pctYear        = $derived(yearBudget > 0 ? Math.min(100, (totalSpentYear / yearBudget) * 100) : 0);
  const overBudget     = $derived(yearBudget > 0 && totalSpentYear > yearBudget);

  const donutGradient = $derived.by(() => {
    if (yearBudget <= 0) return 'conic-gradient(var(--ws-border) 0deg 360deg)';
    const pastDeg = Math.min(360, (journalSpentYear / yearBudget) * 360);
    const overDeg = overBudget ? Math.min(360, ((totalSpentYear - yearBudget) / yearBudget) * 360) : 0;
    const restDeg = 360 - pastDeg - overDeg;
    let grad = ''; let cur = 0;
    if (pastDeg > 0) { grad += `#2d6a4f ${cur}deg ${cur + pastDeg}deg,`; cur += pastDeg; }
    if (overDeg > 0) { grad += `#ef4444 ${cur}deg ${cur + overDeg}deg,`; cur += overDeg; }
    if (restDeg > 0) { grad += `var(--ws-border) ${cur}deg ${cur + restDeg}deg,`; }
    return `conic-gradient(${grad.slice(0, -1)})`;
  });

  // ── Bucket list ────────────────────────────────────────────────────────────
  // Bucket state is managed inside BucketListTab.svelte
  // addBucketItem is now inline in the BucketListTab onadd callback
  function toggleBucket(i) { bucketlist.update(l => l.map((x, idx) => idx === i ? { ...x, done: !x.done } : x)); }
  function removeBucket(i) { bucketlist.update(l => l.filter((_, idx) => idx !== i)); }

  // ── Load on mount ──────────────────────────────────────────────────────────
  $effect(() => {
    if ($apiUrl) { loadJournal(); loadBudget(); loadWsTrips(); }
  });

  const inp  = 'text-sm rounded-lg focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 p-2.5 w-full outline-none transition-all border';
  const card = 'rounded-xl shadow-sm p-5 border';
  const btn  = 'w-full py-2.5 px-4 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-[.98]';
</script>

<!-- ── Add Trip Modal ────────────────────────────────────────────────────── -->
{#if addModalOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center" style="background:rgba(0,0,0,.45);backdrop-filter:blur(4px)" role="dialog">
    <div class="w-full max-w-sm mx-4 rounded-2xl shadow-2xl border p-6 space-y-4" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h3 class="font-bold text-base" style="color:var(--ws-text)">{$t('addTripTitle')}</h3>
      <input bind:value={mName} placeholder={$t('addTripDest')} class={inp} style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="text-xs mb-1 block" style="color:var(--ws-muted)">{$t('addTripStart')}</label>
          <input type="date" bind:value={mStart} class={inp} style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>
        <div>
          <label class="text-xs mb-1 block" style="color:var(--ws-muted)">{$t('addTripEnd')}</label>
          <input type="date" bind:value={mEnd} class={inp} style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>
      </div>
      <input type="number" bind:value={mCost} placeholder={$t('addTripCost')} class={inp} style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <div class="flex gap-3">
        <button onclick={() => addModalOpen = false} class="flex-1 py-2.5 rounded-xl border text-sm font-semibold hover:opacity-70" style="border-color:var(--ws-border);color:var(--ws-muted)">{$t('addTripCancel')}</button>
        <button onclick={addManualTrip} disabled={mAdding} class="flex-1 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40" style="background:var(--ws-accent);color:#fff5ec">
          {mAdding ? '⏳' : $t('addTripSave')}
        </button>
      </div>
    </div>
  </div>
{/if}

<div class="w-full space-y-4">

  <!-- ── Tab Bar ─────────────────────────────────────────────────────────── -->
  <div class="flex items-center gap-1 overflow-x-auto pb-1">
    {#each tabs as tab}
      <button onclick={() => activeTab = tab.id}
        class="shrink-0 px-4 py-2 rounded-xl text-sm font-semibold transition-all whitespace-nowrap"
        style={activeTab === tab.id
          ? 'background:var(--ws-accent);color:#fff5ec'
          : 'background:var(--ws-surface2);color:var(--ws-muted)'}>
        {tab.label}
      </button>
    {/each}
    <!-- View toggle (planned + archive) -->
    {#if activeTab === 'planned' || activeTab === 'ontour' || activeTab === 'archive'}
      <div class="ml-auto flex items-center gap-1 shrink-0">
        <button onclick={() => viewMode = 'grid'}
          class="p-2 rounded-xl border transition-all"
          style={viewMode === 'grid'
            ? 'background:var(--ws-accent);color:#fff5ec;border-color:var(--ws-accent)'
            : 'background:var(--ws-surface2);color:var(--ws-muted);border-color:var(--ws-border)'}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
            <rect x="0" y="0" width="6" height="6" rx="1"/><rect x="8" y="0" width="6" height="6" rx="1"/>
            <rect x="0" y="8" width="6" height="6" rx="1"/><rect x="8" y="8" width="6" height="6" rx="1"/>
          </svg>
        </button>
        <button onclick={() => viewMode = 'list'}
          class="p-2 rounded-xl border transition-all"
          style={viewMode === 'list'
            ? 'background:var(--ws-accent);color:#fff5ec;border-color:var(--ws-accent)'
            : 'background:var(--ws-surface2);color:var(--ws-muted);border-color:var(--ws-border)'}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
            <rect x="0" y="1" width="14" height="2" rx="1"/><rect x="0" y="6" width="14" height="2" rx="1"/>
            <rect x="0" y="11" width="14" height="2" rx="1"/>
          </svg>
        </button>
      </div>
    {/if}
  </div>

  <!-- ══ OVERVIEW ══════════════════════════════════════════════════════════ -->
  {#if activeTab === 'overview'}
    <div class="space-y-5">
      <!-- Year selector compact row -->
      <div class="flex items-center justify-end gap-2">
        <span class="text-xs" style="color:var(--ws-muted)">{$t('yearSelect')}:</span>
        {#each [selectedYear - 1, selectedYear, selectedYear + 1] as yr}
          <button onclick={() => selectedYear = yr}
            class="px-3 py-1 rounded-full text-xs font-semibold transition-all"
            style={selectedYear === yr
              ? 'background:var(--ws-accent);color:#fff5ec'
              : 'background:var(--ws-surface2);border:1px solid var(--ws-border);color:var(--ws-muted)'}>
            {yr}
          </button>
        {/each}
      </div>
      <!-- Stats row -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        {#each [
          ['🗺️', journalTrips.length, 'Reisen gesamt'],
          ['📅', journalYear.length, `Reisen ${selectedYear}`],
          ['💶', yearBudget > 0 ? remainingYear.toFixed(0) + ' €' : '—', 'Budget frei'],
          ['🌟', $bucketlist.filter(b=>!b.done).length, 'Wunschziele'],
        ] as [icon, val, label]}
          <div class="rounded-xl border p-4 text-center" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="text-2xl mb-1">{icon}</div>
            <div class="text-xl font-bold" style="color:var(--ws-text)">{val}</div>
            <div class="text-xs" style="color:var(--ws-muted)">{label}</div>
          </div>
        {/each}
      </div>

      <!-- Donut + Map row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <!-- Budget Donut -->
        {#if yearBudget > 0}
          <div class="rounded-xl border p-5" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <h3 class="text-sm font-semibold mb-4" style="color:var(--ws-text)">💶 Budget {selectedYear}</h3>
            <div class="flex items-center gap-5">
              <div class="relative w-24 h-24 shrink-0">
                <div class="w-24 h-24 rounded-full" style="background:{donutGradient}"></div>
                <div class="absolute inset-3 rounded-full flex items-center justify-center" style="background:var(--ws-surface2)">
                  <span class="text-xs font-bold" style="color:var(--ws-text)">{pctYear.toFixed(0)}%</span>
                </div>
              </div>
              <div class="space-y-1.5 text-xs">
                <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm shrink-0" style="background:#2d6a4f"></span><span style="color:var(--ws-muted)">Ausgegeben: <strong style="color:var(--ws-text)">{totalSpentYear.toFixed(0)} €</strong></span></div>
                <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm shrink-0" style="background:var(--ws-border)"></span><span style="color:var(--ws-muted)">Verfügbar: <strong style="color:var(--ws-text)">{remainingYear.toFixed(0)} €</strong></span></div>
                {#if overBudget}<div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm shrink-0" style="background:#ef4444"></span><span class="text-red-500 font-semibold">Überschritten!</span></div>{/if}
              </div>
            </div>
          </div>
        {/if}


      </div>

      <!-- World map -->
      <div class="rounded-xl border overflow-hidden" style="border-color:var(--ws-border)">
        <ScratchMap journalTrips={journalYear} plannedTrips={[]} selectedYear={String(selectedYear)} refreshKey={mapRefreshKey} />
      </div>
    </div>

  <!-- ══ PLANNED TRIPS ══════════════════════════════════════════════════════ -->
  {:else if activeTab === 'planned'}
    <div class="space-y-4">
      {#if wsTripsLoad}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each [1,2,3] as _}<div class="rounded-2xl border p-5 animate-pulse h-40" style="background:var(--ws-surface2);border-color:var(--ws-border)"></div>{/each}
        </div>
      {:else if plannedWsTrips.length === 0}
        <div class="rounded-2xl border p-10 text-center space-y-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <p class="text-4xl">🗺️</p>
          <p class="text-sm" style="color:var(--ws-muted)">{$t('plannedEmpty')}</p>
          <button onclick={() => currentPage.set('planer')}
            class="px-5 py-2 rounded-xl text-sm font-semibold"
            style="background:var(--ws-accent);color:#fff5ec">
            🧙 {$t('navPlaner')}
          </button>
        </div>
      {:else if viewMode === 'list'}
        <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
          {#each plannedWsTrips as trip, i}
            <div class="flex items-center gap-4 px-5 py-3 transition-all hover:opacity-90 cursor-pointer {i > 0 ? 'border-t' : ''}"
              style="background:var(--ws-surface);border-color:var(--ws-border)"
              role="button" tabindex="0"
              onclick={() => goToTripHub(trip.id)}
              onkeydown={(e) => e.key === 'Enter' && goToTripHub(trip.id)}>
              <span class="text-2xl shrink-0">{trip.travel_mode === 'car' ? '🚗' : '✈️'}</span>
              <div class="flex-1 min-w-0">
                <div class="font-semibold text-sm truncate" style="font-family:var(--ws-serif);color:var(--ws-text)">{trip.title || trip.destination || 'Reise'}</div>
                {#if trip.destination}<div class="text-xs" style="color:var(--ws-muted)">📍 {trip.destination}</div>{/if}
              </div>
              {#if trip.start_date}
                <div class="text-xs font-mono shrink-0" style="color:var(--ws-muted)">{trip.start_date}{trip.end_date && trip.end_date !== trip.start_date ? ' → ' + trip.end_date : ''}</div>
              {/if}
              <span class="text-xs px-2 py-0.5 rounded-full font-semibold shrink-0"
                style="background:color-mix(in srgb,var(--ws-accent) 12%,var(--ws-surface));color:var(--ws-accent)">
                {trip.status === 'booked' ? $t('tripHubStatusBooked') : $t('tripHubStatusPlanning')}
              </span>
              <span style="color:var(--ws-muted)">›</span>
            </div>
          {/each}
        </div>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4">
          {#each plannedWsTrips as trip}
            <TripCard
              {trip}
              mode="planned"
              ongoToHub={(t) => goToTripHub(t.id)}
            />
          {/each}
        </div>
      {/if}
    </div>

  <!-- ══ ON TOUR ═══════════════════════════════════════════════════════════ -->
  {:else if activeTab === 'ontour'}
    <div class="space-y-4">
      {#if wsTripsLoad}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each [1,2,3] as _}<div class="rounded-2xl border p-5 animate-pulse h-40" style="background:var(--ws-surface2);border-color:var(--ws-border)"></div>{/each}
        </div>
      {:else if onTourTrips.length === 0}
        <div class="rounded-2xl border p-10 text-center space-y-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <p class="text-4xl">🌍</p>
          <p class="text-sm font-semibold" style="color:var(--ws-text)">{$t('onTourEmpty') || 'Gerade keine aktive Reise'}</p>
          <p class="text-xs" style="color:var(--ws-muted)">{$t('onTourEmptyHint') || 'Reisen die heute stattfinden erscheinen hier'}</p>
        </div>
      {:else if viewMode === 'list'}
        <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
          {#each onTourTrips as trip, i}
            <div class="flex items-center gap-4 px-5 py-3 transition-all hover:opacity-90 cursor-pointer {i > 0 ? 'border-t' : ''}"
              style="background:var(--ws-surface);border-color:var(--ws-border)"
              role="button" tabindex="0"
              onclick={() => goToTripHub(trip.id)}
              onkeydown={(e) => e.key === 'Enter' && goToTripHub(trip.id)}>
              <span class="text-2xl shrink-0">{trip.travel_mode === 'car' ? '🚗' : '✈️'}</span>
              <div class="flex-1 min-w-0">
                <div class="font-semibold text-sm truncate" style="font-family:var(--ws-serif);color:var(--ws-text)">{trip.title || trip.destination || 'Reise'}</div>
                {#if trip.destination}<div class="text-xs" style="color:var(--ws-muted)">📍 {trip.destination}</div>{/if}
              </div>
              {#if trip.start_date}
                <div class="text-xs font-mono shrink-0" style="color:var(--ws-muted)">{trip.start_date}{trip.end_date && trip.end_date !== trip.start_date ? ' → ' + trip.end_date : ''}</div>
              {/if}
              <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold shrink-0"
                style="background:rgba(45,106,79,.15);color:var(--ws-green,#2d6a4f)">
                <span class="w-1.5 h-1.5 rounded-full animate-pulse" style="background:var(--ws-green,#2d6a4f)"></span>
                ON TOUR
              </span>
              <span style="color:var(--ws-muted)">›</span>
            </div>
          {/each}
        </div>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4">
          {#each onTourTrips as trip}
            <TripCard
              {trip}
              mode="planned"
              ongoToHub={(t) => goToTripHub(t.id)}
            />
          {/each}
        </div>
      {/if}
    </div>

  <!-- ══ ARCHIVE (Reisechronik) ══════════════════════════════════════════════ -->
  {:else if activeTab === 'archive'}
    <div class="space-y-4">

      <!-- Admin Bar -->
      <div class="flex items-center gap-2 flex-wrap rounded-xl border px-4 py-2.5" style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <!-- Inline Budget -->
        {#if !budgetEditing}
          <button onclick={() => budgetEditing = true}
            class="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all hover:opacity-80"
            style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)">
            💰 {yearBudget > 0 ? `${yearBudget.toFixed(0)} €` : $t('archiveBudgetBtn')} ✎
          </button>
        {:else}
          <div class="flex items-center gap-1.5">
            <input type="number" bind:value={budgetInput} placeholder="0"
              class="w-24 px-2 py-1 text-xs rounded-lg border focus:outline-none focus:ring-1"
              style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"
              onkeydown={(e) => { if (e.key === 'Enter') saveBudget(); if (e.key === 'Escape') budgetEditing = false; }}/>
            <span class="text-xs" style="color:var(--ws-muted)">€</span>
            <button onclick={saveBudget} disabled={budgetSaving}
              class="px-2 py-1 rounded-lg text-xs font-bold disabled:opacity-40"
              style="background:var(--ws-accent);color:#fff5ec">{budgetSaving ? '⏳' : '✓'}</button>
            <button onclick={() => budgetEditing = false} class="px-2 py-1 text-xs" style="color:var(--ws-muted)">✕</button>
          </div>
        {/if}

        <!-- Dawarich -->
        <button onclick={syncJournal} disabled={syncing}
          class="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all hover:opacity-80 disabled:opacity-40"
          style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)">
          {syncing ? '⏳' : $t('archiveDawarichSync')}
        </button>

        <!-- ActualBudget -->
        <button onclick={syncActual} disabled={actualSyncing}
          class="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all hover:opacity-80 disabled:opacity-40"
          style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)">
          {actualSyncing ? '⏳' : $t('archiveActualSync')}
        </button>

        <!-- Spacer -->
        <div class="flex-1"></div>

        <!-- Year compact selector -->
        <div class="flex items-center gap-1">
          {#each [selectedYear - 1, selectedYear, selectedYear + 1] as yr}
            <button onclick={() => selectedYear = yr}
              class="px-2.5 py-1 rounded-lg text-xs font-semibold transition-all"
              style={selectedYear === yr
                ? 'background:var(--ws-accent);color:#fff5ec'
                : 'background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)'}>
              {yr}
            </button>
          {/each}
        </div>

        <!-- Add trip button -->
        <button onclick={() => addModalOpen = true}
          class="flex items-center gap-1.5 text-xs font-bold px-4 py-1.5 rounded-lg transition-all hover:opacity-85"
          style="background:var(--ws-accent);color:#fff5ec">
          {$t('archiveAddTrip')}
        </button>
      </div>

      <!-- Sync result info -->
      {#if syncInfo}
        <div class="text-xs px-1" style="color:var(--ws-muted)">📡 {syncInfo}</div>
      {/if}

      <!-- Archive Trip Cards grid -->
      {#if journalLoad}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each [1,2,3] as _}<div class="rounded-2xl border p-5 animate-pulse h-40" style="background:var(--ws-surface2);border-color:var(--ws-border)"></div>{/each}
        </div>
      {:else if journalYear.length === 0}
        <div class="rounded-2xl border p-10 text-center" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <p class="text-4xl mb-3">📓</p>
          <p class="text-sm" style="color:var(--ws-muted)">{$t('archiveEmpty')}</p>
        </div>
      {:else if viewMode === 'list'}
        <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
          {#each journalYear as trip, i}
            <div class="flex items-center gap-4 px-5 py-3 transition-all hover:opacity-90 {i > 0 ? 'border-t' : ''}"
              style="background:var(--ws-surface);border-color:var(--ws-border)">
              <span class="text-2xl shrink-0">🌍</span>
              <div class="flex-1 min-w-0">
                <div class="font-semibold text-sm truncate" style="font-family:var(--ws-serif);color:var(--ws-text)">{trip.name || trip.destination || 'Reise'}</div>
                {#if trip.start_date}
                  <div class="text-xs font-mono" style="color:var(--ws-muted)">{trip.start_date}{trip.end_date && trip.end_date !== trip.start_date ? ' → ' + trip.end_date : ''}</div>
                {/if}
              </div>
              {#if (trip.cost ?? trip.auto_cost)}
                <div class="text-sm font-mono font-bold shrink-0" style="color:var(--ws-text)">{parseFloat(trip.cost ?? trip.auto_cost).toFixed(0)} €</div>
              {/if}
              <button onclick={() => deleteJournalTrip(trip.id)}
                class="text-xs px-2 py-1 rounded-lg border hover:border-red-400 hover:text-red-400 shrink-0 transition-colors"
                style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
          {/each}
        </div>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4">
          {#each journalYear as trip}
            <TripCard
              {trip}
              mode="archive"
              ongoToHub={() => {}}
              ondelete={(t) => deleteJournalTrip(t.id)}
            />
          {/each}
        </div>
      {/if}
    </div>

  <!-- ══ BUCKET LIST ════════════════════════════════════════════════════════ -->
  {:else if activeTab === 'bucketlist'}
    <BucketListTab
      onadd={(item, dest) => {
        bucketlist.update(l => [...l, { item, dest, done: false, created: new Date().toISOString().slice(0, 10) }]);
        toast($t('toastBucketAdded'), 'success');
      }}
      ontoggle={toggleBucket}
      onremove={removeBucket}
    />
  {/if}

</div>


