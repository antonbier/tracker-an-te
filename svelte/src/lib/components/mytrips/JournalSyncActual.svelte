<script>
  import { t } from '$lib/i18n.js';

  let {
    actualSyncing,
    actualResult,
    actualFiles,
    actualFilesLoading,
    autoCostRunning,
    autoCostResult,
    onsync,
    onlistfiles,
    onrunautocost,
  } = $props();
</script>

<div class="rounded-xl shadow-sm p-5 border border-l-4 border-l-blue-400">
  <div class="flex items-center gap-2 mb-1">
    <span class="w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center shrink-0">2</span>
    <h3 class="text-sm font-semibold">{$t('mytripsActualSync')}</h3>
  </div>
  <p class="text-xs mb-3 ml-7" style="color:var(--ws-muted)">{$t('mytripsActualDesc')}</p>

  {#if !actualFiles.length}
    <details class="mb-3 ml-7">
      <summary class="text-xs cursor-pointer hover:text-orange-500" style="color:var(--ws-muted);transition:colors">💡 Budget-Dateiname unbekannt?</summary>
      <div class="mt-2 p-3 rounded-lg border text-xs space-y-2">
        <p>In ActualBudget: oben links Budget-Name anklicken → ID aus der URL kopieren</p>
        <button onclick={onlistfiles} disabled={actualFilesLoading}
          class="w-full py-1.5 px-3 rounded-lg border hover:border-orange-300 hover:text-orange-600 transition-all disabled:opacity-40 text-xs font-medium">
          {actualFilesLoading ? '⏳…' : '📂 Dateien anzeigen'}
        </button>
      </div>
    </details>
  {/if}

  {#if actualFiles.length}
    <div class="mb-3 ml-7 p-2 rounded-lg bg-emerald-50 border border-emerald-200">
      <p class="text-xs font-semibold text-emerald-700 mb-1">Budget-Dateien:</p>
      {#each actualFiles as f}
        <div class="text-xs font-mono text-emerald-600 truncate">📄 {f.name}</div>
      {/each}
      <p class="text-[10px] text-emerald-500 mt-1">→ In Einstellungen → Mein Bereich eintragen</p>
    </div>
  {/if}

  <button onclick={onsync} disabled={actualSyncing}
    class="w-full py-2 px-4 rounded-lg text-sm font-semibold border
           hover:border-blue-300 hover:text-blue-700 transition-all disabled:opacity-40">
    {actualSyncing ? '⏳ Sync…' : '🔄 Synchronisieren'}
  </button>

  {#if actualResult?.error}
    <div class="mt-2 p-2 rounded-lg bg-red-50 border border-red-200 text-xs text-red-600">
      ⚠️ {actualResult.error}
    </div>
  {/if}

  {#if actualResult?.transactions?.length}
    <div class="mt-3 pt-3 border-t space-y-1 max-h-32 overflow-y-auto">
      {#each actualResult.transactions.slice(0,10) as tx}
        <div class="flex justify-between text-xs py-0.5">
          <span class="truncate flex-1 mr-2">{tx.payee_name||tx.notes||'–'}</span>
          <span class="font-mono font-bold text-orange-600 shrink-0">{Math.abs(tx.amount??0).toFixed(2)} €</span>
        </div>
      {/each}
    </div>

    <div class="mt-3 pt-3 border-t">
      <button onclick={onrunautocost} disabled={autoCostRunning}
        class="w-full py-2 px-4 rounded-lg text-sm font-semibold border-2 border-orange-300 bg-orange-50
               text-orange-700 hover:bg-orange-100 transition-all disabled:opacity-40">
        {autoCostRunning ? '⏳ Zuordne…' : '🔗 Kosten automatisch zuordnen'}
      </button>
      {#if autoCostResult}
        <p class="text-xs text-emerald-600 mt-1.5 text-center">
          ✓ {autoCostResult.trips_updated} Reisen · {autoCostResult.total_assigned?.toFixed(2)} € zugeordnet
        </p>
      {/if}
    </div>
  {/if}
</div>
