<script>
  import { currentPage } from '$lib/stores.js';
  let { onSettings } = $props();

  const nav = [
    { id: 'home',        icon: '🏠', label: 'Dashboard' },
    { id: 'priceradar',  icon: '🎯', label: 'Preis-Radar' },
    { id: 'discover',    icon: '✨', label: 'Inspiration' },
    { id: 'mytrips',     icon: '🎒', label: 'Meine Reisen' },
    { id: 'journal',     icon: '📓', label: 'Reisetagebuch' },
  ];
</script>

<aside class="hidden md:flex flex-col w-56 shrink-0 border-r"
  style="background:var(--ws-surface);border-color:var(--ws-border)">

  <nav class="flex-1 p-3 flex flex-col gap-1 pt-4">
    {#each nav as item}
      <button
        onclick={() => currentPage.set(item.id)}
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors text-left w-full"
        class:active={$currentPage === item.id}
        style={$currentPage === item.id
          ? 'background:var(--ws-accent);color:#fff'
          : 'color:var(--ws-muted)'}
      >
        <span class="text-base">{item.icon}</span>
        {item.label}
      </button>
    {/each}
  </nav>

  <div class="p-3 border-t" style="border-color:var(--ws-border)">
    <button
      onclick={onSettings}
      class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium w-full transition-colors"
      style="color:var(--ws-muted)"
    >
      <span class="text-base">⚙️</span>
      Einstellungen
    </button>
  </div>
</aside>
