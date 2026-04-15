<script>
  /**
   * BudgetWidget.svelte
   * Budget breakdown card for TripHub.
   */
  import { t } from '$lib/i18n.js';

  let {
    trip             = null,
    budgetBreakdown  = null,
    manualExpEditing = $bindable(false),
    manualExpDraft   = $bindable(''),
    manualExpSaving  = false,
    onsaveManualExp  = () => {},
  } = $props();
</script>

{#if budgetBreakdown?.has_budget}
  <div class="rounded-2xl border p-4 space-y-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
    <h3 class="font-bold text-sm" style="color:var(--ws-text)">💶 Budget</h3>
    <div class="space-y-2">
      {#each [
        [$t('hubBudgetTotal'),  budgetBreakdown.total_budget,  false],
        [$t('hubBudgetFlight'), budgetBreakdown.booked_flight, true],
        [$t('hubBudgetHotel'),  budgetBreakdown.booked_hotel,  true],
      ] as [label, val, indent]}
        {#if val > 0 || !indent}
          <div class="flex items-center justify-between {indent ? 'pl-3 border-l-2' : ''}"
            style="{indent ? 'border-color:var(--ws-border)' : ''}">
            <span class="text-xs" style="color:var(--ws-muted)">{label}</span>
            <span class="text-sm font-mono font-bold" style="color:var(--ws-text)">
              {indent ? '−' : ''}{parseFloat(val).toFixed(0)} €
            </span>
          </div>
        {/if}
      {/each}

      <!-- Manual expenses row -->
      <div class="flex items-center justify-between pl-3 border-l-2" style="border-color:var(--ws-border)">
        <span class="text-xs" style="color:var(--ws-muted)">💵 {$t('hubManualExp') || 'Barausgaben'}</span>
        {#if manualExpEditing}
          <div class="flex items-center gap-1">
            <input type="number" min="0" step="0.01"
              bind:value={manualExpDraft}
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
            <span class="text-sm font-mono font-bold" style="color:var(--ws-text)">
              −{parseFloat(trip?.manual_expenses ?? 0).toFixed(0)} €
            </span>
            <button onclick={() => { manualExpEditing=true; manualExpDraft=String(trip?.manual_expenses??0); }}
              class="text-[10px] px-1.5 py-0.5 rounded border hover:opacity-70"
              style="border-color:var(--ws-border);color:var(--ws-muted)">✏️</button>
          </div>
        {/if}
      </div>

      <!-- On-site remainder -->
      <div class="flex items-center justify-between pt-2 mt-1 border-t" style="border-color:var(--ws-border)">
        <span class="text-sm font-semibold" style="color:var(--ws-text)">{$t('hubBudgetOnSite')}</span>
        <span class="text-lg font-bold font-mono"
          style="color:{budgetBreakdown.on_site_budget >= 0 ? 'var(--ws-green,#2d6a4f)' : '#ef4444'}">
          {parseFloat(budgetBreakdown.on_site_budget).toFixed(0)} €
        </span>
      </div>
    </div>

    {#if budgetBreakdown.total_budget > 0}
      {@const spent = budgetBreakdown.booked_flight + budgetBreakdown.booked_hotel + (budgetBreakdown.manual_expenses || 0)}
      {@const pct   = Math.min(100, (spent / budgetBreakdown.total_budget) * 100)}
      <div class="h-2 rounded-full overflow-hidden" style="background:var(--ws-border)">
        <div class="h-full rounded-full transition-all duration-700"
          style="width:{pct}%;background:{pct > 85 ? '#ef4444' : 'var(--ws-green,#2d6a4f)'}"></div>
      </div>
    {/if}
  </div>
{/if}
