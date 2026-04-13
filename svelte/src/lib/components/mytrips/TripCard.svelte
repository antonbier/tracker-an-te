<script>
  /**
   * TripCard.svelte — Wiederverwendbare Reisekarte
   * Unterstützt zwei Modi:
   *   mode="planned"  → Gradient, Status-Badge, "Trip Hub →"-Button
   *   mode="archive"  → Gedämpfter Gradient, "ERLEBT"-Badge, ⋮-Menü für Aktionen
   */
  import { t } from '$lib/i18n.js';

  let {
    trip,
    mode        = 'planned',   // 'planned' | 'archive'
    ongoToHub   = () => {},
    ondelete    = () => {},
  } = $props();

  let menuOpen = $state(false);

  const isFlight = $derived(trip.travel_mode === 'flight' || trip.travel_mode === 'flight');

  // Hero gradient — archive gets a more muted / sepia tone
  const heroGradient = $derived.by(() => {
    if (mode === 'archive') {
      return isFlight
        ? 'linear-gradient(135deg,#1a2030 0%,#3a3020 100%)'
        : 'linear-gradient(135deg,#1a2820 0%,#2a4030 100%)';
    }
    return isFlight
      ? 'linear-gradient(135deg,#1a2a4a 0%,var(--ws-accent) 100%)'
      : 'linear-gradient(135deg,#1a3a2a 0%,#2d6a4f 100%)';
  });

  const badgeText = $derived.by(() => {
    if (mode === 'archive') return $t('tripCardExperienced');
    if (trip.status === 'booked') return $t('tripCardBooked');
    return $t('tripCardPlanning');
  });

  const badgeBg = $derived.by(() => {
    if (mode === 'archive') return 'rgba(255,255,255,.12)';
    if (trip.status === 'booked') return 'rgba(45,106,79,.7)';
    return 'rgba(255,255,255,.2)';
  });

  const actionBtnLabel = $derived(
    mode === 'archive' ? $t('tripCardView') : $t('tripCardGoToHub')
  );

  const travelIcon   = $derived(isFlight ? '✈️' : '🚗');
  const tripTitle    = $derived(trip.title || trip.destination || trip.name || '—');
  const tripDateStr  = $derived.by(() => {
    const s = trip.start_date || trip.dateStart || '';
    const e = trip.end_date   || trip.dateEnd   || '';
    if (!s) return '';
    return e && e !== s ? `${s} → ${e}` : s;
  });
</script>

<div class="relative rounded-2xl border overflow-hidden transition-all hover:shadow-lg group"
  style="border-color:var(--ws-border);background:var(--ws-surface2)">

  <!-- ── Hero header ──────────────────────────────────────────────────────── -->
  <div class="px-5 pt-5 pb-3 relative" style="background:{heroGradient};min-height:88px">
    <div class="flex items-start justify-between">
      <span class="text-2xl">{travelIcon}</span>

      <div class="flex items-center gap-2">
        <!-- Status badge -->
        <span class="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full"
          style="background:{badgeBg};color:rgba(255,255,255,.9)">
          {badgeText}
        </span>

        <!-- ⋮ Menu (archive mode only) -->
        {#if mode === 'archive'}
          <div class="relative">
            <button
              onclick={(e) => { e.stopPropagation(); menuOpen = !menuOpen; }}
              class="w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold transition-all hover:opacity-80"
              style="background:rgba(255,255,255,.15);color:rgba(255,255,255,.85)">
              ⋮
            </button>
            {#if menuOpen}
              <!-- Click-outside backdrop -->
              <div class="fixed inset-0 z-10" role="button" tabindex="-1" aria-label="close"
                onclick={() => menuOpen = false}></div>
              <div class="absolute right-0 top-8 z-20 rounded-xl shadow-xl border overflow-hidden min-w-[130px]"
                style="background:var(--ws-surface);border-color:var(--ws-border)">
                <button onclick={() => { menuOpen = false; ondelete(trip); }}
                  class="w-full text-left px-4 py-2.5 text-xs font-semibold transition-all hover:opacity-75"
                  style="color:#ef4444">
                  🗑️ {$t('tripCardDelete')}
                </button>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    </div>

    <h3 class="font-bold text-base mt-2 leading-tight pr-2"
      style="font-family:var(--ws-serif);color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.45)">
      {tripTitle}
    </h3>
  </div>

  <!-- ── Meta ─────────────────────────────────────────────────────────────── -->
  <div class="px-5 py-3 space-y-1">
    {#if tripDateStr}
      <div class="text-xs font-mono" style="color:var(--ws-muted)">📅 {tripDateStr}</div>
    {/if}
    {#if trip.budget || trip.cost || trip.auto_cost}
      <div class="text-xs" style="color:var(--ws-muted)">
        💶 {parseFloat(trip.budget ?? trip.cost ?? trip.auto_cost ?? 0).toFixed(0)} €
      </div>
    {/if}
    {#if trip.vibes?.length}
      <div class="text-xs" style="color:var(--ws-muted)">{trip.vibes.slice(0, 3).join(' · ')}</div>
    {/if}
    {#if trip.destination && trip.title && trip.destination !== trip.title}
      <div class="text-xs" style="color:var(--ws-muted)">📍 {trip.destination}</div>
    {/if}
  </div>

  <!-- ── Action button ─────────────────────────────────────────────────────── -->
  <div class="px-5 pb-4">
    <button onclick={() => ongoToHub(trip)}
      class="w-full py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-85 active:scale-[.98]"
      style={mode === 'archive'
        ? 'background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)'
        : 'background:var(--ws-accent);color:#fff5ec'}>
      {actionBtnLabel}
    </button>
  </div>

</div>
