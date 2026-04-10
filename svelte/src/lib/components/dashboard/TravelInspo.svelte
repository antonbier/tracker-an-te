<script>
  import { t } from '$lib/i18n.js';

  let {
    recentDawarich,
    onstartwizard,
    onnavto,
  } = $props();

  // Third card: last Dawarich trip as nostalgia suggestion
  const nostalgiaTrip = $derived(recentDawarich[0] ?? null);
  const nostalgiaName = $derived.by(() => {
    if (!nostalgiaTrip) return null;
    return nostalgiaTrip.location_name || nostalgiaTrip.country || null;
  });
</script>

<div>
  <h2 class="text-xs font-bold uppercase tracking-widest mb-3" style="color:var(--ws-muted)">
    ✨ Reise-Inspiration
  </h2>

  <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">

    <!-- Card 1: Neuen Trip planen -->
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

    <!-- Card 2: PriceRadar / Preise beobachten -->
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
      <!-- Accent dot -->
      <div class="absolute top-4 right-4 w-2 h-2 rounded-full animate-pulse" style="background:var(--ws-green)"></div>
    </button>

    <!-- Card 3: Nostalgie / WanderWizzard (dynamic) -->
    {#if nostalgiaName}
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
      <!-- Fallback: Discover -->
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

  </div>
</div>
