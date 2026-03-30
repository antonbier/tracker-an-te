<script>
  import { apiUrl, onboardingDone } from '$lib/stores.js';
  import { checkApiStatus } from '$lib/api.js';

  let step      = $state(1);
  let urlInput  = $state('');
  let checking  = $state(false);
  let connected = $state(false);
  let error     = $state('');

  async function checkUrl() {
    checking = true;
    error = '';
    connected = await checkApiStatus(urlInput);
    if (!connected) error = 'Verbindung fehlgeschlagen. Bitte URL prüfen.';
    checking = false;
  }

  function next() {
    if (step < 3) step++;
    else finish();
  }

  function finish() {
    apiUrl.set(urlInput.trim());
    onboardingDone.set('1');
  }

  function skip() {
    onboardingDone.set('1');
  }
</script>

<!-- Full-screen overlay — lives at document root, no stacking context issues -->
<div class="fixed inset-0 z-50 flex items-center justify-center p-4"
  style="background:var(--ws-bg)">

  <div class="w-full max-w-sm">
    <!-- Logo -->
    <div class="text-center mb-8">
      <div class="text-5xl mb-3">🧭</div>
      <h1 class="text-2xl font-bold" style="color:var(--ws-accent)">WanderSuite</h1>
      <p class="text-sm mt-1" style="color:var(--ws-muted)">Schritt {step} von 3</p>
    </div>

    <!-- Progress bar -->
    <div class="h-1 rounded-full mb-8" style="background:var(--ws-border)">
      <div class="h-1 rounded-full transition-all" style="background:var(--ws-accent);width:{(step/3)*100}%"></div>
    </div>

    {#if step === 1}
      <h2 class="font-semibold text-lg mb-1">Backend verbinden</h2>
      <p class="text-sm mb-4" style="color:var(--ws-muted)">Gib die URL deines WanderSuite-Backends ein.</p>
      <input
        type="url"
        bind:value={urlInput}
        placeholder="https://dein-backend.railway.app"
        class="w-full px-4 py-3 rounded-xl border text-sm mb-3"
        style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"
      />
      {#if error}
        <p class="text-sm text-red-500 mb-3">{error}</p>
      {/if}
      <button
        onclick={checkUrl}
        disabled={checking || !urlInput}
        class="w-full py-3 rounded-xl text-sm font-semibold mb-3 transition-opacity"
        style="background:var(--ws-surface2);color:var(--ws-text)"
      >
        {checking ? '⏳ Verbinde…' : '🔗 Verbindung testen'}
      </button>
      <button
        onclick={next}
        disabled={!connected}
        class="w-full py-3 rounded-xl text-sm font-semibold text-white transition-opacity"
        style="background:var(--ws-accent);opacity:{connected ? 1 : 0.4}"
      >
        Weiter →
      </button>

    {:else if step === 2}
      <h2 class="font-semibold text-lg mb-1">API-Keys (optional)</h2>
      <p class="text-sm mb-4" style="color:var(--ws-muted)">
        SerpAPI, Gemini und OpenAI kannst du später in den Einstellungen konfigurieren.
      </p>
      <button onclick={next} class="w-full py-3 rounded-xl text-sm font-semibold text-white"
        style="background:var(--ws-accent)">
        Weiter →
      </button>

    {:else}
      <h2 class="font-semibold text-lg mb-1">Alles bereit! 🎉</h2>
      <p class="text-sm mb-6" style="color:var(--ws-muted)">
        WanderSuite ist verbunden und bereit.
      </p>
      <button onclick={finish} class="w-full py-3 rounded-xl text-sm font-semibold text-white"
        style="background:var(--ws-accent)">
        Los geht's →
      </button>
    {/if}

    <button onclick={skip} class="w-full text-center text-xs mt-4 py-2" style="color:var(--ws-muted)">
      Überspringen
    </button>
  </div>
</div>
