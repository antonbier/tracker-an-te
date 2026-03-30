<script>
  import { currentPage, currentUser, appStatus, logout, isAdmin } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';
  let { onSettings } = $props();

  const nav = [
    { id: 'home',       icon: '🏠', labelKey: 'navHome' },
    { id: 'priceradar', icon: '🎯', labelKey: 'navRadar' },
    { id: 'discover',   icon: '✨', labelKey: 'navDiscover' },
    { id: 'mytrips',    icon: '🎒', labelKey: 'navTrips' },
    { id: 'journal',    icon: '📓', labelKey: 'navJournal' },
  ];

  function handleLogout() { logout(); window.location.reload(); }
</script>

<aside class="hidden md:flex flex-col w-56 shrink-0 border-r"
  style="background:var(--ws-surface);border-color:var(--ws-border)">
  <nav class="flex-1 p-3 flex flex-col gap-1 pt-4">
    {#each nav as item}
      <button onclick={() => currentPage.set(item.id)}
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors text-left w-full"
        style={$currentPage === item.id
          ? 'background:var(--ws-accent);color:#fff'
          : 'color:var(--ws-muted)'}>
        <span class="text-base">{item.icon}</span>
        {$t(item.labelKey)}
      </button>
    {/each}
  </nav>
  <div class="p-3 border-t space-y-1" style="border-color:var(--ws-border)">
    {#if $appStatus?.auth_enabled && $currentUser}
      <div class="px-3 py-2 rounded-xl text-xs" style="background:var(--ws-surface2);color:var(--ws-muted)">
        <div class="font-bold truncate" style="color:var(--ws-text)">{$currentUser.email}</div>
        <div class="capitalize">{$currentUser.role}</div>
      </div>
    {/if}
    <button onclick={onSettings}
      class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium w-full transition-colors"
      style="color:var(--ws-muted)">
      <span class="text-base">⚙️</span>
      {$t('settings')}
    </button>
    {#if $appStatus?.auth_enabled && $currentUser}
      <button onclick={handleLogout}
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium w-full transition-colors"
        style="color:var(--ws-muted)">
        <span class="text-base">🚪</span>
        {$t('logout')}
      </button>
    {/if}
  </div>
</aside>
