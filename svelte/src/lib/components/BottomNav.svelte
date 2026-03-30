<script>
  let { currentPage = $bindable() } = $props();

  const nav = [
    { id: 'home',       icon: '🏠', label: 'Home' },
    { id: 'priceradar', icon: '🎯', label: 'Radar' },
    { id: 'discover',   icon: '✨', label: 'Discover' },
    { id: 'mytrips',    icon: '🎒', label: 'Reisen' },
  ];
</script>

<nav class="md:hidden flex border-t shrink-0"
  style="background:var(--ws-surface);border-color:var(--ws-border)">
  {#each nav as item}
    <button
      onclick={() => currentPage = item.id}
      class="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 text-xs font-medium transition-colors"
      style={currentPage === item.id ? 'color:var(--ws-accent)' : 'color:var(--ws-muted)'}
    >
      <span class="text-lg leading-none">{item.icon}</span>
      {item.label}
    </button>
  {/each}
</nav>
