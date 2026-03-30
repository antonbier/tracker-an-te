<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { apiUrl, trips, budget } from '$lib/stores.js';
  import { currentPage } from '$lib/stores.js';

  let trackers    = $state([]);
  let stats       = $state(null);
  let loading     = $state(true);

  const totalBudget = $derived($budget ? parseFloat($budget) : 0);
  const totalSpent  = $derived($trips.reduce((s, t) => s + (parseFloat(t.cost) || 0), 0));
  const remaining   = $derived(Math.max(0, totalBudget - totalSpent));
  const spentPct    = $derived(totalBudget > 0 ? Math.min(100, (totalSpent / totalBudget) * 100) : 0);

  // Donut math (r=38, circumference≈239)
  const CIRC = 2 * Math.PI * 38;
  const donutFill = $derived((spentPct / 100) * CIRC);
  const donutColor = $derived(spentPct > 85 ? 'var(--ws-red)' : spentPct > 60 ? 'var(--ws-accent2)' : 'var(--ws-accent)');

  onMount(async () => {
    if (!$apiUrl) { loading = false; return; }
    try {
      trackers = await api('/api/trackers');
    } catch (e) { /* no backend */ }
    loading = false;
  });

  const activeTrackers = $derived(trackers.filter(t => t.active));
  const today = new Date().toISOString().slice(0, 10);
  const upcoming  = $derived($trips.filter(t => t.date >= today));
  const completed = $derived($trips.filter(t => t.date < today));
</script>

<div class="space-y-4">

  <!-- Welcome -->
  <div>
    <h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif);color:var(--ws-text)">
      Willkommen zurück
    </h1>
    <p class="text-sm mt-0.5" style="color:var(--ws-muted)">Dein Reise-Überblick</p>
  </div>

  <!-- Stats row -->
  <div class="grid grid-cols-3 gap-3">
    {#each [
      { label: 'Aktive Tracker', value: activeTrackers.length, color: 'var(--ws-accent)' },
      { label: 'Jahresbudget',   value: totalBudget > 0 ? totalBudget.toFixed(0) + ' €' : '–', color: 'var(--ws-accent2)' },
      { label: 'Verbleibend',    value: totalBudget > 0 ? remaining.toFixed(0) + ' €' : '–', color: 'var(--ws-green)' },
    ] as s}
      <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
        <div class="text-xs font-bold tracking-widest uppercase mb-1" style="color:var(--ws-muted);font-family:var(--ws-mono)">{s.label}</div>
        <div class="text-2xl font-bold" style="color:{s.color};font-family:var(--ws-serif)">{s.value}</div>
      </div>
    {/each}
  </div>

  <!-- Main grid -->
  <div class="grid md:grid-cols-2 gap-4">

    <!-- Budget Donut -->
    <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">
        💰 Budget-Übersicht
      </h2>
      <div class="flex items-center gap-4">
        <svg width="90" height="90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="38" fill="none" stroke="var(--ws-border)" stroke-width="14"/>
          <circle cx="50" cy="50" r="38" fill="none"
            stroke={donutColor} stroke-width="14"
            stroke-dasharray="{donutFill} {CIRC - donutFill}"
            stroke-dashoffset="60" stroke-linecap="round"
            style="transition: stroke-dasharray .6s ease"/>
        </svg>
        <div class="flex-1 space-y-1.5 text-xs">
          {#each [
            { dot: 'var(--ws-accent)',  label: 'Ausgegeben', val: totalSpent.toFixed(2) + ' €' },
            { dot: 'var(--ws-green)',   label: 'Verbleibend', val: remaining.toFixed(2) + ' €' },
            { dot: 'var(--ws-border)',  label: 'Jahresbudget', val: totalBudget.toFixed(2) + ' €' },
          ] as row}
            <div class="flex items-center gap-2">
              <div class="w-2.5 h-2.5 rounded-full shrink-0" style="background:{row.dot}"></div>
              <span style="color:var(--ws-muted)">{row.label}</span>
              <span class="ml-auto font-bold font-mono" style="color:var(--ws-text)">{row.val}</span>
            </div>
          {/each}
        </div>
      </div>
    </div>

    <!-- Active Trackers -->
    <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">
        🎯 Aktive Tracker
      </h2>
      {#if loading}
        <p class="text-xs" style="color:var(--ws-muted)">Lade...</p>
      {:else if !$apiUrl}
        <p class="text-xs" style="color:var(--ws-muted)">Keine Backend-URL konfiguriert.</p>
      {:else if activeTrackers.length === 0}
        <p class="text-xs mb-3" style="color:var(--ws-muted)">Noch keine Tracker — leg los!</p>
      {:else}
        <div class="space-y-2">
          {#each activeTrackers.slice(0, 4) as tr}
            {@const snap = tr.latest_snapshot}
            <button
              onclick={() => currentPage.set('priceradar')}
              class="w-full flex items-center justify-between p-2.5 rounded-lg border text-left transition-colors hover:border-[var(--ws-accent)]"
              style="background:var(--ws-surface2);border-color:var(--ws-border)"
            >
              <div>
                <div class="text-sm font-bold font-mono" style="color:var(--ws-text)">{tr.origin} → {tr.destination}</div>
                <div class="text-xs mt-0.5" style="color:var(--ws-muted)">{tr.outbound_date}</div>
              </div>
              <div class="text-sm font-bold font-mono" style="color:var(--ws-green)">
                {snap?.total_price ? snap.total_price.toFixed(2) + ' €' : '–'}
              </div>
            </button>
          {/each}
        </div>
      {/if}
      <button
        onclick={() => currentPage.set('priceradar')}
        class="mt-3 w-full py-2 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec"
      >
        + Tracker starten
      </button>
    </div>

  </div>

  <!-- Trips row -->
  <div class="grid md:grid-cols-2 gap-4">

    <!-- Upcoming -->
    <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">✈️ Geplante Reisen</h2>
      {#if upcoming.length === 0}
        <p class="text-xs" style="color:var(--ws-muted)">Keine geplanten Reisen.</p>
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

    <!-- Completed -->
    <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">✅ Abgeschlossen</h2>
      {#if completed.length === 0}
        <p class="text-xs" style="color:var(--ws-muted)">Noch keine abgeschlossenen Reisen.</p>
      {:else}
        <div class="space-y-2">
          {#each completed.slice(0, 4) as t}
            <div class="flex items-center gap-3 p-2 rounded-lg opacity-70" style="background:var(--ws-surface2)">
              <span>✅</span>
              <div class="flex-1">
                <div class="text-sm font-semibold italic" style="font-family:var(--ws-serif)">{t.name}</div>
                <div class="text-xs font-mono" style="color:var(--ws-muted)">{t.date}</div>
              </div>
              <div class="text-sm font-bold font-mono" style="color:var(--ws-muted)">{parseFloat(t.cost).toFixed(2)} €</div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>

</div>
