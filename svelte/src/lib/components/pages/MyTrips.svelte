<script>
  import { trips, budget, bucketlist, apiUrl } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';

  let activeTab  = $state('overview');

  // Trip form
  let tripName  = $state('');
  let tripDate  = $state(new Date().toISOString().slice(0,10));
  let tripCost  = $state('');
  let tripSource = $state('manual');

  // Budget
  let budgetInput = $state('');
  $effect(() => { budgetInput = $budget || ''; });

  // ActualBudget sync
  let actualSyncing = $state(false);
  let actualResult  = $state(null); // { total, transactions }

  // Bucket list
  let bucketItem = $state('');
  let bucketDest = $state('');

  function addTrip() {
    if (!tripName||!tripDate||!tripCost) { toast('Bitte alle Felder ausfüllen','error'); return; }
    trips.update(t => [...t, { name:tripName, date:tripDate, cost:parseFloat(tripCost), source:tripSource }]);
    tripName=''; tripCost=''; tripSource='manual';
    toast('Reise hinzugefügt','success');
  }
  function removeTrip(i) { trips.update(t => t.filter((_,idx)=>idx!==i)); }

  function saveBudget() { budget.set(budgetInput); toast('Budget gespeichert','success'); }

  async function syncActual() {
    if (!$apiUrl) { toast('Backend-URL fehlt','warning'); return; }
    const url      = browser ? localStorage.getItem('s-actualUrl')      || '' : '';
    const password = browser ? localStorage.getItem('s-actualPassword') || '' : '';
    const file     = browser ? localStorage.getItem('s-actualFile')     || '' : '';
    const cats     = browser ? localStorage.getItem('s-travelCategories') || '' : '';
    if (!url || !password) {
      toast('ActualBudget URL + Passwort fehlen → Einstellungen → Integrationen','warning');
      return;
    }
    actualSyncing = true; actualResult = null;
    try {
      const r = await api('/api/budget/actual/transactions', {
        method: 'POST',
        body: JSON.stringify({
          actual_url:   url,
          actual_token: password,
          actual_file:  file   || null,
          categories:   cats   || null,
        }),
      });
      actualResult = r;
      toast(`${r.transactions?.length ?? 0} Transaktionen geladen ✓`, 'success');
    } catch(e) {
      toast('ActualBudget Sync fehlgeschlagen: ' + e.message, 'error');
    }
    actualSyncing = false;
  }

  function addBucketItem() {
    if (!bucketItem) { toast('Bitte Eintrag eingeben','error'); return; }
    bucketlist.update(l => [...l, { item:bucketItem, dest:bucketDest, done:false, created:new Date().toISOString().slice(0,10) }]);
    bucketItem=''; bucketDest='';
    toast('Hinzugefügt ✓','success');
  }
  function toggleBucket(i) { bucketlist.update(l => l.map((x,idx) => idx===i ? {...x,done:!x.done} : x)); }
  function removeBucket(i) { bucketlist.update(l => l.filter((_,idx)=>idx!==i)); }

  const totalBudget = $derived(parseFloat($budget)||0);
  const totalSpent  = $derived($trips.reduce((s,t)=>s+(parseFloat(t.cost)||0),0));
  const remaining   = $derived(Math.max(0,totalBudget-totalSpent));
  const pct         = $derived(totalBudget>0?Math.min(100,(totalSpent/totalBudget)*100):0);
  const today       = new Date().toISOString().slice(0,10);

  const tabs = [
    { id:'overview',   label:'📊 Übersicht' },
    { id:'trips',      label:'✈️ Reisen' },
    { id:'budget',     label:'💶 Budget' },
    { id:'bucketlist', label:'🌟 Bucket List' },
  ];
</script>

<div class="space-y-4">
  <h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif)">🎒 Meine Reisen</h1>

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

  {#if activeTab==='overview'}
    <div class="grid grid-cols-3 gap-3">
      {#each [
        { label:'Reisen', value:$trips.length, color:'var(--ws-text)' },
        { label:'Ausgegeben', value:totalSpent.toFixed(2)+' €', color:'var(--ws-accent)' },
        { label:'Verbleibend', value:totalBudget>0?remaining.toFixed(2)+' €':'–', color:'var(--ws-green)' },
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
          <span>Budget-Fortschritt</span><span>{pct.toFixed(0)}%</span>
        </div>
        <div class="h-2 rounded-full" style="background:var(--ws-border)">
          <div class="h-2 rounded-full transition-all"
            style="width:{pct}%;background:{pct>85?'var(--ws-red)':pct>60?'var(--ws-accent2)':'var(--ws-green)'}">
          </div>
        </div>
        <div class="flex justify-between text-xs mt-2" style="color:var(--ws-muted)">
          <span>{totalSpent.toFixed(2)} € ausgegeben</span>
          <span>{totalBudget.toFixed(2)} € gesamt</span>
        </div>
      </div>
    {/if}
    {#if $trips.length > 0}
      <div class="space-y-2">
        <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Letzte Reisen</div>
        {#each [...$trips].sort((a,b)=>b.date.localeCompare(a.date)).slice(0,3) as t}
          <div class="flex items-center gap-3 p-3 rounded-xl border" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <span>{t.date >= today ? '✈️' : '✅'}</span>
            <div class="flex-1">
              <div class="text-sm font-semibold italic" style="font-family:var(--ws-serif)">{t.name}</div>
              <div class="text-xs font-mono" style="color:var(--ws-muted)">{t.date}</div>
            </div>
            <div class="font-bold font-mono text-sm" style="color:var(--ws-accent2)">{parseFloat(t.cost).toFixed(2)} €</div>
          </div>
        {/each}
      </div>
    {/if}

  {:else if activeTab==='trips'}
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Reise hinzufügen</h2>
      <input bind:value={tripName} placeholder="Ziel / Name"
        class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <div class="grid grid-cols-2 gap-2">
        <input type="date" bind:value={tripDate}
          class="px-3 py-2 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        <input type="number" bind:value={tripCost} placeholder="Kosten €"
          class="px-3 py-2 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      </div>
      <button onclick={addTrip}
        class="w-full py-2.5 rounded-xl font-semibold text-sm"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        + Hinzufügen
      </button>
    </div>
    {#if $trips.length===0}
      <p class="text-sm" style="color:var(--ws-muted)">Noch keine Reisen erfasst.</p>
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
            <button onclick={() => removeTrip(i)}
              class="text-xs px-2 py-1 rounded-lg border"
              style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
          </div>
        {/each}
      </div>
    {/if}

  {:else if activeTab==='budget'}
    <!-- Manuelles Budget -->
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Jahresbudget (manuell)</h2>
      <input type="number" bind:value={budgetInput} placeholder="z.B. 3000"
        class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <button onclick={saveBudget}
        class="w-full py-2.5 rounded-xl font-semibold text-sm"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        Speichern
      </button>
    </div>

    <!-- ActualBudget Sync -->
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">
            ActualBudget Sync
          </h2>
          <p class="text-xs mt-0.5" style="color:var(--ws-muted)">
            Reiseausgaben aus ActualBudget importieren
          </p>
        </div>
        <button onclick={syncActual} disabled={actualSyncing || !$apiUrl}
          class="px-4 py-2 rounded-xl text-sm font-semibold border transition-all disabled:opacity-40 shrink-0"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
          {actualSyncing ? '⏳ Sync…' : '🔄 Synchronisieren'}
        </button>
      </div>

      {#if !$apiUrl}
        <p class="text-xs" style="color:var(--ws-muted)">Backend-URL in den Einstellungen konfigurieren.</p>
      {:else}
        <!-- Config hint -->
        {#if !browser || !localStorage.getItem('s-actualUrl')}
          <p class="text-xs" style="color:var(--ws-muted)">
            ⚙️ ActualBudget URL + Passwort in Einstellungen → Integrationen eintragen.
          </p>
        {/if}
      {/if}

      <!-- Result -->
      {#if actualResult}
        <div class="rounded-xl p-3 border space-y-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div class="flex justify-between text-sm font-semibold">
            <span>Reiseausgaben</span>
            <span style="color:var(--ws-accent)">
              {(actualResult.total ?? actualResult.transactions?.reduce((s,t) => s + Math.abs(t.amount ?? 0), 0) ?? 0).toFixed(2)} €
            </span>
          </div>
          {#if actualResult.transactions?.length}
            <div class="space-y-1 max-h-48 overflow-y-auto">
              {#each actualResult.transactions.slice(0,20) as tx}
                <div class="flex justify-between text-xs py-1 border-b" style="border-color:var(--ws-border)">
                  <span class="truncate flex-1 mr-2" style="color:var(--ws-text)">{tx.payee_name || tx.notes || '–'}</span>
                  <span class="font-mono shrink-0" style="color:var(--ws-muted)">{tx.date}</span>
                  <span class="font-mono font-bold ml-2 shrink-0" style="color:var(--ws-accent2)">
                    {Math.abs(tx.amount ?? 0).toFixed(2)} €
                  </span>
                </div>
              {/each}
              {#if actualResult.transactions.length > 20}
                <p class="text-xs text-center pt-1" style="color:var(--ws-muted)">
                  + {actualResult.transactions.length - 20} weitere
                </p>
              {/if}
            </div>
          {/if}
        </div>
      {/if}
    </div>

  {:else if activeTab==='bucketlist'}
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">🌟 Bucket List</h2>
      <input bind:value={bucketItem} placeholder="Was möchtest du erleben?"
        class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <input bind:value={bucketDest} placeholder="Zielort (optional)"
        class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <button onclick={addBucketItem}
        class="w-full py-2.5 rounded-xl font-semibold text-sm"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        + Hinzufügen
      </button>
    </div>
    {#if $bucketlist.length===0}
      <p class="text-sm" style="color:var(--ws-muted)">Noch keine Einträge — träume groß! 🌍</p>
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
            <button onclick={() => removeBucket(i)}
              class="text-xs px-2 py-1 rounded-lg border"
              style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
          </div>
        {/each}
        <div class="text-xs text-right" style="color:var(--ws-muted)">
          {$bucketlist.filter(x=>x.done).length}/{$bucketlist.length} erledigt
        </div>
      </div>
    {/if}
  {/if}
</div>
