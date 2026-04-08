<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { apiUrl, trips, budget, appVersion } from '$lib/stores.js';
  import { currentPage } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { t } from '$lib/i18n.js';

  const currentYear = new Date().getFullYear();
  let trackers = $state([]), dawarichTrips = $state([]), loading = $state(true);
  let budgetByYear = $state({});
  let budgetInput  = $state('');
  let budgetSaving = $state(false);

  const yearBudget  = $derived(parseFloat(budgetByYear[String(currentYear)]) || 0);
  const totalBudget = $derived(yearBudget || ($budget ? parseFloat($budget) : 0));
  const totalSpent  = $derived($trips.reduce((s, t) => s + (parseFloat(t.cost) || 0), 0));
  const remaining   = $derived(Math.max(0, totalBudget - totalSpent));
  const spentPct    = $derived(totalBudget > 0 ? Math.min(100, (totalSpent / totalBudget) * 100) : 0);
  const CIRC = 2 * Math.PI * 38;
  const donutFill  = $derived((spentPct / 100) * CIRC);
  const donutColor = $derived(spentPct > 85 ? 'var(--ws-red)' : spentPct > 60 ? 'var(--ws-accent2)' : 'var(--ws-accent)');

  async function loadBudget() {
    if (!$apiUrl) return;
    try { budgetByYear = (await api('/api/trips/budget')) || {}; } catch {}
    budgetInput = budgetByYear[String(currentYear)] != null ? String(budgetByYear[String(currentYear)]) : '';
  }

  async function saveBudget() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const amount = parseFloat(budgetInput);
    if (isNaN(amount) || amount < 0) { toast('Ungültiger Betrag', 'error'); return; }
    budgetSaving = true;
    try {
      await api('/api/trips/budget', { method: 'PUT', body: JSON.stringify({ year: currentYear, amount }) });
      budgetByYear = { ...budgetByYear, [String(currentYear)]: amount };
      toast(`Budget ${currentYear}: ${amount.toFixed(0)} € gespeichert ✓`, 'success');
    } catch (e) { toast(e.message, 'error'); }
    budgetSaving = false;
  }

  onMount(async () => {
    if (!$apiUrl) { loading = false; return; }
    try {
      [trackers, dawarichTrips] = await Promise.all([
        api('/api/trackers').catch(() => []),
        api('/api/dawarich/trips?limit=20').catch(() => []),
      ]);
      await loadBudget();
    } catch {}
    loading = false;
  });

  const activeTrackers  = $derived(trackers.filter(t => t.active));
  const today           = new Date().toISOString().slice(0, 10);
  const upcoming        = $derived($trips.filter(t => t.date >= today));
  const completed       = $derived($trips.filter(t => t.date < today));
  const recentDawarich  = $derived([...dawarichTrips].sort((a,b)=>b.start_date.localeCompare(a.start_date)).slice(0,4));
</script>

<div class="space-y-4">
  <div>
    <h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif);color:var(--ws-text)">{$t('dashWelcome')}</h1>
    <p class="text-sm mt-0.5" style="color:var(--ws-muted)">{$t('dashSubtitle')}</p>
  </div>

  <div class="grid grid-cols-3 gap-3">
    {#each [
      { labelKey:'dashActiveTrackers', value:activeTrackers.length,                                      color:'var(--ws-accent)' },
      { labelKey:'dashBudget',         value:totalBudget>0?totalBudget.toFixed(0)+' €':'–',              color:'var(--ws-accent2)' },
      { labelKey:'dashRemaining',      value:totalBudget>0?remaining.toFixed(0)+' €':'–',               color:'var(--ws-green)' },
    ] as s}
      <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
        <div class="text-xs font-bold tracking-widest uppercase mb-1" style="color:var(--ws-muted)">{$t(s.labelKey)}</div>
        <div class="text-2xl font-bold" style="color:{s.color};font-family:var(--ws-serif)">{s.value}</div>
      </div>
    {/each}
  </div>

  <div class="grid md:grid-cols-2 gap-4">
    <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashBudgetOverview')}</h2>
      <div class="flex items-center gap-4">
        <svg width="90" height="90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="38" fill="none" stroke="var(--ws-border)" stroke-width="14"/>
          <circle cx="50" cy="50" r="38" fill="none" stroke={donutColor} stroke-width="14"
            stroke-dasharray="{donutFill} {CIRC-donutFill}" stroke-dashoffset="60" stroke-linecap="round"
            style="transition:stroke-dasharray .6s ease"/>
        </svg>
        <div class="flex-1 space-y-1.5 text-xs">
          {#each [
            {dot:'var(--ws-accent)', labelKey:'dashSpent',       val:totalSpent.toFixed(2)+' €'},
            {dot:'var(--ws-green)',  labelKey:'dashRemaining',    val:remaining.toFixed(2)+' €'},
            {dot:'var(--ws-border)', labelKey:'dashBudgetTotal',  val:totalBudget.toFixed(2)+' €'},
          ] as row}
            <div class="flex items-center gap-2">
              <div class="w-2.5 h-2.5 rounded-full shrink-0" style="background:{row.dot}"></div>
              <span style="color:var(--ws-muted)">{$t(row.labelKey)}</span>
              <span class="ml-auto font-bold font-mono" style="color:var(--ws-text)">{row.val}</span>
            </div>
          {/each}
        </div>
      </div>
      <!-- Inline budget input -->
      <div class="flex gap-2 mt-3 pt-3 border-t" style="border-color:var(--ws-border)">
        <input
          type="number"
          bind:value={budgetInput}
          placeholder="{currentYear} Budget (€)"
          class="flex-1 min-w-0 px-3 py-1.5 rounded-lg border text-xs"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
          onkeydown={(e) => e.key === 'Enter' && saveBudget()}
        />
        <button onclick={saveBudget} disabled={budgetSaving}
          class="px-3 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-50"
          style="background:var(--ws-accent);color:#fff5ec">
          {budgetSaving ? '⏳' : '✓'}
        </button>
      </div>
    </div>

    <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashActiveTrackersCard')}</h2>
      {#if loading}
        <p class="text-xs" style="color:var(--ws-muted)">{$t('dashLoading')}</p>
      {:else if !$apiUrl}
        <p class="text-xs" style="color:var(--ws-muted)">{$t('dashNoBackend')}</p>
      {:else if activeTrackers.length===0}
        <p class="text-xs mb-3" style="color:var(--ws-muted)">{$t('dashNoTrackers')}</p>
      {:else}
        <div class="space-y-2">
          {#each activeTrackers.slice(0,4) as tr}
            {@const snap=tr.latest_snapshot}
            <button onclick={()=>currentPage.set('priceradar')}
              class="w-full flex items-center justify-between p-2.5 rounded-lg border text-left transition-colors hover:border-[var(--ws-accent)]"
              style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <div>
                <div class="text-sm font-bold font-mono" style="color:var(--ws-text)">{tr.origin} → {tr.destination}</div>
                <div class="text-xs mt-0.5" style="color:var(--ws-muted)">{tr.outbound_date}</div>
              </div>
              <div class="text-sm font-bold font-mono" style="color:var(--ws-green)">
                {snap?.total_price?snap.total_price.toFixed(2)+' €':'–'}
              </div>
            </button>
          {/each}
        </div>
      {/if}
      <button onclick={()=>currentPage.set('priceradar')}
        class="mt-3 w-full py-2 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        {$t('dashStartTracker')}
      </button>
    </div>
  </div>

  <div class="grid md:grid-cols-2 gap-4">
    <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashUpcoming')}</h2>
      {#if upcoming.length===0}
        <p class="text-xs" style="color:var(--ws-muted)">{$t('dashNoUpcoming')}</p>
      {:else}
        <div class="space-y-2">
          {#each upcoming as t}
            <div class="flex items-center gap-3 p-2 rounded-lg" style="background:var(--ws-surface2)">
              <span>✈️</span>
              <div class="flex-1">
                <div class="text-sm font-semibold italic" style="font-family:var(--ws-serif)">{t.name}</div>
                <div class="text-xs font-mono" style="color:var(--ws-muted)">{t.date}</div>
              </div>
              <div class="text-sm font-bold font-mono" style="color:var(--ws-accent2)">{parseFloat(t.cost).toFixed(2)} €</div>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('dashCompleted')}</h2>
      {#if completed.length===0 && recentDawarich.length===0}
        <p class="text-xs" style="color:var(--ws-muted)">{$t('dashNoCompleted')}</p>
      {:else}
        <div class="space-y-2">
          {#each completed.slice(0,2) as t}
            <div class="flex items-center gap-3 p-2 rounded-lg opacity-80" style="background:var(--ws-surface2)">
              <span>✅</span>
              <div class="flex-1">
                <div class="text-sm font-semibold italic" style="font-family:var(--ws-serif)">{t.name}</div>
                <div class="text-xs font-mono" style="color:var(--ws-muted)">{t.date}</div>
              </div>
              <div class="text-sm font-bold font-mono" style="color:var(--ws-muted)">{parseFloat(t.cost).toFixed(2)} €</div>
            </div>
          {/each}
          {#each recentDawarich as trip}
            {@const loc=[trip.location_name,trip.country].filter(Boolean).join(', ')||'?'}
            <div class="flex items-center gap-3 p-2 rounded-lg opacity-80" style="background:var(--ws-surface2)">
              <span>📍</span>
              <div class="flex-1">
                <div class="text-sm font-semibold italic truncate" style="font-family:var(--ws-serif)">{loc}</div>
                <div class="text-xs font-mono" style="color:var(--ws-muted)">{trip.start_date} · {trip.nights}N</div>
              </div>
              <span class="text-xs px-2 py-0.5 rounded-full shrink-0"
                style="background:rgba(196,98,45,.1);color:var(--ws-accent)">Dawarich</span>
            </div>
          {/each}
        </div>
      {/if}
      <button onclick={()=>currentPage.set('journal')}
        class="mt-3 text-xs" style="color:var(--ws-muted)">{$t('dashAllJournal')}</button>
    </div>
  </div>

  {#if $appVersion}
    <div class="text-center pt-2">
      <span class="text-xs font-mono" style="color:var(--ws-border)">{$appVersion}</span>
    </div>
  {/if}
</div>
