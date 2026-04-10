<script>
  import { t } from '$lib/i18n.js';
  import JournalSyncDawarich from './JournalSyncDawarich.svelte';
  import JournalSyncActual   from './JournalSyncActual.svelte';
  import JournalTimeline     from './JournalTimeline.svelte';

  let {
    budgetInput    = $bindable(),
    mName          = $bindable(),
    mStart         = $bindable(),
    mEnd           = $bindable(),
    mCountry       = $bindable(),
    mCost          = $bindable(),
    forceFull      = $bindable(),
    selectedYear,
    journalYear,
    journalTrips,
    journalLoad,
    budgetSaving,
    mAdding,
    editingCost,
    costDraft,
    syncing,
    syncInfo,
    actualSyncing,
    actualResult,
    actualFiles,
    actualFilesLoading,
    autoCostRunning,
    autoCostResult,
    inp,
    card,
    btn,
    onsavebudget,
    onaddmanualtrip,
    ondeletejournaltrip,
    onsavecost,
    oneditcost,
    oncanceledit,
    onsyncjournal,
    onsyncactual,
    onlistactualfiles,
    onrunautocost,
  } = $props();
</script>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

  <!-- 1/3 Links: Aktionen & Sync -->
  <div class="lg:col-span-1 space-y-4">

    <!-- Jahresbudget -->
    <div class={card}>
      <h3 class="text-sm font-semibold mb-3" style="color:var(--ws-text)">💶 Jahresbudget {selectedYear}</h3>
      <input type="number" bind:value={budgetInput} placeholder="z.B. 4000" class="{inp} mb-3" />
      <button onclick={onsavebudget} disabled={budgetSaving}
        class="{btn} disabled:opacity-50" style="background:linear-gradient(135deg,#c4622d,#b84928)">
        {budgetSaving ? '⏳…' : 'Speichern'}
      </button>
    </div>

    <!-- Manuell erfassen -->
    <div class={card}>
      <h3 class="text-sm font-semibold mb-1" style="color:var(--ws-text)">➕ Reise erfassen</h3>
      <p class="text-xs mb-3" style="color:var(--ws-muted)">Manuell eintragen — kein Dawarich nötig.</p>
      <div class="space-y-2.5">
        <input bind:value={mName} placeholder="Ort / Name *" class={inp} />
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-xs mb-1 block" style="color:var(--ws-muted)">Von *</label>
            <input type="date" bind:value={mStart} class={inp} />
          </div>
          <div>
            <label class="text-xs mb-1 block" style="color:var(--ws-muted)">Bis</label>
            <input type="date" bind:value={mEnd} class={inp} />
          </div>
        </div>
        <input bind:value={mCountry} placeholder="Land (optional)" class={inp} />
        <input type="number" bind:value={mCost} placeholder="Kosten € (optional)" class={inp} />
        <button onclick={onaddmanualtrip} disabled={mAdding}
          class="{btn} disabled:opacity-50" style="background:linear-gradient(135deg,#c4622d,#b84928)">
          {mAdding ? '⏳…' : '+ Hinzufügen'}
        </button>
      </div>
    </div>

    <!-- Tipp-Banner -->
    <div class="rounded-xl p-3 bg-amber-50 border border-amber-200 text-xs text-amber-800">
      <div class="font-semibold mb-1">💡 Tipp: Optimale Reihenfolge</div>
      <p class="leading-relaxed">Synchronisiere zuerst <strong>Dawarich</strong>, dann <strong>ActualBudget</strong>. So können Ausgaben automatisch den erkannten Reisen zugeordnet werden — ohne manuelle Eingabe.</p>
    </div>

    <!-- Dawarich Sync -->
    <JournalSyncDawarich
      bind:forceFull
      {syncing}
      {syncInfo}
      onsync={onsyncjournal}
    />

    <!-- ActualBudget Sync -->
    <JournalSyncActual
      {actualSyncing}
      {actualResult}
      {actualFiles}
      {actualFilesLoading}
      {autoCostRunning}
      {autoCostResult}
      onsync={onsyncactual}
      onlistfiles={onlistactualfiles}
      onrunautocost={onrunautocost}
    />

  </div>

  <!-- 2/3 Rechts: Timeline -->
  <div class="lg:col-span-2">
    <JournalTimeline
      {journalYear}
      {journalLoad}
      {selectedYear}
      {editingCost}
      {costDraft}
      {card}
      ondelete={ondeletejournaltrip}
      onsavecost={onsavecost}
      oneditcost={oneditcost}
      oncanceledit={oncanceledit}
    />
  </div>

</div>
