<script>
  import { t } from '$lib/i18n.js';

  let {
    upcoming,
    completed,
    recentDawarich,
    yearBudget,
    yearSpent,
    yearRemaining,
    yearSpentPct,
    yearDonutFill,
    yearDonutColor,
    CIRC,
    loading,
    onnavto,
  } = $props();

  // Merge completed localStorage trips + recent Dawarich for display
  const pastItems = $derived.by(() => {
    const lsItems = completed.slice(0, 2).map(t => ({
      name:  t.name,
      date:  t.dateStart || t.date || '',
      cost:  t.cost ? parseFloat(t.cost) : null,
      src:   'planned',
    }));
    const dwItems = recentDawarich.slice(0, 3).map(t => ({
      name:  t.location_name || t.country || '?',
      date:  t.start_date || '',
      cost:  null,
      nights: t.nights,
      src:   'dawarich',
    }));
    // Merge, deduplicate by date prefix
    const seen = new Set(lsItems.map(i => i.date.slice(0, 7)));
    const filtered = dwItems.filter(i => !seen.has(i.date.slice(0, 7)));
    return [...lsItems, ...filtered].slice(0, 4);
  });
</script>

<div class="rounded-xl border overflow-hidden" style="background:var(--ws-surface);border-color:var(--ws-border)">

  <!-- Budget Donut header -->
  {#if yearBudget > 0}
    <div class="p-4 border-b" style="border-color:var(--ws-border)">
      <div class="flex items-center gap-4">
        <svg width="64" height="64" viewBox="0 0 100 100" class="shrink-0">
          <circle cx="50" cy="50" r="38" fill="none" stroke="var(--ws-border)" stroke-width="14"/>
          <circle cx="50" cy="50" r="38" fill="none" stroke={yearDonutColor} stroke-width="14"
            stroke-dasharray="{yearDonutFill} {CIRC - yearDonutFill}"
            stroke-dashoffset="60" stroke-linecap="round"
            style="transition:stroke-dasharray .6s ease"/>
          <text x="50" y="55" text-anchor="middle" font-size="18" font-weight="bold"
            fill="var(--ws-text)" font-family="var(--ws-serif)">
            {yearSpentPct.toFixed(0)}%
          </text>
        </svg>
        <div class="flex-1 space-y-1 text-xs min-w-0">
          {#each [
            { dot: 'var(--ws-accent)',  label: 'Ausgegeben',  val: yearSpent.toFixed(0) + ' €' },
            { dot: 'var(--ws-green)',   label: 'Verfügbar',   val: yearRemaining.toFixed(0) + ' €' },
            { dot: 'var(--ws-border)',  label: 'Budget ges.', val: yearBudget.toFixed(0) + ' €' },
          ] as row}
            <div class="flex items-center gap-1.5">
              <div class="w-2 h-2 rounded-full shrink-0" style="background:{row.dot}"></div>
              <span class="truncate" style="color:var(--ws-muted)">{row.label}</span>
              <span class="ml-auto font-mono font-bold shrink-0" style="color:var(--ws-text)">{row.val}</span>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}

  <!-- Upcoming trips -->
  <div class="p-4 border-b" style="border-color:var(--ws-border)">
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-xs font-bold uppercase tracking-widest" style="color:var(--ws-muted)">{$t('dashUpcoming')}</h2>
      {#if upcoming.length > 0}
        <span class="text-xs px-2 py-0.5 rounded-full font-medium"
          style="background:rgba(196,98,45,.1);color:var(--ws-accent)">{upcoming.length}</span>
      {/if}
    </div>

    {#if upcoming.length === 0}
      <p class="text-xs py-3 text-center" style="color:var(--ws-muted)">{$t('dashNoUpcoming')}</p>
    {:else}
      <div class="space-y-1.5">
        {#each upcoming.slice(0, 3) as tr}
          <div class="flex items-center gap-2 p-2 rounded-lg" style="background:var(--ws-surface2)">
            <span class="text-base shrink-0">✈️</span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold truncate" style="font-family:var(--ws-serif);color:var(--ws-text)">{tr.name}</div>
              <div class="text-xs font-mono" style="color:var(--ws-muted)">{tr.dateStart || tr.date}</div>
            </div>
            {#if tr.cost}
              <div class="text-sm font-bold font-mono shrink-0" style="color:var(--ws-accent2)">
                {parseFloat(tr.cost).toFixed(0)} €
              </div>
            {/if}
          </div>
        {/each}
        {#if upcoming.length > 3}
          <button onclick={() => onnavto('mytrips')} class="text-xs w-full text-center pt-1 hover:underline" style="color:var(--ws-muted)">
            + {upcoming.length - 3} weitere →
          </button>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Past / Dawarich trips -->
  <div class="p-4">
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-xs font-bold uppercase tracking-widest" style="color:var(--ws-muted)">{$t('dashCompleted')}</h2>
    </div>

    {#if pastItems.length === 0}
      <p class="text-xs py-3 text-center" style="color:var(--ws-muted)">{$t('dashNoCompleted')}</p>
    {:else}
      <div class="space-y-1.5">
        {#each pastItems as item}
          <div class="flex items-center gap-2 p-2 rounded-lg opacity-85" style="background:var(--ws-surface2)">
            <span class="text-base shrink-0">{item.src === 'dawarich' ? '📍' : '✅'}</span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold truncate" style="font-family:var(--ws-serif);color:var(--ws-text)">{item.name}</div>
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-mono" style="color:var(--ws-muted)">{item.date}</span>
                {#if item.nights}
                  <span class="text-xs" style="color:var(--ws-muted)">· {item.nights}N</span>
                {/if}
              </div>
            </div>
            {#if item.cost != null}
              <div class="text-sm font-bold font-mono shrink-0" style="color:var(--ws-muted)">
                {item.cost.toFixed(0)} €
              </div>
            {:else if item.src === 'dawarich'}
              <span class="text-[10px] px-1.5 py-0.5 rounded-full shrink-0"
                style="background:rgba(196,98,45,.1);color:var(--ws-accent)">GPS</span>
            {/if}
          </div>
        {/each}
      </div>
    {/if}

    <button onclick={() => onnavto('mytrips')}
      class="mt-3 w-full py-2 rounded-xl text-xs font-semibold transition-opacity hover:opacity-80 border"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
      {$t('dashAllJournal')} →
    </button>
  </div>

</div>
