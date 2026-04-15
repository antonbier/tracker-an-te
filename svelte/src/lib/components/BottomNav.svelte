<script>
  import { currentPage, currentUser, appStatus } from '$lib/stores.js';
  import { logout } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';

  let { onSettings } = $props();

  const nav = [
    { id: 'home',       icon: '🏠', labelKey: 'navHomeShort' },
    { id: 'priceradar', icon: '🎯', labelKey: 'navRadarShort' },
    { id: 'planer',     icon: '🪄', labelKey: 'navWizzardShort' },
    { id: 'mytrips',    icon: '🎒', labelKey: 'navTripsShort' },
  ];

  let userMenuOpen = $state(false);

  function handleLogout() {
    userMenuOpen = false;
    logout();
  }
</script>

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
  <button onclick={() => userMenuOpen = !userMenuOpen}
    class="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 text-xs font-medium transition-colors"
    style="color:var(--ws-muted)">
    <span class="text-lg leading-none">⚙️</span>
    {$t('navMore')}
  </button>
</nav>

{#if userMenuOpen}
  <div class="md:hidden fixed inset-0 z-[60] bg-black/40"
    onclick={() => userMenuOpen = false}
    role="button" tabindex="-1" aria-label={$t('settingsClose')}>
  </div>
  <div class="md:hidden fixed bottom-16 left-2 right-2 z-[70] rounded-2xl shadow-2xl border p-4 space-y-3"
    style="background:var(--ws-surface);border-color:var(--ws-border)">

    {#if $appStatus?.auth_enabled && $currentUser}
      <div class="flex items-center gap-3 px-3 py-2.5 rounded-xl border"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="w-9 h-9 rounded-full flex items-center justify-center text-base shrink-0"
          style="background:var(--ws-accent);color:#fff">
          {$currentUser.email?.[0]?.toUpperCase() ?? '?'}
        </div>
        <div class="min-w-0">
          <div class="text-sm font-semibold truncate" style="color:var(--ws-text)">{$currentUser.email}</div>
          <div class="text-xs" style="color:var(--ws-muted)">{$currentUser.role}</div>
        </div>
      </div>
    {/if}

    <button onclick={() => { userMenuOpen = false; onSettings?.(); }}
      class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border text-left transition-opacity hover:opacity-80"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
      <span class="text-lg">⚙️</span>
      <span class="text-sm font-medium">{$t('settings')}</span>
    </button>

    {#if $appStatus?.auth_enabled && $currentUser}
      <button onclick={handleLogout}
        class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border text-left transition-opacity hover:opacity-80"
        style="background:rgba(220,38,38,.06);border-color:rgba(220,38,38,.2);color:#dc2626">
        <span class="text-lg">🚪</span>
        <span class="text-sm font-semibold">{$t('logout')}</span>
      </button>
    {/if}
  </div>
{/if}

<div class="md:hidden h-16 shrink-0"></div>
