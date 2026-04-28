<script>
  /**
   * BudgetWidget.svelte — 4-Säulen Finanz-Dashboard für TripHub
   *
   * Säulen:
   *   1. Gesamtbudget     (editierbar)
   *   2. Gebuchte Kosten  (Tracker: Flug + Hotel)
   *   3. Manuelle Ausgaben (inline editierbar)
   *   4. ActualBudget Synced (ausklappbar, Sync-Button, Link ↗)
   *
   * Bilanz: Restbudget = Gesamt - Gebucht - Manuell - Synced
   */
  import { t }    from '$lib/i18n.js';
  import { api }  from '$lib/api.js';
  import { apiUrl } from '$lib/stores.js';
  import { browser } from '$app/environment';

  let {
    trip             = null,
    budgetBreakdown  = null,
    manualExpEditing = $bindable(false),
    manualExpDraft   = $bindable(''),
    manualExpSaving  = false,
    onsaveManualExp  = () => {},
    onreloadBudget   = () => {},
  } = $props();

  // ── Budget-Edit (Gesamtbudget) ────────────────────────────────────────────
  let budgetEditing = $state(false);
  let budgetDraft   = $state('');
  let budgetSaving  = $state(false);

  async function saveBudget() {
    const val = parseFloat(budgetDraft);
    if (isNaN(val) || val < 0) return;
    budgetSaving = true;
    try {
      await api(`/api/ws-trips/${trip.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ budget: val }),
      });
      budgetEditing = false;
      onreloadBudget();
    } catch { /* ignore */ }
    budgetSaving = false;
  }

  // ── ActualBudget Sync ─────────────────────────────────────────────────────
  let syncing       = $state(false);
  let syncError     = $state('');
  let txExpanded    = $state(false);

  async function syncBudget() {
    if (!trip?.id) return;
    syncing = true; syncError = '';
    try {
      await api(`/api/ws-trips/${trip.id}/sync-budget`, { method: 'POST' });
      onreloadBudget();
    } catch (e) {
      syncError = e?.message || 'Sync fehlgeschlagen';
    }
    syncing = false;
  }

  // ActualBudget URL — aus Backend-Settings geladen (nicht localStorage)
  // Link wird nur angezeigt wenn URL bekannt; Backend liefert sie via budgetBreakdown
  const actualUrl = $derived(budgetBreakdown?.actual_url || '');

  // ── Derived Werte ─────────────────────────────────────────────────────────
  const total        = $derived(parseFloat(budgetBreakdown?.total_budget   ?? 0));
  const booked       = $derived(parseFloat(budgetBreakdown?.booked_flight  ?? 0) +
                                parseFloat(budgetBreakdown?.booked_hotel   ?? 0));
  const manual       = $derived(parseFloat(trip?.manual_expenses           ?? 0));
  const synced       = $derived(parseFloat(budgetBreakdown?.synced_expenses ?? 0));
  const totalSpent   = $derived(booked + manual + synced);
  const remaining    = $derived(total - totalSpent);
  const pct          = $derived(total > 0 ? Math.min(110, (totalSpent / total) * 100) : 0);
  const overBudget   = $derived(total > 0 && remaining < 0);

  const barColor = $derived(
    pct > 100 ? '#ef4444' :
    pct > 85  ? '#f97316' :
    'var(--ws-green, #2d6a4f)'
  );

  const syncedTxs   = $derived(budgetBreakdown?.synced_transactions ?? []);
  const syncedAt    = $derived(budgetBreakdown?.synced_at ?? null);

  const syncedAtLabel = $derived.by(() => {
    if (!syncedAt) return '';
    try {
      return new Date(syncedAt + 'Z').toLocaleDateString('de-AT', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' });
    } catch { return syncedAt.slice(0, 16).replace('T', ' '); }
  });
</script>

{#if budgetBreakdown}
<div class="rounded-2xl border p-4 space-y-4" style="background:var(--ws-surface2);border-color:var(--ws-border)">

  <!-- Header -->
  <div class="flex items-center justify-between">
    <h3 class="font-bold text-sm" style="color:var(--ws-text)">💶 Budget</h3>
    {#if overBudget}
      <span class="text-[10px] font-bold px-2 py-0.5 rounded-full" style="background:rgba(239,68,68,.15);color:#ef4444">
        ⚠️ Überschritten
      </span>
    {/if}
  </div>

  <!-- ── Säule 1: Gesamtbudget ──────────────────────────────────────────── -->
  <div class="flex items-center justify-between py-2 border-b" style="border-color:var(--ws-border)">
    <span class="text-xs font-semibold" style="color:var(--ws-text)">
      🎯 {$t('hubBudgetTotal') || 'Gesamtbudget'}
    </span>
    {#if budgetEditing}
      <div class="flex items-center gap-1">
        <input type="number" min="0" step="1" bind:value={budgetDraft}
          class="w-24 px-2 py-0.5 text-xs rounded-lg border font-mono focus:outline-none"
          style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"
          onkeydown={(e) => { if (e.key==='Enter') saveBudget(); if (e.key==='Escape') budgetEditing=false; }} />
        <span class="text-xs" style="color:var(--ws-muted)">€</span>
        <button onclick={saveBudget} disabled={budgetSaving}
          class="px-2 py-0.5 rounded text-xs font-bold disabled:opacity-40"
          style="background:var(--ws-accent);color:#fff5ec">{budgetSaving ? '⏳' : '✓'}</button>
        <button onclick={() => budgetEditing=false} class="text-xs px-1" style="color:var(--ws-muted)">✕</button>
      </div>
    {:else}
      <div class="flex items-center gap-2">
        <span class="text-sm font-mono font-bold" style="color:var(--ws-text)">
          {total > 0 ? total.toFixed(0) + ' €' : '—'}
        </span>
        <button onclick={() => { budgetEditing=true; budgetDraft=String(total || ''); }}
          class="text-[10px] px-1.5 py-0.5 rounded border hover:opacity-70"
          style="border-color:var(--ws-border);color:var(--ws-muted)">✏️</button>
      </div>
    {/if}
  </div>

  <!-- ── Ausgaben-Zeilen ────────────────────────────────────────────────── -->
  <div class="space-y-2">

    <!-- Säule 2: Gebuchte Kosten -->
    {#if booked > 0 || budgetBreakdown.booked_flight > 0 || budgetBreakdown.booked_hotel > 0}
      <div class="space-y-1">
        <div class="flex items-center justify-between pl-3 border-l-2" style="border-color:color-mix(in srgb,var(--ws-accent) 40%,transparent)">
          <span class="text-xs font-medium" style="color:var(--ws-muted)">
            ✈️ {$t('hubBudgetBooked') || 'Gebuchte Kosten'}
          </span>
          <span class="text-sm font-mono font-semibold" style="color:var(--ws-text)">−{booked.toFixed(0)} €</span>
        </div>
        {#if budgetBreakdown.booked_flight > 0}
          <div class="flex items-center justify-between pl-6 text-[11px]" style="color:var(--ws-muted)">
            <span>✈️ {$t('hubBudgetFlight') || 'Flug'}</span>
            <span class="font-mono">{budgetBreakdown.booked_flight.toFixed(0)} €</span>
          </div>
        {/if}
        {#if budgetBreakdown.booked_hotel > 0}
          <div class="flex items-center justify-between pl-6 text-[11px]" style="color:var(--ws-muted)">
            <span>🏨 {$t('hubBudgetHotel') || 'Hotel'}</span>
            <span class="font-mono">{budgetBreakdown.booked_hotel.toFixed(0)} €</span>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Säule 3: Manuelle Ausgaben -->
    <div class="flex items-center justify-between pl-3 border-l-2" style="border-color:color-mix(in srgb,var(--ws-accent2,#e9a84c) 40%,transparent)">
      <span class="text-xs font-medium" style="color:var(--ws-muted)">
        💵 {$t('hubManualExp') || 'Barausgaben'}
      </span>
      {#if manualExpEditing}
        <div class="flex items-center gap-1">
          <input type="number" min="0" step="0.01" bind:value={manualExpDraft}
            class="w-20 px-2 py-0.5 text-xs rounded-lg border font-mono focus:outline-none"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"
            onkeydown={(e) => { if (e.key==='Enter') onsaveManualExp(); if (e.key==='Escape') manualExpEditing=false; }} />
          <span class="text-xs" style="color:var(--ws-muted)">€</span>
          <button onclick={onsaveManualExp} disabled={manualExpSaving}
            class="px-2 py-0.5 rounded text-xs font-bold disabled:opacity-40"
            style="background:var(--ws-accent);color:#fff5ec">{manualExpSaving ? '⏳' : '✓'}</button>
          <button onclick={() => manualExpEditing=false} class="text-xs px-1" style="color:var(--ws-muted)">✕</button>
        </div>
      {:else}
        <div class="flex items-center gap-2">
          <span class="text-sm font-mono font-semibold" style="color:var(--ws-text)">
            {manual > 0 ? '−' + manual.toFixed(0) + ' €' : '0 €'}
          </span>
          <button onclick={() => { manualExpEditing=true; manualExpDraft=String(trip?.manual_expenses??0); }}
            class="text-[10px] px-1.5 py-0.5 rounded border hover:opacity-70"
            style="border-color:var(--ws-border);color:var(--ws-muted)">✏️</button>
        </div>
      {/if}
    </div>

    <!-- Säule 4: ActualBudget Synced -->
    <div class="pl-3 border-l-2 space-y-1" style="border-color:color-mix(in srgb,var(--ws-green,#2d6a4f) 40%,transparent)">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5">
          <!-- Akkordeon-Toggle -->
          {#if syncedTxs.length > 0}
            <button onclick={() => txExpanded = !txExpanded}
              class="text-xs font-medium flex items-center gap-1 hover:opacity-70 transition-all"
              style="color:var(--ws-muted)">
              <span style="transform:{txExpanded ? 'rotate(90deg)' : 'rotate(0)'};transition:transform .2s;display:inline-block">›</span>
              📊 ActualBudget
            </button>
          {:else}
            <span class="text-xs font-medium" style="color:var(--ws-muted)">📊 ActualBudget</span>
          {/if}
          <!-- Sync Button -->
          <button onclick={syncBudget} disabled={syncing}
            class="text-[10px] px-1.5 py-0.5 rounded border transition-all hover:opacity-70 disabled:opacity-40"
            style="border-color:var(--ws-border);color:var(--ws-muted)">
            {syncing ? '⏳' : '🔄'}
          </button>
          <!-- Link ↗ -->
          {#if actualUrl}
            <a href={actualUrl} target="_blank" rel="noopener noreferrer"
              class="text-[10px] px-1.5 py-0.5 rounded border transition-all hover:opacity-70"
              style="border-color:var(--ws-border);color:var(--ws-muted)">↗</a>
          {/if}
        </div>
        <div class="text-right">
          <span class="text-sm font-mono font-semibold" style="color:var(--ws-text)">
            {synced > 0 ? '−' + synced.toFixed(0) + ' €' : '0 €'}
          </span>
        </div>
      </div>

      <!-- Sync-Datum -->
      {#if syncedAtLabel}
        <div class="text-[10px] pl-4" style="color:var(--ws-muted)">Sync: {syncedAtLabel}</div>
      {/if}

      <!-- Fehler -->
      {#if syncError}
        <div class="text-[10px] pl-4 text-red-400">{syncError}</div>
      {/if}

      <!-- Akkordeon: Transaktionsliste -->
      {#if txExpanded && syncedTxs.length > 0}
        <div class="mt-1 ml-4 space-y-0.5 max-h-40 overflow-y-auto rounded-lg p-2"
          style="background:var(--ws-surface);border:1px solid var(--ws-border)">
          {#each syncedTxs as tx}
            <div class="flex items-center justify-between text-[10px] py-0.5">
              <div class="flex-1 min-w-0 flex items-center gap-1.5">
                <span class="shrink-0 font-mono" style="color:var(--ws-muted)">{tx.date?.slice(5)}</span>
                <span class="truncate" style="color:var(--ws-text)">{tx.name || '—'}</span>
              </div>
              <span class="shrink-0 font-mono font-semibold ml-2" style="color:var(--ws-text)">
                {tx.amount?.toFixed(2)} €
              </span>
            </div>
          {/each}
        </div>
      {:else if txExpanded && syncedTxs.length === 0}
        <div class="text-[10px] pl-4" style="color:var(--ws-muted)">Keine Transaktionen im Reisezeitraum</div>
      {/if}
    </div>
  </div>

  <!-- ── Bilanz ─────────────────────────────────────────────────────────── -->
  {#if total > 0}
    <div class="pt-2 border-t space-y-2" style="border-color:var(--ws-border)">
      <div class="flex items-center justify-between">
        <span class="text-sm font-semibold" style="color:var(--ws-text)">
          {$t('hubBudgetOnSite') || 'Restbudget'}
        </span>
        <span class="text-lg font-bold font-mono"
          style="color:{overBudget ? '#ef4444' : 'var(--ws-green, #2d6a4f)'}">
          {remaining.toFixed(0)} €
        </span>
      </div>

      <!-- Progress Bar -->
      <div class="h-2.5 rounded-full overflow-hidden" style="background:var(--ws-border)">
        <div class="h-full rounded-full transition-all duration-700"
          style="width:{Math.min(100, pct)}%;background:{barColor}"></div>
      </div>

      <div class="flex justify-between text-[10px]" style="color:var(--ws-muted)">
        <span>{totalSpent.toFixed(0)} € ausgegeben</span>
        <span style="color:{barColor}">{pct.toFixed(0)}%</span>
      </div>
    </div>
  {:else}
    <!-- Kein Budget gesetzt — CTA -->
    <div class="flex items-center gap-2 pt-1">
      <span class="text-xs" style="color:var(--ws-muted)">Kein Budget gesetzt</span>
      <button onclick={() => { budgetEditing=true; budgetDraft=''; }}
        class="text-xs px-2 py-1 rounded-lg hover:opacity-80"
        style="background:var(--ws-accent);color:#fff5ec">+ Budget setzen</button>
    </div>
  {/if}

</div>
{/if}
