<script>
  /**
   * HeroPastTrip.svelte — Nostalgie-Kachel
   * - Bekommt archivedTrips[] statt eines einzelnen trips
   * - Wählt random einen Trip aus dem Archiv
   * - Refresh-Button wechselt zu einem anderen Trip
   * - Immich-Bild aus Reisezeitraum (mit sessionStorage-Cache)
   * - Reiselust-Modus wenn > 6 Monate her
   */
  import { t }       from '$lib/i18n.js';
  import { apiUrl }  from '$lib/stores.js';
  import { api }     from '$lib/api.js';
  import { fmtDate } from '$lib/components/priceradar/helpers.js';
  import { onMount } from 'svelte';

  let { archivedTrips = [], ongoToHub } = $props();

  // ── Random Trip aus Archiv ────────────────────────────────────────
  let currentIndex = $state(0);

  // Beim ersten Render: zufälligen Index wählen
  onMount(() => {
    if (archivedTrips.length > 1) {
      currentIndex = Math.floor(Math.random() * archivedTrips.length);
    }
  });

  const trip = $derived(archivedTrips[currentIndex] ?? null);

  function nextTrip() {
    if (archivedTrips.length <= 1) return;
    currentIndex = (currentIndex + 1) % archivedTrips.length;
  }

  // ── Zeit-Berechnung ──────────────────────────────────────────────
  const today = new Date().toISOString().slice(0, 10);

  const daysAgo = $derived.by(() => {
    // Block 8 Fix: end_date für vergangene Reisen nutzen (nicht start_date).
    // start_date → "Heute geht's los" Bug bei archivierten Trips.
    const endRaw   = trip?.end_date   || trip?.dateEnd   || '';
    const startRaw = trip?.start_date || trip?.dateStart || trip?.date || '';
    const d = endRaw || startRaw;  // end_date bevorzugen
    if (!d) return null;
    const tripDate = new Date(d.slice(0, 10) + 'T00:00:00');
    const todayDate = new Date(today + 'T00:00:00');
    return Math.floor((todayDate - tripDate) / 86400000);
  });

  const isOld = $derived((daysAgo ?? 0) > 180);

  const timeLabel = $derived.by(() => {
    const d = daysAgo;
    if (d === null) return '';
    if (d === 0)  return $t('heroPastToday')  || 'Gerade zurückgekehrt';
    if (d < 7)    return ($t('heroPastDays')  || 'Vor {n} Tagen').replace('{n}', String(d));
    if (d < 30) {
      const w = Math.floor(d / 7);
      return ($t('heroPastWeeks') || 'Vor {n} Woche{s}')
        .replace('{n}', String(w)).replace('{s}', w > 1 ? 'n' : '');
    }
    const m = Math.floor(d / 30);
    return ($t('heroPastMonths') || 'Schon {n} Monat{s} her')
      .replace('{n}', String(m)).replace('{s}', m > 1 ? 'e' : '');
  });

  // ── Immich-Bild mit sessionStorage-Cache ─────────────────────────
  let imgUrl   = $state(null);
  let imgError = $state(false);
  let imgLoading = $state(false);

  function cacheKey(t) {
    if (!t) return null;
    const dest = t.location_name || t.name || t.destination || t.title || '';
    const from = t.start_date || t.dateStart || '';
    return dest && from ? `ws-img-past-${dest}-${from}`.replace(/\s+/g, '_') : null;
  }

  async function loadImage() {
    if (!$apiUrl || !trip) return;
    imgError = false;

    // 1. Check cache first
    const key = cacheKey(trip);
    if (key) {
      const cached = sessionStorage.getItem(key);
      if (cached) { imgUrl = cached === 'null' ? null : cached; return; }
    }

    imgLoading = true;
    const dest      = trip.location_name || trip.name || trip.destination || trip.title || '';
    const startDate = trip.start_date || trip.dateStart || '';
    const endDate   = trip.end_date   || trip.dateEnd   || startDate;

    try {
      let imgEndpoint = `/api/discovery/trip-image?destination=${encodeURIComponent(dest)}`;
      if (startDate) imgEndpoint += `&date_from=${encodeURIComponent(startDate)}`;
      if (endDate)   imgEndpoint += `&date_to=${encodeURIComponent(endDate)}`;
      const res = await api(imgEndpoint);
      const url = res?.image_url || null;
      imgUrl = url;
      if (key) sessionStorage.setItem(key, url ?? 'null');
    } catch {
      imgUrl = null;
      if (key) sessionStorage.setItem(key, 'null');
    }
    imgLoading = false;
  }

  // Reload wenn trip wechselt
  $effect(() => {
    if (trip && $apiUrl) { imgUrl = null; imgError = false; loadImage(); }
  });

  // ── Abgeleitete Anzeige-Werte ────────────────────────────────────
  const tripName = $derived(
    trip?.location_name || trip?.name || trip?.destination || trip?.title || '–'
  );
  const dateStr = $derived.by(() => {
    const s = trip?.start_date || trip?.dateStart || '';
    const e = trip?.end_date   || trip?.dateEnd   || '';
    if (!s) return '';
    return e && e !== s ? `${fmtDate(s)} – ${fmtDate(e)}` : fmtDate(s);
  });
  const accentGrad = $derived(
    isOld
      ? 'linear-gradient(135deg, #7c2d12 0%, #c4622d 60%, #ea580c 100%)'
      : 'linear-gradient(135deg, #2d1b0e 0%, #6b3a2a 50%, #2d6a4f 100%)'
  );
</script>

{#if trip}
<div class="relative rounded-2xl overflow-hidden flex flex-col" style="min-height:200px;background:{accentGrad}">

  <!-- Immich background image -->
  {#if imgUrl && !imgError}
    <img src={imgUrl} alt=""
      class="absolute inset-0 w-full h-full object-cover"
      style="opacity:.35"
      onerror={() => { imgError = true; }} />
    <div class="absolute inset-0" style="background:rgba(0,0,0,.45)"></div>
  {/if}

  <!-- Texture -->
  <div class="absolute inset-0 opacity-15 pointer-events-none"
    style="background-image:radial-gradient(circle at 15% 85%, rgba(255,255,255,.12) 0%, transparent 50%)"></div>

  <!-- Content -->
  <div class="relative z-10 flex flex-col justify-between h-full p-4 flex-1">

    <!-- Top row: Badge + Refresh-Button nebeneinander -->
    <div>
      <div class="flex items-start justify-between gap-2 mb-2">
        <!-- Reiselust-Badge / Zeit-Badge -->
        {#if isOld}
          <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold"
            style="background:rgba(234,88,12,.35);color:#fed7aa;backdrop-filter:blur(6px)">
            🌍 {$t('heroPastLust') || 'Reiselust meldet sich…'}
          </div>
        {:else}
          <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold"
            style="background:rgba(0,0,0,.25);color:rgba(255,255,255,.8);backdrop-filter:blur(6px)">
            🕐 {timeLabel}
          </div>
        {/if}
        <!-- Refresh-Button: Teil des normalen Flows, kein absolute -->
        {#if archivedTrips.length > 1}
          <button
            onclick={nextTrip}
            title="Anderen Trip anzeigen"
            class="shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-all hover:opacity-80 active:scale-90"
            style="background:rgba(0,0,0,.35);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.2);color:rgba(255,255,255,.85);font-size:13px">
            🔀
          </button>
        {/if}
      </div>

      <!-- Trip-Name -->
      <h2 class="text-lg font-bold leading-tight"
        style="font-family:var(--ws-serif);color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.5)">
        {tripName}
      </h2>

      <!-- Datum -->
      {#if dateStr}
        <p class="text-xs mt-0.5 font-mono" style="color:rgba(255,255,255,.65)">📅 {dateStr}</p>
      {/if}

      <!-- Reiselust-Hint -->
      {#if isOld}
        <p class="text-xs mt-1.5 leading-relaxed" style="color:rgba(255,200,150,.85)">
          {timeLabel} — {$t('heroPastLustHint') || 'Zeit für ein neues Abenteuer?'}
        </p>
      {/if}

      <!-- Archiv-Counter -->
      {#if archivedTrips.length > 1}
        <p class="text-[10px] mt-1" style="color:rgba(255,255,255,.35)">
          {currentIndex + 1}/{archivedTrips.length}
        </p>
      {/if}
    </div>  <!-- end top row -->

    <!-- Action Button -->
    <div class="mt-3">
      <button
        onclick={() => ongoToHub(trip)}
        class="w-full py-2 rounded-xl text-xs font-semibold transition-all hover:opacity-90 active:scale-[.98]"
        style="background:rgba(0,0,0,.35);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.2);color:rgba(255,255,255,.9)">
        🗺️ {$t('heroPastGoHub') || 'Zum Trip Hub'}
      </button>
    </div>
  </div>

</div>
{/if}
