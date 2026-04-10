<script>
  let {
    forceFull = $bindable(),
    syncing,
    syncInfo,
    onsync,
  } = $props();
</script>

<div class="rounded-xl shadow-sm p-5 border border-l-4 border-l-emerald-400">
  <div class="flex items-center gap-2 mb-1">
    <span class="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center shrink-0">1</span>
    <h3 class="text-sm font-semibold">Dawarich Sync</h3>
  </div>
  <p class="text-xs mb-3 ml-7" style="color:var(--ws-muted)">GPS-Reisen automatisch erkennen und importieren.</p>

  <label class="flex items-center gap-2 text-xs mb-3 ml-7 cursor-pointer">
    <input type="checkbox" bind:checked={forceFull}
      class="rounded text-orange-500 focus:ring-orange-400" />
    Gelöschte Reisen erzwingen (Full Sync)
  </label>

  <button onclick={onsync} disabled={syncing}
    class="w-full py-2 px-4 rounded-lg text-sm font-semibold border
           hover:border-emerald-300 hover:text-emerald-700 transition-all disabled:opacity-50">
    {syncing ? '⏳ Sync…' : '🧭 Synchronisieren'}
  </button>
  {#if syncInfo}
    <p class="text-xs mt-2 ml-1" style="color:var(--ws-muted)">ℹ️ {syncInfo}</p>
  {/if}
</div>
