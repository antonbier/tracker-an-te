<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { theme, isDark, apiUrl, onboardingDone, jwtToken, currentUser,
           appStatus, logout, loadSettingsFromBackend } from '$lib/stores.js';
  import { loadLocale } from '$lib/i18n.js';
  import { lang } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import Toast      from '$lib/components/Toast.svelte';
  import AppShell   from '$lib/components/AppShell.svelte';
  import Onboarding from '$lib/components/Onboarding.svelte';
  import Login      from '$lib/components/Login.svelte';
  import Setup      from '$lib/components/Setup.svelte';

  let { children } = $props();
  let statusLoading = $state(false);   // start false — show Onboarding immediately

  $effect(() => {
    if ($isDark) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  });

  onMount(async () => {
    await loadLocale($lang);
    // Only check status if we're past onboarding
    if ($apiUrl && $onboardingDone) await checkStatus();
  });

  $effect(() => { loadLocale($lang); });

  async function checkStatus() {
    statusLoading = true;
    try {
      const s = await api('/api/status');
      appStatus.set(s);
    } catch {
      appStatus.set({ auth_enabled: false, needs_setup: false });
    }
    await loadSettingsFromBackend($apiUrl);
    statusLoading = false;
  }

  $effect(() => {
    if ($apiUrl && $onboardingDone) checkStatus();
  });

  const needsOnboarding = $derived(!$onboardingDone || !$apiUrl);
  const needsSetup = $derived(!needsOnboarding && $appStatus?.needs_setup === true);
  const needsLogin = $derived(
    !needsOnboarding && !needsSetup &&
    $appStatus?.auth_enabled === true && !$jwtToken
  );
  const showApp = $derived(!needsOnboarding && !needsSetup && !needsLogin && !statusLoading);
</script>

<!-- Onboarding always renders on top via z-index:9999 in its own component -->
{#if needsOnboarding}
  <Onboarding onDone={checkStatus} />
{:else if statusLoading}
  <div style="position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:var(--ws-bg)">
    <div style="text-align:center">
      <div style="font-size:2.5rem;margin-bottom:0.75rem">🧭</div>
      <p style="font-size:0.875rem;color:var(--ws-muted)">Verbinde…</p>
    </div>
  </div>
{:else if needsSetup}
  <Setup onDone={checkStatus} />
{:else if needsLogin}
  <Login onDone={checkStatus} />
{:else if showApp}
  <AppShell>
    {@render children()}
  </AppShell>
{/if}

<Toast />
