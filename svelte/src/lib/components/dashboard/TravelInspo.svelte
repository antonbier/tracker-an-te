<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { apiUrl, settingsOpen } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';
  import DestinationDetail from '$lib/components/dashboard/DestinationDetail.svelte';

  let {
    recentDawarich,
    onstartwizard,
    onnavto,
  } = $props();

  // ── Nostalgie: random archived trip ──────────────────────────────────────
  let archivedTrips = $state([]);
  let nostalgiaIndex = $state(0);

  // Load archived (erlebt) ws-trips for Nostalgie tile
  async function loadArchivedTrips() {
    if (!$apiUrl) return;
    try {
      const trips = await api('/api/ws-trips');
      archivedTrips = (trips || []).filter(t => t.status === 'archived' || t.status === 'experienced');
    } catch {}
    // pick random start index
    if (archivedTrips.length > 0) {
      nostalgiaIndex = Math.floor(Math.random() * archivedTrips.length);
    }
  }

  function refreshNostalgia() {
    if (archivedTrips.length > 1) {
      nostalgiaIndex = (nostalgiaIndex + Math.floor(Math.random() * (archivedTrips.length - 1)) + 1) % archivedTrips.length;
    } else if (archivedTrips.length === 1) {
      nostalgiaIndex = 0;
    }
  }

  const nostalgiaTrip = $derived.by(() => {
    if (archivedTrips.length > 0) return archivedTrips[nostalgiaIndex] ?? null;
    // fallback: first Dawarich trip
    return recentDawarich[0] ?? null;
  });

  const nostalgiaName = $derived.by(() => {
    if (!nostalgiaTrip) return null;
    return nostalgiaTrip.destination || nostalgiaTrip.location_name || nostalgiaTrip.country || null;
  });

  // AI Suggestions
  let suggestions  = $state([]);
  let loadingSugg  = $state(false);
  let apiError        = $state('');
  let detailOpen      = $state(false);
  let detailSuggestion = $state(null);

  const PANEL_GRADS = [
    'linear-gradient(135deg,#1a3a4a,#0f2a38)',
    'linear-gradient(135deg,#2d6a4f,#1e4a37)',
    'linear-gradient(135deg,#3b1f5e,#1e1035)',
  ];

  onMount(async () => {
    await loadArchivedTrips();
    if (!$apiUrl) return;
    loadingSugg = true;
    apiError = '';
    try {
      const data = await api('/api/discovery/suggestions?count=3');
      suggestions = Array.isArray(data) ? data : [];
      if (suggestions.length === 0) apiError = $t('inspoNoLlmKey');
    } catch (e) {
      suggestions = [];
      apiError = e?.message || $t('inspoLoadError');
    }
    loadingSugg = false;
  });

  async function refreshSuggestions() {
    if (!$apiUrl || loadingSugg) return;
    loadingSugg = true;
    apiError = '';
    try {
      const data = await api('/api/discovery/refresh?count=3', { method: 'POST' });
      suggestions = Array.isArray(data) ? data : [];
      if (suggestions.length === 0) apiError = $t('inspoNoNewSuggestions');
    } catch (e) {
      apiError = e?.message || $t('inspoLoadError');
    }
    loadingSugg = false;
  }
</script>

<div class="space-y-5">

  <!-- ── Quick Action Cards ── -->
  <div>
    <h2 class="text-xs font-bold uppercase tracking-widest mb-3" style="color:var(--ws-muted)">
      ✨ {$t('inspoTitle')}
    </h2>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">

      <!-- Card 1: Neuen Trip planen — clicks open WanderWizzard directly -->
      <button onclick={() => onstartwizard({})}
        class="group relative rounded-2xl p-5 text-left overflow-hidden transition-all hover:scale-[1.02] active:scale-[.98]"
        style="background:linear-gradient(135deg,var(--ws-accent) 0%,#b84928 100%);min-height:140px">
        <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
          style="background:rgba(255,255,255,.08)"></div>
        <div class="relative z-10 flex flex-col h-full" style="min-height:100px">
          <div class="text-2xl mb-2">➕</div>
          <div class="font-bold text-sm leading-snug mb-1" style="color:#fff5ec;font-family:var(--ws-serif)">
            {$t('inspoNewTrip')}
          </div>
          <div class="text-xs mt-auto" style="color:rgba(255,245,236,.65)">
            {$t('inspoNewTripSub')}
          </div>
        </div>
      </button>

      <!-- Card 2: PriceRadar -->
      <button onclick={() => onnavto('priceradar')}
        class="group relative rounded-2xl p-5 text-left overflow-hidden transition-all hover:scale-[1.02] active:scale-[.98]"
        style="background:linear-gradient(135deg,#1a3a4a 0%,#0f2a38 100%);min-height:140px">
        <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
          style="background:rgba(255,255,255,.06)"></div>
        <div class="relative z-10 flex flex-col h-full" style="min-height:100px">
          <div class="text-2xl mb-2">📡</div>
          <div class="font-bold text-sm leading-snug mb-1" style="color:#fff;font-family:var(--ws-serif)">
            {$t('inspoPriceWatch')}
          </div>
          <div class="text-xs mt-auto" style="color:rgba(255,255,255,.45)">{$t('inspoPriceWatchSub')}</div>
        </div>
        <div class="absolute top-4 right-4 w-2 h-2 rounded-full animate-pulse" style="background:var(--ws-green)"></div>
      </button>

      <!-- Card 3: Nostalgie (archived trips) or Discover -->
      {#if nostalgiaName}
        <div class="group relative rounded-2xl text-left transition-all hover:scale-[1.02] active:scale-[.98]"
          style="background:linear-gradient(135deg,#2d6a4f 0%,#1e4a37 100%);min-height:140px">
          <div class="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
            style="background:rgba(255,255,255,.06)"></div>

          <!-- Content-Button: volle Fläche, Padding rechts oben für Refresh-Button freilassen -->
          <button
            class="relative w-full h-full text-left p-5 flex flex-col"
            style="min-height:140px"
            onclick={() => onstartwizard({ destination: nostalgiaName })}>
            <div class="text-2xl mb-2">🔁</div>
            <!-- Titel mit rechts genug Platz für den Refresh-Button -->
            <div class="font-bold text-sm leading-snug mb-1 pr-9" style="color:#ecfdf5;font-family:var(--ws-serif)">
              {$t('inspoNostalgiaTitle')} {nostalgiaName}?
            </div>
            <div class="text-xs mt-auto" style="color:rgba(236,253,245,.5)">{$t('inspoNostalgiaSub')}</div>
          </button>

          <!-- Refresh-Button: nach Content-Button im DOM → höherer paint-order → liegt automatisch oben -->
          <button
            onclick={(e) => { e.stopPropagation(); refreshNostalgia(); }}
            class="absolute top-3 right-3 w-7 h-7 flex items-center justify-center rounded-full transition-all hover:opacity-80 active:scale-[.95]"
            style="background:rgba(255,255,255,.18);color:rgba(255,255,255,.9);font-size:13px"
            title={$t('inspoNostalgiaRefresh')}>
            🔄
          </button>

          <span class="absolute bottom-3 left-5 text-[10px] font-bold px-2 py-0.5 rounded-full pointer-events-none"
            style="background:rgba(255,255,255,.15);color:rgba(255,255,255,.7)">{$t('inspoNostalgiaLabel')}</span>
        </div>
      {:else}
        <button onclick={() => onnavto('discover')}
          class="group relative rounded-2xl p-5 text-left overflow-hidden transition-all hover:scale-[1.02] active:scale-[.98] border-2 border-dashed"
          style="background:var(--ws-surface);border-color:var(--ws-border);min-height:140px">
          <div class="relative z-10 flex flex-col h-full" style="min-height:100px">
            <div class="text-2xl mb-2">🌍</div>
            <div class="font-bold text-sm leading-snug mb-1" style="color:var(--ws-text);font-family:var(--ws-serif)">
              {$t('inspoDiscover')}
            </div>
            <div class="text-xs mt-auto" style="color:var(--ws-muted)">{$t('inspoDiscoverSub')}</div>
          </div>
        </button>
      {/if}

    </div>
  </div>

  <!-- ── KI Discovery Panel (always rendered) ── -->
  <div>
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-xs font-bold uppercase tracking-widest" style="color:var(--ws-muted)">
        🤖 {$t('inspoAiTitle')}
      </h2>
      <div class="flex items-center gap-2">
        {#if !loadingSugg && suggestions.length > 0}
          <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold"
            style="background:rgba(196,98,45,.12);color:var(--ws-accent)">✨ {$t('inspoPersonalized')}</span>
        {/if}
        <button onclick={refreshSuggestions} disabled={loadingSugg}
          class="text-[10px] px-2 py-1 rounded-lg border transition-opacity hover:opacity-70 disabled:opacity-30 flex items-center gap-1"
          style="border-color:var(--ws-border);color:var(--ws-muted);background:var(--ws-surface2)">
          {loadingSugg ? '⏳' : '🔄'} {$t('inspoNewSuggestions')}
        </button>
      </div>
    </div>

    {#if loadingSugg}
      <!-- Skeleton -->
      <div class="space-y-3">
        {#each [1,2,3] as _}
          <div class="rounded-2xl animate-pulse flex gap-0 overflow-hidden"
            style="background:var(--ws-surface2);border:1px solid var(--ws-border);min-height:96px">
            <div class="w-28 shrink-0" style="background:var(--ws-border)"></div>
            <div class="flex-1 p-4 flex flex-col gap-2 justify-center">
              <div class="w-1/3 h-4 rounded" style="background:var(--ws-border)"></div>
              <div class="w-3/4 h-3 rounded" style="background:var(--ws-border)"></div>
              <div class="w-1/2 h-3 rounded" style="background:var(--ws-border)"></div>
            </div>
          </div>
        {/each}
      </div>

    {:else if suggestions.length > 0}
      <!-- Suggestion rows -->
      <div class="space-y-3">
        {#each suggestions as sugg, i}
          <button
            onclick={() => { detailSuggestion = sugg; detailOpen = true; }}
            class="group w-full rounded-2xl overflow-hidden flex text-left transition-all hover:scale-[1.005] active:scale-[.995]"
            style="background:var(--ws-surface2);border:1px solid var(--ws-border)">

            <!-- Thumbnail -->
            <div class="relative w-28 sm:w-36 shrink-0 overflow-hidden"
              style="background:{PANEL_GRADS[i % 3]};min-height:96px">
              {#if sugg.image_url}
                <img src={sugg.image_url} alt={sugg.destination}
                  class="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  onerror={(e) => { e.currentTarget.style.display='none'; }}/>
              {:else}
                <div class="absolute inset-0 flex items-center justify-center text-4xl opacity-30">🌍</div>
              {/if}
              {#if sugg.image_source === 'immich'}
                <span class="absolute bottom-1 left-1 text-[8px] px-1 py-0.5 rounded"
                  style="background:rgba(0,0,0,.6);color:rgba(255,255,255,.7)">📸</span>
              {:else if sugg.image_source === 'unsplash'}
                <span class="absolute bottom-1 left-1 text-[8px] px-1 py-0.5 rounded"
                  style="background:rgba(0,0,0,.6);color:rgba(255,255,255,.7)">🖼️</span>
              {/if}
            </div>

            <!-- Content -->
            <div class="flex-1 p-4 flex flex-col justify-between min-w-0">
              <div>
                <div class="flex items-start justify-between gap-2 mb-1">
                  <span class="font-bold text-sm leading-snug"
                    style="color:var(--ws-text);font-family:var(--ws-serif)">
                    {sugg.destination}
                  </span>
                  <span class="text-[10px] shrink-0 px-1.5 py-0.5 rounded-full font-semibold"
                    style="background:rgba(196,98,45,.1);color:var(--ws-accent)">✨ KI</span>
                </div>
                <p class="text-xs leading-relaxed line-clamp-2" style="color:var(--ws-muted)">
                  {sugg.reason}
                </p>
              </div>
              <div class="flex items-center justify-between mt-3">
                {#if sugg.prefill?.tripType}
                  {@const icons = { flight: '✈️', hotel: '🏨', camping: '⛺', car: '🚗' }}
                  <span class="text-[10px] px-2 py-0.5 rounded-full"
                    style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)">
                    {icons[sugg.prefill.tripType] || '🗺️'} {sugg.prefill.tripType}
                  </span>
                {:else}
                  <span></span>
                {/if}
                <span class="text-xs font-semibold" style="color:var(--ws-accent)">{$t('inspoPlan')} →</span>
              </div>
            </div>
          </button>
        {/each}
      </div>

    {:else}
      <!-- No LLM configured — info box -->
      <div class="rounded-2xl p-4 flex items-start gap-3"
        style="background:var(--ws-surface2);border:1px solid var(--ws-border)">
        <span class="text-2xl shrink-0">🤖</span>
        <div>
          <div class="text-sm font-semibold mb-1" style="color:var(--ws-text)">
            {$t('inspoAiUnavailableTitle')}
          </div>
          <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">
            {apiError || $t('inspoAiUnavailableDesc')}
          </p>
          <button onclick={() => settingsOpen.set(true)}
            class="mt-2 text-xs font-semibold px-3 py-1.5 rounded-lg transition-opacity hover:opacity-80"
            style="background:var(--ws-accent);color:#fff5ec">
            ⚙️ {$t('inspoOpenSettings')}
          </button>
        </div>
      </div>
    {/if}
  </div>


<DestinationDetail
  bind:open={detailOpen}
  suggestion={detailSuggestion}
  onplan={(prefill) => onstartwizard(prefill)}
/>

</div>
