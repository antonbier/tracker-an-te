<script>
  import { api } from '$lib/api.js';
  import { apiUrl } from '$lib/stores.js';

  let {
    open        = $bindable(false),
    suggestion  = null,   // { destination, country, reason, prefill, image_url }
    onplan      = () => {},
  } = $props();

  let detail       = $state(null);
  let loading      = $state(false);
  let activeImg    = $state(0);
  let error        = $state('');

  const PANEL_GRADS = [
    'linear-gradient(135deg,#1a3a4a,#0f2a38)',
    'linear-gradient(135deg,#2d6a4f,#1e4a37)',
    'linear-gradient(135deg,#3b1f5e,#1e1035)',
  ];

  $effect(() => {
    if (open && suggestion) {
      detail    = null;
      activeImg = 0;
      error     = '';
      loadDetail();
    }
  });

  async function loadDetail() {
    if (!$apiUrl) return;
    loading = true;
    try {
      const dest    = encodeURIComponent(suggestion.destination);
      const country = encodeURIComponent(suggestion.prefill?.country || '');
      detail = await api(`/api/discovery/detail?destination=${dest}&country=${country}`);
      activeImg = 0;
    } catch (e) {
      error = e?.message || 'Fehler beim Laden.';
    }
    loading = false;
  }

  function close() { open = false; }

  // All images: detail.images first, fallback to suggestion.image_url
  const allImages = $derived.by(() => {
    if (detail?.images?.length) return detail.images;
    if (suggestion?.image_url) return [{ url: suggestion.image_url, source: suggestion.image_source }];
    return [];
  });
</script>

{#if open && suggestion}
<div class="fixed inset-0 z-[60] flex items-center justify-center"
  style="background:rgba(0,0,0,.6);backdrop-filter:blur(6px)"
  role="dialog" aria-modal="true">

  <div class="fixed inset-0 md:inset-[4vh_8vw] flex flex-col rounded-none md:rounded-2xl overflow-hidden shadow-2xl"
    style="background:var(--ws-surface);border:1px solid var(--ws-border)">

    <!-- Header -->
    <div class="flex items-center gap-3 px-5 py-4 border-b shrink-0"
      style="border-color:var(--ws-border)">
      <span class="text-xl">🌍</span>
      <div class="flex-1 min-w-0">
        <h2 class="font-bold text-base truncate" style="color:var(--ws-text);font-family:var(--ws-serif)">
          {suggestion.destination}
          {#if suggestion.prefill?.country}
            <span class="text-sm font-normal ml-1" style="color:var(--ws-muted)">{suggestion.prefill.country}</span>
          {/if}
        </h2>
        {#if detail?.vibe}
          <p class="text-xs truncate" style="color:var(--ws-accent)">{detail.vibe}</p>
        {/if}
      </div>
      <button onclick={close}
        class="w-8 h-8 rounded-xl flex items-center justify-center text-lg hover:opacity-60"
        style="color:var(--ws-muted)">✕</button>
    </div>

    <!-- Body -->
    <div class="flex-1 overflow-y-auto">

      {#if loading}
        <!-- Skeleton -->
        <div class="animate-pulse space-y-0">
          <div class="w-full" style="height:240px;background:var(--ws-surface2)"></div>
          <div class="p-5 space-y-3">
            <div class="h-4 w-3/4 rounded" style="background:var(--ws-border)"></div>
            <div class="h-3 w-full rounded" style="background:var(--ws-border)"></div>
            <div class="h-3 w-5/6 rounded" style="background:var(--ws-border)"></div>
            <div class="h-3 w-2/3 rounded" style="background:var(--ws-border)"></div>
          </div>
        </div>

      {:else if error}
        <div class="p-6 text-center">
          <div class="text-4xl mb-3">⚠️</div>
          <p class="text-sm" style="color:var(--ws-muted)">{error}</p>
        </div>

      {:else}
        <!-- Photo Gallery -->
        <div class="relative" style="height:260px;background:{PANEL_GRADS[0]}">
          {#if allImages.length > 0}
            <img
              src={allImages[activeImg]?.url}
              alt={suggestion.destination}
              class="absolute inset-0 w-full h-full object-cover"
              onerror={(e) => { e.currentTarget.style.display='none'; }}
            />
            <!-- Dark overlay bottom -->
            <div class="absolute inset-0"
              style="background:linear-gradient(to top,rgba(0,0,0,.5) 0%,transparent 60%)"></div>

            <!-- Thumbnail strip (if >1 image) -->
            {#if allImages.length > 1}
              <div class="absolute bottom-3 left-0 right-0 flex justify-center gap-2 z-10 px-4">
                {#each allImages as img, i}
                  <button onclick={() => activeImg = i}
                    class="relative rounded-lg overflow-hidden transition-all shrink-0"
                    style="width:52px;height:36px;
                      border:2px solid {i === activeImg ? 'var(--ws-accent)' : 'rgba(255,255,255,.3)'}">
                    <img src={img.url} alt="" class="w-full h-full object-cover"
                      onerror={(e) => { e.currentTarget.style.display='none'; }}/>
                  </button>
                {/each}
              </div>
            {/if}

            <!-- Source badge -->
            {#if allImages[activeImg]?.source === 'unsplash'}
              <span class="absolute top-3 right-3 text-[9px] px-1.5 py-0.5 rounded"
                style="background:rgba(0,0,0,.5);color:rgba(255,255,255,.7)">🖼️ Unsplash</span>
            {:else if allImages[activeImg]?.source === 'immich'}
              <span class="absolute top-3 right-3 text-[9px] px-1.5 py-0.5 rounded"
                style="background:rgba(0,0,0,.5);color:rgba(255,255,255,.7)">📸 Immich</span>
            {/if}
          {:else}
            <!-- No image fallback -->
            <div class="absolute inset-0 flex items-center justify-center text-6xl opacity-20">🌍</div>
          {/if}
        </div>

        <!-- Content -->
        <div class="p-5 space-y-5">

          <!-- Description -->
          {#if detail?.description}
            <div>
              <div class="text-xs font-bold uppercase tracking-wider mb-2" style="color:var(--ws-muted)">
                ✨ Warum {suggestion.destination}?
              </div>
              <p class="text-sm leading-relaxed" style="color:var(--ws-text)">
                {detail.description}
              </p>
            </div>
          {:else}
            <p class="text-sm leading-relaxed" style="color:var(--ws-text)">{suggestion.reason}</p>
          {/if}

          <!-- Best Season -->
          {#if detail?.best_season}
            <div class="flex items-center gap-2 text-xs px-3 py-2 rounded-xl"
              style="background:var(--ws-surface2);border:1px solid var(--ws-border)">
              <span>🗓️</span>
              <span style="color:var(--ws-muted)">Beste Reisezeit:</span>
              <span class="font-semibold" style="color:var(--ws-text)">{detail.best_season}</span>
            </div>
          {/if}

          <!-- Things to do -->
          {#if detail?.things_to_do?.length}
            <div>
              <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">
                📋 Things to do
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {#each detail.things_to_do as item, i}
                  <div class="flex items-start gap-2 px-3 py-2.5 rounded-xl"
                    style="background:var(--ws-surface2);border:1px solid var(--ws-border)">
                    <span class="text-xs font-bold shrink-0 w-5 h-5 rounded-full flex items-center justify-center"
                      style="background:var(--ws-accent);color:#fff5ec">{i+1}</span>
                    <span class="text-xs leading-relaxed" style="color:var(--ws-text)">{item}</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

        </div>
      {/if}
    </div>

    <!-- Footer -->
    <div class="px-5 py-4 border-t shrink-0 flex gap-3" style="border-color:var(--ws-border)">
      <button onclick={close}
        class="flex-1 py-2.5 rounded-xl border text-sm font-semibold hover:opacity-70"
        style="border-color:var(--ws-border);color:var(--ws-muted)">
        Schließen
      </button>
      <button onclick={() => { onplan(suggestion.prefill); close(); }}
        class="flex-1 py-2.5 rounded-xl text-sm font-semibold hover:opacity-80"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        🧳 Trip planen
      </button>
    </div>

  </div>
</div>
{/if}
