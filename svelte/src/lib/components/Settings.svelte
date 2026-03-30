<script>
  import { apiUrl, theme, isDark, lang } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { checkApiStatus, api } from '$lib/api.js';
  import { browser } from '$app/environment';

  let { open = $bindable(false) } = $props();

  let activeTab = $state('basic');
  let urlInput  = $state('');
  let testing   = $state(false);
  let testOk    = $state(null);

  // Integration keys (localStorage)
  function ls(key, fallback = '') { return browser ? (localStorage.getItem(key) || fallback) : fallback; }

  let dawarichUrl   = $state('');
  let dawarichToken = $state('');
  let actualUrl     = $state('');
  let actualToken   = $state('');
  let actualFile    = $state('');
  let homeLat       = $state('');
  let homeLon       = $state('');
  let travelCats    = $state('');
  let serpApiKey    = $state('');
  let geminiKey     = $state('');
  let openaiKey     = $state('');
  let telegramToken = $state('');
  let telegramChat  = $state('');
  let gotifyUrl     = $state('');
  let gotifyToken   = $state('');

  $effect(() => {
    if (open) {
      urlInput      = $apiUrl;
      dawarichUrl   = ls('s-dawarichUrl');
      dawarichToken = ls('s-dawarichToken');
      actualUrl     = ls('s-actualUrl');
      actualToken   = ls('s-actualPassword');
      actualFile    = ls('s-actualFile');
      homeLat       = ls('s-homeLat');
      homeLon       = ls('s-homeLon');
      travelCats    = ls('s-travelCategories');
      serpApiKey    = ls('s-serpApiKey');
      geminiKey     = ls('s-geminiKey');
      openaiKey     = ls('s-openaiKey');
      telegramToken = ls('s-telegramToken');
      telegramChat  = ls('s-telegramChat');
      gotifyUrl     = ls('s-gotifyUrl');
      gotifyToken   = ls('s-gotifyToken');
    }
  });

  const tabs = [
    { id: 'basic',         label: '⚙️ Allgemein' },
    { id: 'integrations',  label: '🔗 Integrationen' },
    { id: 'apis',          label: '🤖 APIs & KI' },
    { id: 'notifications', label: '🔔 Alerts' },
  ];

  async function testConnection() {
    testing = true; testOk = null;
    testOk = await checkApiStatus(urlInput);
    testing = false;
  }

  async function save() {
    if (!browser) return;
    // Basic
    apiUrl.set(urlInput.trim().replace(/\/$/, ''));
    // Integrations
    localStorage.setItem('s-dawarichUrl',       dawarichUrl);
    localStorage.setItem('s-dawarichToken',     dawarichToken);
    localStorage.setItem('s-actualUrl',         actualUrl);
    localStorage.setItem('s-actualPassword',    actualToken);
    localStorage.setItem('s-actualFile',        actualFile);
    localStorage.setItem('s-homeLat',           homeLat);
    localStorage.setItem('s-homeLon',           homeLon);
    localStorage.setItem('s-travelCategories',  travelCats);
    // APIs
    localStorage.setItem('s-serpApiKey',        serpApiKey);
    localStorage.setItem('s-geminiKey',         geminiKey);
    localStorage.setItem('s-openaiKey',         openaiKey);
    // Notifications
    localStorage.setItem('s-telegramToken',     telegramToken);
    localStorage.setItem('s-telegramChat',      telegramChat);
    localStorage.setItem('s-gotifyUrl',         gotifyUrl);
    localStorage.setItem('s-gotifyToken',       gotifyToken);

    // Sync to backend if configured
    if ($apiUrl) {
      try {
        await api('/api/settings', {
          method: 'POST',
          body: JSON.stringify({
            serpapi_key:       serpApiKey  || null,
            gemini_key:        geminiKey   || null,
            openai_key:        openaiKey   || null,
            dawarich_url:      dawarichUrl || null,
            dawarich_token:    dawarichToken || null,
            actual_url:        actualUrl   || null,
            actual_token:      actualToken || null,
            home_lat:          homeLat     || null,
            home_lon:          homeLon     || null,
            travel_categories: travelCats  || null,
          }),
        });
      } catch { /* offline — localStorage is fallback */ }
    }

    toast('Einstellungen gespeichert ✓', 'success');
    open = false;
  }

  function field(label, hint = '') {
    return { label, hint };
  }
</script>

{#if open}
  <!-- Backdrop -->
  <div class="fixed inset-0 z-40 bg-black/40" onclick={() => open = false}
    onkeydown={(e) => e.key === 'Escape' && (open = false)}
    role="button" tabindex="-1" aria-label="Schließen">
  </div>

  <!-- Panel -->
  <div class="fixed inset-y-0 right-0 z-50 w-full max-w-md flex flex-col shadow-2xl"
    style="background:var(--ws-surface)">

    <div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--ws-border)">
      <h2 class="font-semibold text-lg">Einstellungen</h2>
      <button onclick={() => open = false} class="p-1.5 rounded-lg hover:opacity-60">✕</button>
    </div>

    <!-- Tabs -->
    <div class="flex border-b px-2 gap-0.5 pt-2 overflow-x-auto shrink-0" style="border-color:var(--ws-border)">
      {#each tabs as tab}
        <button onclick={() => activeTab = tab.id}
          class="px-3 py-2 text-xs rounded-t-lg font-medium whitespace-nowrap transition-colors shrink-0"
          style={activeTab === tab.id
            ? 'color:var(--ws-accent);border-bottom:2px solid var(--ws-accent)'
            : 'color:var(--ws-muted)'}>
          {tab.label}
        </button>
      {/each}
    </div>

    <div class="flex-1 overflow-y-auto p-5 space-y-4">

      {#if activeTab === 'basic'}
        <!-- Backend URL -->
        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-1" style="color:var(--ws-muted)">
            Backend URL
          </label>
          <input type="url" bind:value={urlInput} placeholder="http://192.168.1.51:8766"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="flex items-center gap-2 mt-2">
            <button onclick={testConnection} disabled={testing}
              class="px-4 py-1.5 rounded-xl text-xs border transition-opacity hover:opacity-70 disabled:opacity-40"
              style="border-color:var(--ws-border);color:var(--ws-muted)">
              {testing ? '⏳ Testen…' : '🔗 Verbinden'}
            </button>
            {#if testOk === true}
              <span class="text-xs font-medium" style="color:var(--ws-green)">✓ Verbunden</span>
            {:else if testOk === false}
              <span class="text-xs font-medium" style="color:var(--ws-red)">✗ Nicht erreichbar</span>
            {/if}
          </div>
        </div>

        <!-- Theme -->
        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">Darstellung</label>
          <div class="flex gap-2">
            {#each [{ val: '', label: '☀️ Hell' }, { val: 'dark', label: '🌙 Dunkel' }] as opt}
              <button onclick={() => theme.set(opt.val)}
                class="flex-1 py-2 rounded-xl text-sm border transition-all"
                style={$theme === opt.val
                  ? 'background:var(--ws-accent);color:#fff;border-color:var(--ws-accent)'
                  : 'background:var(--ws-surface2);color:var(--ws-muted);border-color:var(--ws-border)'}>
                {opt.label}
              </button>
            {/each}
          </div>
        </div>

      {:else if activeTab === 'integrations'}
        <!-- Dawarich -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Dawarich</div>
          <input bind:value={dawarichUrl} placeholder="https://dawarich.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={dawarichToken} type="password" placeholder="API Token"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="grid grid-cols-2 gap-2">
            <input bind:value={homeLat} placeholder="Lat: 46.7987" class="px-3 py-2 rounded-xl border text-sm"
              style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
            <input bind:value={homeLon} placeholder="Lon: 11.7188" class="px-3 py-2 rounded-xl border text-sm"
              style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          </div>
          <div class="text-xs" style="color:var(--ws-muted)">Home-Koordinaten für Trip-Erkennung (>50km)</div>
        </div>

        <hr style="border-color:var(--ws-border)"/>

        <!-- ActualBudget -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">ActualBudget</div>
          <input bind:value={actualUrl} placeholder="https://actual.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={actualToken} type="password" placeholder="Server Password"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={actualFile} placeholder="Budget-Datei ID (optional)"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={travelCats} placeholder="Kategorien: Holiday, Flights, Hotel"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>

      {:else if activeTab === 'apis'}
        <!-- SerpAPI -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">SerpAPI</div>
          <input bind:value={serpApiKey} type="password" placeholder="API Key — serpapi.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="text-xs" style="color:var(--ws-muted)">Für Google Flights + Booking — 100 Suchen/Monat kostenlos</div>
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <!-- Gemini -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Google Gemini</div>
          <input bind:value={geminiKey} type="password" placeholder="AIzaSy… — aistudio.google.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="text-xs" style="color:var(--ws-muted)">Für KI-Reiseempfehlungen — kostenlos</div>
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <!-- OpenAI -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">OpenAI</div>
          <input bind:value={openaiKey} type="password" placeholder="sk-… — platform.openai.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="text-xs" style="color:var(--ws-muted)">gpt-4o-mini — ~$0.00015/1k Tokens</div>
        </div>

      {:else if activeTab === 'notifications'}
        <!-- Telegram -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Telegram</div>
          <input bind:value={telegramToken} type="password" placeholder="Bot Token"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={telegramChat} placeholder="Chat ID"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="text-xs" style="color:var(--ws-muted)">Preisalerts wenn unter definiertem Schwellenwert</div>
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <!-- Gotify -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Gotify</div>
          <input bind:value={gotifyUrl} placeholder="https://gotify.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={gotifyToken} type="password" placeholder="App Token"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>
      {/if}

    </div>

    <div class="p-4 border-t shrink-0" style="border-color:var(--ws-border)">
      <button onclick={save}
        class="w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        Speichern
      </button>
    </div>

  </div>
{/if}
