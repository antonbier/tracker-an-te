<script>
  import { currentPage } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';

  const nav = [
    { id: 'home',       icon: '🏠', labelKey: 'navHomeShort' },
    { id: 'priceradar', icon: '🎯', labelKey: 'navRadarShort' },
    { id: 'mytrips',    icon: '🎒', labelKey: 'navTripsShort' },
    { id: 'discover',   icon: '✨', labelKey: 'navDiscover' },
  ];
</script>

<!-- Fixed bottom nav for mobile — always visible, never scrolled away -->
<nav class="md:hidden fixed bottom-0 left-0 right-0 z-50 flex border-t safe-area-bottom"
  style="background:var(--ws-surface);border-color:var(--ws-border)">
  {#each nav as item}
    <button onclick={() => currentPage.set(item.id)}
      class="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 text-xs font-medium transition-colors"
      style={$currentPage === item.id ? 'color:var(--ws-accent)' : 'color:var(--ws-muted)'}>
      <span class="text-lg leading-none">{item.icon}</span>
      {$t(item.labelKey)}
    </button>
  {/each}
</nav>
<!-- Spacer so content isn't hidden behind fixed nav -->
<div class="md:hidden h-16 shrink-0"></div>
