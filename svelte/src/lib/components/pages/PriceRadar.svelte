<script>
  // PriceRadar page — full implementation in next iteration
  let activeTab = $state('ryanair');
  const tabs = ['ryanair', 'google', 'homair', 'booking'];
</script>

<div class="space-y-4">
  <h1 class="text-xl font-semibold">Preis-Radar 🎯</h1>
  <div class="flex gap-2 flex-wrap">
    {#each tabs as tab}
      <button
        onclick={() => activeTab = tab}
        class="px-4 py-1.5 rounded-full text-sm font-medium capitalize transition-colors"
        style={activeTab === tab
          ? 'background:var(--ws-accent);color:#fff'
          : 'background:var(--ws-surface2);color:var(--ws-muted)'}
      >
        {tab}
      </button>
    {/each}
  </div>
  <p class="text-sm" style="color:var(--ws-muted)">Tracker-Komponenten folgen in der nächsten Iteration.</p>
</div>
