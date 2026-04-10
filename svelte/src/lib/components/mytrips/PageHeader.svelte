<script>
  import { t } from '$lib/i18n.js';
  import { bucketlist } from '$lib/stores.js';

  let {
    selectedYear,
    globalSyncing,
    upcomingCount,
    journalYearLength,
    bucketWishCount,
    totalCount,
    visibleYears,
    tabs,
    activeTab,
    onglobalsync,
    onprevyear,
    onnextyear,
    onselectyear,
    onswitchtab,
  } = $props();
</script>

<div class="flex flex-wrap items-center gap-3">
  <h1 class="text-2xl font-bold mr-auto" style="font-family:var(--ws-serif)">{$t('mytripsTitle')}</h1>

  <!-- Globaler Sync -->
  <button onclick={onglobalsync} disabled={globalSyncing}
    title="Dawarich + ActualBudget + Auto-Cost synchronisieren"
    class="w-9 h-9 rounded-full border flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed"
    style="background:var(--ws-surface)">
    {#if globalSyncing}
      <span class="text-sm" style="display:inline-block;animation:spin 1s linear infinite">⟳</span>
    {:else}
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/>
        <path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/>
      </svg>
    {/if}
  </button>

  <!-- Jahr-Switcher -->
  <div class="flex items-center rounded-full shadow-sm overflow-hidden" style="background:var(--ws-surface);border:1px solid var(--ws-border)">
    <button onclick={onprevyear}
      class="w-8 h-8 flex items-center justify-center transition-all text-sm font-bold" style="color:var(--ws-muted)">‹</button>
    {#each visibleYears as y}
      <button onclick={() => onselectyear(y)}
        class="px-3 h-8 text-sm font-semibold transition-all border-x"
        style="border-color:var(--ws-border);{selectedYear !== y ? 'color:var(--ws-muted)' : ''}"
        class:bg-orange-600={selectedYear === y}
        class:text-white={selectedYear === y}>
        {y}
      </button>
    {/each}
    <button onclick={onnextyear}
      class="w-8 h-8 flex items-center justify-center transition-all text-sm font-bold" style="color:var(--ws-muted)">›</button>
  </div>

  <!-- 4 Badges -->
  <div class="flex gap-1.5 flex-wrap">
    <button onclick={() => onswitchtab('trips')}
      class="text-xs font-medium px-2 py-1 rounded-full border transition-colors
             {upcomingCount > 0 ? 'border-orange-200 text-orange-600 bg-orange-50 hover:bg-orange-100' : ''}">
      ✈️ {upcomingCount} geplant
    </button>
    <button onclick={() => onswitchtab('journal')}
      class="text-xs font-medium px-2 py-1 rounded-full border transition-colors" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
      ✅ {journalYearLength} vergangen
    </button>
    <button onclick={() => onswitchtab('bucketlist')}
      class="text-xs font-medium px-2 py-1 rounded-full border transition-colors" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
      🌟 {bucketWishCount} wünsche
    </button>
    <div class="text-xs font-medium px-2 py-1 rounded-full border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
      {totalCount} gesamt
    </div>
  </div>
</div>

<!-- Tab bar -->
<div class="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1">
  {#each tabs as tab}
    <button onclick={() => onswitchtab(tab.id)}
      class="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all border"
      class:bg-orange-600={activeTab===tab.id}
      class:text-white={activeTab===tab.id}
      class:border-orange-600={activeTab===tab.id}>
      {tab.label}
    </button>
  {/each}
</div>
