<script>
  /**
   * ImmichGallery.svelte — Foto-Collage aus Immich für einen archivierten Trip.
   *
   * Lädt bis zu 12 Fotos aus dem Reisezeitraum via GET /api/ws-trips/{id}/gallery.
   * Zeigt eine masonry-ähnliche Collage + "In Immich öffnen"-Button.
   *
   * Props:
   *   trip  — ws_trip Objekt (braucht id, start_date, end_date, destination)
   */
  import { api }    from '$lib/api.js';
  import { t }      from '$lib/i18n.js';
  import { apiUrl } from '$lib/stores.js';

  let { trip } = $props();

  let photos      = $state([]);
  let loading     = $state(true);
  let error       = $state(null);
  let deepLink    = $state('');
  let immichBase  = $state('');
  let lightbox    = $state(null); // asset_id im Fullscreen

  $effect(() => {
    if (trip?.id && $apiUrl) loadGallery();
  });

  async function loadGallery() {
    loading = true; error = null;
    try {
      const res = await api(`/api/ws-trips/${trip.id}/gallery`);
      photos    = res.photos || [];
      deepLink  = res.deep_link || '';
      immichBase = res.immich_url || '';
    } catch (e) {
      error = e?.message || 'Immich nicht erreichbar';
    }
    loading = false;
  }

  function openLightbox(photo) { lightbox = photo; }
  function closeLightbox() { lightbox = null; }

  // Keyboard ESC closes lightbox
  function onKeydown(e) { if (e.key === 'Escape') closeLightbox(); }
</script>

<svelte:window onkeydown={onKeydown} />

<div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border);background:var(--ws-surface)">

  <!-- Header -->
  <div class="px-5 py-4 flex items-center justify-between border-b" style="border-color:var(--ws-border)">
    <div class="flex items-center gap-2">
      <span class="text-xl">📷</span>
      <div>
        <h3 class="text-sm font-bold" style="color:var(--ws-text)">
          {$t('galleryTitle') || 'Reisefotos'}
        </h3>
        {#if trip.start_date && trip.end_date}
          <p class="text-[10px]" style="color:var(--ws-muted)">
            {trip.start_date} – {trip.end_date}
            {#if photos.length > 0}· {photos.length} {$t('galleryPhotos') || 'Fotos'}{/if}
          </p>
        {/if}
      </div>
    </div>

    {#if deepLink && !loading && !error}
      <a href={deepLink} target="_blank" rel="noopener noreferrer"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-opacity hover:opacity-80"
        style="background:color-mix(in srgb,var(--ws-accent) 12%,var(--ws-surface2));color:var(--ws-accent);border:1px solid color-mix(in srgb,var(--ws-accent) 25%,transparent)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
        {$t('galleryOpenImmich') || 'In Immich öffnen'}
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3"/></svg>
      </a>
    {/if}
  </div>

  <!-- Content -->
  <div class="p-4">

    {#if loading}
      <!-- Skeleton Collage -->
      <div class="grid grid-cols-3 sm:grid-cols-4 gap-1.5">
        {#each [1,2,3,4,5,6,7,8] as _}
          <div class="aspect-square rounded-xl animate-pulse" style="background:var(--ws-surface2)"></div>
        {/each}
      </div>

    {:else if error}
      <div class="py-8 text-center space-y-2">
        <span class="text-3xl">📷</span>
        <p class="text-sm font-semibold" style="color:var(--ws-text)">{$t('galleryNoImmich') || 'Immich nicht verbunden'}</p>
        <p class="text-xs max-w-xs mx-auto" style="color:var(--ws-muted)">
          {$t('galleryNoImmichHint') || 'Verbinde deine Immich-Instanz unter Einstellungen → Mein Bereich → Bridges'}
        </p>
      </div>

    {:else if photos.length === 0}
      <div class="py-8 text-center space-y-2">
        <span class="text-3xl">🏜️</span>
        <p class="text-sm font-semibold" style="color:var(--ws-text)">{$t('galleryEmpty') || 'Keine Fotos gefunden'}</p>
        <p class="text-xs" style="color:var(--ws-muted)">
          {$t('galleryEmptyHint') || 'Im Reisezeitraum wurden keine Fotos in Immich gefunden'}
        </p>
        {#if deepLink}
          <a href={deepLink} target="_blank" rel="noopener noreferrer"
            class="inline-block text-xs underline hover:opacity-70" style="color:var(--ws-accent)">
            {$t('galleryOpenImmich') || 'Immich öffnen'}
          </a>
        {/if}
      </div>

    {:else}
      <!-- Collage Grid — erste Kachel doppelt groß -->
      <div class="grid grid-cols-3 sm:grid-cols-4 gap-1.5">
        {#each photos as photo, i}
          <button
            onclick={() => openLightbox(photo)}
            class="relative rounded-xl overflow-hidden cursor-pointer transition-all hover:opacity-90 hover:scale-[1.02] active:scale-[0.98] {i === 0 ? 'col-span-2 row-span-2 aspect-square' : 'aspect-square'}"
            style="background:var(--ws-surface2)"
            title={photo.taken_at || ''}>
            <img
              src={photo.thumbnail_url}
              alt={photo.city || photo.taken_at || 'Foto'}
              class="absolute inset-0 w-full h-full object-cover"
              loading="lazy"
            />
            {#if photo.city}
              <div class="absolute bottom-0 left-0 right-0 px-1.5 py-0.5 text-[9px] font-medium truncate"
                style="background:rgba(0,0,0,.45);color:rgba(255,255,255,.9)">
                {photo.city}
              </div>
            {/if}
          </button>
        {/each}
      </div>

      <!-- "Alle ansehen" Link wenn viele Fotos -->
      {#if deepLink}
        <div class="mt-3 text-center">
          <a href={deepLink} target="_blank" rel="noopener noreferrer"
            class="text-xs hover:underline" style="color:var(--ws-muted)">
            {$t('galleryViewAll') || 'Alle Fotos in Immich ansehen'} →
          </a>
        </div>
      {/if}
    {/if}

  </div>
</div>

<!-- Lightbox -->
{#if lightbox}
  <div class="fixed inset-0 z-[80] flex items-center justify-center"
    style="background:rgba(0,0,0,.85);backdrop-filter:blur(8px)"
    role="dialog" aria-modal="true"
    onclick={closeLightbox}>
    <div class="relative max-w-3xl w-full mx-4" onclick={(e) => e.stopPropagation()}>
      <img
        src={lightbox.thumbnail_url}
        alt={lightbox.city || lightbox.taken_at}
        class="w-full rounded-2xl shadow-2xl object-contain max-h-[80vh]"
      />
      {#if lightbox.taken_at || lightbox.city}
        <div class="mt-2 text-center text-sm" style="color:rgba(255,255,255,.7)">
          {#if lightbox.city}{lightbox.city}{/if}
          {#if lightbox.city && lightbox.taken_at} · {/if}
          {#if lightbox.taken_at}{lightbox.taken_at}{/if}
        </div>
      {/if}
      <button onclick={closeLightbox}
        class="absolute top-3 right-3 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold hover:opacity-80"
        style="background:rgba(0,0,0,.5);color:white">
        ✕
      </button>
      {#if immichBase && lightbox.asset_id}
        <a href="{immichBase}/photos/{lightbox.asset_id}" target="_blank" rel="noopener noreferrer"
          class="absolute bottom-3 right-3 px-3 py-1.5 rounded-xl text-xs font-semibold hover:opacity-80"
          style="background:rgba(0,0,0,.5);color:rgba(255,255,255,.85)">
          In Immich →
        </a>
      {/if}
    </div>
  </div>
{/if}
