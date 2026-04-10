<script>
  import { trips, budget, bucketlist, apiUrl } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';
  import { t } from '$lib/i18n.js';

  import PageHeader    from '$lib/components/mytrips/PageHeader.svelte';
  import OverviewTab   from '$lib/components/mytrips/OverviewTab.svelte';
  import TripsTab      from '$lib/components/mytrips/TripsTab.svelte';
  import JournalTab    from '$lib/components/mytrips/JournalTab.svelte';
  import BucketListTab from '$lib/components/mytrips/BucketListTab.svelte';

  // ── Tabs ──────────────────────────────────────────────────────────────────
  let activeTab = $state('overview');
  const tabs = [
    { id: 'overview',   label: '📊 Übersicht'       },
    { id: 'trips',      label: '✈️ Geplante Reisen' },
    { id: 'journal',    label: '📓 Reisechronik'    },
    { id: 'bucketlist', label: '🌟 Bucket List'     },
  ];

  // ── Jahr-Switcher ─────────────────────────────────────────────────────────
  const currentYear = new Date().getFullYear();
  let selectedYear  = $state(currentYear);

  const allYearsWithData = $derived.by(() => {
    const s = new Set([currentYear]);
    $trips.forEach(t => { const y = +((t.dateStart||t.date||'').slice(0,4)); if(y>2000) s.add(y); });
    journalTrips.forEach(t => { const y = +((t.start_date||'').slice(0,4)); if(y>2000) s.add(y); });
    Object.keys(budgetByYear).forEach(y => s.add(+y));
    return [...s].sort((a,b) => a-b);
  });

  const visibleYears = $derived([selectedYear - 1, selectedYear, selectedYear + 1]);

  function prevYear() { selectedYear = selectedYear - 1; }
  function nextYear() { selectedYear = selectedYear + 1; }

  // ── Budget ────────────────────────────────────────────────────────────────
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

  // ── Reisechronik ──────────────────────────────────────────────────────────
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
    if (!confirm('Eintrag löschen? (Dawarich-Trips werden beim nächsten Sync übersprungen)')) return;
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

  // ── Manueller Chronik-Eintrag ─────────────────────────────────────────────
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

  // ── Dawarich Sync ─────────────────────────────────────────────────────────
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
        ? JSON.stringify({ dawarich_url:url, dawarich_token:token, home_lat:lat||null, home_lon:lon||null, force_full: forceFull })
        : JSON.stringify({ force_full: forceFull });
      const r = await api('/api/dawarich/sync', { method: 'POST', body });
      if (r.trips_detected===0 && r.points_loaded===0) {
        syncInfo = 'Keine GPS-Punkte — Einstellungen prüfen';
        toast('Keine Punkte geladen', 'warning');
      } else {
        syncInfo = `${r.points_loaded} Punkte · ${r.trips_detected} erkannt · ${r.trips_saved} gespeichert`;
        toast(`${r.trips_detected} Reisen erkannt ✓`, 'success');
      }
      await loadJournal();
    } catch (e) { toast('Sync-Fehler: ' + e.message, 'error'); }
    syncing = false;
  }

  // ── ActualBudget Sync ─────────────────────────────────────────────────────
  let actualSyncing      = $state(false);
  let actualResult       = $state(null);
  let actualFiles        = $state([]);
  let actualFilesLoading = $state(false);
  let autoCostRunning    = $state(false);
  let autoCostResult     = $state(null);

  async function listActualFiles() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const url   = browser ? localStorage.getItem('s-actualUrl')      || '' : '';
    const token = browser ? localStorage.getItem('s-actualPassword') || '' : '';
    if (!url || !token) { toast('ActualBudget URL + Passwort fehlen → Einstellungen', 'warning'); return; }
    actualFilesLoading = true;
    try {
      const r = await api('/api/budget/actual/list-files', {
        method: 'POST', body: JSON.stringify({ actual_url: url, actual_token: token }),
      });
      actualFiles = r.files || [];
      if (!actualFiles.length) toast('Keine Budget-Dateien gefunden', 'warning');
    } catch (e) { toast('Fehler: ' + e.message, 'error'); }
    actualFilesLoading = false;
  }

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

  async function runAutoCost() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const url      = browser ? localStorage.getItem('s-actualUrl')        || '' : '';
    const password = browser ? localStorage.getItem('s-actualPassword')   || '' : '';
    const file     = browser ? localStorage.getItem('s-actualFile')       || '' : '';
    const cats     = browser ? localStorage.getItem('s-travelCategories') || '' : '';
    if (!url || !password) { toast('ActualBudget URL + Passwort fehlen → Einstellungen', 'warning'); return; }
    autoCostRunning = true; autoCostResult = null;
    try {
      const r = await api('/api/trips/auto-cost', { method: 'POST',
        body: JSON.stringify({ actual_url:url, actual_token:password, actual_file:file||null, categories:cats||null }),
      });
      autoCostResult = r;
      toast(`${r.trips_updated} Reisen mit ${r.total_assigned?.toFixed(2)} € verknüpft ✓`, 'success');
      await loadJournal();
    } catch (e) { toast('Auto-Cost Fehler: ' + e.message, 'error'); }
    autoCostRunning = false;
  }

  let globalSyncing = $state(false);
  async function globalSync() {
    globalSyncing = true;
    await syncJournal();
    await syncActual();
    await runAutoCost();
    globalSyncing = false;
  }

  // ── Geplante Trips ────────────────────────────────────────────────────────
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

  // ── Bucket list ───────────────────────────────────────────────────────────
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

  // ── Derived ───────────────────────────────────────────────────────────────
  const today = new Date().toISOString().slice(0,10);
  const yr    = $derived(String(selectedYear));

  const journalYear      = $derived(journalTrips.filter(t => (t.start_date||'').slice(0,4) === yr));
  const journalSpentYear = $derived(
    journalYear
      .filter(t => (t.cost ?? t.auto_cost) != null)
      .reduce((s,t) => s + (parseFloat(t.cost ?? t.auto_cost) || 0), 0)
  );

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
  const tripsSpentYear = $derived(
    $trips
      .filter(t => (t.dateStart||t.date||'').slice(0,4) === yr)
      .reduce((s,t) => s+(parseFloat(t.cost)||0), 0)
  );

  const totalSpentYear = $derived(journalSpentYear + tripsSpentYear);
  const remainingYear  = $derived(Math.max(0, yearBudget - totalSpentYear));
  const pctYear        = $derived(yearBudget > 0 ? Math.min(100,(totalSpentYear/yearBudget)*100) : 0);
  const overBudget     = $derived(yearBudget > 0 && totalSpentYear > yearBudget);

  const donutGradient = $derived.by(() => {
    if (yearBudget <= 0) return 'conic-gradient(#e2e8f0 0deg 360deg)';
    const pastDeg    = Math.min(360, (journalSpentYear / yearBudget) * 360);
    const plannedDeg = Math.min(360 - pastDeg, (tripsSpentYear / yearBudget) * 360);
    const overDeg    = overBudget ? Math.min(360, ((totalSpentYear - yearBudget) / yearBudget) * 360) : 0;
    const restDeg    = 360 - pastDeg - plannedDeg - overDeg;
    let grad = ''; let cur = 0;
    if (pastDeg > 0)    { grad += `#2d6a4f ${cur}deg ${cur+pastDeg}deg,`;    cur += pastDeg; }
    if (plannedDeg > 0) { grad += `#86efac ${cur}deg ${cur+plannedDeg}deg,`; cur += plannedDeg; }
    if (overDeg > 0)    { grad += `#ef4444 ${cur}deg ${cur+overDeg}deg,`;    cur += overDeg; }
    if (restDeg > 0)    { grad += `#e2e8f0 ${cur}deg ${cur+restDeg}deg,`;    cur += restDeg; }
    return `conic-gradient(${grad.slice(0,-1)})`;
  });

  const totalCount    = $derived(upcomingTrips.length + journalTrips.length);
  const upcomingCount = $derived(upcomingTrips.length);

  const inp  = 'text-sm rounded-lg focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 p-2.5 w-full outline-none transition-all border';
  const card = 'rounded-xl shadow-sm p-5 border';
  const btn  = 'w-full py-2.5 px-4 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-[.98]';
</script>

<div class="space-y-5">

  <PageHeader
    {selectedYear}
    {globalSyncing}
    {upcomingCount}
    journalYearLength={journalYear.length}
    bucketWishCount={$bucketlist.filter(b=>!b.done).length}
    {totalCount}
    {visibleYears}
    {tabs}
    {activeTab}
    onglobalsync={globalSync}
    onprevyear={prevYear}
    onnextyear={nextYear}
    onselectyear={(y) => { selectedYear = y; }}
    onswitchtab={(tab) => { activeTab = tab; }}
  />

  {#if activeTab === 'overview'}
    <OverviewTab
      {journalYear}
      {upcomingTrips}
      {journalSpentYear}
      {tripsSpentYear}
      {totalSpentYear}
      {yearBudget}
      {remainingYear}
      {pctYear}
      {overBudget}
      {donutGradient}
      {selectedYear}
      {journalTrips}
      plannedTrips={$trips}
      onswitchtab={(tab) => { activeTab = tab; }}
    />

  {:else if activeTab === 'trips'}
    <TripsTab
      bind:tripName bind:tripDateStart bind:tripDateEnd bind:tripCost
      {upcomingTrips} {pastTrips}
      {yearBudget} {pctYear} {totalSpentYear} {remainingYear} {selectedYear}
      {inp} {card} {btn}
      onaddtrip={addTrip}
      onremovetrip={removeTrip}
    />

  {:else if activeTab === 'journal'}
    <JournalTab
      bind:budgetInput bind:mName bind:mStart bind:mEnd bind:mCountry bind:mCost
      bind:forceFull
      {selectedYear} {journalYear} {journalTrips} {journalLoad}
      {budgetSaving} {mAdding} {editingCost} {costDraft}
      {syncing} {syncInfo}
      {actualSyncing} {actualResult} {actualFiles} {actualFilesLoading}
      {autoCostRunning} {autoCostResult}
      {inp} {card} {btn}
      onsavebudget={saveBudget}
      onaddmanualtrip={addManualTrip}
      ondeletejournaltrip={deleteJournalTrip}
      onsavecost={saveCost}
      oneditcost={(id, draft) => { editingCost = id; costDraft = draft; }}
      oncanceledit={() => { editingCost = null; }}
      onsyncjournal={syncJournal}
      onsyncactual={syncActual}
      onlistactualfiles={listActualFiles}
      onrunautocost={runAutoCost}
    />

  {:else if activeTab === 'bucketlist'}
    <BucketListTab
      bind:bucketItem bind:bucketDest
      {card} {inp} {btn}
      onadd={addBucketItem}
      ontoggle={toggleBucket}
      onremove={removeBucket}
    />
  {/if}

</div>
