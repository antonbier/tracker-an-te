<script>
  /**
   * HeroPastTrip.svelte — Nostalgie-Kachel: letzter Trip
   * Zeigt: wie lange her, Immich-Bild aus Reisezeitraum, "Zum Trip Hub"-Button.
   * Wenn > 6 Monate → Reiselust-Modus (Orange-Akzent + Motivationstext).
   */
  import { t }       from '$lib/i18n.js';
  import { apiUrl }  from '$lib/stores.js';
  import { api }     from '$lib/api.js';
  import { fmtDate } from '$lib/components/priceradar/helpers.js';
  import { onMount } from 'svelte';

  let { trip, ongoToHub } = $props();

  // ── Zeit-Berechnung ──────────────────────────────────────────────
  const today = new Date().toISOString().slice(0, 10);

  const daysAgo = $derived.by(() => {
    const d = trip?.start_date || trip?.dateStart || trip?.date || '';
    if (!d) return null;
    return Math.floor((new Date(today) - new Date(d)) / 86400000);
  });

  const isOld = $derived((daysAgo ?? 0) > 180); // > 6 Monate

  const timeLabel = $derived.by(() => {
    const d = daysAgo;
    if (d === null) return '';
    if (d === 0)  return $t('heroPastToday')  || 'Gerade zurückgekehrt';
    if (d < 7)    return ($t('heroPastDays')  || 'Vor {n} Tagen').replace('{n}', d);
    if (d < 30)   {
      const w = Math.floor(d / 7);
      return ($t('heroPastWeeks') || 'Vor {n} Woche{s}').replace('{n}', w).replace('{s}', w > 1 ? 'n' : '');
    }
    const m = Math.floor(d / 30);
    return ($t('heroPastMonths') || 'Schon {n} Monat{s} her').replace('{n}', m).replace('{s}', m > 1 ? 'e' : '');
  });

  // ── Immich-Bild ──────────────────────────────────────────────────
  let imgUrl   = $state(null);
  let imgError = $state(false);

  async function loadImmichImage() {
    if (!$apiUrl || !trip) return;
    const startDate = trip.start_date || trip.dateStart || '';
    const endDate   = trip.end_date   || trip.dateEnd   || startDate;
    if (!startDate) return;
    try {
      const res = await api(
        `/api/discovery/trip-image?destination=${encodeURIComponent(
          trip.location_name || trip.name || trip.destination || ''
        )}&date_from=${startDate}&date_to=${endDate}&source=immich`
      );
      imgUrl = res?.image_url || null;
    } catch { imgUrl = null; }
  }

  onMount(() => { loadImmichImage(); });
  $effect(() => { if (trip && $apiUrl) loadImmichImage(); });

  // ── Trip Hub Navigation ──────────────────────────────────────────
  const tripName = $derived(
    trip?.location_name || trip?.name || trip?.destination || trip?.title || '–'
  );
  const dateStr = $derived.by(() => {
    const s = trip?.start_date || trip?.dateStart || '';
    const e = trip?.end_date   || trip?.dateEnd   || '';
    if (!s) return '';
    return e && e !== s ? `${fmtDate(s)} – ${fmtDate(e)}` : fmtDate(s);
  });

  // Accent-Farbe: normal = warmbraun, alt = orange (Reiselust)
  const accentGrad = $derived(
    isOld
      ? 'linear-gradient(135deg, #7c2d12 0%, #c4622d 60%, #ea580c 100%)'
      : 'linear-gradient(135deg, #2d1b0e 0%, #6b3a2a 50%, #2d6a4f 100%)'
  );
</script>

<div class="relative rounded-2xl overflow-hidden flex flex-col" style="min-height:200px;background:{accentGrad}">

  <!-- Immich background image -->
  {#if imgUrl && !imgError}
    <img src={imgUrl} alt="" class="absolute inset-0 w-full h-full object-cover"
      style="opacity:.35" onerror={() => { imgError = true; }} />
    <div class="absolute inset-0" style="background:rgba(0,0,0,.45)"></div>
  {/if}

  <!-- Texture -->
  <div class="absolute inset-0 opacity-15 pointer-events-none"
    style="background-image:radial-gradient(circle at 15% 85%, rgba(255,255,255,.12) 0%, transparent 50%)"></div>

  <!-- Content -->
  <div class="relative z-10 flex flex-col justify-between h-full p-4 flex-1">

    <!-- Top -->
    <div>
      <!-- Reiselust-Badge bei altem Trip -->
      {#if isOld}
        <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold mb-2"
          style="background:rgba(234,88,12,.35);color:#fed7aa;backdrop-filter:blur(6px)">
          🌍 {$t('heroPastLust') || 'Reiselust meldet sich…'}
        </div>
      {:else}
        <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold mb-2"
          style="background:rgba(0,0,0,.25);color:rgba(255,255,255,.8);backdrop-filter:blur(6px)">
          🕐 {timeLabel}
        </div>
      {/if}

      <!-- Trip-Name -->
      <h2 class="text-lg font-bold leading-tight" style="font-family:var(--ws-serif);color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.5)">
        {tripName}
      </h2>

      <!-- Datum -->
      {#if dateStr}
        <p class="text-xs mt-0.5 font-mono" style="color:rgba(255,255,255,.65)">📅 {dateStr}</p>
      {/if}

      <!-- Reiselust-Text bei altem Trip -->
      {#if isOld}
        <p class="text-xs mt-1.5 leading-relaxed" style="color:rgba(255,200,150,.85)">
          {timeLabel} — {$t('heroPastLustHint') || 'Zeit für ein neues Abenteuer?'}
        </p>
      {/if}
    </div>

    <!-- Action Button -->
    <div class="mt-3">
      <button
        onclick={ongoToHub}
        class="w-full py-2 rounded-xl text-xs font-semibold transition-all hover:opacity-90 active:scale-[.98]"
        style="background:rgba(0,0,0,.35);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.2);color:rgba(255,255,255,.9)">
        🗺️ {$t('heroPastGoHub') || 'Zum Trip Hub'}
      </button>
    </div>
  </div>

</div>
