<script>
  import { apiUrl } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';

  let {
    journalYear,
    journalLoad,
    selectedYear,
    editingCost,
    costDraft,
    card,
    ondelete,
    onsavecost,
    oneditcost,
    oncanceledit,
  } = $props();
</script>

<div class="flex items-center justify-between mb-3">
  <h3 class="text-sm font-semibold">
    Reisen {selectedYear}
    <span class="ml-1 text-xs font-normal" style="color:var(--ws-muted)">({journalYear.length})</span>
  </h3>
</div>

{#if !$apiUrl}
  <div class="{card} text-center py-12">
    <div class="text-4xl mb-3">🔌</div>
    <p class="text-sm" style="color:var(--ws-muted)">{$t('journalNoBackend')}</p>
  </div>
{:else if journalLoad}
  <div class="space-y-3">
    {#each [1,2,3] as _}
      <div class="h-20 rounded-xl animate-pulse"></div>
    {/each}
  </div>
{:else if journalYear.length === 0}
  <div class="{card} text-center py-12">
    <div class="text-4xl mb-3">🗺️</div>
    <p class="text-sm font-semibold mb-1">Keine Reisen in {selectedYear}</p>
    <p class="text-xs mb-4" style="color:var(--ws-muted)">Links manuell erfassen oder Dawarich synchronisieren.</p>
  </div>
{:else}
  <div class="relative pl-6">
    <div class="absolute left-2.5 top-2 bottom-2 w-0.5 rounded-full"></div>
    {#each journalYear as trip}
      {@const loc      = trip.location_name || trip.name || '–'}
      {@const mapsUrl  = trip.lat&&trip.lon ? `https://www.google.com/maps?q=${trip.lat},${trip.lon}` : null}
      {@const isManual = trip.source==='manual'}
      {@const displayCost = trip.cost ?? trip.auto_cost}
      {@const isAutoCost  = trip.cost == null && trip.auto_cost != null}
      <div class="relative pb-4">
        <div class="absolute -left-6 top-4 w-4 h-4 rounded-full border-2 shadow-sm z-10"
          style="border-color:var(--ws-surface);background:{isManual?'#6366f1':'linear-gradient(135deg,#c4622d,#b84928)'}"></div>
        <div class="{card} ml-2 hover:shadow-md transition-shadow">
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-bold truncate" style="font-family:var(--ws-serif);color:var(--ws-text)">
                  {isManual?'✍️':'📍'} {loc}
                </span>
                {#if isManual}
                  <span class="text-[10px] px-1.5 py-0.5 rounded font-semibold shrink-0"
                    style="background:rgba(99,102,241,.15);color:#6366f1">manuell</span>
                {/if}
              </div>
              <div class="text-xs font-mono mt-0.5" style="color:var(--ws-muted)">{trip.start_date} → {trip.end_date}</div>
              {#if trip.country}
                <div class="text-xs mt-0.5">🌍 {trip.country}</div>
              {/if}
            </div>
            <span class="shrink-0 px-2.5 py-1 rounded-full text-xs font-bold"
              style="background:rgba(196,98,45,.1);color:#c4622d">
              {trip.nights} {trip.nights===1?$t('night'):$t('nights')}
            </span>
          </div>

          <!-- Kosten -->
          <div class="mt-3 flex items-center gap-2 flex-wrap">
            {#if editingCost === trip.id}
              <input type="number"
                value={costDraft}
                oninput={(e) => oneditcost(trip.id, e.target.value)}
                placeholder="Kosten €"
                class="flex-1 min-w-0 text-xs rounded-lg px-2.5 py-1.5 outline-none"
                style="background:var(--ws-surface2);border:1px solid var(--ws-border);color:var(--ws-text)"
                onkeydown={(e) => e.key==='Enter' && onsavecost(trip)} />
              <button onclick={() => onsavecost(trip)}
                class="px-3 py-1.5 rounded-lg text-xs font-semibold text-white shrink-0"
                style="background:#c4622d">✓</button>
              <button onclick={oncanceledit}
                class="px-2 py-1.5 rounded-lg text-xs border shrink-0"
                style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            {:else}
              <button onclick={() => oneditcost(trip.id, trip.cost!=null?String(trip.cost):'')}
                class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs border transition-colors
                       {displayCost!=null?'border-orange-200 bg-orange-50 text-orange-600 font-semibold':'hover:border-orange-200 hover:text-orange-500'}">
                💶 {displayCost!=null ? parseFloat(displayCost).toFixed(2)+' €'+(isAutoCost?' (auto)':'') : 'Kosten hinterlegen'}
              </button>
            {/if}
            <div class="flex gap-1.5 ml-auto">
              {#if mapsUrl}
                <a href={mapsUrl} target="_blank"
                  class="py-1.5 px-2.5 rounded-lg text-xs border hover:border-orange-300 hover:text-orange-600 transition-colors">🗺</a>
              {/if}
              <button onclick={() => ondelete(trip.id)}
                class="py-1.5 px-2.5 rounded-lg text-xs border hover:text-red-500 transition-colors"
                style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
          </div>
        </div>
      </div>
    {/each}
  </div>
{/if}
