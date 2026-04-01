<script>
  import { trips, budget, bucketlist, apiUrl } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';
  import { t } from '$lib/i18n.js';
  import { onMount } from 'svelte';

  let activeTab = $state('overview');

  // Trip form
  let tripName   = $state('');
  let tripDate   = $state(new Date().toISOString().slice(0,10));
  let tripCost   = $state('');

  // Budget
  let budgetInput = $state('');
  $effect(() => { budgetInput = $budget || ''; });

  // ActualBudget sync
  let actualSyncing = $state(false);
  let actualResult  = $state(null);

  // Bucket list
  let bucketItem = $state('');
  let bucketDest = $state('');

  // Journal (Dawarich)
  let journalTrips  = $state([]);
  let journalLoad   = $state(false);
  let syncing       = $state(false);
  let syncInfo      = $state('');

  // Load journal when tab opens
  $effect(() => {
    if (activeTab === 'journal' && journalTrips.length === 0) loadJournal();
  });

  async function loadJournal() {
    if (!$apiUrl) return;
    journalLoad = true;
    try { journalTrips = await api('/api/dawarich/trips?limit=100'); }
    catch(e) { toast('Fehler: ' + e.message, 'error'); }
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
        ? JSON.stringify({ dawarich_url: url, dawarich_token: token, home_lat: lat||null, home_lon: lon||null })
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
    } catch(e) {
      toast('Sync-Fehler: ' + e.message, 'error');
    }
    syncing = false;
  }

  async function deleteJournalTrip(id) {
    if (!confirm('Trip löschen?')) return;
    try { await api(`/api/dawarich/trips/${id}`, { method: 'DELETE' }); toast('Trip gelöscht', 'success'); }
    catch(e) { toast(e.message, 'error'); }
    await loadJournal();
  }

  // Trips
  function addTrip() {
    if (!tripName||!tripDate||!tripCost) { toast('Bitte alle Felder ausfüllen','error'); return; }
    trips.update(t => [...t, { name:tripName, date:tripDate, cost:parseFloat(tripCost) }]);
    tripName=''; tripCost='';
    toast($t('toastTripAdded'), 'success');
  }
  function removeTrip(i) { trips.update(t => t.filter((_,idx)=>idx!==i)); }

  function saveBudget() { budget.set(budgetInput); toast($t('toastBudgetSaved'), 'success'); }

  async function syncActual() {
    if (!$apiUrl) { toast('Backend-URL fehlt','warning'); return; }
    const url      = browser ? localStorage.getItem('s-actualUrl')      || '' : '';
    const password = browser ? localStorage.getItem('s-actualPassword') || '' : '';
    const file     = browser ? localStorage.getItem('s-actualFile')     || '' : '';
    const cats     = browser ? localStorage.getItem('s-travelCategories') || '' : '';
    if (!url || !password) { toast('ActualBudget URL + Passwort fehlen → Einstellungen','warning'); return; }
    actualSyncing = true; actualResult = null;
    try {
      const r = await api('/api/budget/actual/transactions', {
        method: 'POST',
        body: JSON.stringify({ actual_url:url, actual_token:password, actual_file:file||null, categories:cats||null }),
      });
      actualResult = r;
      toast(`${r.transactions?.length ?? 0} Transaktionen geladen ✓`, 'success');
    } catch(e) { toast('ActualBudget Fehler: ' + e.message, 'error'); }
    actualSyncing = false;
  }

  function addBucketItem() {
    if (!bucketItem) { toast('Bitte Eintrag eingeben','error'); return; }
    bucketlist.update(l => [...l, { item:bucketItem, dest:bucketDest, done:false, created:new Date().toISOString().slice(0,10) }]);
    bucketItem=''; bucketDest='';
    toast($t('toastBucketAdded'), 'success');
  }
  function toggleBucket(i) { bucketlist.update(l => l.map((x,idx)=>idx===i?{...x,done:!x.done}:x)); }
  function removeBucket(i) { bucketlist.update(l => l.filter((_,idx)=>idx!==i)); }

  const totalBudget = $derived(parseFloat($budget)||0);
  const totalSpent  = $derived($trips.reduce((s,t)=>s+(parseFloat(t.cost)||0),0));
  const remaining   = $derived(Math.max(0,totalBudget-totalSpent));
  const pct         = $derived(totalBudget>0?Math.min(100,(totalSpent/totalBudget)*100):0);
  const today       = new Date().toISOString().slice(0,10);

  const tabs = $derived([
    { id:'overview',   label:$t('mytripsOverview') },
    { id:'trips',      label:$t('mytripsTrips') },
    { id:'budget',     label:$t('mytripsBudget') },
    { id:'bucketlist', label:$t('mytripsBucketlist') },
    { id:'journal',    label:$t('navJournal') },
  ]);
</script>

<div class="space-y-4">
  <h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif)">{$t('mytripsTitle')}</h1>

  <!-- Tabs -->
  <div class="flex gap-1.5 overflow-x-auto pb-1">
    {#each tabs as tab}
      <button onclick={() => activeTab=tab.id}
        class="px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap border transition-all"
        style={activeTab===tab.id
          ? 'background:var(--ws-accent);color:#fff5ec;border-color:var(--ws-accent)'
          : 'background:var(--ws-surface);color:var(--ws-muted);border-color:var(--ws-border)'}>
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- ── OVERVIEW ── -->
  {#if activeTab==='overview'}
    <div class="grid grid-cols-3 gap-3">
      {#each [
        { label:$t('mytripsStatsTrips'),     value:$trips.length,                                           color:'var(--ws-text)' },
        { label:$t('mytripsStatsSpent'),     value:totalSpent.toFixed(2)+' €',                             color:'var(--ws-accent)' },
        { label:$t('mytripsStatsRemaining'), value:totalBudget>0?remaining.toFixed(2)+' €':'–',            color:'var(--ws-green)' },
      ] as s}
        <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
          <div class="text-xs font-bold uppercase tracking-wider mb-1" style="color:var(--ws-muted)">{s.label}</div>
          <div class="text-xl font-bold" style="color:{s.color};font-family:var(--ws-serif)">{s.value}</div>
        </div>
      {/each}
    </div>
    {#if totalBudget>0}
      <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
        <div class="flex justify-between text-xs mb-2" style="color:var(--ws-muted)">
          <span>{$t('mytripsProgress')}</span><span>{pct.toFixed(0)}%</span>
        </div>
        <div class="h-2 rounded-full" style="background:var(--ws-border)">
          <div class="h-2 rounded-full transition-all"
            style="width:{pct}%;background:{pct>85?'var(--ws-red)':pct>60?'var(--ws-accent2)':'var(--ws-green)'}"></div>
        </div>
        <div class="flex justify-between text-xs mt-2" style="color:var(--ws-muted)">
          <span>{totalSpent.toFixed(2)} € ausgegeben</span>
          <span>{totalBudget.toFixed(2)} € gesamt</span>
        </div>
      </div>
    {/if}
    {#if $trips.length>0}
      <div class="space-y-2">
        <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('mytripsRecentTrips')}</div>
        {#each [...$trips].sort((a,b)=>b.date.localeCompare(a.date)).slice(0,3) as t}
          <div class="flex items-center gap-3 p-3 rounded-xl border" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <span>{t.date>=today?'✈️':'✅'}</span>
            <div class="flex-1">
              <div class="text-sm font-semibold italic" style="font-family:var(--ws-serif)">{t.name}</div>
              <div class="text-xs font-mono" style="color:var(--ws-muted)">{t.date}</div>
            </div>
            <div class="font-bold font-mono text-sm" style="color:var(--ws-accent2)">{parseFloat(t.cost).toFixed(2)} €</div>
          </div>
        {/each}
      </div>
    {/if}

  <!-- ── TRIPS ── -->
  {:else if activeTab==='trips'}
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('mytripsAddTrip')}</h2>
      <input bind:value={tripName} placeholder={$t('mytripsDestPlaceholder')}
        class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <div class="grid grid-cols-2 gap-2">
        <input type="date" bind:value={tripDate} class="px-3 py-2 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        <input type="number" bind:value={tripCost} placeholder={$t('mytripsCostPlaceholder')}
          class="px-3 py-2 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      </div>
      <button onclick={addTrip} class="w-full py-2.5 rounded-xl font-semibold text-sm"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        {$t('mytripsAddBtn')}
      </button>
    </div>
    {#if $trips.length===0}
      <p class="text-sm" style="color:var(--ws-muted)">{$t('mytripsEmpty')}</p>
    {:else}
      <div class="space-y-2">
        {#each [...$trips].sort((a,b)=>b.date.localeCompare(a.date)) as t, i}
          <div class="flex items-center gap-3 p-3 rounded-xl border" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <span>{t.date>=today?'✈️':'✅'}</span>
            <div class="flex-1">
              <div class="text-sm font-semibold italic" style="font-family:var(--ws-serif)">{t.name}</div>
              <div class="text-xs font-mono" style="color:var(--ws-muted)">{t.date}</div>
            </div>
            <div class="font-bold font-mono text-sm" style="color:var(--ws-accent2)">{parseFloat(t.cost).toFixed(2)} €</div>
            <button onclick={() => removeTrip(i)} class="text-xs px-2 py-1 rounded-lg border"
              style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
          </div>
        {/each}
      </div>
    {/if}

  <!-- ── BUDGET ── -->
  {:else if activeTab==='budget'}
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('mytripsBudgetManual')}</h2>
      <input type="number" bind:value={budgetInput} placeholder={$t('mytripsBudgetPlaceholder')}
        class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <button onclick={saveBudget} class="w-full py-2.5 rounded-xl font-semibold text-sm"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        {$t('mytripsBudgetSave')}
      </button>
    </div>
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('mytripsActualSync')}</h2>
          <p class="text-xs mt-0.5" style="color:var(--ws-muted)">{$t('mytripsActualDesc')}</p>
        </div>
        <button onclick={syncActual} disabled={actualSyncing||!$apiUrl}
          class="px-4 py-2 rounded-xl text-sm font-semibold border transition-all disabled:opacity-40 shrink-0"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
          {actualSyncing ? $t('mytripsActualSyncing') : $t('mytripsActualBtn')}
        </button>
      </div>
      {#if actualResult}
        <div class="rounded-xl p-3 border space-y-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div class="flex justify-between text-sm font-semibold">
            <span>{$t('mytripsActualExpenses')}</span>
            <span style="color:var(--ws-accent)">
              {(actualResult.transactions?.reduce((s,t)=>s+Math.abs(t.amount??0),0)??0).toFixed(2)} €
            </span>
          </div>
          {#if actualResult.transactions?.length}
            <div class="space-y-1 max-h-48 overflow-y-auto">
              {#each actualResult.transactions.slice(0,20) as tx}
                <div class="flex justify-between text-xs py-1 border-b" style="border-color:var(--ws-border)">
                  <span class="truncate flex-1 mr-2">{tx.payee_name||tx.notes||'–'}</span>
                  <span class="font-mono shrink-0" style="color:var(--ws-muted)">{tx.date}</span>
                  <span class="font-mono font-bold ml-2 shrink-0" style="color:var(--ws-accent2)">{Math.abs(tx.amount??0).toFixed(2)} €</span>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </div>

  <!-- ── BUCKET LIST ── -->
  {:else if activeTab==='bucketlist'}
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">🌟 Bucket List</h2>
      <input bind:value={bucketItem} placeholder={$t('mytripsBucketItemPlaceholder')}
        class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <input bind:value={bucketDest} placeholder={$t('mytripsBucketDestPlaceholder')}
        class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <button onclick={addBucketItem} class="w-full py-2.5 rounded-xl font-semibold text-sm"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        {$t('mytripsAddBtn')}
      </button>
    </div>
    {#if $bucketlist.length===0}
      <p class="text-sm" style="color:var(--ws-muted)">{$t('mytripsBucketEmpty')}</p>
    {:else}
      <div class="space-y-2">
        {#each $bucketlist as item, i}
          <div class="flex items-center gap-3 p-3 rounded-xl border transition-opacity"
            class:opacity-50={item.done}
            style="background:var(--ws-surface);border-color:var(--ws-border)">
            <button onclick={() => toggleBucket(i)}
              class="w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 text-xs"
              style="border-color:{item.done?'var(--ws-green)':'var(--ws-border)'};background:{item.done?'var(--ws-green)':'transparent'};color:#fff">
              {item.done?'✓':''}
            </button>
            <div class="flex-1">
              <div class="text-sm" class:line-through={item.done}>{item.item}</div>
              {#if item.dest}<div class="text-xs font-mono" style="color:var(--ws-muted)">📍 {item.dest}</div>{/if}
            </div>
            <button onclick={() => removeBucket(i)} class="text-xs px-2 py-1 rounded-lg border"
              style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
          </div>
        {/each}
        <div class="text-xs text-right" style="color:var(--ws-muted)">
          {$bucketlist.filter(x=>x.done).length}/{$bucketlist.length} erledigt
        </div>
      </div>
    {/if}

  <!-- ── JOURNAL (Dawarich) ── -->
  {:else if activeTab==='journal'}
    <div class="flex items-start justify-between">
      <p class="text-sm" style="color:var(--ws-muted)">{journalTrips.length} Reisen erkannt</p>
      <button onclick={syncJournal} disabled={syncing}
        class="px-4 py-2 rounded-xl text-sm font-semibold border transition-all disabled:opacity-50"
        style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">
        {syncing ? '⏳ Sync…' : '🧭 Synchronisieren'}
      </button>
    </div>
    {#if syncInfo}
      <div class="rounded-xl px-4 py-2.5 text-xs border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
        ℹ️ {syncInfo}
      </div>
    {/if}
    {#if !$apiUrl}
      <div class="rounded-xl p-6 border-2 border-dashed text-center" style="border-color:var(--ws-border)">
        <div class="text-3xl mb-2">🗺️</div>
        <p class="text-sm italic" style="font-family:var(--ws-serif);color:var(--ws-muted)">Backend-URL in den Einstellungen konfigurieren</p>
      </div>
    {:else if journalLoad}
      <p class="text-sm" style="color:var(--ws-muted)">Lade…</p>
    {:else if journalTrips.length===0}
      <div class="rounded-xl p-6 border-2 border-dashed text-center" style="border-color:var(--ws-border)">
        <div class="text-3xl mb-2">🗺️</div>
        <p class="text-sm font-semibold italic mb-1" style="font-family:var(--ws-serif)">Noch keine Reisen erkannt</p>
        <p class="text-xs mb-3" style="color:var(--ws-muted)">Dawarich URL + Token + Home-Koordinaten in Einstellungen eintragen</p>
        <button onclick={syncJournal} disabled={syncing}
          class="px-4 py-2 rounded-xl text-sm font-semibold"
          style="background:var(--ws-accent);color:#fff5ec">
          {syncing ? '⏳ Sync…' : '🧭 Jetzt synchronisieren'}
        </button>
      </div>
    {:else}
      <div class="space-y-3">
        {#each journalTrips as trip}
          {@const loc=[trip.location_name,trip.country].filter(Boolean).join(', ')||`${trip.lat},${trip.lon}`}
          {@const mapsUrl=`https://www.google.com/maps?q=${trip.lat},${trip.lon}`}
          <div class="rounded-xl p-4 border flex gap-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <div class="w-9 h-9 rounded-full shrink-0 flex items-center justify-center text-sm mt-0.5"
              style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec;box-shadow:0 2px 8px rgba(196,98,45,.3)">
              📍
            </div>
            <div class="flex-1 min-w-0">
              <div class="font-bold italic truncate" style="font-family:var(--ws-serif)">{loc}</div>
              <div class="text-xs font-mono mt-0.5" style="color:var(--ws-muted)">{trip.start_date} → {trip.end_date}</div>
              <div class="mt-1.5 flex items-center gap-2">
                <span class="px-2 py-0.5 rounded-full text-xs font-mono font-bold"
                  style="background:rgba(196,98,45,.1);color:var(--ws-accent)">
                  {trip.nights} {trip.nights===1?'Nacht':'Nächte'}
                </span>
                <a href={mapsUrl} target="_blank"
                  class="px-2 py-0.5 rounded-full text-xs border"
                  style="border-color:var(--ws-border);color:var(--ws-muted)">🗺 Maps</a>
                <button onclick={() => deleteJournalTrip(trip.id)}
                  class="px-2 py-0.5 rounded-full text-xs border ml-auto"
                  style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {/if}
</div>
