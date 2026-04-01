<script>
  import { trips, budget, bucketlist, apiUrl } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';
  import { t } from '$lib/i18n.js';
  import { onMount } from 'svelte';
  import ScratchMap from '$lib/components/ScratchMap.svelte';

  let activeTab = $state('overview');

  // ── Trip form ────────────────────────────────────────────────────────
  let tripName = $state('');
  let tripDate = $state(new Date().toISOString().slice(0, 10));
  let tripCost = $state('');

  // ── Budget ───────────────────────────────────────────────────────────
  let budgetInput = $state('');
  $effect(() => { budgetInput = $budget || ''; });

  // ── ActualBudget sync ────────────────────────────────────────────────
  let actualSyncing = $state(false);
  let actualResult  = $state(null);

  // ── Bucket list ──────────────────────────────────────────────────────
  let bucketItem = $state('');
  let bucketDest = $state('');

  // ── Journal (Dawarich) ───────────────────────────────────────────────
  let journalTrips = $state([]);
  let journalLoad  = $state(false);
  let syncing      = $state(false);
  let syncInfo     = $state('');

  $effect(() => {
    if (activeTab === 'journal' && journalTrips.length === 0) loadJournal();
  });

  async function loadJournal() {
    if (!$apiUrl) return;
    journalLoad = true;
    try { journalTrips = await api('/api/dawarich/trips?limit=100'); }
    catch (e) { toast('Fehler: ' + e.message, 'error'); }
    journalLoad = false;
  }

  async function syncJournal() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const url   = browser ? localStorage.getItem('s-dawarichUrl')   || '' : '';
    const token = browser ? localStorage.getItem('s-dawarichToken') || '' : '';
    const lat   = parseFloat(browser ? localStorage.getItem('s-homeLat') || '0' : '0');
    const lon   = parseFloat(browser ? localStorage.getItem('s-homeLon') || '0' : '0');
    syncing = true; syncInfo = '';
    try {
      const body = (url && token)
        ? JSON.stringify({ dawarich_url: url, dawarich_token: token, home_lat: lat || null, home_lon: lon || null })
        : '{}';
      const r = await api('/api/dawarich/sync', { method: 'POST', body });
      if (r.trips_detected === 0 && r.points_loaded === 0) {
        syncInfo = 'Keine GPS-Punkte gefunden — Dawarich-Einstellungen prüfen';
        toast('Keine Punkte geladen', 'warning');
      } else {
        syncInfo = `${r.points_loaded} Punkte · ${r.trips_detected} erkannt · ${r.trips_saved} gespeichert`;
        toast(`${r.trips_detected} Reisen erkannt ✓`, 'success');
      }
      await loadJournal();
    } catch (e) { toast('Sync-Fehler: ' + e.message, 'error'); }
    syncing = false;
  }

  async function deleteJournalTrip(id) {
    if (!confirm($t('delete') + '?')) return;
    try { await api(`/api/dawarich/trips/${id}`, { method: 'DELETE' }); toast('Trip gelöscht', 'success'); }
    catch (e) { toast(e.message, 'error'); }
    await loadJournal();
  }

  // ── Trips ─────────────────────────────────────────────────────────────
  function addTrip() {
    if (!tripName || !tripDate || !tripCost) { toast('Bitte alle Felder ausfüllen', 'error'); return; }
    trips.update(l => [...l, { name: tripName, date: tripDate, cost: parseFloat(tripCost) }]);
    tripName = ''; tripCost = '';
    toast($t('toastTripAdded'), 'success');
  }
  function removeTrip(i) { trips.update(l => l.filter((_, idx) => idx !== i)); }

  function saveBudget() { budget.set(budgetInput); toast($t('toastBudgetSaved'), 'success'); }

  async function syncActual() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const url      = browser ? localStorage.getItem('s-actualUrl')        || '' : '';
    const password = browser ? localStorage.getItem('s-actualPassword')   || '' : '';
    const file     = browser ? localStorage.getItem('s-actualFile')       || '' : '';
    const cats     = browser ? localStorage.getItem('s-travelCategories') || '' : '';
    if (!url || !password) { toast('ActualBudget URL + Passwort fehlen → Einstellungen', 'warning'); return; }
    actualSyncing = true; actualResult = null;
    try {
      const r = await api('/api/budget/actual/transactions', {
        method: 'POST',
        body: JSON.stringify({ actual_url: url, actual_token: password, actual_file: file || null, categories: cats || null }),
      });
      actualResult = r;
      toast(`${r.transactions?.length ?? 0} Transaktionen geladen ✓`, 'success');
    } catch (e) { toast('ActualBudget Fehler: ' + e.message, 'error'); }
    actualSyncing = false;
  }

  // ── Bucket list ───────────────────────────────────────────────────────
  function addBucketItem() {
    if (!bucketItem) { toast('Bitte Eintrag eingeben', 'error'); return; }
    bucketlist.update(l => [...l, { item: bucketItem, dest: bucketDest, done: false, created: new Date().toISOString().slice(0, 10) }]);
    bucketItem = ''; bucketDest = '';
    toast($t('toastBucketAdded'), 'success');
  }
  function toggleBucket(i) { bucketlist.update(l => l.map((x, idx) => idx === i ? { ...x, done: !x.done } : x)); }
  function removeBucket(i) { bucketlist.update(l => l.filter((_, idx) => idx !== i)); }

  // ── Derived ───────────────────────────────────────────────────────────
  const totalBudget = $derived(parseFloat($budget) || 0);
  const totalSpent  = $derived($trips.reduce((s, t) => s + (parseFloat(t.cost) || 0), 0));
  const remaining   = $derived(Math.max(0, totalBudget - totalSpent));
  const pct         = $derived(totalBudget > 0 ? Math.min(100, (totalSpent / totalBudget) * 100) : 0);
  const today       = new Date().toISOString().slice(0, 10);

  const tabs = $derived([
    { id: 'overview',   label: '📊 ' + $t('mytripsOverview').replace(/^📊\s*/,'') },
    { id: 'trips',      label: '🧳 ' + $t('mytripsTrips').replace(/^[^\s]+\s*/,'') },
    { id: 'bucketlist', label: '🗺️ ' + $t('mytripsBucketlist').replace(/^[^\s]+\s*/,'') },
    { id: 'journal',    label: '📓 ' + $t('navJournal').replace(/^[^\s]+\s*/,'') },
  ]);

  // Input class helper
  const inp = 'bg-stone-50 border border-stone-200 text-stone-800 text-sm rounded-lg focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 p-2.5 w-full outline-none transition-all';
  const card = 'bg-white border border-stone-200 rounded-xl shadow-sm p-5';
  const btnPrimary = 'w-full py-2.5 px-4 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-[.98]';
</script>

<div class="space-y-5">

  <!-- Header -->
  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-bold" style="font-family:var(--ws-serif)">{$t('mytripsTitle')}</h1>
    <div class="text-xs font-medium px-2.5 py-1 rounded-full border border-stone-200 text-stone-500 bg-white">
      {$trips.length} {$t('mytripsStatsTrips').toLowerCase()}
    </div>
  </div>

  <!-- Tabs (Pills) -->
  <div class="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1">
    {#each tabs as tab}
      <button
        onclick={() => activeTab = tab.id}
        class="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all border"
        class:bg-orange-600={activeTab === tab.id}
        class:text-white={activeTab === tab.id}
        class:border-orange-600={activeTab === tab.id}
        class:bg-white={activeTab !== tab.id}
        class:text-stone-500={activeTab !== tab.id}
        class:border-stone-200={activeTab !== tab.id}
        class:hover:border-stone-300={activeTab !== tab.id}
      >
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- ═══════════════════════════════════════════════════════════════════
       TAB 1 — ÜBERSICHT
  ════════════════════════════════════════════════════════════════════ -->
  {#if activeTab === 'overview'}

    <!-- Stats-Karten -->
    <div class="grid grid-cols-3 gap-3">
      {#each [
        { label: $t('mytripsStatsTrips'),     value: $trips.length,                                icon: '✈️', color: 'text-stone-800' },
        { label: $t('mytripsStatsSpent'),     value: totalSpent.toFixed(2) + ' €',                icon: '💸', color: 'text-orange-600' },
        { label: $t('mytripsStatsRemaining'), value: totalBudget > 0 ? remaining.toFixed(2) + ' €' : '–', icon: '💰', color: 'text-emerald-700' },
      ] as s}
        <div class={card + ' text-center'}>
          <div class="text-2xl mb-1">{s.icon}</div>
          <div class="text-xs font-medium text-stone-400 mb-0.5 uppercase tracking-wide">{s.label}</div>
          <div class="text-lg font-bold {s.color}" style="font-family:var(--ws-serif)">{s.value}</div>
        </div>
      {/each}
    </div>

    <!-- Budget-Fortschritt -->
    {#if totalBudget > 0}
      <div class={card}>
        <div class="flex justify-between text-xs text-stone-500 mb-2">
          <span>{$t('mytripsProgress')}</span>
          <span class="font-semibold {pct > 85 ? 'text-red-500' : 'text-stone-700'}">{pct.toFixed(0)}%</span>
        </div>
        <div class="h-2.5 rounded-full bg-stone-100 overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500"
            style="width:{pct}%;background:{pct>85?'#ef4444':pct>60?'#f97316':'#059669'}"></div>
        </div>
        <div class="flex justify-between text-xs text-stone-400 mt-2">
          <span>{totalSpent.toFixed(2)} € ausgegeben</span>
          <span>{totalBudget.toFixed(2)} € gesamt</span>
        </div>
      </div>
    {/if}

    <!-- Scratch Map -->
    <div class={card + ' !p-4'}>
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-stone-700">🗺️ Meine Reisekarte</h2>
        <span class="text-xs text-stone-400">{$trips.length + journalTrips.length} Orte</span>
      </div>
      <ScratchMap {journalTrips} />
    </div>

    <!-- Letzte Reisen -->
    {#if $trips.length > 0}
      <div class={card}>
        <h2 class="text-sm font-semibold text-stone-700 mb-3">{$t('mytripsRecentTrips')}</h2>
        <div class="space-y-2">
          {#each [...$trips].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 4) as tr}
            <div class="flex items-center gap-3 py-2 border-b border-stone-100 last:border-0">
              <span class="text-lg">{tr.date >= today ? '✈️' : '✅'}</span>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-semibold text-stone-800 truncate" style="font-family:var(--ws-serif)">{tr.name}</div>
                <div class="text-xs text-stone-400 font-mono">{tr.date}</div>
              </div>
              <div class="text-sm font-bold text-orange-600 font-mono shrink-0">{parseFloat(tr.cost).toFixed(2)} €</div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

  <!-- ═══════════════════════════════════════════════════════════════════
       TAB 2 — REISEN & BUDGET
  ════════════════════════════════════════════════════════════════════ -->
  {:else if activeTab === 'trips'}
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

      <!-- ── Linke Spalte ── -->
      <div class="lg:col-span-1 space-y-4">

        <!-- Smart Reise-Planer (Coming Soon) -->
        <div class="{card} border-orange-200 bg-gradient-to-br from-orange-50 to-amber-50 relative overflow-hidden">
          <div class="absolute top-3 right-3">
            <span class="text-[10px] font-bold uppercase tracking-wider bg-orange-600 text-white px-2 py-0.5 rounded-full">
              Bald verfügbar
            </span>
          </div>
          <div class="text-xl mb-2">✨</div>
          <h3 class="font-bold text-stone-800 text-sm mb-1" style="font-family:var(--ws-serif)">Smart Reise-Planer</h3>
          <p class="text-xs text-stone-500 leading-relaxed">
            Demnächst: Budget, Personen & Zeitraum definieren — WanderSuite findet Flüge, Mietwagen und Hotels auf einmal.
          </p>
        </div>

        <!-- Jahresbudget -->
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-3">💶 {$t('mytripsBudgetManual')}</h3>
          <input type="number" bind:value={budgetInput}
            placeholder={$t('mytripsBudgetPlaceholder')}
            class={inp + ' mb-3'} />
          <button onclick={saveBudget}
            class={btnPrimary}
            style="background:linear-gradient(135deg,#c4622d,#b84928)">
            {$t('mytripsBudgetSave')}
          </button>
        </div>

        <!-- ActualBudget Sync -->
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-1">{$t('mytripsActualSync')}</h3>
          <p class="text-xs text-stone-400 mb-3">{$t('mytripsActualDesc')}</p>
          <button onclick={syncActual} disabled={actualSyncing || !$apiUrl}
            class={btnPrimary + ' disabled:opacity-40'}
            style="background:linear-gradient(135deg,#c4622d,#b84928)">
            {actualSyncing ? $t('mytripsActualSyncing') : $t('mytripsActualBtn')}
          </button>
          {#if actualResult}
            <div class="mt-3 pt-3 border-t border-stone-100">
              <div class="flex justify-between text-xs font-semibold text-stone-700 mb-2">
                <span>{$t('mytripsActualExpenses')}</span>
                <span class="text-orange-600">
                  {(actualResult.transactions?.reduce((s, tx) => s + Math.abs(tx.amount ?? 0), 0) ?? 0).toFixed(2)} €
                </span>
              </div>
              {#if actualResult.transactions?.length}
                <div class="space-y-1 max-h-40 overflow-y-auto">
                  {#each actualResult.transactions.slice(0, 15) as tx}
                    <div class="flex justify-between text-xs py-1 border-b border-stone-50">
                      <span class="truncate flex-1 mr-2 text-stone-600">{tx.payee_name || tx.notes || '–'}</span>
                      <span class="font-mono font-bold text-orange-600 shrink-0">{Math.abs(tx.amount ?? 0).toFixed(2)} €</span>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}
        </div>

        <!-- Neue Reise hinzufügen -->
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-3">➕ {$t('mytripsAddTrip')}</h3>
          <div class="space-y-2.5">
            <input bind:value={tripName} placeholder={$t('mytripsDestPlaceholder')} class={inp} />
            <input type="date" bind:value={tripDate} class={inp} />
            <input type="number" bind:value={tripCost} placeholder={$t('mytripsCostPlaceholder')} class={inp} />
            <button onclick={addTrip}
              class={btnPrimary}
              style="background:linear-gradient(135deg,#c4622d,#b84928)">
              {$t('mytripsAddBtn')}
            </button>
          </div>
        </div>
      </div>

      <!-- ── Rechte Spalte ── -->
      <div class="lg:col-span-2 space-y-4">

        <!-- Budget Progress -->
        {#if totalBudget > 0}
          <div class={card}>
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-semibold text-stone-500 uppercase tracking-wide">{$t('mytripsProgress')}</span>
              <span class="text-xs font-bold {pct > 85 ? 'text-red-500' : 'text-emerald-600'}">{pct.toFixed(0)}% verbraucht</span>
            </div>
            <div class="h-3 rounded-full bg-stone-100 overflow-hidden">
              <div class="h-full rounded-full transition-all duration-500"
                style="width:{pct}%;background:{pct>85?'#ef4444':pct>60?'#f97316':'#059669'}"></div>
            </div>
            <div class="flex justify-between text-xs text-stone-400 mt-1.5">
              <span>{totalSpent.toFixed(2)} € ausgegeben</span>
              <span class="text-emerald-600 font-medium">{remaining.toFixed(2)} € frei</span>
            </div>
          </div>
        {/if}

        <!-- Reise-Liste -->
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-3">
            ✈️ Alle Reisen
            <span class="ml-1.5 text-xs font-normal text-stone-400">({$trips.length})</span>
          </h3>
          {#if $trips.length === 0}
            <div class="text-center py-10 text-stone-400">
              <div class="text-4xl mb-2">✈️</div>
              <p class="text-sm">{$t('mytripsEmpty')}</p>
            </div>
          {:else}
            <div class="space-y-2">
              {#each [...$trips].sort((a, b) => b.date.localeCompare(a.date)) as tr, i}
                <div class="flex items-center gap-3 p-3 rounded-lg bg-stone-50 border border-stone-100
                            hover:border-stone-200 transition-colors group">
                  <div class="w-8 h-8 rounded-full flex items-center justify-center text-base shrink-0"
                    style="background:{tr.date >= today ? '#fff7ed' : '#f0fdf4'}">
                    {tr.date >= today ? '✈️' : '✅'}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-semibold text-stone-800 truncate" style="font-family:var(--ws-serif)">{tr.name}</div>
                    <div class="text-xs text-stone-400 font-mono">{tr.date}</div>
                  </div>
                  <div class="text-base font-bold text-orange-600 font-mono shrink-0">{parseFloat(tr.cost).toFixed(2)} €</div>
                  <button onclick={() => removeTrip(i)}
                    class="opacity-0 group-hover:opacity-100 transition-opacity text-stone-400 hover:text-red-500 ml-1 text-xs px-1.5 py-1 rounded border border-stone-200 hover:border-red-200">
                    ✕
                  </button>
                </div>
              {/each}
            </div>
            <!-- Summe -->
            <div class="mt-3 pt-3 border-t border-stone-100 flex justify-between text-sm font-semibold">
              <span class="text-stone-500">Gesamt</span>
              <span class="text-orange-600 font-mono">{totalSpent.toFixed(2)} €</span>
            </div>
          {/if}
        </div>
      </div>
    </div>

  <!-- ═══════════════════════════════════════════════════════════════════
       TAB 3 — BUCKET LIST
  ════════════════════════════════════════════════════════════════════ -->
  {:else if activeTab === 'bucketlist'}
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

      <!-- Formular -->
      <div class="lg:col-span-1">
        <div class={card}>
          <h3 class="text-sm font-semibold text-stone-700 mb-3">🌟 {$t('mytripsBucketAdd')}</h3>
          <div class="space-y-2.5">
            <input bind:value={bucketItem} placeholder={$t('mytripsBucketItemPlaceholder')} class={inp} />
            <input bind:value={bucketDest} placeholder={$t('mytripsBucketDestPlaceholder')} class={inp} />
            <button onclick={addBucketItem}
              class={btnPrimary}
              style="background:linear-gradient(135deg,#c4622d,#b84928)">
              {$t('mytripsAddBtn')}
            </button>
          </div>
          {#if $bucketlist.length > 0}
            <div class="mt-4 pt-4 border-t border-stone-100 text-xs text-stone-400 text-center">
              {$bucketlist.filter(x => x.done).length} / {$bucketlist.length} erledigt
            </div>
          {/if}
        </div>
      </div>

      <!-- Grid der Wunschziele -->
      <div class="lg:col-span-2">
        {#if $bucketlist.length === 0}
          <div class={card + ' text-center py-14'}>
            <div class="text-5xl mb-3">🌍</div>
            <p class="text-sm text-stone-400">{$t('mytripsBucketEmpty')}</p>
          </div>
        {:else}
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {#each $bucketlist as item, i}
              <div class="group relative {card} transition-all hover:shadow-md"
                class:opacity-50={item.done}>
                <!-- Done-Toggle -->
                <button onclick={() => toggleBucket(i)}
                  class="absolute top-4 right-4 w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs transition-all"
                  style="border-color:{item.done?'#059669':'#d1d5db'};background:{item.done?'#059669':'transparent'};color:white">
                  {item.done ? '✓' : ''}
                </button>
                <!-- Delete -->
                <button onclick={() => removeBucket(i)}
                  class="absolute top-4 right-12 w-6 h-6 rounded-full border border-stone-200 flex items-center
                         justify-center text-xs text-stone-400 hover:text-red-500 hover:border-red-200
                         opacity-0 group-hover:opacity-100 transition-all">
                  ✕
                </button>
                <div class="text-2xl mb-2">🌟</div>
                <div class="text-sm font-semibold text-stone-800 pr-12"
                  style="font-family:var(--ws-serif)"
                  class:line-through={item.done}>
                  {item.item}
                </div>
                {#if item.dest}
                  <div class="text-xs text-stone-400 mt-1">📍 {item.dest}</div>
                {/if}
                <div class="text-xs text-stone-300 mt-2 font-mono">{item.created}</div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

  <!-- ═══════════════════════════════════════════════════════════════════
       TAB 4 — REISETAGEBUCH (Dawarich)
  ════════════════════════════════════════════════════════════════════ -->
  {:else if activeTab === 'journal'}

    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-base font-semibold text-stone-800">{$t('journalTitle')}</h2>
        <p class="text-xs text-stone-400 mt-0.5">{journalTrips.length} Reisen erkannt</p>
      </div>
      <button onclick={syncJournal} disabled={syncing}
        class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold border border-stone-200 bg-white
               text-stone-700 hover:border-orange-300 hover:text-orange-600 transition-all disabled:opacity-50 shadow-sm">
        <span>{syncing ? '⏳' : '🧭'}</span>
        {syncing ? $t('journalSyncing') : $t('journalSync')}
      </button>
    </div>

    {#if syncInfo}
      <div class="text-xs px-4 py-2.5 rounded-lg bg-stone-50 border border-stone-200 text-stone-500">
        ℹ️ {syncInfo}
      </div>
    {/if}

    {#if !$apiUrl}
      <div class="{card} text-center py-12">
        <div class="text-4xl mb-3">🔌</div>
        <p class="text-sm text-stone-400">{$t('journalNoBackend')}</p>
      </div>
    {:else if journalLoad}
      <div class="space-y-3">
        {#each [1,2,3] as _}
          <div class="h-20 rounded-xl bg-stone-100 animate-pulse"></div>
        {/each}
      </div>
    {:else if journalTrips.length === 0}
      <div class="{card} text-center py-12">
        <div class="text-4xl mb-3">🗺️</div>
        <p class="text-sm font-semibold text-stone-700 mb-1">{$t('journalEmpty')}</p>
        <p class="text-xs text-stone-400 mb-4 max-w-xs mx-auto">{$t('journalEmptyHint')}</p>
        <button onclick={syncJournal} disabled={syncing}
          class="px-5 py-2 rounded-lg text-sm font-semibold text-white"
          style="background:linear-gradient(135deg,#c4622d,#b84928)">
          {$t('journalSyncNow')}
        </button>
      </div>
    {:else}
      <!-- Timeline -->
      <div class="relative space-y-0 pl-6">
        <!-- Vertikale Linie -->
        <div class="absolute left-2.5 top-2 bottom-2 w-0.5 bg-stone-200 rounded-full"></div>

        {#each journalTrips as trip, idx}
          {@const loc = [trip.location_name, trip.country].filter(Boolean).join(', ') || `${trip.lat}, ${trip.lon}`}
          {@const mapsUrl = `https://www.google.com/maps?q=${trip.lat},${trip.lon}`}
          <div class="relative pb-4">
            <!-- Dot -->
            <div class="absolute -left-6 top-4 w-4 h-4 rounded-full border-2 border-white shadow-sm z-10"
              style="background:linear-gradient(135deg,#c4622d,#b84928)"></div>

            <div class="{card} ml-2 hover:shadow-md transition-shadow">
              <div class="flex items-start justify-between gap-3">
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-stone-800 truncate" style="font-family:var(--ws-serif)">
                    📍 {loc}
                  </div>
                  <div class="text-xs text-stone-400 font-mono mt-0.5">
                    {trip.start_date} → {trip.end_date}
                  </div>
                </div>
                <span class="shrink-0 px-2.5 py-1 rounded-full text-xs font-bold"
                  style="background:rgba(196,98,45,.1);color:#c4622d">
                  {trip.nights} {trip.nights === 1 ? $t('journalNight') : $t('journalNights')}
                </span>
              </div>
              <div class="flex gap-2 mt-3">
                <a href={mapsUrl} target="_blank"
                  class="flex-1 text-center py-1.5 rounded-lg text-xs border border-stone-200 text-stone-500 hover:border-orange-300 hover:text-orange-600 transition-colors">
                  🗺 {$t('journalMaps')}
                </a>
                <button onclick={() => deleteJournalTrip(trip.id)}
                  class="px-3 py-1.5 rounded-lg text-xs border border-stone-200 text-stone-400 hover:border-red-200 hover:text-red-500 transition-colors">
                  {$t('journalDelete')}
                </button>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {/if}
</div>
