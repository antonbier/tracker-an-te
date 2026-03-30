<script>
  import { trips, budget } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';

  let activeTab  = $state('overview');
  let tripName   = $state('');
  let tripDate   = $state(new Date().toISOString().slice(0,10));
  let tripCost   = $state('');
  let budgetInput = $state('');

  $effect(() => { budgetInput = $budget || ''; });

  function addTrip() {
    if (!tripName || !tripDate || !tripCost) { toast('Bitte alle Felder ausfüllen', 'error'); return; }
    trips.update(t => [...t, { name: tripName, date: tripDate, cost: parseFloat(tripCost) }]);
    tripName = ''; tripCost = '';
    toast('Reise hinzugefügt', 'success');
  }

  function removeTrip(i) {
    trips.update(t => t.filter((_, idx) => idx !== i));
  }

  function saveBudget() {
    budget.set(budgetInput);
    toast('Budget gespeichert', 'success');
  }

  const totalSpent = $derived($trips.reduce((s, t) => s + (parseFloat(t.cost) || 0), 0));
  const totalBudget = $derived(parseFloat($budget) || 0);
  const pct = $derived(totalBudget > 0 ? Math.min(100, (totalSpent / totalBudget) * 100) : 0);

  const tabs = [
    { id: 'overview', label: '📊 Übersicht' },
    { id: 'trips',    label: '✈️ Reisen' },
    { id: 'budget',   label: '💶 Budget' },
  ];
</script>

<div class="space-y-4">
  <h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif)">🎒 Meine Reisen</h1>

  <div class="flex gap-1 overflow-x-auto pb-1">
    {#each tabs as tab}
      <button
        onclick={() => activeTab = tab.id}
        class="px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all border"
        style={activeTab === tab.id
          ? 'background:var(--ws-accent);color:#fff5ec;border-color:var(--ws-accent)'
          : 'background:var(--ws-surface);color:var(--ws-muted);border-color:var(--ws-border)'}
      >{tab.label}</button>
    {/each}
  </div>

  {#if activeTab === 'overview'}
    <div class="grid md:grid-cols-3 gap-3">
      {#each [
        { label: 'Reisen', value: $trips.length },
        { label: 'Ausgegeben', value: totalSpent.toFixed(2) + ' €', color: 'var(--ws-accent)' },
        { label: 'Verbleibend', value: totalBudget > 0 ? Math.max(0, totalBudget - totalSpent).toFixed(2) + ' €' : '–', color: 'var(--ws-green)' },
      ] as s}
        <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
          <div class="text-xs font-bold uppercase tracking-wider mb-1" style="color:var(--ws-muted)">{s.label}</div>
          <div class="text-2xl font-bold" style="color:{s.color ?? 'var(--ws-text)'};font-family:var(--ws-serif)">{s.value}</div>
        </div>
      {/each}
    </div>
    {#if totalBudget > 0}
      <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
        <div class="flex justify-between text-xs mb-2" style="color:var(--ws-muted)">
          <span>Budget-Fortschritt</span><span>{pct.toFixed(0)}%</span>
        </div>
        <div class="h-2 rounded-full" style="background:var(--ws-border)">
          <div class="h-2 rounded-full transition-all"
            style="width:{pct}%;background:{pct > 85 ? 'var(--ws-red)' : pct > 60 ? 'var(--ws-accent2)' : 'var(--ws-green)'}">
          </div>
        </div>
      </div>
    {/if}

  {:else if activeTab === 'trips'}
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Reise hinzufügen</h2>
      <input bind:value={tripName} placeholder="Ziel / Name" class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <div class="grid grid-cols-2 gap-2">
        <input type="date" bind:value={tripDate} class="px-3 py-2 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        <input type="number" bind:value={tripCost} placeholder="Kosten €" class="px-3 py-2 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      </div>
      <button onclick={addTrip}
        class="w-full py-2.5 rounded-xl font-semibold text-sm"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        + Hinzufügen
      </button>
    </div>
    <div class="space-y-2">
      {#each $trips as t, i}
        <div class="flex items-center gap-3 p-3 rounded-xl border" style="background:var(--ws-surface);border-color:var(--ws-border)">
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

  {:else if activeTab === 'budget'}
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Jahresbudget</h2>
      <input type="number" bind:value={budgetInput} placeholder="z.B. 3000" class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <button onclick={saveBudget}
        class="w-full py-2.5 rounded-xl font-semibold text-sm"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        Speichern
      </button>
    </div>
  {/if}
</div>
