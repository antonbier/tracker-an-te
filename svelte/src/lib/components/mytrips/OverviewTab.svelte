<script>
  import { t } from '$lib/i18n.js';
  import ScratchMap from '$lib/components/ScratchMap.svelte';

  let {
    journalYear,
    upcomingTrips,
    journalSpentYear,
    tripsSpentYear,
    totalSpentYear,
    yearBudget,
    remainingYear,
    pctYear,
    overBudget,
    donutGradient,
    selectedYear,
    journalTrips,
    plannedTrips,
    onswitchtab,
  } = $props();

  const card = 'rounded-xl shadow-sm p-5 border';
</script>

<!-- 4 Stats-Karten -->
<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
  <button onclick={() => onswitchtab('journal')}
    class="{card} text-center hover:border-orange-200 hover:shadow-md transition-all group cursor-pointer"
    style="background:var(--ws-surface);border-color:var(--ws-border)">
    <div class="text-2xl mb-1">✅</div>
    <div class="text-xs font-medium mb-0.5 uppercase tracking-wide" style="color:var(--ws-muted)">Vergangen</div>
    <div class="text-xl font-bold group-hover:text-orange-600 transition-colors" style="font-family:var(--ws-serif);color:var(--ws-text)">{journalYear.length}</div>
    <div class="text-[10px] mt-1" style="color:var(--ws-muted)">→ Chronik</div>
  </button>
  <button onclick={() => onswitchtab('trips')}
    class="{card} text-center hover:border-orange-200 hover:shadow-md transition-all group cursor-pointer"
    style="background:var(--ws-surface);border-color:var(--ws-border)">
    <div class="text-2xl mb-1">✈️</div>
    <div class="text-xs font-medium mb-0.5 uppercase tracking-wide" style="color:var(--ws-muted)">Geplant</div>
    <div class="text-xl font-bold group-hover:text-orange-600 transition-colors" style="font-family:var(--ws-serif);color:var(--ws-text)">{upcomingTrips.length}</div>
    <div class="text-[10px] mt-1" style="color:var(--ws-muted)">→ Geplante Reisen</div>
  </button>
  <button onclick={() => onswitchtab('bucketlist')}
    class="{card} text-center hover:border-orange-200 hover:shadow-md transition-all group cursor-pointer"
    style="background:var(--ws-surface);border-color:var(--ws-border)">
    <div class="text-2xl mb-1">🌟</div>
    <div class="text-xs font-medium mb-0.5 uppercase tracking-wide" style="color:var(--ws-muted)">Wunschziele</div>
    <div class="text-xl font-bold group-hover:text-orange-600 transition-colors" style="font-family:var(--ws-serif);color:var(--ws-text)">{upcomingTrips.length}</div>
    <div class="text-[10px] mt-1" style="color:var(--ws-muted)">→ Bucket List</div>
  </button>
  <div class="{card} text-center" style="background:var(--ws-surface);border-color:var(--ws-border)">
    <div class="text-2xl mb-1">💸</div>
    <div class="text-xs font-medium mb-0.5 uppercase tracking-wide" style="color:var(--ws-muted)">{$t('mytripsStatsSpent')}</div>
    <div class="text-xl font-bold text-orange-600" style="font-family:var(--ws-serif)">{totalSpentYear.toFixed(2)} €</div>
    {#if yearBudget > 0}
      <div class="text-[10px] mt-1" style="color:{overBudget ? '#f87171' : 'var(--ws-muted)'}">
        {overBudget ? '⚠️ überschritten' : remainingYear.toFixed(0) + ' € frei'}
      </div>
    {/if}
  </div>
</div>

<!-- Donut-Chart Budget -->
{#if yearBudget > 0}
  <div class="{card}" style="background:var(--ws-surface);border-color:var(--ws-border)">
    <div class="flex items-center gap-6">
      <!-- Donut -->
      <div class="relative shrink-0 w-24 h-24">
        <div class="w-24 h-24 rounded-full" style="background:{donutGradient}"></div>
        <div class="absolute inset-3 rounded-full flex flex-col items-center justify-center"
          style="background:var(--ws-surface)">
          <span class="text-xs font-bold" style="color:{overBudget ? '#f87171' : 'var(--ws-text)'}">{pctYear.toFixed(0)}%</span>
          <span class="text-[9px]" style="color:var(--ws-muted)">{selectedYear}</span>
        </div>
      </div>
      <!-- Legende -->
      <div class="flex-1 space-y-2 text-xs">
        <button onclick={() => onswitchtab('journal')}
          class="flex items-center gap-2 w-full text-left hover:opacity-70 transition-opacity group">
          <span class="w-3 h-3 rounded-sm shrink-0" style="background:#2d6a4f"></span>
          <span style="color:var(--ws-muted)">Vergangen</span>
          <span class="ml-auto font-mono font-semibold" style="color:var(--ws-text)">{journalSpentYear.toFixed(2)} €</span>
        </button>
        <button onclick={() => onswitchtab('trips')}
          class="flex items-center gap-2 w-full text-left hover:opacity-70 transition-opacity group">
          <span class="w-3 h-3 rounded-sm shrink-0" style="background:#86efac"></span>
          <span style="color:var(--ws-muted)">Geplant</span>
          <span class="ml-auto font-mono font-semibold" style="color:var(--ws-text)">{tripsSpentYear.toFixed(2)} €</span>
        </button>
        {#if overBudget}
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-sm shrink-0" style="background:#ef4444"></span>
            <span class="text-red-500 font-semibold">Überschuss</span>
            <span class="ml-auto font-mono font-semibold text-red-500">{(totalSpentYear - yearBudget).toFixed(2)} €</span>
          </div>
        {:else}
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-sm shrink-0" style="background:#e2e8f0"></span>
            <span style="color:var(--ws-muted)">Verfügbar</span>
            <span class="ml-auto font-mono" style="color:var(--ws-muted)">{remainingYear.toFixed(2)} €</span>
          </div>
        {/if}
        <div class="pt-1 border-t flex justify-between font-semibold" style="border-color:var(--ws-border);color:var(--ws-text)">
          <span>Budget gesamt</span>
          <span class="font-mono">{yearBudget.toFixed(2)} €</span>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Weltkarte -->
<div class="{card} !p-4" style="background:var(--ws-surface);border-color:var(--ws-border)">
  <div class="flex items-center justify-between mb-3">
    <h2 class="text-sm font-semibold" style="color:var(--ws-text)">🗺️ Meine Reisekarte — {selectedYear}</h2>
    <span class="text-xs" style="color:var(--ws-muted)">{journalYear.length} Chronik · {upcomingTrips.length} geplant</span>
  </div>
  <ScratchMap {journalTrips} {plannedTrips} {selectedYear} />
</div>

<!-- Nächste Abenteuer -->
{#if upcomingTrips.length > 0}
  <div class={card} style="background:var(--ws-surface);border-color:var(--ws-border)">
    <h2 class="text-sm font-semibold mb-3" style="color:var(--ws-text)">
      ✈️ Nächste Abenteuer <span class="ml-1 text-xs font-normal" style="color:var(--ws-muted)">({upcomingTrips.length})</span>
    </h2>
    <div class="space-y-2">
      {#each upcomingTrips.slice(0,4) as tr}
        {@const start = tr.dateStart||tr.date||''}
        {@const end   = tr.dateEnd||''}
        <div class="flex items-center gap-3 py-2 border-b last:border-0" style="border-color:var(--ws-border)">
          <span class="text-lg">✈️</span>
          <div class="flex-1 min-w-0">
            <div style="font-family:var(--ws-serif);color:var(--ws-text)" class="text-sm font-semibold truncate">{tr.name}</div>
            <div class="text-xs font-mono" style="color:var(--ws-muted)">{start}{end&&end!==start?' → '+end:''}</div>
          </div>
          <div class="text-sm font-bold text-orange-600 font-mono shrink-0">{parseFloat(tr.cost).toFixed(2)} €</div>
        </div>
      {/each}
      {#if upcomingTrips.length > 4}
        <button onclick={() => onswitchtab('trips')} class="text-xs text-orange-600 hover:underline pt-1">+ {upcomingTrips.length-4} weitere →</button>
      {/if}
    </div>
  </div>
{/if}

<!-- Letzte Erinnerungen -->
{#if journalYear.length > 0}
  <div class={card} style="background:var(--ws-surface);border-color:var(--ws-border)">
    <h2 class="text-sm font-semibold mb-3" style="color:var(--ws-text)">
      ✅ Letzte Erinnerungen — {selectedYear}
      <span class="ml-1 text-xs font-normal" style="color:var(--ws-muted)">({journalYear.length})</span>
    </h2>
    <div class="space-y-2">
      {#each journalYear.slice(0,4) as tr}
        {@const name  = tr.location_name||tr.name||'–'}
        {@const start = tr.start_date||''}
        {@const end   = tr.end_date||''}
        {@const cost  = tr.cost ?? tr.auto_cost}
        <div class="flex items-center gap-3 py-2 border-b last:border-0" style="border-color:var(--ws-border)">
          <span class="text-lg">{tr.source==='manual'?'✍️':'📍'}</span>
          <div class="flex-1 min-w-0">
            <div style="font-family:var(--ws-serif);color:var(--ws-text)" class="text-sm font-semibold truncate">{name}</div>
            <div class="text-xs font-mono" style="color:var(--ws-muted)">{start}{end&&end!==start?' → '+end:''}</div>
          </div>
          {#if cost != null}
            <div class="text-sm font-bold font-mono shrink-0" style="color:var(--ws-muted)">{parseFloat(cost).toFixed(2)} €</div>
          {/if}
        </div>
      {/each}
      {#if journalYear.length > 4}
        <button onclick={() => onswitchtab('journal')} class="text-xs text-orange-600 hover:underline pt-1">+ {journalYear.length-4} weitere →</button>
      {/if}
    </div>
  </div>
{/if}
