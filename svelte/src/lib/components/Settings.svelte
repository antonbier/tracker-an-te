<script>
  import { apiUrl } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { checkApiStatus } from '$lib/api.js';

  let { open = $bindable(false) } = $props();

  let activeTab = $state('basic');
  let urlInput  = $state('');
  let testing   = $state(false);
  let testOk    = $state(null);

  // Sync input with store when panel opens
  $effect(() => {
    if (open) urlInput = $apiUrl;
  });

  const tabs = [
    { id: 'basic',         label: '⚙️ Allgemein' },
    { id: 'integrations',  label: '🔗 Integrationen' },
    { id: 'apis',          label: '🤖 APIs & KI' },
    { id: 'notifications', label: '🔔 Alerts' },
  ];

  async function testConnection() {
    testing = true;
    testOk = await checkApiStatus(urlInput);
    testing = false;
  }

  function save() {
    apiUrl.set(urlInput.trim());
    toast('Einstellungen gespeichert', 'success');
    open = false;
  }
</script>

{#if open}
  <div class="fixed inset-0 z-40 bg-black/40 cursor-default" onclick={() => open = false} onkeydown={(e) => e.key === "Escape" && (open = false)} role="button" tabindex="-1" aria-label="Schließen"></div>

  <div class="fixed inset-y-0 right-0 z-50 w-full max-w-md flex flex-col shadow-2xl"
    style="background:var(--ws-surface)">

    <div class="flex items-center justify-between px-5 py-4 border-b"
      style="border-color:var(--ws-border)">
      <h2 class="font-semibold text-lg">Einstellungen</h2>
      <button onclick={() => open = false} class="p-1.5 rounded-lg hover:opacity-60">✕</button>
    </div>

    <!-- Tab bar -->
    <div class="flex border-b px-2 gap-1 pt-2 overflow-x-auto" style="border-color:var(--ws-border)">
      {#each tabs as tab}
        <button
          onclick={() => activeTab = tab.id}
          class="px-3 py-2 text-xs rounded-t-lg font-medium whitespace-nowrap transition-colors shrink-0"
          style={activeTab === tab.id
            ? 'color:var(--ws-accent);border-bottom:2px solid var(--ws-accent)'
            : 'color:var(--ws-muted)'}
        >
          {tab.label}
        </button>
      {/each}
    </div>

    <div class="flex-1 overflow-y-auto p-5">
      {#if activeTab === 'basic'}
        <label class="block mb-1 text-sm font-medium">Backend URL</label>
        <input
          type="url"
          bind:value={urlInput}
          placeholder="https://..."
          class="w-full px-3 py-2 rounded-xl border text-sm mb-3"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
        />
        <div class="flex gap-2">
          <button
            onclick={testConnection}
            disabled={testing}
            class="px-4 py-2 rounded-xl text-sm border transition-opacity hover:opacity-70"
            style="border-color:var(--ws-border);color:var(--ws-muted)"
          >
            {testing ? '⏳ Testen…' : '🔗 Verbindung testen'}
          </button>
          {#if testOk === true}
            <span class="text-green-600 text-sm self-center">✓ Verbunden</span>
          {:else if testOk === false}
            <span class="text-red-500 text-sm self-center">✗ Fehler</span>
          {/if}
        </div>
      {:else if activeTab === 'integrations'}
        <p class="text-sm" style="color:var(--ws-muted)">Dawarich & ActualBudget — folgt in nächster Iteration.</p>
      {:else if activeTab === 'apis'}
        <p class="text-sm" style="color:var(--ws-muted)">SerpAPI, Gemini, OpenAI — folgt in nächster Iteration.</p>
      {:else if activeTab === 'notifications'}
        <p class="text-sm" style="color:var(--ws-muted)">Telegram & Gotify — folgt in nächster Iteration.</p>
      {/if}
    </div>

    <div class="p-4 border-t" style="border-color:var(--ws-border)">
      <button
        onclick={save}
        class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-opacity hover:opacity-90"
        style="background:var(--ws-accent)"
      >
        Speichern
      </button>
    </div>
  </div>
{/if}
