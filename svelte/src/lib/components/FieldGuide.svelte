<script>
  let { open = $bindable(false) } = $props();

  let activeTab = $state('start');

  const tabs = [
    { id: 'start',    label: '🚀 Start' },
    { id: 'radar',    label: '🎯 Preis-Radar' },
    { id: 'reisen',   label: '🎒 Reisen' },
    { id: 'settings', label: '⚙️ Setup' },
  ];
</script>

{#if open}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 z-40 bg-black/40"
    onclick={() => open = false}
  ></div>

  <!-- Panel — slides in from right, z-50 above backdrop -->
  <div class="fixed inset-y-0 right-0 z-50 w-full max-w-md flex flex-col shadow-2xl"
    style="background:var(--ws-surface)">

    <div class="flex items-center justify-between px-5 py-4 border-b"
      style="border-color:var(--ws-border)">
      <h2 class="font-semibold text-lg">📖 Field Guide</h2>
      <button onclick={() => open = false} class="p-1.5 rounded-lg hover:opacity-60">✕</button>
    </div>

    <!-- Tabs -->
    <div class="flex border-b px-4 gap-1 pt-2" style="border-color:var(--ws-border)">
      {#each tabs as tab}
        <button
          onclick={() => activeTab = tab.id}
          class="px-3 py-2 text-sm rounded-t-lg font-medium transition-colors"
          style={activeTab === tab.id
            ? 'color:var(--ws-accent);border-bottom:2px solid var(--ws-accent)'
            : 'color:var(--ws-muted)'}
        >
          {tab.label}
        </button>
      {/each}
    </div>

    <div class="flex-1 overflow-y-auto p-5 text-sm" style="color:var(--ws-text)">
      {#if activeTab === 'start'}
        <h3 class="font-semibold mb-2">Willkommen bei WanderSuite 👋</h3>
        <p style="color:var(--ws-muted)">Gib im ersten Schritt deine Backend-URL in den Einstellungen ein.</p>
      {:else if activeTab === 'radar'}
        <h3 class="font-semibold mb-2">Preis-Radar 🎯</h3>
        <p style="color:var(--ws-muted)">Verfolge Flugpreise mit Ryanair, Google Flights, Homair und Booking.</p>
      {:else if activeTab === 'reisen'}
        <h3 class="font-semibold mb-2">Meine Reisen 🎒</h3>
        <p style="color:var(--ws-muted)">Scratch Map, Bucket List, Reisejournal und Budget-Übersicht.</p>
      {:else if activeTab === 'settings'}
        <h3 class="font-semibold mb-2">Setup ⚙️</h3>
        <p style="color:var(--ws-muted)">Backend-URL, API-Keys und Benachrichtigungen konfigurieren.</p>
      {/if}
    </div>
  </div>
{/if}
