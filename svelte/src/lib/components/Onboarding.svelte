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

<!--
  z-index: 9999 + pointer-events: all explizit gesetzt
  isolation: isolate verhindert dass parent stacking contexts interferen
-->
<div
  style="position:fixed;inset:0;z-index:9999;pointer-events:all;isolation:isolate;background:var(--ws-bg);display:flex;align-items:center;justify-content:center;padding:1rem"
>
  <div style="width:100%;max-width:24rem">
    <div style="text-align:center;margin-bottom:2rem">
      <div style="font-size:3rem;margin-bottom:0.75rem">🧭</div>
      <h1 style="font-size:1.5rem;font-weight:700;color:var(--ws-accent)">WanderSuite</h1>
      <p style="font-size:0.875rem;margin-top:0.25rem;color:var(--ws-muted)">Schritt {step} von 3</p>
    </div>

    <div style="height:4px;border-radius:9999px;margin-bottom:2rem;background:var(--ws-border)">
      <div style="height:4px;border-radius:9999px;background:var(--ws-accent);width:{(step/3)*100}%;transition:width .3s ease"></div>
    </div>

    {#if step === 1}
      <h2 style="font-size:1.125rem;font-weight:600;margin-bottom:0.25rem">{$t('onboardingConnectTitle')}</h2>
      <p style="font-size:0.875rem;margin-bottom:1rem;color:var(--ws-muted)">{$t('onboardingConnectDesc')}</p>
      <input
        type="url"
        bind:value={urlInput}
        placeholder="https://dein-backend.railway.app"
        style="width:100%;padding:0.75rem 1rem;border-radius:0.75rem;border:1px solid var(--ws-border);background:var(--ws-surface);color:var(--ws-text);font-size:0.875rem;margin-bottom:0.75rem;box-sizing:border-box;pointer-events:all"
      />
      {#if error}<p style="font-size:0.875rem;color:#dc2626;margin-bottom:0.75rem">{error}</p>{/if}
      <button
        onclick={checkUrl}
        disabled={checking || !urlInput}
        style="width:100%;padding:0.75rem;border-radius:0.75rem;font-size:0.875rem;font-weight:600;margin-bottom:0.75rem;background:var(--ws-surface2);color:var(--ws-text);border:none;cursor:pointer;pointer-events:all;opacity:{checking||!urlInput?0.5:1}"
      >
        {checking ? $t('onboardingTesting') : $t('onboardingTest')}
      </button>
      <button
        onclick={next}
        disabled={!connected}
        style="width:100%;padding:0.75rem;border-radius:0.75rem;font-size:0.875rem;font-weight:600;color:#fff;background:var(--ws-accent);border:none;cursor:pointer;pointer-events:all;opacity:{connected?1:0.4}"
      >
        {$t('onboardingNext')}
      </button>

    {:else if step === 2}
      <h2 style="font-size:1.125rem;font-weight:600;margin-bottom:0.25rem">{$t('onboardingApisTitle')}</h2>
      <p style="font-size:0.875rem;margin-bottom:1rem;color:var(--ws-muted)">{$t('onboardingApisDesc')}</p>
      <button
        onclick={next}
        style="width:100%;padding:0.75rem;border-radius:0.75rem;font-size:0.875rem;font-weight:600;color:#fff;background:var(--ws-accent);border:none;cursor:pointer;pointer-events:all"
      >
        {$t('onboardingNext')}
      </button>

    {:else}
      <h2 style="font-size:1.125rem;font-weight:600;margin-bottom:0.25rem">{$t('onboardingDoneTitle')}</h2>
      <p style="font-size:0.875rem;margin-bottom:1.5rem;color:var(--ws-muted)">{$t('onboardingDoneDesc')}</p>
      <button
        onclick={finish}
        style="width:100%;padding:0.75rem;border-radius:0.75rem;font-size:0.875rem;font-weight:600;color:#fff;background:var(--ws-accent);border:none;cursor:pointer;pointer-events:all"
      >
        {$t('onboardingStart')}
      </button>
    {/if}

    <button
      onclick={skip}
      style="width:100%;text-align:center;font-size:0.75rem;margin-top:1rem;padding:0.5rem;color:var(--ws-muted);background:none;border:none;cursor:pointer;pointer-events:all"
    >
      {$t('onboardingSkip')}
    </button>
  </div>
</div>
