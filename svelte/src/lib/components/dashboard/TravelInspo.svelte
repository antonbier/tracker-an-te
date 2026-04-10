<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { apiUrl } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';

  let {
    recentDawarich,
    onstartwizard,
    onnavto,
  } = $props();

  // Third card: last Dawarich trip as nostalgia fallback
  const nostalgiaTrip = $derived(recentDawarich[0] ?? null);
  const nostalgiaName = $derived.by(() => {
    if (!nostalgiaTrip) return null;
    return nostalgiaTrip.location_name || nostalgiaTrip.country || null;
  });

  // ── AI Suggestions (cards 2+3) ─────────────────────────────────────────────
  let suggestions   = $state([]);
  let loadingSugg   = $state(false);

  // CSS-Fallback gradients for cards without image
  const FALLBACK_GRADIENTS = [
    'linear-gradient(135deg,#1a3a4a 0%,#0f2a38 100%)',
    'linear-gradient(135deg,#2d6a4f 0%,#1e4a37 100%)',
    'linear-gradient(135deg,#3b1f5e 0%,#1e1035 100%)',
  ];

  onMount(async () => {
    if (!$apiUrl) return;
    loadingSugg = true;
    try {
      const data = await api('/api/discovery/suggestions?count=3');
      suggestions = Array.isArray(data) ? data : [];
    } catch (e) {
      suggestions = [];
    }
    loadingSugg = false;
  });
</script>

<div>
  <h2 class="text-xs font-bold uppercase tracking-widest mb-3" style="color:var(--ws-muted)">
    ✨ Reise-Inspiration
  </h2>

  <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">

    <!-- Card 1: Neuen Trip planen (fix) -->
    <button
      onclick={() => onnavto('mytrips')}
      class="group relative rounded-2xl p-5 text-left overflow-hidden transition-all hover:scale-[1.02] active:scale-[.98]"
      style="background:linear-gradient(135deg,var(--ws-accent) 0%,#b84928 100%);min-height:140px">
      <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
        style="background:rgba(255,255,255,.08)"></div>
      <div class="relative z-10 flex flex-col h-full" style="min-height:100px">
        <div class="text-2xl mb-2">➕</div>
        <div class="font-bold text-sm leading-snug mb-1" style="color:#fff5ec;font-family:var(--ws-serif)">
          Neuen Trip planen
        </div>
        <div class="text-xs mt-auto" style="color:rgba(255,245,236,.65)">
          Ziel, Datum & Budget festlegen →
        </div>
      </div>
    </button>

    <!-- Cards 2+3: AI Suggestions or Skeleton / Fallback -->
    {#each [0, 1] as cardIdx}
      {@const sugg = suggestions[cardIdx]}
      {@const fallbackGrad = FALLBACK_GRADIENTS[cardIdx + 1]}

      {#if loadingSugg}
        <!-- Skeleton -->
        <div class="rounded-2xl overflow-hidden animate-pulse"
          style="background:var(--ws-surface2);min-height:140px">
          <div class="h-full p-5 flex flex-col gap-3">
            <div class="w-12 h-4 rounded" style="background:var(--ws-border)"></div>
            <div class="w-3/4 h-4 rounded" style="background:var(--ws-border)"></div>
            <div class="w-1/2 h-3 rounded mt-auto" style="background:var(--ws-border)"></div>
          </div>
        </div>

      {:else if sugg}
        <!-- AI Suggestion card -->
        <button
          onclick={() => onstartwizard(sugg.prefill)}
          class="group relative rounded-2xl text-left overflow-hidden transition-all hover:scale-[1.02] active:scale-[.98]"
          style="min-height:140px;background:{fallbackGrad}">

          <!-- Background image if available -->
          {#if sugg.image_url}
            <img
              src={sugg.image_url}
              alt={sugg.destination}
              class="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              style="opacity:.55"
              onerror={(e) => { e.currentTarget.style.display='none'; }}
            />
          {/if}

          <!-- Dark overlay for readability -->
          <div class="absolute inset-0"
            style="background:linear-gradient(to top,rgba(0,0,0,.75) 0%,rgba(0,0,0,.2) 60%,transparent 100%)"></div>

          <!-- Hover shimmer -->
          <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
            style="background:rgba(255,255,255,.06)"></div>

          <!-- Content -->
          <div class="relative z-10 flex flex-col h-full p-5" style="min-height:140px">
            <!-- AI badge -->
            <div class="flex justify-between items-start mb-auto">
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full"
                style="background:rgba(255,255,255,.18);color:rgba(255,255,255,.85)">
                ✨ KI-Vorschlag
              </span>
              {#if sugg.image_source === 'immich'}
                <span class="text-[9px] px-1.5 py-0.5 rounded-full"
                  style="background:rgba(0,0,0,.35);color:rgba(255,255,255,.6)">📸 Immich</span>
              {:else if sugg.image_source === 'unsplash'}
                <span class="text-[9px] px-1.5 py-0.5 rounded-full"
                  style="background:rgba(0,0,0,.35);color:rgba(255,255,255,.6)">🖼️ Unsplash</span>
              {/if}
            </div>

            <div class="mt-auto">
              <div class="font-bold text-sm leading-snug mb-1 truncate"
                style="color:#fff;font-family:var(--ws-serif);text-shadow:0 1px 6px rgba(0,0,0,.6)">
                {sugg.destination}
              </div>
              <div class="text-xs leading-relaxed line-clamp-2"
                style="color:rgba(255,255,255,.75);text-shadow:0 1px 4px rgba(0,0,0,.5)">
                {sugg.reason}
              </div>
              <div class="text-xs mt-2 font-semibold" style="color:rgba(255,255,255,.6)">
                WanderWizzard starten →
              </div>
            </div>
          </div>
        </button>

      {:else if cardIdx === 0}
        <!-- Fallback card 2: PriceRadar -->
        <button
          onclick={() => onnavto('priceradar')}
          class="group relative rounded-2xl p-5 text-left overflow-hidden transition-all hover:scale-[1.02] active:scale-[.98]"
          style="background:linear-gradient(135deg,#1a3a4a 0%,#0f2a38 100%);min-height:140px">
          <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
            style="background:rgba(255,255,255,.06)"></div>
          <div class="relative z-10 flex flex-col h-full" style="min-height:100px">
            <div class="text-2xl mb-2">📡</div>
            <div class="font-bold text-sm leading-snug mb-1" style="color:#fff;font-family:var(--ws-serif)">
              Preise beobachten
            </div>
            <div class="text-xs mt-auto" style="color:rgba(255,255,255,.45)">
              PriceRadar öffnen →
            </div>
          </div>
          <div class="absolute top-4 right-4 w-2 h-2 rounded-full animate-pulse" style="background:var(--ws-green)"></div>
        </button>

      {:else if nostalgiaName}
        <!-- Fallback card 3: Nostalgie -->
        <button
          onclick={() => onstartwizard({ destination: nostalgiaName })}
          class="group relative rounded-2xl p-5 text-left overflow-hidden transition-all hover:scale-[1.02] active:scale-[.98]"
          style="background:linear-gradient(135deg,#2d6a4f 0%,#1e4a37 100%);min-height:140px">
          <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
            style="background:rgba(255,255,255,.06)"></div>
          <div class="relative z-10 flex flex-col h-full" style="min-height:100px">
            <div class="text-2xl mb-2">🔁</div>
            <div class="font-bold text-sm leading-snug mb-1" style="color:#ecfdf5;font-family:var(--ws-serif)">
              Wieder nach {nostalgiaName}?
            </div>
            <div class="text-xs mt-auto" style="color:rgba(236,253,245,.5)">
              WanderWizzard starten →
            </div>
          </div>
          <span class="absolute top-4 right-4 text-[10px] font-bold px-2 py-0.5 rounded-full"
            style="background:rgba(255,255,255,.15);color:rgba(255,255,255,.7)">Nostalgie</span>
        </button>

      {:else}
        <!-- Fallback card 3: Discover -->
        <button
          onclick={() => onnavto('discover')}
          class="group relative rounded-2xl p-5 text-left overflow-hidden transition-all hover:scale-[1.02] active:scale-[.98] border-2 border-dashed"
          style="background:var(--ws-surface);border-color:var(--ws-border);min-height:140px">
          <div class="relative z-10 flex flex-col h-full" style="min-height:100px">
            <div class="text-2xl mb-2">🌍</div>
            <div class="font-bold text-sm leading-snug mb-1" style="color:var(--ws-text);font-family:var(--ws-serif)">
              Neue Ziele entdecken
            </div>
            <div class="text-xs mt-auto" style="color:var(--ws-muted)">
              Discover öffnen →
            </div>
          </div>
        </button>
      {/if}
    {/each}

  </div>

  <!-- ── KI Discovery Panel ── -->
  {#if loadingSugg || suggestions.length > 0}
    <div class="mt-5">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-xs font-bold uppercase tracking-widest" style="color:var(--ws-muted)">
          🤖 KI-Reisevorschläge
        </h2>
        {#if !loadingSugg && suggestions.length > 0}
          <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold"
            style="background:rgba(196,98,45,.12);color:var(--ws-accent)">
            ✨ personalisiert
          </span>
        {/if}
      </div>

      {#if loadingSugg}
        <!-- Skeleton rows -->
        <div class="space-y-3">
          {#each [1,2,3] as _}
            <div class="rounded-2xl overflow-hidden animate-pulse flex gap-4 p-4"
              style="background:var(--ws-surface2);min-height:96px">
              <div class="w-24 h-full rounded-xl shrink-0" style="background:var(--ws-border);min-height:64px"></div>
              <div class="flex-1 flex flex-col gap-2 justify-center">
                <div class="w-1/3 h-4 rounded" style="background:var(--ws-border)"></div>
                <div class="w-3/4 h-3 rounded" style="background:var(--ws-border)"></div>
                <div class="w-1/2 h-3 rounded" style="background:var(--ws-border)"></div>
              </div>
            </div>
          {/each}
        </div>

      {:else}
        <div class="space-y-3">
          {#each suggestions as sugg, i}
            {@const panelGrads = [
              'linear-gradient(135deg,#1a3a4a,#0f2a38)',
              'linear-gradient(135deg,#2d6a4f,#1e4a37)',
              'linear-gradient(135deg,#3b1f5e,#1e1035)',
            ]}
            <button
              onclick={() => onstartwizard(sugg.prefill)}
              class="group w-full rounded-2xl overflow-hidden flex text-left transition-all hover:scale-[1.01] active:scale-[.99] hover:shadow-lg"
              style="background:var(--ws-surface2);border:1px solid var(--ws-border)">

              <!-- Thumbnail -->
              <div class="relative w-28 sm:w-36 shrink-0 overflow-hidden"
                style="background:{panelGrads[i % 3]};min-height:96px">
                {#if sugg.image_url}
                  <img
                    src={sugg.image_url}
                    alt={sugg.destination}
                    class="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                    onerror={(e) => { e.currentTarget.style.display='none'; }}
                  />
                {:else}
                  <!-- CSS gradient placeholder with destination initial -->
                  <div class="absolute inset-0 flex items-center justify-center text-3xl opacity-40">🌍</div>
                {/if}
                <!-- Image source badge -->
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
                    <span class="font-bold text-sm leading-snug truncate"
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

                <div class="flex items-center justify-between mt-3 gap-2">
                  <!-- Trip type chips from prefill -->
                  <div class="flex gap-1 flex-wrap">
                    {#if sugg.prefill?.tripType}
                      {@const icons = { flight: '✈️', hotel: '🏨', camping: '⛺', car: '🚗' }}
                      <span class="text-[10px] px-2 py-0.5 rounded-full"
                        style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)">
                        {icons[sugg.prefill.tripType] || '🗺️'} {sugg.prefill.tripType}
                      </span>
                    {/if}
                  </div>
                  <span class="text-xs font-semibold shrink-0 transition-colors group-hover:opacity-80"
                    style="color:var(--ws-accent)">
                    Planen →
                  </span>
                </div>
              </div>
            </button>
          {/each}
        </div>
      {/if}
    </div>
  {/if}

</div>
