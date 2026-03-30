<script>
  import { currentPage, currentUser, appStatus, logout, isAdmin } from '$lib/stores.js';
  let { onSettings } = $props();

  const nav = [
    { id: 'home',        icon: '🏠', label: 'Dashboard' },
    { id: 'priceradar',  icon: '🎯', label: 'Preis-Radar' },
    { id: 'discover',    icon: '✨', label: 'Inspiration' },
    { id: 'mytrips',     icon: '🎒', label: 'Meine Reisen' },
    { id: 'journal',     icon: '📓', label: 'Reisetagebuch' },
  ];

  function handleLogout() {
    logout();
    // Reload so layout gate re-evaluates
    window.location.reload();
  }
</script>

<aside class="hidden md:flex flex-col w-56 shrink-0 border-r"
  style="background:var(--ws-surface);border-color:var(--ws-border)">

  <nav class="flex-1 p-3 flex flex-col gap-1 pt-4">
    {#each nav as item}
      <button
        onclick={() => currentPage.set(item.id)}
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors text-left w-full"
        style={$currentPage === item.id
          ? 'background:var(--ws-accent);color:#fff'
          : 'color:var(--ws-muted)'}
      >
        <span class="text-base">{item.icon}</span>
        {item.label}
      </button>
    {/each}
  </nav>

  <div class="p-3 border-t space-y-1" style="border-color:var(--ws-border)">
    <!-- Current user badge (only when auth enabled) -->
    {#if $appStatus?.auth_enabled && $currentUser}
      <div class="px-3 py-2 rounded-xl text-xs" style="background:var(--ws-surface2);color:var(--ws-muted)">
        <div class="font-bold truncate" style="color:var(--ws-text)">{$currentUser.email}</div>
        <div class="capitalize">{$currentUser.role}</div>
      </div>
    {/if}

    <button
      onclick={onSettings}
      class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium w-full transition-colors"
      style="color:var(--ws-muted)"
    >
      <span class="text-base">⚙️</span>
      Einstellungen
    </button>

    <!-- Logout (only when auth enabled and logged in) -->
    {#if $appStatus?.auth_enabled && $currentUser}
      <button
        onclick={handleLogout}
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium w-full transition-colors"
        style="color:var(--ws-muted)"
      >
        <span class="text-base">🚪</span>
        Abmelden
      </button>
    {/if}
  </div>
</aside>
