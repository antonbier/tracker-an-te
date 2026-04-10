<script>
  import { t } from '$lib/i18n.js';

  let {
    tripName      = $bindable(),
    tripDateStart = $bindable(),
    tripDateEnd   = $bindable(),
    tripCost      = $bindable(),
    upcomingTrips,
    pastTrips,
    yearBudget,
    pctYear,
    totalSpentYear,
    remainingYear,
    selectedYear,
    inp,
    card,
    btn,
    onaddtrip,
    onremovetrip,
  } = $props();
</script>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
  <div class="lg:col-span-1 space-y-4">

    <!-- Smart Planer Teaser -->
    <div class="rounded-xl shadow-sm p-5 relative overflow-hidden border"
      style="background:color-mix(in srgb,var(--ws-accent) 8%,var(--ws-surface));border-color:color-mix(in srgb,var(--ws-accent) 30%,var(--ws-border))">
      <span class="absolute top-3 right-3 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
        style="background:var(--ws-accent);color:#fff5ec">Bald verfügbar</span>
      <div class="text-xl mb-2">✨</div>
      <h3 class="font-bold text-sm mb-1" style="font-family:var(--ws-serif);color:var(--ws-text)">Smart Reise-Planer</h3>
      <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">Budget, Personen & Zeitraum — WanderSuite findet Flüge, Mietwagen und Hotels auf einmal.</p>
    </div>

    <!-- Reise planen Formular -->
    <div class={card}>
      <h3 class="text-sm font-semibold mb-3" style="color:var(--ws-text)">➕ Reise planen</h3>
      <div class="space-y-2.5">
        <input bind:value={tripName} placeholder="Ziel / Name *" class={inp} />
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-xs mb-1 block" style="color:var(--ws-muted)">Von *</label>
            <input type="date" bind:value={tripDateStart} class={inp} />
          </div>
          <div>
            <label class="text-xs block mb-1" style="color:var(--ws-muted)">Bis (opt.)</label>
            <input type="date" bind:value={tripDateEnd} class={inp} />
          </div>
        </div>
        <input type="number" bind:value={tripCost} placeholder="Budget / Kosten €" class={inp} />
        <button onclick={onaddtrip} class={btn} style="background:linear-gradient(135deg,#c4622d,#b84928)">+ Hinzufügen</button>
      </div>
    </div>
  </div>

  <div class="lg:col-span-2 space-y-4">
    <!-- Budget-Bar -->
    {#if yearBudget > 0}
      <div class={card}>
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold uppercase tracking-wide">Budget {selectedYear}</span>
          <span class="text-xs font-bold {pctYear>85?'text-red-500':'text-emerald-600'}">{pctYear.toFixed(0)}% verbraucht</span>
        </div>
        <div class="h-3 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500"
            style="width:{pctYear}%;background:{pctYear>85?'#ef4444':pctYear>60?'#f97316':'#059669'}"></div>
        </div>
        <div class="flex justify-between text-xs mt-1.5" style="color:var(--ws-muted)">
          <span>{totalSpentYear.toFixed(2)} € ausgegeben</span>
          <span class="text-emerald-600 font-medium">{remainingYear.toFixed(2)} € frei</span>
        </div>
      </div>
    {/if}

    <!-- Upcoming -->
    <div class={card}>
      <h3 class="text-sm font-semibold mb-3">✈️ Nächste Abenteuer <span class="ml-1 text-xs font-normal" style="color:var(--ws-muted)">({upcomingTrips.length})</span></h3>
      {#if upcomingTrips.length === 0}
        <p class="text-sm py-6 text-center" style="color:var(--ws-muted)">Noch keine Reisen geplant.</p>
      {:else}
        <div class="space-y-2">
          {#each upcomingTrips as tr}
            {@const start = tr.dateStart||tr.date||''}
            {@const end   = tr.dateEnd||''}
            {@const idx   = upcomingTrips.indexOf(tr)}
            <div class="flex items-center gap-3 p-3 rounded-lg bg-orange-50 border border-orange-100 hover:border-orange-200 transition-colors group">
              <div class="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center shrink-0 text-base">✈️</div>
              <div class="flex-1 min-w-0">
                <div style="font-family:var(--ws-serif);color:var(--ws-text)" class="text-sm font-semibold truncate">{tr.name}</div>
                <div class="text-xs font-mono" style="color:var(--ws-muted)">{start}{end&&end!==start?' → '+end:''}</div>
              </div>
              <div class="text-sm font-bold text-orange-600 font-mono shrink-0">{parseFloat(tr.cost).toFixed(2)} €</div>
              <button onclick={() => onremovetrip(idx)}
                class="opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-500 text-xs px-1.5 py-1 rounded border hover:border-red-200">✕</button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Past -->
    {#if pastTrips.length > 0}
      <div class={card}>
        <h3 class="text-sm font-semibold mb-3">✅ Vergangen (manuell) <span class="ml-1 text-xs font-normal" style="color:var(--ws-muted)">({pastTrips.length})</span></h3>
        <div class="space-y-2">
          {#each pastTrips as tr}
            {@const start = tr.dateStart||tr.date||''}
            {@const end   = tr.dateEnd||''}
            {@const idx   = pastTrips.indexOf(tr)}
            <div class="flex items-center gap-3 p-3 rounded-lg border hover:group transition-colors group">
              <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-base">✅</div>
              <div class="flex-1 min-w-0">
                <div style="font-family:var(--ws-serif);color:var(--ws-text)" class="text-sm font-semibold truncate">{tr.name}</div>
                <div class="text-xs font-mono" style="color:var(--ws-muted)">{start}{end&&end!==start?' → '+end:''}</div>
              </div>
              <div class="text-sm font-bold font-mono shrink-0" style="color:var(--ws-muted)">{parseFloat(tr.cost).toFixed(2)} €</div>
              <button onclick={() => onremovetrip(idx)}
                class="opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-500 text-xs px-1.5 py-1 rounded border hover:border-red-200">✕</button>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</div>
