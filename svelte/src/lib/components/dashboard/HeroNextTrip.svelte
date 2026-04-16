<script>
  /**
   * HeroNextTrip.svelte — Countdown-Kachel: nächster geplanter WS-Trip
   * Zeigt: Countdown in Tagen, Unsplash-Bild zur Destination,
   *        "Zur Reiseplanung"-Button → Trip Hub.
   */
  import { t }        from '$lib/i18n.js';
  import { apiUrl }   from '$lib/stores.js';
  import { api }      from '$lib/api.js';
  import { fmtDate }  from '$lib/components/priceradar/helpers.js';
  import { onMount }  from 'svelte';

  let { trip, ongoToHub } = $props();

  // ── Countdown ────────────────────────────────────────────────────
  const today = new Date().toISOString().slice(0, 10);

  const daysUntil = $derived.by(() => {
    const d = trip?.start_date || trip?.dateStart || trip?.date || '';
    if (!d) return null;
    const ms = new Date(d + 'T00:00:00').getTime() - new Date(today + 'T00:00:00').getTime();
    return Math.ceil(ms / 86400000);
  });

  const countdownLabel = $derived.by(() => {
    const d = daysUntil;
    if (d === null) return '';
    if (d <= 0)  return '🎒 ' + ($t('heroTodayStart') || "Heute geht's los!");
    if (d === 1) return '✈️ ' + ($t('heroTomorrow')   || 'Morgen geht's los!');
    return '✈️ ' + ($t('heroInDays') || 'Noch {n} Tage').replace('{n}', d);
  });

  // ── Unsplash-Bild ─────────────────────────────────────────────────
  let imgUrl   = $state(null);
  let imgError = $state(false);

  async function loadUnsplashImage() {
    if (!$apiUrl || !trip) return;
    const dest = trip.destination || trip.title || trip.name || '';
    if (!dest) return;
    try {
      const res = await api(
        `/api/discovery/trip-image?destination=${encodeURIComponent(dest)}&source=unsplash`
      );
      imgUrl = res?.image_url || null;
    } catch { imgUrl = null; }
  }

  onMount(() => { loadUnsplashImage(); });
  $effect(() => { if (trip && $apiUrl) loadUnsplashImage(); });

  // ── Daten ─────────────────────────────────────────────────────────
  const tripName = $derived(
    trip?.destination || trip?.title || trip?.name || '–'
  );
  const dateStr = $derived.by(() => {
    const s = trip?.start_date || trip?.dateStart || '';
    const e = trip?.end_date   || trip?.dateEnd   || '';
    if (!s) return '';
    return e && e !== s ? `${fmtDate(s)} – ${fmtDate(e)}` : fmtDate(s);
  });

  // Gradient: Dunkelblau-Orange (WS-Markenfarben für "bevorstehend")
  const bgGrad = 'linear-gradient(135deg, #1a3a4a 0%, #c4622d 60%, #b84928 100%)';

  // Urgency-Indikator: < 7 Tage = pulsierend grün
  const isUrgent = $derived((daysUntil ?? 999) <= 7 && (daysUntil ?? 999) >= 0);
</script>

<div class="relative rounded-2xl overflow-hidden flex flex-col" style="min-height:200px;background:{bgGrad}">

  <!-- Unsplash background image -->
  {#if imgUrl && !imgError}
    <img src={imgUrl} alt="" class="absolute inset-0 w-full h-full object-cover"
      style="opacity:.4" onerror={() => { imgError = true; }} />
    <div class="absolute inset-0" style="background:rgba(0,0,0,.4)"></div>
  {/if}

  <!-- Texture -->
  <div class="absolute inset-0 opacity-15 pointer-events-none"
    style="background-image:radial-gradient(circle at 80% 20%, rgba(0,0,0,.3) 0%, transparent 50%)"></div>

  <!-- Content -->
  <div class="relative z-10 flex flex-col justify-between h-full p-4 flex-1">

    <!-- Top -->
    <div>
      <!-- Countdown-Pill -->
      <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold mb-2"
        style="background:rgba(0,0,0,.3);color:rgba(255,255,255,.9);backdrop-filter:blur(6px)">
        {#if isUrgent}
          <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse shrink-0"></span>
        {/if}
        {countdownLabel}
      </div>

      <!-- Trip-Name -->
      <h2 class="text-lg font-bold leading-tight" style="font-family:var(--ws-serif);color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.5)">
        {tripName}
      </h2>

      <!-- Datum -->
      {#if dateStr}
        <p class="text-xs mt-0.5 font-mono" style="color:rgba(255,255,255,.65)">📅 {dateStr}</p>
      {/if}

      <!-- Budget badge wenn vorhanden -->
      {#if trip?.budget}
        <p class="text-xs mt-1 font-mono font-semibold" style="color:rgba(255,245,236,.85)">
          💶 {parseFloat(trip.budget).toFixed(0)} €
        </p>
      {/if}
    </div>

    <!-- Action Button -->
    <div class="mt-3">
      <button
        onclick={ongoToHub}
        class="w-full py-2 rounded-xl text-xs font-semibold transition-all hover:opacity-90 active:scale-[.98]"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec;border:none">
        🗺️ {$t('dashTripHub') || 'Zur Reiseplanung'}
      </button>
    </div>
  </div>

</div>
