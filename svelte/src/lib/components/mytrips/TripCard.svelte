<script>
  /**
   * TripCard.svelte — Wiederverwendbare Reisekarte
   * Phase-aware: berechnet 3-Phasen-Logik direkt aus Datum,
   * unabhängig vom übergebenen mode-Prop.
   *   mode="planned"  → Gradient, Status-Badge, "Trip Hub →"-Button
   *   mode="archive"  → Gedämpfter Gradient, ⋮-Menü für Aktionen
   */
  import { t } from '$lib/i18n.js';
  import { destinationGradient } from '$lib/components/triphub/helpers.js';

  let {
    trip,
    mode        = 'planned',   // 'planned' | 'archive'
    ongoToHub   = () => {},
  } = $props();

  const isFlight = $derived(trip.travel_mode === 'flight');

  // FIX: 3-Phasen-Logik direkt aus Datum — nicht nur aus mode-Prop
  const today = new Date().toISOString().slice(0, 10);

  const phase = $derived.by(() => {
    const t_start = (trip.start_date || '').slice(0, 10);
    const t_end   = (trip.end_date   || trip.start_date || '').slice(0, 10);
    if (!t_end) return 'planning';
    if (today > t_end)    return 'archived';
    if (today >= t_start) return 'active';
    return 'planning';
  });

  // Hero gradient — generative from destination, no external images
  const heroGradient = $derived.by(() => {
    if (phase === 'active') return 'linear-gradient(135deg,#0f4c2a 0%,#1a6b3a 50%,#0d3d22 100%)';
    const base = destinationGradient(trip.destination || trip.title || trip.name, trip.travel_mode);
    if (phase === 'archived') {
      // desaturate archived: overlay dark tint
      return base.replace('linear-gradient(', 'linear-gradient(').replace(/,#/g, ',#');
    }
    return base;
  });

  // FIX: badge text basiert auf phase, nicht nur auf mode
  const badgeText = $derived.by(() => {
    if (phase === 'archived') return $t('tripCardExperienced') || 'ERLEBT';
    if (phase === 'active')   return $t('tripPhaseActive')     || 'ON TOUR';
    if (trip.status === 'booked') return $t('tripCardBooked')  || 'GEBUCHT';
    return $t('tripCardPlanning') || 'IN PLANUNG';
  });

  const badgeBg = $derived.by(() => {
    if (phase === 'archived') return 'rgba(255,255,255,.12)';
    if (phase === 'active')   return 'rgba(45,106,79,.7)';
    if (trip.status === 'booked') return 'rgba(45,106,79,.7)';
    return 'rgba(255,255,255,.2)';
  });

  // FIX: Pulseeffekt für aktive Reisen
  const badgePulse = $derived(phase === 'active');

  // Label: ws-trips get "Trip Hub →", detected_trips (archive mode) get "Erlebt ✓"
  const actionBtnLabel = $derived(
    mode === 'archive' ? ($t('tripCardExperienced') || 'ERLEBT') : ($t('tripCardGoToHub') || 'Trip Hub →')
  );
  // Archive-mode cards (detected_trips) are not navigable to TripHub
  const isNavigable = $derived(mode !== 'archive');

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
  <div class="px-5 pt-5 pb-3 relative" style="background:{heroGradient};min-height:88px;{phase==='archived'?'opacity:0.85;filter:saturate(0.6)':''}">
    <!-- Generative gradient background — no external image requests -->
    <div class="flex items-start justify-between">
      <span class="text-2xl">{travelIcon}</span>

      <div class="flex items-center gap-2">
        <!-- Status badge mit Pulse für active -->
        <span class="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full"
          style="background:{badgeBg};color:rgba(255,255,255,.9)">
          {#if badgePulse}
            <span class="w-1 h-1 rounded-full animate-pulse" style="background:#4ade80"></span>
          {/if}
          {badgeText}
        </span>

        <!-- Delete moved to TripHub — no menu on cards -->
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
    {#if isNavigable}
      <button onclick={() => ongoToHub(trip)}
        class="w-full py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-85 active:scale-[.98]"
        style="background:var(--ws-accent);color:#fff5ec">
        {actionBtnLabel}
      </button>
    {:else}
      <!-- detected_trip — no TripHub, just show "Erlebt" label -->
      <div class="w-full py-2 rounded-xl text-sm font-semibold text-center cursor-default"
        style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)">
        ✓ {$t('tripCardExperienced') || 'ERLEBT'}
      </div>
    {/if}
  </div>

</div>
