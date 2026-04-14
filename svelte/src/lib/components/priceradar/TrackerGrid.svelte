<script>
  import { t } from '$lib/i18n.js';
  import TrackerCard from './TrackerCard.svelte';

  let {
    trackers,
    allCount,
    loading,
    isRefreshing,
    activeCategory,
    wsTrips      = [],
    chartState   = $bindable(),
    wishState    = $bindable(),
    stopsOpen    = $bindable(),
    onrefreshall,
    ondelete,
    onscrape,
    onwishsave,
    ontogglerchart,
    onlinktrip,
  } = $props();
</script>

<div>
  <div class="flex items-center justify-between gap-2 mb-3 flex-wrap">
    <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">
      📌 {$t('radarActiveTrackers')}
      {#if trackers.length > 0}
        <span class="ml-1 text-xs font-normal" style="color:var(--ws-muted)">({trackers.length} / {allCount} {$t('radarTotal') || 'gesamt'})</span>
      {/if}
    </h2>
    {#if allCount > 0}
      <button
        onclick={onrefreshall}
        disabled={isRefreshing}
        class="px-3 py-1.5 rounded-xl text-xs border transition-all disabled:opacity-50"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
        {isRefreshing ? '⏳ ' + $t('radarRefreshing') : '🔄 ' + $t('radarRefreshAll')}
      </button>
    {/if}
  </div>

  {#if loading}
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 items-stretch">
      {#each [1,2,3] as _}
        <div class="rounded-2xl border animate-pulse overflow-hidden" style="background:var(--ws-surface);border-color:var(--ws-border)">
          <div class="h-[72px]" style="background:var(--ws-surface2)"></div>
          <div class="p-4 space-y-2">
            <div class="h-3 w-32 rounded" style="background:var(--ws-border)"></div>
            <div class="h-8 rounded" style="background:var(--ws-border)"></div>
          </div>
        </div>
      {/each}
    </div>

  {:else if trackers.length === 0}
    <div class="rounded-xl p-6 border text-center" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <div class="text-2xl mb-2">📭</div>
      <p class="text-xs" style="color:var(--ws-muted)">
        {allCount > 0
          ? ($t('radarNoTypeTrackers') || 'Keine') + ' ' + (activeCategory === 'flights' ? 'Flug' : activeCategory === 'hotels' ? 'Hotel' : 'Camping') + '-Tracker — oben suchen und speichern!'
          : $t('dashNoTrackers')}
      </p>
    </div>

  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4 items-stretch">
      {#each trackers as tr}
        {@const cKey = `${tr._type}-${tr.id}`}
        <TrackerCard
          {tr}
          {wsTrips}
          bind:chartData={chartState[cKey]}
          bind:wishData={wishState[cKey]}
          bind:stopsOpenMap={stopsOpen}
          ondelete={() => ondelete(tr)}
          onscrape={() => onscrape(tr)}
          onwishsave={(val) => onwishsave(tr._type, tr.id, tr._table, val)}
          ontogglerchart={() => ontogglerchart(tr._type, tr.id)}
          onwishedit={(editing) => {
            wishState[cKey] = editing
              ? { ...wishState[cKey], editing: true, value: tr.wish_price?.toString() || '' }
              : { editing: false };
          }}
          onlinktrip={onlinktrip}
        />
      {/each}
    </div>
  {/if}
</div>
