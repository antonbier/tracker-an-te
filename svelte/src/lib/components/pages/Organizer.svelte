<script>
  import { t } from '$lib/i18n.js';
  import VaultTab     from '$lib/components/organizer/VaultTab.svelte';
  import PackingTab   from '$lib/components/organizer/PackingTab.svelte';
  import EmergencyTab from '$lib/components/organizer/EmergencyTab.svelte';

  let activeTab = $state('vault');

  const tabs = $derived([
    { id: 'vault',     label: $t('organizerTabVault') },
    { id: 'packing',   label: $t('organizerTabPacking') },
    { id: 'emergency', label: $t('organizerTabEmergency') },
  ]);
</script>

<div class="w-full space-y-4">
  <h1 class="text-xl font-bold" style="font-family:var(--ws-serif);color:var(--ws-text)">
    🗂️ {$t('navOrganizer')}
  </h1>

  <div class="flex items-center gap-1 overflow-x-auto pb-1">
    {#each tabs as tab}
      <button onclick={() => activeTab = tab.id}
        class="shrink-0 px-4 py-2 rounded-xl text-sm font-semibold transition-all whitespace-nowrap"
        style={activeTab === tab.id
          ? 'background:var(--ws-accent);color:#fff5ec'
          : 'background:var(--ws-surface2);color:var(--ws-muted)'}>
        {tab.label}
      </button>
    {/each}
  </div>

  {#if activeTab === 'vault'}
    <VaultTab />
  {:else if activeTab === 'packing'}
    <PackingTab />
  {:else if activeTab === 'emergency'}
    <EmergencyTab />
  {/if}
</div>
