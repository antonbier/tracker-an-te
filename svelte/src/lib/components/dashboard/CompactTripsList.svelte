<script>
  import { t } from '$lib/i18n.js';
  import { activeMyTripsTab } from '$lib/stores.js';

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

  // Source-Icon für alle Trip-Typen
  function srcIcon(trip) {
    if (trip.source === 'dawarich') return '📡';
    if (trip.source === 'manual')   return '✍️';
    return '🪄';  // ws_trips / WanderWizzard
  }

  // Titel: ws_trips haben title/destination, detected_trips haben location_name
  function tripLabel(trip) {
    return trip.title || trip.destination || trip.location_name || trip.name || '—';
  }

  // Datum: ws_trips haben start_date, detected_trips auch
  function tripDate(trip) {
    return trip.start_date || trip.dateStart || trip.date || '';
  }

  // Kosten aus ws_trips
  function tripCost(trip) {
    const booked = parseFloat(trip.booked_flight||0) + parseFloat(trip.booked_hotel||0);
    const manual = parseFloat(trip.manual_expenses||0);
    const synced = parseFloat(trip.synced_expenses||0);
    const total  = booked + manual + synced;
    return total || parseFloat(trip.budget||0) || parseFloat(trip.cost||0) || null;
  }
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

  <!-- Geplante Reisen: alle Typen (📡 / ✍️ / 🪄) -->
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
        {#each upcoming.slice(0, 3) as trip}
          <div class="flex items-center gap-2 p-2 rounded-lg" style="background:var(--ws-surface2)">
            <span class="text-base shrink-0">{srcIcon(trip)}</span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold truncate capitalize"
                style="font-family:var(--ws-serif);color:var(--ws-text)">{tripLabel(trip)}</div>
              <div class="text-xs font-mono" style="color:var(--ws-muted)">{tripDate(trip)}</div>
            </div>
            {#if tripCost(trip)}
              <div class="text-sm font-bold font-mono shrink-0"
                title="Gebuchte Kosten + Ausgaben"
                style="color:var(--ws-accent2)">
                {tripCost(trip).toFixed(0)} €
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
      <button onclick={() => { activeMyTripsTab.set('planned'); onnavto('mytrips'); }}
        class="mt-2 w-full py-1.5 rounded-lg text-xs font-medium transition-opacity hover:opacity-80 border"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-accent)">
        🧳 {$t('dashAllPlanned')}
      </button>
    {/if}
  </div>

  <!-- Abgeschlossene Reisen: alle Typen (📡 / ✍️ / 🪄) -->
  <div class="p-4">
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-xs font-bold uppercase tracking-widest" style="color:var(--ws-muted)">{$t('dashCompleted')}</h2>
    </div>

    {#if completed.length === 0}
      <p class="text-xs py-3 text-center" style="color:var(--ws-muted)">{$t('dashNoCompleted')}</p>
    {:else}
      <div class="space-y-1.5">
        {#each completed.slice(0, 4) as trip}
          <div class="flex items-center gap-2 p-2 rounded-lg opacity-85" style="background:var(--ws-surface2)">
            <span class="text-base shrink-0">{srcIcon(trip)}</span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold truncate capitalize"
                style="font-family:var(--ws-serif);color:var(--ws-text)">{tripLabel(trip)}</div>
              <div class="text-xs font-mono" style="color:var(--ws-muted)">{tripDate(trip)}</div>
            </div>
            {#if tripCost(trip)}
              <div class="text-sm font-bold font-mono shrink-0" style="color:var(--ws-muted)">
                {tripCost(trip).toFixed(0)} €
              </div>
            {:else}
              <span class="text-[10px] px-1.5 py-0.5 rounded-full shrink-0"
                style="background:rgba(196,98,45,.1);color:var(--ws-accent)">
                {trip.source === 'dawarich' ? 'GPS' : trip.nights ? trip.nights + 'N' : '—'}
              </span>
            {/if}
          </div>
        {/each}
      </div>
    {/if}

    <button onclick={() => { activeMyTripsTab.set('archive'); onnavto('mytrips'); }}
      class="mt-3 w-full py-2 rounded-xl text-xs font-semibold transition-opacity hover:opacity-80 border"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
      🗄️ {$t('dashToArchive')}
    </button>
  </div>

</div>
