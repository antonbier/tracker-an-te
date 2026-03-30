<script>
  let activeTab = $state('overview');
  const tabs = [
    { id: 'overview',   label: '🗺️ Karte' },
    { id: 'bucketlist', label: '⭐ Bucket List' },
    { id: 'journal',    label: '📔 Journal' },
    { id: 'budget',     label: '💶 Budget' },
  ];
</script>

<div class="space-y-4">
  <h1 class="text-xl font-semibold">Meine Reisen 🎒</h1>
  <div class="flex gap-2 flex-wrap">
    {#each tabs as tab}
      <button
        onclick={() => activeTab = tab.id}
        class="px-4 py-1.5 rounded-full text-sm font-medium transition-colors"
        style={activeTab === tab.id
          ? 'background:var(--ws-accent);color:#fff'
          : 'background:var(--ws-surface2);color:var(--ws-muted)'}
      >
        {tab.label}
      </button>
    {/each}
  </div>
  <p class="text-sm" style="color:var(--ws-muted)">Scratch Map, Journal und Budget folgen in der nächsten Iteration.</p>
</div>
