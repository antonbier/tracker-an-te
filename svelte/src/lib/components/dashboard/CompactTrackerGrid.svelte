<script>
  import { t } from '$lib/i18n.js';

  let {
    allTrackers,
    loading,
    onnavto,
  } = $props();

  function providerIcon(type) {
    if (type === 'flight')        return '🟠';
    if (type === 'google_flight') return '🔵';
    if (type === 'camping')       return '⛺';
    if (type === 'hotel')         return '🏨';
    return '📍';
  }

  function trackerLabel(tr) {
    if (tr._type === 'flight' || tr._type === 'google_flight') {
      return (tr.origin && tr.destination) ? `${tr.origin} → ${tr.destination}` : tr.destination || '–';
    }
    if (tr._type === 'hotel')   return tr.hotel_name   || tr.destination || '–';
    if (tr._type === 'camping') return tr.campsite_name || tr.region      || '–';
    return tr.destination || '–';
  }

  function trackerDate(tr) {
    return tr.outbound_date || tr.checkin_date || '–';
  }

  function wishMet(tr) {
    const price = tr.latest_snapshot?.total_price;
    const wish  = tr.wish_price;
    return wish && price && price <= wish;
  }

  // Sort: wish-met first, then by price availability
  const sortedTrackers = $derived(
    [...allTrackers].sort((a, b) => {
      if (wishMet(a) && !wishMet(b)) return -1;
      if (!wishMet(a) && wishMet(b)) return 1;
      const pa = a.latest_snapshot?.total_price ?? Infinity;
      const pb = b.latest_snapshot?.total_price ?? Infinity;
      return pa - pb;
    })
  );
</script>

<div class="rounded-xl border overflow-hidden" style="background:var(--ws-surface);border-color:var(--ws-border)">

  <!-- Header -->
  <div class="p-4 border-b flex items-center justify-between" style="border-color:var(--ws-border)">
    <h2 class="text-xs font-bold uppercase tracking-widest" style="color:var(--ws-muted)">
      {$t('dashActiveTrackersCard')}
    </h2>
    {#if allTrackers.length > 0}
      <span class="text-xs px-2 py-0.5 rounded-full font-medium"
        style="background:rgba(196,98,45,.1);color:var(--ws-accent)">{allTrackers.length}</span>
    {/if}
  </div>

  <!-- Tracker tiles -->
  <div class="p-3">
    {#if loading}
      <div class="space-y-2">
        {#each [1, 2, 3] as _}
          <div class="h-14 rounded-xl animate-pulse" style="background:var(--ws-border)"></div>
        {/each}
      </div>

    {:else if allTrackers.length === 0}
      <div class="py-8 text-center">
        <div class="text-3xl mb-2">📡</div>
        <p class="text-xs" style="color:var(--ws-muted)">{$t('dashNoTrackers')}</p>
      </div>

    {:else}
      <div class="space-y-2">
        {#each sortedTrackers.slice(0, 6) as tr}
          {@const snap     = tr.latest_snapshot}
          {@const price    = snap?.total_price}
          {@const met      = wishMet(tr)}
          <button onclick={() => onnavto('priceradar')}
            class="w-full flex items-center gap-2.5 p-2.5 rounded-xl border text-left transition-all hover:border-[var(--ws-accent)] hover:shadow-sm"
            style="background:var(--ws-surface2);border-color:{met ? 'var(--ws-green)' : 'var(--ws-border)'}">

            <!-- Provider icon -->
            <span class="text-base shrink-0">{providerIcon(tr._type)}</span>

            <!-- Label + date -->
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold truncate" style="color:var(--ws-text)">{trackerLabel(tr)}</div>
              <div class="text-xs font-mono" style="color:var(--ws-muted)">{trackerDate(tr)}</div>
            </div>

            <!-- Price + wish indicator -->
            <div class="text-right shrink-0">
              {#if price != null}
                <div class="text-sm font-bold font-mono" style="color:{met ? 'var(--ws-green)' : 'var(--ws-text)'}">
                  {price.toFixed(2)} €
                </div>
                {#if met}
                  <div class="text-[10px] font-bold" style="color:var(--ws-green)">🎯 Ziel!</div>
                {:else if tr.wish_price}
                  <div class="text-[10px]" style="color:var(--ws-muted)">Ziel: {tr.wish_price.toFixed(0)} €</div>
                {/if}
              {:else}
                <div class="text-xs" style="color:var(--ws-muted)">–</div>
              {/if}
            </div>

          </button>
        {/each}

        {#if allTrackers.length > 6}
          <p class="text-xs text-center pt-1" style="color:var(--ws-muted)">
            + {allTrackers.length - 6} weitere
          </p>
        {/if}
      </div>
    {/if}

    <!-- CTA -->
    <button onclick={() => onnavto('priceradar')}
      class="mt-3 w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80"
      style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
      {allTrackers.length > 0 ? $t('dashActiveTrackersCard') + ' →' : $t('dashStartTracker')}
    </button>
  </div>

</div>
