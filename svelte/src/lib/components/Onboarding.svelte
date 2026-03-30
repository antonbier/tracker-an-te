<script>
  import { apiUrl, onboardingDone } from '$lib/stores.js';
  import { checkApiStatus } from '$lib/api.js';
  import { t } from '$lib/i18n.js';

  let { onDone } = $props();
  let step      = $state(1);
  let urlInput  = $state('');
  let checking  = $state(false);
  let connected = $state(false);
  let error     = $state('');

  async function checkUrl() {
    checking = true; error = '';
    connected = await checkApiStatus(urlInput);
    if (!connected) error = 'Verbindung fehlgeschlagen.';
    checking = false;
  }

  function next() { if (step < 3) step++; else finish(); }
  function finish() { apiUrl.set(urlInput.trim()); onboardingDone.set('1'); onDone?.(); }
  function skip() { onboardingDone.set('1'); onDone?.(); }
</script>

<div class="fixed inset-0 flex items-center justify-center p-4" style="background:var(--ws-bg)">
  <div class="w-full max-w-sm">
    <div class="text-center mb-8">
      <div class="text-5xl mb-3">🧭</div>
      <h1 class="text-2xl font-bold" style="color:var(--ws-accent)">WanderSuite</h1>
      <p class="text-sm mt-1" style="color:var(--ws-muted)">Schritt {step} von 3</p>
    </div>
    <div class="h-1 rounded-full mb-8" style="background:var(--ws-border)">
      <div class="h-1 rounded-full transition-all" style="background:var(--ws-accent);width:{(step/3)*100}%"></div>
    </div>

    {#if step === 1}
      <h2 class="font-semibold text-lg mb-1">{$t('onboardingConnectTitle')}</h2>
      <p class="text-sm mb-4" style="color:var(--ws-muted)">{$t('onboardingConnectDesc')}</p>
      <input type="url" bind:value={urlInput} placeholder="https://dein-backend.railway.app"
        class="w-full px-4 py-3 rounded-xl border text-sm mb-3"
        style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"/>
      {#if error}<p class="text-sm text-red-500 mb-3">{error}</p>{/if}
      <button onclick={checkUrl} disabled={checking || !urlInput}
        class="w-full py-3 rounded-xl text-sm font-semibold mb-3 transition-opacity disabled:opacity-50"
        style="background:var(--ws-surface2);color:var(--ws-text)">
        {checking ? $t('onboardingTesting') : $t('onboardingTest')}
      </button>
      <button onclick={next} disabled={!connected}
        class="w-full py-3 rounded-xl text-sm font-semibold text-white transition-opacity"
        style="background:var(--ws-accent);opacity:{connected?1:0.4}">
        {$t('onboardingNext')}
      </button>
    {:else if step === 2}
      <h2 class="font-semibold text-lg mb-1">{$t('onboardingApisTitle')}</h2>
      <p class="text-sm mb-4" style="color:var(--ws-muted)">{$t('onboardingApisDesc')}</p>
      <button onclick={next} class="w-full py-3 rounded-xl text-sm font-semibold text-white"
        style="background:var(--ws-accent)">{$t('onboardingNext')}</button>
    {:else}
      <h2 class="font-semibold text-lg mb-1">{$t('onboardingDoneTitle')}</h2>
      <p class="text-sm mb-6" style="color:var(--ws-muted)">{$t('onboardingDoneDesc')}</p>
      <button onclick={finish} class="w-full py-3 rounded-xl text-sm font-semibold text-white"
        style="background:var(--ws-accent)">{$t('onboardingStart')}</button>
    {/if}
    <button onclick={skip} class="w-full text-center text-xs mt-4 py-2" style="color:var(--ws-muted)">
      {$t('onboardingSkip')}
    </button>
  </div>
</div>
