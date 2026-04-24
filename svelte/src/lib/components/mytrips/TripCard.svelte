<script>
  /**
   * TripCard.svelte — Wiederverwendbare Reisekarte
   * Phase-aware: berechnet 3-Phasen-Logik direkt aus Datum.
   * Alle Karten (planned, archive, dawarich, manual) haben "Trip Hub →"-Button.
   * Source-Badge: 📡 Dawarich · ✍️ Manuell · 🪄 WanderWizzard
   */
  import { t } from '$lib/i18n.js';
  import { destinationGradient } from '$lib/components/triphub/helpers.js';
  import { fmtDate } from '$lib/utils.js';
  import { today, getTripPhase } from '$lib/utils.js';

  let {
    trip,
    mode        = 'planned',   // 'planned' | 'archive'
    ongoToHub   = () => {},
  } = $props();

  const isFlight = $derived(trip.travel_mode === 'flight');

  // 3-Phasen-Logik direkt aus Datum
  const phase = $derived(getTripPhase(trip));

  // Hero gradient
  const heroGradient = $derived.by(() => {
    if (phase === 'active') return 'linear-gradient(135deg,#0f4c2a 0%,#1a6b3a 50%,#0d3d22 100%)';
    const base = destinationGradient(trip.destination || trip.title || trip.name, trip.travel_mode);
    return base;
  });

  // Robustes Fallback-Mapping für beide Trip-Typen:
  // detected_trips: location_name, country
  // ws_trips:       title, destination
  function notEmpty(v) { return v && v.trim() !== '' && v.trim() !== '-'; }
  // Block 7 — Strikte Fallback-Kette:
  // 1. title       = kosmetischer Name (WanderWizzard-Trips nach Edit)
  // 2. destination = geocodierter Ort  (alle Trips, Kernfeld)
  // 3. location_name/name = Dawarich-Altdaten
  // 4. country     = letzter Fallback
  const tripTitle = $derived(
    notEmpty(trip.title)         ? trip.title         :
    notEmpty(trip.destination)   ? trip.destination   :
    notEmpty(trip.location_name) ? trip.location_name :
    notEmpty(trip.name)          ? trip.name          :
    notEmpty(trip.country)       ? trip.country       : '—'
  );

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

  const badgePulse = $derived(phase === 'active');

  // Source-Badge Icon
  const sourceIcon = $derived.by(() => {
    const src = trip.source || (trip.id && !trip.start_date ? 'ws' : '');
    // ws_trips haben kein "source"-Feld — sie kommen von /api/ws-trips
    // detected_trips haben source: 'dawarich' | 'manual'
    if (src === 'dawarich') return '📡';
    if (src === 'manual')   return '✍️';
    // WanderWizzard-Trips (ws_trips) haben kein source-Feld
    return '🪄';
  });

  // Alle Karten navigieren zum Trip Hub
  // detected_trips (dawarich/manual) triggern on-the-fly Container-Erstellung
  const travelIcon  = $derived(isFlight ? '✈️' : '🚗');
  const tripDateStr = $derived.by(() => {
    const s = trip.start_date || trip.dateStart || '';
    const e = trip.end_date   || trip.dateEnd   || '';
    if (!s) return '';
    return e && e !== s ? `${fmtDate(s)} → ${fmtDate(e)}` : fmtDate(s);
  });
</script>

<div class="relative rounded-2xl border overflow-hidden transition-all hover:shadow-lg group"
  style="border-color:var(--ws-border);background:var(--ws-surface2)">

  <!-- ── Hero header ──────────────────────────────────────────────────────── -->
  <div class="px-5 pt-5 pb-3 relative" style="background:{heroGradient};min-height:88px;{phase==='archived'?'opacity:0.85;filter:saturate(0.6)':''}">
    <div class="flex items-start justify-between">
      <span class="text-2xl">{travelIcon}</span>

      <div class="flex items-center gap-1.5">
        <!-- Source-Badge -->
        <span class="text-sm" title={trip.source === 'dawarich' ? 'Dawarich GPS' : trip.source === 'manual' ? 'Manuell eingetragen' : 'WanderWizzard'}>
          {sourceIcon}
        </span>
        <!-- Status badge -->
        <span class="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full"
          style="background:{badgeBg};color:rgba(255,255,255,.9)">
          {#if badgePulse}
            <span class="w-1 h-1 rounded-full animate-pulse" style="background:#4ade80"></span>
          {/if}
          {badgeText}
        </span>
      </div>
    </div>

    <!-- FIX: capitalize für Ortnamen -->
    <h3 class="font-bold text-base mt-2 leading-tight pr-2"
      style="font-family:var(--ws-serif);color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.45);text-transform:capitalize">
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

  <!-- ── Action button — immer "Trip Hub →" ───────────────────────────────── -->
  <div class="px-5 pb-4">
    <button onclick={() => ongoToHub(trip)}
      class="w-full py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-85 active:scale-[.98]"
      style="background:var(--ws-accent);color:#fff5ec">
      {$t('tripCardGoToHub') || 'Trip Hub →'}
    </button>
  </div>

</div>
